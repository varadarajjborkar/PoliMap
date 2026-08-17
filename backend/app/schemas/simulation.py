"""Cost estimation contracts.

The output of a simulation is not a number, it is an *argument*: an itemised
bill, then an ordered chain of deductions, each naming the policy clause that
caused it and explaining itself in plain words. A user under stress should be
able to read down the chain and see exactly where their money went.

Every result carries an internal reconciliation check. A cost breakdown whose
lines do not sum to its own total is worse than no estimate at all, so the
invariant is asserted rather than assumed.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, computed_field

from app.schemas.money import Rupees, round_inr
from app.schemas.policy import ExpenseHead, RoomCategory


class BillLine(BaseModel):
    head: ExpenseHead
    amount: Rupees
    note: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def label(self) -> str:
        return self.head.label


class EstimatedBill(BaseModel):
    """What the hospital is expected to charge, before insurance is applied."""

    hospital_id: str
    procedure_code: str
    room_category: RoomCategory
    los_days: float = Field(ge=0)
    icu_days: float = Field(default=0.0, ge=0)
    room_rate_per_day: Rupees
    lines: list[BillLine] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total(self) -> Rupees:
        return round_inr(sum((line.amount for line in self.lines), Decimal(0)))

    def amount_for(self, head: ExpenseHead) -> Decimal:
        return round_inr(
            sum((line.amount for line in self.lines if line.head is head), Decimal(0))
        )

    def by_head(self) -> dict[ExpenseHead, Decimal]:
        totals: dict[ExpenseHead, Decimal] = {}
        for line in self.lines:
            totals[line.head] = totals.get(line.head, Decimal(0)) + line.amount
        return totals


class DeductionKind(StrEnum):
    """Why money came off. Ordered as the waterfall applies them."""

    NON_PAYABLE = "non_payable"
    """IRDAI non-medical items, gloves, gowns, admin fees."""
    EXCLUSION = "exclusion"
    """Named policy exclusion."""
    WAITING_PERIOD = "waiting_period"
    """Benefit not yet active."""
    SUBLIMIT = "sublimit"
    """Per-head cap exceeded."""
    ROOM_RENT_CAP = "room_rent_cap"
    """Room billed above the eligible daily rate."""
    PROPORTIONATE = "proportionate"
    """The knock-on deduction across room-linked heads."""
    PROCEDURE_CAP = "procedure_cap"
    COPAY = "copay"
    DEDUCTIBLE = "deductible"
    SUM_INSURED_EXHAUSTED = "sum_insured_exhausted"

    # Scheme settlement. A package rate is not a deduction in the indemnity
    # sense, but it is the same thing from the family's side: the gap between
    # what the hospital would charge and what actually has to be found.
    SCHEME_PACKAGE_RATE = "scheme_package_rate"
    """The hospital's price replaced by the scheme's fixed package rate."""
    SCHEME_NOT_EMPANELLED = "scheme_not_empanelled"
    """This hospital cannot accept the scheme, so it pays nothing here."""

    @property
    def label(self) -> str:
        return {
            DeductionKind.NON_PAYABLE: "Items your policy never covers",
            DeductionKind.EXCLUSION: "Excluded by your policy",
            DeductionKind.WAITING_PERIOD: "Still in waiting period",
            DeductionKind.SUBLIMIT: "Above a category limit",
            DeductionKind.ROOM_RENT_CAP: "Room costs more than you are covered for",
            DeductionKind.PROPORTIONATE: "Proportionate deduction",
            DeductionKind.PROCEDURE_CAP: "Above the limit for this treatment",
            DeductionKind.COPAY: "Your co-payment share",
            DeductionKind.DEDUCTIBLE: "Your deductible",
            DeductionKind.SUM_INSURED_EXHAUSTED: "Beyond your remaining cover",
            DeductionKind.SCHEME_PACKAGE_RATE: "Covered by the scheme package",
            DeductionKind.SCHEME_NOT_EMPANELLED: "This hospital does not accept your scheme",
        }[self]


class WaterfallStep(BaseModel):
    """One deduction, with its cause and its effect."""

    kind: DeductionKind
    deducted: Rupees
    payable_after: Rupees
    explanation: str
    """Plain language. Written for someone in a hospital corridor."""

    clause_ids: list[str] = Field(default_factory=list)
    affected_heads: list[ExpenseHead] = Field(default_factory=list)
    detail: dict[str, float | str] = Field(default_factory=dict)
    """Supporting figures, e.g. the proportionality ratio that was applied."""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def label(self) -> str:
        return self.kind.label


class CostBand(BaseModel):
    """Low / expected / high, with the reason the high figure is high.

    An earlier version of this varied only the length of stay. Once the insurer
    is paying for everything that scales with days, the only thing left moving
    was the flat non-medical charge, so every estimate on every card came out at
    the same few hundred rupees either side of centre. A range that never
    changes is not a confidence interval; it is decoration, and a reader who
    puts two cards side by side sees through it immediately.

    The high figure is now a named scenario rather than a spread: a longer stay,
    an extra day in intensive care, a second implant where the procedure uses
    one. That is what a family is actually bracing for, and `high_driver` says
    which of those it is so the number can be defended out loud.
    """

    low: Rupees
    expected: Rupees
    high: Rupees
    high_driver: str = ""
    """Plain-language cause of the high figure, e.g. "a second stent"."""


class SettlementMode(StrEnum):
    CASHLESS = "cashless"
    """Insurer settles with the hospital directly."""
    REIMBURSEMENT = "reimbursement"
    """Patient pays the full bill upfront and claims it back later."""
    SCHEME_PACKAGE = "scheme_package"
    """Government scheme pays the hospital a fixed package rate."""

    @property
    def label(self) -> str:
        return {
            SettlementMode.CASHLESS: "Cashless",
            SettlementMode.REIMBURSEMENT: "Pay first, claim later",
            SettlementMode.SCHEME_PACKAGE: "Scheme package",
        }[self]


class SimulationResult(BaseModel):
    """A complete, auditable cost estimate for one hospital and room choice."""

    hospital_id: str
    hospital_name: str = ""
    procedure_code: str
    room_category: RoomCategory

    bill: EstimatedBill
    steps: list[WaterfallStep] = Field(default_factory=list)

    payable_by_insurer: Rupees
    out_of_pocket: Rupees
    cash_to_arrange_upfront: Rupees
    """What the patient must physically produce at admission. Equals the full
    bill under reimbursement, which is the distinction that decides whether a
    family can use a hospital at all."""

    settlement_mode: SettlementMode
    band: CostBand | None = None
    warnings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def gross_total(self) -> Rupees:
        return self.bill.total

    @computed_field  # type: ignore[prop-decorator]
    @property
    def covered_fraction(self) -> float:
        total = self.bill.total
        return float(self.payable_by_insurer / total) if total else 0.0

    def reconciles(self) -> bool:
        """Deductions must exactly account for the gap between bill and payout."""
        deducted = sum((s.deducted for s in self.steps), Decimal(0))
        return round_inr(self.bill.total - deducted) == round_inr(
            self.payable_by_insurer
        ) and round_inr(self.out_of_pocket) == round_inr(
            self.bill.total - self.payable_by_insurer
        )

    def deduction_for(self, kind: DeductionKind) -> Decimal:
        return round_inr(
            sum((s.deducted for s in self.steps if s.kind is kind), Decimal(0))
        )
