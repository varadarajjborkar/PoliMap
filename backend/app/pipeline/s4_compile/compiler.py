"""Stage 4 — compile a verified clause ledger into an executable policy.

The ledger is evidence: overlapping, sometimes contradictory, carrying claims of
varying authority. The cost engine needs the opposite — one settled, strongly
typed answer per question. This stage performs that collapse, and it is the only
place allowed to choose between competing clauses.

Resolution is by declared precedence rather than by confidence alone. A figure
printed on the policyholder's own schedule outranks the same figure in generic
wording even when the wording was read more cleanly, because the schedule is
what they actually bought. Confidence only breaks ties within a tier.

Anything that cannot be settled becomes a `ClarificationRequest` rather than a
default. Silently assuming a missing co-payment is zero produces an estimate
that is too good and a user who discovers the truth at the billing counter.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.core.events import bus
from app.core.logging import get_logger
from app.schemas.events import EventStatus, PipelineStage
from app.schemas.money import format_inr
from app.schemas.policy import (
    Clause,
    ClauseKind,
    ClarificationRequest,
    ClauseStatus,
    Exclusion,
    ExpenseHead,
    NormalizedPolicy,
    PolicyMeta,
    RoomCategory,
    RoomLimit,
    RoomLimitBasis,
    SubLimit,
    WaitingPeriod,
)

log = get_logger(__name__)
STAGE = PipelineStage.COMPILE

# Below this a clause is reported to the user for confirmation rather than
# simply believed. Tuned so a clean schedule read passes untouched while a
# hedged wording clause or a poor OCR read always asks.
CONFIRM_BELOW = 0.55


def _num(value: object) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _winner(clauses: list[Clause], kind: ClauseKind) -> Clause | None:
    """The single clause that should decide this question."""
    candidates = [c for c in clauses if c.kind is kind and c.is_admissible]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda c: (c.evidence.section.precedence, c.confidence, -c.round_added),
    )


def _room_limit_from(clause: Clause | None) -> RoomLimit:
    if clause is None:
        return RoomLimit()

    params = clause.params
    basis = params.get("basis", "flat")
    amount = _num(params.get("amount_inr"))
    pct = _num(params.get("pct_of_si"))
    category = params.get("category")

    if basis == "no_limit":
        return RoomLimit(basis=RoomLimitBasis.NO_LIMIT, source_clause_ids=[clause.clause_id])
    if basis == "category" and category:
        return RoomLimit(
            basis=RoomLimitBasis.CATEGORY_ONLY,
            category_ceiling=RoomCategory(category),
            source_clause_ids=[clause.clause_id],
        )
    if basis == "pct_with_max":
        return RoomLimit(
            basis=RoomLimitBasis.PCT_OF_SI_PER_DAY,
            pct_of_si=pct, amount_per_day=amount,
            source_clause_ids=[clause.clause_id],
        )
    if basis == "pct_of_si" and pct is not None:
        return RoomLimit(
            basis=RoomLimitBasis.PCT_OF_SI_PER_DAY, pct_of_si=pct,
            source_clause_ids=[clause.clause_id],
        )
    if amount is not None:
        return RoomLimit(
            basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=amount,
            source_clause_ids=[clause.clause_id],
        )
    return RoomLimit()


def _ask(
    kind: ClauseKind, question: str, *, help_text: str = "",
    suggested: object = None, clause: Clause | None = None,
    options: list[dict] | None = None,
) -> ClarificationRequest:
    return ClarificationRequest(
        clause_kind=kind,
        question=question,
        help_text=help_text,
        suggested_value=suggested,
        options=options or [],
        evidence=clause.evidence if clause else None,
    )


def compile_policy(
    clauses: list[Clause], *, session_id: str | None = None
) -> NormalizedPolicy:
    """Collapse the ledger into the settled policy the engine executes."""
    with bus.step(
        STAGE, "compile_policy", session_id=session_id,
        summary="Building your coverage profile",
    ) as step:
        policy = NormalizedPolicy()
        asks: list[ClarificationRequest] = []

        # --- sum insured: nothing downstream works without it ---
        si_clause = _winner(clauses, ClauseKind.SUM_INSURED)
        si = _num(si_clause.params.get("amount_inr")) if si_clause else None
        if si is not None:
            policy.sum_insured = si
        if si is None:
            asks.append(_ask(
                ClauseKind.SUM_INSURED,
                "What is the total cover amount on your policy?",
                help_text="This is the maximum your insurer will pay in a year. "
                          "It is usually the largest figure on your policy schedule.",
            ))
        elif si_clause and si_clause.confidence < CONFIRM_BELOW:
            asks.append(_ask(
                ClauseKind.SUM_INSURED,
                f"Is your total cover {format_inr(si)}?",
                help_text="We read this from your document but could not be sure.",
                suggested=float(si), clause=si_clause,
            ))

        # --- room entitlement ---
        room_clause = _winner(clauses, ClauseKind.ROOM_RENT_CAP) or _winner(
            clauses, ClauseKind.ROOM_CATEGORY_ELIGIBILITY
        )
        policy.room_limit = _room_limit_from(room_clause)
        policy.icu_limit = _room_limit_from(_winner(clauses, ClauseKind.ICU_CAP))

        if room_clause is None:
            asks.append(_ask(
                ClauseKind.ROOM_RENT_CAP,
                "Does your policy limit how much it pays for your hospital room?",
                help_text="Most policies cap the daily room rent, either as a rupee "
                          "amount or as a percentage of your cover. This matters a "
                          "lot: a room above your limit reduces what your insurer "
                          "pays on other charges too.",
                options=[
                    {"label": "No limit on my room", "value": "none"},
                    {"label": "A fixed amount per day", "value": "flat"},
                    {"label": "A percentage of my cover", "value": "pct"},
                    {"label": "I do not know", "value": "unknown"},
                ],
            ))
        elif room_clause.confidence < CONFIRM_BELOW:
            cap = policy.room_limit.effective_daily_cap(policy.sum_insured)
            asks.append(_ask(
                ClauseKind.ROOM_RENT_CAP,
                f"Is your room rent limit {policy.room_limit.describe(policy.sum_insured)}?"
                if cap else "Is this your room entitlement?",
                help_text=(
                    "We found this in the policy wording rather than your schedule, "
                    "so it may describe a standard plan rather than yours."
                    if room_clause.notes else
                    "We read this from your document but could not be sure."
                ),
                suggested=float(cap) if cap else None, clause=room_clause,
            ))

        # --- shares the policyholder bears ---
        copay_clause = _winner(clauses, ClauseKind.COPAY)
        if copay_clause and (pct := _num(copay_clause.params.get("pct"))) is not None:
            policy.copay_pct = pct
            if copay_clause.confidence < CONFIRM_BELOW and pct > 0:
                asks.append(_ask(
                    ClauseKind.COPAY,
                    f"Do you pay a {pct:g}% share of every claim?",
                    help_text="A co-payment is the part of every approved claim you "
                              "pay yourself.",
                    suggested=float(pct), clause=copay_clause,
                ))

        deductible_clause = _winner(clauses, ClauseKind.DEDUCTIBLE)
        if deductible_clause:
            amount = _num(deductible_clause.params.get("amount_inr"))
            if amount is not None:
                policy.deductible = amount

        # --- windows and flags ---
        for kind, attr in (
            (ClauseKind.PRE_HOSPITALISATION, "pre_hospitalisation_days"),
            (ClauseKind.POST_HOSPITALISATION, "post_hospitalisation_days"),
        ):
            clause = _winner(clauses, kind)
            if clause and (days := clause.params.get("days")) is not None:
                setattr(policy, attr, int(days))

        consumables = _winner(clauses, ClauseKind.CONSUMABLES_COVER)
        if consumables is not None:
            policy.covers_consumables = bool(consumables.params.get("covered"))

        restore = _winner(clauses, ClauseKind.RESTORE_BENEFIT)
        if restore is not None:
            policy.restore_benefit = bool(restore.params.get("available"))

        # --- multi-valued groups ---
        policy.sublimits = _compile_sublimits(clauses)
        policy.waiting_periods = _compile_waiting_periods(clauses)
        policy.exclusions = [
            Exclusion(text=c.verbatim, source_clause_ids=[c.clause_id])
            for c in clauses
            if c.kind is ClauseKind.EXCLUSION and c.is_admissible
        ]
        policy.meta = _compile_meta(clauses)

        policy.clauses = clauses
        policy.open_clarifications = asks
        policy.confidence = _overall_confidence(clauses, asks)

        summary = (
            f"Cover {format_inr(policy.sum_insured)}, "
            f"room {policy.room_limit.describe(policy.sum_insured)}"
        )
        if asks:
            step.warn(
                f"{summary} — {len(asks)} thing"
                f"{'s' if len(asks) != 1 else ''} to confirm with you",
                sum_insured=float(policy.sum_insured),
                clarifications=len(asks),
                confidence=policy.confidence,
            )
        else:
            step.ok(
                summary,
                sum_insured=float(policy.sum_insured),
                sublimits=len(policy.sublimits),
                confidence=policy.confidence,
            )

    return policy


def _compile_sublimits(clauses: list[Clause]) -> list[SubLimit]:
    """One cap per head or procedure, the tightest winning.

    Where two clauses cap the same head differently the lower is taken: an
    estimate that overstates cover is the one that hurts, and the conservative
    reading is also the likelier reading of a document that says both.
    """
    best: dict[tuple, tuple[Decimal, Clause]] = {}

    for clause in clauses:
        if clause.kind is not ClauseKind.SUBLIMIT or not clause.is_admissible:
            continue
        amount = _num(clause.params.get("amount_inr"))
        if amount is None:
            continue

        head_value = clause.scope.get("head") or clause.params.get("head")
        code = clause.scope.get("procedure_code") or clause.params.get("procedure_code")
        if not head_value and not code:
            continue

        key = ("head", head_value) if head_value else ("code", code)
        current = best.get(key)
        if current is None or amount < current[0]:
            best[key] = (amount, clause)

    limits: list[SubLimit] = []
    for (kind, value), (amount, clause) in best.items():
        try:
            limits.append(SubLimit(
                head=ExpenseHead(value) if kind == "head" else None,
                procedure_code=None if kind == "head" else value,
                label=clause.scope.get("label", ""),
                amount=amount,
                source_clause_ids=[clause.clause_id],
            ))
        except ValueError:
            log.debug("unknown sub-limit target", value=value)
    return limits


def _compile_waiting_periods(clauses: list[Clause]) -> list[WaitingPeriod]:
    seen: dict[tuple, WaitingPeriod] = {}
    for clause in clauses:
        if clause.kind is not ClauseKind.WAITING_PERIOD or not clause.is_admissible:
            continue
        months = clause.params.get("months")
        if not months:
            continue
        applies = str(clause.params.get("applies_to") or "unspecified")
        key = (int(months), applies.lower()[:40])
        seen.setdefault(key, WaitingPeriod(
            months=int(months), applies_to=applies,
            source_clause_ids=[clause.clause_id],
        ))
    return sorted(seen.values(), key=lambda w: w.months)


def _compile_meta(clauses: list[Clause]) -> PolicyMeta:
    meta = PolicyMeta()
    for clause in clauses:
        if clause.kind is not ClauseKind.POLICY_META or not clause.is_admissible:
            continue
        field = clause.scope.get("field") or clause.params.get("field")
        value = str(clause.params.get("value", "")).strip()
        if field and value and hasattr(meta, field) and not getattr(meta, field):
            setattr(meta, field, value)
    return meta


def _overall_confidence(
    clauses: list[Clause], asks: list[ClarificationRequest]
) -> float:
    """How much of this compilation the user should be shown as settled.

    Weighted toward the clauses that drive money — a perfectly read policy
    number does not offset an uncertain room limit.
    """
    weights = {
        ClauseKind.SUM_INSURED: 3.0,
        ClauseKind.ROOM_RENT_CAP: 3.0,
        ClauseKind.ROOM_CATEGORY_ELIGIBILITY: 2.0,
        ClauseKind.COPAY: 2.0,
        ClauseKind.DEDUCTIBLE: 1.5,
        ClauseKind.ICU_CAP: 1.0,
        ClauseKind.SUBLIMIT: 1.0,
    }
    scored = [
        (weights[c.kind], c.confidence)
        for c in clauses
        if c.kind in weights and c.is_admissible
    ]
    if not scored:
        return 0.0

    total_weight = sum(w for w, _ in scored)
    base = sum(w * c for w, c in scored) / total_weight
    # Each open question is a known gap and should show as one.
    return round(max(0.0, min(1.0, base - 0.08 * len(asks))), 3)


def apply_answer(
    policy: NormalizedPolicy, request_id: str, answer: object
) -> NormalizedPolicy:
    """Fold a user's confirmation back into the compiled policy."""
    request = next(
        (r for r in policy.open_clarifications if r.request_id == request_id), None
    )
    if request is None:
        return policy

    request.answered = True
    request.answer = answer

    if request.clause_kind is ClauseKind.SUM_INSURED:
        if (value := _num(answer)) is not None:
            policy.sum_insured = value
    elif request.clause_kind is ClauseKind.COPAY:
        if (value := _num(answer)) is not None:
            policy.copay_pct = value
    elif request.clause_kind is ClauseKind.ROOM_RENT_CAP:
        if answer in ("none", "no", False):
            policy.room_limit = RoomLimit(basis=RoomLimitBasis.NO_LIMIT)
        elif (value := _num(answer)) is not None:
            policy.room_limit = RoomLimit(
                basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=value
            )

    # A user's own answer is authoritative; the clause it replaces is settled.
    for clause in policy.clauses:
        if clause.kind is request.clause_kind and clause.status is ClauseStatus.NEEDS_USER:
            clause.status = ClauseStatus.CONFIRMED

    policy.open_clarifications = [
        r for r in policy.open_clarifications if not r.answered
    ]
    policy.confidence = _overall_confidence(policy.clauses, policy.open_clarifications)
    return policy
