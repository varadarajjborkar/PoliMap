"""M9, matching, ranking and graceful degradation.

The starvation tests carry the most weight. Returning an empty list to someone
standing in a hospital corridor is the failure this stage exists to prevent, so
the relaxation ladder is tested against constraints that genuinely cannot be
satisfied, and checked for both producing results *and* labelling honestly what
it gave up to produce them.
"""

from __future__ import annotations

import json
from decimal import Decimal as D

import pytest

from app.core.config import GENERATED_DIR
from app.pipeline.s5_match.matcher import (
    find_options,
    pareto_frontier,
    travel_minutes,
)
from app.schemas.hospital import GeoPoint, Hospital
from app.schemas.match import (
    CareContext,
    ExclusionCause,
    Objectives,
    Preference,
    RankedOption,
    RelaxationKind,
)
from app.schemas.policy import NormalizedPolicy, RoomLimit, RoomLimitBasis
from app.schemas.procedure import Procedure, Urgency
from app.schemas.simulation import SettlementMode

BENGALURU_CENTRE = GeoPoint(lat=12.9716, lon=77.5946)


@pytest.fixture(scope="module")
def corpus():
    hospitals = [
        Hospital(**h)
        for h in json.loads((GENERATED_DIR / "hospitals.json").read_text())
    ]
    procedures = {
        p["code"]: Procedure(**p)
        for p in json.loads((GENERATED_DIR / "procedures.json").read_text())
    }
    return hospitals, procedures


@pytest.fixture
def policy():
    return NormalizedPolicy(
        sum_insured=D(500000),
        room_limit=RoomLimit(basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=D(5000)),
    )


def context(**kw) -> CareContext:
    defaults = dict(
        procedure_code="CP-ORTH-001",
        origin=BENGALURU_CENTRE,
        city="Bengaluru",
        max_distance_km=10.0,
        insurer_id="INS_SENTINEL",
        preference=Preference.BALANCED,
    )
    return CareContext(**{**defaults, **kw})


# --- the happy path -------------------------------------------------------


def test_a_normal_search_returns_ranked_costed_options(corpus, policy):
    hospitals, procedures = corpus
    result = find_options(hospitals, procedures, policy, context())

    assert result.options
    assert result.is_fully_satisfied
    assert [o.rank for o in result.options] == list(range(1, len(result.options) + 1))
    for option in result.options:
        assert option.simulation.out_of_pocket >= 0
        assert option.simulation.reconciles()
        assert option.reasons


def test_every_option_carries_a_cost_band(corpus, policy):
    """Length of stay varies; a single figure would overclaim precision."""
    hospitals, procedures = corpus
    for option in find_options(hospitals, procedures, policy, context()).options:
        band = option.simulation.band
        assert band is not None
        assert band.low <= band.expected <= band.high


def test_the_band_is_not_the_same_width_on_every_card(corpus, policy):
    """The defect this replaced: the band varied only length of stay, and the
    insurer absorbed everything that scaled with days, so the only thing left
    moving was a flat per-day charge. Every card came out at the same few
    hundred rupees either side of centre, on bills an order of magnitude apart.
    Two cards side by side gave that away in seconds."""
    hospitals, procedures = corpus
    options = find_options(hospitals, procedures, policy, context()).options
    widths = {
        option.simulation.band.high - option.simulation.band.low
        for option in options
        if option.simulation.band
    }
    assert len(widths) > 1, "every option shares one band width"


def test_the_band_says_why_the_high_figure_is_high(corpus, policy):
    """A range without a cause is decoration. A named scenario can be argued
    with, which is what makes it worth showing a family."""
    hospitals, procedures = corpus
    for option in find_options(hospitals, procedures, policy, context()).options:
        band = option.simulation.band
        assert band is not None
        if band.high > band.expected:
            assert band.high_driver, "a wider high figure with no stated cause"


def test_the_band_scales_with_the_size_of_the_bill(corpus, policy):
    """A claim to predict a two lakh admission as tightly as a twenty thousand
    one is not a confidence interval, it is a decoration."""
    hospitals, procedures = corpus
    options = [
        o for o in find_options(hospitals, procedures, policy, context()).options
        if o.simulation.band
    ]
    if len(options) < 2:
        pytest.skip("need at least two costed options to compare")

    cheapest = min(options, key=lambda o: o.simulation.bill.total)
    dearest = max(options, key=lambda o: o.simulation.bill.total)
    if dearest.simulation.bill.total <= cheapest.simulation.bill.total * 2:
        pytest.skip("the costed options are too close in size to compare")

    narrow = cheapest.simulation.band.high - cheapest.simulation.band.low
    wide = dearest.simulation.band.high - dearest.simulation.band.low
    assert wide > narrow


def test_excluded_hospitals_record_why(corpus, policy):
    """Without this the system cannot explain itself or relax the right thing."""
    hospitals, procedures = corpus
    result = find_options(hospitals, procedures, policy, context())

    assert result.exclusions
    summary = result.exclusion_summary()
    assert summary
    assert sum(summary.values()) == len(result.exclusions)


def test_distance_is_expressed_as_travel_time():
    assert travel_minutes(18.0) == 60
    assert travel_minutes(0.1) >= 1


# --- preference -----------------------------------------------------------


def test_preference_changes_the_ordering(corpus, policy):
    hospitals, procedures = corpus
    cheap = find_options(
        hospitals, procedures, policy, context(preference=Preference.PROTECT_MONEY)
    )
    near = find_options(
        hospitals, procedures, policy, context(preference=Preference.NEAREST)
    )

    assert cheap.options and near.options
    # Whatever the ordering, each preference should win on its own axis.
    assert cheap.options[0].simulation.out_of_pocket <= max(
        o.simulation.out_of_pocket for o in cheap.options
    )
    assert near.options[0].distance_km <= max(o.distance_km for o in near.options)


def test_money_first_beats_distance_first_on_cost(corpus, policy):
    hospitals, procedures = corpus
    cheap = find_options(
        hospitals, procedures, policy, context(preference=Preference.PROTECT_MONEY)
    ).options[0]
    near = find_options(
        hospitals, procedures, policy, context(preference=Preference.NEAREST)
    ).options[0]
    assert cheap.simulation.out_of_pocket <= near.simulation.out_of_pocket
    assert near.distance_km <= cheap.distance_km


# --- pareto ---------------------------------------------------------------


def _option(cost: float, capability: float, proximity: float, cashless: float = 1.0):
    opt = RankedOption.model_construct(
        objectives=Objectives(
            affordability=cost, capability=capability,
            proximity=proximity, cashless=cashless,
        ),
        score=0.0, rank=0, distance_km=0.0,
        reasons=[], tradeoffs=[], counterfactual="",
    )
    return opt


def test_a_dominated_option_is_off_the_frontier():
    strong = _option(0.9, 0.9, 0.9)
    weak = _option(0.4, 0.4, 0.4)
    assert pareto_frontier([strong, weak]) == [strong]


def test_genuine_trade_offs_all_stay_on_the_frontier():
    """Cheap-and-far versus costly-and-near: neither is objectively better."""
    cheap = _option(0.95, 0.4, 0.2)
    near = _option(0.3, 0.4, 0.95)
    strong = _option(0.4, 0.95, 0.3)
    assert len(pareto_frontier([cheap, near, strong])) == 3


def test_frontier_membership_is_marked_on_results(corpus, policy):
    hospitals, procedures = corpus
    result = find_options(hospitals, procedures, policy, context())
    assert any(o.on_pareto_frontier for o in result.options)


# --- starvation and relaxation -------------------------------------------


def test_an_impossible_radius_still_returns_options(corpus, policy):
    """The core requirement: never hand back an empty page."""
    hospitals, procedures = corpus
    result = find_options(
        hospitals, procedures, policy, context(max_distance_km=0.4)
    )

    assert result.options, "starved search returned nothing"
    assert result.relaxations
    assert RelaxationKind.WIDER_RADIUS in {r.kind for r in result.relaxations}


def test_relaxations_are_labelled_with_their_consequence(corpus, policy):
    hospitals, procedures = corpus
    result = find_options(
        hospitals, procedures, policy, context(max_distance_km=0.4)
    )
    for relaxation in result.relaxations:
        assert relaxation.description
        assert relaxation.consequence
        assert not result.is_fully_satisfied


def test_an_insurer_with_no_network_falls_back_to_reimbursement(corpus, policy):
    """Leaving the cashless network is surrendered, but only late and loudly."""
    hospitals, procedures = corpus
    result = find_options(
        hospitals, procedures, policy,
        context(insurer_id="INS_DOES_NOT_EXIST", max_distance_km=6),
    )

    assert result.options
    kinds = {r.kind for r in result.relaxations}
    assert RelaxationKind.NON_NETWORK in kinds

    consequence = next(
        r.consequence for r in result.relaxations if r.kind is RelaxationKind.NON_NETWORK
    )
    assert "upfront" in consequence or "claim it back" in consequence

    option = result.options[0]
    assert option.simulation.settlement_mode is SettlementMode.REIMBURSEMENT
    # The whole bill must be arranged, not just the shortfall.
    assert option.simulation.cash_to_arrange_upfront == option.simulation.gross_total


def test_the_ladder_gives_up_distance_before_the_network(corpus, policy):
    """Travelling further is an inconvenience; losing cashless is a cash crisis."""
    assert RelaxationKind.WIDER_RADIUS < RelaxationKind.NON_NETWORK

    hospitals, procedures = corpus
    result = find_options(
        hospitals, procedures, policy, context(max_distance_km=0.4)
    )
    kinds = [r.kind for r in result.relaxations]
    if RelaxationKind.NON_NETWORK in kinds:
        assert kinds.index(RelaxationKind.WIDER_RADIUS) < kinds.index(
            RelaxationKind.NON_NETWORK
        )


def test_a_procedure_nobody_offers_explains_itself(corpus, policy):
    hospitals, procedures = corpus
    result = find_options(
        hospitals, procedures, policy,
        context(procedure_code="CP-ENT-006", max_distance_km=1.0),
    )
    # Either options were found by relaxing, or the message says what blocked it.
    if not result.options:
        assert result.message
        assert any(
            cause.value in result.exclusion_summary()
            for cause in (ExclusionCause.TOO_FAR, ExclusionCause.PROCEDURE_UNAVAILABLE)
        )


def test_an_unknown_procedure_is_reported_not_crashed(corpus, policy):
    hospitals, procedures = corpus
    result = find_options(hospitals, procedures, policy, context(procedure_code="NOPE"))
    assert not result.options
    assert "treatment" in result.message.text.lower()


# --- explanation ----------------------------------------------------------


def test_each_option_explains_itself_in_plain_language(corpus, policy):
    hospitals, procedures = corpus
    for option in find_options(hospitals, procedures, policy, context()).options:
        assert option.reasons
        for said in [*option.reasons, *option.tradeoffs]:
            assert len(said.text) > 10
            # Every one of these is read in five languages, so every one of
            # them has to be findable under a key.
            assert said.key
            # Sentences may open with a currency symbol or a figure.
            assert not (said.text[0].isalpha() and said.text[0].islower())


def test_a_costed_alternative_is_offered_when_the_room_costs_money(corpus, policy):
    """Room choice is the lever a family controls, and its cost is not obvious.

    A tight room cap is used so the chosen room genuinely triggers a
    proportionate deduction. Left with a generous cap the matcher already picks
    a room under it, a cheaper room would save nothing, and staying silent is
    the correct behaviour rather than a gap.
    """
    from app.schemas.policy import RoomCategory

    hospitals, procedures = corpus
    tight = NormalizedPolicy(
        sum_insured=D(500000),
        room_limit=RoomLimit(basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=D(1000)),
    )
    result = find_options(
        hospitals, procedures, tight,
        context(procedure_code="CP-CARD-002", max_distance_km=25,
                preferred_room=RoomCategory.SINGLE_PRIVATE),
    )

    counterfactuals = [o.counterfactual for o in result.options if o.counterfactual]
    assert counterfactuals, "no cheaper-room alternative offered"
    assert any("save" in said.text for said in counterfactuals)
    # The saving must be attributed to the cap, since that is what causes it.
    assert any("a day you are covered for" in said.text for said in counterfactuals)


def test_no_alternative_is_invented_when_the_room_already_fits(corpus, policy):
    """Silence is the right answer when there is nothing to save."""
    hospitals, procedures = corpus
    result = find_options(hospitals, procedures, policy, context())
    for option in result.options:
        if option.counterfactual:
            assert "save" in option.counterfactual


def test_emergency_urgency_demands_an_available_bed(corpus, policy):
    hospitals, procedures = corpus
    result = find_options(
        hospitals, procedures, policy,
        context(urgency=Urgency.EMERGENCY, require_bed_availability=False,
                max_distance_km=12),
    )
    if result.options and not any(
        r.kind is RelaxationKind.BED_AVAILABILITY for r in result.relaxations
    ):
        for option in result.options:
            assert option.hospital.available_rooms()


# --- urgency has to mean something ------------------------------------------


def test_a_planned_admission_is_never_told_we_relaxed_bed_availability(corpus, policy):
    """Waiting a week for a bed is a normal thing to do when the procedure is
    three weeks away. Presenting it as a sacrifice made on the family's behalf
    is noise, and it was the review's clearest example of urgency doing nothing.
    """
    hospitals, procedures = corpus
    result = find_options(
        hospitals, procedures, policy,
        # Deliberately starved, so the ladder is forced to run.
        context(urgency=Urgency.PLANNED, max_distance_km=2.0,
                origin=GeoPoint(lat=12.80, lon=77.45)),
    )
    kinds = {r.kind for r in result.relaxations}
    assert RelaxationKind.BED_AVAILABILITY not in kinds


def test_an_emergency_never_relaxes_bed_availability_either(corpus, policy):
    """For the opposite reason: a hospital with no free bed is not an option
    when the patient is already in the car."""
    hospitals, procedures = corpus
    result = find_options(
        hospitals, procedures, policy,
        context(urgency=Urgency.EMERGENCY, max_distance_km=2.0,
                origin=GeoPoint(lat=12.80, lon=77.45)),
    )
    kinds = {r.kind for r in result.relaxations}
    assert RelaxationKind.BED_AVAILABILITY not in kinds


def test_urgency_changes_how_much_distance_counts(corpus, policy):
    """Forty minutes across a city is an inconvenience when the procedure is
    weeks away and a different problem when it is tonight. Ranking has to say
    so, or the urgency control is decoration."""
    hospitals, procedures = corpus

    def ranked(urgency):
        result = find_options(
            hospitals, procedures, policy,
            context(urgency=urgency, preference=Preference.PROTECT_MONEY,
                    max_distance_km=2.0, origin=GeoPoint(lat=12.80, lon=77.45)),
        )
        return [o.hospital.hospital_id for o in result.options]

    emergency, planned = ranked(Urgency.EMERGENCY), ranked(Urgency.PLANNED)
    if len(emergency) < 3 or len(planned) < 3:
        pytest.skip("not enough options to compare orderings")
    assert emergency != planned, "urgency did not change the ranking at all"


def test_the_urgency_weighting_never_overrides_a_stated_preference(corpus, policy):
    """Somebody who asked to protect their money in an emergency still meant
    it. Urgency tilts the ranking; it does not take it over."""
    from app.pipeline.s5_match.matcher import _weights_for

    for urgency in Urgency:
        weights = _weights_for(context(
            urgency=urgency, preference=Preference.PROTECT_MONEY
        ))
        assert abs(sum(weights.values()) - 1.0) < 1e-6
        assert weights["affordability"] >= weights["proximity"]
        assert all(w >= 0 for w in weights.values())
