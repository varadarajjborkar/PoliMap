"""The tracker and the estimator must agree, and the projection must be sane.

Two defects motivate this file.

The tracker summed recorded charges and reported the total, which is the
hospital's number rather than the family's, while the estimator on the previous
screen had already worked out what the insurer would allow. A room rate typed at
a billing counter was stored and compared to nothing at all, so a family could
enter nine thousand a day against a five thousand limit and be told nothing.

The projection divided everything accrued by days elapsed. A seventy thousand
rupee operation on day one therefore became a seventy thousand rupee daily rate,
and a family whose cover was fine was told it was about to run out.
"""

from __future__ import annotations

from decimal import Decimal

from app.journey import position, tracker
from app.schemas.journey import JourneyStage, JourneyState
from app.schemas.policy import (
    ExpenseHead,
    NormalizedPolicy,
    RoomCategory,
    RoomLimit,
    RoomLimitBasis,
)


def make_policy(*, room_cap: str = "5000", cover: str = "500000") -> NormalizedPolicy:
    return NormalizedPolicy(
        sum_insured=Decimal(cover),
        room_limit=RoomLimit(
            basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=Decimal(room_cap)
        ),
    )


def admitted_state(*, booked_rate: str = "1430") -> JourneyState:
    return JourneyState(
        stage=JourneyStage.ADMITTED,
        hospital_id="H00001",
        hospital_name="Test General Hospital",
        procedure_code="CP-TEST-001",
        room_category=RoomCategory.SINGLE_PRIVATE,
        room_rate_per_day=Decimal(booked_rate),
        days_elapsed=3,
    )


def charge(state: JourneyState, head: ExpenseHead, amount: str, policy) -> None:
    tracker.record_cost(state, head, Decimal(amount), policy)


# --- the room rate actually billed ------------------------------------------


def test_the_room_rate_comes_from_what_was_recorded():
    """Not from the tariff captured at admission. They disagree exactly when
    it matters: a patient moved room, or a hospital billing another rate."""
    policy = make_policy()
    state = admitted_state(booked_rate="1430")
    for _ in range(3):
        charge(state, ExpenseHead.ROOM_RENT, "9000", policy)

    assert position.observed_room_rate(state) == Decimal("9000")


def test_the_booked_rate_stands_when_no_room_charge_is_recorded():
    state = admitted_state(booked_rate="1430")
    assert position.observed_room_rate(state) == Decimal("1430")


def test_a_room_above_the_limit_raises_the_deduction_alert():
    """The defect: this stayed silent because it tested the booked rate."""
    policy = make_policy(room_cap="5000")
    state = admitted_state(booked_rate="1430")
    for _ in range(3):
        charge(state, ExpenseHead.ROOM_RENT, "9000", policy)
    charge(state, ExpenseHead.SURGEON_FEE, "70000", policy)

    alerts = tracker.evaluate(state, policy)
    over_limit = [a for a in alerts if "costs more than your policy covers" in a.title]
    assert len(over_limit) == 1

    message = over_limit[0].message
    assert "₹9,000" in message
    assert "₹5,000" in message
    # The knock-on across room-linked heads is the part nobody sees coming.
    assert "surgeon" in message.lower()


def test_a_booked_rate_that_contradicts_the_charges_is_flagged():
    policy = make_policy()
    state = admitted_state(booked_rate="1430")
    for _ in range(3):
        charge(state, ExpenseHead.ROOM_RENT, "9000", policy)

    titles = [a.title for a in tracker.evaluate(state, policy)]
    assert any("billing at a different rate" in t for t in titles)


def test_small_billing_differences_are_not_flagged_as_contradictions():
    policy = make_policy()
    state = admitted_state(booked_rate="5000")
    charge(state, ExpenseHead.ROOM_RENT, "5200", policy)

    assert position.room_rate_conflict(state) is None


# --- one engine, not two ----------------------------------------------------


def test_recorded_charges_are_adjudicated_not_merely_summed():
    policy = make_policy(room_cap="5000")
    state = admitted_state()
    for _ in range(3):
        charge(state, ExpenseHead.ROOM_RENT, "9000", policy)
    charge(state, ExpenseHead.SURGEON_FEE, "70000", policy)
    charge(state, ExpenseHead.PHARMACY, "6000", policy)

    result = position.position(state, policy)
    assert result is not None

    # The gross total is what the hospital billed.
    assert result.bill.total == Decimal("103000")
    # What the family owes is smaller, and is reached through stated steps.
    assert result.out_of_pocket > 0
    assert result.payable_by_insurer < result.bill.total
    assert result.reconciles()

    kinds = {s.kind.value for s in result.steps}
    assert "room_rent_cap" in kinds
    assert "proportionate" in kinds


def test_nothing_recorded_yet_means_no_position_rather_than_a_zero():
    policy = make_policy()
    assert position.position(admitted_state(), policy) is None


def test_a_scheme_beneficiary_is_not_adjudicated_against_the_bill():
    """Under a package rate the hospital cannot bill these items to the family,
    so deducting from them would invent an exposure that does not exist."""
    policy = make_policy()
    policy.government_scheme = "pmjay"

    state = admitted_state()
    charge(state, ExpenseHead.PHARMACY, "6000", policy)

    assert position.position(state, policy) is None


# --- the projection ---------------------------------------------------------


def test_one_off_charges_do_not_become_a_daily_rate():
    """A surgeon is not paid again tomorrow because the patient is still in bed."""
    policy = make_policy()
    state = admitted_state()
    for _ in range(3):
        charge(state, ExpenseHead.ROOM_RENT, "9000", policy)
    charge(state, ExpenseHead.SURGEON_FEE, "70000", policy)
    charge(state, ExpenseHead.PHARMACY, "6000", policy)

    # Recurring only: 27,000 room + 6,000 pharmacy over three days.
    assert tracker.daily_run_rate(state) == Decimal("11000")
    # The naive figure would have been 103,000 / 3, over three times higher.
    assert tracker.daily_run_rate(state) < state.accrued_total / Decimal(3)


def test_the_projection_uses_the_recurring_rate():
    policy = make_policy()
    state = admitted_state()
    for _ in range(3):
        charge(state, ExpenseHead.ROOM_RENT, "3000", policy)
    charge(state, ExpenseHead.IMPLANTS, "90000", policy)

    burn = tracker.burn_down(state, policy)
    # 99,000 accrued, 3,000 a day recurring, two days ahead.
    assert burn.consumed == Decimal("99000")
    assert burn.projected_total == Decimal("105000")


def test_days_of_cover_left_is_a_number_a_family_can_act_on():
    policy = make_policy(cover="100000")
    state = admitted_state()
    for _ in range(2):
        charge(state, ExpenseHead.ROOM_RENT, "10000", policy)
    state.days_elapsed = 2

    # 80,000 left at 10,000 a day.
    assert tracker.days_until_cover_exhausted(state, policy) == 8


def test_no_recurring_spend_means_no_exhaustion_date_rather_than_a_guess():
    policy = make_policy()
    state = admitted_state()
    charge(state, ExpenseHead.SURGEON_FEE, "70000", policy)

    assert tracker.days_until_cover_exhausted(state, policy) is None


def test_a_settled_journey_projects_nothing_further():
    policy = make_policy()
    state = admitted_state()
    charge(state, ExpenseHead.PHARMACY, "6000", policy)
    state.stage = JourneyStage.SETTLED

    burn = tracker.burn_down(state, policy)
    assert burn.projected_total == burn.consumed
