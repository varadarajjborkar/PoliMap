"""M6 and M7, verification and compilation.

The verification loop exists because of a measured problem: adding a language
model to extraction halved missed fields and tripled *confidently wrong* ones.
These tests hold the loop to the job that justified it, catching wrong values
without simply discarding the recall the model bought.

Escalating to the user counts as success. A question is a safe outcome; a
confident wrong figure is not.
"""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from app.pipeline.s3_verify import challenger
from app.pipeline.s3_verify.adjudicator import escalate
from app.pipeline.s3_verify.loop import verify
from app.pipeline.s4_compile.compiler import apply_answer, compile_policy
from app.schemas.policy import (
    Challenge,
    ChallengeKind,
    Clause,
    ClauseKind,
    ClauseStatus,
    DocumentSection,
    Evidence,
    ExpenseHead,
    ExtractorKind,
    RoomCategory,
    RoomLimitBasis,
)


def C(
    kind: ClauseKind,
    params: dict,
    verbatim: str,
    *,
    section: DocumentSection = DocumentSection.SCHEDULE,
    confidence: float = 0.8,
    source: ExtractorKind = ExtractorKind.GRAMMAR,
    scope: dict | None = None,
) -> Clause:
    return Clause(
        kind=kind, verbatim=verbatim,
        evidence=Evidence(page_index=0, section=section),
        params=params, scope=scope or {}, confidence=confidence, extracted_by=source,
    )


# Built fresh per use rather than shared. The verification loop mutates clause
# status in place, the ledger is its working state, so module-level instances
# would leak a rejection from one test into the next.
def sum_insured() -> Clause:
    return C(ClauseKind.SUM_INSURED, {"amount_inr": "500000"},
             "Sum Insured (per policy year) Rs. 5,00,000/-")


def room_cap() -> Clause:
    return C(ClauseKind.ROOM_RENT_CAP, {"basis": "flat", "amount_inr": "5000"},
             "Room Rent Limit Rs. 5,000 per day")


# --- evidence checking ----------------------------------------------------


def test_a_clause_must_survive_re_reading_its_own_quote():
    """The sharpest check available, and it needs no model.

    A clause that quotes the sum-insured row while reporting the premium
    printed below it cannot re-derive its own value.
    """
    bad = C(ClauseKind.SUM_INSURED, {"amount_inr": "21712"},
            "Sum Insured (per policy year) Rs. 5,00,000/-")
    assert challenger.check_evidence_supports_value(bad) is not None


def test_a_correct_clause_passes_re_reading():
    assert challenger.check_evidence_supports_value(sum_insured()) is None
    assert challenger.check_evidence_supports_value(room_cap()) is None


def test_a_percentage_clause_passes_re_reading():
    clause = C(ClauseKind.ROOM_RENT_CAP, {"basis": "pct_of_si", "pct_of_si": "1"},
               "Room Rent Limit 1% of Sum Insured per day")
    assert challenger.check_evidence_supports_value(clause) is None


@pytest.mark.parametrize(
    ("kind", "params", "quote"),
    [
        (ClauseKind.COPAY, {"pct": "90"}, "Co-payment 90% of each claim"),
        (ClauseKind.SUM_INSURED, {"amount_inr": "500"}, "Sum Insured Rs. 500"),
        (ClauseKind.SUM_INSURED, {"amount_inr": "900000000"},
         "Sum Insured Rs. 90,00,00,000"),
    ],
)
def test_implausible_values_are_challenged(kind, params, quote):
    assert challenger.check_plausible(C(kind, params, quote)) is not None


def test_realistic_values_are_not_challenged():
    for clause in (sum_insured(), room_cap()):
        assert challenger.check_plausible(clause) is None


def test_a_room_cap_too_large_for_its_cover_is_challenged():
    """Individually plausible, impossible together."""
    challenges = challenger.check_cross_field_coherence([
        sum_insured(),
        C(ClauseKind.ROOM_RENT_CAP, {"basis": "flat", "amount_inr": "400000"},
          "Room Rent Rs. 4,00,000"),
    ])
    assert challenges


def test_a_normal_room_cap_is_not_challenged():
    assert not challenger.check_cross_field_coherence([sum_insured(), room_cap()])


def test_missing_required_terms_are_reported():
    challenges = challenger.check_completeness([sum_insured()])
    assert {c.target_kind for c in challenges} == {ClauseKind.ROOM_RENT_CAP}


def test_a_category_entitlement_satisfies_the_room_requirement():
    clauses = [
        sum_insured(),
        C(ClauseKind.ROOM_CATEGORY_ELIGIBILITY,
          {"basis": "category", "category": "single_private"},
          "Room Rent Limit Single Private Room entitlement"),
    ]
    assert not challenger.check_completeness(clauses)


# --- adjudication ---------------------------------------------------------


def test_a_self_refuting_clause_is_rejected_outright():
    bad = C(ClauseKind.SUM_INSURED, {"amount_inr": "21712"},
            "Sum Insured (per policy year) Rs. 5,00,000/-")
    result = verify([bad, room_cap()])
    assert bad.status is ClauseStatus.REJECTED
    assert bad not in result.surviving


def test_the_schedule_beats_the_wording_without_asking_anyone():
    """The case that produced a wrong value before this stage existed."""
    schedule = C(ClauseKind.ROOM_RENT_CAP, {"basis": "flat", "amount_inr": "10000"},
                 "Room Rent Limit Rs. 10,000 per day",
                 section=DocumentSection.SCHEDULE, confidence=0.86)
    wording = C(ClauseKind.ROOM_RENT_CAP, {"basis": "flat", "amount_inr": "2000"},
                "Room rent entitlement under the standard plan is Rs. 2,000 per day",
                section=DocumentSection.WORDING, confidence=0.21)

    result = verify([sum_insured(), schedule, wording])

    assert wording.status is ClauseStatus.REJECTED
    assert schedule in result.surviving
    assert "schedule" in wording.notes[-1].lower()


def test_an_unresolvable_conflict_becomes_a_question_rather_than_a_guess():
    a = C(ClauseKind.SUM_INSURED, {"amount_inr": "500000"},
          "Sum Insured Rs. 5,00,000", confidence=0.80)
    b = C(ClauseKind.SUM_INSURED, {"amount_inr": "1000000"},
          "Sum Insured Rs. 10,00,000", confidence=0.79)

    result = verify([a, b, room_cap()], max_rounds=2)
    assert result.clarifications
    question = result.clarifications[0]
    assert question.clause_kind is ClauseKind.SUM_INSURED
    # Both readings are offered rather than one being silently chosen.
    assert len(question.options) == 2


def test_missing_terms_produce_plain_language_questions():
    result = verify([C(ClauseKind.COPAY, {"pct": "10"}, "Co-payment 10% of each claim")])
    kinds = {q.clause_kind for q in result.clarifications}
    assert ClauseKind.SUM_INSURED in kinds

    question = next(q for q in result.clarifications
                    if q.clause_kind is ClauseKind.SUM_INSURED)
    assert "?" in question.question
    assert question.help_text
    # Written for a stressed non-expert, not an adjuster.
    assert "clause" not in question.question.lower()


def test_a_user_is_never_asked_the_same_thing_twice():
    a = C(ClauseKind.SUM_INSURED, {"amount_inr": "500000"}, "Sum Insured Rs. 5,00,000")
    b = C(ClauseKind.SUM_INSURED, {"amount_inr": "700000"}, "Sum Insured Rs. 7,00,000")
    c = C(ClauseKind.SUM_INSURED, {"amount_inr": "900000"}, "Sum Insured Rs. 9,00,000")
    result = verify([a, b, c, room_cap()], max_rounds=3)
    kinds = [q.clause_kind for q in result.clarifications]
    assert len(kinds) == len(set(kinds))


def test_escalation_labels_each_option_readably():
    a = C(ClauseKind.SUM_INSURED, {"amount_inr": "500000"}, "Sum Insured Rs. 5,00,000")
    b = C(ClauseKind.SUM_INSURED, {"amount_inr": "1000000"}, "Sum Insured Rs. 10,00,000")
    challenge = Challenge(
        kind=ChallengeKind.CONTRADICTION,
        clause_ids=[a.clause_id, b.clause_id],
        target_kind=ClauseKind.SUM_INSURED,
        question="which?",
    )
    request = escalate(challenge, {a.clause_id: a, b.clause_id: b})
    labels = [o["label"] for o in request.options]
    assert "₹5,00,000" in labels and "₹10,00,000" in labels


# --- loop behaviour -------------------------------------------------------


def test_a_clean_ledger_settles_in_one_round():
    result = verify([sum_insured(), room_cap()])
    assert result.rounds == 1
    assert not result.clarifications
    assert len(result.surviving) == 2


def test_the_loop_respects_its_round_limit():
    a = C(ClauseKind.SUM_INSURED, {"amount_inr": "500000"}, "Sum Insured Rs. 5,00,000")
    b = C(ClauseKind.SUM_INSURED, {"amount_inr": "600000"}, "Sum Insured Rs. 6,00,000")
    assert verify([a, b], max_rounds=2).rounds <= 2


def test_the_same_objection_is_not_raised_twice():
    a = C(ClauseKind.SUM_INSURED, {"amount_inr": "500000"}, "Sum Insured Rs. 5,00,000")
    b = C(ClauseKind.SUM_INSURED, {"amount_inr": "600000"}, "Sum Insured Rs. 6,00,000")
    result = verify([a, b], max_rounds=3)
    keys = [
        (c.kind, tuple(sorted(c.clause_ids)), c.target_kind) for c in result.challenges
    ]
    assert len(keys) == len(set(keys))


# --- compilation ----------------------------------------------------------


def test_compilation_produces_an_executable_policy():
    policy = compile_policy([sum_insured(), room_cap()])
    assert policy.sum_insured == D(500000)
    assert policy.room_limit.effective_daily_cap(policy.sum_insured) == D(5000)
    assert policy.is_usable


def test_percentage_limits_resolve_against_the_cover():
    policy = compile_policy([
        sum_insured(),
        C(ClauseKind.ROOM_RENT_CAP, {"basis": "pct_of_si", "pct_of_si": "1"},
          "Room Rent Limit 1% of Sum Insured per day"),
    ])
    assert policy.room_limit.effective_daily_cap(policy.sum_insured) == D(5000)


def test_a_capped_percentage_keeps_both_bounds():
    policy = compile_policy([
        sum_insured(),
        C(ClauseKind.ROOM_RENT_CAP,
          {"basis": "pct_with_max", "pct_of_si": "2", "amount_inr": "7500"},
          "Room Rent Limit 2% of Sum Insured, subject to a maximum of Rs. 7,500"),
    ])
    # 2% of 5,00,000 is 10,000, but the stated maximum binds.
    assert policy.room_limit.effective_daily_cap(policy.sum_insured) == D(7500)


def test_a_category_entitlement_compiles_without_a_rupee_cap():
    policy = compile_policy([
        sum_insured(),
        C(ClauseKind.ROOM_CATEGORY_ELIGIBILITY,
          {"basis": "category", "category": "single_private"},
          "Room Rent Limit Single Private Room entitlement"),
    ])
    assert policy.room_limit.basis is RoomLimitBasis.CATEGORY_ONLY
    assert policy.room_limit.category_ceiling is RoomCategory.SINGLE_PRIVATE
    assert policy.room_limit.effective_daily_cap(policy.sum_insured) is None


def test_a_missing_cover_amount_is_asked_about_not_assumed():
    """Assuming a default produces an estimate that is wrong and reassuring."""
    policy = compile_policy([room_cap()])
    assert not policy.is_usable
    assert any(
        r.clause_kind is ClauseKind.SUM_INSURED for r in policy.open_clarifications
    )


def test_a_low_confidence_reading_is_offered_for_confirmation():
    uncertain = C(ClauseKind.SUM_INSURED, {"amount_inr": "500000"},
                  "Sum Insured Rs. 5,00,000", confidence=0.30)
    policy = compile_policy([uncertain, room_cap()])
    request = next(
        r for r in policy.open_clarifications if r.clause_kind is ClauseKind.SUM_INSURED
    )
    assert "5,00,000" in request.question
    assert request.suggested_value == 500000.0


def test_the_tightest_sublimit_wins():
    """An estimate that overstates cover is the one that hurts."""
    policy = compile_policy([
        sum_insured(), room_cap(),
        C(ClauseKind.SUBLIMIT, {"amount_inr": "25000", "head": "investigations"},
          "Diagnostics Rs. 25,000", scope={"head": "investigations"}),
        C(ClauseKind.SUBLIMIT, {"amount_inr": "15000", "head": "investigations"},
          "Investigations Rs. 15,000", scope={"head": "investigations"}),
    ])
    limit = policy.sublimit_for(ExpenseHead.INVESTIGATIONS)
    assert limit is not None and limit.amount == D(15000)


def test_confidence_falls_with_each_open_question():
    settled = compile_policy([sum_insured(), room_cap()])
    unsettled = compile_policy([room_cap()])
    assert settled.confidence > unsettled.confidence
    assert not settled.open_clarifications


def test_a_user_answer_overrides_what_was_read():
    policy = compile_policy([room_cap()])
    request = next(
        r for r in policy.open_clarifications if r.clause_kind is ClauseKind.SUM_INSURED
    )
    updated = apply_answer(policy, request.request_id, 750000)

    assert updated.sum_insured == D(750000)
    assert updated.is_usable
    assert not any(r.request_id == request.request_id for r in updated.open_clarifications)


def test_answering_that_there_is_no_room_limit():
    policy = compile_policy([sum_insured()])
    request = next(
        r for r in policy.open_clarifications if r.clause_kind is ClauseKind.ROOM_RENT_CAP
    )
    updated = apply_answer(policy, request.request_id, "none")
    assert updated.room_limit.effective_daily_cap(updated.sum_insured) is None


# --- end to end -----------------------------------------------------------


def test_the_pipeline_reads_a_real_policy_correctly():
    import json

    from app.core.config import GENERATED_DIR
    from app.pipeline.run import run_policy_pipeline

    truth = json.loads(
        (GENERATED_DIR / "policies/truth/POL001.json").read_text()
    )["truth"]
    result = run_policy_pipeline(
        GENERATED_DIR / "policies/clean/POL001.pdf",
        session_id="test", use_model=False,
    )

    assert result.policy.sum_insured == D(str(truth["sum_insured"]))
    assert result.policy.is_usable
    assert not result.needs_user_input
    assert result.document.quality_score == 1.0
