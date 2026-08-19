"""Care journey tracking with stage-aware, costed guidance.

The insurance position is not static. Costs accrue daily, sub-limits drain, a
room that was affordable on day one is expensive by day five, and
pre-authorisation has a window that closes. This module re-answers "where do I
stand" at every stage instead of once at admission.

Two rules govern what it says.

**Stages are administrative, never clinical.** Admission, investigation,
procedure, recovery describe where the paperwork is. Nothing here infers,
records or reasons about a diagnosis, and no alert ever suggests a course of
treatment: the problem statement rules that out and the distinction is worth
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
from app.journey import position
from app.schemas.events import EventStatus, PipelineStage
from app.schemas.journey import (
    Alert,
    AlertKind,
    AlertSeverity,
    BurnDown,
    CostEntry,
    JourneyEvent,
    JourneyStage,
    JourneyState,
    TransitionKind,
)
from app.schemas.money import ZERO, format_inr, round_inr
from app.schemas.policy import ExpenseHead, NormalizedPolicy, RoomCategory

log = get_logger(__name__)
STAGE = PipelineStage.JOURNEY

SUBLIMIT_WARNING_FRACTION = 0.75
COVER_WARNING_FRACTION = 0.70
COVER_URGENT_FRACTION = 0.90

# Once the patient is in, pre-authorisation should already be filed. Insurers
# require it before a planned procedure and within 24 hours of an emergency
# admission, and a missed window turns a cashless claim into a reimbursement one.
#
# It used to be a stage of its own, which imposed an order that does not exist:
# the request is filed while the patient is admitted and being investigated, not
# in a period between the two. It is a fact about the stay, and this is the
# stage during which the fact matters.
PRE_AUTH_DUE_AT = {JourneyStage.ADMITTED}


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
    cover = format_inr(policy.sum_insured)
    state.timeline.append(JourneyEvent(
        stage=JourneyStage.PRE_ADMISSION,
        title="Planning your care",
        title_key="start",
        description=(
            f"{cover} of cover. Looking at {hospital_name}."
            if hospital_name else f"{cover} of cover."
        ),
        note_key="start_hospital" if hospital_name else "start",
        values={"cover": cover} | ({"hospital": hospital_name} if hospital_name else {}),
    ))
    return state


def skipped_between(current: JourneyStage, target: JourneyStage) -> list[JourneyStage]:
    """Stages a forward move would pass over without visiting."""
    if target.order <= current.order:
        return []
    return [
        s for s in JourneyStage
        if current.order < s.order < target.order
    ]


def classify(current: JourneyStage, target: JourneyStage) -> TransitionKind:
    """What kind of move this is, before deciding whether to allow it.

    Decided purely by what the move passes over. An earlier version consulted
    a table of ordinary transitions, but several of those still jump stages:
    investigation straight to planning discharge is a normal thing to do and
    still skips pre-authorisation, treatment and recovery. Asking the table
    would have stayed silent on exactly the jumps worth mentioning.
    """
    if target.order < current.order:
        return TransitionKind.BACK
    if target.order == current.order + 1:
        return TransitionKind.ADVANCE
    return TransitionKind.SKIP


def advance(
    state: JourneyState,
    target: JourneyStage,
    policy: NormalizedPolicy,
    *,
    note: str = "",
    reason: str = "",
    force: bool = False,
) -> JourneyState:
    """Move to a new stage and recompute the guidance that applies there.

    A real admission does not follow the diagram. People are discharged without
    a procedure, go back to investigation after a complication, and update the
    app hours after the fact. So the model allows three kinds of move:

    * the natural next step, always allowed;
    * a step backwards, always allowed, because correcting a mistake should
      never be harder than making one;
    * a jump forward past stages, allowed only with `force`, which the
      interface sets after telling the user what is being skipped.

    Only moving to the stage you are already on is refused, since that is never
    what anyone meant.
    """
    if target is state.stage:
        raise TransitionError(
            f"You are already at {target.label.lower()}."
        )

    kind = classify(state.stage, target)
    skipped = skipped_between(state.stage, target)

    if kind is TransitionKind.SKIP and not force:
        names = ", ".join(s.label.lower() for s in skipped)
        raise TransitionError(
            f"Moving to {target.label.lower()} skips {names}. "
            f"Confirm to continue."
        )

    previous = state.stage
    state.stage = target

    if target is JourneyStage.ADMITTED and state.admitted_at is None:
        state.admitted_at = datetime.now(UTC)

    alerts = evaluate(state, policy)
    state.active_alerts = alerts

    title, title_key = _transition_title(kind, target)
    described, note_key, values = _stage_description(target, state, policy)
    state.timeline.append(JourneyEvent(
        stage=target,
        title=title,
        title_key=title_key,
        description=note or described,
        # A note the user typed is their own words and is never looked up.
        note_key="" if note else note_key,
        values={"stage": target.label} | values,
        alerts=alerts,
        kind=kind,
        skipped=skipped if kind is TransitionKind.SKIP else [],
        reason=reason.strip(),
    ))

    bus.publish(
        STAGE, "advance_stage", session_id=state.session_id or None,
        status=EventStatus.WARN if any(
            a.severity is AlertSeverity.URGENT for a in alerts
        ) else EventStatus.OK,
        summary=f"{previous.label} to {target.label}"
                + (f", skipping {len(skipped)}" if skipped else "")
                + (f", {len(alerts)} thing{'s' if len(alerts) != 1 else ''} to know"
                   if alerts else ""),
        # Not `stage=`: the bus already takes that as its first positional
        # argument, and passing it again raises before the event is ever built.
        from_stage=previous.value,
        to_stage=target.value,
        kind=kind.value,
        skipped=[s.value for s in skipped],
        alerts=len(alerts),
        accrued=float(state.accrued_total),
    )
    return state


def _transition_title(kind: TransitionKind, target: JourneyStage) -> tuple[str, str]:
    """The heading for this move, and the key it is read under.

    An ordinary move forward has no key: its title is the stage's own name,
    which the interface already knows in every language it speaks.
    """
    if kind is TransitionKind.BACK:
        return f"Back to {target.label.lower()}", "back"
    if kind is TransitionKind.SKIP:
        return f"{target.label} (skipped ahead)", "skipped"
    return target.label, ""


def record_cost(
    state: JourneyState,
    head: ExpenseHead,
    amount: Decimal,
    policy: NormalizedPolicy,
    *,
    description: str = "",
    receipt_name: str = "",
) -> CostEntry:
    """Add an actual charge and re-evaluate the position."""
    entry = CostEntry(
        head=head, amount=amount, description=description, stage=state.stage,
        receipt_name=receipt_name,
    )
    state.costs.append(entry)
    state.active_alerts = evaluate(state, policy)

    bus.publish(
        STAGE, "record_cost", session_id=state.session_id or None,
        summary=f"{head.label} {format_inr(amount)}, "
                f"{format_inr(state.accrued_total)} so far",
        head=head.value, amount=float(amount),
        receipt=bool(receipt_name),
        accrued=float(state.accrued_total),
    )
    return entry


class CostNotFound(LookupError):
    """The charge being edited or removed is not on this journey."""


def _find_cost(state: JourneyState, entry_id: str) -> CostEntry:
    for entry in state.costs:
        if entry.entry_id == entry_id:
            return entry
    raise CostNotFound(entry_id)


def update_cost(
    state: JourneyState,
    entry_id: str,
    policy: NormalizedPolicy,
    *,
    head: ExpenseHead | None = None,
    amount: Decimal | None = None,
    recorded_at: datetime | None = None,
    description: str | None = None,
) -> JourneyState:
    """Correct a charge already recorded.

    People mistype amounts and pick the wrong head, usually while standing at a
    billing counter. Every field passed is applied; the rest are left alone.
    The accrued total is a computed property over the list, so it follows on
    its own and cannot drift from the entries it is meant to summarise.
    """
    entry = _find_cost(state, entry_id)
    before = entry.amount

    if head is not None:
        entry.head = head
    if amount is not None:
        entry.amount = amount
    if recorded_at is not None:
        entry.recorded_at = recorded_at
    if description is not None:
        entry.description = description

    state.active_alerts = evaluate(state, policy)

    bus.publish(
        STAGE, "update_cost", session_id=state.session_id or None,
        summary=f"Charge corrected: {format_inr(before)} to "
                f"{format_inr(entry.amount)}, {format_inr(state.accrued_total)} so far",
        entry=entry_id, head=entry.head.value, amount=float(entry.amount),
        accrued=float(state.accrued_total),
    )
    return state


def remove_cost(
    state: JourneyState, entry_id: str, policy: NormalizedPolicy
) -> JourneyState:
    """Delete a charge that should not have been recorded."""
    entry = _find_cost(state, entry_id)
    state.costs = [c for c in state.costs if c.entry_id != entry_id]
    state.active_alerts = evaluate(state, policy)

    bus.publish(
        STAGE, "remove_cost", session_id=state.session_id or None,
        summary=f"Charge removed: {entry.head.label} {format_inr(entry.amount)}, "
                f"{format_inr(state.accrued_total)} so far",
        entry=entry_id, accrued=float(state.accrued_total),
    )
    return state


# Charges that happen once, whatever the stay length. A surgeon is not paid
# again tomorrow because the patient is still in bed, and a stent is bought
# once. Dividing these by days elapsed and projecting forward is what turns a
# seventy thousand rupee operation on day one into a seventy thousand rupee
# daily rate, which is the kind of number that panics a family for no reason.
_ONE_OFF_HEADS = frozenset({
    ExpenseHead.SURGEON_FEE,
    ExpenseHead.ANAESTHETIST_FEE,
    ExpenseHead.OT_CHARGES,
    ExpenseHead.IMPLANTS,
    ExpenseHead.BLOOD,
})

PROJECTION_HORIZON_DAYS = Decimal(2)
"""How far ahead the projection looks. Deliberately short: a family can act on
what the next two days cost, and a five day forecast built from three days of
data is a guess wearing a number."""


def daily_run_rate(state: JourneyState) -> Decimal:
    """What one more day is likely to cost, from the recurring charges only.

    Separating one-off charges from recurring ones is the whole point. A stay
    where the theatre bill has already landed has a low run rate and a high
    total, and treating those as the same thing produces a projection that is
    wrong by a multiple rather than by a margin.
    """
    days = Decimal(max(state.days_elapsed, 1))
    recurring = sum(
        (c.amount for c in state.costs if c.head not in _ONE_OFF_HEADS), ZERO
    )
    return round_inr(recurring / days)


def burn_down(state: JourneyState, policy: NormalizedPolicy) -> BurnDown:
    """Cover consumed against cover available, projected to discharge.

    Projection uses the observed rate of the *recurring* charges rather than
    the original estimate, because the point of tracking is to notice when
    reality has departed from the plan, and rather than the whole accrued
    total, because most of that total is work already done and not repeatable.
    """
    consumed = state.accrued_total
    available = policy.available_cover

    if state.stage in (JourneyStage.SETTLED, JourneyStage.DISCHARGE_PLANNING):
        projected = consumed
    else:
        projected = round_inr(
            consumed + daily_run_rate(state) * PROJECTION_HORIZON_DAYS
        )

    return BurnDown(
        sum_insured=available,
        consumed=consumed,
        projected_total=max(projected, consumed),
        remaining=max(available - consumed, ZERO),
    )


def days_until_cover_exhausted(
    state: JourneyState, policy: NormalizedPolicy
) -> int | None:
    """How long the remaining cover lasts at the current recurring rate.

    None when nothing recurring is accruing, or when the cover is already gone.
    A number here is worth far more than a percentage: "you cross your cover on
    day six" is something a family can act on, and "82% used" is not.
    """
    rate = daily_run_rate(state)
    if rate <= 0 or not state.is_active:
        return None

    remaining = policy.available_cover - state.accrued_total
    if remaining <= 0:
        return 0
    return int(remaining / rate)


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
    """The proportionate-deduction warning, expressed in money already lost.

    Tested against the rate the recorded charges imply, not the one captured
    from the hospital's tariff at admission. Those disagree exactly when this
    alert matters most: a room rent typed at a billing counter used to be
    stored as an ordinary charge and compared to nothing, so a family paying
    well above their limit was told nothing at all.
    """
    alerts: list[Alert] = []
    if not state.is_active:
        return []

    conflict = position.room_rate_conflict(state)
    if conflict is not None:
        booked, observed = conflict
        alerts.append(Alert(
            kind=AlertKind.ROOM_OVER_LIMIT,
            severity=AlertSeverity.ATTENTION,
            title="Your room is billing at a different rate",
            message=(
                f"This stay was set up at {format_inr(booked)} a day, and the "
                f"charges recorded work out at {format_inr(observed)}. Both "
                f"cannot be right."
            ),
            action=(
                "If you moved room, this is expected. If not, ask the billing "
                "desk which rate applies."
            ),
            key="room_rate_conflict",
            values={"booked": format_inr(booked), "observed": format_inr(observed)},
            stage=state.stage,
        ))

    rate = position.observed_room_rate(state)
    if rate is None:
        return alerts

    cap = policy.room_limit.effective_daily_cap(policy.sum_insured)
    if cap is None or rate <= cap:
        return alerts

    days = max(state.days_elapsed, 1)
    excess = round_inr((rate - cap) * Decimal(days))
    ratio = cap / rate

    room_linked = sum(
        (amount for head, amount in state.accrued_by_head().items()
         if head in _ROOM_LINKED_HEADS),
        ZERO,
    )
    knock_on = round_inr(room_linked * (Decimal(1) - ratio))

    alerts.append(Alert(
        kind=AlertKind.ROOM_OVER_LIMIT,
        severity=AlertSeverity.URGENT,
        title="Your room costs more than your cover",
        message=(
            f"Your room is {format_inr(rate)} a day and you are covered for "
            f"{format_inr(cap)}. After {days} day{'s' if days != 1 else ''} "
            f"that is {format_inr(excess)} in room rent, plus about "
            f"{format_inr(knock_on)} off your surgeon, theatre and nursing."
            + (
                " That second cut lands on charges that are not the room, and "
                "it is the part most people never see coming."
                if knock_on > 0 else ""
            )
        ),
        action=(
            "Ask the insurance desk about a room within your limit. It stops "
            "further cuts from tomorrow."
        ),
        key="room_over_limit_knock_on" if knock_on > 0 else "room_over_limit",
        values={
            "rate": format_inr(rate), "cap": format_inr(cap), "days": str(days),
            "excess": format_inr(excess), "knock_on": format_inr(knock_on),
        },
        amount=round_inr(excess + knock_on),
        clause_ids=policy.room_limit.source_clause_ids,
        stage=state.stage,
    ))
    return alerts


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
                f"You are covered for {format_inr(cap)} of "
                f"{sublimit.head.label.lower()} and {format_inr(spent)} is "
                f"billed, {used:.0%} of it."
            ),
            action=(
                "Anything beyond this is yours to pay. Ask the desk before "
                "more tests are ordered."
            ),
            values={
                "head": sublimit.head.label,
                "head_key": sublimit.head.value,
                "cap": format_inr(cap), "spent": format_inr(spent),
                "pct": f"{used:.0%}",
            },
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
                f"{format_inr(burn.consumed)} of your "
                f"{format_inr(burn.sum_insured)} cover is billed. "
                f"{format_inr(burn.remaining)} is left."
            ),
            action="Ask about discharge planning and what you will owe directly.",
            key="cover_almost_gone",
            values={
                "consumed": format_inr(burn.consumed),
                "total": format_inr(burn.sum_insured),
                "remaining": format_inr(burn.remaining),
            },
            amount=burn.remaining,
            stage=state.stage,
        )]

    if burn.will_exceed and state.is_active:
        days = days_until_cover_exhausted(state, policy)
        rate = daily_run_rate(state)
        return [Alert(
            kind=AlertKind.COVER_NEARLY_EXHAUSTED,
            severity=AlertSeverity.ATTENTION,
            title="Costs are on track to pass your cover",
            message=(
                f"Daily charges are running at about {format_inr(rate)} a day, "
                f"not counting theatre and implants already billed. At that "
                f"rate you cross your {format_inr(burn.sum_insured)} cover "
                + (
                    "today." if days == 0 else
                    f"in about {days} day{'s' if days != 1 else ''}."
                    if days is not None else "during this stay."
                )
            ),
            action=(
                "Worth raising now rather than at discharge: ask about a "
                "top-up, whether a second cover applies, and what the "
                "hospital's instalment desk offers."
            ),
            key=(
                "cover_on_track_today" if days == 0
                else "cover_on_track_days" if days is not None
                else "cover_on_track_soon"
            ),
            values={
                "rate": format_inr(rate),
                "total": format_inr(burn.sum_insured),
                "days": str(days or 0),
            },
            amount=max(burn.projected_total - burn.sum_insured, ZERO),
            stage=state.stage,
        )]

    if burn.consumed_fraction >= COVER_WARNING_FRACTION:
        return [Alert(
            kind=AlertKind.COVER_NEARLY_EXHAUSTED,
            severity=AlertSeverity.ATTENTION,
            title="Most of your cover is used",
            message=f"{format_inr(burn.remaining)} of cover is left this year.",
            action="Keep this in mind if more treatment is needed.",
            key="cover_most_used",
            values={"remaining": format_inr(burn.remaining)},
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
            f"policy repays: gloves, syringes, registration. You pay these "
            f"whatever else is covered."
        ),
        action="Ask for an itemised bill so you can check them.",
        values={"amount": format_inr(non_payable)},
        amount=non_payable,
        stage=state.stage,
    )]


def _stage_alerts(state: JourneyState, policy: NormalizedPolicy) -> list[Alert]:
    alerts: list[Alert] = []

    if state.stage in PRE_AUTH_DUE_AT and not state.pre_auth_filed:
        alerts.append(Alert(
            kind=AlertKind.PRE_AUTH_DUE,
            severity=AlertSeverity.URGENT,
            title="Pre-authorisation needs filing",
            message=(
                "Cashless needs your insurer's approval before the procedure. "
                "Without it you pay the hospital and claim it back later."
            ),
            action="Ask the insurance desk to file it now.",
            stage=state.stage,
        ))

    # The discharge paperwork used to be one alert repeating the same four
    # sentences to everybody. It is now a checklist carrying this policy's own
    # figures and its own deadlines, ticked off as each is dealt with, which is
    # both more use and impossible to state in a single paragraph.

    return alerts


def _stage_description(
    stage: JourneyStage, state: JourneyState, policy: NormalizedPolicy
) -> tuple[str, str, dict[str, str]]:
    """The line under the heading, its key, and what was written into it."""
    if stage is JourneyStage.ADMITTED:
        room = state.room_category.label if state.room_category else "a room"
        values = {"room": room} | (
            {"room_key": state.room_category.value} if state.room_category else {}
        )
        if state.room_rate_per_day:
            rate = format_inr(state.room_rate_per_day)
            return (
                f"Admitted to {room} at {rate} a day.",
                "admitted_rate",
                values | {"rate": rate},
            )
        return f"Admitted to {room}.", "admitted", values
    if stage is JourneyStage.SETTLED:
        total = format_inr(state.accrued_total)
        return f"Total billed {total}.", "settled", {"total": total}
    if stage is JourneyStage.DISCHARGE_PLANNING:
        return "Getting the paperwork ready.", "discharge", {}
    # Nothing useful to add beyond the title the entry already carries, and
    # repeating it under itself only reads as a rendering mistake.
    return "", "", {}
