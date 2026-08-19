"""Stage guidance carrying this policy's own figures.

Advice about hospital admissions in general is available everywhere and helps
nobody: "keep your documents safe" is true of every policy ever written. What is
not available anywhere is "ask for a room at or under Rs 5,000 a day", and that
is the sentence deciding how much of the rest of the bill the insurer pays.

So these check that the list is built from the compiled policy rather than
printed from a template, that an item which does not apply is absent rather than
shown and ignored, and that a tick survives.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal as D

import pytest
from fastapi.testclient import TestClient

from app.journey import checklist
from app.main import app
from app.schemas.journey import JourneyStage, JourneyState
from app.schemas.policy import (
    ExpenseHead,
    NormalizedPolicy,
    RoomLimit,
    RoomLimitBasis,
    SubLimit,
)
from app.schemas.simulation import SettlementMode


def a_policy(**kw) -> NormalizedPolicy:
    defaults = dict(
        sum_insured=D(500000),
        room_limit=RoomLimit(basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=D(5000)),
        pre_hospitalisation_days=30,
        post_hospitalisation_days=90,
    )
    policy = NormalizedPolicy(**{**defaults, **kw})
    policy.meta.insurer_name = "Nivaran Health"
    return policy


def a_stay(stage: JourneyStage, **kw) -> JourneyState:
    return JourneyState(stage=stage, **kw)


def texts(items) -> str:
    return " || ".join(item.text for item in items)


def ids(items) -> set[str]:
    return {item.item_id for item in items}


# --- built from the policy, not from a template ----------------------------


def test_the_room_cap_appears_as_the_figure_to_ask_for():
    items = checklist.items_for(a_stay(JourneyStage.PRE_ADMISSION), a_policy())
    assert "₹5,000 a day or less" in texts(items)


def test_a_policy_with_no_room_cap_does_not_ask_for_one():
    """An instruction that does not apply costs the same attention as one that
    does."""
    policy = a_policy(room_limit=RoomLimit(basis=RoomLimitBasis.NO_LIMIT))
    items = checklist.items_for(a_stay(JourneyStage.PRE_ADMISSION), policy)
    assert "ask_for_room" not in ids(items)


def test_the_insurer_is_named():
    items = checklist.items_for(a_stay(JourneyStage.PRE_ADMISSION), a_policy())
    assert "Nivaran Health" in texts(items)


def test_the_diagnostics_sublimit_becomes_the_number_to_quote():
    policy = a_policy(sublimits=[
        SubLimit(head=ExpenseHead.INVESTIGATIONS, label="Tests", amount=D(20000))
    ])
    items = checklist.items_for(a_stay(JourneyStage.ADMITTED), policy)
    assert "₹20,000" in texts(items)
    # Among the urgent few, not buried under the general advice: a sub-limit
    # crossed is crossed, and nobody is told at the time.
    quoted = next(i for i in items if i.item_id == "diagnostics_sublimit")
    assert quoted.urgent
    assert items.index(quoted) < len([i for i in items if i.urgent])


def test_a_policy_without_that_sublimit_quotes_no_number():
    items = checklist.items_for(a_stay(JourneyStage.ADMITTED), a_policy())
    assert "diagnostics_sublimit" not in ids(items)


def test_the_post_hospitalisation_window_becomes_a_date():
    """"Ninety days" is a duration. "Until 8 November" is an instruction."""
    stay = a_stay(
        JourneyStage.DISCHARGE_PLANNING,
        admitted_at=datetime(2026, 8, 10, tzinfo=UTC),
    )
    items = checklist.items_for(stay, a_policy())
    post = next(i for i in items if i.item_id == "post_window")
    assert "08 November" in post.text
    # The wording changes with the date, so the key has to as well: a
    # sentence naming a day and one counting days are not one sentence.
    assert post.string_key == "post_window_until"
    assert post.values["days"] == "90"
    # And the machine form beside it, because "08 November" is an English month
    # name wherever it has been dropped into a sentence. The browser writes the
    # date out of this one in whatever language it is reading in.
    assert post.values["until_iso"] == "2026-11-08"


def test_a_policy_with_no_post_window_says_nothing_about_one():
    policy = a_policy(post_hospitalisation_days=0)
    items = checklist.items_for(a_stay(JourneyStage.DISCHARGE_PLANNING), policy)
    assert "post_window" not in ids(items)


def test_consumables_are_only_mentioned_when_they_are_yours_to_pay():
    covered = a_policy(covers_consumables=True)
    not_covered = a_policy(covers_consumables=False)
    assert "expect_consumables" not in ids(
        checklist.items_for(a_stay(JourneyStage.PRE_ADMISSION), covered)
    )
    assert "expect_consumables" in ids(
        checklist.items_for(a_stay(JourneyStage.PRE_ADMISSION), not_covered)
    )


# --- the discharge list ----------------------------------------------------


def test_the_discharge_list_covers_what_cannot_be_done_afterwards():
    """A discharge summary can be requested again. An itemised bill from a
    hospital that has already been paid, in practice, cannot."""
    items = ids(checklist.items_for(a_stay(JourneyStage.DISCHARGE_PLANNING), a_policy()))
    assert {"discharge_summary", "itemised_bill", "originals"} <= items


def test_a_reimbursement_claim_is_warned_about_its_deadline():
    items = checklist.items_for(
        a_stay(JourneyStage.DISCHARGE_PLANNING), a_policy(),
        settlement=SettlementMode.REIMBURSEMENT,
    )
    assert "claim_deadline" in ids(items)
    assert "final_approval" not in ids(items)


def test_a_cashless_claim_is_told_to_read_before_signing_instead():
    items = checklist.items_for(
        a_stay(JourneyStage.DISCHARGE_PLANNING), a_policy(),
        settlement=SettlementMode.CASHLESS,
    )
    assert "final_approval" in ids(items)
    assert "claim_deadline" not in ids(items)


def test_the_deduction_check_appears_only_where_a_room_cap_could_bite():
    with_room = a_stay(JourneyStage.DISCHARGE_PLANNING, room_rate_per_day=D(6000))
    assert "check_deduction" in ids(checklist.items_for(with_room, a_policy()))

    no_cap = a_policy(room_limit=RoomLimit(basis=RoomLimitBasis.NO_LIMIT))
    assert "check_deduction" not in ids(checklist.items_for(with_room, no_cap))


# --- ordering and ticking --------------------------------------------------


def test_the_urgent_items_come_first_and_the_done_ones_last():
    stay = a_stay(JourneyStage.PRE_ADMISSION)
    stay.checklist_done = ["carry_card"]
    items = checklist.items_for(stay, a_policy())
    assert items[0].urgent and not items[0].done
    assert items[-1].done


def test_progress_counts_what_is_ticked():
    stay = a_stay(JourneyStage.PRE_ADMISSION)
    stay.checklist_done = ["carry_card", "confirm_network"]
    items = checklist.items_for(stay, a_policy())
    assert checklist.progress(items) == (2, len(items))


def test_a_tick_from_another_stage_does_not_count_here():
    stay = a_stay(JourneyStage.ADMITTED)
    stay.checklist_done = ["carry_card"]
    items = checklist.items_for(stay, a_policy())
    assert all(not item.done for item in items)


def test_every_stage_has_something_to_say():
    """A stage with an empty list reads as a broken screen."""
    for stage in JourneyStage:
        items = checklist.items_for(a_stay(stage), a_policy())
        assert items, f"{stage.value} has no guidance"
        assert all(item.why for item in items), f"{stage.value} has an item with no reason"


# --- through the API -------------------------------------------------------


@pytest.fixture
def stay():
    with TestClient(app) as client:
        session_id = client.post("/api/policy/manual", json={
            "sum_insured": 500000, "room_limit_type": "flat",
            "room_limit_amount": 5000,
        }).json()["session_id"]

        reference = client.get("/api/reference").json()
        code = reference["procedures"][0]["code"]
        found = client.post(f"/api/search/{session_id}", json={
            "procedure_code": code, "lat": 12.9716, "lon": 77.5946,
            "city": "Bengaluru", "max_distance_km": 25,
            "preference": "balanced", "urgency": "planned",
        }).json()
        option = found["options"][0]
        journey = client.post(f"/api/journey/{session_id}/start", json={
            "hospital_id": option["hospital"]["id"], "procedure_code": code,
            "room_category": option["room"]["category"],
        }).json()
        yield client, session_id, journey


def test_the_journey_carries_its_checklist(stay):
    _, _, journey = stay
    assert journey["checklist"]["total"] > 0
    assert journey["checklist"]["done"] == 0
    assert all(item["why"] for item in journey["checklist"]["items"])


def test_ticking_an_item_is_remembered(stay):
    client, session_id, journey = stay
    first = journey["checklist"]["items"][0]["id"]

    after = client.post(f"/api/journey/{session_id}/checklist",
                        json={"item_id": first, "done": True}).json()
    assert after["checklist"]["done"] == 1

    reloaded = client.get(f"/api/journey/{session_id}").json()
    assert reloaded["checklist"]["done"] == 1


def test_an_item_can_be_unticked(stay):
    client, session_id, journey = stay
    first = journey["checklist"]["items"][0]["id"]
    client.post(f"/api/journey/{session_id}/checklist",
                json={"item_id": first, "done": True})
    after = client.post(f"/api/journey/{session_id}/checklist",
                        json={"item_id": first, "done": False}).json()
    assert after["checklist"]["done"] == 0


def test_ticking_the_same_item_twice_counts_once(stay):
    client, session_id, journey = stay
    first = journey["checklist"]["items"][0]["id"]
    for _ in range(3):
        after = client.post(f"/api/journey/{session_id}/checklist",
                            json={"item_id": first, "done": True}).json()
    assert after["checklist"]["done"] == 1


def test_the_list_changes_when_the_stage_does(stay):
    client, session_id, journey = stay
    before = {i["id"] for i in journey["checklist"]["items"]}
    moved = client.post(f"/api/journey/{session_id}/advance", json={
        "stage": "discharge_planning", "confirm_skip": True,
    }).json()
    after = {i["id"] for i in moved["checklist"]["items"]}
    assert after != before
    assert "discharge_summary" in after


def test_a_tick_survives_the_browser_handing_the_session_back(stay):
    """The device is the durable copy, so the ticks have to come back with it."""
    client, session_id, journey = stay
    first = journey["checklist"]["items"][0]["id"]
    client.post(f"/api/journey/{session_id}/checklist",
                json={"item_id": first, "done": True})

    snapshot = client.get(f"/api/session/{session_id}/export").json()["snapshot"]
    revived = client.post("/api/session/import", json={"snapshot": snapshot}).json()
    assert revived["journey"]["checklist"]["done"] == 1
