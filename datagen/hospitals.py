"""Hospital corpus generator.

The corpus is synthetic but not arbitrary. Every attribute is derived from a
small number of drivers that correlate the way they do in reality:

* size drives accreditation odds, specialty breadth and ICU depth;
* locality affluence and city cost index drive room tariffs;
* size and accreditation drive how many insurers bother to sign a cashless
  tie-up, which is why the largest hospitals are in everyone's network and small
  nursing homes are in almost nobody's.

That correlation structure is what makes the matching stage interesting. If
price, quality and network status were independent random draws there would be
no real trade-offs to reason about, and the ranking engine would have nothing to
say. Here, the cheap hospital genuinely tends to be the one outside your network
with no ICU, which is exactly the decision a family actually faces.

Generation is seeded, so the corpus is identical on every machine.
"""

from __future__ import annotations

import random
from decimal import Decimal

from app.schemas.hospital import (
    Accreditation,
    GeoPoint,
    GovernmentScheme,
    Hospital,
    HospitalType,
    QualitySignals,
    RoomTariff,
)
from app.schemas.money import round_inr
from app.schemas.policy import SELECTABLE_ROOMS, RoomCategory
from app.schemas.procedure import Procedure, Specialty
from datagen.geo import CITIES, HOSPITAL_COUNTS, City, Locality
from datagen.insurers import NETWORK_REACH

SEED = 20260817

# Invented name components, combined so collisions with real institutions are
# unlikely. Deduplicated at build time.
NAME_ROOTS = [
    "Aarogya", "Amrit", "Anantha", "Chetana", "Dhruva", "Ekaant", "Harita",
    "Ishaan", "Jeevan", "Kalpa", "Lakshya", "Maitri", "Navya", "Ojas",
    "Prerna", "Rachana", "Sadhana", "Tejas", "Udaya", "Vaibhav", "Yashas",
    "Nabha", "Samvid", "Trilok", "Urja", "Vistaar", "Shanti", "Prakash",
    "Suraksh", "Nandana", "Girija", "Vasudha", "Anvi", "Rithvik", "Saanvi",
    "Kaveri", "Tungabhadra", "Sharada", "Mandara", "Neelkanth", "Arjuna",
    "Bodhi", "Chandana", "Deepashree", "Gokula", "Hridaya", "Indira Vihar",
    "Kalyani", "Madhuvan", "Nirvana",
]

LARGE_SUFFIXES = [
    "Institute of Medical Sciences",
    "Super Speciality Hospital",
    "Multispeciality Hospital",
    "Medical College and Hospital",
    "Healthcare Institute",
]
MID_SUFFIXES = [
    "Hospital",
    "Speciality Hospital",
    "Medical Centre",
    "Healthcare",
    "Hospital and Research Centre",
]
SMALL_SUFFIXES = [
    "Nursing Home",
    "Clinic and Nursing Home",
    "Maternity and Nursing Home",
    "Polyclinic",
    "Medical Centre",
]

CORE_SPECIALTIES = [
    Specialty.GENERAL_MEDICINE,
    Specialty.GENERAL_SURGERY,
    Specialty.OBSTETRICS_GYNAECOLOGY,
    Specialty.PAEDIATRICS,
    Specialty.ORTHOPAEDICS,
]
ADVANCED_SPECIALTIES = [
    Specialty.CARDIOLOGY,
    Specialty.NEUROLOGY,
    Specialty.NEPHROLOGY,
    Specialty.GASTROENTEROLOGY,
    Specialty.PULMONOLOGY,
    Specialty.UROLOGY,
    Specialty.ONCOLOGY,
    Specialty.ENT,
    Specialty.OPHTHALMOLOGY,
    Specialty.DERMATOLOGY,
    Specialty.ENDOCRINOLOGY,
    Specialty.PSYCHIATRY,
    Specialty.EMERGENCY,
]
TERTIARY_SPECIALTIES = [
    Specialty.CARDIOTHORACIC_SURGERY,
    Specialty.NEUROSURGERY,
    Specialty.PLASTIC_SURGERY,
]

# Base room rates for a mid-tier private hospital at cost index 1.0, before
# locality and accreditation adjustment.
BASE_ROOM_RATES: dict[RoomCategory, int] = {
    RoomCategory.GENERAL_WARD: 1800,
    RoomCategory.TWIN_SHARING: 3500,
    RoomCategory.SINGLE_PRIVATE: 6500,
    RoomCategory.DELUXE: 11000,
    RoomCategory.SUITE: 19000,
    RoomCategory.ICU: 14000,
}


class SizeTier:
    SMALL = "small"
    MID = "mid"
    LARGE = "large"


def _pick_size(rng: random.Random, hospital_type: HospitalType) -> str:
    if hospital_type is HospitalType.GOVERNMENT:
        return rng.choices([SizeTier.MID, SizeTier.LARGE], weights=[0.45, 0.55])[0]
    if hospital_type is HospitalType.ESI:
        return SizeTier.MID
    return rng.choices(
        [SizeTier.SMALL, SizeTier.MID, SizeTier.LARGE], weights=[0.46, 0.38, 0.16]
    )[0]


def _pick_accreditation(
    rng: random.Random, size: str, affluence: float, hospital_type: HospitalType
) -> Accreditation:
    """Larger, better-funded private hospitals are far likelier to be accredited."""
    if hospital_type in (HospitalType.GOVERNMENT, HospitalType.ESI):
        # Public hospitals are accredited less often, and rarely at the top tier.
        return rng.choices(
            [Accreditation.NONE, Accreditation.NABH_ENTRY, Accreditation.NABH_FULL],
            weights=[0.55, 0.30, 0.15],
        )[0]

    score = {SizeTier.SMALL: 0.15, SizeTier.MID: 0.5, SizeTier.LARGE: 0.9}[size]
    score = score * 0.7 + affluence * 0.3
    if score > 0.78:
        return rng.choices(
            [Accreditation.NABH_FULL, Accreditation.JCI, Accreditation.NABH_ENTRY],
            weights=[0.62, 0.18, 0.20],
        )[0]
    if score > 0.5:
        return rng.choices(
            [Accreditation.NABH_FULL, Accreditation.NABH_ENTRY, Accreditation.NONE],
            weights=[0.35, 0.45, 0.20],
        )[0]
    return rng.choices(
        [Accreditation.NONE, Accreditation.NABH_ENTRY], weights=[0.72, 0.28]
    )[0]


def _bed_count(rng: random.Random, size: str) -> int:
    return {
        SizeTier.SMALL: rng.randint(18, 75),
        SizeTier.MID: rng.randint(80, 260),
        SizeTier.LARGE: rng.randint(280, 850),
    }[size]


def _pick_specialties(rng: random.Random, size: str) -> list[Specialty]:
    if size == SizeTier.SMALL:
        chosen = rng.sample(CORE_SPECIALTIES, k=rng.randint(2, 4))
        if rng.random() < 0.35:
            chosen.append(rng.choice(ADVANCED_SPECIALTIES))
    elif size == SizeTier.MID:
        chosen = list(CORE_SPECIALTIES)
        chosen += rng.sample(ADVANCED_SPECIALTIES, k=rng.randint(3, 7))
        if rng.random() < 0.25:
            chosen.append(rng.choice(TERTIARY_SPECIALTIES))
    else:
        chosen = list(CORE_SPECIALTIES)
        chosen += rng.sample(ADVANCED_SPECIALTIES, k=rng.randint(8, len(ADVANCED_SPECIALTIES)))
        chosen += rng.sample(TERTIARY_SPECIALTIES, k=rng.randint(1, 3))
    return sorted(set(chosen), key=lambda s: s.value)


def _room_tariffs(
    rng: random.Random,
    size: str,
    affluence: float,
    cost_index: float,
    accreditation: Accreditation,
    hospital_type: HospitalType,
    bed_count: int,
) -> list[RoomTariff]:
    """Price rooms, then decide which categories this hospital even offers."""
    if hospital_type in (HospitalType.GOVERNMENT, HospitalType.ESI):
        # Public hospitals charge a fraction of private rates and mostly offer
        # wards. This is the affordability escape hatch the ranking relies on.
        multiplier = 0.22
        offered = [RoomCategory.GENERAL_WARD, RoomCategory.TWIN_SHARING, RoomCategory.ICU]
        if size == SizeTier.LARGE and rng.random() < 0.5:
            offered.append(RoomCategory.SINGLE_PRIVATE)
    else:
        accreditation_bump = {
            Accreditation.NONE: 0.88,
            Accreditation.NABH_ENTRY: 1.0,
            Accreditation.NABH_FULL: 1.18,
            Accreditation.JCI: 1.45,
        }[accreditation]
        size_bump = {SizeTier.SMALL: 0.78, SizeTier.MID: 1.0, SizeTier.LARGE: 1.22}[size]
        multiplier = (
            accreditation_bump * size_bump * (0.75 + 0.5 * affluence)
            * rng.uniform(0.93, 1.07)
        )
        offered = [RoomCategory.GENERAL_WARD, RoomCategory.TWIN_SHARING, RoomCategory.ICU]
        if size != SizeTier.SMALL or rng.random() < 0.6:
            offered.append(RoomCategory.SINGLE_PRIVATE)
        if size in (SizeTier.MID, SizeTier.LARGE) and rng.random() < 0.65:
            offered.append(RoomCategory.DELUXE)
        if size == SizeTier.LARGE and rng.random() < 0.55:
            offered.append(RoomCategory.SUITE)

    tariffs: list[RoomTariff] = []
    for category in [*SELECTABLE_ROOMS, RoomCategory.ICU]:
        if category not in offered:
            continue
        rate = Decimal(BASE_ROOM_RATES[category]) * Decimal(
            str(round(multiplier * cost_index, 4))
        )
        share = {
            RoomCategory.GENERAL_WARD: 0.34,
            RoomCategory.TWIN_SHARING: 0.26,
            RoomCategory.SINGLE_PRIVATE: 0.18,
            RoomCategory.DELUXE: 0.07,
            RoomCategory.SUITE: 0.03,
            RoomCategory.ICU: 0.12,
        }[category]
        beds_total = max(2, int(bed_count * share))
        # Occupancy is high in Indian hospitals; free beds are genuinely scarce
        # and that scarcity is a real constraint on where a patient can go.
        beds_available = max(0, int(beds_total * rng.uniform(0.0, 0.32)))
        tariffs.append(
            RoomTariff(
                category=category,
                per_day=round_inr(rate),
                beds_total=beds_total,
                beds_available=beds_available,
            )
        )
    return tariffs


def _cashless_network(
    rng: random.Random, size: str, accreditation: Accreditation, hospital_type: HospitalType
) -> list[str]:
    """Which insurers have a cashless tie-up here.

    Desirability rises with size and accreditation, so the biggest hospitals
    appear in nearly every network while small nursing homes appear in few.
    """
    if hospital_type in (HospitalType.GOVERNMENT, HospitalType.ESI):
        # Public hospitals settle through schemes, not commercial cashless desks.
        if rng.random() < 0.25:
            return [
                iid for iid in NETWORK_REACH if rng.random() < 0.15
            ]
        return []

    desirability = {SizeTier.SMALL: 0.30, SizeTier.MID: 0.70, SizeTier.LARGE: 1.0}[size]
    desirability *= {
        Accreditation.NONE: 0.6,
        Accreditation.NABH_ENTRY: 0.85,
        Accreditation.NABH_FULL: 1.0,
        Accreditation.JCI: 1.05,
    }[accreditation]

    return [
        insurer_id
        for insurer_id, reach in NETWORK_REACH.items()
        if rng.random() < min(reach * desirability, 0.97)
    ]


def _empanelled_schemes(
    rng: random.Random, city: City, size: str, hospital_type: HospitalType
) -> list[GovernmentScheme]:
    available = [GovernmentScheme(s) for s in city.schemes]
    if hospital_type in (HospitalType.GOVERNMENT, HospitalType.ESI):
        # Public facilities are empanelled for essentially everything going.
        return [
            s
            for s in available
            if s is not GovernmentScheme.ESI or hospital_type is HospitalType.ESI
        ]
    chance = {SizeTier.SMALL: 0.18, SizeTier.MID: 0.40, SizeTier.LARGE: 0.62}[size]
    return [s for s in available if rng.random() < chance]


def _procedure_codes(
    rng: random.Random, specialties: list[Specialty], size: str, procedures: list[Procedure]
) -> list[str]:
    """Procedures offered, restricted to this hospital's specialties.

    Smaller hospitals offer only part of what their specialty nominally covers,
    which is what makes "no hospital near you does this procedure" a real
    outcome the relaxation ladder has to handle.
    """
    coverage = {SizeTier.SMALL: 0.45, SizeTier.MID: 0.75, SizeTier.LARGE: 0.95}[size]
    specialty_set = set(specialties)
    return [
        p.code
        for p in procedures
        if p.specialty in specialty_set and rng.random() < coverage
    ]


def build_hospitals(procedures: list[Procedure]) -> list[Hospital]:
    rng = random.Random(SEED)
    hospitals: list[Hospital] = []
    used_names: set[str] = set()
    counter = 0

    for city in CITIES:
        target = HOSPITAL_COUNTS[city.name]
        for _ in range(target):
            counter += 1
            locality: Locality = rng.choices(
                city.localities,
                weights=[0.5 + loc.affluence for loc in city.localities],
            )[0]

            hospital_type = rng.choices(
                [
                    HospitalType.PRIVATE,
                    HospitalType.GOVERNMENT,
                    HospitalType.TRUST,
                    HospitalType.ESI,
                ],
                weights=[0.70, 0.15, 0.10, 0.05],
            )[0]

            size = _pick_size(rng, hospital_type)
            accreditation = _pick_accreditation(rng, size, locality.affluence, hospital_type)
            bed_count = _bed_count(rng, size)
            specialties = _pick_specialties(rng, size)

            name = _make_name(rng, size, locality, hospital_type, used_names)
            used_names.add(name)

            icu_share = {SizeTier.SMALL: 0.05, SizeTier.MID: 0.10, SizeTier.LARGE: 0.14}[size]
            icu_beds = max(0, int(bed_count * icu_share * rng.uniform(0.7, 1.3)))

            # Jitter the coordinate so hospitals in one locality are not stacked
            # on a single point; roughly +/- 1.5 km.
            lat = locality.lat + rng.uniform(-0.013, 0.013)
            lon = locality.lon + rng.uniform(-0.013, 0.013)

            hospitals.append(
                Hospital(
                    hospital_id=f"H{counter:05d}",
                    name=name,
                    hospital_type=hospital_type,
                    location=GeoPoint(lat=round(lat, 6), lon=round(lon, 6)),
                    locality=locality.name,
                    city=city.name,
                    state=city.state,
                    pincode=f"{city.pincode_prefix}{rng.randint(1, 110):03d}",
                    phone=f"{city.phone_std}-{rng.randint(2, 4)}{rng.randint(1000000, 9999999)}",
                    specialties=[s.value for s in specialties],
                    procedure_codes=_procedure_codes(rng, specialties, size, procedures),
                    room_tariffs=_room_tariffs(
                        rng, size, locality.affluence, city.cost_index,
                        accreditation, hospital_type, bed_count,
                    ),
                    quality=QualitySignals(
                        accreditation=accreditation,
                        bed_count=bed_count,
                        icu_beds=icu_beds,
                        specialty_count=len(specialties),
                        doctor_count=int(bed_count * rng.uniform(0.35, 0.75)),
                        has_emergency=size != SizeTier.SMALL or rng.random() < 0.4,
                        has_blood_bank=size == SizeTier.LARGE or rng.random() < 0.25,
                        established_year=rng.randint(1955, 2021),
                    ),
                    cost_index=round(
                        city.cost_index
                        * (0.80 + 0.42 * locality.affluence)
                        * {
                            Accreditation.NONE: 0.90,
                            Accreditation.NABH_ENTRY: 1.0,
                            Accreditation.NABH_FULL: 1.14,
                            Accreditation.JCI: 1.38,
                        }[accreditation]
                        * (0.30 if hospital_type in (HospitalType.GOVERNMENT, HospitalType.ESI) else 1.0)
                        * rng.uniform(0.95, 1.05),
                        4,
                    ),
                    cashless_insurers=_cashless_network(rng, size, accreditation, hospital_type),
                    empanelled_schemes=_empanelled_schemes(rng, city, size, hospital_type),
                )
            )

    return hospitals


def _make_name(
    rng: random.Random,
    size: str,
    locality: Locality,
    hospital_type: HospitalType,
    used: set[str],
) -> str:
    suffixes = {
        SizeTier.SMALL: SMALL_SUFFIXES,
        SizeTier.MID: MID_SUFFIXES,
        SizeTier.LARGE: LARGE_SUFFIXES,
    }[size]

    for _ in range(60):
        if hospital_type is HospitalType.GOVERNMENT:
            name = rng.choice(
                [
                    f"{locality.name} Government Hospital",
                    f"{locality.name} General Hospital",
                    f"District Hospital, {locality.name}",
                    f"{rng.choice(NAME_ROOTS)} Government {rng.choice(['Hospital', 'Medical College and Hospital'])}",
                ]
            )
        elif hospital_type is HospitalType.ESI:
            name = f"ESI Hospital, {locality.name}"
        elif hospital_type is HospitalType.TRUST:
            name = f"{rng.choice(NAME_ROOTS)} Charitable {rng.choice(['Hospital', 'Medical Centre'])}"
        elif rng.random() < 0.22:
            name = f"{locality.name} {rng.choice(suffixes)}"
        else:
            name = f"{rng.choice(NAME_ROOTS)} {rng.choice(suffixes)}"

        if name not in used:
            return name

    return f"{rng.choice(NAME_ROOTS)} {rng.choice(suffixes)} ({locality.name})"
