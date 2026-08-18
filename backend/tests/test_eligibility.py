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
