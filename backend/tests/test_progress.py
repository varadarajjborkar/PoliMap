"""Watching a read happen, rather than waiting for it to end.

Reading a policy is the slowest thing this system does and the one moment the
user is certainly waiting on it. The activity stream is keyed by session, so
until the browser can name the session before the upload, the only honest thing
it can show while a document is read is a spinner.

These cover the handover that makes it watchable: the browser claims a session,
hands the id back with the files, and the steps it sees are the steps of its own
upload.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.session import sessions
from app.core.events import bus
from app.main import app
from app.pipeline.run import _starting_on
from app.schemas.events import PipelineStage


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_a_session_can_be_claimed_before_there_is_anything_in_it(client):
    response = client.post("/api/session")
    assert response.status_code == 200

    session_id = response.json()["session_id"]
    assert session_id
    assert sessions.get(session_id) is not None
    assert sessions.get(session_id).policy is None


def test_two_claims_are_two_sessions(client):
    first = client.post("/api/session").json()["session_id"]
    second = client.post("/api/session").json()["session_id"]
    assert first != second


def test_an_upload_lands_in_the_session_the_browser_claimed(client):
    """The whole point: the stream the browser opened is the stream it gets."""
    claimed = client.post("/api/session").json()["session_id"]

    response = client.post(
        "/api/policy/upload-many",
        files=[("files", ("cover.txt", b"Sum insured Rs. 5,00,000", "text/plain"))],
        data={"insurer_id": "", "session_id": claimed},
    )
    assert response.status_code == 200
    assert response.json()["session_id"] == claimed


def test_the_events_of_that_upload_carry_the_claimed_id(client):
    claimed = client.post("/api/session").json()["session_id"]

    client.post(
        "/api/policy/upload-many",
        files=[("files", ("cover.txt", b"Sum insured Rs. 5,00,000", "text/plain"))],
        data={"insurer_id": "", "session_id": claimed},
    )

    history = client.get(f"/api/events/{claimed}/history").json()["events"]
    steps = [event["step"] for event in history]
    assert "upload_received" in steps
    # The first thing the stream carries is the arrival of the files, so a
    # phone on a slow connection has something true on screen immediately.
    assert steps[0] == "upload_received"
    assert "pipeline_complete" in steps or "compile_policy" in steps


def test_a_session_already_holding_a_policy_is_never_overwritten(client):
    """A stale id in an old tab must not be able to replace a live policy."""
    existing = client.post(
        "/api/policy/manual",
        json={"sum_insured": 500000, "room_limit_type": "flat",
              "room_limit_amount": 5000},
    ).json()["session_id"]

    response = client.post(
        "/api/policy/upload-many",
        files=[("files", ("cover.txt", b"Sum insured Rs. 3,00,000", "text/plain"))],
        data={"insurer_id": "", "session_id": existing},
    )
    assert response.status_code == 200
    assert response.json()["session_id"] != existing

    # And the original is exactly as it was.
    kept = client.get(f"/api/policy/{existing}").json()
    assert kept["sum_insured"] == 500000


def test_an_unknown_id_is_ignored_rather_than_refused(client):
    """A browser whose session expired mid-upload still gets its policy read."""
    response = client.post(
        "/api/policy/upload-many",
        files=[("files", ("cover.txt", b"Sum insured Rs. 5,00,000", "text/plain"))],
        data={"insurer_id": "", "session_id": "deadbeefcafe"},
    )
    assert response.status_code == 200
    assert response.json()["session_id"] != "deadbeefcafe"


def test_single_file_upload_also_honours_the_claimed_id(client):
    claimed = client.post("/api/session").json()["session_id"]
    response = client.post(
        "/api/policy/upload",
        files={"file": ("cover.txt", b"Sum insured Rs. 5,00,000", "text/plain")},
        data={"insurer_id": "", "session_id": claimed},
    )
    assert response.status_code == 200
    assert response.json()["session_id"] == claimed


def test_uploading_without_an_id_still_works(client):
    """Nothing about the old path changed for a client that does not send one."""
    response = client.post(
        "/api/policy/upload-many",
        files=[("files", ("cover.txt", b"Sum insured Rs. 5,00,000", "text/plain"))],
        data={"insurer_id": ""},
    )
    assert response.status_code == 200
    assert response.json()["session_id"]


# --- per-document markers --------------------------------------------------


def test_one_document_gets_no_document_marker():
    """"Document 1 of 1" is noise. It is only worth saying when there are two."""
    _starting_on(PipelineStage.INTAKE, "only.pdf", 0, 1, "sess-one")
    assert bus.history("sess-one") == []


def test_several_documents_each_announce_themselves():
    for index, name in enumerate(["schedule.pdf", "wording.pdf", "endorsement.jpg"]):
        _starting_on(PipelineStage.INTAKE, name, index, 3, "sess-many")

    events = bus.history("sess-many")
    assert [e.detail["file"] for e in events] == [
        "schedule.pdf", "wording.pdf", "endorsement.jpg"
    ]
    assert [e.detail["index"] for e in events] == [0, 1, 2]
    assert all(e.detail["documents"] == 3 for e in events)
    assert events[1].summary == "wording.pdf (2 of 3)"


# --- endings ---------------------------------------------------------------


def test_a_multi_file_read_says_when_it_is_over(client):
    """The single-file path always did. Without it the last step on the
    browser's progress panel sits there looking unfinished."""
    claimed = client.post("/api/session").json()["session_id"]
    client.post(
        "/api/policy/upload-many",
        files=[
            ("files", ("a.txt", b"Sum insured Rs. 5,00,000", "text/plain")),
            ("files", ("b.txt", b"Room rent limit Rs. 5,000 per day", "text/plain")),
        ],
        data={"insurer_id": "", "session_id": claimed},
    )
    history = client.get(f"/api/events/{claimed}/history").json()["events"]
    assert history[-1]["step"] == "pipeline_complete"
    assert history[-1]["detail"]["merged"] is True


def test_a_document_that_will_not_open_ends_the_log_too(client):
    """It fails before any timed step begins, so nothing else marks the end."""
    claimed = client.post("/api/session").json()["session_id"]
    response = client.post(
        "/api/policy/upload-many",
        files=[("files", ("broken.pdf", b"%PDF-1.4 not really", "application/pdf"))],
        data={"insurer_id": "", "session_id": claimed},
    )
    assert response.status_code == 500

    history = client.get(f"/api/events/{claimed}/history").json()["events"]
    assert history[-1]["step"] == "read_failed"
    assert history[-1]["status"] == "failed"


def test_the_reader_is_told_something_they_can_act_on(client):
    """The exception names a temporary file on the server. That is for the log."""
    response = client.post(
        "/api/policy/upload-many",
        files=[("files", ("broken.pdf", b"%PDF-1.4 not really", "application/pdf"))],
        data={"insurer_id": ""},
    )
    assert response.status_code == 500
    message = response.json()["detail"]
    assert "password-protected" in message
    assert "/var/" not in message and ".pdf'" not in message
