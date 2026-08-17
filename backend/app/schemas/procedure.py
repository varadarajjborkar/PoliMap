"""Treatment package catalogue.

Costs are anchored to CGHS published package rates, which give a defensible,
government-sourced baseline with a real NABH / non-NABH split. A hospital's
actual price is derived from that baseline by its `cost_index`, rather than
being invented per hospital.

`CostSplit` is what makes proportionate deduction computable: the deduction
applies per expense head, so a package total is useless without knowing how it
divides across room, surgeon, implants and the rest.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from app.schemas.money import Rupees, round_inr
from app.schemas.policy import ExpenseHead


class Specialty(StrEnum):
    GENERAL_MEDICINE = "general_medicine"
    GENERAL_SURGERY = "general_surgery"
    CARDIOLOGY = "cardiology"
    CARDIOTHORACIC_SURGERY = "cardiothoracic_surgery"
    ORTHOPAEDICS = "orthopaedics"
    NEUROLOGY = "neurology"
    NEUROSURGERY = "neurosurgery"
    ONCOLOGY = "oncology"
    NEPHROLOGY = "nephrology"
    UROLOGY = "urology"
    GASTROENTEROLOGY = "gastroenterology"
    PULMONOLOGY = "pulmonology"
    OBSTETRICS_GYNAECOLOGY = "obstetrics_gynaecology"
    PAEDIATRICS = "paediatrics"
    OPHTHALMOLOGY = "ophthalmology"
    ENT = "ent"
    DERMATOLOGY = "dermatology"
    PSYCHIATRY = "psychiatry"
    ENDOCRINOLOGY = "endocrinology"
    PLASTIC_SURGERY = "plastic_surgery"
    EMERGENCY = "emergency"

    @property
    def label(self) -> str:
        return self.value.replace("_", " ").title()


class Urgency(StrEnum):
    EMERGENCY = "emergency"
    """Now. Distance dominates every other consideration."""
    URGENT = "urgent"
    """Within days."""
    PLANNED = "planned"
    """Elective; there is time to optimise cost and quality."""


class CostSplit(BaseModel):
    """How a package total divides across bill heads.

    Fractions must sum to 1. Validated on construction because a split that
    silently fails to sum turns every downstream rupee figure into nonsense.
    """

    fractions: dict[ExpenseHead, float]

    @model_validator(mode="after")
    def _must_sum_to_one(self) -> CostSplit:
        total = sum(self.fractions.values())
        if abs(total - 1.0) > 0.005:
            raise ValueError(f"cost split must sum to 1.0, got {total:.4f}")
        if any(v < 0 for v in self.fractions.values()):
            raise ValueError("cost split fractions must be non-negative")
        return self

    def apply(self, total: Decimal) -> dict[ExpenseHead, Decimal]:
        """Divide a package total into per-head amounts.

        Rounding residue is pushed onto the largest head so the parts always
        reconcile exactly against the whole — a bill whose lines do not add up
        destroys trust faster than a wrong estimate.
        """
        if not self.fractions:
            return {}
        amounts = {
            head: round_inr(total * Decimal(str(frac)))
            for head, frac in self.fractions.items()
        }
        residue = round_inr(total) - sum(amounts.values())
        if residue:
            largest = max(amounts, key=lambda h: amounts[h])
            amounts[largest] += residue
        return amounts


class Procedure(BaseModel):
    """One treatment package."""

    code: str
    name: str
    specialty: Specialty
    description: str = ""

    base_rate_non_nabh: Rupees
    base_rate_nabh: Rupees
    """CGHS-anchored package rates. NABH-accredited hospitals bill higher."""

    typical_los_days: float = Field(default=1.0, ge=0)
    """Typical length of stay, used to project room-rent exposure."""
    typical_icu_days: float = Field(default=0.0, ge=0)

    cost_split: CostSplit
    requires_implant: bool = False
    is_daycare: bool = False
    """Under 24 hours. Many policies cover only listed daycare procedures."""

    los_variability: float = Field(default=0.35, ge=0, le=2)
    """Relative spread of stay length, used to build the low/high cost band
    rather than presenting a single falsely precise number."""

    def base_rate(self, *, nabh: bool) -> Decimal:
        return self.base_rate_nabh if nabh else self.base_rate_non_nabh

    def package_price(self, *, nabh: bool, cost_index: float) -> Decimal:
        """Indicative price at a hospital with the given cost index."""
        return round_inr(self.base_rate(nabh=nabh) * Decimal(str(cost_index)))
