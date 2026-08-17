"""Raise objections against extracted clauses.

Extraction produces a first draft. This module's job is to attack it.

The benchmark that motivated this stage is worth stating plainly: adding a
language model to extraction halved the number of missed fields and tripled the
number of *confidently wrong* ones. Wrong values are the dangerous failure —
nothing prompts anyone to check them — so a system that gains recall by taking
on wrong values has not improved. The challenger exists to convert that new
recall into either a verified value or an honest question.

Most challenges are raised deterministically, because most of them can be. The
strongest check needs no model at all: re-parse a clause's own quoted text and
confirm it still yields the value the clause claims. A model that read a figure
from the wrong table row leaves a quote that does not contain the number it
reported, and that is provable in code.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.core.logging import get_logger
from app.pipeline.s2_atomize import patterns as P
from app.schemas.policy import (
    Challenge,
    ChallengeKind,
    Clause,
    ClauseKind,
    REQUIRED_CLAUSE_KINDS,
)

log = get_logger(__name__)

# Ranges outside which a value is not a plausible reading of an Indian policy.
SUM_INSURED_RANGE = (Decimal(25000), Decimal(100000000))
ROOM_CAP_RANGE = (Decimal(200), Decimal(200000))
MAX_COPAY_PCT = Decimal(50)

# A daily room cap is conventionally 1-2% of the sum insured. Well outside that
# band usually means one of the two figures was misread.
ROOM_CAP_SANE_FRACTION = Decimal("0.10")

SINGLE_VALUED = {
    ClauseKind.SUM_INSURED,
    ClauseKind.ROOM_RENT_CAP,
    ClauseKind.ICU_CAP,
    ClauseKind.COPAY,
    ClauseKind.DEDUCTIBLE,
    ClauseKind.CONSUMABLES_COVER,
}


def _num(value: object) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _claimed_value(clause: Clause) -> Decimal | None:
    for field in ("amount_inr", "pct_of_si", "pct"):
        if (value := _num(clause.params.get(field))) is not None:
            return value
    return None


def check_evidence_supports_value(clause: Clause) -> Challenge | None:
    """Re-derive the clause's value from its own quote.

    The cheapest and sharpest check available. A clause quoting "Sum Insured
    (per policy year)" while reporting the premium below it cannot survive
    re-parsing its own evidence, and no model call is needed to prove it.
    """
    claimed = _claimed_value(clause)
    if claimed is None:
        return None

    text = clause.verbatim
    candidates = set(P.all_amounts(text))
    if (pct := P.parse_percent(text)) is not None:
        candidates.add(pct)
    if (pct_si := P.parse_pct_of_sum_insured(text)) is not None:
        candidates.add(pct_si)
    if (days := P.parse_days(text)) is not None:
        candidates.add(Decimal(days))
    if (months := P.parse_months(text)) is not None:
        candidates.add(Decimal(months))

    if not candidates:
        return None
    if any(abs(candidate - claimed) < Decimal("0.01") for candidate in candidates):
        return None

    return Challenge(
        kind=ChallengeKind.EVIDENCE_WEAK,
        clause_ids=[clause.clause_id],
        question=(
            f"This says {claimed}, but the text it quotes contains "
            f"{', '.join(str(c) for c in sorted(candidates)[:4])}."
        ),
        rationale="The quoted evidence does not contain the reported value.",
    )


def check_plausible(clause: Clause) -> Challenge | None:
    """Reject values outside any realistic range for a real policy."""
    value = _claimed_value(clause)
    if value is None:
        return None

    def objection(reason: str) -> Challenge:
        return Challenge(
            kind=ChallengeKind.IMPLAUSIBLE,
            clause_ids=[clause.clause_id],
            question=reason,
            rationale="Outside the range real Indian policies use.",
        )

    if clause.kind is ClauseKind.SUM_INSURED:
        low, high = SUM_INSURED_RANGE
        if not (low <= value <= high):
            return objection(f"A cover amount of {value} is not realistic.")

    if clause.kind in (ClauseKind.ROOM_RENT_CAP, ClauseKind.ICU_CAP):
        if clause.params.get("basis") in ("flat", "pct_with_max"):
            low, high = ROOM_CAP_RANGE
            if (amount := _num(clause.params.get("amount_inr"))) is not None:
                if not (low <= amount <= high):
                    return objection(f"A daily room limit of {amount} is not realistic.")

    if clause.kind is ClauseKind.COPAY and value > MAX_COPAY_PCT:
        return objection(f"A co-payment of {value}% is not realistic.")

    return None


def check_contradictions(clauses: list[Clause]) -> list[Challenge]:
    """Find single-valued questions that have more than one answer."""
    challenges: list[Challenge] = []
    grouped: dict[ClauseKind, list[Clause]] = {}
    for clause in clauses:
        if clause.kind in SINGLE_VALUED and clause.is_admissible:
            grouped.setdefault(clause.kind, []).append(clause)

    for kind, group in grouped.items():
        distinct: dict[str, list[Clause]] = {}
        for clause in group:
            distinct.setdefault(_signature(clause), []).append(clause)
        if len(distinct) < 2:
            continue

        challenges.append(Challenge(
            kind=ChallengeKind.CONTRADICTION,
            clause_ids=[c.clause_id for c in group],
            target_kind=kind,
            question=(
                f"The document gives {len(distinct)} different answers for "
                f"{kind.label.lower()}: "
                + " / ".join(sorted(distinct)[:3])
            ),
            rationale="Only one of these can be this policyholder's term.",
        ))
    return challenges


def _signature(clause: Clause) -> str:
    parts = [
        f"{k}={v}"
        for k, v in sorted(clause.params.items())
        if k in ("amount_inr", "pct_of_si", "pct", "basis", "category", "covered")
    ]
    return ", ".join(parts) or clause.verbatim[:30]


def check_cross_field_coherence(clauses: list[Clause]) -> list[Challenge]:
    """Catch pairs that are individually plausible but wrong together.

    A room cap that is a large fraction of the whole sum insured is the classic
    signature of one of the two having been read from the wrong row.
    """
    challenges: list[Challenge] = []

    si_clause = _best(clauses, ClauseKind.SUM_INSURED)
    room_clause = _best(clauses, ClauseKind.ROOM_RENT_CAP)
    if si_clause is None or room_clause is None:
        return challenges

    si = _num(si_clause.params.get("amount_inr"))
    cap = _num(room_clause.params.get("amount_inr"))
    if si is None or cap is None or si <= 0:
        return challenges

    if cap > si * ROOM_CAP_SANE_FRACTION:
        challenges.append(Challenge(
            kind=ChallengeKind.CONTRADICTION,
            clause_ids=[si_clause.clause_id, room_clause.clause_id],
            question=(
                f"A daily room limit of {cap} against total cover of {si} does "
                f"not fit — one of these was probably read from the wrong line."
            ),
            rationale="Daily room limits are typically 1-2% of the sum insured.",
        ))
    return challenges


def check_completeness(clauses: list[Clause]) -> list[Challenge]:
    """Report required terms that no clause covers."""
    present = {c.kind for c in clauses if c.is_admissible}
    if ClauseKind.ROOM_CATEGORY_ELIGIBILITY in present:
        present.add(ClauseKind.ROOM_RENT_CAP)

    return [
        Challenge(
            kind=ChallengeKind.MISSING,
            target_kind=kind,
            question=f"No {kind.label.lower()} was found in this document.",
            rationale="Every health policy states this.",
        )
        for kind in sorted(REQUIRED_CLAUSE_KINDS - present, key=lambda k: k.value)
    ]


def _best(clauses: list[Clause], kind: ClauseKind) -> Clause | None:
    candidates = [c for c in clauses if c.kind is kind and c.is_admissible]
    if not candidates:
        return None
    return max(
        candidates, key=lambda c: (c.evidence.section.precedence, c.confidence)
    )


def raise_challenges(clauses: list[Clause], *, round_number: int = 1) -> list[Challenge]:
    """Every objection that can be raised against the current ledger."""
    challenges: list[Challenge] = []

    for clause in clauses:
        if not clause.is_admissible:
            continue
        if (challenge := check_evidence_supports_value(clause)) is not None:
            challenges.append(challenge)
        if (challenge := check_plausible(clause)) is not None:
            challenges.append(challenge)

    challenges.extend(check_contradictions(clauses))
    challenges.extend(check_cross_field_coherence(clauses))
    challenges.extend(check_completeness(clauses))

    for challenge in challenges:
        challenge.round_raised = round_number
    return challenges
