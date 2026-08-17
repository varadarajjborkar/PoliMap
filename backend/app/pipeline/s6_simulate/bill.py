"""Build the hospital bill that insurance is then applied to.

The bill is constructed from three things: the procedure's CGHS-anchored package
price, that hospital's cost index, and the room the patient actually occupies.
Room choice does not merely change the room line — it moves the whole bill, and
that coupling is what makes the room decision expensive in ways people do not
expect.

Length of stay is carried as a range rather than a point. Presenting a single
figure would claim precision the inputs do not support, and a family that plans
against one number and then overshoots it has been misled by the system rather
than helped by it.
"""

from __future__ import annotations

from decimal import Decimal

from app.schemas.hospital import Hospital
from app.schemas.money import round_inr
from app.schemas.policy import ExpenseHead, RoomCategory
from app.schemas.procedure import Procedure
from app.schemas.simulation import BillLine, EstimatedBill

# Heads whose cost tracks the room tier, and by how much relative to a private
# room. A general ward is cheaper to nurse; a suite comes with more attention.
ROOM_TIER_MULTIPLIER: dict[RoomCategory, float] = {
    RoomCategory.GENERAL_WARD: 0.80,
    RoomCategory.TWIN_SHARING: 0.90,
    RoomCategory.SINGLE_PRIVATE: 1.00,
    RoomCategory.DELUXE: 1.15,
    RoomCategory.SUITE: 1.35,
    RoomCategory.ICU: 1.00,
}

# Heads that scale with the room tier. Deliberately the same set the post-2024
# rules treat as room-linked: the reason proportionate deduction applies to
# these heads is that hospitals really do price them by room category.
TIER_SCALED_HEADS = frozenset({
    ExpenseHead.NURSING,
    ExpenseHead.DOCTOR_VISIT,
    ExpenseHead.SURGEON_FEE,
    ExpenseHead.ANAESTHETIST_FEE,
    ExpenseHead.OT_CHARGES,
})

NON_MEDICAL_PER_DAY = Decimal(350)
"""Registration, records, attendant meals and the like — never reimbursable."""


def estimate_bill(
    hospital: Hospital,
    procedure: Procedure,
    room_category: RoomCategory,
    *,
    los_days: float | None = None,
    icu_days: float | None = None,
) -> EstimatedBill:
    """Project what a hospital will charge for a procedure in a given room."""
    tariff = hospital.tariff_for(room_category)
    if tariff is None:
        raise ValueError(
            f"{hospital.name} does not offer {room_category.label}"
        )

    stay = float(los_days if los_days is not None else procedure.typical_los_days)
    icu = float(icu_days if icu_days is not None else procedure.typical_icu_days)
    ward_days = max(stay - icu, 0.0)

    package = procedure.package_price(
        nabh=hospital.quality.accreditation.is_nabh_tier,
        cost_index=hospital.cost_index,
    )
    split = procedure.cost_split.apply(package)
    multiplier = Decimal(str(ROOM_TIER_MULTIPLIER[room_category]))

    lines: list[BillLine] = []

    # Room and ICU are billed from the hospital's own tariff by nights stayed,
    # not from the package split, because that is how they are actually charged
    # and because the room rate is what the policy's cap is tested against.
    if ward_days > 0:
        lines.append(BillLine(
            head=ExpenseHead.ROOM_RENT,
            amount=round_inr(tariff.per_day * Decimal(str(ward_days))),
            note=f"{ward_days:g} nights at {room_category.label}",
        ))

    if icu > 0:
        icu_tariff = hospital.tariff_for(RoomCategory.ICU)
        icu_rate = icu_tariff.per_day if icu_tariff else tariff.per_day * Decimal(2)
        lines.append(BillLine(
            head=ExpenseHead.ICU_CHARGES,
            amount=round_inr(icu_rate * Decimal(str(icu))),
            note=f"{icu:g} days in intensive care",
        ))

    for head, amount in split.items():
        if head in (ExpenseHead.ROOM_RENT, ExpenseHead.ICU_CHARGES, ExpenseHead.NON_MEDICAL):
            continue
        value = amount * multiplier if head in TIER_SCALED_HEADS else amount
        if value <= 0:
            continue
        lines.append(BillLine(
            head=head,
            amount=round_inr(value),
            note="scales with room category" if head in TIER_SCALED_HEADS else "",
        ))

    lines.append(BillLine(
        head=ExpenseHead.NON_MEDICAL,
        amount=round_inr(NON_MEDICAL_PER_DAY * Decimal(str(max(stay, 1.0)))),
        note="registration, records and attendant charges",
    ))

    return EstimatedBill(
        hospital_id=hospital.hospital_id,
        procedure_code=procedure.code,
        room_category=room_category,
        los_days=stay,
        icu_days=icu,
        room_rate_per_day=tariff.per_day,
        lines=lines,
    )


def stay_range(procedure: Procedure) -> tuple[float, float]:
    """Plausible shortest and longest stay, from the procedure's variability."""
    typical = procedure.typical_los_days
    spread = procedure.los_variability
    low = max(typical * (1 - spread), 1.0 if not procedure.is_daycare else 0.5)
    high = typical * (1 + spread)
    return round(low, 1), round(high, 1)
