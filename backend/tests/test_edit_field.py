"""Correcting a figure the system read wrong.

Machines misread documents. When they do, the user is looking straight at the
mistake on their own screen, beside the figure they know to be right, and until
now there was nothing they could do about it. Everything downstream is computed
from these few numbers, so one misread digit poisons every estimate after it
while the user watches.

The properties under test are the ones that make a correction trustworthy: it
accepts what the document says rather than only digits, it cannot introduce a
field, and once made it outranks whatever was extracted so the system stops
asking about something the user has already answered.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.pipeline.s4_compile.edit import NotEditable, Unreadable, edit_field
from app.schemas.policy import (
    ClarificationRequest,
    Clause,
    ClauseKind,
    ClauseStatus,
    DocumentSection,
    Evidence,
    NormalizedPolicy,
    RoomCategory,
    RoomLimitBasis,
)


def a_policy() -> NormalizedPolicy:
    return NormalizedPolicy(sum_insured=Decimal("300000"))


# --- values in the forms a document uses ------------------------------------


@pytest.mark.parametrize("typed, expected", [
    ("500000", 500000),
    ("5 lakh", 500000),
    ("5,00,000", 500000),
    ("Rs. 5 lakhs", 500000),
    (500000, 500000),
])
def test_a_cover_correction_accepts_what_the_document_says(typed, expected):
    policy = edit_field(a_policy(), "sum_insured", typed)
    assert policy.sum_insured == Decimal(expected)


def test_a_room_limit_can_be_a_rupee_cap():
    policy = edit_field(a_policy(), "room_limit", "5000")
    assert policy.room_limit.basis is RoomLimitBasis.FLAT_PER_DAY
    assert policy.room_limit.amount_per_day == Decimal(5000)


def test_a_room_limit_can_be_a_percentage():
    """A room limit is not one number. An edit box that only took rupees would
    force the other shapes into one the policy never had."""
    policy = edit_field(a_policy(), "room_limit", "1%")
    assert policy.room_limit.basis is RoomLimitBasis.PCT_OF_SI_PER_DAY
    assert policy.room_limit.pct_of_si == Decimal(1)


def test_a_room_limit_can_be_a_category():
    policy = edit_field(a_policy(), "room_limit", "single private room")
    assert policy.room_limit.basis is RoomLimitBasis.CATEGORY_ONLY
    assert policy.room_limit.category_ceiling is RoomCategory.SINGLE_PRIVATE


@pytest.mark.parametrize("typed", ["none", "no limit", "unlimited", ""])
def test_a_room_limit_can_be_removed(typed):
    policy = edit_field(a_policy(), "room_limit", typed)
    assert policy.room_limit.basis is RoomLimitBasis.NO_LIMIT


def test_a_copay_correction_reads_a_percentage():
    policy = edit_field(a_policy(), "copay_pct", "10%")
    assert policy.copay_pct == Decimal(10)


def test_a_deductible_can_be_set_back_to_nothing():
    policy = a_policy()
    policy.deductible = Decimal(50000)
    assert edit_field(policy, "deductible", "0").deductible == Decimal(0)


# --- the guardrails ---------------------------------------------------------


def test_an_unknown_field_is_refused():
    """A closed set. An open one would let a mistyped name create a second,
    wrong field beside the real one, which is the failure the whole
    clarification design is built to avoid."""
    with pytest.raises(NotEditable):
        edit_field(a_policy(), "sum_insured_2", "500000")


def test_unreadable_text_is_refused_in_words_the_user_can_act_on():
    with pytest.raises(Unreadable) as caught:
        edit_field(a_policy(), "sum_insured", "whatever my brother has")
    assert "5 lakh" in str(caught.value)


def test_a_refused_edit_leaves_the_old_value_alone():
    policy = a_policy()
    with pytest.raises(Unreadable):
        edit_field(policy, "sum_insured", "no idea really")
    assert policy.sum_insured == Decimal("300000")


# --- a correction outranks what was extracted -------------------------------


def clause_of(kind: ClauseKind) -> Clause:
    return Clause(
        kind=kind,
        verbatim="Sum Insured: Rs. 3,00,000",
        evidence=Evidence(page_index=0, section=DocumentSection.SCHEDULE),
        params={"amount_inr": "300000"},
        confidence=0.4,
        status=ClauseStatus.NEEDS_USER,
    )


def test_a_correction_settles_the_clause_it_replaces():
    policy = a_policy()
    policy.clauses = [clause_of(ClauseKind.SUM_INSURED)]

    policy = edit_field(policy, "sum_insured", "5 lakh")

    assert policy.clauses[0].status is ClauseStatus.CONFIRMED
    assert "Corrected by you." in policy.clauses[0].notes


def test_a_correction_stops_the_system_asking_about_it():
    """Without this the user answers a question they have already answered, by
    correcting the value the question was about."""
    policy = a_policy()
    policy.open_clarifications = [
        ClarificationRequest(
            clause_kind=ClauseKind.SUM_INSURED,
            question="What is your total cover?",
        ),
        ClarificationRequest(
            clause_kind=ClauseKind.COPAY,
            question="What is your co-payment?",
        ),
    ]

    policy = edit_field(policy, "sum_insured", "5 lakh")

    kinds = {r.clause_kind for r in policy.open_clarifications}
    assert ClauseKind.SUM_INSURED not in kinds
    assert ClauseKind.COPAY in kinds


# --- over the API -----------------------------------------------------------


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def session_id(client) -> str:
    return client.post("/api/policy/manual", json={
        "sum_insured": 300000, "room_limit_type": "flat",
        "room_limit_amount": 3000, "copay_pct": 0,
    }).json()["session_id"]


def test_correcting_over_the_api_returns_the_updated_policy(client, session_id):
    response = client.patch(
        f"/api/policy/{session_id}/field",
        json={"field": "sum_insured", "value": "5 lakh"},
    )
    assert response.status_code == 200
    assert response.json()["sum_insured"] == 500000


def test_the_correction_survives_into_the_estimate(client, session_id):
    """The point of correcting is that everything after it changes too."""
    client.patch(
        f"/api/policy/{session_id}/field",
        json={"field": "room_limit", "value": "1%"},
    )
    policy = client.get(f"/api/policy/{session_id}").json()
    # One percent of five lakh a day, not the three thousand entered by hand.
    assert policy["room_limit"]["daily_cap"] == 3000.0


def test_an_unknown_field_is_refused_over_the_api(client, session_id):
    response = client.patch(
        f"/api/policy/{session_id}/field",
        json={"field": "nonsense", "value": "1"},
    )
    assert response.status_code == 400


def test_unreadable_input_returns_a_message_worth_showing(client, session_id):
    response = client.patch(
        f"/api/policy/{session_id}/field",
        json={"field": "sum_insured", "value": "ask my brother"},
    )
    assert response.status_code == 400
    assert "lakh" in response.json()["detail"]


def test_the_interface_is_told_which_fields_it_may_write_to(client, session_id):
    policy = client.get(f"/api/policy/{session_id}").json()
    assert "sum_insured" in policy["editable_fields"]
    assert "room_limit" in policy["editable_fields"]
