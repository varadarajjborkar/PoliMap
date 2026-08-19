"""Contracts for reading and checking a hospital's final bill.

The estimate answers what a stay should cost. This answers what it did cost, and
whether the figure in front of the family is the one the policy and the
regulator say it should be. The two run through the same adjudication engine on
purpose: a family that was quoted an amount before admission and is handed a
different one at discharge can put the two side by side and see which line moved.

A finding is written to be *acted on at a counter*. It carries the rupees, the
lines it came from, and a sentence that can be said out loud to a billing clerk.
A flag with no sentence attached leaves somebody holding a piece of paper they
know is wrong and no idea what to say next, which is where most of these
conversations already end.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, computed_field

from app.schemas.journey import AlertSeverity
from app.schemas.money import ZERO, Rupees, round_inr
from app.schemas.policy import ExpenseHead
from app.schemas.simulation import SimulationResult


class BilledItem(BaseModel):
    """One line as the hospital printed it."""

    line_no: int = Field(ge=1)
    description: str
    amount: Rupees
    qty: Decimal | None = None
    rate: Rupees | None = None

    head: ExpenseHead | None = None
    """None where neither the words nor the section it sits under place it."""
    from_section: bool = False
    """Whether the head came from a banner rather than the line's own words."""

    page_index: int = 0
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    """Lowest recognition confidence among the words on the line."""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def head_label(self) -> str:
        return self.head.label if self.head else "Not placed"


class ReadBill(BaseModel):
    """Everything the reader could get off the document."""

    document_name: str = ""
    items: list[BilledItem] = Field(default_factory=list)

    gross_total: Rupees | None = None
    """The bill's own total, before discounts and advances."""
    net_payable: Rupees | None = None
    discount: Rupees = Field(default=ZERO)
    advance_paid: Rupees = Field(default=ZERO)

    notes: list[str] = Field(default_factory=list)
    """What the reader could not do, in words the user can act on."""

    from_text_layer: bool = True
    """False where the figures came from OCR or a vision model rather than the
    document's own text. A misread digit is invisible and changes everything
    after it, so what follows is allowed to depend on this."""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def line_total(self) -> Rupees:
        return round_inr(sum((i.amount for i in self.items), ZERO))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def unplaced_total(self) -> Rupees:
        return round_inr(sum((i.amount for i in self.items if i.head is None), ZERO))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def reconciles(self) -> bool:
        """Whether the lines add up to the bill's own total.

        The printed total is a checksum over the lines. A photograph whose lines
        reproduce it was read correctly, whatever the recognition confidence
        says, and one that does not was not, which is the difference between
        arithmetic worth raising at a counter and arithmetic worth ignoring.
        """
        if self.gross_total is None:
            return False
        difference = abs(self.line_total - self.gross_total)
        return difference <= Decimal(1) or (
            self.discount > ZERO and abs(difference - self.discount) <= Decimal(1)
        )

    @property
    def placed(self) -> list[BilledItem]:
        return [i for i in self.items if i.head is not None]

    def by_head(self) -> dict[ExpenseHead, Decimal]:
        totals: dict[ExpenseHead, Decimal] = {}
        for item in self.placed:
            assert item.head is not None
            totals[item.head] = totals.get(item.head, ZERO) + item.amount
        return totals


class FindingKind(StrEnum):
    """What is wrong, or worth asking about, on a bill."""

    SUBSUMED = "subsumed"
    """Billed separately though the regulator places it inside another charge."""
    OPTIONAL_ITEM = "optional_item"
    """On the IRDAI list no policy pays: yours unless a rider covers it."""
    DUPLICATE = "duplicate"
    LINE_ARITHMETIC = "line_arithmetic"
    """Quantity times rate does not come to the amount charged."""
    TOTAL_MISMATCH = "total_mismatch"
    ROOM_ABOVE_CAP = "room_above_cap"
    PROPORTIONATE = "proportionate"
    SUBLIMIT = "sublimit"
    CONSUMABLES = "consumables"
    UNPLACED = "unplaced"
    """Lines the reader could not place, so they sit outside the check."""
    UNCERTAIN_READ = "uncertain_read"
    """The document did not read cleanly enough to check its arithmetic."""

    @property
    def label(self) -> str:
        return {
            FindingKind.SUBSUMED: "Charged twice for one thing",
            FindingKind.OPTIONAL_ITEM: "Your insurer will not pay this",
            FindingKind.DUPLICATE: "The same line appears twice",
            FindingKind.LINE_ARITHMETIC: "This line does not multiply out",
            FindingKind.TOTAL_MISMATCH: "The lines do not add up to the total",
            FindingKind.ROOM_ABOVE_CAP: "Your room costs more than you are covered for",
            FindingKind.PROPORTIONATE: "Proportionate deduction",
            FindingKind.SUBLIMIT: "Above a category limit",
            FindingKind.CONSUMABLES: "Consumables are yours to pay",
            FindingKind.UNPLACED: "Lines we could not place",
            FindingKind.UNCERTAIN_READ: "This document did not read cleanly",
        }[self]


class BillFinding(BaseModel):
    """One thing to raise, with the sentence to raise it in."""

    kind: FindingKind
    severity: AlertSeverity = AlertSeverity.ATTENTION
    headline: str
    detail: str = ""
    ask: str = ""
    """What to say at the billing counter."""
    amount: Rupees = Field(default=ZERO)
    lines: list[int] = Field(default_factory=list)
    """Line numbers on the bill this concerns."""

    key: str = ""
    """Which wording this is, where the kind alone does not say."""
    values: dict[str, str] = Field(default_factory=dict)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def label(self) -> str:
        return self.kind.label

    @property
    def string_key(self) -> str:
        return self.key or self.kind.value


class BillReview(BaseModel):
    """A bill, read and checked against the policy."""

    bill: ReadBill
    findings: list[BillFinding] = Field(default_factory=list)
    settlement: SimulationResult | None = None
    """The same waterfall the estimate used, run on the real bill."""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def questionable(self) -> Rupees:
        """What is on the lines worth raising, before anybody argues about them."""
        raisable = {
            FindingKind.SUBSUMED,
            FindingKind.DUPLICATE,
            FindingKind.LINE_ARITHMETIC,
            FindingKind.TOTAL_MISMATCH,
        }
        return round_inr(
            sum((f.amount for f in self.findings if f.kind in raisable), ZERO)
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def worth_asking(self) -> int:
        return sum(1 for f in self.findings if f.severity is not AlertSeverity.INFO)
