"""Asking a person for the two things we could not read, without trapping them.

The old loop offered fixed choices and a box that took digits. Both assume the
user's situation is one the form anticipated. Often it is not: the figure on
their document is written in words, or their answer is none of the options.

Three properties matter, and each of them exists because of a way this can go
wrong. Free text has to be understood without letting the answer steer the
engine, or a typed near-miss creates a second, wrong field beside the real one.
Anything interpreted has to be confirmed before it is used, or a paraphrase
becomes a settled number nobody looked at. And every question has to have an
exit, or the loop keeps asking and the user abandons it with less recorded than
if we had stopped and asked for the two that mattered.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.pipeline.s4_compile.compiler import apply_answer, skip_question
from app.pipeline.s4_compile.interpret import (
    interpret,
    parse_amount,
    parse_percent,
    says_nothing_applies,
)
from app.schemas.policy import (
    ClarificationRequest,
    ClauseKind,
    NormalizedPolicy,
    RoomLimitBasis,
)

# --- reading amounts the way people write them ------------------------------


@pytest.mark.parametrize("text, expected", [
    ("5 lakh", 500000),
    ("5L", 500000),
    ("5,00,000", 500000),
    ("Rs. 5 lakhs", 500000),
    ("₹500000", 500000),
    ("50k", 50000),
    ("2.5 lakh", 250000),
    ("five lakh", 500000),
    ("1 crore", 10000000),
    ("about 5 lakh", 500000),
    ("5000 per day", 5000),
    ("Rs 8,000/-", 8000),
    ("fifty thousand", 50000),
])
def test_amounts_are_read_in_the_forms_people_use(text, expected):
    assert parse_amount(text) == Decimal(expected)


@pytest.mark.parametrize("text", ["", "sometime next week", "the blue one", "abcd"])
def test_unreadable_text_returns_nothing_rather_than_a_guess(text):
    """A wrong figure here becomes a wrong figure in every estimate after it."""
    assert parse_amount(text) is None


@pytest.mark.parametrize("text, expected", [
    ("1%", 1), ("one percent", 1), ("20 per cent", 20),
    ("10 percent of my cover", 10),
])
def test_percentages_are_read(text, expected):
    assert parse_percent(text) == Decimal(expected)


@pytest.mark.parametrize("text", [
    "no limit", "none", "I don't know", "I dont know", "not sure", "nil",
    "nothing", "no", "N/A", "we have no idea", "no idea", "unlimited",
    "not applicable", "No Limit.", "there is no limit", "it's not mentioned",
    "I have no clue", "cant say",
])
def test_a_non_answer_is_recognised_as_an_answer(text):
    assert says_nothing_applies(text)


@pytest.mark.parametrize("text", [
    "5 lakh", "500000", "1%", "single private room",
    "i know it is 5 lakh", "5000", "no more than 5000",
])
def test_a_real_answer_is_not_mistaken_for_a_non_answer(text):
    """A loose pattern that also swallowed "i know it is 5 lakh" would record
    "no answer" over a perfectly good one."""
    assert not says_nothing_applies(text)


# --- interpretation ---------------------------------------------------------


def test_a_clean_amount_needs_no_confirmation():
    """The rules cost nothing and cannot hallucinate, so what they settle is
    applied directly. Only what they could not read goes near a model."""
    result = interpret("What is your total cover?", "5 lakh")
    assert result.best is not None
    assert result.best.value == Decimal(500000)
    assert not result.needs_confirmation
    assert result.best.source == "rules"


def test_no_limit_is_recorded_as_a_fact_not_a_blank():
    result = interpret("Does your policy cap your room rent?", "no limit")
    assert result.best is not None
    assert result.best.is_none


def test_nothing_typed_is_not_an_answer():
    assert interpret("What is your cover?", "   ").best is None


# --- folding answers into the policy ----------------------------------------


def policy_with_question(kind=ClauseKind.SUM_INSURED, expects="amount"):
    policy = NormalizedPolicy()
    policy.open_clarifications = [ClarificationRequest(
        clause_kind=kind,
        question="What is the total cover amount on your policy?",
        expects=expects,
    )]
    return policy


def test_a_typed_amount_in_words_settles_the_field():
    policy = policy_with_question()
    request_id = policy.open_clarifications[0].request_id

    policy = apply_answer(policy, request_id, "5 lakh")

    assert policy.sum_insured == Decimal(500000)
    assert not policy.open_clarifications


def test_plain_digits_still_work():
    policy = policy_with_question()
    request_id = policy.open_clarifications[0].request_id
    policy = apply_answer(policy, request_id, "500000")
    assert policy.sum_insured == Decimal(500000)


def test_no_limit_on_the_room_is_applied_as_no_limit():
    policy = policy_with_question(ClauseKind.ROOM_RENT_CAP)
    request_id = policy.open_clarifications[0].request_id
    policy = apply_answer(policy, request_id, "there is no limit")
    assert policy.room_limit.basis is RoomLimitBasis.NO_LIMIT


def test_text_we_cannot_read_reopens_the_question_rather_than_guessing():
    policy = policy_with_question()
    request_id = policy.open_clarifications[0].request_id

    policy = apply_answer(policy, request_id, "somewhere around what my brother has")

    # Still open, still asking, and nothing invented in the meantime.
    assert len(policy.open_clarifications) == 1
    assert policy.sum_insured == Decimal(0)


def test_a_rejected_reading_returns_the_original_question():
    policy = policy_with_question()
    request = policy.open_clarifications[0]
    request.pending_value = "500000"
    request.question = "Did you mean ₹5,00,000?"
    request.options = [{"label": "Yes", "value": "__confirm__500000"}]

    policy = apply_answer(policy, request.request_id, "__retry__")

    reopened = policy.open_clarifications[0]
    assert reopened.pending_value is None
    assert reopened.question == "What is the total cover amount on your policy?"
    assert reopened.options == []


def test_a_confirmed_reading_is_applied():
    policy = policy_with_question()
    request_id = policy.open_clarifications[0].request_id

    policy = apply_answer(policy, request_id, "__confirm__500000")

    assert policy.sum_insured == Decimal(500000)
    assert not policy.open_clarifications


# --- skipping ---------------------------------------------------------------


def test_skipping_stops_the_asking_without_settling_anything():
    policy = policy_with_question()
    request_id = policy.open_clarifications[0].request_id

    policy = skip_question(policy, request_id)

    assert not policy.open_clarifications
    # Nothing was invented to fill the gap.
    assert policy.sum_insured == Decimal(0)


def test_skipping_an_unknown_question_is_harmless():
    policy = policy_with_question()
    before = len(policy.open_clarifications)
    assert len(skip_question(policy, "nosuchquestion").open_clarifications) == before


# --- over the API -----------------------------------------------------------


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_the_question_tells_the_interface_how_to_render_itself(client):
    """Without these the interface cannot offer an escape or a way out."""
    policy = client.post("/api/policy/manual", json={
        "sum_insured": 500000, "room_limit_type": "none",
    }).json()

    for question in policy["questions"]:
        assert question["expects"] in ("amount", "percent", "choice")
        assert "allow_other" in question
        assert "skippable" in question


def test_skipping_over_the_api_returns_the_policy(client):
    session_id = client.post("/api/policy/manual", json={
        "sum_insured": 500000, "room_limit_type": "none",
    }).json()["session_id"]

    response = client.post(
        f"/api/policy/{session_id}/skip", json={"question_id": "whatever"}
    )
    assert response.status_code == 200
    assert "questions" in response.json()


def test_the_loop_is_bounded(client):
    """Each round is a model call and a wait. A loop that keeps producing
    another question is one people abandon, leaving less recorded than if we
    had stopped and asked for the two that mattered."""
    from app.api.routes import MAX_CLARIFICATION_ROUNDS

    session_id = client.post("/api/policy/manual", json={
        "sum_insured": 500000, "room_limit_type": "none",
    }).json()["session_id"]

    for _ in range(MAX_CLARIFICATION_ROUNDS + 2):
        client.post(
            f"/api/policy/{session_id}/answer",
            json={"question_id": "x", "answer": "5 lakh"},
        )

    final = client.get(f"/api/policy/{session_id}").json()
    assert final["questions"] == []
