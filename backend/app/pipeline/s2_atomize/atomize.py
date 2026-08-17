"""Stage 2 — build the clause ledger.

Two independent extractors read the same pages: deterministic rules and a
language model. Running both and merging is deliberate. They fail differently —
the rules miss unfamiliar phrasings, the model misreads figures — so agreement
between them is real evidence, and disagreement is exactly what the verification
loop in the next stage needs to see.

Merging keeps that signal rather than flattening it. Two findings that agree are
kept as one clause with raised confidence and both sources recorded. Two that
disagree are *both* kept, so the challenge stage can adjudicate them on evidence
instead of the merge silently picking a winner here.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from app.agents.registry import registry
from app.core.events import bus
from app.core.logging import get_logger
from app.pipeline.s1_triage import triage as triage_stage
from app.pipeline.s2_atomize import grammar, model_extract
from app.schemas.document import IngestedDocument
from app.schemas.events import EventStatus, PipelineStage
from app.schemas.policy import Clause, ClauseKind, ExtractorKind

log = get_logger(__name__)
STAGE = PipelineStage.ATOMIZE

AGREEMENT_BONUS = 0.12
"""Confidence added when both extractors independently found the same thing."""

# Kinds where more than one clause is legitimate, so duplicates must not merge
# across different subjects.
MULTI_VALUED = {
    ClauseKind.SUBLIMIT,
    ClauseKind.WAITING_PERIOD,
    ClauseKind.EXCLUSION,
    ClauseKind.POLICY_META,
}


def _identity(clause: Clause) -> tuple:
    """What makes two findings the same finding.

    Includes the parsed value, so two extractors reporting *different* room
    limits stay separate and reach the adjudicator rather than merging into one
    arbitrary answer.
    """
    key: tuple = (clause.kind, _value_signature(clause))
    if clause.kind in MULTI_VALUED:
        # The subject may be recorded in either place: the grammar rules set
        # scope, the model extractor only sets params. Missing it here merges
        # two genuinely different sub-limits into one and loses a cap.
        subject = (
            clause.scope.get("head")
            or clause.params.get("head")
            or clause.scope.get("procedure_code")
            or clause.params.get("procedure_code")
            or clause.scope.get("field")
            or clause.params.get("field")
            or clause.params.get("applies_to")
            or clause.verbatim[:40].lower()
        )
        key = (*key, subject)
    return key


def _value_signature(clause: Clause) -> tuple:
    """A comparable summary of a clause's value."""
    params = clause.params
    parts: list = []
    for field in ("amount_inr", "pct_of_si", "pct", "days", "months",
                  "category", "basis", "covered", "available", "value"):
        if field in params:
            value = params[field]
            if field in ("amount_inr", "pct_of_si", "pct"):
                try:
                    value = str(Decimal(str(value)).normalize())
                except Exception:
                    value = str(value)
            parts.append((field, str(value)))
    return tuple(parts)


def merge(clauses: Iterable[Clause]) -> list[Clause]:
    """Combine findings, preserving genuine disagreement."""
    merged: dict[tuple, Clause] = {}

    for clause in clauses:
        key = _identity(clause)
        existing = merged.get(key)
        if existing is None:
            merged[key] = clause
            continue

        # Same finding from both extractors: keep the better-sourced one and
        # raise confidence, because independent agreement is real evidence.
        winner, loser = (
            (existing, clause) if existing.supersedes(clause) else (clause, existing)
        )
        if winner.extracted_by is not loser.extracted_by:
            winner.confidence = min(1.0, round(winner.confidence + AGREEMENT_BONUS, 3))
            winner.notes.append(
                f"Confirmed independently by the {loser.extracted_by.value} extractor"
            )
        merged[key] = winner

    return list(merged.values())


def atomize(
    document: IngestedDocument,
    *,
    use_model: bool = True,
) -> list[Clause]:
    """Read a document into a clause ledger."""
    session_id = document.session_id

    if all(p.section.value == "unknown" for p in document.pages):
        triage_stage.triage(document)

    grammar_clauses: list[Clause] = []
    with bus.step(
        STAGE, "grammar_extract", session_id=session_id,
        summary="Reading the policy with the rule-based extractor",
    ) as step:
        for page in document.pages:
            grammar_clauses.extend(grammar.extract_page(page))
        step.ok(
            f"Rules found {len(grammar_clauses)} clauses",
            clauses=len(grammar_clauses),
            kinds=sorted({c.kind.value for c in grammar_clauses}),
        )

    model_clauses: list[Clause] = []
    if use_model and registry.has_llm:
        with bus.step(
            STAGE, "model_extract_all", session_id=session_id,
            summary="Reading the policy with a language model",
        ) as step:
            model_clauses = model_extract.extract_pages(
                document.pages, session_id=session_id
            )
            step.ok(
                f"Model contributed {len(model_clauses)} verified clauses",
                clauses=len(model_clauses),
            )
    elif use_model:
        bus.publish(
            STAGE, "model_extract_all", status=EventStatus.SKIPPED,
            summary="No language model available; rules only",
            session_id=session_id,
        )

    with bus.step(
        STAGE, "merge_clauses", session_id=session_id,
        summary="Combining what both extractors found",
    ) as step:
        combined = merge([*grammar_clauses, *model_clauses])
        agreed = sum(1 for c in combined if c.notes)
        conflicts = _count_conflicts(combined)
        step.ok(
            f"{len(combined)} clauses in the ledger, {agreed} confirmed by both, "
            f"{conflicts} in conflict",
            total=len(combined),
            from_rules=len(grammar_clauses),
            from_model=len(model_clauses),
            agreed=agreed,
            conflicts=conflicts,
        )

    return combined


def _count_conflicts(clauses: list[Clause]) -> int:
    """Single-valued kinds holding more than one distinct answer."""
    seen: dict[ClauseKind, set] = {}
    for clause in clauses:
        if clause.kind in MULTI_VALUED:
            continue
        seen.setdefault(clause.kind, set()).add(_value_signature(clause))
    return sum(1 for values in seen.values() if len(values) > 1)


def ledger_summary(clauses: list[Clause]) -> dict:
    """Counts for logging and the interface."""
    by_kind: dict[str, int] = {}
    by_source: dict[str, int] = {}
    for clause in clauses:
        by_kind[clause.kind.value] = by_kind.get(clause.kind.value, 0) + 1
        by_source[clause.extracted_by.value] = by_source.get(clause.extracted_by.value, 0) + 1
    return {
        "total": len(clauses),
        "by_kind": by_kind,
        "by_source": by_source,
        "mean_confidence": (
            round(sum(c.confidence for c in clauses) / len(clauses), 3)
            if clauses else 0.0
        ),
        "grammar_only": sum(
            1 for c in clauses if c.extracted_by is ExtractorKind.GRAMMAR and not c.notes
        ),
    }
