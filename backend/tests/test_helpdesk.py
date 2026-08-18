"""The help desk: what it answers, and what it refuses.

The refusals matter more than the answers. This sits in the corner of an app
somebody is using during a hospital admission, and the three things it must
never do are give clinical advice, tell somebody what their insurer will
decide, and change anything. The first two are the problem statement's own
boundaries. The third is structural: there is no write path from here, so the
worst a wrong answer can do is mislead somebody looking straight at the screen
that contradicts it.

The model path is not exercised here on purpose. These test the ground it
stands on, which is the part that has to be right whether or not a model is
reachable, and which is what CI runs with no key set.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.help import assistant, knowledge
from app.main import app
from app.schemas.help import HelpSource


def ask(question: str, screen: str = ""):
    return assistant.answer(question, screen=screen, use_model=False)


# --- the questions somebody actually asks -----------------------------------


@pytest.mark.parametrize("question, key", [
    ("whose name should I enter?", "whose_name"),
    ("should I put my name or the patient's name", "whose_name"),
    ("which document do I upload", "which_document"),
    ("I don't have my policy document", "no_document"),
    ("what counts as a pre-existing condition", "pre_existing"),
    ("why does the room change the whole bill", "room_limit"),
    ("what is cashless", "cashless"),
    ("I have two policies", "second_policy"),
    ("the sum insured was read wrong", "wrong_figure"),
    ("I already claimed this year", "cover_left"),
    ("how do I check the final bill", "bill_check"),
    ("what are non-payable items", "non_payable"),
    ("what papers do I need for the claim", "claim_papers"),
    ("where is my data stored", "privacy"),
])
def test_it_answers_what_it_was_asked(question, key):
    assert knowledge.best_match(question).key == key
    assert ask(question).source is HelpSource.KNOWLEDGE


def test_the_name_question_is_answered_rather_than_refused():
    """The single question this help desk most exists to answer. An earlier
    clinical filter caught it on the words "should I" alone."""
    reply = ask("whose name should I enter?")
    assert "Yours" in reply.text
    assert "medical question" not in reply.text


# --- the three refusals -----------------------------------------------------


@pytest.mark.parametrize("question", [
    "should I have this surgery?",
    "do I need this treatment",
    "which treatment is best for me",
    "is it safe",
    "what is wrong with me",
    "what medicine should I take for the pain",
])
def test_clinical_questions_are_sent_to_a_doctor(question):
    assert "medical question" in ask(question).text


@pytest.mark.parametrize("question", [
    "do I need a doctor's letter for the claim?",
    "should I take the general ward or twin sharing",
])
def test_paperwork_is_not_mistaken_for_medicine(question):
    """"Doctor" and "should I" are not clinical on their own, and refusing
    these would refuse the ordinary questions of an admission."""
    assert "medical question" not in ask(question).text


@pytest.mark.parametrize("question", [
    "can you change my sum insured for me please",
    "please update the room limit for me",
    "fill in the treatment for me",
])
def test_it_says_plainly_that_it_cannot_change_anything(question):
    reply = ask(question)
    assert "cannot change anything" in reply.text
    assert "point you at where" in reply.text


@pytest.mark.parametrize("question", [
    "will my insurer pay for this?",
    "am I covered for this surgery",
    "will they approve the claim",
])
def test_it_never_says_what_an_insurer_will_decide(question):
    assert "Only your insurer can decide" in ask(question).text


def test_what_it_does_not_know_it_says_it_does_not_know():
    reply = ask("what is the capital of France")
    assert reply.source is HelpSource.UNKNOWN
    assert reply.offer_ticket


# --- what it offers before anybody types ------------------------------------


def test_the_suggestions_are_about_the_screen_you_are_on():
    on_upload = {s.key for s in assistant.opening("upload").suggestions}
    on_journey = {s.key for s in assistant.opening("journey").suggestions}
    assert "whose_name" in on_upload
    assert "bill_check" in on_journey
    assert on_upload != on_journey


def test_an_empty_question_opens_rather_than_failing():
    assert ask("").suggestions


def test_every_suggested_key_is_a_real_answer():
    for screen in (*knowledge.SUGGESTED, "nonsense"):
        for suggestion in assistant.opening(screen).suggestions:
            assert suggestion.key in knowledge.BY_KEY


def test_nothing_in_the_knowledge_base_reads_as_clinical_advice():
    """The knowledge base is the ground a model is given. If it strayed, so
    would anything grounded in it."""
    from app.core import guardrails

    for answer in knowledge.ANSWERS:
        assert not guardrails.contains_clinical_advice(answer.body), answer.key


# --- the line between a diagnosis and an ordinary sentence -------------------


@pytest.mark.parametrize("text", [
    "You have a co-payment of 10% on every claim.",
    "You have a room limit of Rs 5,000 a day.",
    "If you have both, add both.",
    "If you have a condition that predates the policy, a waiting period applies.",
])
def test_ordinary_sentences_are_not_read_as_diagnosis(text):
    """Caught text is dropped rather than trimmed, so a rule this broad was
    deleting correct answers. "You have" is not a diagnosis on its own, and
    supposing a condition is not the same as telling somebody they have one."""
    from app.core import guardrails

    assert not guardrails.contains_clinical_advice(text)
    assert guardrails.sanitise(text, fallback="dropped") != "dropped"


@pytest.mark.parametrize("text", [
    "You have diabetes and it is excluded.",
    "You are diagnosed with a heart condition.",
    "You are suffering from an infection.",
])
def test_asserting_a_condition_is_still_refused(text):
    from app.core import guardrails

    assert guardrails.contains_clinical_advice(text)
    assert guardrails.sanitise(text, fallback="dropped") == "dropped"


# --- over the API -----------------------------------------------------------


@pytest.fixture
def api():
    with TestClient(app) as client:
        yield client


def test_asking_over_the_api_returns_an_answer(api):
    reply = api.post("/api/help/ask", json={
        "message": "whose name should I enter", "screen": "upload",
    }).json()
    assert reply["text"]
    assert reply["suggestions"]


def test_the_help_desk_is_not_given_a_session(api):
    """It explains how things work and where they are done. Not being handed
    somebody's policy is a stronger guarantee than being trusted not to read
    it."""
    import inspect

    from app.api import routes

    assert "session_id" not in inspect.signature(routes.help_ask).parameters
    assert "session_id" not in routes.HelpAsk.model_fields


def test_a_ticket_comes_back_with_a_reference_and_an_honest_status(api):
    ticket = api.post("/api/help/ticket", json={
        "kind": "feedback", "subject": "The bill check found a duplicate line",
        "screen": "journey",
    }).json()
    assert ticket["ticket_id"].startswith("PM-")
    assert ticket["stage"] == "received"
    assert "no support desk" in ticket["note"]


def test_a_ticket_needs_a_subject(api):
    assert api.post("/api/help/ticket", json={
        "kind": "feedback", "subject": "",
    }).status_code == 422


def test_a_very_long_question_is_refused_rather_than_forwarded(api):
    """A pasted policy is not a question, and it is not going to a model."""
    assert api.post("/api/help/ask", json={
        "message": "x" * 5000, "screen": "upload",
    }).status_code == 422
