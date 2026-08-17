"""Model-assisted clause extraction.

The grammar rules cover the phrasings that were anticipated. This layer exists
for the ones that were not: an insurer wording a room limit as "eligible for
accommodation up to the Single Occupancy category" carries no percentage, no
rupee figure and no keyword the rules look for, but a language model reads it
without difficulty.

What the model is *not* trusted with is the value itself. It is required to
quote the text it read, that quote is verified against the page before the
clause is admitted, and the numbers are then parsed out of the quote by the same
deterministic code the grammar rules use. So the model contributes recall and
localisation; arithmetic and interpretation stay in Python where they can be
tested.

Extraction runs per *chunk* rather than per page or per document. A page-scoped
prompt truncated anything past six thousand characters and asked the model to
hold a benefit table, an exclusions list and three sub-limits in mind at once,
which is where recall went. Chunks are cut on the document's own headings (see
`chunking.py`), so each request covers one subject, carries the heading that
says whether it is schedule or wording, and stays small enough to be read
attentively by the free-tier models this runs against.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.agents.base import LLMUnavailable
from app.agents.registry import registry
from app.core.config import ModelRole
from app.core.events import bus
from app.core.logging import get_logger
from app.pipeline.s0_intake.ocr import confidence_of_span
from app.pipeline.s2_atomize import grounding
from app.pipeline.s2_atomize import patterns as P
from app.pipeline.s2_atomize.chunking import Chunk, chunk_page
from app.schemas.document import Page
from app.schemas.events import EventStatus, PipelineStage
from app.schemas.policy import (
    Clause,
    ClauseKind,
    DocumentSection,
    Evidence,
    ExtractorKind,
)

log = get_logger(__name__)
STAGE = PipelineStage.ATOMIZE

MAX_PAGE_CHARS = 6000
MAX_WORKERS = 4

EXTRACTABLE_KINDS = [
    "sum_insured", "room_rent_cap", "icu_cap", "room_category_eligibility",
    "sublimit", "copay", "deductible", "waiting_period",
    "pre_hospitalisation", "post_hospitalisation", "consumables_cover",
    "restore_benefit", "exclusion",
]

UNITS = [
    "rupees", "percent_of_sum_insured", "percent", "days", "months",
    "room_category", "boolean", "text",
]


class ModelClause(BaseModel):
    kind: str = Field(description="One of the allowed clause kinds")
    verbatim: str = Field(description="Exact text copied from the document")
    value: str = Field(description="The value, e.g. '500000' or '1' or 'single_private'")
    unit: str = Field(description="One of the allowed units")
    condition: str = Field(
        default="",
        description=(
            "Any qualifier the document attaches to this term: per day, per eye, "
            "per policy year, after a waiting period, for insured above a given "
            "age, on a specific plan. Empty if the term is unconditional."
        ),
    )


class PageExtraction(BaseModel):
    clauses: list[ModelClause] = Field(default_factory=list)


SYSTEM = (
    "You read Indian health insurance documents and report the coverage terms "
    "they state. You never infer, estimate, or fill in what a typical policy "
    "would say. If the text does not state something, you omit it. You pay "
    "particular attention to the words around a number, because a limit and "
    "the condition attached to it are two different facts and the second is "
    "the one people miss."
)

PROMPT_TEMPLATE = """Read this extract from an Indian health insurance policy and list every coverage term it states.

Allowed values for "kind": {kinds}
Allowed values for "unit": {units}

Rules you must follow:
- "verbatim" must be copied character-for-character from the extract below. Never paraphrase, reword, or reconstruct it. It is checked against the source and discarded if it does not match.
- Report only what this extract actually states. Do not add standard or typical terms.
- "condition" carries the qualifier attached to the figure: per day, per eye, per policy year, subject to a maximum, after a waiting period, for members above a stated age, only on a named plan. A limit reported without its condition is misleading, so look for it deliberately.
- Where a figure is stated as one thing "subject to a maximum of" another, report both, as separate entries.
- For a percentage of sum insured, use unit "percent_of_sum_insured" and put just the number in "value" (e.g. "1").
- For a rupee amount, use unit "rupees" and put digits only in "value" (e.g. "500000").
- Do not report the premium, GST, or agent code. Those are not coverage terms.
- If the extract states no coverage terms, return an empty list.

{where}
{page_text}
"""


def _params_for(clause: ModelClause) -> dict[str, Any] | None:
    """Turn a model's value and unit into typed parameters.

    Values are re-parsed from the quoted text wherever possible, so the figure
    that reaches the ledger is the one on the page rather than the one the model
    typed into its own answer.
    """
    kind = clause.kind
    unit = clause.unit
    raw = clause.value.strip()

    if unit == "rupees":
        amount = P.parse_amount(clause.verbatim) or P.parse_amount(f"Rs. {raw}")
        if amount is None:
            return None
        if kind in ("room_rent_cap", "icu_cap"):
            return {"basis": "flat", "amount_inr": str(amount),
                    "per_day": P.is_per_day(clause.verbatim)}
        return {"amount_inr": str(amount)}

    if unit == "percent_of_sum_insured":
        pct = P.parse_pct_of_sum_insured(clause.verbatim) or _decimal(raw)
        if pct is None:
            return None
        if kind in ("room_rent_cap", "icu_cap"):
            return {"basis": "pct_of_si", "pct_of_si": str(pct)}
        return {"pct_of_si": str(pct)}

    if unit == "percent":
        pct = P.parse_percent(clause.verbatim) or _decimal(raw)
        return {"pct": str(pct)} if pct is not None else None

    if unit == "days":
        days = P.parse_days(clause.verbatim) or _int(raw)
        return {"days": days} if days is not None else None

    if unit == "months":
        months = P.parse_months(clause.verbatim) or _int(raw)
        return {"months": months, "applies_to": "unspecified"} if months else None

    if unit == "room_category":
        category = P.parse_room_category(clause.verbatim) or P.parse_room_category(raw)
        return {"basis": "category", "category": category} if category else None

    if unit == "boolean":
        return {"covered": raw.strip().lower() in ("true", "yes", "covered", "1")}

    if unit == "text":
        # Free text is only a value for clauses that genuinely are text. For a
        # limit it means the model recognised the label and failed to read the
        # figure, and admitting it produces a clause that looks like an answer,
        # carries nothing usable, and displaces the correct reading.
        if kind == "exclusion":
            return {"text": clause.verbatim}
        # A room entitlement stated as a category is still recoverable.
        if kind in ("room_rent_cap", "room_category_eligibility", "icu_cap"):
            if category := P.parse_room_category(clause.verbatim):
                return {"basis": "category", "category": category}
            if P.states_no_limit(clause.verbatim):
                return {"basis": "no_limit"}
        return None

    return None


def _decimal(raw: str) -> Decimal | None:
    try:
        return Decimal(raw.replace("%", "").replace(",", "").strip())
    except Exception:
        return None


def _int(raw: str) -> int | None:
    try:
        return int(float(raw.replace(",", "").strip()))
    except Exception:
        return None


def extract_page(page: Page, *, session_id: str | None = None) -> list[Clause]:
    """Read one page as a single unit. Kept for callers that want no chunking."""
    text = page.text.strip()
    if len(text) < 60:
        return []
    return _extract_text(
        text[:MAX_PAGE_CHARS], page,
        where=f"PAGE {page.page_index + 1}:",
        label=f"Page {page.page_index + 1}",
        session_id=session_id,
    )


def extract_chunk(chunk: Chunk, page: Page, *, session_id: str | None = None) -> list[Clause]:
    """Read one chunk of a page, told where in the document it sits.

    The heading goes into the prompt with the text. Whether a figure came from
    the schedule or from the wording decides which one wins when they disagree,
    and on a real document the heading is the only thing that says which.
    """
    if chunk.char_count < 60:
        return []

    where = f"EXTRACT FROM PAGE {chunk.page_index + 1}"
    if chunk.heading:
        where += f", UNDER THE HEADING: {chunk.heading}"
    if chunk.contains_table:
        where += (
            "\nThis extract contains a table. A row's meaning depends on its "
            "column heading, so read the headings before the rows."
        )

    return _extract_text(
        chunk.text[:MAX_PAGE_CHARS], page,
        where=where + ":",
        label=chunk.describe(),
        session_id=session_id,
        section=chunk.section,
    )


def _extract_text(
    text: str,
    page: Page,
    *,
    where: str,
    label: str,
    session_id: str | None,
    section: DocumentSection | None = None,
) -> list[Clause]:
    """Ask a model to read some text, then admit only what it can prove."""
    prompt = PROMPT_TEMPLATE.format(
        kinds=", ".join(EXTRACTABLE_KINDS),
        units=", ".join(UNITS),
        where=where,
        page_text=text,
    )

    try:
        extraction = registry.complete_structured(
            ModelRole.EXTRACT, prompt=prompt, schema=PageExtraction,
            system=SYSTEM, temperature=0.0,
        )
    except LLMUnavailable as exc:
        bus.publish(
            STAGE, "model_extract", status=EventStatus.SKIPPED,
            summary="No model available; using the rule-based extractor only",
            session_id=session_id, page=page.page_index, reason=str(exc)[:160],
        )
        return []

    admitted: list[Clause] = []
    rejected = 0

    for candidate in extraction.clauses:
        try:
            kind = ClauseKind(candidate.kind)
        except ValueError:
            rejected += 1
            continue

        # Grounded against the whole page, not the chunk. A model quoting one
        # word past a chunk boundary is still quoting the document, and
        # rejecting that would punish the split rather than the model.
        result = grounding.check(candidate.verbatim, page.text)
        if not result.grounded:
            # The defining guarantee: unprovable text never enters the ledger.
            rejected += 1
            log.debug(
                "rejected ungrounded clause", kind=candidate.kind,
                quote=candidate.verbatim[:70], reason=result.reason,
            )
            continue

        params = _params_for(candidate)
        if not params:
            rejected += 1
            continue

        verbatim = grounding.find_in_page(candidate.verbatim, page.text) or candidate.verbatim
        admitted.append(
            Clause(
                kind=kind,
                verbatim=P.normalise_whitespace(verbatim),
                evidence=Evidence(
                    page_index=page.page_index,
                    bbox=page.bbox_for_span(verbatim),
                    section=section or page.section,
                    ocr_confidence=confidence_of_span(page.words, verbatim),
                ),
                params=params,
                # The qualifier attached to the figure. A sub-limit reported
                # without its "per eye" or "per policy year" is a different,
                # and more generous, term than the one the document states.
                notes=candidate.condition.strip()[:200],
                # Capped below the grammar rules' ceiling: a model finding is a
                # lead to be verified, not a settled fact.
                confidence=round(0.70 * result.score, 3),
                extracted_by=ExtractorKind.MODEL,
            )
        )

    bus.publish(
        STAGE, "model_extract", session_id=session_id,
        summary=(
            f"{label}: model proposed {len(extraction.clauses)}, "
            f"{len(admitted)} backed by the document, {rejected} discarded"
        ),
        page=page.page_index,
        proposed=len(extraction.clauses),
        admitted=len(admitted),
        rejected=rejected,
    )
    return admitted


MAX_CHUNKS = 90
"""Ceiling on model calls for one document. A hundred-page wording would
otherwise cost a hundred requests and several minutes, and the terms that
matter are not evenly spread through it. Beyond this the chunks carrying the
most figures are read and the rest are left to the grammar rules, which is
stated in the activity log rather than done quietly."""


def _priority(chunk: Chunk) -> tuple[int, int]:
    """Which chunks to read first when a document is too long to read whole.

    Ordered by what the section is worth, then by how many figures it carries.
    A schedule holds this policyholder's actual numbers and is worth reading
    before a definitions page that holds none.
    """
    figures = len(re.findall(r"(?:₹|Rs\.?|INR)\s*[\d,]+|\d+(?:\.\d+)?\s*%", chunk.text))
    return (-chunk.section.precedence, -figures)


def extract_pages(pages: list[Page], *, session_id: str | None = None) -> list[Clause]:
    """Chunk every page, then read each chunk on its own, concurrently.

    Reading a whole page in one request truncated anything past six thousand
    characters and asked the model to hold a benefit table, an exclusions list
    and three sub-limits in mind at once. Chunking costs more requests and
    finds considerably more, which is the right trade for the one step that
    everything downstream depends on.

    Cloud calls take tens of seconds each on the free tier, so chunks are read
    in parallel; a forty-page wording would otherwise take an hour.
    """
    if not pages:
        return []

    by_page = {page.page_index: page for page in pages}
    chunks = [chunk for page in pages for chunk in chunk_page(page)]
    if not chunks:
        return []

    selected = chunks
    if len(chunks) > MAX_CHUNKS:
        selected = sorted(chunks, key=_priority)[:MAX_CHUNKS]
        bus.publish(
            STAGE, "chunk_document", status=EventStatus.WARN, session_id=session_id,
            summary=(
                f"This document splits into {len(chunks)} sections, more than "
                f"we read in one pass. Reading the {MAX_CHUNKS} most likely to "
                f"carry your cover terms."
            ),
            chunks=len(chunks), read=MAX_CHUNKS,
        )
    else:
        bus.publish(
            STAGE, "chunk_document", session_id=session_id,
            summary=(
                f"Split into {len(chunks)} section"
                f"{'s' if len(chunks) != 1 else ''} to read one at a time"
            ),
            chunks=len(chunks),
        )

    def read(chunk: Chunk) -> list[Clause]:
        page = by_page.get(chunk.page_index)
        if page is None:
            return []
        return extract_chunk(chunk, page, session_id=session_id)

    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(selected))) as pool:
        results = pool.map(read, selected)
    return [clause for chunk_clauses in results for clause in chunk_clauses]
