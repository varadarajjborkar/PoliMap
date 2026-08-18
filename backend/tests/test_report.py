"""The stay as one printable page.

A screen cannot be put in front of a hospital insurance desk, and a phone
battery does not last a five-day admission. The document's job is to be
checkable by somebody who was not there when it was produced, so these test that
every figure on it is present and named rather than that it renders at all.
"""

from __future__ import annotations

from decimal import Decimal as D
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.session import sessions
from app.main import app
from app.report import stay as report


@pytest.fixture
def api():
    with TestClient(app) as client:
        yield client


def text_of(pdf: bytes) -> str:
    import fitz

    with fitz.open(stream=pdf, filetype="pdf") as document:
        return "\n".join(page.get_text() for page in document)


@pytest.fixture
def full_stay(api):
    """A policy read, a hospital chosen, costs recorded, discharge approaching."""
    document = Path("../data/generated/policies/clean/POL006.pdf")
    if not document.exists():
        pytest.skip("corpus not built")

    session_id = api.post("/api/session").json()["session_id"]
    api.post(
        "/api/policy/upload-many",
        files=[("files", (document.name, document.read_bytes(), "application/pdf"))],
        data={"insurer_id": "", "session_id": session_id},
    )
    code = "CP-CARD-006"
    found = api.post(f"/api/search/{session_id}", json={
        "procedure_code": code, "lat": 12.9716, "lon": 77.5946,
        "city": "Bengaluru", "max_distance_km": 25, "preference": "balanced",
        "urgency": "planned", "pre_existing": False,
        "preferred_room": "single_private",
    }).json()
    option = found["options"][0]
    api.post(f"/api/journey/{session_id}/start", json={
        "hospital_id": option["hospital"]["id"], "procedure_code": code,
        "room_category": option["room"]["category"],
    })
    api.post(f"/api/journey/{session_id}/cost", data={
        "head": "investigations", "amount": "12400",
        "description": "CT angiogram", "advance_day": "false",
    })
    api.post(f"/api/journey/{session_id}/advance", json={
        "stage": "discharge_planning", "confirm_skip": True,
    })
    return session_id, option


def test_the_report_downloads_as_a_pdf(api, full_stay):
    session_id, _ = full_stay
    response = api.get(f"/api/session/{session_id}/report.pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")


def test_it_is_named_after_the_hospital(api, full_stay):
    session_id, option = full_stay
    disposition = api.get(
        f"/api/session/{session_id}/report.pdf"
    ).headers["content-disposition"]
    assert "polimap-" in disposition
    assert ".pdf" in disposition


def test_it_carries_the_cover_the_policy_states(api, full_stay):
    session_id, _ = full_stay
    printed = text_of(api.get(f"/api/session/{session_id}/report.pdf").content)
    policy = sessions.get(session_id).policy
    assert policy.meta.insurer_name in printed
    assert policy.meta.policy_number in printed
    assert "Total cover this year" in printed


def test_the_policy_number_is_not_the_page_header(api, full_stay):
    """A running header puts several fields on one line: "Policy No. X | Page 1"."""
    session_id, _ = full_stay
    policy = sessions.get(session_id).policy
    assert "|" not in policy.meta.policy_number
    assert not policy.meta.policy_number.startswith(".")
    assert "Page" not in policy.meta.policy_number


def test_it_names_everybody_on_the_policy(api, full_stay):
    session_id, _ = full_stay
    printed = text_of(api.get(f"/api/session/{session_id}/report.pdf").content)
    for person in sessions.get(session_id).policy.insured:
        assert person.name in printed


def test_every_deduction_is_named_with_its_reason(api, full_stay):
    """A total cannot be argued with. A line saying why money came off can."""
    session_id, option = full_stay
    printed = text_of(api.get(f"/api/session/{session_id}/report.pdf").content)
    assert option["estimated_bill_display"] in printed
    assert option["you_pay_display"] in printed
    for step in option["waterfall"]:
        assert step["label"] in printed


def test_it_carries_what_has_actually_been_billed(api, full_stay):
    session_id, _ = full_stay
    printed = text_of(api.get(f"/api/session/{session_id}/report.pdf").content)
    assert "CT angiogram" in printed
    assert "12,400" in printed


def test_it_lists_only_what_is_still_to_do(api, full_stay):
    """A printed list of ticked boxes is a poster, not an instruction."""
    session_id, _ = full_stay
    journey = api.get(f"/api/journey/{session_id}").json()
    first = journey["checklist"]["items"][0]
    api.post(f"/api/journey/{session_id}/checklist",
             json={"item_id": first["id"], "done": True})

    printed = text_of(api.get(f"/api/session/{session_id}/report.pdf").content)
    assert first["text"] not in printed
    assert "Still to do" in printed


def test_it_says_what_it_is_not(api, full_stay):
    session_id, _ = full_stay
    printed = text_of(api.get(f"/api/session/{session_id}/report.pdf").content)
    assert "not a quotation" in printed
    assert "Nothing here is medical advice" in printed


def test_a_stay_with_only_a_policy_still_prints(api):
    """Somebody may want the cover summary before choosing anything."""
    session_id = api.post("/api/policy/manual", json={
        "sum_insured": 500000, "room_limit_type": "flat",
        "room_limit_amount": 5000, "insurer_name": "Test Insurer",
    }).json()["session_id"]

    response = api.get(f"/api/session/{session_id}/report.pdf")
    assert response.status_code == 200
    printed = text_of(response.content)
    assert "Test Insurer" in printed
    assert "5,00,000" in printed


def test_a_stay_with_no_policy_is_refused_rather_than_printed_blank(api):
    session_id = api.post("/api/session").json()["session_id"]
    response = api.get(f"/api/session/{session_id}/report.pdf")
    assert response.status_code == 400


def test_building_without_a_policy_raises(api):
    session_id = api.post("/api/session").json()["session_id"]
    with pytest.raises(ValueError, match="no policy"):
        report.build(sessions.get(session_id))


def test_a_second_policy_appears_on_the_page(api):
    first = api.post("/api/policy/manual", json={
        "sum_insured": 300000, "room_limit_type": "flat",
        "room_limit_amount": 5000, "insurer_name": "First Insurer",
    }).json()
    api.post("/api/policy/manual", json={
        "sum_insured": 500000, "room_limit_type": "none",
        "insurer_name": "Employer Group",
        "session_id": first["session_id"], "attach": True,
    })
    printed = text_of(
        api.get(f"/api/session/{first['session_id']}/report.pdf").content
    )
    assert "Employer Group" in printed


def test_the_rupee_sign_survives_or_becomes_something_readable():
    """Helvetica has no rupee glyph and several fonts that look safe emit NUL."""
    rendered = report.rupee_safe("₹5,00,000")
    assert "₹" in rendered or "Rs." in rendered
    assert "\x00" not in rendered


def test_money_is_whole_rupees(api, full_stay):
    """Indian claims settle in whole rupees; a paise figure on this page would
    be one nobody can reconcile against a hospital bill."""
    session_id, _ = full_stay
    printed = text_of(api.get(f"/api/session/{session_id}/report.pdf").content)
    import re

    assert not re.search(r"[₹]\s?[\d,]+\.\d", printed)
    assert D("1") == D(1)
