"""Split a policy document where its own structure says to split it.

Extraction used to run once per page against the first six thousand characters.
That is fine for a two-page schedule and quietly wrong for the document people
actually hold: a policy wording runs to forty dense pages, and the terms that
cost money are rarely on page one. Anything past the cut was never read at all,
and a single pass over a whole page asks the model to hold a benefit table, an
exclusions list and three sub-limits in mind at once, which is where recall goes.

So the document is cut into chunks and each chunk is read on its own, in detail.
Three rules decide where the cuts fall.

**Cut on headings, not on character counts.** Indian policy documents are
heavily sectioned, numbered clauses, capitalised banners, schedule tables. Those
boundaries are where the subject changes, so a chunk that respects them is about
one thing and a chunk that ignores them is about the end of one subject and the
start of another.

**Never split a table.** A benefit table means nothing row by row: the row says
"Cataract" and the column heading two lines up says "per eye, per policy year".
Splitting between them turns a qualified limit into an unqualified one, which is
worse than not reading it.

**Carry the heading into the chunk.** Whether a figure comes from the schedule
or from the wording decides which one wins when they disagree, and the heading
is usually the only thing that says which. It goes into the prompt with the text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.schemas.document import Page
from app.schemas.policy import DocumentSection

TARGET_CHARS = 2600
"""What a chunk aims for. Small enough that a free-tier model reads all of it
attentively, large enough that a clause and its qualifying sentence stay
together."""

MAX_CHARS = 4200
"""Hard ceiling. A single unsplittable block larger than this is cut anyway,
because sending it whole would be truncated at the other end instead."""

MIN_CHARS = 220
"""Below this a chunk is merged into its neighbour. A heading with two words
under it costs a model call and returns nothing."""

OVERLAP_CHARS = 240
"""Carried from the end of one chunk to the start of the next, so a limit and
the sentence qualifying it are never separated by a cut alone."""


# Headings, in the forms Indian policy documents actually use. Ordered most
# specific first: a numbered clause that is also capitalised should be read as
# a numbered clause, since the number is what the rest of the document
# cross-references.
_HEADING_PATTERNS = [
    # 4.2.1  Room Rent and Boarding Expenses
    re.compile(r"^\s{0,6}(\d{1,2}(?:\.\d{1,2}){0,3})[.)]?\s+([A-Z][^\n]{2,90})$"),
    # SECTION C - EXCLUSIONS      /      PART II: BENEFITS
    re.compile(
        r"^\s{0,6}((?:SECTION|PART|ANNEXURE|SCHEDULE|CHAPTER)\s+[IVXLC\d]+[^\n]{0,80})$",
        re.IGNORECASE,
    ),
    # WHAT IS COVERED
    re.compile(r"^\s{0,6}([A-Z][A-Z \-&/,()']{6,70})$"),
    # (a) Pre-hospitalisation expenses
    re.compile(r"^\s{0,6}\(([a-z]|[ivx]{1,4})\)\s+([A-Z][^\n]{4,90})$"),
]

# A line that is part of a table: two or more columns separated by a run of
# whitespace, or by a pipe. Rupee figures and percentages at the end of a line
# are the giveaway in a benefit table.
_TABLE_LINE = re.compile(
    r"(\S.*?(?:\s{3,}|\s*\|\s*)\S.*)|"
    r"(.*(?:₹|Rs\.?|INR)\s*[\d,]+.*)|"
    r"(.*\b\d{1,3}(?:\.\d+)?\s*%.*)",
    re.IGNORECASE,
)

# Checked against the start of a chunk. Ordered so the more specific heading
# wins: "SCHEDULE OF BENEFITS" is a benefit table, not the policy schedule,
# and the two carry different precedence when their figures disagree.
_SECTION_HINTS: list[tuple[re.Pattern[str], DocumentSection]] = [
    (re.compile(r"\b(table of benefits?|benefits? table|schedule of benefits?|"
                r"sum insured details)\b", re.IGNORECASE),
     DocumentSection.BENEFIT_TABLE),
    (re.compile(r"\b(exclusions?|not covered|we (?:will|shall) not pay|"
                r"permanent exclusions?|what is not covered)\b", re.IGNORECASE),
     DocumentSection.EXCLUSIONS),
    (re.compile(r"\b(policy schedule|schedule of insurance|certificate of "
                r"insurance|policy details)\b", re.IGNORECASE),
     DocumentSection.SCHEDULE),
    (re.compile(r"\b(endorsements?|amendment to the policy)\b", re.IGNORECASE),
     DocumentSection.ENDORSEMENT),
]


@dataclass
class Chunk:
    """One readable unit of the document, with where it came from."""

    page_index: int
    text: str
    heading: str = ""
    """The nearest heading above this text. Empty when the chunk starts mid-flow."""

    section: DocumentSection = DocumentSection.UNKNOWN
    contains_table: bool = False
    char_start: int = 0
    """Offset into the page's own text, so evidence still resolves to a page."""

    @property
    def char_count(self) -> int:
        return len(self.text.strip())

    def describe(self) -> str:
        """A one-line label for the activity log."""
        where = f"page {self.page_index + 1}"
        if self.heading:
            return f"{where}, {self.heading[:60]}"
        return where


@dataclass
class _Block:
    """A heading and the lines belonging to it, before any size limits apply."""

    heading: str
    lines: list[str] = field(default_factory=list)
    start: int = 0
    has_table: bool = False

    @property
    def text(self) -> str:
        return "\n".join(self.lines).strip()


def heading_of(line: str) -> str | None:
    """The heading this line is, or None if it is body text."""
    stripped = line.rstrip()
    if not stripped or len(stripped) > 110:
        return None
    # A line ending in a sentence full stop is prose, whatever its casing.
    if stripped.endswith((".", ";", ",")) and not re.match(r"^\s*\d", stripped):
        return None

    for pattern in _HEADING_PATTERNS:
        match = pattern.match(stripped)
        if match:
            return " ".join(part for part in match.groups() if part).strip()
    return None


def looks_like_table(line: str) -> bool:
    return bool(line.strip()) and bool(_TABLE_LINE.match(line))


def section_for(
    heading: str, body: str, fallback: DocumentSection
) -> DocumentSection:
    """Refine the page-level section using what this chunk actually says.

    A page is one section only in a tidy document. Real ones run the benefit
    table straight into the exclusions, and the precedence rules care which of
    the two a figure came from.

    The heading is consulted first and, when it says anything at all, alone. A
    body scan alone misreads a general-conditions section that happens to use
    the word "exclusions" in a cross-reference, and mislabelling wording as
    exclusions changes which clause wins a conflict.
    """
    if heading:
        for pattern, section in _SECTION_HINTS:
            if pattern.search(heading):
                return section
        # A heading that named itself something else is a stronger signal than
        # any word further down, so the body is not consulted behind it.
        return fallback

    for pattern, section in _SECTION_HINTS:
        if pattern.search(body[:300]):
            return section
    return fallback


def _blocks_of(page: Page) -> list[_Block]:
    """Group a page's lines under the headings that introduce them."""
    lines = page.text.splitlines()
    blocks: list[_Block] = []
    current = _Block(heading="")
    offset = 0

    for line in lines:
        found = heading_of(line)
        if found is not None and current.lines:
            blocks.append(current)
            current = _Block(heading=found, start=offset)
        elif found is not None:
            current.heading = found
            current.start = offset
        else:
            current.lines.append(line)
            if looks_like_table(line):
                current.has_table = True
        offset += len(line) + 1

    if current.lines:
        blocks.append(current)
    return blocks


def _split_oversized(block: _Block) -> list[str]:
    """Cut a block that is too large on its own, preferring paragraph breaks.

    A table is never cut here. Losing the column heading that qualifies a row
    is worse than one long request, so an oversized table goes whole and is
    truncated at the far end only if it exceeds the hard ceiling.
    """
    text = block.text
    if len(text) <= MAX_CHARS:
        return [text]
    if block.has_table:
        return [text[:MAX_CHARS]]

    parts: list[str] = []
    remaining = text
    while len(remaining) > MAX_CHARS:
        window = remaining[:MAX_CHARS]
        cut = max(window.rfind("\n\n"), window.rfind(". "), window.rfind("\n"))
        if cut < MIN_CHARS:
            cut = MAX_CHARS
        parts.append(remaining[:cut].strip())
        # Overlap backwards, so a sentence spanning the cut survives in one of
        # the two pieces intact.
        remaining = remaining[max(cut - OVERLAP_CHARS, 0):]
    if remaining.strip():
        parts.append(remaining.strip())
    return parts


def chunk_page(page: Page) -> list[Chunk]:
    """Cut one page into chunks that each cover a single subject."""
    if not page.text.strip():
        return []

    chunks: list[Chunk] = []
    pending: _Block | None = None

    for block in _blocks_of(page):
        if not block.text:
            continue

        # Merge a block too small to be worth its own request into the one
        # before it, unless that would push the pair past the target.
        if (
            pending is not None
            and len(block.text) < MIN_CHARS
            and len(pending.text) + len(block.text) < TARGET_CHARS
        ):
            # The merged block's heading goes in as a line. Dropping it loses
            # text from the document: a short "3. WAITING PERIODS" section
            # merged into the one above it would arrive at the model with its
            # own title missing, which is the one word saying what it is.
            if block.heading:
                pending.lines.append(block.heading)
            pending.lines.extend(block.lines)
            pending.has_table = pending.has_table or block.has_table
            continue

        if pending is not None:
            chunks.extend(_emit(pending, page))
        pending = block

    if pending is not None:
        chunks.extend(_emit(pending, page))

    return [c for c in chunks if c.char_count >= 40]


def _emit(block: _Block, page: Page) -> list[Chunk]:
    return [
        Chunk(
            page_index=page.page_index,
            text=(f"{block.heading}\n{part}" if block.heading else part),
            heading=block.heading,
            section=section_for(block.heading, part, page.section),
            contains_table=block.has_table,
            char_start=block.start,
        )
        for part in _split_oversized(block)
    ]


def chunk_document(pages: list[Page]) -> list[Chunk]:
    """Cut every page, in reading order."""
    return [chunk for page in pages for chunk in chunk_page(page)]
