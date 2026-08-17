"""The care journey: stage transitions, accrued cost, and the alerts they raise.

This module exists because the tracker had no tests and a real defect hid in
that gap: `advance` passed `stage=` to the event bus, which already takes it
positionally, so every stage change raised a TypeError before it could do
anything. The suite passed, and the button did nothing.

So the first thing asserted here is that each function actually publishes.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.core.events import bus
from app.journey import tracker
from app.schemas.journey import STAGE_TRANSITIONS, AlertSeverity, JourneyStage
from app.schemas.policy import (
    ExpenseHead,
    NormalizedPolicy,
    RoomCategory,
    RoomLimit,
    RoomLimitBasis,
)

D = Decimal


def make_policy(sum_insured="500000", room_cap="5000", copay="0") -> NormalizedPolicy:
    return NormalizedPolicy(
        sum_insured=D(sum_insured),
        room_limit=RoomLimit(
            basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=D(room_cap)
        ),
        copay_pct=D(copay),
    )


def start(policy=None, *, room_rate="8000"):
    return tracker.start_journey(
        policy or make_policy(),
        session_id="testsession",
        hospital_id="H0001",
        hospital_name="Ashwin Multispeciality",
        procedure_code="CARD001",
        room_category=RoomCategory.SINGLE_PRIVATE,
        room_rate_per_day=D(room_rate),
    )


# --- transitions ------------------------------------------------------------


def test_a_journey_starts_before_admission():
    state = start()
    assert state.stage is JourneyStage.PRE_ADMISSION
    assert state.accrued_total == D(0)


def test_advance_moves_the_stage():
    """The regression this module was written for."""
    state = start()
    tracker.advance(state, JourneyStage.ADMITTED, make_policy())
    assert state.stage is JourneyStage.ADMITTED


def test_advance_publishes_an_event_rather_than_raising():
    """The defect was a TypeError inside the publish call, not in the logic."""
    state = start()
    before = len(bus.history("testsession"))

    tracker.advance(state, JourneyStage.ADMITTED, make_policy())

    events = bus.history("testsession")
    assert len(events) > before
    assert any(e.step == "advance_stage" for e in events)


def test_the_published_event_records_both_ends_of_the_move():
    state = start()
    tracker.advance(state, JourneyStage.ADMITTED, make_policy())

    event = next(
        e for e in reversed(bus.history("testsession")) if e.step == "advance_stage"
    )
    assert event.detail["from_stage"] == "pre_admission"
    assert event.detail["to_stage"] == "admitted"


def test_a_whole_journey_can_be_walked_to_settlement():
    """Every stage in turn, which is what a real admission does."""
    policy = make_policy()
    state = start(policy)
    seen = [state.stage]

    # Forward only. The graph legitimately allows going back, so always taking
    # the lowest-order option would oscillate between investigation and
    # pre-authorisation rather than reaching settlement.
    while STAGE_TRANSITIONS[state.stage]:
        ahead = [
            s for s in STAGE_TRANSITIONS[state.stage] if s.order > state.stage.order
        ]
        if not ahead:
            break
        tracker.advance(state, min(ahead, key=lambda s: s.order), policy)
        seen.append(state.stage)

    assert seen[0] is JourneyStage.PRE_ADMISSION
    assert seen[-1] is JourneyStage.SETTLED
    # One timeline entry per stage: starting the journey writes the first.
    assert [e.stage for e in state.timeline] == seen


def test_an_illegal_transition_is_refused():
    state = start()
    with pytest.raises(tracker.TransitionError):
        tracker.advance(state, JourneyStage.SETTLED, make_policy())
    assert state.stage is JourneyStage.PRE_ADMISSION


def test_the_refusal_names_what_is_allowed():
    state = start()
    with pytest.raises(tracker.TransitionError, match="admitted"):
        tracker.advance(state, JourneyStage.SETTLED, make_policy())


def test_admission_is_timestamped():
    state = start()
    tracker.advance(state, JourneyStage.ADMITTED, make_policy())
    assert state.admitted_at is not None


def test_each_stage_appends_to_the_timeline():
    policy = make_policy()
    state = start(policy)
    tracker.advance(state, JourneyStage.ADMITTED, policy)
    tracker.advance(state, JourneyStage.INVESTIGATION, policy)

    # Starting the journey records the first entry, so the opening stage is
    # part of the history a user reads back.
    assert [e.stage for e in state.timeline] == [
        JourneyStage.PRE_ADMISSION,
        JourneyStage.ADMITTED,
        JourneyStage.INVESTIGATION,
    ]


# --- accrued cost -----------------------------------------------------------


def test_recording_a_cost_accrues_it():
    policy = make_policy()
    state = start(policy)
    tracker.record_cost(state, ExpenseHead.ROOM_RENT, D("18000"), policy)
    assert state.accrued_total == D("18000")


def test_costs_accumulate_across_entries():
    policy = make_policy()
    state = start(policy)
    for _ in range(3):
        tracker.record_cost(state, ExpenseHead.ROOM_RENT, D("18000"), policy)
    assert state.accrued_total == D("54000")
    assert len(state.costs) == 3


def test_recording_a_cost_publishes_too():
    policy = make_policy()
    state = start(policy)
    tracker.record_cost(state, ExpenseHead.PHARMACY, D("2500"), policy)
    assert any(e.step == "record_cost" for e in bus.history("testsession"))


def test_money_stays_decimal():
    policy = make_policy()
    state = start(policy)
    tracker.record_cost(state, ExpenseHead.ROOM_RENT, D("18000.50"), policy)
    assert isinstance(state.accrued_total, Decimal)


# --- burn down --------------------------------------------------------------


def test_burn_down_reports_what_is_left():
    policy = make_policy(sum_insured="500000")
    state = start(policy)
    tracker.record_cost(state, ExpenseHead.ROOM_RENT, D("100000"), policy)

    burn = tracker.burn_down(state, policy)

    assert burn.sum_insured == D("500000")
    assert burn.consumed == D("100000")
    assert burn.remaining == D("400000")
    assert burn.consumed_fraction == pytest.approx(0.2)


def test_burn_down_never_reports_negative_cover():
    """Spending past the cover is a real case; a negative balance is not."""
    policy = make_policy(sum_insured="100000")
    state = start(policy)
    tracker.record_cost(state, ExpenseHead.ROOM_RENT, D("250000"), policy)

    burn = tracker.burn_down(state, policy)
    assert burn.remaining >= D(0)
    assert burn.will_exceed


# --- alerts -----------------------------------------------------------------


def test_a_room_above_the_cap_raises_an_alert_with_a_figure():
    """The room is 8,000 a day against a 5,000 cap, so this must be said."""
    policy = make_policy(room_cap="5000")
    state = start(policy, room_rate="8000")
    tracker.advance(state, JourneyStage.ADMITTED, policy)

    alerts = tracker.evaluate(state, policy)

    assert alerts, "an over-cap room must raise something"
    assert any(a.amount is not None for a in alerts), (
        "an alert without a rupee figure is not actionable"
    )


def test_a_room_within_the_cap_raises_no_room_alert():
    policy = make_policy(room_cap="10000")
    state = start(policy, room_rate="8000")
    tracker.advance(state, JourneyStage.ADMITTED, policy)

    alerts = tracker.evaluate(state, policy)
    assert not any("room" in a.title.lower() for a in alerts)


def test_filing_pre_auth_is_remembered():
    policy = make_policy()
    state = start(policy)
    assert not state.pre_auth_filed
    state.pre_auth_filed = True
    state.active_alerts = tracker.evaluate(state, policy)
    assert state.pre_auth_filed


def test_every_alert_carries_an_action():
    """An alert the reader cannot act on is noise at the worst moment."""
    policy = make_policy(sum_insured="100000", room_cap="2000")
    state = start(policy, room_rate="12000")
    tracker.advance(state, JourneyStage.ADMITTED, policy)
    tracker.record_cost(state, ExpenseHead.ROOM_RENT, D("90000"), policy)

    for alert in tracker.evaluate(state, policy):
        assert alert.action, f"{alert.title} has no action"
        assert alert.message


def test_nearing_the_cover_limit_is_flagged_urgently():
    policy = make_policy(sum_insured="100000")
    state = start(policy)
    tracker.record_cost(state, ExpenseHead.ROOM_RENT, D("95000"), policy)

    alerts = tracker.evaluate(state, policy)
    assert any(a.severity is AlertSeverity.URGENT for a in alerts)
