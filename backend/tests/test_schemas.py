"""M1, domain contracts.

Money handling and the expense-head classification get the heaviest coverage:
both are load-bearing for every rupee figure the system shows, and both are
places where a quiet mistake produces plausible-looking wrong numbers.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.hospital import (
    Accreditation,
    GeoPoint,
    Hospital,
    HospitalType,
    QualitySignals,
    RoomTariff,
)
from app.schemas.journey import (
    Alert,
    AlertKind,
    BurnDown,
    CostEntry,
    JourneyStage,
    JourneyState,
)
from app.schemas.match import (
    MatchResult,
    Objectives,
    Preference,
    Relaxation,
    RelaxationKind,
)
from app.schemas.money import (
    apply_pct,
    format_inr,
    format_inr_compact,
    round_inr,
    to_decimal,
)
from app.schemas.policy import (
    Clause,
    ClauseKind,
    DeductionRegime,
    DocumentSection,
    Evidence,
    ExpenseHead,
    NormalizedPolicy,
    RoomCategory,
    RoomLimit,
    RoomLimitBasis,
    SubLimit,
    is_never_payable,
    is_room_linked,
)
from app.schemas.procedure import CostSplit, Procedure, Specialty
from app.schemas.simulation import (
    BillLine,
    DeductionKind,
    EstimatedBill,
    SettlementMode,
    SimulationResult,
    WaterfallStep,
)

# --- money ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Rs. 5,00,000", Decimal(500000)),
        ("₹5,000/-", Decimal(5000)),
        ("INR 1,25,000", Decimal(125000)),
        ("  42000  ", Decimal(42000)),
        (5000, Decimal(5000)),
        (5000.5, Decimal("5000.5")),
    ],
)
def test_indian_currency_strings_are_parsed(raw, expected):
    assert to_decimal(raw) == expected


@pytest.mark.parametrize("raw", ["", "abc", None, True, "Rs. "])
def test_non_monetary_input_is_rejected(raw):
    with pytest.raises(ValueError):
        to_decimal(raw)


def test_float_input_avoids_binary_artefacts():
    # Decimal(0.1) is 0.1000000000000000055511151231257827; via str it is exact.
    assert to_decimal(0.1) == Decimal("0.1")


@pytest.mark.parametrize(
    ("value", "expected"),
    [("100.4", 100), ("100.5", 101), ("100.6", 101), ("-100.5", -101)],
)
def test_rounding_is_half_up(value, expected):
    assert round_inr(Decimal(value)) == Decimal(expected)


def test_percentage_of_amount():
    assert apply_pct(Decimal(500000), Decimal(1)) == Decimal(5000)
    assert apply_pct(Decimal(42000), Decimal("10")) == Decimal(4200)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (500, "₹500"),
        (5000, "₹5,000"),
        (500000, "₹5,00,000"),
        (1234567, "₹12,34,567"),
        (-5000, "-₹5,000"),
    ],
)
def test_indian_digit_grouping(value, expected):
    # Lakh grouping, not thousands separators.
    assert format_inr(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(500, "₹500"), (5000, "₹5K"), (500000, "₹5 L"), (12500000, "₹1.25 Cr")],
)
def test_compact_formatting_uses_indian_scale(value, expected):
    assert format_inr_compact(value) == expected


def test_rupees_field_rounds_on_construction():
    line = BillLine(head=ExpenseHead.PHARMACY, amount="4999.6")
    assert line.amount == Decimal(5000)


# --- expense head classification -----------------------------------------


def test_post_2024_exempts_icu_pharmacy_implants_and_diagnostics():
    # The May 2024 IRDAI circular narrowed proportionate deduction to
    # room-linked heads. Getting this wrong overstates deductions badly.
    for head in (
        ExpenseHead.ICU_CHARGES,
        ExpenseHead.PHARMACY,
        ExpenseHead.IMPLANTS,
        ExpenseHead.CONSUMABLES,
        ExpenseHead.INVESTIGATIONS,
    ):
        assert not is_room_linked(head, DeductionRegime.POST_2024), head


def test_post_2024_still_covers_room_linked_heads():
    for head in (
        ExpenseHead.ROOM_RENT,
        ExpenseHead.NURSING,
        ExpenseHead.SURGEON_FEE,
        ExpenseHead.OT_CHARGES,
        ExpenseHead.ANAESTHETIST_FEE,
        ExpenseHead.DOCTOR_VISIT,
    ):
        assert is_room_linked(head, DeductionRegime.POST_2024), head


def test_legacy_regime_hits_everything_payable():
    assert is_room_linked(ExpenseHead.PHARMACY, DeductionRegime.LEGACY)
    assert is_room_linked(ExpenseHead.IMPLANTS, DeductionRegime.LEGACY)


def test_non_medical_is_never_room_linked_under_any_regime():
    # It is never payable at all, so it can never be proportionately reduced.
    for regime in DeductionRegime:
        assert not is_room_linked(ExpenseHead.NON_MEDICAL, regime)
    assert is_never_payable(ExpenseHead.NON_MEDICAL)


def test_every_head_has_a_label():
    for head in ExpenseHead:
        assert head.label and not head.label.islower()


# --- room categories ------------------------------------------------------


def test_room_ladder_is_ordered_by_cost():
    assert (
        RoomCategory.GENERAL_WARD.rank
        < RoomCategory.TWIN_SHARING.rank
        < RoomCategory.SINGLE_PRIVATE.rank
        < RoomCategory.DELUXE.rank
        < RoomCategory.SUITE.rank
    )


def test_eligibility_ceiling_admits_cheaper_rooms():
    assert RoomCategory.TWIN_SHARING.is_within(RoomCategory.SINGLE_PRIVATE)
    assert RoomCategory.SINGLE_PRIVATE.is_within(RoomCategory.SINGLE_PRIVATE)
    assert not RoomCategory.DELUXE.is_within(RoomCategory.SINGLE_PRIVATE)


def test_icu_sits_outside_the_ladder():
    # ICU has its own limit; it is never "above" a room entitlement.
    assert RoomCategory.ICU.is_within(RoomCategory.GENERAL_WARD)


# --- room limits ----------------------------------------------------------


def test_percentage_basis_resolves_against_sum_insured():
    limit = RoomLimit(basis=RoomLimitBasis.PCT_OF_SI_PER_DAY, pct_of_si=Decimal(1))
    assert limit.effective_daily_cap(Decimal(500000)) == Decimal(5000)


def test_lower_of_percentage_and_flat_maximum_binds():
    # "1% of sum insured per day, subject to a maximum of Rs. 4,000", the
    # stated maximum overrides the percentage when the percentage is higher.
    limit = RoomLimit(
        basis=RoomLimitBasis.PCT_OF_SI_PER_DAY,
        pct_of_si=Decimal(1),
        amount_per_day=Decimal(4000),
    )
    assert limit.effective_daily_cap(Decimal(500000)) == Decimal(4000)


def test_no_limit_resolves_to_none():
    assert RoomLimit().effective_daily_cap(Decimal(500000)) is None


def test_limit_description_is_human_readable():
    limit = RoomLimit(basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=Decimal(5000))
    assert "₹5,000 per day" in limit.describe(Decimal(500000))
    assert RoomLimit().describe(Decimal(500000)) == "No room rent limit"


# --- clauses --------------------------------------------------------------


def _clause(**kw) -> Clause:
    defaults = dict(
        kind=ClauseKind.SUM_INSURED,
        verbatim="Sum Insured: Rs. 5,00,000",
        evidence=Evidence(page_index=0),
    )
    return Clause(**{**defaults, **kw})


def test_schedule_beats_wording_on_conflict():
    # The schedule carries this policyholder's real numbers; wording is generic.
    schedule = _clause(evidence=Evidence(page_index=0, section=DocumentSection.SCHEDULE))
    wording = _clause(
        evidence=Evidence(page_index=9, section=DocumentSection.WORDING), confidence=0.99
    )
    assert schedule.supersedes(wording)
    assert not wording.supersedes(schedule)


def test_endorsement_beats_schedule():
    endorsement = _clause(
        evidence=Evidence(page_index=0, section=DocumentSection.ENDORSEMENT)
    )
    schedule = _clause(evidence=Evidence(page_index=0, section=DocumentSection.SCHEDULE))
    assert endorsement.supersedes(schedule)


def test_confidence_breaks_ties_within_a_section():
    high = _clause(confidence=0.9)
    low = _clause(confidence=0.4)
    assert high.supersedes(low)


def test_rejected_clauses_are_inadmissible():
    from app.schemas.policy import ClauseStatus

    assert _clause().is_admissible
    assert not _clause(status=ClauseStatus.REJECTED).is_admissible
    assert _clause(status=ClauseStatus.CONFIRMED).is_admissible


def test_challenge_requires_a_target():
    from app.schemas.policy import Challenge, ChallengeKind

    with pytest.raises(ValidationError, match="must reference"):
        Challenge(kind=ChallengeKind.CONTRADICTION, question="?")

    assert Challenge(
        kind=ChallengeKind.MISSING, target_kind=ClauseKind.SUM_INSURED, question="?"
    )


# --- normalized policy ----------------------------------------------------


def test_remaining_cover_overrides_sum_insured():
    policy = NormalizedPolicy(sum_insured=Decimal(500000))
    assert policy.available_cover == Decimal(500000)
    policy.sum_insured_remaining = Decimal(120000)
    assert policy.available_cover == Decimal(120000)


def test_policy_without_sum_insured_is_unusable():
    assert not NormalizedPolicy().is_usable
    assert NormalizedPolicy(sum_insured=Decimal(1)).is_usable


def test_sublimit_lookup_by_head_and_procedure():
    policy = NormalizedPolicy(
        sum_insured=Decimal(500000),
        sublimits=[
            SubLimit(head=ExpenseHead.INVESTIGATIONS, amount=Decimal(25000)),
            SubLimit(procedure_code="CGHS-0421", amount=Decimal(40000)),
        ],
    )
    assert policy.sublimit_for(ExpenseHead.INVESTIGATIONS).amount == Decimal(25000)
    assert policy.sublimit_for(ExpenseHead.PHARMACY) is None
    assert policy.sublimit_for_procedure("CGHS-0421").amount == Decimal(40000)


def test_sublimit_needs_a_target_and_a_cap():
    with pytest.raises(ValidationError, match="expense head or a procedure"):
        SubLimit(amount=Decimal(1000))
    with pytest.raises(ValidationError, match="amount or a percentage"):
        SubLimit(head=ExpenseHead.PHARMACY)


def test_per_day_sublimit_scales_with_stay():
    limit = SubLimit(head=ExpenseHead.NURSING, amount=Decimal(500), per_day=True)
    assert limit.resolve(Decimal(500000), days=4) == Decimal(2000)


# --- procedures -----------------------------------------------------------


def test_cost_split_must_sum_to_one():
    with pytest.raises(ValidationError, match="sum to 1.0"):
        CostSplit(fractions={ExpenseHead.ROOM_RENT: 0.5, ExpenseHead.PHARMACY: 0.2})


def test_cost_split_apply_reconciles_exactly():
    # Rounding residue must land somewhere, or lines stop summing to the total.
    split = CostSplit(
        fractions={
            ExpenseHead.ROOM_RENT: 0.333,
            ExpenseHead.SURGEON_FEE: 0.333,
            ExpenseHead.PHARMACY: 0.334,
        }
    )
    amounts = split.apply(Decimal(100000))
    assert sum(amounts.values()) == Decimal(100000)


def test_nabh_accreditation_selects_the_higher_package_rate():
    proc = Procedure(
        code="P1",
        name="Test",
        specialty=Specialty.GENERAL_SURGERY,
        base_rate_non_nabh=Decimal(20000),
        base_rate_nabh=Decimal(23000),
        cost_split=CostSplit(fractions={ExpenseHead.SURGEON_FEE: 1.0}),
    )
    assert proc.base_rate(nabh=True) == Decimal(23000)
    assert proc.package_price(nabh=True, cost_index=1.5) == Decimal(34500)


# --- hospitals ------------------------------------------------------------


def _hospital(**kw) -> Hospital:
    defaults = dict(
        hospital_id="H1",
        name="Test Hospital",
        hospital_type=HospitalType.PRIVATE,
        location=GeoPoint(lat=12.97, lon=77.59),
        locality="Indiranagar",
        city="Bengaluru",
        state="Karnataka",
        room_tariffs=[
            RoomTariff(category=RoomCategory.GENERAL_WARD, per_day=2000, beds_available=4),
            RoomTariff(category=RoomCategory.TWIN_SHARING, per_day=4000, beds_available=0),
            RoomTariff(category=RoomCategory.SINGLE_PRIVATE, per_day=7500, beds_available=2),
        ],
    )
    return Hospital(**{**defaults, **kw})


def test_distance_between_known_points():
    # Bengaluru city centre to Whitefield is roughly 17 km.
    centre = GeoPoint(lat=12.9716, lon=77.5946)
    whitefield = GeoPoint(lat=12.9698, lon=77.7500)
    assert 16 < centre.distance_km(whitefield) < 18


def test_zero_distance_to_self():
    p = GeoPoint(lat=12.97, lon=77.59)
    assert p.distance_km(p) == pytest.approx(0.0, abs=1e-9)


def test_cheapest_room_within_ceiling():
    h = _hospital()
    assert h.cheapest_room_within(RoomCategory.SINGLE_PRIVATE).per_day == Decimal(2000)
    assert h.cheapest_room_within(RoomCategory.GENERAL_WARD).per_day == Decimal(2000)


def test_available_rooms_excludes_full_categories():
    categories = {t.category for t in _hospital().available_rooms()}
    assert RoomCategory.TWIN_SHARING not in categories
    assert RoomCategory.SINGLE_PRIVATE in categories


def test_cashless_membership_is_per_insurer():
    h = _hospital(cashless_insurers=["INS_A"])
    assert h.is_cashless_for("INS_A")
    assert not h.is_cashless_for("INS_B")


def test_capability_score_rises_with_accreditation():
    weak = QualitySignals(accreditation=Accreditation.NONE, bed_count=100)
    strong = QualitySignals(accreditation=Accreditation.JCI, bed_count=100)
    assert strong.capability_score > weak.capability_score
    assert 0.0 <= weak.capability_score <= 1.0


def test_capability_score_saturates():
    # A 5000-bed hospital is not ten times better than a 500-bed one: once every
    # component maxes out the score reaches 1.0 and stops.
    maxed = dict(accreditation=Accreditation.JCI, bed_count=500, icu_beds=60,
                 specialty_count=20, doctor_count=200, has_emergency=True,
                 has_blood_bank=True)
    assert QualitySignals(**maxed).capability_score == pytest.approx(1.0)

    tenfold = QualitySignals(**{**maxed, "bed_count": 5000, "doctor_count": 2000})
    assert tenfold.capability_score == pytest.approx(1.0)


# --- simulation -----------------------------------------------------------


def _bill(*lines: tuple[ExpenseHead, int]) -> EstimatedBill:
    return EstimatedBill(
        hospital_id="H1",
        procedure_code="P1",
        room_category=RoomCategory.SINGLE_PRIVATE,
        los_days=4,
        room_rate_per_day=Decimal(8000),
        lines=[BillLine(head=h, amount=Decimal(a)) for h, a in lines],
    )


def test_bill_total_sums_its_lines():
    bill = _bill((ExpenseHead.ROOM_RENT, 32000), (ExpenseHead.PHARMACY, 18000))
    assert bill.total == Decimal(50000)


def test_bill_groups_repeated_heads():
    bill = _bill((ExpenseHead.PHARMACY, 1000), (ExpenseHead.PHARMACY, 500))
    assert bill.amount_for(ExpenseHead.PHARMACY) == Decimal(1500)
    assert bill.by_head()[ExpenseHead.PHARMACY] == Decimal(1500)


def _result(steps: list[WaterfallStep], payable: int, gross: int) -> SimulationResult:
    return SimulationResult(
        hospital_id="H1",
        procedure_code="P1",
        room_category=RoomCategory.SINGLE_PRIVATE,
        bill=_bill((ExpenseHead.ROOM_RENT, gross)),
        steps=steps,
        payable_by_insurer=Decimal(payable),
        out_of_pocket=Decimal(gross - payable),
        cash_to_arrange_upfront=Decimal(gross - payable),
        settlement_mode=SettlementMode.CASHLESS,
    )


def test_reconciliation_passes_when_deductions_account_for_the_gap():
    steps = [
        WaterfallStep(
            kind=DeductionKind.COPAY,
            deducted=Decimal(10000),
            payable_after=Decimal(90000),
            explanation="10% co-pay",
        )
    ]
    assert _result(steps, payable=90000, gross=100000).reconciles()


def test_reconciliation_fails_when_a_deduction_is_unaccounted():
    steps = [
        WaterfallStep(
            kind=DeductionKind.COPAY,
            deducted=Decimal(5000),
            payable_after=Decimal(95000),
            explanation="wrong",
        )
    ]
    assert not _result(steps, payable=90000, gross=100000).reconciles()


def test_deduction_totals_are_queryable_by_kind():
    steps = [
        WaterfallStep(kind=DeductionKind.COPAY, deducted=Decimal(100),
                      payable_after=Decimal(0), explanation=""),
        WaterfallStep(kind=DeductionKind.COPAY, deducted=Decimal(50),
                      payable_after=Decimal(0), explanation=""),
        WaterfallStep(kind=DeductionKind.SUBLIMIT, deducted=Decimal(25),
                      payable_after=Decimal(0), explanation=""),
    ]
    result = _result(steps, payable=100000, gross=100000)
    assert result.deduction_for(DeductionKind.COPAY) == Decimal(150)
    assert result.deduction_for(DeductionKind.DEDUCTIBLE) == Decimal(0)


def test_every_deduction_kind_has_a_plain_language_label():
    for kind in DeductionKind:
        assert kind.label and " " in kind.label


# --- matching -------------------------------------------------------------


def test_pareto_dominance():
    strong = Objectives(affordability=0.9, capability=0.9, proximity=0.9, cashless=1.0)
    weak = Objectives(affordability=0.5, capability=0.5, proximity=0.5, cashless=1.0)
    assert strong.dominates(weak)
    assert not weak.dominates(strong)


def test_equal_options_do_not_dominate_each_other():
    a = Objectives(affordability=0.5, capability=0.5, proximity=0.5, cashless=0.5)
    assert not a.dominates(a.model_copy())


def test_trade_off_options_do_not_dominate_each_other():
    # Cheap-and-far versus costly-and-near: neither is objectively better.
    cheap = Objectives(affordability=0.9, capability=0.4, proximity=0.2, cashless=1.0)
    near = Objectives(affordability=0.3, capability=0.4, proximity=0.95, cashless=1.0)
    assert not cheap.dominates(near)
    assert not near.dominates(cheap)


def test_preference_weights_are_normalised():
    for pref in Preference:
        assert sum(pref.weights.values()) == pytest.approx(1.0)


def test_preference_changes_the_winner():
    cheap = Objectives(affordability=0.95, capability=0.3, proximity=0.4, cashless=1.0)
    good = Objectives(affordability=0.3, capability=0.95, proximity=0.4, cashless=1.0)
    assert cheap.score(Preference.PROTECT_MONEY.weights) > good.score(
        Preference.PROTECT_MONEY.weights
    )
    assert good.score(Preference.BEST_CARE.weights) > cheap.score(
        Preference.BEST_CARE.weights
    )


def test_relaxation_ladder_is_ordered_by_user_cost():
    # Travelling further is a smaller sacrifice than losing cashless settlement.
    assert RelaxationKind.WIDER_RADIUS < RelaxationKind.NON_NETWORK
    assert RelaxationKind.NONE < RelaxationKind.ROOM_CATEGORY


def test_match_tier_reports_the_deepest_relaxation():
    result = MatchResult(
        relaxations=[
            Relaxation(kind=RelaxationKind.WIDER_RADIUS, description="", consequence=""),
            Relaxation(kind=RelaxationKind.NON_NETWORK, description="", consequence=""),
        ]
    )
    assert result.tier == RelaxationKind.NON_NETWORK.value
    assert not result.is_fully_satisfied


def test_a_search_with_no_options_is_not_fully_satisfied():
    # Zero relaxations but zero results is a starved search, not a clean one.
    empty = MatchResult()
    assert empty.tier == 0
    assert not empty.is_fully_satisfied


def test_exclusions_are_summarised_by_cause():
    from app.schemas.match import Exclusion, ExclusionCause

    result = MatchResult(
        exclusions=[
            Exclusion(hospital_id="1", hospital_name="A", cause=ExclusionCause.TOO_FAR),
            Exclusion(hospital_id="2", hospital_name="B", cause=ExclusionCause.TOO_FAR),
            Exclusion(hospital_id="3", hospital_name="C", cause=ExclusionCause.NOT_CASHLESS),
        ]
    )
    assert result.exclusion_summary() == {"too_far": 2, "not_cashless": 1}


# --- journey --------------------------------------------------------------


def test_stage_ordering_is_monotonic():
    stages = list(JourneyStage)
    assert [s.order for s in stages] == sorted(s.order for s in stages)


def test_settled_is_the_last_stage():
    assert max(JourneyStage, key=lambda s: s.order) is JourneyStage.SETTLED


def test_every_stage_has_a_distinct_position():
    orders = [s.order for s in JourneyStage]
    assert len(set(orders)) == len(orders)


def test_accrued_costs_total_and_group():
    state = JourneyState(
        costs=[
            CostEntry(head=ExpenseHead.ROOM_RENT, amount=Decimal(8000)),
            CostEntry(head=ExpenseHead.ROOM_RENT, amount=Decimal(8000)),
            CostEntry(head=ExpenseHead.PHARMACY, amount=Decimal(3200)),
        ]
    )
    assert state.accrued_total == Decimal(19200)
    assert state.accrued_by_head()[ExpenseHead.ROOM_RENT] == Decimal(16000)


def test_journey_activity_flags():
    assert not JourneyState(stage=JourneyStage.PRE_ADMISSION).is_active
    assert JourneyState(stage=JourneyStage.ADMITTED).is_active
    assert JourneyState(stage=JourneyStage.DISCHARGE_PLANNING).is_active
    assert not JourneyState(stage=JourneyStage.SETTLED).is_active


def test_burndown_projects_overrun():
    burn = BurnDown(
        sum_insured=Decimal(500000),
        consumed=Decimal(200000),
        projected_total=Decimal(620000),
        remaining=Decimal(300000),
    )
    assert burn.consumed_fraction == pytest.approx(0.4)
    assert burn.will_exceed


def test_alert_carries_an_action():
    alert = Alert(
        kind=AlertKind.ROOM_OVER_LIMIT,
        title="Room above your limit",
        message="You are in a room costing more than your policy covers.",
        action="Ask about moving to twin sharing.",
        amount=Decimal(22000),
    )
    assert alert.action
    assert alert.amount == Decimal(22000)
