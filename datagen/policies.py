"""Synthetic policy generator.

Each policy is produced twice: once as a `NormalizedPolicy` holding the exact
truth, and once as document text laid out the way Indian insurers actually lay
policies out. Extraction is then scored field by field against the truth, which
is what turns "improve the pipeline" into a measurable claim rather than an
impression.

The variation is chosen adversarially, around the places extraction really
fails:

* the same limit expressed four different ways — a flat rupee figure, a
  percentage of sum insured, a percentage capped by a maximum, or a room
  category with no number at all;
* figures written as "Rs. 5,00,000", "INR 5,00,000/-", "Rupees Five Lakh" and
  "5.00 Lakhs" within one corpus;
* decoy numbers near the real ones — premium, GST, agent codes and UINs sit
  beside the sum insured and are easy to grab by mistake;
* a schedule that contradicts the wording, so precedence has to be applied;
* top-up plans, where a large deductible changes the answer completely.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from app.schemas.money import format_inr
from app.schemas.policy import (
    DeductionRegime,
    Exclusion,
    ExpenseHead,
    NormalizedPolicy,
    PolicyMeta,
    RoomCategory,
    RoomLimit,
    RoomLimitBasis,
    SubLimit,
    WaitingPeriod,
)
from datagen.insurers import PRIVATE_INSURERS

SEED = 771026

FIRST_NAMES = [
    "Ramesh", "Sunita", "Arjun", "Kavitha", "Prakash", "Meera", "Vikram",
    "Lakshmi", "Anil", "Deepa", "Suresh", "Radha", "Manoj", "Shalini",
    "Rajesh", "Anjali", "Girish", "Padma", "Naveen", "Bhavani", "Sanjay",
    "Rekha", "Harish", "Vidya", "Mahesh", "Sarita", "Kiran", "Latha",
]
LAST_NAMES = [
    "Iyer", "Sharma", "Reddy", "Nair", "Patel", "Rao", "Gowda", "Menon",
    "Desai", "Kulkarni", "Shetty", "Verma", "Bhat", "Joshi", "Pillai",
    "Chatterjee", "Naidu", "Hegde", "Kaur", "Mishra",
]

CITIES_FOR_ADDRESS = [
    ("Bengaluru", "Karnataka", "560"),
    ("Delhi", "Delhi", "110"),
    ("Mumbai", "Maharashtra", "400"),
    ("Hyderabad", "Telangana", "500"),
]

PLAN_NAMES = [
    "Arogya Shield", "Total Health Plus", "Secure Health", "Family Care Optima",
    "Health Advantage", "Vital Protect", "Complete Cover", "Prime Health",
    "Sampoorna Suraksha", "Health Elite",
]

STANDARD_EXCLUSIONS = [
    "Cosmetic or aesthetic treatment unless required for reconstruction following an accident.",
    "Dental treatment or surgery unless necessitated by an accidental injury.",
    "Expenses arising from war, invasion, or nuclear contamination.",
    "Treatment for obesity or weight control unless medically necessary and covered under the policy.",
    "Any expenses related to participation in hazardous or adventure sports.",
    "Treatment taken outside the geographical limits of India.",
    "Unproven treatments, experimental procedures, and off-label drug use.",
    "Self-inflicted injury, suicide, or attempted suicide.",
    "Expenses for spectacles, contact lenses, and hearing aids.",
    "Treatment for alcoholism, drug or substance abuse.",
]


# --- how a number is written on the page ----------------------------------


def write_amount(value: int, style: str) -> str:
    """Render a rupee figure in one of the forms insurers actually use."""
    if style == "rs_grouped":
        return f"Rs. {format_inr(value)[1:]}/-"
    if style == "inr_grouped":
        return f"INR {format_inr(value)[1:]}"
    if style == "symbol":
        return format_inr(value)
    if style == "lakh_decimal":
        # Only cover amounts get written in lakhs. No real schedule expresses a
        # daily room rate as "Rs. 0.08 Lakhs", so smaller figures fall back to
        # the grouped form the same document would use for them.
        if value < 100000:
            return f"Rs. {format_inr(value)[1:]}/-"
        return f"Rs. {value / 100000:.2f} Lakhs"
    if style == "words":
        return f"Rupees {_in_words(value)} Only"
    return format_inr(value)


_UNITS = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen",
]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def _under_hundred(n: int) -> str:
    if n < 20:
        return _UNITS[n]
    tens, unit = divmod(n, 10)
    return _TENS[tens] + (f" {_UNITS[unit]}" if unit else "")


def _in_words(value: int) -> str:
    """Indian numbering: crore, lakh, thousand."""
    parts: list[str] = []
    for divisor, label in ((10000000, "Crore"), (100000, "Lakh"), (1000, "Thousand")):
        count, value = divmod(value, divisor)
        if count:
            parts.append(f"{_under_hundred(count)} {label}")
    if value >= 100:
        hundreds, value = divmod(value, 100)
        parts.append(f"{_UNITS[hundreds]} Hundred")
    if value:
        parts.append(_under_hundred(value))
    return " ".join(parts) or "Zero"


# --- blueprint ------------------------------------------------------------


@dataclass
class PolicyBlueprint:
    """Every knob that varies between generated policies."""

    policy_id: str
    insurer_id: str
    insurer_name: str
    plan_name: str
    policy_type: str
    policyholder: str
    age: int
    address: str
    policy_number: str
    uin: str
    start_date: date
    end_date: date

    sum_insured: int
    room_basis: str
    """flat | pct | pct_with_max | category | none"""
    room_pct: float | None
    room_flat: int | None
    room_category: RoomCategory | None
    icu_basis: str
    icu_pct: float | None
    icu_flat: int | None

    copay_pct: int
    deductible: int
    sublimits: list[tuple[ExpenseHead | None, str | None, str, int]]
    """(head, procedure_code, label, amount)"""
    waiting_periods: list[tuple[int, str]]
    covers_consumables: bool
    restore_benefit: bool
    pre_hosp_days: int
    post_hosp_days: int
    exclusions: list[str]

    amount_style: str
    contradicts_wording: bool
    """When set, the wording states a different room limit than the schedule.
    Precedence must resolve it in the schedule's favour."""
    wording_room_flat: int | None

    premium: int
    gst: int
    agent_code: str
    is_top_up: bool = False
    notes: list[str] = field(default_factory=list)


def _room_limit_sentence(bp: PolicyBlueprint) -> str:
    """The schedule line for room rent, in the blueprint's chosen phrasing."""
    if bp.room_basis == "none":
        return "No sub-limit on room rent. Any room category permitted."
    if bp.room_basis == "flat":
        return f"{write_amount(bp.room_flat, bp.amount_style)} per day"
    if bp.room_basis == "pct":
        return f"{bp.room_pct:g}% of Sum Insured per day"
    if bp.room_basis == "pct_with_max":
        return (
            f"{bp.room_pct:g}% of Sum Insured per day, subject to a maximum of "
            f"{write_amount(bp.room_flat, bp.amount_style)} per day"
        )
    return f"{bp.room_category.label} entitlement. No monetary sub-limit."


def _icu_limit_sentence(bp: PolicyBlueprint) -> str:
    if bp.icu_basis == "none":
        return "Covered up to Sum Insured. No separate sub-limit."
    if bp.icu_basis == "flat":
        return f"{write_amount(bp.icu_flat, bp.amount_style)} per day"
    return f"{bp.icu_pct:g}% of Sum Insured per day"


def make_blueprints(count: int = 40) -> list[PolicyBlueprint]:
    rng = random.Random(SEED)
    blueprints: list[PolicyBlueprint] = []

    # Deliberately spread across every room-limit phrasing so the extractor is
    # never rewarded for learning one dominant format.
    room_bases = ["flat", "pct", "pct_with_max", "category", "none"]

    for i in range(count):
        insurer_id, insurer_name, _, _ = PRIVATE_INSURERS[i % len(PRIVATE_INSURERS)]
        sum_insured = rng.choice(
            [300000, 500000, 500000, 750000, 1000000, 1000000, 1500000, 2000000, 2500000]
        )
        room_basis = room_bases[i % len(room_bases)]
        is_top_up = i % 11 == 7
        is_senior = i % 9 == 4

        room_pct = rng.choice([1.0, 1.0, 1.5, 2.0]) if room_basis in ("pct", "pct_with_max") else None
        if room_basis == "flat":
            room_flat = rng.choice([3000, 4000, 5000, 6000, 8000, 10000])
        elif room_basis == "pct_with_max":
            # A maximum that actually bites, so the "lower of" rule is exercised.
            room_flat = rng.choice([4000, 5000, 6000, 7500])
        else:
            room_flat = None

        icu_basis = rng.choice(["pct", "flat", "none", "pct"])
        city, state, pin_prefix = rng.choice(CITIES_FOR_ADDRESS)
        start = date(2026, 1, 1) + timedelta(days=rng.randint(0, 300))
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)

        sublimits: list[tuple[ExpenseHead | None, str | None, str, int]] = []
        if rng.random() < 0.55:
            sublimits.append(
                (ExpenseHead.INVESTIGATIONS, None, "Diagnostics and investigations",
                 rng.choice([15000, 20000, 25000, 40000]))
            )
        if rng.random() < 0.35:
            sublimits.append(
                (ExpenseHead.AMBULANCE, None, "Road ambulance",
                 rng.choice([2000, 3000, 5000]))
            )
        if rng.random() < 0.40:
            sublimits.append(
                (None, "CP-OPHT-001", "Cataract surgery, per eye",
                 rng.choice([25000, 30000, 40000]))
            )
        if rng.random() < 0.30:
            sublimits.append(
                (None, "CP-ORTH-001", "Joint replacement",
                 rng.choice([150000, 200000, 250000]))
            )

        # The initial waiting period is universally 30 days in India, not 30
        # months. It is carried as one month internally and printed as "30 days",
        # which is how every real schedule words it.
        waiting = [(1, "all illnesses other than accidental injury")]
        waiting.append((rng.choice([24, 36, 48]), "pre-existing diseases"))
        if rng.random() < 0.6:
            waiting.append((24, "cataract, hernia, and joint replacement"))

        copay = 0
        if is_senior:
            copay = rng.choice([20, 25])
        elif rng.random() < 0.35:
            copay = rng.choice([10, 10, 20])

        blueprints.append(
            PolicyBlueprint(
                policy_id=f"POL{i + 1:03d}",
                insurer_id=insurer_id,
                insurer_name=insurer_name,
                plan_name=(
                    f"{rng.choice(PLAN_NAMES)} {'Top-Up' if is_top_up else ''}".strip()
                ),
                policy_type=(
                    "Top-Up / Super Top-Up" if is_top_up
                    else "Senior Citizen Individual" if is_senior
                    else rng.choice(["Individual", "Family Floater", "Family Floater",
                                     "Group Employee Health"])
                ),
                policyholder=f"{first} {last}",
                age=rng.randint(61, 74) if is_senior else rng.randint(24, 58),
                address=(
                    f"{rng.randint(1, 400)}, {rng.choice(['1st', '2nd', '3rd', '4th'])} Cross, "
                    f"{rng.choice(['Layout', 'Nagar', 'Colony', 'Extension'])}, "
                    f"{city} - {pin_prefix}{rng.randint(1, 99):03d}, {state}"
                ),
                policy_number=(
                    f"{insurer_name[:3].upper()}/{start.year}/"
                    f"{rng.choice(['HLT', 'MED', 'IND'])}/{rng.randint(1000000, 9999999)}"
                ),
                uin=(
                    f"{insurer_name[:3].upper()}HLIP{str(start.year)[2:]}"
                    f"{rng.randint(100, 999)}V0{rng.randint(10, 99)}2425"
                ),
                start_date=start,
                end_date=start + timedelta(days=364),
                sum_insured=sum_insured,
                room_basis=room_basis,
                room_pct=room_pct,
                room_flat=room_flat,
                room_category=(
                    rng.choice([RoomCategory.SINGLE_PRIVATE, RoomCategory.TWIN_SHARING])
                    if room_basis == "category" else None
                ),
                icu_basis=icu_basis,
                icu_pct=rng.choice([2.0, 2.0, 4.0]) if icu_basis == "pct" else None,
                icu_flat=rng.choice([8000, 10000, 15000]) if icu_basis == "flat" else None,
                copay_pct=copay,
                deductible=rng.choice([300000, 500000]) if is_top_up else 0,
                sublimits=sublimits,
                waiting_periods=waiting,
                covers_consumables=rng.random() < 0.25,
                restore_benefit=rng.random() < 0.45,
                pre_hosp_days=rng.choice([30, 30, 60]),
                post_hosp_days=rng.choice([60, 90, 90, 180]),
                exclusions=rng.sample(STANDARD_EXCLUSIONS, k=rng.randint(6, 9)),
                amount_style=rng.choice(
                    ["rs_grouped", "rs_grouped", "inr_grouped", "symbol", "lakh_decimal"]
                ),
                # Roughly one policy in five disagrees with itself, forcing the
                # precedence rule to be exercised on real documents. Only
                # applies where the schedule states a figure the wording can
                # contradict — a category-only or unlimited policy cannot.
                # Modulus 7 is coprime with the 5-length room_bases cycle, so
                # this selects across all bases rather than colliding with one.
                contradicts_wording=(
                    i % 7 == 3 and room_basis in ("flat", "pct", "pct_with_max")
                ),
                wording_room_flat=(
                    rng.choice([2000, 2500, 3000]) if i % 7 == 3 else None
                ),
                premium=int(sum_insured * rng.uniform(0.018, 0.042)),
                gst=0,
                agent_code=f"AG{rng.randint(100000, 999999)}",
                is_top_up=is_top_up,
            )
        )

    for bp in blueprints:
        bp.gst = int(bp.premium * 0.18)

    return blueprints


# --- ground truth ---------------------------------------------------------


def blueprint_to_truth(bp: PolicyBlueprint) -> NormalizedPolicy:
    """The exact answer the pipeline is expected to arrive at."""
    if bp.room_basis == "flat":
        room = RoomLimit(basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=Decimal(bp.room_flat))
    elif bp.room_basis == "pct":
        room = RoomLimit(
            basis=RoomLimitBasis.PCT_OF_SI_PER_DAY, pct_of_si=Decimal(str(bp.room_pct))
        )
    elif bp.room_basis == "pct_with_max":
        room = RoomLimit(
            basis=RoomLimitBasis.PCT_OF_SI_PER_DAY,
            pct_of_si=Decimal(str(bp.room_pct)),
            amount_per_day=Decimal(bp.room_flat),
        )
    elif bp.room_basis == "category":
        room = RoomLimit(basis=RoomLimitBasis.CATEGORY_ONLY, category_ceiling=bp.room_category)
    else:
        room = RoomLimit(basis=RoomLimitBasis.NO_LIMIT)

    if bp.icu_basis == "flat":
        icu = RoomLimit(basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=Decimal(bp.icu_flat))
    elif bp.icu_basis == "pct":
        icu = RoomLimit(
            basis=RoomLimitBasis.PCT_OF_SI_PER_DAY, pct_of_si=Decimal(str(bp.icu_pct))
        )
    else:
        icu = RoomLimit(basis=RoomLimitBasis.NO_LIMIT)

    return NormalizedPolicy(
        policy_id=bp.policy_id,
        meta=PolicyMeta(
            insurer_name=bp.insurer_name,
            plan_name=bp.plan_name,
            policy_number=bp.policy_number,
            policyholder_name=bp.policyholder,
            policy_type=bp.policy_type,
            start_date=bp.start_date,
            end_date=bp.end_date,
            uin=bp.uin,
        ),
        sum_insured=Decimal(bp.sum_insured),
        room_limit=room,
        icu_limit=icu,
        copay_pct=Decimal(bp.copay_pct),
        deductible=Decimal(bp.deductible),
        sublimits=[
            SubLimit(head=head, procedure_code=code, label=label, amount=Decimal(amount))
            for head, code, label, amount in bp.sublimits
        ],
        waiting_periods=[
            WaitingPeriod(months=months, applies_to=applies)
            for months, applies in bp.waiting_periods
        ],
        exclusions=[Exclusion(text=text) for text in bp.exclusions],
        covers_consumables=bp.covers_consumables,
        restore_benefit=bp.restore_benefit,
        pre_hospitalisation_days=bp.pre_hosp_days,
        post_hospitalisation_days=bp.post_hosp_days,
        deduction_regime=DeductionRegime.POST_2024,
        confidence=1.0,
    )
