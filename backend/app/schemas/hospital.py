"""Hospital and care-provider representation.

A deliberate constraint runs through this module: nothing here claims anything
about clinical outcomes. `QualitySignals` holds only externally observable,
verifiable facts — accreditation status, bed counts, whether a specialty is
present. The problem statement forbids clinical recommendation, and a
"quality score" that implied outcome prediction would cross that line. What is
modelled instead is *capability and assurance*, and the UI says so.
"""

from __future__ import annotations

import math
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.money import Rupees
from app.schemas.policy import RoomCategory

EARTH_RADIUS_KM = 6371.0


class HospitalType(StrEnum):
    GOVERNMENT = "government"
    PRIVATE = "private"
    TRUST = "trust"
    """Charitable / not-for-profit."""
    ESI = "esi"
    """Employees' State Insurance hospital."""

    @property
    def label(self) -> str:
        return {
            HospitalType.GOVERNMENT: "Government",
            HospitalType.PRIVATE: "Private",
            HospitalType.TRUST: "Trust / not-for-profit",
            HospitalType.ESI: "ESI hospital",
        }[self]


class Accreditation(StrEnum):
    """Quality accreditation, which also drives tariff tiers in India.

    CGHS publishes separate NABH and non-NABH package rates, so accreditation is
    both a quality signal and a price signal.
    """

    NONE = "none"
    NABH_ENTRY = "nabh_entry"
    NABH_FULL = "nabh_full"
    JCI = "jci"

    @property
    def label(self) -> str:
        return {
            Accreditation.NONE: "Not accredited",
            Accreditation.NABH_ENTRY: "NABH entry-level",
            Accreditation.NABH_FULL: "NABH accredited",
            Accreditation.JCI: "JCI accredited",
        }[self]

    @property
    def is_nabh_tier(self) -> bool:
        """Whether CGHS NABH package rates apply."""
        return self in (Accreditation.NABH_FULL, Accreditation.JCI)


class GovernmentScheme(StrEnum):
    """Public schemes named in the problem statement, plus the central ones."""

    PMJAY = "pmjay"
    CGHS = "cghs"
    ESI = "esi"
    AROGYA_KARNATAKA = "arogya_karnataka"
    YESHASWINI = "yeshaswini"
    MJPJAY = "mjpjay"
    """Mahatma Jyotirao Phule Jan Arogya Yojana — Maharashtra."""
    AAROGYASRI = "aarogyasri"
    """Telangana / Andhra Pradesh."""
    DELHI_AAROGYA_KOSH = "delhi_aarogya_kosh"

    @property
    def label(self) -> str:
        return {
            GovernmentScheme.PMJAY: "Ayushman Bharat PM-JAY",
            GovernmentScheme.CGHS: "CGHS",
            GovernmentScheme.ESI: "ESI",
            GovernmentScheme.AROGYA_KARNATAKA: "Arogya Karnataka",
            GovernmentScheme.YESHASWINI: "Yeshaswini",
            GovernmentScheme.MJPJAY: "MJPJAY",
            GovernmentScheme.AAROGYASRI: "Aarogyasri",
            GovernmentScheme.DELHI_AAROGYA_KOSH: "Delhi Aarogya Kosh",
        }[self]


class GeoPoint(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)

    def distance_km(self, other: GeoPoint) -> float:
        """Great-circle distance. Adequate at city scale."""
        lat1, lon1, lat2, lon2 = map(
            math.radians, (self.lat, self.lon, other.lat, other.lon)
        )
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


class RoomTariff(BaseModel):
    """What one room category costs per day at one hospital."""

    category: RoomCategory
    per_day: Rupees
    beds_total: int = Field(default=0, ge=0)
    beds_available: int = Field(default=0, ge=0)

    @property
    def has_availability(self) -> bool:
        return self.beds_available > 0


class QualitySignals(BaseModel):
    """Observable assurance and capability indicators.

    Not a clinical outcome measure. Kept as separate components rather than one
    opaque number so the interface can show what drove a ranking.
    """

    accreditation: Accreditation = Accreditation.NONE
    bed_count: int = Field(default=0, ge=0)
    icu_beds: int = Field(default=0, ge=0)
    specialty_count: int = Field(default=0, ge=0)
    doctor_count: int = Field(default=0, ge=0)
    has_emergency: bool = False
    has_blood_bank: bool = False
    established_year: int | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def capability_score(self) -> float:
        """0-1 composite over the observable signals above.

        Weights are stated openly and the components stay visible, so a user can
        disagree with the weighting rather than be handed a verdict.
        """
        accreditation_points = {
            Accreditation.NONE: 0.0,
            Accreditation.NABH_ENTRY: 0.55,
            Accreditation.NABH_FULL: 0.85,
            Accreditation.JCI: 1.0,
        }[self.accreditation]

        # Saturating curves: past a point, more beds stop signalling more.
        size = min(self.bed_count / 500.0, 1.0)
        icu_depth = min(self.icu_beds / 60.0, 1.0)
        breadth = min(self.specialty_count / 20.0, 1.0)
        staffing = min(self.doctor_count / 200.0, 1.0)
        facilities = (0.5 if self.has_emergency else 0.0) + (
            0.5 if self.has_blood_bank else 0.0
        )

        return round(
            0.34 * accreditation_points
            + 0.18 * size
            + 0.16 * icu_depth
            + 0.14 * breadth
            + 0.10 * staffing
            + 0.08 * facilities,
            4,
        )


class Hospital(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    hospital_id: str
    name: str
    hospital_type: HospitalType
    location: GeoPoint
    locality: str
    city: str
    state: str
    pincode: str = ""
    phone: str = ""

    specialties: list[str] = Field(default_factory=list)
    procedure_codes: list[str] = Field(default_factory=list)
    """Procedures this hospital performs, by catalogue code."""

    room_tariffs: list[RoomTariff] = Field(default_factory=list)
    quality: QualitySignals = Field(default_factory=QualitySignals)

    cost_index: float = Field(default=1.0, gt=0)
    """Multiplier applied to CGHS base package rates to price this hospital.
    Captures city cost of living and positioning within that city."""

    cashless_insurers: list[str] = Field(default_factory=list)
    """Insurer ids with a cashless tie-up. Absence means reimbursement only —
    the patient pays upfront and claims later, which is a cash-flow problem
    even when the claim is eventually paid in full."""

    empanelled_schemes: list[GovernmentScheme] = Field(default_factory=list)

    def tariff_for(self, category: RoomCategory) -> RoomTariff | None:
        return next((t for t in self.room_tariffs if t.category is category), None)

    def available_rooms(self) -> list[RoomTariff]:
        return [t for t in self.room_tariffs if t.has_availability]

    def cheapest_room_within(self, ceiling: RoomCategory) -> RoomTariff | None:
        eligible = [
            t
            for t in self.room_tariffs
            if t.category.is_within(ceiling) and t.category is not RoomCategory.ICU
        ]
        return min(eligible, key=lambda t: t.per_day) if eligible else None

    def is_cashless_for(self, insurer_id: str) -> bool:
        return insurer_id in self.cashless_insurers

    def performs(self, procedure_code: str) -> bool:
        return procedure_code in self.procedure_codes

    def daily_room_rate(self, category: RoomCategory) -> Decimal | None:
        tariff = self.tariff_for(category)
        return tariff.per_day if tariff else None


class Insurer(BaseModel):
    insurer_id: str
    name: str
    short_name: str = ""
    is_government_scheme: bool = False
    network_size: int = 0
