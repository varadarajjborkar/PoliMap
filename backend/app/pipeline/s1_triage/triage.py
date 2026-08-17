"""Stage 1: work out what each page is before reading anything off it.

This stage looks slight and carries a lot of weight. A policy *schedule* holds
the figures belonging to this specific policyholder; policy *wording* holds
generic terms that may describe a standard plan the customer did not buy. Both
say "Room Rent Limit" and both quote a rupee figure, so an extractor that treats
the document as one flat body of text will sometimes lift the wording's number
and report it with total confidence.

The generated corpus contains policies that contradict themselves precisely so
this failure is reachable in testing: the schedule states one room limit and the
wording states another. Labelling the section is what lets the compile stage
resolve that by precedence, schedule over wording, endorsement over both,
without ever bothering the user.

Classification is deliberately keyword and structure based rather than
model-based. It is cheap, it runs offline, and being wrong here is expensive, so
predictability is worth more than cleverness.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.events import bus
from app.schemas.document import IngestedDocument, Page
from app.schemas.events import EventStatus, PipelineStage
from app.schemas.policy import DocumentSection

STAGE = PipelineStage.TRIAGE


@dataclass
class SectionSignal:
    section: DocumentSection
    patterns: list[re.Pattern[str]]
    weight: float = 1.0
    hits: int = field(default=0, init=False)


def _compile(*patterns: str) -> list[re.Pattern[str]]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


# Markers that identify a section. Headings score higher than passing mentions
# because a heading is a structural claim about the page, not a coincidence.
SECTION_MARKERS: list[SectionSignal] = [
    SectionSignal(
        DocumentSection.SCHEDULE,
        _compile(
            r"policy\s+schedule",
            r"schedule\s+of\s+(?:benefits|insurance)",
            r"certificate\s+of\s+insurance",
            r"insured\s+persons?",
            r"premium\s+details",
            r"intermediary\s+code",
            r"date\s+of\s+issue",
        ),
        weight=2.0,
    ),
    SectionSignal(
        DocumentSection.BENEFIT_TABLE,
        _compile(
            r"schedule\s+of\s+benefits",
            r"benefit\s*/?\s*limit",
            r"sub[- ]?limits?",
            r"table\s+of\s+benefits",
        ),
        weight=1.2,
    ),
    SectionSignal(
        DocumentSection.WORDING,
        _compile(
            r"policy\s+wording",
            r"terms\s+and\s+conditions",
            r"\bdefinitions?\b",
            r"\bmeans\b\s+the",
            r"general\s+conditions",
            r"claim\s+procedure",
            r"the\s+company\s+shall",
        ),
        weight=1.5,
    ),
    SectionSignal(
        DocumentSection.EXCLUSIONS,
        _compile(
            r"permanent\s+exclusions?",
            r"\bexclusions?\b",
            r"shall\s+not\s+be\s+liable",
            r"not\s+covered\s+under\s+this\s+policy",
        ),
        weight=1.3,
    ),
    SectionSignal(
        DocumentSection.ENDORSEMENT,
        _compile(
            r"\bendorsement\b",
            r"endorsement\s+schedule",
            r"policy\s+alteration",
            r"revised\s+schedule",
        ),
        weight=2.5,
    ),
]

# A health card is not a section but it changes what may be believed: it carries
# a handful of headline figures and none of the terms.
CARD_MARKERS = _compile(
    r"health\s+(?:insurance\s+)?(?:identity\s+)?card",
    r"member\s+name",
    r"valid\s+up\s*to",
)

# Fields whose presence marks a page as carrying this policyholder's own data
# rather than boilerplate.
PERSONALISED_MARKERS = _compile(
    r"policy\s*(?:no\.?|number)",
    r"policyholder\s+name",
    r"\bUIN\b",
    r"policy\s+period",
    r"sum\s+insured",
)


def classify_page(page: Page) -> tuple[DocumentSection, float]:
    """Label a page's section and report how strongly it was indicated."""
    text = page.text
    if not text.strip():
        return DocumentSection.UNKNOWN, 0.0

    scores: dict[DocumentSection, float] = {}
    for signal in SECTION_MARKERS:
        hits = sum(1 for pattern in signal.patterns if pattern.search(text))
        if hits:
            scores[signal.section] = scores.get(signal.section, 0.0) + hits * signal.weight

    if not scores:
        return DocumentSection.UNKNOWN, 0.0

    # A page carrying the policyholder's own identifiers is a schedule even when
    # it also quotes standard terms, which schedules routinely do.
    personalised = sum(1 for p in PERSONALISED_MARKERS if p.search(text))
    if personalised >= 3:
        scores[DocumentSection.SCHEDULE] = scores.get(DocumentSection.SCHEDULE, 0.0) + 3.0

    best = max(scores, key=lambda s: scores[s])
    total = sum(scores.values())
    return best, round(scores[best] / total, 3) if total else 0.0


def is_card(page: Page) -> bool:
    return sum(1 for p in CARD_MARKERS if p.search(page.text)) >= 2


INSURER_NAME_RE = re.compile(
    r"^([A-Z][A-Za-z&.\- ]{4,48}?"
    r"(?:INSURANCE|ASSURANCE|HEALTH|GENERAL INSURANCE))\b",
    re.MULTILINE,
)


def detect_insurer(document: IngestedDocument) -> str:
    """Read the insurer's name off the document.

    Matched on the letterhead rather than against a list of known insurers, so
    an insurer the system has never seen is still identified.
    """
    for page in document.pages[:2]:
        for line in page.text.splitlines()[:12]:
            candidate = line.strip()
            if not candidate or len(candidate) > 60:
                continue
            match = INSURER_NAME_RE.match(candidate)
            if match:
                return match.group(1).strip().title()
    return ""


def triage(document: IngestedDocument) -> IngestedDocument:
    """Label every page in place and report what was found."""
    with bus.step(
        STAGE, "classify_pages", session_id=document.session_id,
        summary=f"Working out what {document.filename} contains",
    ) as step:
        labels: dict[str, int] = {}
        for page in document.pages:
            section, confidence = classify_page(page)
            if is_card(page):
                # A card carries headline figures without the terms behind them,
                # so it is treated as schedule-grade for the fields it does show.
                section = DocumentSection.SCHEDULE
            page.section = section
            labels[section.value] = labels.get(section.value, 0) + 1

        insurer = detect_insurer(document)
        has_schedule = any(
            p.section in (DocumentSection.SCHEDULE, DocumentSection.BENEFIT_TABLE)
            for p in document.pages
        )

        if not has_schedule:
            step.warn(
                "No policy schedule found, figures may come from standard terms "
                "rather than this policy",
                sections=labels, insurer=insurer or None,
            )
            document.warnings.append(
                "We could not find a policy schedule in this document. "
                "Any figures shown may be standard terms rather than yours."
            )
        else:
            step.ok(
                f"{document.filename}: "
                + ", ".join(f"{n} {s}" for s, n in sorted(labels.items()))
                + (f", {insurer}" if insurer else ""),
                sections=labels, insurer=insurer or None,
            )

    return document


def schedule_pages(document: IngestedDocument) -> list[Page]:
    """Pages holding this policyholder's own figures, best first."""
    ranked = sorted(
        document.pages,
        key=lambda p: (
            -p.section.precedence,
            p.page_index,
        ),
    )
    return [p for p in ranked if p.section is not DocumentSection.UNKNOWN] or document.pages
