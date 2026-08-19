"""Two policies on one admission.

A great many Indian families hold more than one: an employer's group cover and
a personal policy, or a modest base with a top-up above it. Only one was ever
consulted, because every tool that reads a policy reads one policy, and the
second sits in a drawer while the family pays a bill it would have covered.

The dangerous mistakes here are arithmetic ones that look plausible: applying a
top-up's deductible twice, or recommending an order no insurer would accept.
"""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from app.pipeline.s6_simulate import stack
from app.pipeline.s6_simulate.waterfall import simulate
from app.schemas.policy import NormalizedPolicy, RoomLimit, RoomLimitBasis
from app.schemas.simulation import BillLine, EstimatedBill, ExpenseHead, RoomCategory

# The canonical bill used across the deduction tests: a five-night stay in a
# ₹8,000 room, ₹1,10,000 of room-linked charges and ₹50,000 that is exempt.
BILL = EstimatedBill(
    hospital_id="H1", procedure_code="CP-CARD-007",
    room_category=RoomCategory.SINGLE_PRIVATE, los_days=5, icu_days=0,
    room_rate_per_day=D(8000),
    lines=[
        BillLine(head=ExpenseHead.ROOM_RENT, label="Room", amount=D(40000)),
        BillLine(head=ExpenseHead.SURGEON_FEE, label="Surgeon", amount=D(60000)),
        BillLine(head=ExpenseHead.OT_CHARGES, label="Theatre", amount=D(30000)),
        BillLine(head=ExpenseHead.NURSING, label="Nursing", amount=D(20000)),
        BillLine(head=ExpenseHead.PHARMACY, label="Medicines", amount=D(25000)),
        BillLine(head=ExpenseHead.INVESTIGATIONS, label="Tests", amount=D(15000)),
        BillLine(head=ExpenseHead.IMPLANTS, label="Implants", amount=D(10000)),
    ],
)


def policy(name: str, **kw) -> NormalizedPolicy:
    defaults = dict(
        sum_insured=D(500000),
        room_limit=RoomLimit(basis=RoomLimitBasis.NO_LIMIT),
    )
    made = NormalizedPolicy(**{**defaults, **kw})
    made.meta.insurer_name = name
    return made


CAPPED = policy(
    "Sentinel Health", sum_insured=D(300000),
    room_limit=RoomLimit(basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=D(5000)),
)
TOP_UP = policy("Nivaran", sum_insured=D(1500000), deductible=D(100000))


# --- what the first policy leaves --------------------------------------------


def test_the_residual_is_carried_head_by_head():
    """A second policy adjudicates against its own room cap and sub-limits, and
    one combined figure cannot be adjudicated."""
    alone = simulate(CAPPED, BILL)
    assert alone.out_of_pocket == D(56250)
    assert sum(alone.unpaid.values()) == alone.out_of_pocket
    # The room cap and the proportionate deduction it triggers, and nothing on
    # the heads the 2024 circular exempts.
    assert ExpenseHead.ROOM_RENT in alone.unpaid
    assert ExpenseHead.SURGEON_FEE in alone.unpaid
    assert ExpenseHead.PHARMACY not in alone.unpaid
    assert ExpenseHead.IMPLANTS not in alone.unpaid


def test_the_residual_bill_keeps_the_room_actually_occupied():
    """The second policy caps the room somebody slept in, not whatever fraction
    of the room rent is still outstanding."""
    alone = simulate(CAPPED, BILL)
    residual = stack.residual_bill(BILL, alone)
    assert residual.room_rate_per_day == BILL.room_rate_per_day
    assert residual.los_days == BILL.los_days
    assert residual.total == alone.out_of_pocket


def test_a_fully_paid_bill_leaves_nothing_behind():
    generous = policy("Generous", sum_insured=D(1000000))
    result = simulate(generous, BILL)
    assert result.out_of_pocket == 0
    assert stack.residual_bill(BILL, result).total == 0


# --- the top-up ---------------------------------------------------------------


def test_a_top_up_settles_the_balance_the_base_could_not():
    """What a super top-up is for, and what families do not realise they have."""
    settled = stack.settle_across([CAPPED, TOP_UP], BILL)
    assert settled.legs[0].label.startswith("Sentinel Health")
    assert settled.legs[1].pays == D(56250)
    assert settled.out_of_pocket == 0


def test_the_deductible_is_not_charged_twice():
    """It is a band on the whole bill, not on the fraction reaching this
    insurer. Applied again to the residual it is the difference between a
    top-up paying the entire balance and paying nothing at all."""
    settled = stack.settle_across([CAPPED, TOP_UP], BILL)
    # The base paid ₹1,43,750, well through the ₹1,00,000 band.
    assert settled.legs[0].pays == D(143750)
    assert settled.legs[1].pays > 0


def test_a_top_up_is_never_put_first():
    """It pays only above a band somebody else covers, so leading with it is
    not an option an insurer entertains, however well the arithmetic comes out."""
    for order in ([CAPPED, TOP_UP], [TOP_UP, CAPPED]):
        settled = stack.settle_across(order, BILL)
        assert settled.legs[0].policy_id == CAPPED.policy_id
        assert settled.legs[1].policy_id == TOP_UP.policy_id
        assert "top-up" in settled.legs[1].label
        assert "has to be that way round" in settled.order_note.text


def test_a_top_up_alone_above_an_unmet_band_pays_nothing():
    small = policy("Small", sum_insured=D(20000))
    settled = stack.settle_across([small, TOP_UP], BILL)
    # ₹20,000 nowhere near the ₹1,00,000 band, so the top-up still has
    # ₹80,000 of it left to absorb before paying anything.
    assert settled.legs[0].pays == D(20000)
    assert settled.out_of_pocket > 0


# --- when the order is genuinely open -----------------------------------------


def test_the_cheaper_order_is_chosen_and_the_difference_stated():
    """The advice people are given, claim from the corporate policy first, is a
    rule of thumb that a nearly spent policy turns upside down."""
    nearly_spent = policy("Nearly Spent", sum_insured_remaining=D(50000))
    copay_heavy = policy("Twenty Per Cent", copay_pct=D(20))

    settled = stack.settle_across([nearly_spent, copay_heavy], BILL)
    assert settled.legs[0].label.startswith("Twenty Per Cent")
    assert settled.out_of_pocket == 0
    assert settled.alternative_out_of_pocket == D(30000)
    assert "other way round" in settled.order_note.text


def test_the_same_result_whichever_way_they_are_handed_in():
    nearly_spent = policy("Nearly Spent", sum_insured_remaining=D(50000))
    copay_heavy = policy("Twenty Per Cent", copay_pct=D(20))
    forward = stack.settle_across([nearly_spent, copay_heavy], BILL)
    backward = stack.settle_across([copay_heavy, nearly_spent], BILL)
    assert forward.out_of_pocket == backward.out_of_pocket
    assert forward.legs[0].label == backward.legs[0].label


def test_an_order_that_changes_nothing_says_so():
    settled = stack.settle_across(
        [policy("One"), policy("Two")], BILL
    )
    assert settled.out_of_pocket == 0
    assert settled.alternative_out_of_pocket is None
    assert "the same figure" in settled.order_note.text


# --- the totals hold -----------------------------------------------------------


def test_what_the_policies_pay_and_what_is_left_add_up_to_the_bill():
    settled = stack.settle_across([CAPPED, TOP_UP], BILL)
    assert settled.payable + settled.out_of_pocket == BILL.total
    assert settled.bill_total == BILL.total


def test_two_policies_never_leave_more_owing_than_one():
    """Adding cover cannot cost money. Worth asserting: the residual model has
    every opportunity to double-count a deduction."""
    alone = simulate(CAPPED, BILL)
    both = stack.settle_across([CAPPED, TOP_UP], BILL)
    assert both.out_of_pocket <= alone.out_of_pocket


def test_the_upfront_cash_is_the_whole_bill_if_either_leg_is_a_reimbursement():
    """A family funds the whole bill and waits, whichever insurer eventually
    pays, and that is what decides if they can use the hospital at all."""
    settled = stack.settle_across([CAPPED, TOP_UP], BILL, is_network=False)
    assert settled.cash_to_arrange_upfront == BILL.total


def test_a_cashless_stay_only_needs_the_shortfall_upfront():
    settled = stack.settle_across([CAPPED, TOP_UP], BILL, is_network=True)
    assert settled.cash_to_arrange_upfront == settled.out_of_pocket


def test_both_insurers_have_to_be_told_about_each_other():
    settled = stack.settle_across([CAPPED, TOP_UP], BILL)
    assert any("disclosing the second policy" in note.text for note in settled.notes)


def test_one_policy_is_not_a_stack():
    with pytest.raises(ValueError, match="two policies"):
        stack.settle_across([CAPPED], BILL)


# --- naming them back ----------------------------------------------------------


def test_a_policy_is_named_by_its_insurer_and_plan():
    named = policy("Sentinel Health")
    named.meta.plan_name = "Family Care Optima"
    assert stack.label_for(named) == "Sentinel Health Family Care Optima"


def test_a_top_up_says_so_in_its_name():
    assert stack.label_for(TOP_UP).endswith("(top-up)")


def test_an_unnamed_policy_still_gets_something_to_call_it():
    blank = NormalizedPolicy(sum_insured=D(100000))
    assert stack.label_for(blank)


# --- through the API ---------------------------------------------------------


@pytest.fixture
def api():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        yield client


def _manual(api, **kw):
    body = {
        "sum_insured": 300000, "room_limit_type": "flat",
        # Low enough that any real room exceeds it, so the base policy takes a
        # proportionate deduction and there is something for a second policy to
        # settle. A cap nothing crosses leaves only the non-payable items, which
        # no policy covers and which therefore proves nothing.
        "room_limit_amount": 1200, "insurer_name": "First Insurer",
        **kw,
    }
    return api.post("/api/policy/manual", json=body).json()


def _two_policies(api):
    """A tight base policy and a second with no room cap: the corporate-beside-
    personal case, which is the commonest way to hold two in India."""
    first = _manual(api)
    session_id = first["session_id"]
    _manual(
        api, session_id=session_id, attach=True, insurer_name="Employer Group",
        sum_insured=500000, room_limit_type="none",
    )
    return session_id


def _search(api, session_id, code):
    return api.post(f"/api/search/{session_id}", json={
        "procedure_code": code, "lat": 12.9716, "lon": 77.5946,
        "city": "Bengaluru", "max_distance_km": 25,
        "preference": "balanced", "urgency": "planned",
        # A private room, so the base policy's cap actually bites and there is
        # something for the second policy to settle. Left to itself the matcher
        # picks a room inside the cap, and the only residual is the non-payable
        # items, which no policy covers and which therefore proves nothing.
        "preferred_room": "single_private",
    }).json()


def _expensive_code(api):
    procedures = api.get("/api/reference").json()["procedures"]
    return next(p["code"] for p in procedures if p["code"] == "CP-CARD-006")


def test_a_second_policy_attaches_rather_than_replacing(api):
    session_id = _two_policies(api)
    policy = api.get(f"/api/policy/{session_id}").json()
    assert policy["sum_insured"] == 300000
    assert policy["second_policy"]["label"].startswith("Employer Group")


def test_an_upload_without_attach_does_not_touch_an_existing_policy(api):
    """The two cases arrive looking identical, so adding cover has to be asked
    for rather than inferred: a stale tab must not silently become a stack."""
    first = _manual(api)
    session_id = first["session_id"]
    second = _manual(api, session_id=session_id, sum_insured=999999)
    assert second["session_id"] != session_id
    assert api.get(f"/api/policy/{session_id}").json()["second_policy"] is None


def test_a_second_policy_lowers_what_you_pay(api):
    session_id = _two_policies(api)
    code = _expensive_code(api)
    with_both = _search(api, session_id, code)["options"][0]

    api.delete(f"/api/policy/{session_id}/second")
    alone = _search(api, session_id, code)["options"][0]

    assert with_both["you_pay"] < alone["you_pay"]
    assert with_both["estimated_bill"] == alone["estimated_bill"]


def test_the_waterfall_shows_the_second_policy_paying(api):
    session_id = _two_policies(api)
    option = _search(api, session_id, _expensive_code(api))["options"][0]
    step = next(
        (s for s in option["waterfall"] if s["kind"] == "second_policy"), None
    )
    assert step is not None
    assert "Employer Group" in step["explanation"]


def test_the_order_to_claim_in_is_stated(api):
    session_id = _two_policies(api)
    option = _search(api, session_id, _expensive_code(api))["options"][0]
    assert any("Claim from" in note["text"] for note in option["notes"])


def test_both_insurers_must_be_told_about_each_other_in_the_payload(api):
    session_id = _two_policies(api)
    option = _search(api, session_id, _expensive_code(api))["options"][0]
    assert any("disclosing the second policy" in note["text"] for note in option["notes"])


def test_a_second_policy_can_be_detached(api):
    """Somebody who attached the wrong document should not have to start the
    stay again to say so."""
    session_id = _two_policies(api)
    after = api.delete(f"/api/policy/{session_id}/second").json()
    assert after["second_policy"] is None
    assert after["sum_insured"] == 300000


def test_the_second_policy_survives_the_server_forgetting_the_session(api):
    session_id = _two_policies(api)
    snapshot = api.get(f"/api/session/{session_id}/export").json()["snapshot"]
    revived = api.post("/api/session/import", json={"snapshot": snapshot}).json()
    assert revived["policy"]["second_policy"]["label"].startswith("Employer Group")
