"""Several files: one policy in pieces, or two policies that must not merge.

Most people uploading more than one file are uploading one policy in pieces, a
schedule and a wording and a photograph of an endorsement, and pooling those is
the reason to accept more than one file at a time.

A family holding a corporate policy and a personal one has two of everything.
Merging those silently produces a policy that exists nowhere: one document's
room cap against the other's cover, with no clause disagreeing loudly enough for
anything to notice. Every figure after it is wrong and nothing says so.

The test is identity rather than values, because two documents of one policy
disagree on values all the time and section precedence exists to settle exactly
that.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import GENERATED_DIR
from app.main import app
from app.pipeline.s0_intake.intake import ingest
from app.pipeline.s1_triage.triage import triage
from app.pipeline.s4_compile.reconcile import (
    DocumentIdentity,
    disagreements,
    identify,
    looks_like_two_policies,
    merge_clauses,
)


@pytest.fixture(scope="module")
def policy_pdfs() -> list[Path]:
    found = sorted((GENERATED_DIR / "policies" / "clean").glob("*.pdf"))[:3]
    if len(found) < 2:
        pytest.skip("policy corpus not built")
    return found


@pytest.fixture(scope="module")
def identities(policy_pdfs) -> list[DocumentIdentity]:
    return [
        identify(triage(ingest(path, save_page_images=False)))
        for path in policy_pdfs
    ]


# --- reading identity off a document ----------------------------------------


def test_a_schedule_yields_its_policy_number_insurer_and_holder(identities):
    for identity in identities:
        assert identity.policy_number
        assert identity.insurer
        assert identity.policyholder


def test_a_field_label_is_never_taken_for_a_name(identities):
    """The label and its value sit on separate lines in a flattened table. An
    earlier version stopped at the end of the label line and gave everybody a
    policyholder called "Name", which made every document agree and stopped
    the check firing at all."""
    for identity in identities:
        assert identity.policyholder.lower() not in ("name", "policyholder", "insured")


# --- deciding whether to merge ----------------------------------------------


def test_two_different_policies_are_held_apart(identities):
    assert looks_like_two_policies(identities[:2])
    reasons = {d.what for d in disagreements(identities[:2])}
    assert "policy number" in reasons


def test_the_same_policy_uploaded_twice_is_merged(identities):
    original = identities[0]
    duplicate = DocumentIdentity(
        filename="copy.pdf",
        policy_number=original.policy_number,
        insurer=original.insurer,
        policyholder=original.policyholder,
    )
    assert not looks_like_two_policies([original, duplicate])


def test_a_wording_that_names_nothing_does_not_block_the_merge(identities):
    """The commonest two-file upload is a schedule and a wording, and a wording
    usually names no policyholder. Treating that silence as a disagreement
    would hold up every ordinary upload."""
    wording = DocumentIdentity(filename="wording.pdf")
    assert not looks_like_two_policies([identities[0], wording])
    assert disagreements([identities[0], wording]) == []


def test_a_different_insurer_alone_is_not_enough_to_hold_the_merge():
    """A wording may name a group company rather than the issuing entity, so
    the weaker signals have to agree together before a merge is stopped."""
    a = DocumentIdentity("a.pdf", insurer="Sentinel Health")
    b = DocumentIdentity("b.pdf", insurer="Sentinel General")
    assert not looks_like_two_policies([a, b])


def test_insurer_and_holder_disagreeing_together_is_enough():
    a = DocumentIdentity("a.pdf", insurer="Sentinel Health", policyholder="Vikram Iyer")
    b = DocumentIdentity("b.pdf", insurer="Prayaan General", policyholder="Meera Gowda")
    assert looks_like_two_policies([a, b])


def test_spacing_and_case_do_not_invent_a_conflict():
    a = DocumentIdentity("a.pdf", policy_number="SEN/2026/IND/9620782")
    b = DocumentIdentity("b.pdf", policy_number="sen 2026 ind 9620782")
    assert not looks_like_two_policies([a, b])


def test_a_single_file_is_never_held():
    assert not looks_like_two_policies([DocumentIdentity("only.pdf")])


# --- merging ----------------------------------------------------------------


def test_merging_keeps_every_clause_including_agreements():
    """Two documents stating the same cap is corroboration, and the compiler
    resolves competitors by section precedence. Deduplicating first would
    throw away the evidence that they agreed."""
    from app.pipeline.s2_atomize.atomize import atomize

    documents = [
        triage(ingest(path, save_page_images=False))
        for path in sorted((GENERATED_DIR / "policies" / "clean").glob("*.pdf"))[:2]
    ]
    per_document = [atomize(d, use_model=False) for d in documents]
    merged = merge_clauses(per_document)

    assert len(merged) == sum(len(c) for c in per_document)


# --- over the API -----------------------------------------------------------


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def files_for(paths: list[Path]):
    return [
        ("files", (path.name, path.read_bytes(), "application/pdf"))
        for path in paths
    ]


def test_two_files_of_one_policy_read_as_one_policy(client, policy_pdfs):
    """The same document twice stands in for a schedule and its own wording:
    identical identity, so nothing should be held."""
    path = policy_pdfs[0]
    response = client.post("/api/policy/upload-many", files=[
        ("files", (path.name, path.read_bytes(), "application/pdf")),
        ("files", ("copy.pdf", path.read_bytes(), "application/pdf")),
    ])

    assert response.status_code == 200
    body = response.json()
    assert len(body["documents"]) == 2
    assert body["sum_insured"] > 0


def test_two_different_policies_are_refused_with_the_reason(client, policy_pdfs):
    response = client.post(
        "/api/policy/upload-many", files=files_for(policy_pdfs[:2])
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "different policies" in detail["message"]
    assert any(c["what"] == "policy number" for c in detail["conflicts"])
    assert len(detail["files"]) == 2


def test_a_refused_upload_leaves_no_session_behind(client, policy_pdfs):
    before = client.get("/api/health").json()["active_sessions"]
    client.post("/api/policy/upload-many", files=files_for(policy_pdfs[:2]))
    assert client.get("/api/health").json()["active_sessions"] == before


def test_too_many_files_is_refused_in_plain_words(client, policy_pdfs):
    path = policy_pdfs[0]
    response = client.post("/api/policy/upload-many", files=[
        ("files", (f"{i}.pdf", path.read_bytes(), "application/pdf"))
        for i in range(8)
    ])
    assert response.status_code == 400
    assert "usually enough" in response.json()["detail"]


def test_an_empty_upload_is_refused(client):
    response = client.post("/api/policy/upload-many", files=[
        ("files", ("empty.pdf", b"", "application/pdf")),
    ])
    assert response.status_code == 400
