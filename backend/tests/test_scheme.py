"""Government schemes settle on package rates, not against a bill.

Every test here exists because running the indemnity waterfall over a scheme
beneficiary produced advice that was not merely wrong but inverted, and aimed at
the poorest users this system has: that consumables were theirs to pay, and that
they should raise the full bill in cash and claim it back afterwards.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.pipeline.s6_simulate.bill import estimate_bill
from app.pipeline.s6_simulate.estimate import estimate_for
from app.pipeline.s6_simulate.scheme_settle import package_price, settle_under_scheme
from app.schemas.hospital import (
    Accreditation,
    GeoPoint,
    GovernmentScheme,
    Hospital,
    HospitalType,
    QualitySignals,
    RoomTariff,
)
from app.schemas.money import ZERO
from app.schemas.policy import (
    ExpenseHead,
    NormalizedPolicy,
    RoomCategory,
    RoomLimit,
    RoomLimitBasis,
)
from app.schemas.procedure import CostSplit, Procedure, Specialty
from app.schemas.scheme import rules_for
from app.schemas.simulation import DeductionKind, SettlementMode


def make_hospital(*, schemes: list[GovernmentScheme]) -> Hospital:
    return Hospital(
        hospital_id="H00001",
        name="Test General Hospital",
        hospital_type=HospitalType.PRIVATE,
        locality="Indiranagar",
        city="Bengaluru",
        state="Karnataka",
        pincode="560038",
        location=GeoPoint(lat=12.97, lon=77.64),
        quality=QualitySignals(
            accreditation=Accreditation.NONE,
            bed_count=200,
            icu_beds=20,
            specialty_count=8,
            doctor_count=90,
        ),
        cost_index=1.0,
        room_tariffs=[
            RoomTariff(category=RoomCategory.GENERAL_WARD, per_day=Decimal("1200"),
                       beds_total=40, beds_available=6),
            RoomTariff(category=RoomCategory.SINGLE_PRIVATE, per_day=Decimal("6000"),
                       beds_total=20, beds_available=4),
            RoomTariff(category=RoomCategory.ICU, per_day=Decimal("9000"),
                       beds_total=20, beds_available=3),
        ],
        specialties=[Specialty.CARDIOLOGY.value],
        procedure_codes=["CP-TEST-001"],
        empanelled_schemes=schemes,
    )


def make_procedure() -> Procedure:
    return Procedure(
        code="CP-TEST-001",
        name="Test procedure with stent",
        specialty=Specialty.CARDIOLOGY,
        base_rate_non_nabh=Decimal("150000"),
        base_rate_nabh=Decimal("180000"),
        typical_los_days=4.0,
        typical_icu_days=1.0,
        requires_implant=True,
        cost_split=CostSplit(fractions={
            ExpenseHead.ROOM_RENT: 0.10,
            ExpenseHead.SURGEON_FEE: 0.25,
            ExpenseHead.OT_CHARGES: 0.10,
            ExpenseHead.NURSING: 0.05,
            ExpenseHead.IMPLANTS: 0.30,
            ExpenseHead.PHARMACY: 0.10,
            ExpenseHead.CONSUMABLES: 0.05,
            ExpenseHead.INVESTIGATIONS: 0.05,
        }),
    )


def scheme_policy(scheme: GovernmentScheme = GovernmentScheme.PMJAY) -> NormalizedPolicy:
    rules = rules_for(scheme)
    assert rules is not None
    return NormalizedPolicy(
        sum_insured=rules.cover_per_year,
        government_scheme=scheme.value,
        covers_consumables=True,
        copay_pct=rules.copay_pct,
        room_limit=RoomLimit(
            basis=RoomLimitBasis.CATEGORY_ONLY,
            category_ceiling=rules.room_entitlement,
        ),
    )


# --- the empanelled case ----------------------------------------------------


def test_an_empanelled_hospital_costs_the_family_nothing():
    hospital = make_hospital(schemes=[GovernmentScheme.PMJAY])
    procedure = make_procedure()
    policy = scheme_policy()

    result = estimate_for(
        policy, hospital, procedure, RoomCategory.GENERAL_WARD, with_band=False
    )

    assert result.out_of_pocket == ZERO
    assert result.cash_to_arrange_upfront == ZERO
    assert result.settlement_mode is SettlementMode.SCHEME_PACKAGE


def test_the_family_is_never_told_to_pay_first_and_claim_later():
    """The single most harmful sentence this system could show a PM-JAY user."""
    hospital = make_hospital(schemes=[GovernmentScheme.PMJAY])
    result = estimate_for(
        scheme_policy(), hospital, make_procedure(),
        RoomCategory.GENERAL_WARD, is_network=False, with_band=False,
    )

    prose = " ".join(str(p) for p in result.warnings + result.notes).lower()
    assert "claim" not in prose or "nothing to claim" in prose
    assert "pay the full" not in prose


def test_consumables_are_not_declared_the_patients_problem():
    """They are inside the package. Saying otherwise inverts the truth."""
    hospital = make_hospital(schemes=[GovernmentScheme.PMJAY])
    result = estimate_for(
        scheme_policy(), hospital, make_procedure(),
        RoomCategory.GENERAL_WARD, with_band=False,
    )

    kinds = {step.kind for step in result.steps}
    assert DeductionKind.NON_PAYABLE not in kinds
    assert not any("gloves" in w.text.lower() for w in result.warnings)


def test_no_room_cap_and_so_no_proportionate_deduction():
    hospital = make_hospital(schemes=[GovernmentScheme.PMJAY])
    result = estimate_for(
        scheme_policy(), hospital, make_procedure(),
        RoomCategory.GENERAL_WARD, with_band=False,
    )

    kinds = {step.kind for step in result.steps}
    assert DeductionKind.ROOM_RENT_CAP not in kinds
    assert DeductionKind.PROPORTIONATE not in kinds
    assert DeductionKind.COPAY not in kinds


def test_a_room_above_the_ward_is_the_patients_choice_to_pay_for():
    """Charged as an upgrade, not modelled as a deduction across other heads."""
    hospital = make_hospital(schemes=[GovernmentScheme.PMJAY])
    result = estimate_for(
        scheme_policy(), hospital, make_procedure(),
        RoomCategory.SINGLE_PRIVATE, with_band=False,
    )

    assert result.out_of_pocket > 0
    assert any("upgrade" in w.text.lower() for w in result.warnings)
    # The treatment itself stays covered; only the room moved.
    assert result.payable_by_insurer > 0
    assert DeductionKind.PROPORTIONATE not in {s.kind for s in result.steps}


# --- the non-empanelled case ------------------------------------------------


def test_a_non_empanelled_hospital_says_so_and_sends_you_elsewhere():
    hospital = make_hospital(schemes=[GovernmentScheme.ESI])
    result = estimate_for(
        scheme_policy(), hospital, make_procedure(),
        RoomCategory.GENERAL_WARD, with_band=False,
    )

    assert result.payable_by_insurer == ZERO
    assert result.out_of_pocket == result.bill.total
    assert DeductionKind.SCHEME_NOT_EMPANELLED in {s.kind for s in result.steps}

    prose = " ".join(w.text for w in result.warnings).lower()
    assert "nothing to claim back later" in prose
    assert "empanelled" in prose


def test_cghs_may_reimburse_where_the_package_schemes_cannot():
    """The rules differ per scheme, so the advice has to differ with them."""
    hospital = make_hospital(schemes=[])
    result = estimate_for(
        scheme_policy(GovernmentScheme.CGHS), hospital, make_procedure(),
        RoomCategory.GENERAL_WARD, with_band=False,
    )

    prose = " ".join(w.text for w in result.warnings).lower()
    assert "only with approval beforehand" in prose


# --- package pricing --------------------------------------------------------


def test_the_package_rate_is_the_schemes_price_not_the_hospitals():
    hospital = make_hospital(schemes=[GovernmentScheme.PMJAY])
    procedure = make_procedure()
    rules = rules_for(GovernmentScheme.PMJAY)
    assert rules is not None

    hospital_bill = estimate_bill(hospital, procedure, RoomCategory.GENERAL_WARD)
    scheme_rate = package_price(rules, procedure, hospital)

    assert scheme_rate < hospital_bill.total
    assert scheme_rate == procedure.base_rate_non_nabh * rules.package_rate_factor


def test_cover_spent_earlier_in_the_year_is_honoured():
    """A family floater can have been spent by a relative's admission."""
    hospital = make_hospital(schemes=[GovernmentScheme.PMJAY])
    procedure = make_procedure()
    policy = scheme_policy()
    policy.sum_insured_remaining = Decimal("20000")

    bill = estimate_bill(hospital, procedure, RoomCategory.GENERAL_WARD)
    rules = rules_for(GovernmentScheme.PMJAY)
    assert rules is not None
    result = settle_under_scheme(policy, rules, bill, procedure, hospital)

    assert result.payable_by_insurer == Decimal("20000")
    assert result.out_of_pocket > 0
    assert any("is left" in w.text for w in result.warnings)


@pytest.mark.parametrize("scheme", list(GovernmentScheme))
def test_every_scheme_in_the_dropdown_has_settlement_rules(scheme):
    """A scheme offered but unmodelled falls back to the indemnity path, which
    is the exact failure this module was written to stop."""
    assert rules_for(scheme) is not None
