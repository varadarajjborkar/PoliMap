"""Care journey tracking with stage-aware, costed guidance.

The insurance position is not static. Costs accrue daily, sub-limits drain, a
room that was affordable on day one is expensive by day five, and
pre-authorisation has a window that closes. This module re-answers "where do I
stand" at every stage instead of once at admission.

Two rules govern what it says.

**Stages are administrative, never clinical.** Admission, investigation,
procedure, recovery describe where the paperwork is. Nothing here infers,
records or reasons about a diagnosis, and no alert ever suggests a course of
treatment — the problem statement rules that out and the distinction is worth
holding precisely.

**Every alert states a rupee figure and an action.** An alert that says "your
costs are rising" without saying by how much, or what could be done about it, is
just anxiety delivered on a schedule.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.core.events import bus
from app.core.logging import get_logger
from app.schemas.events import EventStatus, PipelineStage
from app.schemas.journey import (
    STAGE_TRANSITIONS,
    Alert,
    AlertKind,
    AlertSeverity,
    BurnDown,
    CostEntry,
    JourneyEvent,
    JourneyStage,
    JourneyState,
)
from app.schemas.money import ZERO, format_inr, round_inr
from app.schemas.policy import ExpenseHead, NormalizedPolicy, RoomCategory

log = get_logger(__name__)
STAGE = PipelineStage.JOURNEY

SUBLIMIT_WARNING_FRACTION = 0.75
COVER_WARNING_FRACTION = 0.70
COVER_URGENT_FRACTION = 0.90

# Stages at which a cashless pre-authorisation should already be filed. Insurers
# require it before a planned procedure and within 24 hours of an emergency
# admission, and a missed window turns a cashless claim into a reimbursement one.
PRE_AUTH_DUE_AT = {
    JourneyStage.ADMITTED,
    JourneyStage.INVESTIGATION,
    JourneyStage.PRE_AUTH,
}


class TransitionError(ValueError):
    """Raised when a stage move is not one the journey model allows."""


def start_journey(
    policy: NormalizedPolicy,
    *,
    session_id: str = "",
    hospital_id: str | None = None,
    hospital_name: str = "",
    procedure_code: str | None = None,
    room_category: RoomCategory | None = None,
    room_rate_per_day: Decimal | None = None,
) -> JourneyState:
    state = JourneyState(
        session_id=session_id,
        policy_id=policy.policy_id,
        hospital_id=hospital_id,
        hospital_name=hospital_name,
        procedure_code=procedure_code,
        room_category=room_category,
        room_rate_per_day=room_rate_per_day,
    )
    state.timeline.append(JourneyEvent(
        stage=JourneyStage.PRE_ADMISSION,
        title="Planning your care",
        description=(
            f"Cover of {format_inr(policy.sum_insured)} available."
            + (f" Considering {hospital_name}." if hospital_name else "")
        ),
    ))
    return state


def advance(
    state: JourneyState,
    target: JourneyStage,
    policy: NormalizedPolicy,
    *,
    note: str = "",
) -> JourneyState:
    """Move to a new stage and recompute the guidance that applies there."""
    if not state.can_move_to(target):
        allowed = ", ".join(sorted(s.value for s in STAGE_TRANSITIONS[state.stage]))
        raise TransitionError(
            f"Cannot move from {state.stage.value} to {target.value}. "
            f"Allowed: {allowed or 'none — this journey is complete'}"
        )

    previous = state.stage
    state.stage = target

    if target is JourneyStage.ADMITTED and state.admitted_at is None:
        state.admitted_at = datetime.now(UTC)

    alerts = evaluate(state, policy)
    state.active_alerts = alerts

    state.timeline.append(JourneyEvent(
        stage=target,
        title=target.label,
        description=note or _stage_description(target, state, policy),
        alerts=alerts,
    ))

    bus.publish(
        STAGE, "advance_stage", session_id=state.session_id or None,
        status=EventStatus.WARN if any(
            a.severity is AlertSeverity.URGENT for a in alerts
        ) else EventStatus.OK,
        summary=f"{previous.label} to {target.label}"
                + (f" — {len(alerts)} thing{'s' if len(alerts) != 1 else ''} to know"
                   if alerts else ""),
        stage=target.value,
        alerts=len(alerts),
        accrued=float(state.accrued_total),
    )
    return state


def record_cost(
    state: JourneyState,
    head: ExpenseHead,
    amount: Decimal,
    policy: NormalizedPolicy,
    *,
    description: str = "",
) -> JourneyState:
    """Add an actual charge and re-evaluate the position."""
    state.costs.append(CostEntry(
        head=head, amount=amount, description=description, stage=state.stage
    ))
    state.active_alerts = evaluate(state, policy)

    bus.publish(
        STAGE, "record_cost", session_id=state.session_id or None,
        summary=f"{head.label} {format_inr(amount)} — "
                f"{format_inr(state.accrued_total)} so far",
        head=head.value, amount=float(amount),
        accrued=float(state.accrued_total),
    )
    return state


def burn_down(state: JourneyState, policy: NormalizedPolicy) -> BurnDown:
    """Cover consumed against cover available, projected to discharge.

    Projection uses the daily rate observed so far rather than the original
    estimate, because the point of tracking is to notice when reality has
    departed from the plan.
    """
    consumed = state.accrued_total
    available = policy.available_cover
    days = max(state.days_elapsed, 1)

    if state.stage in (JourneyStage.SETTLED, JourneyStage.DISCHARGE_PLANNING):
        projected = consumed
    else:
        per_day = consumed / Decimal(days)
        remaining_days = Decimal(2)  # A conservative near-term horizon.
        projected = round_inr(consumed + per_day * remaining_days)

    return BurnDown(
        sum_insured=available,
        consumed=consumed,
        projected_total=max(projected, consumed),
        remaining=max(available - consumed, ZERO),
    )


def evaluate(state: JourneyState, policy: NormalizedPolicy) -> list[Alert]:
    """Every alert that applies right now, most urgent first."""
    alerts: list[Alert] = []
    accrued = state.accrued_by_head()
    burn = burn_down(state, policy)

    alerts.extend(_room_alerts(state, policy))
    alerts.extend(_sublimit_alerts(state, policy, accrued))
    alerts.extend(_cover_alerts(state, policy, burn))
    alerts.extend(_non_payable_alerts(state, policy, accrued))
    alerts.extend(_stage_alerts(state, policy))

    alerts.sort(key=lambda a: -a.severity.rank)
    return alerts


def _room_alerts(state: JourneyState, policy: NormalizedPolicy) -> list[Alert]:
    """The proportionate-deduction warning, expressed in money already lost."""
    if state.room_rate_per_day is None or not state.is_active:
        return []

    cap = policy.room_limit.effective_daily_cap(policy.sum_insured)
    if cap is None or state.room_rate_per_day <= cap:
        return []

    days = max(state.days_elapsed, 1)
    excess = round_inr((state.room_rate_per_day - cap) * Decimal(days))
    ratio = cap / state.room_rate_per_day

    room_linked = sum(
        (amount for head, amount in state.accrued_by_head().items()
         if head in _ROOM_LINKED_HEADS),
        ZERO,
    )
    knock_on = round_inr(room_linked * (Decimal(1) - ratio))

    return [Alert(
        kind=AlertKind.ROOM_OVER_LIMIT,
        severity=AlertSeverity.URGENT,
        title="Your room costs more than your policy covers",
        message=(
            f"Your room is {format_inr(state.room_rate_per_day)} a day and your "
            f"policy covers {format_inr(cap)}. After {days} day"
            f"{'s' if days != 1 else ''} that is {format_inr(excess)} in room "
            f"rent, plus about {format_inr(knock_on)} deducted from your "
            f"surgeon, theatre and nursing charges."
        ),
        action=(
            "Ask the hospital insurance desk about moving to a room within your "
            "limit. It stops further deductions from tomorrow."
        ),
        amount=round_inr(excess + knock_on),
        clause_ids=policy.room_limit.source_clause_ids,
        stage=state.stage,
    )]


_ROOM_LINKED_HEADS = frozenset({
    ExpenseHead.NURSING, ExpenseHead.DOCTOR_VISIT, ExpenseHead.SURGEON_FEE,
    ExpenseHead.ANAESTHETIST_FEE, ExpenseHead.OT_CHARGES,
})


def _sublimit_alerts(
    state: JourneyState, policy: NormalizedPolicy, accrued: dict[ExpenseHead, Decimal]
) -> list[Alert]:
    alerts: list[Alert] = []
    for sublimit in policy.sublimits:
        if sublimit.head is None:
            continue
        spent = accrued.get(sublimit.head, ZERO)
        cap = sublimit.resolve(policy.sum_insured, days=max(state.days_elapsed, 1))
        if cap <= 0 or spent < cap * Decimal(str(SUBLIMIT_WARNING_FRACTION)):
            continue

        used = spent / cap
        alerts.append(Alert(
            kind=AlertKind.SUBLIMIT_NEARLY_USED,
            severity=AlertSeverity.URGENT if used >= 1 else AlertSeverity.ATTENTION,
            title=f"{sublimit.head.label} limit almost used",
            message=(
                f"Your policy covers {format_inr(cap)} of "
                f"{sublimit.head.label.lower()} and {format_inr(spent)} has been "
                f"billed — {used:.0%} of the limit."
            ),
            action=(
                "Anything beyond this you pay yourself. Ask the desk before "
                "further tests are ordered."
            ),
            amount=max(spent - cap, ZERO),
            clause_ids=sublimit.source_clause_ids,
            stage=state.stage,
        ))
    return alerts


def _cover_alerts(
    state: JourneyState, policy: NormalizedPolicy, burn: BurnDown
) -> list[Alert]:
    if burn.sum_insured <= 0:
        return []

    if burn.consumed_fraction >= COVER_URGENT_FRACTION:
        return [Alert(
            kind=AlertKind.COVER_NEARLY_EXHAUSTED,
            severity=AlertSeverity.URGENT,
            title="Your cover is almost used up",
            message=(
                f"{format_inr(burn.consumed)} of your {format_inr(burn.sum_insured)} "
                f"cover has been billed. {format_inr(burn.remaining)} remains."
            ),
            action="Ask about discharge planning and what you will owe directly.",
            amount=burn.remaining,
            stage=state.stage,
        )]

    if burn.will_exceed and state.is_active:
        return [Alert(
            kind=AlertKind.COVER_NEARLY_EXHAUSTED,
            severity=AlertSeverity.ATTENTION,
            title="Costs are on track to pass your cover",
            message=(
                f"At the current rate this stay reaches about "
                f"{format_inr(burn.projected_total)}, above your "
                f"{format_inr(burn.sum_insured)} cover."
            ),
            action="Ask the desk for a running bill so there are no surprises.",
            amount=max(burn.projected_total - burn.sum_insured, ZERO),
            stage=state.stage,
        )]

    if burn.consumed_fraction >= COVER_WARNING_FRACTION:
        return [Alert(
            kind=AlertKind.COVER_NEARLY_EXHAUSTED,
            severity=AlertSeverity.ATTENTION,
            title="Most of your cover is used",
            message=f"{format_inr(burn.remaining)} of cover remains for this year.",
            action="Keep this in mind if further treatment is needed.",
            amount=burn.remaining,
            stage=state.stage,
        )]

    return []


def _non_payable_alerts(
    state: JourneyState, policy: NormalizedPolicy, accrued: dict[ExpenseHead, Decimal]
) -> list[Alert]:
    """Charges the policy will never reimburse, surfaced while they accumulate."""
    non_payable = accrued.get(ExpenseHead.NON_MEDICAL, ZERO)
    if not policy.covers_consumables:
        non_payable += accrued.get(ExpenseHead.CONSUMABLES, ZERO)

    if non_payable < Decimal(2000):
        return []

    return [Alert(
        kind=AlertKind.NON_PAYABLE_ACCUMULATING,
        severity=AlertSeverity.ATTENTION,
        title="Charges your policy will not cover",
        message=(
            f"{format_inr(non_payable)} of the bill so far is for items no "
            f"health policy reimburses — gloves, syringes, registration and "
            f"similar. You pay these whatever else your policy covers."
        ),
        action="Ask for an itemised bill so you can check these are correct.",
        amount=non_payable,
        stage=state.stage,
    )]


def _stage_alerts(state: JourneyState, policy: NormalizedPolicy) -> list[Alert]:
    alerts: list[Alert] = []

    if state.stage in PRE_AUTH_DUE_AT and not state.pre_auth_filed:
        alerts.append(Alert(
            kind=AlertKind.PRE_AUTH_DUE,
            severity=AlertSeverity.URGENT,
            title="Pre-authorisation needs to be filed",
            message=(
                "Cashless treatment needs your insurer's approval before the "
                "procedure. Without it you would pay the hospital yourself and "
                "claim it back later."
            ),
            action="Ask the hospital insurance desk to file the pre-authorisation now.",
            stage=state.stage,
        ))

    if state.stage is JourneyStage.DISCHARGE_PLANNING:
        alerts.append(Alert(
            kind=AlertKind.DOCUMENTS_NEEDED,
            severity=AlertSeverity.ATTENTION,
            title="Collect your documents before you leave",
            message=(
                "You will need the discharge summary, the itemised final bill, "
                "and all original test reports and pharmacy receipts."
                + (f" Treatment costs for {policy.post_hospitalisation_days} days "
                   f"after discharge are also covered."
                   if policy.post_hospitalisation_days else "")
            ),
            action="Ask for originals, not photocopies. Claims are refused without them.",
            stage=state.stage,
        ))

    return alerts


def _stage_description(
    stage: JourneyStage, state: JourneyState, policy: NormalizedPolicy
) -> str:
    if stage is JourneyStage.ADMITTED:
        room = state.room_category.label if state.room_category else "a room"
        return f"Admitted to {room}" + (
            f" at {format_inr(state.room_rate_per_day)} a day."
            if state.room_rate_per_day else "."
        )
    if stage is JourneyStage.SETTLED:
        return f"Total billed {format_inr(state.accrued_total)}."
    if stage is JourneyStage.PRE_AUTH:
        return "Waiting for your insurer to approve cashless treatment."
    return stage.label
