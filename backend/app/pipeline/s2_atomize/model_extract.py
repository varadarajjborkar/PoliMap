"""Model-assisted clause extraction.

The grammar rules cover the phrasings that were anticipated. This layer exists
for the ones that were not — an insurer wording a room limit as "eligible for
accommodation up to the Single Occupancy category" carries no percentage, no
rupee figure and no keyword the rules look for, but a language model reads it
without difficulty.

What the model is *not* trusted with is the value itself. It is required to
quote the text it read, that quote is verified against the page before the
clause is admitted, and the numbers are then parsed out of the quote by the same
deterministic code the grammar rules use. So the model contributes recall and
localisation; arithmetic and interpretation stay in Python where they can be
tested.

Extraction runs per page rather than per document. A page-scoped prompt cannot
attribute a figure from the wording to the schedule, and it keeps each request
small enough to stay accurate on the free-tier models this runs against.
"""

from __future__ import annotations

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
from app.schemas.document import Page
from app.schemas.events import EventStatus, PipelineStage
from app.schemas.policy import Clause, ClauseKind, Evidence, ExtractorKind

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


class PageExtraction(BaseModel):
    clauses: list[ModelClause] = Field(default_factory=list)


SYSTEM = (
    "You read Indian health insurance documents and report the coverage terms "
    "they state. You never infer, estimate, or fill in what a typical policy "
    "would say. If the page does not state something, you omit it."
)

PROMPT_TEMPLATE = """Read this page of an Indian health insurance policy and list every coverage term it states.

Allowed values for "kind": {kinds}
Allowed values for "unit": {units}

Rules you must follow:
- "verbatim" must be copied character-for-character from the page below. Never paraphrase, reword, or reconstruct it. It is checked against the page and discarded if it does not match.
- Report only what this page actually states. Do not add standard or typical terms.
- For a percentage of sum insured, use unit "percent_of_sum_insured" and put just the number in "value" (e.g. "1").
- For a rupee amount, use unit "rupees" and put digits only in "value" (e.g. "500000").
- Do not report the premium, GST, or agent code. Those are not coverage terms.
- If the page states no coverage terms, return an empty list.

PAGE {page_number}:
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
        return {"text": clause.verbatim}

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
    """Ask a model to read one page, then admit only what it can prove."""
    text = page.text.strip()
    if len(text) < 60:
        return []

    prompt = PROMPT_TEMPLATE.format(
        kinds=", ".join(EXTRACTABLE_KINDS),
        units=", ".join(UNITS),
        page_number=page.page_index + 1,
        page_text=text[:MAX_PAGE_CHARS],
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
                    section=page.section,
                    ocr_confidence=confidence_of_span(page.words, verbatim),
                ),
                params=params,
                # Capped below the grammar rules' ceiling: a model finding is a
                # lead to be verified, not a settled fact.
                confidence=round(0.70 * result.score, 3),
                extracted_by=ExtractorKind.MODEL,
            )
        )

    bus.publish(
        STAGE, "model_extract", session_id=session_id,
        summary=(
            f"Page {page.page_index + 1}: model proposed {len(extraction.clauses)}, "
            f"{len(admitted)} backed by the page, {rejected} discarded"
        ),
        page=page.page_index,
        proposed=len(extraction.clauses),
        admitted=len(admitted),
        rejected=rejected,
    )
    return admitted


def extract_pages(pages: list[Page], *, session_id: str | None = None) -> list[Clause]:
    """Extract across pages concurrently.

    Cloud calls take tens of seconds each on the free tier, so pages are read in
    parallel; a five-page document would otherwise take minutes.
    """
    if not pages:
        return []
    if len(pages) == 1:
        return extract_page(pages[0], session_id=session_id)

    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(pages))) as pool:
        results = pool.map(lambda p: extract_page(p, session_id=session_id), pages)
    return [clause for page_clauses in results for clause in page_clauses]
