"""Resolve challenges, and escalate honestly when they cannot be resolved.

The adjudicator has three ways to settle an objection, tried in order of how
much they can be trusted:

1. **Rules.** A clause whose own quote does not contain the value it reports is
   simply wrong, and precedence settles most contradictions — a schedule figure
   beats the same figure in generic wording. No judgement is required.
2. **A model re-reading the evidence.** Where two readings are both defensible,
   the competing quotes are put to a model with the question stated plainly.
   The model is asked to choose between existing candidates, never to supply a
   value of its own, so this step cannot introduce a new figure.
3. **The user.** Anything still open becomes a plain-language question with the
   relevant part of their document attached.

The third outcome is a success, not a failure. Turning a confidently wrong
number into a question the user can answer is the entire point of the stage.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.base import LLMUnavailable
from app.agents.registry import registry
from app.core.config import ModelRole
from app.core.logging import get_logger
from app.pipeline.s3_verify import challenger
from app.schemas.policy import (
    Challenge,
    ChallengeKind,
    ChallengeResolution,
    ClarificationRequest,
    Clause,
    ClauseKind,
    ClauseStatus,
)

log = get_logger(__name__)

# Below this gap the two readings are too close to separate on precedence alone
# and the evidence is re-read instead.
DECISIVE_PRECEDENCE_GAP = 10


class Verdict(BaseModel):
    winning_quote: str = Field(
        description="The quote that states this policyholder's actual term, "
                    "copied exactly from the candidates offered"
    )
    reason: str = Field(description="One sentence, in plain language")
    confident: bool = Field(description="False if the document is genuinely unclear")


ADJUDICATOR_SYSTEM = (
    "You settle disagreements about what an Indian health insurance policy "
    "states. You choose between the readings you are given and never invent a "
    "value. A policy schedule states the policyholder's own terms; policy "
    "wording states standard terms that may not apply to them. If the document "
    "genuinely does not settle the question, you say so."
)

ADJUDICATOR_PROMPT = """A policy document has been read two or more ways for the same term, and only one can be correct.

TERM IN QUESTION: {term}

CANDIDATE READINGS:
{candidates}

Choose the reading that states this policyholder's actual term.

Guidance:
- A figure on the policy schedule beats the same figure in the policy wording.
- Wording that says "standard plan" or "unless otherwise specified in the Schedule" is describing a default, not this policyholder's term.
- Copy "winning_quote" exactly from one of the candidates above.
- Set "confident" to false if the document does not actually settle this.
"""


def _describe(clause: Clause) -> str:
    params = ", ".join(
        f"{k}={v}" for k, v in sorted(clause.params.items())
        if k in ("amount_inr", "pct_of_si", "pct", "basis", "category", "covered")
    )
    return (
        f'- section: {clause.evidence.section.value}, page {clause.evidence.page_index + 1}, '
        f'read by {clause.extracted_by.value}, reports [{params}]\n'
        f'  quote: "{clause.verbatim[:200]}"'
    )


def resolve_by_rule(
    challenge: Challenge, by_id: dict[str, Clause]
) -> ChallengeResolution | None:
    """Settle what can be settled without judgement."""
    clauses = [by_id[cid] for cid in challenge.clause_ids if cid in by_id]

    if challenge.kind in (ChallengeKind.EVIDENCE_WEAK, ChallengeKind.IMPLAUSIBLE):
        # The clause is self-refuting; it does not get a second hearing.
        for clause in clauses:
            clause.status = ClauseStatus.REJECTED
            clause.notes.append(f"Rejected: {challenge.question}")
        challenge.resolution_note = "Rejected on its own evidence."
        return ChallengeResolution.UPHELD

    if challenge.kind is ChallengeKind.CONTRADICTION and len(clauses) >= 2:
        ranked = sorted(
            clauses,
            key=lambda c: (c.evidence.section.precedence, c.confidence),
            reverse=True,
        )
        best, runner_up = ranked[0], ranked[1]
        gap = best.evidence.section.precedence - runner_up.evidence.section.precedence
        if gap >= DECISIVE_PRECEDENCE_GAP:
            for clause in ranked[1:]:
                clause.status = ClauseStatus.REJECTED
                clause.notes.append(
                    f"Superseded by the {best.evidence.section.value} "
                    f"on page {best.evidence.page_index + 1}"
                )
            challenge.winning_clause_id = best.clause_id
            challenge.resolution_note = (
                f"The {best.evidence.section.value} states this policyholder's "
                f"own terms and overrides the {runner_up.evidence.section.value}."
            )
            return ChallengeResolution.DISMISSED

    return None


def resolve_by_model(
    challenge: Challenge, by_id: dict[str, Clause]
) -> ChallengeResolution | None:
    """Put the competing quotes to a model and let it choose between them."""
    clauses = [by_id[cid] for cid in challenge.clause_ids if cid in by_id]
    if len(clauses) < 2 or not registry.has_llm:
        return None

    term = (challenge.target_kind or clauses[0].kind).label
    prompt = ADJUDICATOR_PROMPT.format(
        term=term,
        candidates="\n".join(_describe(c) for c in clauses),
    )

    try:
        verdict = registry.complete_structured(
            ModelRole.ADJUDICATE, prompt=prompt, schema=Verdict,
            system=ADJUDICATOR_SYSTEM, temperature=0.0,
        )
    except LLMUnavailable:
        return None

    if not verdict.confident:
        challenge.resolution_note = verdict.reason
        return ChallengeResolution.ESCALATED

    # The verdict must name one of the candidates. A quote that matches none of
    # them means the model answered a different question, and is discarded.
    winner = _match_candidate(verdict.winning_quote, clauses)
    if winner is None:
        log.debug("adjudicator quote matched no candidate", quote=verdict.winning_quote[:80])
        return None

    for clause in clauses:
        if clause.clause_id != winner.clause_id:
            clause.status = ClauseStatus.REJECTED
            clause.notes.append(f"Set aside: {verdict.reason}")
    winner.status = ClauseStatus.CONFIRMED
    winner.confidence = min(1.0, round(winner.confidence + 0.10, 3))
    challenge.winning_clause_id = winner.clause_id
    challenge.resolution_note = verdict.reason
    return ChallengeResolution.DISMISSED


def _match_candidate(quote: str, clauses: list[Clause]) -> Clause | None:
    from app.pipeline.s2_atomize.grounding import normalise

    target = normalise(quote)
    if not target:
        return None
    for clause in clauses:
        candidate = normalise(clause.verbatim)
        if target == candidate or target in candidate or candidate in target:
            return clause
    return None


def escalate(challenge: Challenge, by_id: dict[str, Clause]) -> ClarificationRequest:
    """Turn an unresolved objection into a question a stressed person can answer."""
    clauses = [by_id[cid] for cid in challenge.clause_ids if cid in by_id]
    kind = challenge.target_kind or (clauses[0].kind if clauses else ClauseKind.SUM_INSURED)

    for clause in clauses:
        clause.status = ClauseStatus.NEEDS_USER

    if challenge.kind is ChallengeKind.MISSING:
        question, help_text = _missing_prompt(kind)
        options: list[dict] = []
    else:
        question = f"Which of these is right for your {kind.label.lower()}?"
        help_text = (
            "Your document says different things in different places. "
            "The policy schedule is usually the page with your name and policy "
            "number on it."
        )
        options = [
            {
                "label": _option_label(clause),
                "value": clause.clause_id,
                "source": clause.evidence.section.value,
                "page": clause.evidence.page_index + 1,
            }
            for clause in clauses
        ]

    return ClarificationRequest(
        clause_kind=kind,
        question=question,
        help_text=help_text,
        options=options,
        evidence=clauses[0].evidence if clauses else None,
        challenge_id=challenge.challenge_id,
    )


def _option_label(clause: Clause) -> str:
    from app.schemas.money import format_inr

    params = clause.params
    if (amount := params.get("amount_inr")) is not None:
        try:
            return format_inr(amount)
        except Exception:
            return str(amount)
    if (pct := params.get("pct_of_si")) is not None:
        return f"{pct}% of your cover"
    if (pct := params.get("pct")) is not None:
        return f"{pct}%"
    if (category := params.get("category")) is not None:
        return str(category).replace("_", " ").capitalize()
    return clause.verbatim[:60]


def _missing_prompt(kind: ClauseKind) -> tuple[str, str]:
    prompts = {
        ClauseKind.SUM_INSURED: (
            "What is the total cover amount on your policy?",
            "This is the most your insurer will pay in a year. It is usually the "
            "largest figure on your policy schedule.",
        ),
        ClauseKind.ROOM_RENT_CAP: (
            "Does your policy limit how much it pays for your hospital room?",
            "Most policies cap the daily room rent. This matters: a room above "
            "your limit also reduces what your insurer pays on other charges.",
        ),
    }
    return prompts.get(
        kind,
        (
            f"What does your policy say about {kind.label.lower()}?",
            "We could not find this in the document you uploaded.",
        ),
    )


def adjudicate(
    challenge: Challenge, clauses: list[Clause]
) -> tuple[ChallengeResolution, ClarificationRequest | None]:
    """Settle one challenge by rule, then by model, then by asking.

    Challenges are raised in a batch and adjudicated in sequence, so a clause
    can already have been rejected by an earlier challenge in the same round.
    Only clauses still standing are considered: without this, a later objection
    can pick an already-discredited reading as its winner and reinstate it.
    """
    by_id = {c.clause_id: c for c in clauses if c.is_admissible}

    live = [cid for cid in challenge.clause_ids if cid in by_id]
    if challenge.clause_ids and not live:
        # Everything this objection was about has already been settled.
        challenge.resolution = ChallengeResolution.UPHELD
        challenge.resolution_note = "Already resolved by an earlier check."
        return ChallengeResolution.UPHELD, None
    if challenge.clause_ids and len(live) < len(challenge.clause_ids):
        challenge.clause_ids = live
        if challenge.kind is ChallengeKind.CONTRADICTION and len(live) < 2:
            # The disagreement evaporated when the other reading was rejected.
            challenge.resolution = ChallengeResolution.DISMISSED
            challenge.resolution_note = "The competing reading was already rejected."
            return ChallengeResolution.DISMISSED, None

    if (resolution := resolve_by_rule(challenge, by_id)) is not None:
        challenge.resolution = resolution
        return resolution, None

    if (resolution := resolve_by_model(challenge, by_id)) is not None:
        challenge.resolution = resolution
        if resolution is ChallengeResolution.ESCALATED:
            return resolution, escalate(challenge, by_id)
        return resolution, None

    challenge.resolution = ChallengeResolution.ESCALATED
    return ChallengeResolution.ESCALATED, escalate(challenge, by_id)


__all__ = ["adjudicate", "escalate", "challenger"]
