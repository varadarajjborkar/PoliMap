"""Deterministic clause extraction from Indian policy documents.

This is the pipeline's floor. It runs with no model, no key and no network, and
its behaviour is fully predictable, which matters, because a system that gives
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
from datetime import date
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

DAYCARE_RE = re.compile(
    r"\bday\s*[- ]?care\b(?:\s+(?:treatment|procedure|surgery)s?)?", re.IGNORECASE
)

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

# The line that says when cover began. Everything about waiting periods hangs
# off this one date, and until now nothing read it.
POLICY_PERIOD_RE = re.compile(
    r"\b(?:policy\s*period|period\s+of\s+insurance|policy\s+term|"
    r"cover\s+period|from\s+and\s+to)\b",
    re.IGNORECASE,
)
INCEPTION_RE = re.compile(
    r"\b(?:date\s+of\s+(?:issue|inception|commencement)|inception\s+date|"
    r"commencement\s+date|policy\s+start\s+date)\b",
    re.IGNORECASE,
)

# The table of who is covered. A schedule flattens to one value per line, so
# the header row is found first and the rows read beneath it.
INSURED_TABLE_RE = re.compile(
    r"\b(?:insured\s+persons?|details\s+of\s+insured|persons?\s+insured|"
    r"list\s+of\s+insured)\b",
    re.IGNORECASE,
)
RELATIONSHIP_WORDS = frozenset(
    {
        "self", "spouse", "wife", "husband", "son", "daughter", "child",
        "father", "mother", "father-in-law", "mother-in-law", "brother",
        "sister", "dependent", "dependant", "proposer",
    }
)

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
    unreadable schedule page lets a boilerplate default become the answer, the
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
        # "1% of Sum Insured, subject to a maximum of Rs. 5,000", both bind,
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
        params: dict[str, Any] = {"pct": str(pct)}
        # A co-payment is commonly imposed only on older members. Which member
        # is being admitted then decides whether it applies at all.
        band = P.parse_age_band(match.verbatim)
        if band is not None and pct > 0:
            params["above_age"] = band
        clauses.append(
            _clause(
                ClauseKind.COPAY, match.verbatim, page,
                params=params,
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
        # The initial waiting period is written as "30 days", never as a month,
        # and reading only months dropped the one period that applies to every
        # illness there is. It was invisible on every policy in the corpus.
        months = P.parse_months(line) or 0
        days = 0 if months else (P.parse_days(line) or 0)
        if months > 120 or days > 400 or (not months and not days):
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
                params={
                    "months": months,
                    "days": days,
                    "applies_to": applies or "unspecified",
                },
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

    for match in find_labelled(page.text, DAYCARE_RE):
        covered = not re.search(
            r"not\s+covered|not\s+payable|excluded|\bnil\b|not\s+applicable",
            match.value_text, re.IGNORECASE,
        )
        clauses.append(
            _clause(
                ClauseKind.DAYCARE_COVER, match.verbatim, page,
                params={"covered": covered}, confidence=0.74,
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
            # A running header puts several fields on one line: "Policy No.
            # BHA/2026/IND/4029929 | Page 1". Everything past the first bar
            # belongs to the next field, and the full stop belongs to the label
            # that was just matched.
            value = match.value_text.split("|")[0].strip(" :|-.	")
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


def extract_policy_period(page: Page) -> list[Clause]:
    """When cover began and when it ends.

    Every waiting period is counted from the start date, so without it the
    system can list what is not yet covered but cannot say whether any of it
    still applies. The end date matters on its own: a policy that renews next
    week resets the sum insured, and someone deciding when to be admitted
    should know that.
    """
    clauses: list[Clause] = []
    lines = _lines(page.text)

    for i, line in enumerate(lines):
        if not POLICY_PERIOD_RE.search(line) and not INCEPTION_RE.search(line):
            continue

        # A schedule table flattens to label on one line, value on the next.
        found: list[date] = []
        for offset in range(0, 3):
            if i + offset >= len(lines):
                break
            found = P.all_dates(lines[i + offset])
            if found:
                line = lines[i] if offset == 0 else f"{lines[i]} {lines[i + offset]}"
                break
        if not found:
            continue

        fields = [("start_date", found[0])]
        if len(found) > 1 and found[-1] > found[0]:
            fields.append(("end_date", found[-1]))

        for field, value in fields:
            clauses.append(
                _clause(
                    ClauseKind.POLICY_META, line, page,
                    params={"field": field, "value": value.isoformat()},
                    scope={"field": field},
                    confidence=0.82,
                )
            )
        break
    return clauses


def extract_insured_persons(page: Page) -> list[Clause]:
    """Who is covered, and how old they are.

    Age is not decoration. Co-payment is commonly imposed on entrants above
    sixty, a pre-existing waiting period is far likelier to bite at seventy
    than at thirty, and a family floater is conditioned on its eldest member.
    The schedule states it plainly and nothing was reading it.

    The table flattens to one cell per line, so this reads forward from the
    heading and takes a name, an age and a relationship as they arrive rather
    than trying to reconstruct columns.
    """
    lines = _lines(page.text)
    start = next(
        (i for i, line in enumerate(lines) if INSURED_TABLE_RE.search(line)), None
    )
    if start is None:
        return []

    clauses: list[Clause] = []
    pending: dict[str, object] = {}
    verbatim: list[str] = []

    for line in lines[start + 1: start + 60]:
        cell = line.strip(" :|-	")
        if not cell:
            continue
        if _ends_the_table(cell):
            break

        lower = cell.lower()
        if lower in RELATIONSHIP_WORDS:
            pending["relationship"] = cell
            verbatim.append(cell)
        elif cell.isdigit() and len(cell) <= 3 and 0 < int(cell) <= 120:
            # A bare small number in this table is either a serial number or an
            # age. The serial comes before the name and the age after it, which
            # is what tells them apart; the first such number after a name is
            # the age, and the next one is the following row's serial.
            if pending.get("name") and pending.get("age") is None:
                pending["age"] = int(cell)
                verbatim.append(cell)
        elif P.parse_amount(cell) is not None and any(
            token in lower for token in ("rs", "₹", "inr", "lakh", "crore")
        ):
            pending["sum_insured"] = str(P.parse_amount(cell))
            verbatim.append(cell)
        elif _looks_like_a_person(cell):
            # A name begins a row, so it also ends the one before it. Closing
            # the previous person only once every field arrived would end them
            # at the relationship and hand their sum insured to the next row.
            if pending.get("name"):
                clauses.append(_insured_clause(pending, verbatim, page))
                pending, verbatim = {}, []
            pending["name"] = cell
            verbatim.append(cell)

    if pending.get("name"):
        clauses.append(_insured_clause(pending, verbatim, page))
    return [c for c in clauses if c.params.get("age") is not None]


def _ends_the_table(cell: str) -> bool:
    """Whether this cell is the next section heading rather than another row.

    Capitals alone are not enough. A sum insured written "INR 25,00,000" is
    uppercase, and treating it as a heading ended the table one row in, which
    on a family policy quietly dropped the spouse.
    """
    if len(cell) <= 6 or not cell.isupper():
        return False
    return any(ch.isalpha() for ch in cell) and not any(ch.isdigit() for ch in cell)


def _insured_clause(
    pending: dict[str, object], verbatim: list[str], page: Page
) -> Clause:
    return _clause(
        ClauseKind.INSURED_PERSON, " ".join(verbatim)[:180], page,
        params=dict(pending),
        scope={"person": str(pending.get("name", ""))},
        confidence=0.78,
    )


# A cell holding a person's name: words, initials, the occasional full stop.
#
# Two words at least. A schedule writes a full name, and a single-word cell in
# this table is a column value rather than a person. "Floater", which is what a
# family policy puts in the sum insured column for everyone after the proposer,
# was being read as a family member who then took the next row's serial number
# as their age.
_PERSON_NAME = re.compile(r"^[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){1,3}$")
_NOT_A_PERSON = frozenset(
    {
        "name", "age", "sl", "sl.", "no", "no.", "relationship", "sum",
        "insured", "sum insured", "name of insured person", "policy",
        "gender", "date of birth", "dob", "member", "s.no",
    }
)


def _looks_like_a_person(cell: str) -> bool:
    if cell.lower().strip(". ") in _NOT_A_PERSON:
        return False
    if len(cell) < 3 or len(cell) > 60:
        return False
    return bool(_PERSON_NAME.match(cell))


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
    extract_policy_period,
    extract_insured_persons,
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
