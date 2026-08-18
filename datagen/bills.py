"""Generate hospital final bills, with the mistakes real ones carry.

A bill checker cannot be trusted on the strength of a hand-written fixture. It
has to be measured, which means documents whose every line and every planted
fault is known in advance, so recall can be stated as a number: how many of the
faults it finds, and how much it invents.

The bills are built from the same tariffs and cost splits the estimator uses, so
a bill and an estimate for the same treatment at the same hospital are two views
of one arithmetic. That is the comparison a family actually makes at discharge,
and generating them from a common source is what makes the comparison mean
something rather than being two independent guesses.

Five faults are planted, each drawn from what Indian billing desks actually do:

  subsumed_item     a blade or a dressing billed on its own, though the
                    regulator places it inside the room or procedure charge
  duplicate_line    one line entered twice
  line_arithmetic   quantity times rate not equal to the amount charged
  total_mismatch    the printed total not equal to the lines above it
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from app.pipeline.s6_simulate.bill import estimate_bill
from app.schemas.hospital import Hospital
from app.schemas.money import ZERO, round_inr
from app.schemas.policy import ExpenseHead, RoomCategory
from app.schemas.procedure import Procedure

SEED = 20260101

PROBLEMS = (
    "subsumed_item",
    "duplicate_line",
    "line_arithmetic",
    "total_mismatch",
)

# Items the IRDAI list places inside another charge. Billed separately here on
# purpose, which is exactly what the checker has to notice.
SUBSUMED_ITEMS: tuple[tuple[str, Decimal], ...] = (
    ("Surgical Blade", Decimal(180)),
    ("Gauze", Decimal(320)),
    ("Shoe Cover", Decimal(120)),
    ("Sterillium 500ml", Decimal(450)),
    ("Thermometer", Decimal(200)),
    ("Admission Kit", Decimal(650)),
)

# How each head is itemised on a printed bill, and roughly in what proportions.
_ITEMISATION: dict[ExpenseHead, tuple[str, ...]] = {
    ExpenseHead.INVESTIGATIONS: (
        "CBC with ESR", "Serum Creatinine", "Liver Function Test",
        "Chest X-Ray PA View", "2D Echocardiography", "Troponin I",
        "Blood Sugar Fasting", "Urine Routine", "ECG",
    ),
    ExpenseHead.PHARMACY: (
        "Inj. Pantoprazole 40mg", "Tab. Atorvastatin 20mg", "IV Fluid NS 500ml",
        "Inj. Ceftriaxone 1g", "Tab. Clopidogrel 75mg", "Inj. Heparin 5000IU",
        "Tab. Paracetamol 650mg",
    ),
    ExpenseHead.CONSUMABLES: (
        "IV Cannula 18G", "Disposable Syringe 5ml", "Surgical Gloves",
        "Urinary Catheter", "Dressing Set",
    ),
    ExpenseHead.IMPLANTS: ("Drug Eluting Stent", "Bone Cement", "Titanium Screws"),
    # Every Indian hospital bill carries these, which is the point: they are
    # ordinary rather than planted, and the checker has to name them anyway.
    ExpenseHead.NON_MEDICAL: (
        "Registration Charges", "Medical Records Charges", "Service Charges",
        "Attendant Charges", "Telephone Charges", "Laundry Charges",
    ),
}

_SINGLE_LINE: dict[ExpenseHead, str] = {
    ExpenseHead.SURGEON_FEE: "Surgeon's Professional Fee",
    ExpenseHead.ANAESTHETIST_FEE: "Anaesthetist Fee",
    ExpenseHead.OT_CHARGES: "Operation Theatre Charges",
    ExpenseHead.BLOOD: "Blood Transfusion Charges",
    ExpenseHead.OXYGEN: "Oxygen Charges",
    ExpenseHead.PHYSIOTHERAPY: "Physiotherapy Sessions",
    ExpenseHead.AMBULANCE: "Ambulance Charges",
}

_SECTIONS: tuple[tuple[str, tuple[ExpenseHead, ...]], ...] = (
    ("ROOM AND NURSING", (ExpenseHead.ROOM_RENT, ExpenseHead.ICU_CHARGES,
                          ExpenseHead.NURSING)),
    ("PROFESSIONAL FEES", (ExpenseHead.DOCTOR_VISIT, ExpenseHead.SURGEON_FEE,
                           ExpenseHead.ANAESTHETIST_FEE)),
    ("OPERATION THEATRE", (ExpenseHead.OT_CHARGES, ExpenseHead.IMPLANTS)),
    ("INVESTIGATIONS", (ExpenseHead.INVESTIGATIONS,)),
    ("PHARMACY AND CONSUMABLES", (ExpenseHead.PHARMACY, ExpenseHead.CONSUMABLES,
                                  ExpenseHead.BLOOD, ExpenseHead.OXYGEN)),
    ("OTHER CHARGES", (ExpenseHead.PHYSIOTHERAPY, ExpenseHead.AMBULANCE,
                       ExpenseHead.NON_MEDICAL)),
)

_FIRST_NAMES = ("Anil", "Sunita", "Ravi", "Meena", "Prakash", "Lakshmi",
                "Vikram", "Deepa", "Suresh", "Kavita")
_LAST_NAMES = ("Sharma", "Reddy", "Nair", "Patil", "Iyer", "Gowda",
               "Chatterjee", "Menon", "Desai", "Rao")


@dataclass
class BillLineSpec:
    description: str
    amount: Decimal
    head: ExpenseHead | None
    qty: Decimal | None = None
    rate: Decimal | None = None
    planted: str = ""
    """Which fault this line embodies, empty where the line is honest."""


@dataclass
class BillSectionSpec:
    title: str
    lines: list[BillLineSpec] = field(default_factory=list)


@dataclass
class BillBlueprint:
    bill_id: str
    hospital_id: str
    hospital_name: str
    city: str
    patient_name: str
    bill_number: str
    uhid: str
    admitted: date
    discharged: date
    procedure_code: str
    procedure_name: str
    room_label: str
    room_category: RoomCategory
    room_rate: Decimal
    los_days: int
    icu_days: int
    sections: list[BillSectionSpec]
    discount: Decimal
    advance_paid: Decimal
    stated_gross: Decimal
    planted: list[str]

    @property
    def lines(self) -> list[BillLineSpec]:
        return [line for section in self.sections for line in section.lines]

    @property
    def line_total(self) -> Decimal:
        return round_inr(sum((line.amount for line in self.lines), ZERO))

    @property
    def net_payable(self) -> Decimal:
        return round_inr(self.stated_gross - self.discount - self.advance_paid)


def _split_amount(
    rng: random.Random, total: Decimal, parts: int
) -> list[Decimal]:
    """Break a head's total into line amounts that still sum to it exactly."""
    if parts <= 1 or total <= ZERO:
        return [round_inr(total)]
    weights = [rng.uniform(0.6, 1.6) for _ in range(parts)]
    scale = sum(weights)
    amounts = [round_inr(total * Decimal(str(w / scale))) for w in weights]
    drift = round_inr(total) - sum(amounts, ZERO)
    amounts[0] = round_inr(amounts[0] + drift)
    return [a for a in amounts if a > ZERO] or [round_inr(total)]


def _priced(
    description: str, head: ExpenseHead, total: Decimal, qty: int
) -> BillLineSpec:
    """A line that multiplies out exactly, the way a printed bill does.

    Deriving the rate from a rounded total instead left lines a rupee or two
    short of their own arithmetic, which is indistinguishable from the fault
    the checker is being measured on.
    """
    rate = round_inr(total / Decimal(qty))
    return BillLineSpec(
        description=description, amount=round_inr(rate * Decimal(qty)),
        head=head, qty=Decimal(qty), rate=rate,
    )


def _lines_for(
    rng: random.Random,
    head: ExpenseHead,
    total: Decimal,
    *,
    los_days: int,
    icu_days: int,
    room_rate: Decimal,
    room_label: str,
) -> list[BillLineSpec]:
    if total <= ZERO:
        return []

    if head is ExpenseHead.ROOM_RENT:
        return [_priced(f"Room Rent - {room_label}", head, total,
                        max(los_days - icu_days, 1))]
    if head is ExpenseHead.ICU_CHARGES:
        return [_priced("ICU Charges", head, total, max(icu_days, 1))]
    if head is ExpenseHead.NURSING:
        return [_priced("Nursing Charges", head, total, max(los_days, 1))]
    if head is ExpenseHead.DOCTOR_VISIT:
        return [_priced("Consultant Visit Charges", head, total, max(los_days, 1))]

    if head in _SINGLE_LINE:
        return [BillLineSpec(
            description=_SINGLE_LINE[head], amount=round_inr(total), head=head
        )]

    names = _ITEMISATION.get(head)
    if not names:
        return [BillLineSpec(description=head.label, amount=round_inr(total), head=head)]

    count = min(len(names), max(2, min(6, int(total // Decimal(2500)) or 2)))
    chosen = rng.sample(names, count)
    return [
        BillLineSpec(description=name, amount=amount, head=head)
        for name, amount in zip(chosen, _split_amount(rng, total, count), strict=False)
    ]


def make_blueprint(
    rng: random.Random,
    index: int,
    hospital: Hospital,
    procedure: Procedure,
    room: RoomCategory,
    *,
    faults: int = 2,
) -> BillBlueprint:
    """Build one bill for a real hospital, procedure and room."""
    estimate = estimate_bill(hospital, procedure, room)
    los_days = max(int(round(estimate.los_days)), 1)
    icu_days = int(round(estimate.icu_days))
    tariff = hospital.tariff_for(room)
    room_rate = tariff.per_day if tariff else ZERO

    by_head = estimate.by_head()
    sections: list[BillSectionSpec] = []
    for title, group in _SECTIONS:
        lines: list[BillLineSpec] = []
        for head in group:
            lines.extend(_lines_for(
                rng, head, by_head.get(head, ZERO),
                los_days=los_days, icu_days=icu_days,
                room_rate=room_rate, room_label=room.label,
            ))
        if lines:
            sections.append(BillSectionSpec(title=title, lines=lines))

    planted = sorted(rng.sample(PROBLEMS, faults)) if faults else []
    _plant(rng, sections, planted)

    discharged = date(2026, 8, 1) + timedelta(days=rng.randint(0, 200))
    admitted = discharged - timedelta(days=los_days)

    blueprint = BillBlueprint(
        bill_id=f"BILL{index:03d}",
        hospital_id=hospital.hospital_id,
        hospital_name=hospital.name,
        city=hospital.city,
        patient_name=f"{rng.choice(_FIRST_NAMES)} {rng.choice(_LAST_NAMES)}",
        bill_number=f"IP/{discharged.year}/{rng.randint(10000, 99999)}",
        uhid=f"UH{rng.randint(100000, 999999)}",
        admitted=admitted,
        discharged=discharged,
        procedure_code=procedure.code,
        procedure_name=procedure.name,
        room_label=room.label,
        room_category=room,
        room_rate=round_inr(room_rate),
        los_days=los_days,
        icu_days=icu_days,
        sections=sections,
        discount=ZERO,
        advance_paid=ZERO,
        stated_gross=ZERO,
        planted=planted,
    )

    blueprint.discount = (
        round_inr(blueprint.line_total * Decimal("0.02")) if rng.random() < 0.4 else ZERO
    )
    blueprint.advance_paid = (
        round_inr(Decimal(rng.randrange(10000, 60000, 5000)))
        if rng.random() < 0.5 else ZERO
    )
    blueprint.stated_gross = blueprint.line_total
    if "total_mismatch" in planted:
        # A printed total that does not match the lines above it. Small enough
        # to be missed by eye, which is the only reason it is worth checking.
        blueprint.stated_gross = round_inr(
            blueprint.line_total + Decimal(rng.randrange(500, 4000, 100))
        )
    return blueprint


def _plant(
    rng: random.Random, sections: list[BillSectionSpec], planted: list[str]
) -> None:
    """Introduce the faults this bill is supposed to carry."""
    if not sections:
        return

    if "subsumed_item" in planted:
        description, amount = rng.choice(SUBSUMED_ITEMS)
        target = sections[-1]
        target.lines.append(BillLineSpec(
            description=description, amount=amount, head=None,
            planted="subsumed_item",
        ))

    if "duplicate_line" in planted:
        section = rng.choice([s for s in sections if s.lines])
        original = rng.choice(section.lines)
        copy = BillLineSpec(
            description=original.description, amount=original.amount,
            head=original.head, qty=original.qty, rate=original.rate,
            planted="duplicate_line",
        )
        section.lines.insert(section.lines.index(original) + 1, copy)

    if "line_arithmetic" in planted:
        candidates = [
            line for section in sections for line in section.lines
            if line.qty and line.rate and line.qty > 1
        ]
        if candidates:
            line = rng.choice(candidates)
            line.qty = line.qty + 1
            line.planted = "line_arithmetic"
        else:
            planted.remove("line_arithmetic")


def blueprint_to_truth(bp: BillBlueprint) -> dict[str, Any]:
    """The exact answer for one bill, for the benchmark to score against."""
    return {
        "bill_id": bp.bill_id,
        "hospital_id": bp.hospital_id,
        "procedure_code": bp.procedure_code,
        "room_category": bp.room_category.value,
        "room_rate": str(bp.room_rate),
        "los_days": bp.los_days,
        "icu_days": bp.icu_days,
        "lines": [
            {
                "description": line.description,
                "amount": str(line.amount),
                "head": line.head.value if line.head else None,
                "qty": str(line.qty) if line.qty is not None else None,
                "rate": str(line.rate) if line.rate is not None else None,
                "planted": line.planted,
            }
            for line in bp.lines
        ],
        "line_total": str(bp.line_total),
        "stated_gross": str(bp.stated_gross),
        "discount": str(bp.discount),
        "advance_paid": str(bp.advance_paid),
        "net_payable": str(bp.net_payable),
        "planted": bp.planted,
    }


def make_blueprints(
    hospitals: list[Hospital], procedures: list[Procedure], count: int = 20
) -> list[BillBlueprint]:
    """A spread of bills across hospitals, treatments and room tiers."""
    rng = random.Random(SEED)
    by_code = {p.code: p for p in procedures}
    blueprints: list[BillBlueprint] = []

    usable = [h for h in hospitals if h.procedure_codes and h.room_tariffs]
    for index in range(count):
        hospital = usable[index % len(usable)]
        codes = [c for c in hospital.procedure_codes if c in by_code]
        if not codes:
            continue
        procedure = by_code[rng.choice(codes)]
        rooms = [
            t.category for t in hospital.room_tariffs
            if t.category is not RoomCategory.ICU
        ]
        room = rng.choice(rooms) if rooms else RoomCategory.GENERAL_WARD
        # A fifth of the corpus is clean, so precision can be measured as well
        # as recall: a checker that flags something on every bill is useless.
        faults = 0 if index % 5 == 0 else rng.randint(1, 3)
        blueprints.append(
            make_blueprint(rng, index + 1, hospital, procedure, room, faults=faults)
        )
    return blueprints
