"""Contracts for the helpdesk and the tickets it raises.

The helpdesk answers and files. It never changes anything: not a figure, not a
stage, not a policy. That boundary is the whole design, and it is not a matter
of prompting. There is no write path from here into a session, so the worst a
wrong answer can do is mislead somebody who can look at the screen and see it
is wrong, rather than quietly alter what their claim is being estimated from.

Tickets are minted here and kept by the browser, in the same place a stay is
kept. Nothing about a ticket is worth a database that outlives the session it
came from, and a reference somebody can quote is a reference either way.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class HelpSource(StrEnum):
    """Where an answer came from, which the interface says out loud."""

    KNOWLEDGE = "knowledge"
    """Straight from what this app knows about itself."""
    MODEL = "model"
    """A language model, grounded in that same knowledge."""
    UNKNOWN = "unknown"
    """Nothing matched. Better said than answered around."""


class Suggestion(BaseModel):
    key: str
    question: str
    goes_to: str = ""
    """A step in the app this is about, so the answer can offer to go there."""


class HelpReply(BaseModel):
    text: str
    source: HelpSource = HelpSource.KNOWLEDGE
    key: str = ""
    """What this answer is, where it is one this app wrote.

    Everything written down here is written in English, and the person reading
    it may not be. So a written answer travels with the name it is read under
    and the browser says it in their language, the same way every other
    sentence this app composed does.

    A model's answer carries no key on purpose: it was written in the language
    it was asked in, and looking it up would replace it with a different
    answer to a different question."""
    goes_to: str = ""
    suggestions: list[Suggestion] = Field(default_factory=list)
    offer_ticket: bool = False
    """Whether this is something the helpdesk cannot answer and should file."""


class TicketKind(StrEnum):
    FEEDBACK = "feedback"
    PROBLEM = "problem"
    """Something in the app is wrong or will not work."""
    DATA = "data"
    """Something the user cannot change themselves and needs changed."""

    @property
    def label(self) -> str:
        return {
            TicketKind.FEEDBACK: "Feedback",
            TicketKind.PROBLEM: "Something is not working",
            TicketKind.DATA: "Something I cannot change myself",
        }[self]


class TicketStage(StrEnum):
    """How far a ticket has got.

    Only the first of these is ever reached. There is no support desk behind
    this and pretending otherwise would be the one dishonest thing in the app,
    so the tracker shows the rest as what they are: not started.
    """

    RECEIVED = "received"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"

    @property
    def label(self) -> str:
        return {
            TicketStage.RECEIVED: "Received",
            TicketStage.TRIAGED: "Triaged",
            TicketStage.IN_PROGRESS: "Being worked on",
            TicketStage.RESOLVED: "Resolved",
        }[self]


TICKET_STAGES: tuple[TicketStage, ...] = (
    TicketStage.RECEIVED,
    TicketStage.TRIAGED,
    TicketStage.IN_PROGRESS,
    TicketStage.RESOLVED,
)


class Ticket(BaseModel):
    ticket_id: str = Field(default_factory=lambda: f"PM-{uuid.uuid4().hex[:6].upper()}")
    kind: TicketKind
    subject: str
    detail: str = ""
    screen: str = ""
    """Where in the app it was raised, which is most of the diagnosis."""
    raised_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    stage: TicketStage = TicketStage.RECEIVED
    note: str = ""
    """What the user is told happens next, in words that do not overpromise."""
