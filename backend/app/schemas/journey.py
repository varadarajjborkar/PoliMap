"""Care journey tracking.

The insurance position is not static. Costs accrue daily, sub-limits drain, a
room that was affordable on day one becomes expensive by day five, and
pre-authorisation has a window that closes. The journey model exists so the
system can re-answer "where do I stand" at every stage rather than once at
admission.

Stages are deliberately coarse and administrative, admission, investigation,
procedure, recovery. They describe *where the paperwork is*, never a clinical
state, and nothing here infers or records a diagnosis.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, computed_field

from app.schemas.money import Rupees, round_inr
from app.schemas.policy import ExpenseHead, RoomCategory


class JourneyStage(StrEnum):
    PRE_ADMISSION = "pre_admission"
    ADMITTED = "admitted"
    INVESTIGATION = "investigation"
    PRE_AUTH = "pre_auth"
    PROCEDURE = "procedure"
    RECOVERY = "recovery"
    DISCHARGE_PLANNING = "discharge_planning"
    SETTLED = "settled"

    @property
    def label(self) -> str:
        return {
            JourneyStage.PRE_ADMISSION: "Choosing a hospital",
            JourneyStage.ADMITTED: "Admitted",
            JourneyStage.INVESTIGATION: "Tests and scans",
            JourneyStage.PRE_AUTH: "Insurance approval",
            JourneyStage.PROCEDURE: "Treatment",
            JourneyStage.RECOVERY: "Recovery",
            JourneyStage.DISCHARGE_PLANNING: "Planning discharge",
            JourneyStage.SETTLED: "Claim settled",
        }[self]

    @property
    def order(self) -> int:
        return _STAGE_ORDER[self]


_STAGE_ORDER: dict[JourneyStage, int] = {
    stage: i
    for i, stage in enumerate(
        [
            JourneyStage.PRE_ADMISSION,
            JourneyStage.ADMITTED,
            JourneyStage.INVESTIGATION,
            JourneyStage.PRE_AUTH,
            JourneyStage.PROCEDURE,
            JourneyStage.RECOVERY,
            JourneyStage.DISCHARGE_PLANNING,
            JourneyStage.SETTLED,
        ]
    )
}



class AlertSeverity(StrEnum):
    INFO = "info"
    ATTENTION = "attention"
    URGENT = "urgent"

    @property
    def rank(self) -> int:
        return {
            AlertSeverity.INFO: 0,
            AlertSeverity.ATTENTION: 1,
            AlertSeverity.URGENT: 2,
        }[self]


class AlertKind(StrEnum):
    ROOM_OVER_LIMIT = "room_over_limit"
    SUBLIMIT_NEARLY_USED = "sublimit_nearly_used"
    COVER_NEARLY_EXHAUSTED = "cover_nearly_exhausted"
    PRE_AUTH_DUE = "pre_auth_due"
    NON_PAYABLE_ACCUMULATING = "non_payable_accumulating"
    ROOM_DOWNGRADE_SAVING = "room_downgrade_saving"
    DOCUMENTS_NEEDED = "documents_needed"
    COVER_HEALTHY = "cover_healthy"


class Alert(BaseModel):
    """A stage-aware, costed prompt.

    Every alert must state what is happening, what it means in rupees, and what
    the user could do. An alert without an action is just anxiety.
    """

    alert_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    kind: AlertKind
    severity: AlertSeverity = AlertSeverity.INFO
    title: str
    message: str
    action: str = ""
    amount: Rupees | None = None
    clause_ids: list[str] = Field(default_factory=list)
    stage: JourneyStage | None = None


class CostEntry(BaseModel):
    """An actual charge recorded during the stay."""

    entry_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    head: ExpenseHead
    amount: Rupees
    description: str = ""
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    stage: JourneyStage = JourneyStage.ADMITTED

    # A photo of the bill, attached when the charge is entered. Optional, and
    # the reason it exists is that hunting for paper receipts weeks later, at
    # claim time, is the part people actually dread.
    receipt_name: str = ""
    """Original filename, shown to the user. Empty when nothing was attached."""


class TransitionKind(StrEnum):
    """How a stage came to change, which decides how it reads back."""

    START = "start"
    ADVANCE = "advance"
    SKIP = "skip"
    BACK = "back"


class JourneyEvent(BaseModel):
    """A recorded transition or note on the timeline."""

    event_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    stage: JourneyStage
    title: str
    description: str = ""
    alerts: list[Alert] = Field(default_factory=list)

    kind: TransitionKind = TransitionKind.ADVANCE
    skipped: list[JourneyStage] = Field(default_factory=list)
    """Stages passed over. Recorded so the history stays honest about it."""
    reason: str = ""
    """Why, in the user's own words. Never required."""


class JourneyState(BaseModel):
    """Where a patient is, and what that means for their cover."""

    journey_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    session_id: str = ""
    policy_id: str = ""

    stage: JourneyStage = JourneyStage.PRE_ADMISSION
    hospital_id: str | None = None
    hospital_name: str = ""
    procedure_code: str | None = None
    room_category: RoomCategory | None = None
    room_rate_per_day: Rupees | None = None

    admitted_at: datetime | None = None
    days_elapsed: int = 0

    costs: list[CostEntry] = Field(default_factory=list)
    timeline: list[JourneyEvent] = Field(default_factory=list)
    active_alerts: list[Alert] = Field(default_factory=list)

    pre_auth_filed: bool = False
    pre_auth_approved_amount: Rupees | None = None

    checklist_done: list[str] = Field(default_factory=list)
    """Items ticked off, across every stage. Kept on the journey rather than in
    the browser so the list is a record of what was done rather than a poster
    that resets on reload, and so a second person opening the same stay sees
    what the first has already dealt with."""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def accrued_total(self) -> Rupees:
        return round_inr(sum((c.amount for c in self.costs), Decimal(0)))

    def accrued_by_head(self) -> dict[ExpenseHead, Decimal]:
        totals: dict[ExpenseHead, Decimal] = {}
        for entry in self.costs:
            totals[entry.head] = totals.get(entry.head, Decimal(0)) + entry.amount
        return totals

    @property
    def is_active(self) -> bool:
        return self.stage not in (JourneyStage.PRE_ADMISSION, JourneyStage.SETTLED)


class BurnDown(BaseModel):
    """Cover consumed against cover available, for the timeline chart."""

    sum_insured: Rupees
    consumed: Rupees
    projected_total: Rupees
    """Expected consumption by discharge at the current rate."""
    remaining: Rupees

    @computed_field  # type: ignore[prop-decorator]
    @property
    def consumed_fraction(self) -> float:
        return float(self.consumed / self.sum_insured) if self.sum_insured else 0.0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def will_exceed(self) -> bool:
        return self.projected_total > self.sum_insured
