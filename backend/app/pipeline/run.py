"""The policy pipeline, end to end.

Chains stages 0 through 4: read the document, work out what it is, break it into
clauses, attack those clauses, and compile what survives into an executable
policy. One entry point so the API, the benchmarks and the tests all exercise
the same path: a benchmark that measured a different code path from the one
users hit would be worse than no benchmark.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.events import bus
from app.pipeline.s0_intake.intake import ingest, ingest_bytes
from app.pipeline.s1_triage.triage import triage
from app.pipeline.s2_atomize.atomize import atomize
from app.pipeline.s3_verify.loop import VerificationResult, verify
from app.pipeline.s4_compile import reconcile
from app.pipeline.s4_compile.compiler import compile_policy
from app.schemas.document import IngestedDocument
from app.schemas.events import EventStatus, PipelineStage
from app.schemas.money import format_inr
from app.schemas.policy import NormalizedPolicy


@dataclass
class PolicyPipelineResult:
    document: IngestedDocument
    policy: NormalizedPolicy
    verification: VerificationResult

    @property
    def needs_user_input(self) -> bool:
        return bool(self.policy.open_clarifications)

    def summary(self) -> dict:
        return {
            "document": self.document.filename,
            "pages": self.document.page_count,
            "read_quality": self.document.quality_score,
            "needed_ocr": self.document.needed_ocr,
            "clauses": len(self.policy.clauses),
            "sum_insured": float(self.policy.sum_insured),
            "confidence": self.policy.confidence,
            "questions": len(self.policy.open_clarifications),
            **self.verification.summary(),
        }


def _run(
    document: IngestedDocument, *, use_model: bool, verify_clauses: bool
) -> PolicyPipelineResult:
    session_id = document.session_id

    triage(document)
    clauses = atomize(document, use_model=use_model)

    if verify_clauses:
        verification = verify(clauses, session_id=session_id)
    else:
        verification = VerificationResult(clauses=clauses)

    policy = compile_policy(verification.surviving, session_id=session_id)

    # Questions raised by verification join those raised by compilation, and the
    # user is asked once about each subject rather than twice.
    known = {r.clause_kind for r in policy.open_clarifications}
    policy.open_clarifications.extend(
        r for r in verification.clarifications if r.clause_kind not in known
    )

    result = PolicyPipelineResult(document, policy, verification)

    bus.publish(
        PipelineStage.SYSTEM, "pipeline_complete", session_id=session_id,
        summary=(
            f"Read {document.filename}: cover {format_inr(policy.sum_insured)}, "
            f"room {policy.room_limit.describe(policy.sum_insured)}"
            + (f", {len(policy.open_clarifications)} question"
               f"{'s' if len(policy.open_clarifications) != 1 else ''} for you"
               if policy.open_clarifications else "")
        ),
        **result.summary(),
    )
    return result


def run_policy_pipeline(
    path: Path,
    *,
    session_id: str | None = None,
    use_model: bool = True,
    verify_clauses: bool = True,
) -> PolicyPipelineResult:
    """Read a policy document from disk into a compiled policy."""
    document = ingest(path, session_id=session_id)
    return _run(document, use_model=use_model, verify_clauses=verify_clauses)


def run_policy_pipeline_bytes(
    data: bytes,
    filename: str,
    *,
    session_id: str | None = None,
    use_model: bool = True,
    verify_clauses: bool = True,
) -> PolicyPipelineResult:
    """Read an uploaded payload into a compiled policy."""
    document = ingest_bytes(data, filename, session_id=session_id)
    return _run(document, use_model=use_model, verify_clauses=verify_clauses)


def _starting_on(
    stage: PipelineStage,
    filename: str,
    index: int,
    total: int,
    session_id: str | None,
) -> None:
    """Mark the point where the work moves onto the next file.

    Reading four documents is four times the wait of reading one, and without
    this the browser can only say that something is happening. With it, it can
    say which of them is being read and how many are left, which is the
    difference between waiting and being kept waiting.
    """
    if total < 2:
        return
    bus.publish(
        stage, "document_started", session_id=session_id,
        summary=f"{filename} ({index + 1} of {total})",
        file=filename, index=index, documents=total,
    )


@dataclass
class MultiDocumentResult:
    """Several uploaded files, read together or held apart deliberately."""

    documents: list[IngestedDocument]
    identities: list[reconcile.DocumentIdentity]
    policy: NormalizedPolicy | None
    verification: VerificationResult | None
    conflicts: list[reconcile.Disagreement]

    @property
    def held_for_conflict(self) -> bool:
        """Whether the files were not merged because they disagree on identity."""
        return self.policy is None

    def summary(self) -> dict:
        return {
            "files": [d.filename for d in self.documents],
            "pages": sum(d.page_count for d in self.documents),
            "conflicts": [c.what for c in self.conflicts],
            "merged": not self.held_for_conflict,
        }


def run_policy_pipeline_many(
    payloads: list[tuple[bytes, str]],
    *,
    session_id: str | None = None,
    use_model: bool = True,
    verify_clauses: bool = True,
) -> MultiDocumentResult:
    """Read several uploaded files as one policy, unless they are not one.

    Most multi-file uploads are one policy in pieces: the schedule, the wording,
    a photograph of an endorsement. Those belong in one ledger, and pooling them
    is the reason to accept more than one file.

    Some are not. A family holding a corporate policy and a personal one has two
    of everything, and merging them silently produces a policy that exists
    nowhere: one document's room cap against the other's cover, with no clause
    disagreeing loudly enough to notice. So identity is checked first, and when
    the files name two different policies nothing is merged and the caller is
    handed the disagreement to put to the user.
    """
    documents = []
    for index, (data, filename) in enumerate(payloads):
        _starting_on(PipelineStage.INTAKE, filename, index, len(payloads), session_id)
        documents.append(ingest_bytes(data, filename, session_id=session_id))

    for document in documents:
        triage(document)

    identities = [reconcile.identify(document) for document in documents]
    conflicts = reconcile.disagreements(identities)

    if len(documents) > 1 and reconcile.looks_like_two_policies(identities):
        bus.publish(
            PipelineStage.SYSTEM, "documents_conflict", session_id=session_id,
            status=EventStatus.WARN,
            summary=(
                f"These {len(documents)} files look like different policies. "
                f"Asking before merging them."
            ),
            files=[d.filename for d in documents],
            conflicts=[c.what for c in conflicts],
        )
        return MultiDocumentResult(
            documents=documents, identities=identities,
            policy=None, verification=None, conflicts=conflicts,
        )

    per_document = []
    for index, document in enumerate(documents):
        _starting_on(
            PipelineStage.ATOMIZE, document.filename, index, len(documents), session_id
        )
        per_document.append(atomize(document, use_model=use_model))
    clauses = reconcile.merge_clauses(per_document)

    if len(documents) > 1:
        bus.publish(
            PipelineStage.ATOMIZE, "merge_documents", session_id=session_id,
            summary=(
                f"Read {len(documents)} files as one policy, "
                f"{len(clauses)} terms between them"
            ),
            files=[d.filename for d in documents], clauses=len(clauses),
        )

    if verify_clauses:
        verification = verify(clauses, session_id=session_id)
    else:
        verification = VerificationResult(clauses=clauses)

    policy = compile_policy(verification.surviving, session_id=session_id)
    policy.meta = reconcile.meta_from(identities, policy.meta)

    known = {r.clause_kind for r in policy.open_clarifications}
    policy.open_clarifications.extend(
        r for r in verification.clarifications if r.clause_kind not in known
    )

    result = MultiDocumentResult(
        documents=documents, identities=identities,
        policy=policy, verification=verification, conflicts=conflicts,
    )

    # The same closing line the single-document path emits. Without it a
    # multi-file read has no end in the log or on the browser's progress panel,
    # which leaves the last step looking as though it never finished.
    bus.publish(
        PipelineStage.SYSTEM, "pipeline_complete", session_id=session_id,
        summary=(
            f"Read {len(documents)} file{'s' if len(documents) != 1 else ''}: "
            f"cover {format_inr(policy.sum_insured)}, "
            f"room {policy.room_limit.describe(policy.sum_insured)}"
            + (f", {len(policy.open_clarifications)} question"
               f"{'s' if len(policy.open_clarifications) != 1 else ''} for you"
               if policy.open_clarifications else "")
        ),
        clauses=len(policy.clauses),
        confidence=policy.confidence,
        questions=len(policy.open_clarifications),
        **result.summary(),
    )
    return result
