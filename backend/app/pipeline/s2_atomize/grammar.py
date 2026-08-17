"""Deterministic clause extraction from Indian policy documents.

This is the pipeline's floor. It runs with no model, no key and no network, and
its behaviour is fully predictable — which matters, because a system that gives
a family a number about their own money should not depend entirely on something
that can hallucinate. The language model layer widens recall on phrasings these
rules do not know; it does not replace them, and where the two disagree the
verification loop has to settle it on evidence.

Layout is the main difficulty. Policy schedules are tables, and a table read
back as text puts the label and its value on separate lines:

    Room Rent Limit
    1% of Sum Insured per day, subject to a maximum of Rs. 5,000 per day

So rules match a label, then search a short window of following lines for a
value. The window is deliberately small: widen it and a label starts capturing
the next row's figure, which produces a confident, well-formed, wrong answer.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.pipeline.s2_atomize import patterns as P
from app.schemas.document import Page
from app.schemas.policy import (
    Clause,
    ClauseKind,
    DocumentSection,
    Evidence,
    ExpenseHead,
    ExtractorKind,
)

VALUE_WINDOW = 2
"""Lines after a label that may hold its value."""

MIN_PLAUSIBLE_SUM_INSURED = Decimal(25000)
MAX_PLAUSIBLE_SUM_INSURED = Decimal(100000000)
MAX_PLAUSIBLE_ROOM_RATE = Decimal(200000)


@dataclass
class LabelledMatch:
    label: str
    value_text: str
    verbatim: str
    line_index: int
    same_line: bool


def _lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines()]


def find_labelled(
    text: str,
    label_re: re.Pattern[str],
    *,
    window: int = VALUE_WINDOW,
    value_test: Callable[[str], bool] | None = None,
) -> list[LabelledMatch]:
    """Locate `label_re`, then find its value on the same line or just below."""
    results: list[LabelledMatch] = []
    lines = _lines(text)

    for i, line in enumerate(lines):
        match = label_re.search(line)
        if not match:
            continue

        # Prefer a value on the same line, after the label.
        tail = line[match.end():].strip(" :\t|-")
        if tail and (value_test is None or value_test(tail)):
            results.append(
                LabelledMatch(match.group(0), tail, line, i, same_line=True)
            )
            continue

        for offset in range(1, window + 1):
            if i + offset >= len(lines):
                break
            candidate = lines[i + offset].strip()
            if not candidate:
                continue
            if value_test is None or value_test(candidate):
                results.append(
                    LabelledMatch(
                        match.group(0), candidate,
                        f"{line} {candidate}".strip(), i, same_line=False,
                    )
                )
            # Stop at the first non-empty line whether or not it matched:
            # anything further belongs to the next table row.
            break

    return results


def _has_amount(text: str) -> bool:
    return P.parse_amount(text) is not None


def _has_amount_or_pct(text: str) -> bool:
    return (
        P.parse_amount(text) is not None
        or P.parse_percent(text) is not None
        or P.parse_room_category(text) is not None
        or P.states_no_limit(text)
    )


def _has_percent(text: str) -> bool:
    return P.parse_percent(text) is not None or P.states_no_limit(text)


# --- label patterns -------------------------------------------------------

SUM_INSURED_RE = re.compile(
    r"\b(?:sum\s+insured|sum\s+assured|basic\s+sum\s+insured|"
    r"coverage\s+amount|total\s+sum\s+insured)\b"
    # Must not be the restoration or cumulative-bonus row, which also say
    # "sum insured" but carry a different figure.
    r"(?!\s*(?:restor|reinstat|recharge|bonus))",
    re.IGNORECASE,
)

ROOM_RENT_RE = re.compile(
    r"\b(?:room\s+rent|room\s+charges?|room\s+categor\w*|"
    r"accommodation\s+charges?|daily\s+room\s+rent|room\s+eligibilit\w*|"
    r"room\s+entitlement)\b",
    re.IGNORECASE,
)

ICU_RE = re.compile(
    r"\b(?:i\.?c\.?u\.?|intensive\s+care(?:\s+unit)?|critical\s+care)\b",
    re.IGNORECASE,
)

COPAY_RE = re.compile(
    r"\b(?:co[- ]?pay(?:ment)?|co[- ]?insurance|copay)\b", re.IGNORECASE
)

DEDUCTIBLE_RE = re.compile(r"\bdeductible\b", re.IGNORECASE)

PRE_HOSP_RE = re.compile(r"\bpre[- ]?hospitali[sz]ation\b", re.IGNORECASE)
POST_HOSP_RE = re.compile(r"\bpost[- ]?hospitali[sz]ation\b", re.IGNORECASE)

WAITING_RE = re.compile(r"\bwaiting\s+period\b", re.IGNORECASE)

CONSUMABLES_RE = re.compile(
    r"\b(?:non[- ]?medical\s+consumables?|consumables?)\b", re.IGNORECASE
)
RESTORE_RE = re.compile(
    r"\b(?:restorat\w*|reinstate\w*|recharge)\b(?:\s+of\s+sum\s+insured)?",
    re.IGNORECASE,
)

POLICY_NUMBER_RE = re.compile(r"\bpolicy\s*(?:no\.?|number)\b", re.IGNORECASE)
POLICYHOLDER_RE = re.compile(
    r"\b(?:policyholder\s*name|name\s+of\s+(?:the\s+)?(?:insured|policyholder))\b",
    re.IGNORECASE,
)
UIN_RE = re.compile(r"\bUIN\b", re.IGNORECASE)

# Sub-limit rows, keyed by the expense head they cap.
SUBLIMIT_HEADS: list[tuple[re.Pattern[str], ExpenseHead, str]] = [
    (re.compile(r"\b(?:diagnostic|investigation|patholog|radiolog|lab\s+test)\w*\b",
                re.IGNORECASE), ExpenseHead.INVESTIGATIONS, "Tests and scans"),
    (re.compile(r"\bambulance\b", re.IGNORECASE), ExpenseHead.AMBULANCE, "Ambulance"),
    (re.compile(r"\b(?:pharmacy|medicines?|drugs?)\b", re.IGNORECASE),
     ExpenseHead.PHARMACY, "Medicines"),
    (re.compile(r"\bimplants?\b", re.IGNORECASE), ExpenseHead.IMPLANTS, "Implants"),
    (re.compile(r"\bnursing\b", re.IGNORECASE), ExpenseHead.NURSING, "Nursing"),
]


# --- extraction -----------------------------------------------------------


# Wording that explicitly defers to the schedule. A clause saying "unless
# otherwise specified in the Schedule" is describing a default the customer may
# never have been sold, so it must not be reported as their entitlement.
HEDGE_RE = re.compile(
    r"unless\s+otherwise\s+(?:specified|stated|provided)|"
    r"standard\s+plan|"
    r"subject\s+to\s+the\s+(?:terms\s+of\s+the\s+)?schedule|"
    r"as\s+(?:may\s+be\s+)?(?:specified|stated)\s+in\s+the\s+schedule|"
    r"where\s+applicable|by\s+way\s+of\s+(?:an\s+)?example|for\s+(?:example|instance)",
    re.IGNORECASE,
)

WORDING_PENALTY = 0.25
HEDGE_PENALTY = 0.40


def _confidence_for(base: float, verbatim: str, section: DocumentSection) -> float:
    """Discount a finding by how much authority its source really carries.

    Generic wording is not this policyholder's schedule, and wording that points
    at the schedule for the real figure carries almost none. Without this, an
    unreadable schedule page lets a boilerplate default become the answer — the
    system reports a number nobody was ever sold, and reports it confidently.
    """
    confidence = base
    if section is DocumentSection.WORDING:
        confidence -= WORDING_PENALTY
    if HEDGE_RE.search(verbatim):
        confidence -= HEDGE_PENALTY
    return round(max(confidence, 0.05), 3)


def _clause(
    kind: ClauseKind,
    verbatim: str,
    page: Page,
    *,
    params: dict[str, Any],
    confidence: float,
    section: DocumentSection | None = None,
    scope: dict[str, Any] | None = None,
) -> Clause:
    from app.pipeline.s0_intake.ocr import confidence_of_span

    verbatim = P.normalise_whitespace(verbatim)
    resolved_section = section or page.section
    adjusted = _confidence_for(confidence, verbatim, resolved_section)

    clause = Clause(
        kind=kind,
        verbatim=verbatim,
        evidence=Evidence(
            page_index=page.page_index,
            bbox=page.bbox_for_span(verbatim),
            section=resolved_section,
            ocr_confidence=confidence_of_span(page.words, verbatim),
        ),
        params=params,
        scope=scope or {},
        confidence=adjusted,
        extracted_by=ExtractorKind.GRAMMAR,
    )
    if adjusted < confidence:
        clause.notes.append(
            "Found in the policy wording rather than your schedule, "
            "so it may describe a standard plan rather than yours"
        )
    return clause


def extract_sum_insured(page: Page) -> list[Clause]:
    """The cover amount.

    The premium block sits directly below this row on a real schedule and is the
    most common wrong answer, so candidates are range-checked and the label
    pattern explicitly refuses restoration and bonus rows.
    """
    clauses: list[Clause] = []
    for match in find_labelled(page.text, SUM_INSURED_RE, value_test=_has_amount):
        amount = P.parse_amount(match.value_text)
        if amount is None:
            continue
        if not (MIN_PLAUSIBLE_SUM_INSURED <= amount <= MAX_PLAUSIBLE_SUM_INSURED):
            continue
        clauses.append(
            _clause(
                ClauseKind.SUM_INSURED, match.verbatim, page,
                params={"amount_inr": str(amount)},
                confidence=0.88 if match.same_line else 0.80,
            )
        )
    return clauses


def _room_params(value_text: str) -> dict[str, Any] | None:
    """Interpret a room-limit value in any of the forms policies use."""
    if P.states_no_limit(value_text):
        return {"basis": "no_limit"}

    pct = P.parse_pct_of_sum_insured(value_text)
    # Anchored on the "subject to a maximum of" wording, so the ceiling is read
    # rather than whichever figure happens to come first or last.
    amount = P.parse_capped_amount(value_text) if pct is not None else P.parse_amount(value_text)
    category = P.parse_room_category(value_text)

    if pct is not None and amount is not None:
        # "1% of Sum Insured, subject to a maximum of Rs. 5,000" — both bind,
        # and the lower one wins at evaluation time.
        return {
            "basis": "pct_with_max",
            "pct_of_si": str(pct),
            "amount_inr": str(amount),
        }
    if pct is not None:
        return {"basis": "pct_of_si", "pct_of_si": str(pct)}
    if amount is not None and amount <= MAX_PLAUSIBLE_ROOM_RATE:
        return {"basis": "flat", "amount_inr": str(amount), "per_day": P.is_per_day(value_text)}
    if category is not None:
        return {"basis": "category", "category": category}
    return None


def extract_room_limit(page: Page) -> list[Clause]:
    clauses: list[Clause] = []
    for match in find_labelled(page.text, ROOM_RENT_RE, value_test=_has_amount_or_pct):
        # ICU rows also mention charges; they are handled by their own rule.
        if ICU_RE.search(match.label):
            continue
        params = _room_params(match.value_text)
        if params is None:
            continue
        kind = (
            ClauseKind.ROOM_CATEGORY_ELIGIBILITY
            if params["basis"] == "category"
            else ClauseKind.ROOM_RENT_CAP
        )
        clauses.append(
            _clause(
                kind, match.verbatim, page,
                params=params,
                confidence=0.86 if match.same_line else 0.78,
            )
        )
    return clauses


def extract_icu_limit(page: Page) -> list[Clause]:
    clauses: list[Clause] = []
    for match in find_labelled(page.text, ICU_RE, value_test=_has_amount_or_pct):
        params = _room_params(match.value_text)
        if params is None:
            continue
        clauses.append(
            _clause(
                ClauseKind.ICU_CAP, match.verbatim, page,
                params=params,
                confidence=0.84 if match.same_line else 0.76,
            )
        )
    return clauses


def extract_copay(page: Page) -> list[Clause]:
    clauses: list[Clause] = []
    for match in find_labelled(page.text, COPAY_RE, value_test=_has_percent):
        if P.states_no_limit(match.value_text):
            pct = Decimal(0)
        else:
            pct = P.parse_percent(match.value_text)
        if pct is None or pct > 100:
            continue
        clauses.append(
            _clause(
                ClauseKind.COPAY, match.verbatim, page,
                params={"pct": str(pct)},
                confidence=0.85 if match.same_line else 0.76,
            )
        )
    return clauses


def extract_deductible(page: Page) -> list[Clause]:
    clauses: list[Clause] = []
    for match in find_labelled(page.text, DEDUCTIBLE_RE, value_test=_has_amount):
        amount = P.parse_amount(match.value_text)
        if amount is None:
            continue
        clauses.append(
            _clause(
                ClauseKind.DEDUCTIBLE, match.verbatim, page,
                params={"amount_inr": str(amount)},
                confidence=0.85 if match.same_line else 0.76,
            )
        )
    return clauses


def extract_hospitalisation_windows(page: Page) -> list[Clause]:
    clauses: list[Clause] = []
    for label_re, kind in (
        (PRE_HOSP_RE, ClauseKind.PRE_HOSPITALISATION),
        (POST_HOSP_RE, ClauseKind.POST_HOSPITALISATION),
    ):
        for match in find_labelled(
            page.text, label_re, value_test=lambda t: P.parse_days(t) is not None
        ):
            days = P.parse_days(match.value_text)
            if days is None or days > 400:
                continue
            clauses.append(
                _clause(
                    kind, match.verbatim, page,
                    params={"days": days},
                    confidence=0.82,
                )
            )
    return clauses


def extract_waiting_periods(page: Page) -> list[Clause]:
    """Waiting periods, which appear as a table or as prose."""
    clauses: list[Clause] = []
    lines = _lines(page.text)

    for i, line in enumerate(lines):
        months = P.parse_months(line)
        if months is None or months == 0 or months > 120:
            continue

        # A duration counts as a waiting period if the row says so, or if the
        # section heading above it did.
        context = " ".join(lines[max(0, i - 6): i + 1])
        if not WAITING_RE.search(context) and not WAITING_RE.search(line):
            continue

        applies = re.sub(
            r"\d{1,3}\s*(?:months?|mths?|years?|yrs?|days?)", "", line, flags=re.IGNORECASE
        ).strip(" -:|\t")

        verbatim = line
        if not applies:
            # A two-column table puts "24 months" and what it applies to on
            # separate lines once the layout is flattened, so the description
            # is on the row below rather than beside it.
            for offset in (1, 2):
                if i + offset >= len(lines):
                    break
                candidate = lines[i + offset].strip(" -:|\t")
                # Skip a bare duration: that is the next row, not this one's label.
                if not candidate or P.parse_months(candidate) is not None:
                    continue
                if len(candidate) > 4 and not candidate.isdigit():
                    applies = candidate
                    verbatim = f"{line} {candidate}"
                break

        clauses.append(
            _clause(
                ClauseKind.WAITING_PERIOD, verbatim, page,
                params={"months": months, "applies_to": applies or "unspecified"},
                confidence=0.74,
            )
        )
    return clauses


def extract_sublimits(page: Page) -> list[Clause]:
    """Per-head caps, read from the sub-limits table."""
    clauses: list[Clause] = []
    lines = _lines(page.text)

    for i, line in enumerate(lines):
        for pattern, head, label in SUBLIMIT_HEADS:
            if not pattern.search(line):
                continue
            amount = P.parse_amount(line)
            if amount is None:
                for offset in (1, 2):
                    if i + offset < len(lines):
                        amount = P.parse_amount(lines[i + offset])
                        if amount is not None:
                            line = f"{line} {lines[i + offset]}"
                            break
            if amount is None:
                continue
            clauses.append(
                _clause(
                    ClauseKind.SUBLIMIT, line, page,
                    params={"amount_inr": str(amount), "head": head.value},
                    scope={"head": head.value, "label": label},
                    confidence=0.72,
                )
            )
            break
    return clauses


def extract_flags(page: Page) -> list[Clause]:
    """Yes/no benefits stated as prose in the schedule."""
    clauses: list[Clause] = []

    for match in find_labelled(page.text, CONSUMABLES_RE):
        covered = not P.states_no_limit(match.value_text) and not re.search(
            r"not\s+cover|excluded", match.value_text, re.IGNORECASE
        )
        clauses.append(
            _clause(
                ClauseKind.CONSUMABLES_COVER, match.verbatim, page,
                params={"covered": covered}, confidence=0.75,
            )
        )

    for match in find_labelled(page.text, RESTORE_RE):
        available = not re.search(
            r"not\s+applicable|not\s+available|\bnil\b", match.value_text, re.IGNORECASE
        )
        clauses.append(
            _clause(
                ClauseKind.RESTORE_BENEFIT, match.verbatim, page,
                params={"available": available}, confidence=0.72,
            )
        )
    return clauses


def extract_meta(page: Page) -> list[Clause]:
    """Identifying details, used to label the policy back to the user."""
    clauses: list[Clause] = []
    specs = [
        (POLICY_NUMBER_RE, "policy_number"),
        (POLICYHOLDER_RE, "policyholder_name"),
        (UIN_RE, "uin"),
    ]
    for label_re, field in specs:
        for match in find_labelled(page.text, label_re):
            value = match.value_text.strip(" :|-")
            if not value or len(value) > 80:
                continue
            clauses.append(
                _clause(
                    ClauseKind.POLICY_META, match.verbatim, page,
                    params={"field": field, "value": value},
                    scope={"field": field},
                    confidence=0.80,
                )
            )
            break
    return clauses


EXTRACTORS: list[Callable[[Page], list[Clause]]] = [
    extract_sum_insured,
    extract_room_limit,
    extract_icu_limit,
    extract_copay,
    extract_deductible,
    extract_hospitalisation_windows,
    extract_waiting_periods,
    extract_sublimits,
    extract_flags,
    extract_meta,
]


def extract_page(page: Page) -> list[Clause]:
    """Run every rule over one page."""
    clauses: list[Clause] = []
    for extractor in EXTRACTORS:
        try:
            clauses.extend(extractor(page))
        except Exception:  # noqa: BLE001 - one bad rule must not stop the rest
            from app.core.logging import get_logger

            get_logger(__name__).warning(
                "grammar rule failed", rule=extractor.__name__, page=page.page_index
            )
    return clauses
