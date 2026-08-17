"""The policy pipeline, end to end.

Chains stages 0 through 4: read the document, work out what it is, break it into
clauses, attack those clauses, and compile what survives into an executable
policy. One entry point so the API, the benchmarks and the tests all exercise
the same path — a benchmark that measured a different code path from the one
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
from app.pipeline.s4_compile.compiler import compile_policy
from app.schemas.document import IngestedDocument
from app.schemas.events import PipelineStage
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
