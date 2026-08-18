"""Whether the policy pays at all, which every other number here assumes.

A room limit, a proportionate deduction, a co-payment and a sub-limit are all
ways of paying less. A waiting period is the way of paying nothing, and it was
the one thing the system read off the document, printed on screen, and then
ignored: someone six weeks into a new policy could be shown a hospital, a room
and a rupee figure for an operation their insurer would decline outright.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal as D

import pytest

from app.pipeline.s4_compile.compiler import classify_waiting
from app.pipeline.s6_simulate import eligibility as E
from app.schemas.policy import (
    InsuredPerson,
    NormalizedPolicy,
    RoomCategory,
    RoomLimit,
    RoomLimitBasis,
    WaitingKind,
    WaitingPeriod,
    add_months,
)
from app.schemas.procedure import CostSplit, ExpenseHead, Procedure, Specialty

START = date(2026, 2, 1)


def make_policy(*, waits=(), start: date | None = START, scheme=None, **kw):
    defaults = dict(
        sum_insured=D(500000),
        room_limit=RoomLimit(basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=D(5000)),
    )
    policy = NormalizedPolicy(**{**defaults, **kw})
    policy.waiting_periods = list(waits)
    policy.meta.start_date = start
    policy.government_scheme = scheme
    return policy


def make_bill(surgeon: D):
    """A one-line bill, so a co-payment is the only thing that can move it."""
    from app.schemas.simulation import BillLine, EstimatedBill

    return EstimatedBill(
        hospital_id="H1", procedure_code="CP-TEST-001",
        room_category=RoomCategory.TWIN_SHARING,
        los_days=2, room_rate_per_day=D(0),
        lines=[BillLine(head=ExpenseHead.SURGEON_FEE, label="Surgeon", amount=surgeon)],
    )


def make_procedure(name: str, specialty=Specialty.GENERAL_SURGERY, synonyms=()):
    return Procedure(
        code="CP-TEST-001",
        name=name,
        specialty=specialty,
        base_rate_non_nabh=D(50000),
        base_rate_nabh=D(60000),
        cost_split=CostSplit(fractions={ExpenseHead.SURGEON_FEE: 1.0}),
        synonyms=list(synonyms),
    )


INITIAL = WaitingPeriod(
    days=30, kind=WaitingKind.INITIAL,
    applies_to="all illnesses other than accidental injury",
)
PED = WaitingPeriod(
    months=24, kind=WaitingKind.PRE_EXISTING, applies_to="pre-existing diseases",
)
NAMED = WaitingPeriod(
    months=24, kind=WaitingKind.SPECIFIC_AILMENT,
    applies_to="cataract, hernia, and joint replacement",
)
MATERNITY = WaitingPeriod(
    months=36, kind=WaitingKind.MATERNITY, applies_to="maternity expenses",
)

CATARACT = make_procedure(
    "Cataract surgery with monofocal lens", Specialty.OPHTHALMOLOGY, ["cataract"]
)
KNEE = make_procedure(
    "Total knee replacement", Specialty.ORTHOPAEDICS, ["knee replacement"]
)
HEART = make_procedure("Coronary angiography", Specialty.CARDIOLOGY, ["angiography"])
DELIVERY = make_procedure(
    "Normal delivery", Specialty.OBSTETRICS_GYNAECOLOGY, ["delivery"]
)


# --- the initial period ----------------------------------------------------


def test_the_first_thirty_days_cover_nothing_but_accidents():
    policy = make_policy(waits=[INITIAL])
    verdict = E.assess(policy, HEART, on=START + timedelta(days=10))
    assert verdict.blocks
    assert verdict.of(WaitingKind.INITIAL).days_left == 20


def test_an_accident_inside_the_first_thirty_days_is_covered():
    policy = make_policy(waits=[INITIAL])
    verdict = E.assess(policy, HEART, on=START + timedelta(days=10), accident=True)
    assert not verdict.blocks
    assert verdict.verdict is E.Verdict.COVERED


def test_the_initial_period_stops_mattering_once_it_has_run():
    policy = make_policy(waits=[INITIAL])
    assert E.assess(policy, HEART, on=START + timedelta(days=31)).verdict is (
        E.Verdict.COVERED
    )


def test_the_day_it_clears_is_covered_not_the_day_after():
    """Thirty days from 1 February is 3 March, and the claim stands that day."""
    policy = make_policy(waits=[INITIAL])
    assert INITIAL.clears_on(START) == date(2026, 3, 3)
    assert E.assess(policy, HEART, on=date(2026, 3, 2)).blocks
    assert not E.assess(policy, HEART, on=date(2026, 3, 3)).blocks


# --- pre-existing ----------------------------------------------------------


def test_a_pre_existing_condition_is_a_question_not_a_guess():
    policy = make_policy(waits=[PED])
    verdict = E.assess(policy, HEART, on=START + timedelta(days=180))
    assert verdict.verdict is E.Verdict.ASK
    assert not verdict.blocks
    assert verdict.of(WaitingKind.PRE_EXISTING).question


def test_answering_yes_blocks_the_claim():
    policy = make_policy(waits=[PED])
    verdict = E.assess(
        policy, HEART, on=START + timedelta(days=180), pre_existing=True
    )
    assert verdict.blocks


def test_answering_no_clears_it():
    policy = make_policy(waits=[PED])
    verdict = E.assess(
        policy, HEART, on=START + timedelta(days=180), pre_existing=False
    )
    assert verdict.verdict is E.Verdict.COVERED


def test_a_long_held_policy_is_not_asked_about_pre_existing_conditions():
    """Three years in, the answer cannot change anything, so nobody is asked."""
    policy = make_policy(waits=[PED])
    verdict = E.assess(policy, HEART, on=START + timedelta(days=1100))
    assert verdict.verdict is E.Verdict.COVERED
    assert verdict.findings == []


# --- named treatments ------------------------------------------------------


def test_a_named_treatment_waits_and_others_do_not():
    policy = make_policy(waits=[NAMED])
    on = START + timedelta(days=180)
    assert E.assess(policy, CATARACT, on=on).blocks
    assert not E.assess(policy, HEART, on=on).blocks


def test_a_multi_word_name_matches_the_clinical_one():
    """The clause says "joint replacement"; the catalogue says "Total knee
    replacement"."""
    assert E.names_this_treatment("cataract, hernia, and joint replacement", KNEE)


def test_a_layman_word_matches_the_clinical_name():
    piles = make_procedure("Haemorrhoidectomy", synonyms=["piles", "haemorrhoids"])
    assert E.names_this_treatment("piles, fistula and fissure", piles)


def test_a_general_word_does_not_match_everything():
    """"Specified surgery" naming nothing must not catch every operation."""
    assert not E.names_this_treatment("specified surgery", HEART)
    assert not E.names_this_treatment("any listed treatment", CATARACT)


def test_maternity_applies_to_obstetrics_and_nothing_else():
    policy = make_policy(waits=[MATERNITY])
    on = START + timedelta(days=180)
    assert E.assess(policy, DELIVERY, on=on).blocks
    assert not E.assess(policy, HEART, on=on).blocks


# --- what we do not know ---------------------------------------------------


def test_an_unread_start_date_is_a_question_not_a_pass():
    """Silence here would tell someone their claim is fine when we cannot know."""
    policy = make_policy(waits=[INITIAL, PED], start=None)
    verdict = E.assess(policy, HEART, on=date(2026, 6, 1))
    assert verdict.verdict is E.Verdict.UNKNOWN
    assert not verdict.blocks
    assert verdict.findings[0].question == "When did this policy start?"


def test_a_policy_with_no_waiting_periods_needs_no_start_date():
    policy = make_policy(waits=[], start=None)
    assert E.assess(policy, HEART, on=date(2026, 6, 1)).verdict is E.Verdict.COVERED


def test_a_government_scheme_serves_no_waiting_period():
    policy = make_policy(waits=[INITIAL, PED], scheme="pmjay")
    verdict = E.assess(policy, HEART, on=START + timedelta(days=3))
    assert verdict.verdict is E.Verdict.COVERED
    assert "day the card is issued" in verdict.findings[0].detail


# --- worst finding wins ----------------------------------------------------


def test_the_worst_finding_decides_the_verdict():
    policy = make_policy(waits=[INITIAL, PED, NAMED])
    verdict = E.assess(policy, CATARACT, on=START + timedelta(days=10))
    assert verdict.verdict is E.Verdict.NOT_YET
    assert [f.verdict for f in verdict.findings][0] is E.Verdict.NOT_YET
    # Every relevant period is still reported, so the user sees the whole shape.
    assert len(verdict.findings) == 3


# --- durations -------------------------------------------------------------


@pytest.mark.parametrize(
    ("months", "days", "expected"),
    [
        (0, 30, "30 days"),
        (1, 0, "1 month"),
        (24, 0, "2 years"),
        (36, 0, "3 years"),
        (18, 0, "18 months"),
        (2, 15, "2 months and 15 days"),
    ],
)
def test_a_duration_reads_the_way_the_document_wrote_it(months, days, expected):
    period = WaitingPeriod(months=months, days=days, applies_to="x")
    assert period.describe() == expected


def test_month_arithmetic_clamps_to_a_short_month():
    """Two years from 29 February is 28 February, not the 1st of March."""
    assert add_months(date(2024, 2, 29), 24) == date(2026, 2, 28)
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)


def test_a_waiting_period_needs_a_duration():
    with pytest.raises(ValueError, match="duration"):
        WaitingPeriod(applies_to="pre-existing diseases")


# --- classification --------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("pre-existing diseases", WaitingKind.PRE_EXISTING),
        ("Pre Existing Disease (PED)", WaitingKind.PRE_EXISTING),
        ("all illnesses other than accidental injury", WaitingKind.INITIAL),
        ("any disease contracted", WaitingKind.INITIAL),
        ("maternity expenses", WaitingKind.MATERNITY),
        ("pregnancy and childbirth", WaitingKind.MATERNITY),
        ("cataract, hernia, and joint replacement", WaitingKind.SPECIFIC_AILMENT),
        ("specified diseases", WaitingKind.SPECIFIC_AILMENT),
    ],
)
def test_a_waiting_period_is_classified_by_what_it_names(text, expected):
    assert classify_waiting(text, days=0, months=24) is expected


def test_a_short_unnamed_period_is_the_initial_one():
    """No other kind is ever written in days."""
    assert classify_waiting("unspecified", days=30, months=0) is WaitingKind.INITIAL


def test_pre_existing_beats_a_list_that_mentions_it():
    text = "pre-existing diseases including cataract and hernia"
    assert classify_waiting(text, days=0, months=48) is WaitingKind.PRE_EXISTING


# --- ages ------------------------------------------------------------------


def test_the_eldest_member_carries_the_policy():
    policy = make_policy()
    policy.insured = [
        InsuredPerson(name="Rajesh Verma", age=41, relationship="Self"),
        InsuredPerson(name="Sunita Verma", age=38, relationship="Spouse"),
        InsuredPerson(name="Aarav Verma", age=9, relationship="Son"),
    ]
    assert policy.oldest_age == 41


def test_a_policy_naming_nobody_has_no_age():
    assert make_policy().oldest_age is None


# --- reading the people off a schedule -------------------------------------


def _page(text: str):
    from app.schemas.document import Page

    return Page(page_index=0, width=595, height=842, text=text)


INSURED_TABLE = """
INSURED PERSONS
Sl.
Name of Insured Person
Age
Relationship
Sum Insured
1
Girish Desai
49
Self
Rs. 5,00,000/
2
Manoj Desai
46
Wife
Floater
3
Ramesh Desai
9
Son
Floater
SCHEDULE OF BENEFITS
"""


def test_a_family_schedule_yields_every_member():
    from app.pipeline.s2_atomize.grammar import extract_insured_persons

    people = [c.params for c in extract_insured_persons(_page(INSURED_TABLE))]
    assert [(p["name"], p["age"], p["relationship"]) for p in people] == [
        ("Girish Desai", 49, "Self"),
        ("Manoj Desai", 46, "Wife"),
        ("Ramesh Desai", 9, "Son"),
    ]


def test_the_word_in_the_cover_column_is_not_a_person():
    """"Floater" is what a family policy writes for everyone after the proposer.
    Read as a name it became a member who took the next row's serial as an age."""
    from app.pipeline.s2_atomize.grammar import extract_insured_persons

    names = [c.params["name"] for c in extract_insured_persons(_page(INSURED_TABLE))]
    assert "Floater" not in names
    assert all(" " in name for name in names)


def test_an_amount_in_capitals_does_not_end_the_table():
    """"INR 25,00,000" is uppercase. Treated as the next section heading it
    ended the table one row in and quietly dropped the spouse."""
    from app.pipeline.s2_atomize.grammar import extract_insured_persons

    text = INSURED_TABLE.replace("Rs. 5,00,000/", "INR 25,00,000")
    assert len(extract_insured_persons(_page(text))) == 3


def test_the_cover_belongs_to_the_row_it_is_written_on():
    """A floater states it against the proposer and leaves the rest blank.
    Closing a person at their relationship handed it to the next row."""
    from app.pipeline.s2_atomize.grammar import extract_insured_persons

    people = [c.params for c in extract_insured_persons(_page(INSURED_TABLE))]
    assert people[0].get("sum_insured")
    assert not people[1].get("sum_insured")


def test_the_next_rows_serial_is_not_an_age():
    """The first bare number after a name is the age; the next one begins the
    following row."""
    from app.pipeline.s2_atomize.grammar import extract_insured_persons

    ages = [c.params["age"] for c in extract_insured_persons(_page(INSURED_TABLE))]
    assert ages == [49, 46, 9]


def test_the_column_headings_are_not_people():
    from app.pipeline.s2_atomize.grammar import extract_insured_persons

    names = [c.params["name"] for c in extract_insured_persons(_page(INSURED_TABLE))]
    assert "Sum Insured" not in names
    assert "Name of Insured Person" not in names


def test_two_people_sharing_a_name_stay_two_people():
    """A father and a son can share one. Merging them would drop whichever age
    the terms are actually conditioned on."""
    from app.pipeline.s2_atomize.grammar import extract_insured_persons
    from app.pipeline.s4_compile.compiler import _compile_insured

    text = INSURED_TABLE.replace("Ramesh Desai\n9\nSon", "Girish Desai\n9\nSon")
    people = _compile_insured(extract_insured_persons(_page(text)))
    assert len(people) == 3
    assert sorted(p.age for p in people) == [9, 46, 49]


# --- reading the period off a schedule --------------------------------------


def test_a_policy_period_yields_both_ends():
    from app.pipeline.s2_atomize.grammar import extract_policy_period

    text = (
        "Policy Period\n"
        "From 00:00 hrs on 01/02/2026 to 23:59 hrs on 31/01/2027\n"
    )
    fields = {c.params["field"]: c.params["value"] for c in
              extract_policy_period(_page(text))}
    assert fields == {"start_date": "2026-02-01", "end_date": "2027-01-31"}


def test_a_date_is_read_day_first():
    """01/02/2026 on an Indian schedule is February, and reading it the other
    way would move every waiting period by eleven months."""
    from app.pipeline.s2_atomize.patterns import parse_date

    assert parse_date("Date of Issue 01/02/2026") == date(2026, 2, 1)


def test_an_impossible_date_is_not_salvaged():
    from app.pipeline.s2_atomize.patterns import parse_date

    assert parse_date("31/02/2026") is None


def test_a_period_running_backwards_is_a_misread():
    from app.pipeline.s2_atomize.grammar import extract_policy_period
    from app.pipeline.s4_compile.compiler import _compile_meta

    text = "Policy Period\nFrom 01/02/2027 to 31/01/2026\n"
    meta = _compile_meta(extract_policy_period(_page(text)))
    assert meta.start_date == date(2027, 2, 1)
    assert meta.end_date is None


def test_a_date_lands_in_the_field_as_a_date():
    """Assignment on a Pydantic model does not coerce, so an ISO string put here
    unchecked would sit in a date field and fail on the first arithmetic."""
    from app.pipeline.s2_atomize.grammar import extract_policy_period
    from app.pipeline.s4_compile.compiler import _compile_meta

    meta = _compile_meta(
        extract_policy_period(_page("Policy Period\n01/02/2026 to 31/01/2027\n"))
    )
    assert isinstance(meta.start_date, date)


# --- waiting periods written in days ---------------------------------------


def test_the_initial_period_is_written_in_days_and_must_be_read():
    """It is always "30 days" and never "1 month", so reading only months lost
    the one period that applies to every illness there is."""
    from app.pipeline.s2_atomize.grammar import extract_waiting_periods

    text = (
        "3. WAITING PERIODS\n"
        "Waiting Period\nApplicable To\n"
        "30 days\nall illnesses other than accidental injury\n"
        "24 months\npre-existing diseases\n"
    )
    found = [(c.params["months"], c.params["days"], c.params["applies_to"])
             for c in extract_waiting_periods(_page(text))]
    assert (0, 30, "all illnesses other than accidental injury") in found
    assert (24, 0, "pre-existing diseases") in found


def test_a_vague_duplicate_of_a_named_period_is_dropped():
    """Both extractors read one row: one reports what it applies to and one
    does not. Keeping both lists every restriction twice and leaves half of
    them uncategorised."""
    from app.pipeline.s2_atomize.grammar import _clause
    from app.pipeline.s4_compile.compiler import _compile_waiting_periods
    from app.schemas.policy import ClauseKind

    page = _page("24 months pre-existing diseases")
    clauses = [
        _clause(ClauseKind.WAITING_PERIOD, "24 months", page,
                params={"months": 24, "days": 0, "applies_to": "unspecified"},
                confidence=0.7),
        _clause(ClauseKind.WAITING_PERIOD, "24 months pre-existing diseases", page,
                params={"months": 24, "days": 0,
                        "applies_to": "pre-existing diseases"},
                confidence=0.8),
    ]
    compiled = _compile_waiting_periods(clauses)
    assert len(compiled) == 1
    assert compiled[0].kind is WaitingKind.PRE_EXISTING


def test_a_vague_period_survives_when_nothing_else_says_that_duration():
    """It is still a real restriction, and dropping it would understate the
    policy."""
    from app.pipeline.s2_atomize.grammar import _clause
    from app.pipeline.s4_compile.compiler import _compile_waiting_periods
    from app.schemas.policy import ClauseKind

    page = _page("36 months")
    compiled = _compile_waiting_periods([
        _clause(ClauseKind.WAITING_PERIOD, "36 months", page,
                params={"months": 36, "days": 0, "applies_to": "unspecified"},
                confidence=0.7),
    ])
    assert len(compiled) == 1
    assert compiled[0].months == 36


# --- through the API -------------------------------------------------------


@pytest.fixture
def api():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def read_policy(api):
    """A real corpus policy read through the real pipeline."""
    from pathlib import Path

    document = Path("../data/generated/policies/clean/POL007.pdf")
    if not document.exists():
        pytest.skip("corpus not built")

    session_id = api.post("/api/session").json()["session_id"]
    response = api.post(
        "/api/policy/upload-many",
        files=[("files", (document.name, document.read_bytes(), "application/pdf"))],
        data={"insurer_id": "", "session_id": session_id},
    )
    assert response.status_code == 200
    return session_id, response.json()


def _search(api, session_id, code, **extra):
    return api.post(f"/api/search/{session_id}", json={
        "procedure_code": code, "lat": 12.9716, "lon": 77.5946,
        "city": "Bengaluru", "max_distance_km": 15,
        "preference": "balanced", "urgency": "planned", **extra,
    }).json()


def _code(api, needle):
    return next(
        p["code"] for p in api.get("/api/reference").json()["procedures"]
        if needle in p["name"].lower()
    )


def test_the_policy_carries_its_household_and_period(read_policy):
    _, policy = read_policy
    assert policy["period"]["start"] and policy["period"]["end"]
    assert len(policy["insured"]) > 1
    assert policy["oldest_age"] == max(p["age"] for p in policy["insured"])


def test_every_waiting_period_carries_the_date_it_clears(read_policy):
    """A duration on its own does not answer "can I have this operation"."""
    _, policy = read_policy
    assert policy["waiting_periods"]
    for wait in policy["waiting_periods"]:
        assert wait["clears_on"]
        assert wait["duration"]
        assert wait["kind"]


def test_a_search_asks_before_it_assumes(api, read_policy):
    session_id, _ = read_policy
    found = _search(api, session_id, _code(api, "angiography"))
    verdict = found["eligibility"]
    assert verdict["verdict"] == "ask"
    assert not verdict["blocks"]
    assert any(f["question"] for f in verdict["findings"])


def test_the_answer_changes_the_verdict(api, read_policy):
    session_id, _ = read_policy
    code = _code(api, "angiography")
    assert _search(api, session_id, code, pre_existing=True)["eligibility"]["blocks"]
    assert not _search(
        api, session_id, code, pre_existing=False
    )["eligibility"]["blocks"]


def test_options_are_still_returned_when_the_claim_would_be_declined(api, read_policy):
    """Someone paying for it themselves still needs to know what it costs."""
    session_id, _ = read_policy
    found = _search(api, session_id, _code(api, "angiography"), pre_existing=True)
    assert found["eligibility"]["blocks"]
    assert found["options"]


def test_the_answer_survives_a_reload(api, read_policy):
    session_id, _ = read_policy
    _search(api, session_id, _code(api, "angiography"), pre_existing=True)
    restored = api.get(f"/api/session/{session_id}").json()
    assert restored["search"]["eligibility"]["blocks"]


def test_the_answer_survives_the_server_forgetting_the_session(api, read_policy):
    """The browser holds the durable copy, so it has to come back with it."""
    session_id, _ = read_policy
    _search(api, session_id, _code(api, "angiography"), pre_existing=True)

    snapshot = api.get(f"/api/session/{session_id}/export").json()["snapshot"]
    revived = api.post("/api/session/import", json={"snapshot": snapshot}).json()
    restored = api.get(f"/api/session/{revived['session_id']}").json()
    assert restored["search"]["eligibility"]["blocks"]


def test_a_future_admission_date_can_clear_a_waiting_period(api, read_policy):
    """Being told the date it clears is only useful if you can plan around it."""
    session_id, policy = read_policy
    longest = max(policy["waiting_periods"], key=lambda w: w["clears_on"])
    found = _search(
        api, session_id, _code(api, "angiography"),
        pre_existing=True, admission_date=longest["clears_on"],
    )
    assert not found["eligibility"]["blocks"]


# --- the co-payment band ---------------------------------------------------


def test_a_banded_copayment_falls_only_on_the_older_member():
    policy = make_policy(copay_pct=D(20), copay_above_age=61)
    assert policy.copay_for(61) == D(20)
    assert policy.copay_for(75) == D(20)
    assert policy.copay_for(60) == D(0)
    assert policy.copay_for(4) == D(0)


def test_an_unbanded_copayment_falls_on_everyone():
    policy = make_policy(copay_pct=D(20))
    assert policy.copay_for(4) == D(20)
    assert policy.copay_for(80) == D(20)


def test_an_unknown_age_is_charged_as_written():
    """The safe direction: the alternative quietly promises a claim without a
    deduction the policy imposes."""
    policy = make_policy(copay_pct=D(20), copay_above_age=61)
    assert policy.copay_for(None) == D(20)


def test_the_band_changes_what_the_waterfall_takes():
    from app.pipeline.s6_simulate.waterfall import simulate
    from app.schemas.simulation import DeductionKind

    policy = make_policy(copay_pct=D(20), copay_above_age=61)
    bill = make_bill(D(100000))

    older = simulate(policy, bill, patient_age=70)
    younger = simulate(policy, bill, patient_age=30)

    assert any(s.kind is DeductionKind.COPAY for s in older.steps)
    assert not any(s.kind is DeductionKind.COPAY for s in younger.steps)
    assert younger.out_of_pocket < older.out_of_pocket


def test_a_spared_member_is_told_why_rather_than_left_to_wonder():
    """A co-payment on the schedule and none in the estimate looks like a bug
    unless the reason is stated."""
    from app.pipeline.s6_simulate.waterfall import simulate

    policy = make_policy(copay_pct=D(20), copay_above_age=61)
    result = simulate(policy, make_bill(D(50000)), patient_age=30)
    assert any("aged 61 and above" in note for note in result.notes)


@pytest.fixture
def banded_policy(api):
    """A corpus policy whose household straddles its co-payment age band.

    Found rather than fixed, so the test exercises a document the generator
    actually produces instead of one written to suit it.
    """
    import json
    from pathlib import Path

    corpus = Path("../data/generated/policies/clean")
    if not corpus.exists():
        pytest.skip("corpus not built")

    for document in sorted(corpus.glob("*.pdf")):
        truth = json.loads(
            Path(f"../data/generated/policies/truth/{document.stem}.json").read_text()
        )["blueprint"]
        band = truth["copay_above_age"]
        ages = [age for _, age, _ in truth["members"]]
        if band and len(ages) > 1 and min(ages) < band <= max(ages):
            break
    else:
        pytest.skip("no corpus policy straddles its own co-payment band")

    session_id = api.post("/api/session").json()["session_id"]
    response = api.post(
        "/api/policy/upload-many",
        files=[("files", (document.name, document.read_bytes(), "application/pdf"))],
        data={"insurer_id": "", "session_id": session_id},
    )
    assert response.status_code == 200
    return session_id, response.json()


def test_choosing_the_patient_changes_the_bill(api, banded_policy):
    """End to end: the same treatment at the same hospital, two members."""
    session_id, policy = banded_policy
    ages = [p["age"] for p in policy["insured"]]
    band = policy["copay_above_age"]
    assert band and min(ages) < band <= max(ages)

    code = _code(api, "angiography")
    older = ages.index(next(a for a in ages if a >= band))
    younger = ages.index(next(a for a in ages if a < band))

    high = _search(api, session_id, code, patient_index=older, pre_existing=False)
    low = _search(api, session_id, code, patient_index=younger, pre_existing=False)
    assert low["options"][0]["you_pay"] < high["options"][0]["you_pay"]
