"""Stage 3: the verification loop.

Runs challenge and adjudication rounds until the ledger stops changing. Each
round re-derives its objections from the current state, so rejecting a clause in
round one can expose a contradiction that only becomes visible in round two, and
the loop keeps going until nothing moves.

It terminates on whichever comes first: no open challenges, no progress since
the previous round, or the configured round limit. Convergence is not assumed,
a document that keeps producing objections stops after the limit and hands the
remainder to the user rather than spinning.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import settings
from app.core.events import bus
from app.core.logging import get_logger
from app.pipeline.s3_verify import challenger
from app.pipeline.s3_verify.adjudicator import adjudicate
from app.schemas.events import EventStatus, PipelineStage
from app.schemas.policy import (
    Challenge,
    ChallengeResolution,
    ClarificationRequest,
    Clause,
    ClauseStatus,
)

log = get_logger(__name__)
STAGE = PipelineStage.CHALLENGE


@dataclass
class VerificationResult:
    clauses: list[Clause]
    challenges: list[Challenge] = field(default_factory=list)
    clarifications: list[ClarificationRequest] = field(default_factory=list)
    rounds: int = 0

    @property
    def rejected(self) -> list[Clause]:
        return [c for c in self.clauses if c.status is ClauseStatus.REJECTED]

    @property
    def confirmed(self) -> list[Clause]:
        return [c for c in self.clauses if c.status is ClauseStatus.CONFIRMED]

    @property
    def surviving(self) -> list[Clause]:
        return [c for c in self.clauses if c.is_admissible]

    def summary(self) -> dict:
        return {
            "rounds": self.rounds,
            "challenges_raised": len(self.challenges),
            "clauses_rejected": len(self.rejected),
            "clauses_confirmed": len(self.confirmed),
            "questions_for_user": len(self.clarifications),
        }


def _fingerprint(clauses: list[Clause]) -> tuple:
    """Ledger state, so a round that changed nothing can be detected."""
    return tuple(sorted((c.clause_id, c.status.value) for c in clauses))


def verify(
    clauses: list[Clause],
    *,
    session_id: str | None = None,
    max_rounds: int | None = None,
) -> VerificationResult:
    """Challenge and adjudicate until the ledger settles."""
    limit = max_rounds or settings.max_challenge_rounds
    result = VerificationResult(clauses=clauses)
    seen_challenges: set[str] = set()

    for round_number in range(1, limit + 1):
        before = _fingerprint(clauses)

        with bus.step(
            STAGE, "challenge_round", session_id=session_id, round=round_number,
            summary=f"Double-checking the policy, round {round_number}",
        ) as step:
            raised = [
                c for c in challenger.raise_challenges(clauses, round_number=round_number)
                if _key(c) not in seen_challenges
            ]
            for challenge in raised:
                seen_challenges.add(_key(challenge))

            if not raised:
                step.ok("Nothing left to question", challenges=0)
                result.rounds = round_number
                break

            upheld = dismissed = escalated = 0
            for challenge in raised:
                resolution, clarification = adjudicate(challenge, clauses)
                result.challenges.append(challenge)

                if resolution is ChallengeResolution.UPHELD:
                    upheld += 1
                elif resolution is ChallengeResolution.DISMISSED:
                    dismissed += 1
                else:
                    escalated += 1
                    if clarification is not None:
                        result.clarifications.append(clarification)

            step.ok(
                f"{len(raised)} question"
                f"{'s' if len(raised) != 1 else ''} raised, "
                f"{upheld} rejected a reading, {dismissed} settled from the "
                f"document, {escalated} need you",
                challenges=len(raised),
                upheld=upheld, dismissed=dismissed, escalated=escalated,
            )

        result.rounds = round_number

        if _fingerprint(clauses) == before and not result.clarifications:
            # Nothing moved and nothing to ask; further rounds cannot help.
            break

    result.clarifications = _deduplicate(result.clarifications)

    bus.publish(
        STAGE, "verification_complete", session_id=session_id,
        status=EventStatus.WARN if result.clarifications else EventStatus.OK,
        summary=(
            f"Checked over {result.rounds} round"
            f"{'s' if result.rounds != 1 else ''}: "
            f"{len(result.rejected)} misreading"
            f"{'s' if len(result.rejected) != 1 else ''} removed, "
            f"{len(result.clarifications)} question"
            f"{'s' if len(result.clarifications) != 1 else ''} for you"
        ),
        **result.summary(),
    )
    return result


def _key(challenge: Challenge) -> str:
    """Identity of a challenge, so the same objection is not re-raised."""
    target = challenge.target_kind.value if challenge.target_kind else ""
    return f"{challenge.kind.value}|{target}|{','.join(sorted(challenge.clause_ids))}"


def _deduplicate(requests: list[ClarificationRequest]) -> list[ClarificationRequest]:
    """One question per subject.

    A stressed user should never be asked the same thing twice in different
    words, so only the first question about each term survives.
    """
    seen: set = set()
    unique: list[ClarificationRequest] = []
    for request in requests:
        if request.clause_kind in seen:
            continue
        seen.add(request.clause_kind)
        unique.append(request)
    return unique
