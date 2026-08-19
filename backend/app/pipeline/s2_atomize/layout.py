"""Rebuild a page's visual rows from where the words actually sit.

A benefit table is read by eye as rows: the label on the left, the figure it
governs on the same line to the right. OCR does not have to hand it back that
way. Tesseract segments a page into blocks and reads each block through, so a
two-column table often comes out as every label in order, then every value in
order, tens of lines apart:

    Sum Insured (per policy year)
    Room Rent Limit
    Intensive Care Unit (ICU) Limit
    Co-payment
    ...
    Rs. 3,00,000/-
    1% of Sum Insured per day, subject to a maximum of Rs. 5,000/- per day
    Rs. 10,000/- per day
    20% of each and every admissible claim

Read as text, "Room Rent Limit" is followed by "Intensive Care Unit (ICU)
Limit". Every rule that looks for a label and then its value finds a label and
then another label, and the whole schedule is lost. That is not a rare case: on
this corpus it is what a photographed policy looks like.

The obvious repair is to search further down the page, and it is the wrong one.
Widening the window means the room-rent rule eventually reaches a figure, and
the figure it reaches is the ICU limit. A silently wrong room cap is worse than
a missing one: the missing one becomes a question, and the wrong one becomes a
proportionate deduction nobody checks.

The information needed to do it properly is already on the page. Every word
carries the box it was recognised in, so the rows can be rebuilt from the
geometry that OCR flattened: group words whose vertical centres fall in the
same band, order each band left to right, and the table reads the way it looks.

This runs as a fallback rather than a replacement. A native PDF's own text
layer already has the row structure and is trusted first; these rows are
consulted only where reading the page as text found nothing at all.
"""

from __future__ import annotations

from app.schemas.document import Page, Word

MIN_WORDS = 12
"""Below this there is no table to rebuild and the flat text is as good."""

BAND_FRACTION = 0.6
"""How much of a word's own height it may sit off a row's centre and still
belong to it. Generous enough for a baseline that drifts across a photographed
page, tight enough that adjacent table rows stay apart."""

COLUMN_GAP_CHARS = 6.0
"""A horizontal gap wider than this many median character widths reads as a
column boundary rather than a word space, and is rendered as one. A word space
is about one character wide; the gutter between the label column and the value
column of a benefit table is many."""


def _centre(word: Word) -> float:
    return (word.bbox.y0 + word.bbox.y1) / 2


def _height(word: Word) -> float:
    return max(word.bbox.y1 - word.bbox.y0, 1.0)


def _rows(words: list[Word]) -> list[list[Word]]:
    """Group words into visual rows by vertical position."""
    ordered = sorted(words, key=_centre)
    rows: list[list[Word]] = []
    band_centre = None
    band_tolerance = 0.0

    for word in ordered:
        centre = _centre(word)
        if band_centre is None or abs(centre - band_centre) > band_tolerance:
            rows.append([word])
            band_centre = centre
            band_tolerance = _height(word) * BAND_FRACTION
            continue
        rows[-1].append(word)
        # The running centre follows the row, so a line that slopes across a
        # photographed page does not fall out of its own band halfway along.
        band_centre = sum(_centre(w) for w in rows[-1]) / len(rows[-1])
        band_tolerance = max(band_tolerance, _height(word) * BAND_FRACTION)

    return [sorted(row, key=lambda w: w.bbox.x0) for row in rows]


def _render(row: list[Word]) -> str:
    """One row as text, with column gaps kept as gaps."""
    widths = sorted(
        (w.bbox.x1 - w.bbox.x0) / max(len(w.text), 1) for w in row if w.text
    )
    char_width = widths[len(widths) // 2] if widths else 1.0
    gap_limit = char_width * COLUMN_GAP_CHARS

    parts: list[str] = []
    previous: Word | None = None
    for word in row:
        if previous is not None and word.bbox.x0 - previous.bbox.x1 > gap_limit:
            # Wide enough to be the next column. Kept as a run of spaces so a
            # label and its value stay distinguishable to anything that cares,
            # and read as ordinary whitespace to anything that does not.
            parts.append("   ")
        elif previous is not None:
            parts.append(" ")
        parts.append(word.text)
        previous = word
    return "".join(parts).strip()


def rows_text(page: Page) -> str:
    """The page read as visual rows, or empty when there is nothing to rebuild.

    Only for pages that came through OCR. A native text layer already carries
    the line structure the publisher intended, and rebuilding it from glyph
    positions can only lose to it.
    """
    if page.source_mode.value != "ocr" or len(page.words) < MIN_WORDS:
        return ""
    if not all(w.bbox for w in page.words):
        return ""
    return "\n".join(line for row in _rows(page.words) if (line := _render(row)))
