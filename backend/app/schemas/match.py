"""Matching, ranking and graceful degradation contracts.

Two design commitments show up in these types.

First, **exclusions are data**. Every hospital that fails a filter records why.
Without that, the system cannot explain an empty result, cannot relax the right
constraint, and cannot tell a user "there are three cardiac hospitals nearby but
none are in your insurer's cashless network", which is far more useful than a
blank page.

Second, **ranking is multi-objective and honest about it**. Cheapest, nearest
and best-equipped are usually different hospitals. Rather than collapsing that
into one opaque score, the non-dominated set is computed first, then ordered by
a preference the user can see and change.
"""

from __future__ import annotations

from enum import IntEnum, StrEnum

from pydantic import BaseModel, Field, computed_field

from app.schemas.hospital import GeoPoint, Hospital
from app.schemas.money import Rupees
from app.schemas.phrasing import Phrase
from app.schemas.policy import RoomCategory
from app.schemas.procedure import Specialty, Urgency
from app.schemas.simulation import SimulationResult


class Preference(StrEnum):
    """How the user wants trade-offs resolved."""

    PROTECT_MONEY = "protect_money"
    BEST_CARE = "best_care"
    NEAREST = "nearest"
    BALANCED = "balanced"

    @property
    def label(self) -> str:
        return {
            Preference.PROTECT_MONEY: "Keep my costs down",
            Preference.BEST_CARE: "Best equipped hospital",
            Preference.NEAREST: "Get there fastest",
            Preference.BALANCED: "Balanced",
        }[self]

    @property
    def weights(self) -> dict[str, float]:
        """Weights over normalised objectives, all in 'higher is better' form."""
        return {
            Preference.PROTECT_MONEY: {
                "affordability": 0.55,
                "capability": 0.15,
                "proximity": 0.10,
                "cashless": 0.20,
            },
            Preference.BEST_CARE: {
                "affordability": 0.15,
                "capability": 0.55,
                "proximity": 0.10,
                "cashless": 0.20,
            },
            Preference.NEAREST: {
                "affordability": 0.15,
                "capability": 0.20,
                "proximity": 0.55,
                "cashless": 0.10,
            },
            Preference.BALANCED: {
                "affordability": 0.30,
                "capability": 0.30,
                "proximity": 0.20,
                "cashless": 0.20,
            },
        }[self]


class CareContext(BaseModel):
    """What the user needs, and the constraints around getting it."""

    procedure_code: str | None = None
    specialty: Specialty | None = None
    urgency: Urgency = Urgency.PLANNED
    origin: GeoPoint
    city: str = ""
    max_distance_km: float = Field(default=15.0, gt=0)
    preference: Preference = Preference.BALANCED
    preferred_room: RoomCategory | None = None
    require_cashless: bool = True
    require_bed_availability: bool = True
    insurer_id: str = ""

    patient_age: int | None = None
    """Age of the person being admitted, where the policy names more than one.

    A co-payment banded on age falls on one member of a household and not the
    rest, so which of them is being treated changes the bill."""


class ExclusionCause(StrEnum):
    TOO_FAR = "too_far"
    PROCEDURE_UNAVAILABLE = "procedure_unavailable"
    SPECIALTY_UNAVAILABLE = "specialty_unavailable"
    NOT_CASHLESS = "not_cashless"
    NO_BED_AVAILABLE = "no_bed_available"
    NO_ELIGIBLE_ROOM = "no_eligible_room"
    SCHEME_NOT_EMPANELLED = "scheme_not_empanelled"

    @property
    def label(self) -> str:
        return {
            ExclusionCause.TOO_FAR: "Outside your distance limit",
            ExclusionCause.PROCEDURE_UNAVAILABLE: "Does not perform this treatment",
            ExclusionCause.SPECIALTY_UNAVAILABLE: "Specialty not available",
            ExclusionCause.NOT_CASHLESS: "Not in your cashless network",
            ExclusionCause.NO_BED_AVAILABLE: "No beds free right now",
            ExclusionCause.NO_ELIGIBLE_ROOM: "No room in your eligible category",
            ExclusionCause.SCHEME_NOT_EMPANELLED: "Not empanelled for your scheme",
        }[self]


class Exclusion(BaseModel):
    """Why one hospital did not make the candidate set."""

    hospital_id: str
    hospital_name: str
    cause: ExclusionCause
    detail: str = ""


class RelaxationKind(IntEnum):
    """Constraint relaxations, in the order the ladder gives them up.

    Ordered by how much they cost the user. Distance is surrendered first
    because it is an inconvenience; leaving the cashless network is surrendered
    late because it converts a covered admission into one the family must fund
    upfront.
    """

    NONE = 0
    WIDER_RADIUS = 1
    ROOM_CATEGORY = 2
    BED_AVAILABILITY = 3
    NON_NETWORK = 4
    GOVERNMENT_SCHEME = 5

    @property
    def label(self) -> str:
        return {
            RelaxationKind.NONE: "All your requirements met",
            RelaxationKind.WIDER_RADIUS: "Searched further away",
            RelaxationKind.ROOM_CATEGORY: "Included other room types",
            RelaxationKind.BED_AVAILABILITY: "Included hospitals with no free bed now",
            RelaxationKind.NON_NETWORK: "Included hospitals outside your network",
            RelaxationKind.GOVERNMENT_SCHEME: "Included government scheme hospitals",
        }[self]


class Relaxation(BaseModel):
    """A constraint that was given up, and what it costs to have given it up."""

    kind: RelaxationKind
    description: str
    consequence: str
    """Stated plainly, e.g. "you would pay the full bill upfront and claim later"."""


class Objectives(BaseModel):
    """Normalised 0-1 objectives, all in 'higher is better' orientation.

    Normalising before comparison is what allows Pareto dominance to mean
    anything across units as different as rupees and kilometres.
    """

    affordability: float = Field(ge=0, le=1)
    capability: float = Field(ge=0, le=1)
    proximity: float = Field(ge=0, le=1)
    cashless: float = Field(ge=0, le=1)

    def dominates(self, other: Objectives) -> bool:
        """True when this option is at least as good on every objective and
        strictly better on one. The definition of a defensible option."""
        mine = self.as_tuple()
        theirs = other.as_tuple()
        return all(a >= b for a, b in zip(mine, theirs, strict=True)) and any(
            a > b for a, b in zip(mine, theirs, strict=True)
        )

    def as_tuple(self) -> tuple[float, ...]:
        return (self.affordability, self.capability, self.proximity, self.cashless)

    def score(self, weights: dict[str, float]) -> float:
        return round(
            sum(getattr(self, k) * w for k, w in weights.items()),
            6,
        )


class RankedOption(BaseModel):
    """One hospital-and-room recommendation, with its reasoning attached."""

    hospital: Hospital
    simulation: SimulationResult
    distance_km: float
    objectives: Objectives
    score: float
    rank: int = 0
    on_pareto_frontier: bool = False

    reasons: list[Phrase] = Field(default_factory=list)
    """Why this option is here."""
    tradeoffs: list[Phrase] = Field(default_factory=list)
    """What the user gives up by taking it."""
    counterfactual: Phrase | None = None
    """A concrete, costed alternative, e.g. moving down a room category."""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def out_of_pocket(self) -> Rupees:
        return self.simulation.out_of_pocket


class MatchResult(BaseModel):
    """The full outcome of a search, including how hard it was to find one."""

    options: list[RankedOption] = Field(default_factory=list)
    relaxations: list[Relaxation] = Field(default_factory=list)
    exclusions: list[Exclusion] = Field(default_factory=list)
    considered_count: int = 0
    context: CareContext | None = None
    message: Phrase | None = None
    """The headline sentence for the UI, tuned to how the search went."""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tier(self) -> int:
        """How far down the relaxation ladder the search had to go."""
        return max((r.kind.value for r in self.relaxations), default=0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_fully_satisfied(self) -> bool:
        return not self.relaxations and bool(self.options)

    def exclusion_summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for exc in self.exclusions:
            counts[exc.cause.value] = counts.get(exc.cause.value, 0) + 1
        return counts
