"""Pipeline telemetry contracts.

Every meaningful action in the system emits a `PipelineEvent`. The same object
is written to the console, persisted, and streamed to the browser, so what the
user sees in the UI is exactly what the server did, no separate reporting path
that can drift from reality.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class PipelineStage(StrEnum):
    """Stages of the coverage pipeline, in execution order."""

    INTAKE = "S0_INTAKE"
    TRIAGE = "S1_TRIAGE"
    ATOMIZE = "S2_ATOMIZE"
    CHALLENGE = "S3_CHALLENGE"
    COMPILE = "S4_COMPILE"
    MATCH = "S5_MATCH"
    SIMULATE = "S6_SIMULATE"
    RANK = "S7_RANK"
    JOURNEY = "JOURNEY"
    SYSTEM = "SYSTEM"

    @property
    def label(self) -> str:
        """Human-readable name for the UI."""
        return _STAGE_LABELS[self]


_STAGE_LABELS: dict[PipelineStage, str] = {
    PipelineStage.INTAKE: "Reading your document",
    PipelineStage.TRIAGE: "Identifying the document",
    PipelineStage.ATOMIZE: "Breaking the policy into clauses",
    PipelineStage.CHALLENGE: "Double-checking each clause",
    PipelineStage.COMPILE: "Building your coverage profile",
    PipelineStage.MATCH: "Finding eligible hospitals",
    PipelineStage.SIMULATE: "Estimating your costs",
    PipelineStage.RANK: "Ranking your options",
    PipelineStage.JOURNEY: "Tracking your care journey",
    PipelineStage.SYSTEM: "System",
}


class EventStatus(StrEnum):
    STARTED = "started"
    OK = "ok"
    WARN = "warn"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineEvent(BaseModel):
    """One observable action. Immutable once emitted."""

    event_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    ts: datetime = Field(default_factory=lambda: datetime.now(UTC))

    stage: PipelineStage
    step: str
    """Short machine-ish name, e.g. "rasterize_page" or "challenge_round"."""

    status: EventStatus = EventStatus.OK
    summary: str = ""
    """One line a non-technical user can read."""

    detail: dict[str, Any] = Field(default_factory=dict)
    """Structured payload, counts, scores, decisions. Rendered as a table."""

    duration_ms: float | None = None
    session_id: str | None = None
    """Groups all events belonging to one user's run."""

    def console_line(self) -> str:
        icon = {
            EventStatus.STARTED: "->",
            EventStatus.OK: "ok",
            EventStatus.WARN: "!!",
            EventStatus.FAILED: "XX",
            EventStatus.SKIPPED: "--",
        }[self.status]
        took = f" ({self.duration_ms:.0f}ms)" if self.duration_ms is not None else ""
        return f"[{icon}] {self.stage.value}/{self.step}{took} {self.summary}".rstrip()
