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
from app.schemas.journey import (
    AlertSeverity,
    JourneyStage,
    TransitionKind,
)
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

    # One stage at a time, so nothing is skipped and no confirmation is needed.
    while (nxt := next(
        (s for s in JourneyStage if s.order == state.stage.order + 1), None
    )):
        tracker.advance(state, nxt, policy)
        seen.append(state.stage)

    assert seen[0] is JourneyStage.PRE_ADMISSION
    assert seen[-1] is JourneyStage.SETTLED
    # One timeline entry per stage: starting the journey writes the first.
    assert [e.stage for e in state.timeline] == seen


def test_a_forward_skip_is_refused_until_confirmed():
    """The user is told what they are passing over before it happens."""
    state = start()
    with pytest.raises(tracker.TransitionError):
        tracker.advance(state, JourneyStage.SETTLED, make_policy())
    assert state.stage is JourneyStage.PRE_ADMISSION


def test_the_refusal_names_the_stages_being_skipped():
    state = start()
    with pytest.raises(tracker.TransitionError, match="in hospital, going home"):
        tracker.advance(state, JourneyStage.SETTLED, make_policy())


def test_a_confirmed_skip_goes_through():
    """Real admissions do not follow the diagram, so this must be possible."""
    state = start()
    tracker.advance(state, JourneyStage.DISCHARGE_PLANNING, make_policy(), force=True)
    assert state.stage is JourneyStage.DISCHARGE_PLANNING


def test_a_skip_records_what_was_passed_over():
    state = start()
    tracker.advance(state, JourneyStage.DISCHARGE_PLANNING, make_policy(), force=True)

    event = state.timeline[-1]
    assert event.kind is TransitionKind.SKIP
    assert JourneyStage.ADMITTED in event.skipped
    assert JourneyStage.DISCHARGE_PLANNING not in event.skipped


def test_a_skip_reason_is_kept_when_given():
    state = start()
    tracker.advance(
        state, JourneyStage.DISCHARGE_PLANNING, make_policy(),
        force=True, reason="Admitted through emergency, no time for pre-auth.",
    )
    assert "emergency" in state.timeline[-1].reason


def test_a_skip_reason_is_never_required():
    state = start()
    tracker.advance(state, JourneyStage.DISCHARGE_PLANNING, make_policy(), force=True)
    assert state.timeline[-1].reason == ""


def test_going_back_is_always_allowed():
    """Correcting a mistake must not be harder than making one."""
    policy = make_policy()
    state = start(policy)
    tracker.advance(state, JourneyStage.ADMITTED, policy)
    tracker.advance(state, JourneyStage.SETTLED, policy, force=True)

    tracker.advance(state, JourneyStage.ADMITTED, policy)

    assert state.stage is JourneyStage.ADMITTED
    assert state.timeline[-1].kind is TransitionKind.BACK


def test_going_back_needs_no_confirmation():
    policy = make_policy()
    state = start(policy)
    tracker.advance(state, JourneyStage.ADMITTED, policy)
    tracker.advance(state, JourneyStage.PRE_ADMISSION, policy)
    assert state.stage is JourneyStage.PRE_ADMISSION


def test_moving_to_the_stage_you_are_on_is_refused():
    """The reported defect: the interface offered pre_auth while on pre_auth."""
    policy = make_policy()
    state = start(policy)
    tracker.advance(state, JourneyStage.ADMITTED, policy)

    with pytest.raises(tracker.TransitionError, match="already"):
        tracker.advance(state, JourneyStage.ADMITTED, policy)


def test_the_next_stage_in_sequence_is_the_one_after_it():
    """What the interface preselects. Alphabetical order caused the defect."""
    from app.api.routes import _natural_next

    assert _natural_next(JourneyStage.PRE_ADMISSION) == "admitted"
    assert _natural_next(JourneyStage.ADMITTED) == "discharge_planning"
    assert _natural_next(JourneyStage.DISCHARGE_PLANNING) == "settled"
    assert _natural_next(JourneyStage.SETTLED) is None


def test_skipped_between_is_exclusive_at_both_ends():
    got = tracker.skipped_between(
        JourneyStage.PRE_ADMISSION, JourneyStage.DISCHARGE_PLANNING
    )
    assert got == [JourneyStage.ADMITTED]


def test_a_natural_step_is_not_classed_as_a_skip():
    assert tracker.classify(
        JourneyStage.PRE_ADMISSION, JourneyStage.ADMITTED
    ) is TransitionKind.ADVANCE


def test_an_ordinary_looking_jump_is_still_a_skip():
    """Going straight from choosing a hospital to going home is a perfectly
    normal thing to record after the fact, and it still passes over the whole
    admission. What matters for the warning is what was passed over, not
    whether the jump is unusual."""
    assert tracker.classify(
        JourneyStage.PRE_ADMISSION, JourneyStage.DISCHARGE_PLANNING
    ) is TransitionKind.SKIP


def test_that_jump_needs_confirming_too():
    policy = make_policy()
    state = start(policy)

    with pytest.raises(tracker.TransitionError, match="hospital|admitted"):
        tracker.advance(state, JourneyStage.DISCHARGE_PLANNING, policy)


def test_admission_is_timestamped():
    state = start()
    tracker.advance(state, JourneyStage.ADMITTED, make_policy())
    assert state.admitted_at is not None


def test_each_stage_appends_to_the_timeline():
    policy = make_policy()
    state = start(policy)
    tracker.advance(state, JourneyStage.ADMITTED, policy)
    tracker.advance(state, JourneyStage.DISCHARGE_PLANNING, policy)

    # Starting the journey records the first entry, so the opening stage is
    # part of the history a user reads back.
    assert [e.stage for e in state.timeline] == [
        JourneyStage.PRE_ADMISSION,
        JourneyStage.ADMITTED,
        JourneyStage.DISCHARGE_PLANNING,
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


# --- correcting a charge ----------------------------------------------------


def test_a_charge_can_be_corrected():
    """People mistype amounts at a billing counter. That must be fixable."""
    policy = make_policy()
    state = start(policy)
    entry = tracker.record_cost(state, ExpenseHead.ROOM_RENT, D("1800"), policy)

    tracker.update_cost(state, entry.entry_id, policy, amount=D("18000"))

    assert state.costs[0].amount == D("18000")
    assert state.accrued_total == D("18000")


def test_correcting_the_head_moves_the_charge():
    policy = make_policy()
    state = start(policy)
    entry = tracker.record_cost(state, ExpenseHead.ROOM_RENT, D("2500"), policy)

    tracker.update_cost(state, entry.entry_id, policy, head=ExpenseHead.PHARMACY)

    assert state.costs[0].head is ExpenseHead.PHARMACY
    assert state.accrued_by_head()[ExpenseHead.PHARMACY] == D("2500")


def test_correcting_the_date_is_allowed():
    from datetime import UTC, datetime

    policy = make_policy()
    state = start(policy)
    entry = tracker.record_cost(state, ExpenseHead.ROOM_RENT, D("2500"), policy)
    when = datetime(2026, 3, 4, 9, 30, tzinfo=UTC)

    tracker.update_cost(state, entry.entry_id, policy, recorded_at=when)

    assert state.costs[0].recorded_at == when


def test_fields_not_sent_are_left_alone():
    policy = make_policy()
    state = start(policy)
    entry = tracker.record_cost(
        state, ExpenseHead.ROOM_RENT, D("2500"), policy, description="day one"
    )

    tracker.update_cost(state, entry.entry_id, policy, amount=D("3000"))

    assert state.costs[0].description == "day one"
    assert state.costs[0].head is ExpenseHead.ROOM_RENT


def test_a_charge_can_be_removed():
    policy = make_policy()
    state = start(policy)
    a = tracker.record_cost(state, ExpenseHead.ROOM_RENT, D("18000"), policy)
    tracker.record_cost(state, ExpenseHead.PHARMACY, D("2000"), policy)

    tracker.remove_cost(state, a.entry_id, policy)

    assert len(state.costs) == 1
    assert state.accrued_total == D("2000")


def test_removing_the_last_charge_returns_the_total_to_zero():
    policy = make_policy()
    state = start(policy)
    entry = tracker.record_cost(state, ExpenseHead.ROOM_RENT, D("18000"), policy)
    tracker.remove_cost(state, entry.entry_id, policy)
    assert state.accrued_total == D(0)


def test_editing_an_unknown_charge_is_reported_not_crashed():
    policy = make_policy()
    state = start(policy)
    with pytest.raises(tracker.CostNotFound):
        tracker.update_cost(state, "nosuchentry", policy, amount=D("1"))


def test_removing_an_unknown_charge_is_reported_not_crashed():
    policy = make_policy()
    state = start(policy)
    with pytest.raises(tracker.CostNotFound):
        tracker.remove_cost(state, "nosuchentry", policy)


def test_alerts_are_recomputed_after_a_correction():
    """A correction that clears an over-spend must clear its alert too."""
    policy = make_policy(sum_insured="100000")
    state = start(policy)
    entry = tracker.record_cost(state, ExpenseHead.ROOM_RENT, D("99000"), policy)
    assert any(a.severity is AlertSeverity.URGENT for a in state.active_alerts)

    tracker.update_cost(state, entry.entry_id, policy, amount=D("1000"))

    assert not any(a.severity is AlertSeverity.URGENT for a in state.active_alerts)


def test_a_receipt_name_is_kept_with_the_charge():
    policy = make_policy()
    state = start(policy)
    entry = tracker.record_cost(
        state, ExpenseHead.ROOM_RENT, D("18000"), policy,
        receipt_name="bill-day-one.pdf",
    )
    assert entry.receipt_name == "bill-day-one.pdf"


def test_a_charge_without_a_receipt_says_so_plainly():
    policy = make_policy()
    state = start(policy)
    entry = tracker.record_cost(state, ExpenseHead.ROOM_RENT, D("18000"), policy)
    assert entry.receipt_name == ""


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


# --- stages that no longer exist --------------------------------------------


def test_a_stay_left_in_a_retired_stage_still_opens():
    """The browser holds the durable copy of an admission, so somebody who left
    a tab open across this change hands back a stay in a stage the code has
    never heard of. Refusing it would lose five days of recorded charges to a
    change in the shape of an enum, which is the one failure this application
    must not have."""
    from app.schemas.journey import JourneyState

    for retired in ("investigation", "pre_auth", "procedure", "recovery"):
        state = JourneyState.model_validate({"stage": retired})
        assert state.stage is JourneyStage.ADMITTED


def test_a_recorded_charge_in_a_retired_stage_still_opens():
    from app.schemas.journey import JourneyState

    state = JourneyState.model_validate({
        "stage": "recovery",
        "costs": [{"head": "pharmacy", "amount": "1200", "stage": "procedure"}],
    })
    assert state.costs[0].stage is JourneyStage.ADMITTED
    assert state.accrued_total == Decimal(1200)


def test_a_timeline_written_before_the_change_still_reads_back():
    from app.schemas.journey import JourneyState

    state = JourneyState.model_validate({
        "stage": "discharge_planning",
        "timeline": [
            {"stage": "pre_auth", "title": "Insurance approval",
             "skipped": ["investigation", "procedure"]},
        ],
    })
    assert state.timeline[0].stage is JourneyStage.ADMITTED
    assert all(s is JourneyStage.ADMITTED for s in state.timeline[0].skipped)


def test_a_stage_that_never_existed_is_still_refused():
    """Forgiving a name we retired is not the same as forgiving nonsense."""
    from pydantic import ValidationError

    from app.schemas.journey import JourneyState

    with pytest.raises(ValidationError):
        JourneyState.model_validate({"stage": "convalescing"})


def test_a_whole_session_snapshot_survives_the_change():
    """The path that actually matters: the browser handing back what it kept."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as api:
        session_id = api.post("/api/policy/manual", json={
            "sum_insured": 500000, "room_limit_type": "flat",
            "room_limit_amount": 5000,
        }).json()["session_id"]
        snapshot = api.get(f"/api/session/{session_id}/export").json()["snapshot"]

        # A stay recorded before the stages were reduced, as the device kept it.
        snapshot["journey"] = {
            "journey_id": "old12345ab", "session_id": session_id,
            "stage": "recovery", "hospital_name": "Old General",
            "costs": [{"entry_id": "c1", "head": "room_rent", "amount": "6000",
                       "stage": "investigation"}],
            "timeline": [{"event_id": "e1", "stage": "pre_auth", "title": "Filed"}],
        }
        revived = api.post("/api/session/import", json={"snapshot": snapshot}).json()
        assert revived["journey"]["stage"] == "admitted"
        assert revived["journey"]["accrued"] == 6000
