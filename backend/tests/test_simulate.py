"""M8 — the cost engine.

Every expected figure here is computed by hand in the test itself rather than
captured from a previous run. A snapshot test on a money engine only proves the
behaviour has not changed; it cannot tell you the behaviour was ever right.

The reconciliation invariant is asserted everywhere: deductions must exactly
account for the gap between the bill and the payout. A breakdown whose lines do
not sum to its own total destroys a user's trust faster than an estimate that is
merely imprecise.
"""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from app.pipeline.s6_simulate.waterfall import _format_ratio, simulate
from app.schemas.policy import (
    DeductionRegime,
    ExpenseHead,
    NormalizedPolicy,
    RoomCategory,
    RoomLimit,
    RoomLimitBasis,
    SubLimit,
)
from app.schemas.simulation import (
    BillLine,
    DeductionKind,
    EstimatedBill,
    SettlementMode,
)


def make_bill(
    *lines: tuple[ExpenseHead, int],
    room_rate: int = 8000,
    los: float = 5,
    icu: float = 0,
    room: RoomCategory = RoomCategory.SINGLE_PRIVATE,
    procedure: str = "P1",
) -> EstimatedBill:
    return EstimatedBill(
        hospital_id="H1", procedure_code=procedure, room_category=room,
        los_days=los, icu_days=icu, room_rate_per_day=D(room_rate),
        lines=[BillLine(head=h, amount=D(a)) for h, a in lines],
    )


def make_policy(**kw) -> NormalizedPolicy:
    defaults = dict(
        sum_insured=D(500000),
        room_limit=RoomLimit(basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=D(5000)),
        deduction_regime=DeductionRegime.POST_2024,
    )
    return NormalizedPolicy(**{**defaults, **kw})


# The canonical bill used across the proportionate-deduction tests.
#   room-linked : surgeon 60,000 + OT 30,000 + nursing 20,000 = 1,10,000
#   exempt      : pharmacy 25,000 + tests 15,000 + implants 10,000 = 50,000
#   room        : 40,000 (5 nights at 8,000)
#   gross       : 2,00,000
CANONICAL = (
    (ExpenseHead.ROOM_RENT, 40000),
    (ExpenseHead.SURGEON_FEE, 60000),
    (ExpenseHead.OT_CHARGES, 30000),
    (ExpenseHead.NURSING, 20000),
    (ExpenseHead.PHARMACY, 25000),
    (ExpenseHead.INVESTIGATIONS, 15000),
    (ExpenseHead.IMPLANTS, 10000),
)


# --- proportionate deduction ---------------------------------------------


def test_canonical_proportionate_deduction():
    """5 lakh policy, 5,000/day cap, an 8,000/day room. Ratio 62.5%.

        room      40,000 capped to 25,000                    -> -15,000
        linked   1,10,000 x 62.5% = 68,750                   -> -41,250
        exempt      50,000 untouched
        payable   25,000 + 68,750 + 50,000                   = 1,43,750
    """
    result = simulate(make_policy(), make_bill(*CANONICAL))

    assert result.gross_total == D(200000)
    assert result.deduction_for(DeductionKind.ROOM_RENT_CAP) == D(15000)
    assert result.deduction_for(DeductionKind.PROPORTIONATE) == D(41250)
    assert result.payable_by_insurer == D(143750)
    assert result.out_of_pocket == D(56250)
    assert result.reconciles()


def test_exempt_heads_are_untouched_by_the_proportionate_reduction():
    """The May 2024 boundary. Getting it wrong overstates the deduction badly."""
    result = simulate(make_policy(), make_bill(*CANONICAL))
    step = next(s for s in result.steps if s.kind is DeductionKind.PROPORTIONATE)

    for head in (ExpenseHead.PHARMACY, ExpenseHead.INVESTIGATIONS,
                 ExpenseHead.IMPLANTS, ExpenseHead.ICU_CHARGES):
        assert head not in step.affected_heads


def test_legacy_regime_reduces_the_whole_bill():
    """Pre-2024 practice, kept so the two can be compared and explained.

        room      40,000 capped to 25,000                    -> -15,000
        everything else 1,60,000 x 62.5% = 1,00,000          -> -60,000
        payable   25,000 + 1,00,000                          = 1,25,000

    Under the post-2024 rules the same admission pays 1,43,750, so the reform
    is worth 18,750 to this patient. Modelling both is what lets the system
    show that rather than assert it.
    """
    result = simulate(
        make_policy(deduction_regime=DeductionRegime.LEGACY), make_bill(*CANONICAL)
    )
    assert result.payable_by_insurer == D(125000)
    assert result.out_of_pocket == D(75000)
    # Strictly worse for the patient than the post-2024 rules.
    assert result.out_of_pocket > D(56250)
    assert result.reconciles()


def test_room_within_the_limit_triggers_nothing():
    result = simulate(
        make_policy(),
        make_bill(*CANONICAL, room_rate=4000, room=RoomCategory.TWIN_SHARING),
    )
    assert result.deduction_for(DeductionKind.ROOM_RENT_CAP) == 0
    assert result.deduction_for(DeductionKind.PROPORTIONATE) == 0
    assert result.payable_by_insurer == D(200000)


def test_icu_days_are_excluded_from_the_room_rent_excess():
    """A patient in ICU is not occupying their ward bed, and is not billed for it."""
    with_icu = simulate(
        make_policy(),
        make_bill(*CANONICAL, los=5, icu=2),
    )
    without = simulate(make_policy(), make_bill(*CANONICAL, los=5, icu=0))
    assert with_icu.deduction_for(DeductionKind.ROOM_RENT_CAP) < without.deduction_for(
        DeductionKind.ROOM_RENT_CAP
    )


def test_percentage_room_limit_resolves_against_sum_insured():
    # 1% of 5,00,000 = 5,000/day — identical to the flat case.
    policy = make_policy(
        room_limit=RoomLimit(basis=RoomLimitBasis.PCT_OF_SI_PER_DAY, pct_of_si=D(1))
    )
    assert simulate(policy, make_bill(*CANONICAL)).payable_by_insurer == D(143750)


def test_uncapped_policy_pays_the_full_bill():
    policy = make_policy(room_limit=RoomLimit(basis=RoomLimitBasis.NO_LIMIT))
    result = simulate(policy, make_bill(*CANONICAL))
    assert result.payable_by_insurer == D(200000)
    assert result.out_of_pocket == 0


def test_category_entitlement_without_a_figure_warns_instead_of_guessing():
    """No rupee cap is stated, so the reduction cannot be computed honestly."""
    policy = make_policy(
        room_limit=RoomLimit(
            basis=RoomLimitBasis.CATEGORY_ONLY,
            category_ceiling=RoomCategory.TWIN_SHARING,
        )
    )
    result = simulate(
        policy, make_bill(*CANONICAL, room=RoomCategory.DELUXE), room_category=RoomCategory.DELUXE
    )
    assert result.deduction_for(DeductionKind.PROPORTIONATE) == 0
    assert any("proportionately" in w for w in result.warnings)


# --- non-payables ---------------------------------------------------------


def test_non_medical_items_are_always_removed():
    result = simulate(
        make_policy(room_limit=RoomLimit()),
        make_bill((ExpenseHead.PHARMACY, 10000), (ExpenseHead.NON_MEDICAL, 2000)),
    )
    assert result.deduction_for(DeductionKind.NON_PAYABLE) == D(2000)
    assert result.payable_by_insurer == D(10000)


def test_consumables_are_excluded_by_default_and_covered_with_a_rider():
    lines = ((ExpenseHead.PHARMACY, 10000), (ExpenseHead.CONSUMABLES, 8000))

    without = simulate(make_policy(room_limit=RoomLimit()), make_bill(*lines))
    assert without.payable_by_insurer == D(10000)

    with_rider = simulate(
        make_policy(room_limit=RoomLimit(), covers_consumables=True), make_bill(*lines)
    )
    assert with_rider.payable_by_insurer == D(18000)


# --- caps and shares ------------------------------------------------------


def test_per_head_sublimit_binds():
    policy = make_policy(
        room_limit=RoomLimit(),
        sublimits=[SubLimit(head=ExpenseHead.INVESTIGATIONS, amount=D(10000))],
    )
    result = simulate(
        policy,
        make_bill((ExpenseHead.INVESTIGATIONS, 25000), (ExpenseHead.PHARMACY, 5000)),
    )
    assert result.deduction_for(DeductionKind.SUBLIMIT) == D(15000)
    assert result.payable_by_insurer == D(15000)


def test_copay_applies_to_what_remains_admissible():
    """10% of 1,00,000 = 10,000."""
    policy = make_policy(room_limit=RoomLimit(), copay_pct=D(10))
    result = simulate(policy, make_bill((ExpenseHead.PHARMACY, 100000)))
    assert result.deduction_for(DeductionKind.COPAY) == D(10000)
    assert result.payable_by_insurer == D(90000)


def test_copay_is_taken_after_the_proportionate_reduction_not_before():
    """Order changes the answer, so it is pinned.

        after proportionate: 1,43,750
        less 10% co-pay:       14,375
        payable:             1,29,375
    """
    result = simulate(make_policy(copay_pct=D(10)), make_bill(*CANONICAL))
    assert result.payable_by_insurer == D(129375)
    assert result.reconciles()


def test_top_up_deductible():
    """A 3 lakh deductible on a 2 lakh bill pays nothing at all."""
    policy = make_policy(room_limit=RoomLimit(), deductible=D(300000))
    result = simulate(policy, make_bill((ExpenseHead.PHARMACY, 200000)))
    assert result.payable_by_insurer == 0
    assert result.out_of_pocket == D(200000)


def test_deductible_pays_only_the_excess():
    policy = make_policy(room_limit=RoomLimit(), deductible=D(100000))
    result = simulate(policy, make_bill((ExpenseHead.PHARMACY, 250000)))
    assert result.payable_by_insurer == D(150000)


def test_procedure_cap_binds():
    policy = make_policy(
        room_limit=RoomLimit(),
        sublimits=[SubLimit(procedure_code="P1", amount=D(40000))],
    )
    result = simulate(policy, make_bill((ExpenseHead.SURGEON_FEE, 90000)))
    assert result.deduction_for(DeductionKind.PROCEDURE_CAP) == D(50000)
    assert result.payable_by_insurer == D(40000)


# --- cover exhaustion -----------------------------------------------------


def test_payout_cannot_exceed_remaining_cover():
    policy = make_policy(room_limit=RoomLimit(), sum_insured=D(500000),
                         sum_insured_remaining=D(80000))
    result = simulate(policy, make_bill((ExpenseHead.PHARMACY, 200000)))
    assert result.payable_by_insurer == D(80000)
    assert result.out_of_pocket == D(120000)
    assert any("remaining cover" in w for w in result.warnings)


def test_exhausted_cover_pays_nothing():
    policy = make_policy(room_limit=RoomLimit(), sum_insured_remaining=D(0))
    result = simulate(policy, make_bill((ExpenseHead.PHARMACY, 50000)))
    assert result.payable_by_insurer == 0


# --- settlement mode ------------------------------------------------------


def test_non_network_requires_the_whole_bill_upfront():
    """The distinction that decides whether a family can use a hospital at all."""
    result = simulate(
        make_policy(room_limit=RoomLimit()),
        make_bill((ExpenseHead.PHARMACY, 200000)),
        is_network=False,
    )
    assert result.settlement_mode is SettlementMode.REIMBURSEMENT
    assert result.cash_to_arrange_upfront == D(200000)
    assert result.payable_by_insurer == D(200000)  # eventually reimbursed in full
    assert any("cashless network" in w for w in result.warnings)


def test_network_hospital_only_needs_the_shortfall():
    result = simulate(
        make_policy(room_limit=RoomLimit(), copay_pct=D(10)),
        make_bill((ExpenseHead.PHARMACY, 200000)),
        is_network=True,
    )
    assert result.settlement_mode is SettlementMode.CASHLESS
    assert result.cash_to_arrange_upfront == D(20000)


# --- invariants -----------------------------------------------------------


@pytest.mark.parametrize(
    "policy_kw",
    [
        {},
        {"copay_pct": D(20)},
        {"deductible": D(50000)},
        {"sum_insured_remaining": D(60000)},
        {"copay_pct": D(10), "deductible": D(25000), "sum_insured_remaining": D(90000)},
        {"deduction_regime": DeductionRegime.LEGACY},
        {"covers_consumables": True},
    ],
)
def test_every_combination_reconciles(policy_kw):
    """Deductions must exactly account for the gap, under any combination."""
    result = simulate(
        make_policy(**policy_kw),
        make_bill(*CANONICAL, (ExpenseHead.CONSUMABLES, 9000),
                  (ExpenseHead.NON_MEDICAL, 1750)),
    )
    assert result.reconciles(), [
        (s.kind.value, str(s.deducted)) for s in result.steps
    ]


def test_payout_is_never_negative_or_above_the_bill():
    result = simulate(
        make_policy(copay_pct=D(50), deductible=D(400000)),
        make_bill(*CANONICAL),
    )
    assert 0 <= result.payable_by_insurer <= result.gross_total
    assert result.out_of_pocket >= 0


def test_every_step_explains_itself_in_plain_language():
    result = simulate(make_policy(copay_pct=D(10)), make_bill(*CANONICAL))
    assert result.steps
    for step in result.steps:
        assert len(step.explanation) > 30
        assert step.deducted > 0
        # Written for a person, not an adjuster.
        assert "proportionate_deduction" not in step.explanation


def test_zero_deduction_steps_are_not_recorded():
    result = simulate(make_policy(room_limit=RoomLimit()),
                      make_bill((ExpenseHead.PHARMACY, 10000)))
    assert all(s.deducted > 0 for s in result.steps)


@pytest.mark.parametrize(
    ("ratio", "expected"),
    [(D("0.625"), "62.5%"), (D("0.5"), "50%"), (D("0.8333"), "83.3%")],
)
def test_ratio_formatting_keeps_the_half_percent(ratio, expected):
    # 5,000 against 8,000 is exactly 62.5%; printing 62% invites a user to
    # think the arithmetic is wrong.
    assert _format_ratio(ratio) == expected


# --- bill construction ----------------------------------------------------


def test_room_choice_moves_the_whole_bill_not_just_the_room():
    """The coupling that makes a room upgrade cost more than it appears to."""
    from app.pipeline.s6_simulate.bill import estimate_bill
    from datagen.hospitals import build_hospitals
    from datagen.procedures import build_procedures

    procedures = build_procedures()
    hospitals = build_hospitals(procedures)
    procedure = next(p for p in procedures if p.code == "CP-GSUR-003")
    hospital = next(
        h for h in hospitals
        if h.performs(procedure.code)
        and h.tariff_for(RoomCategory.GENERAL_WARD)
        and h.tariff_for(RoomCategory.SINGLE_PRIVATE)
    )

    ward = estimate_bill(hospital, procedure, RoomCategory.GENERAL_WARD)
    private = estimate_bill(hospital, procedure, RoomCategory.SINGLE_PRIVATE)

    assert private.total > ward.total
    # The surgeon costs more in a private room too, not only the bed.
    assert private.amount_for(ExpenseHead.SURGEON_FEE) > ward.amount_for(
        ExpenseHead.SURGEON_FEE
    )
    # Medicines do not.
    assert private.amount_for(ExpenseHead.PHARMACY) == ward.amount_for(
        ExpenseHead.PHARMACY
    )


def test_bill_lines_sum_to_the_stated_total():
    from app.pipeline.s6_simulate.bill import estimate_bill
    from datagen.hospitals import build_hospitals
    from datagen.procedures import build_procedures

    procedures = build_procedures()
    hospitals = build_hospitals(procedures)
    procedure = procedures[0]
    hospital = next(h for h in hospitals if h.performs(procedure.code))
    room = hospital.room_tariffs[0].category

    bill = estimate_bill(hospital, procedure, room)
    assert bill.total == sum(line.amount for line in bill.lines)
    assert bill.total > 0
