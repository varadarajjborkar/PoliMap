"""The snapshot round trip that makes a stay survive.

Session rows here expire on a timer and a container restart takes the file with
them, so the server cannot be the durable copy of an admission tracked over
several days. The browser keeps a snapshot and hands it back. These tests cover
that handover, because the failure it prevents, a family losing five days of
recorded charges, is the worst thing this application can do.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def session_id(client) -> str:
    response = client.post(
        "/api/policy/manual",
        json={
            "sum_insured": 500000,
            "room_limit_type": "flat",
            "room_limit_amount": 5000,
            "copay_pct": 10,
        },
    )
    assert response.status_code == 200
    return response.json()["session_id"]


def snapshot_of(client, session_id: str) -> dict:
    response = client.get(f"/api/session/{session_id}/export")
    assert response.status_code == 200
    return response.json()["snapshot"]


def test_export_carries_the_compiled_policy(client, session_id):
    snapshot = snapshot_of(client, session_id)
    assert snapshot["policy"]["sum_insured"] == 500000
    assert snapshot["policy"]["copay_pct"] == 10


def test_import_restores_a_session_the_server_has_forgotten(client, session_id):
    snapshot = snapshot_of(client, session_id)

    client.delete(f"/api/session/{session_id}")
    assert client.get(f"/api/session/{session_id}").status_code == 404

    restored = client.post("/api/session/import", json={"snapshot": snapshot})
    assert restored.status_code == 200

    body = restored.json()
    assert body["policy"]["sum_insured"] == 500000
    assert body["policy"]["room_limit"]["daily_cap"] == 5000


def test_import_issues_a_fresh_id(client, session_id):
    """The old id may still be live elsewhere; reusing it would clobber it."""
    snapshot = snapshot_of(client, session_id)
    restored = client.post("/api/session/import", json={"snapshot": snapshot})

    new_id = restored.json()["session_id"]
    assert new_id != session_id
    assert client.get(f"/api/session/{new_id}").status_code == 200


def test_import_rewrites_the_journey_session_id(client, session_id):
    """A journey carrying a stale id would publish to a stream nobody reads."""
    hospitals = client.get("/api/reference").json()
    procedure = hospitals["procedures"][0]["code"]

    search = client.post(
        f"/api/search/{session_id}",
        json={"procedure_code": procedure, "lat": 12.9716, "lon": 77.5946,
              "city": "Bengaluru", "max_distance_km": 25},
    )
    assert search.status_code == 200
    options = search.json()["options"]
    if not options:
        pytest.skip("no hospital offers this procedure in range")

    started = client.post(
        f"/api/journey/{session_id}/start",
        json={
            "hospital_id": options[0]["hospital"]["id"],
            "procedure_code": procedure,
            "room_category": options[0]["room"]["category"],
        },
    )
    assert started.status_code == 200

    snapshot = snapshot_of(client, session_id)
    assert snapshot["journey"]["session_id"] == session_id

    restored = client.post("/api/session/import", json={"snapshot": snapshot}).json()
    new_id = restored["session_id"]

    rewritten = snapshot_of(client, new_id)
    assert rewritten["journey"]["session_id"] == new_id


def test_import_carries_recorded_charges(client, session_id):
    """The charges are the part nobody would ever re-enter."""
    reference = client.get("/api/reference").json()
    procedure = reference["procedures"][0]["code"]

    search = client.post(
        f"/api/search/{session_id}",
        json={"procedure_code": procedure, "lat": 12.9716, "lon": 77.5946,
              "city": "Bengaluru", "max_distance_km": 25},
    )
    options = search.json()["options"]
    if not options:
        pytest.skip("no hospital offers this procedure in range")

    client.post(
        f"/api/journey/{session_id}/start",
        json={
            "hospital_id": options[0]["hospital"]["id"],
            "procedure_code": procedure,
            "room_category": options[0]["room"]["category"],
        },
    )
    client.post(
        f"/api/journey/{session_id}/cost",
        data={"head": "pharmacy", "amount": "4200",
              "description": "day 2 medicines", "advance_day": "false"},
    )

    snapshot = snapshot_of(client, session_id)
    client.delete(f"/api/session/{session_id}")

    restored = client.post("/api/session/import", json={"snapshot": snapshot}).json()
    costs = restored["journey"]["costs"]
    assert [c["amount"] for c in costs] == [4200]
    assert costs[0]["description"] == "day 2 medicines"


def test_unreadable_snapshot_is_refused_in_plain_words(client):
    response = client.post("/api/session/import", json={"snapshot": {"junk": True}})
    assert response.status_code == 400
    assert "start a new one" in response.json()["detail"].lower()


def test_a_refused_import_leaves_no_session_behind(client):
    """The rebuild allocates before it parses; a failure must not leak the row."""
    before = client.get("/api/health").json()["active_sessions"]
    client.post("/api/session/import", json={"snapshot": {"junk": True}})
    assert client.get("/api/health").json()["active_sessions"] == before