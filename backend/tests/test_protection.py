"""What the app refuses to do, and to whom.

Every case here is one that was possible before it was written. They are worth
having as tests rather than as a note in a document because the failure mode of
a wall is silence: nothing looks different when one stops working, right up
until somebody walks through it.
"""

from __future__ import annotations

import fitz
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.api.store import _new_id, is_well_formed
from app.core.config import settings
from app.core.limits import ASK, HEAVY, READ, WRITE, Bucket, RateLimiter, client_key
from app.core.middleware import bucket_for
from app.main import app

client = TestClient(app)


@pytest.fixture
def rate_limited():
    """Turn the limiter back on for the tests that are about the limiter."""
    from app.core.limits import limiter

    limiter.reset()
    settings.rate_limit_enabled = True
    yield limiter
    settings.rate_limit_enabled = False
    limiter.reset()


# --- the session id is the only secret there is ---------------------------


def test_a_session_id_is_long_enough_to_be_a_secret():
    # There is no password anywhere in this app, so the id is the whole of the
    # access control. Twelve hex characters was 48 bits.
    ident = _new_id()
    assert len(ident) >= 32
    assert is_well_formed(ident)


def test_ids_do_not_repeat():
    assert len({_new_id() for _ in range(2000)}) == 2000


@pytest.mark.parametrize(
    "hostile",
    [
        "../../../etc/passwd",
        "..",
        ".",
        "../uploads",
        "sess/../../secret",
        "a" * 200,
        "",
        "abc",
        "has spaces",
        "semi;colon",
        "null\x00byte",
    ],
)
def test_an_id_that_could_never_have_been_issued_is_refused(hostile):
    assert not is_well_formed(hostile)


@pytest.mark.parametrize(
    "path",
    [
        "/api/session/{}",
        "/api/policy/{}",
        "/api/journey/{}",
        "/api/events/{}/history",
    ],
)
def test_traversal_in_a_session_id_reaches_nothing(path):
    for hostile in ("../../../etc/passwd", "..%2f..%2fetc%2fpasswd", "..", "*"):
        response = client.get(path.format(hostile))
        assert response.status_code in (404, 405), (path, hostile)


def test_a_wrong_shape_and_a_wrong_id_answer_the_same_way():
    """Otherwise the difference is a hint about how to guess better."""
    malformed = client.get("/api/session/!!!")
    unknown = client.get(f"/api/session/{_new_id()}")
    assert malformed.status_code == unknown.status_code == 404
    assert malformed.json()["detail"] == unknown.json()["detail"]


# --- one person's stay is not another's -----------------------------------


def test_the_event_stream_needs_a_session_that_exists():
    # This used to accept any string, which made it the one place an unlimited
    # number of connections could be held open against ids never issued.
    assert client.get("/api/events/does-not-exist/history").status_code == 404
    assert client.get(f"/api/events/{_new_id()}/history").status_code == 404


def test_an_events_history_is_only_its_own_session():
    a = client.post("/api/session").json()["session_id"]
    b = client.post("/api/session").json()["session_id"]
    assert client.get(f"/api/events/{a}/history").json()["events"] == []
    assert client.get(f"/api/events/{b}/history").json()["events"] == []


def test_a_receipt_id_is_matched_not_globbed():
    """`*` in a glob pattern reads a file without knowing its name."""
    session = client.post("/api/session").json()["session_id"]
    for probe in ("*", "?", "*.pdf", "[a-z]*", "../../../etc/passwd"):
        response = client.get(f"/api/journey/{session}/cost/{probe}/receipt")
        # 405 for `?`, which ends the path and turns the request into one for
        # a route that does not take GET. Either way no file is served.
        assert response.status_code in (404, 405), probe


# --- a document cannot ask for more work than it is worth -----------------


def _pdf(pages: int = 1, width: float = 595, height: float = 842) -> bytes:
    doc = fitz.open()
    for _ in range(pages):
        doc.new_page(width=width, height=height)
    return doc.tobytes(deflate=True)


def test_a_small_file_cannot_declare_thousands_of_pages():
    # 5000 blank pages compress to under a megabyte, and every one of them
    # would be rasterised and put through OCR: hours of a core, asked for in
    # one request that the uploader does not even have to wait for.
    bomb = _pdf(pages=settings.max_document_pages + 40)
    assert len(bomb) < 2 * 1024 * 1024

    session = client.post("/api/session").json()["session_id"]
    response = client.post(
        "/api/policy/upload",
        files={"file": ("bomb.pdf", bomb, "application/pdf")},
        data={"session_id": session},
    )
    assert response.status_code == 400
    assert "pages" in response.json()["detail"]


def test_an_ordinary_document_is_nowhere_near_the_ceiling():
    assert settings.max_document_pages >= 40


def _page(width: float, height: float):
    """One page in its own document.

    Adding a page to a document invalidates handles to the pages already in it,
    so two sizes cannot be held at once from one document.
    """
    doc = fitz.open()
    doc.new_page(width=width, height=height)
    return doc[0]


def test_an_ordinary_page_is_read_at_full_resolution():
    from app.pipeline.s0_intake.intake import RASTER_DPI, _raster_dpi

    assert _raster_dpi(_page(595, 842)) == RASTER_DPI          # A4
    assert _raster_dpi(_page(612, 792)) == RASTER_DPI          # US Letter


def test_a_large_scan_gives_up_resolution_rather_than_being_refused():
    """A0 at 300 DPI is 139 megapixels. It is still a real document somebody
    might scan, so the resolution moves and the page is still read."""
    from app.pipeline.s0_intake.intake import RASTER_DPI, _raster_dpi

    a0 = _page(2384, 3370)
    dpi = _raster_dpi(a0)
    assert 60 <= dpi < RASTER_DPI
    megapixels = (2384 / 72 * dpi) * (3370 / 72 * dpi) / 1_000_000
    assert megapixels <= settings.max_page_megapixels * 1.01


def test_a_page_the_size_of_a_wall_is_refused_outright():
    """200 inches square at 300 DPI is 60000 by 60000 pixels: eleven gigabytes
    asked for by about a kilobyte of file. No resolution both fits the ceiling
    and leaves anything readable, so there is nothing to concede."""
    from app.pipeline.s0_intake.intake import DocumentTooLarge, _raster_dpi

    with pytest.raises(DocumentTooLarge):
        _raster_dpi(_page(14400, 14400))


def test_an_image_that_claims_to_be_enormous_is_refused_before_it_is_decoded(tmp_path):
    from app.pipeline.s0_intake.intake import DocumentTooLarge, _refuse_oversized_image

    # A blank image compresses to almost nothing and decodes to gigabytes.
    side = int((settings.max_image_megapixels * 1_000_000) ** 0.5) + 2000
    path = tmp_path / "bomb.png"
    Image.new("L", (side, side)).save(path, optimize=True)
    assert path.stat().st_size < 5 * 1024 * 1024

    with pytest.raises(DocumentTooLarge):
        _refuse_oversized_image(path)


def test_a_photograph_from_a_phone_is_not_refused(tmp_path):
    from app.pipeline.s0_intake.intake import _refuse_oversized_image

    path = tmp_path / "photo.jpg"
    Image.new("RGB", (4032, 3024), "white").save(path)
    _refuse_oversized_image(path)  # 12 megapixels, no complaint


# --- a body is read only once it could be what it says it is --------------


def test_an_oversized_upload_is_refused_on_the_wire():
    session = client.post("/api/session").json()["session_id"]
    response = client.post(
        "/api/policy/upload",
        files={"file": ("big.pdf", b"%PDF-1.4\n" + b"\0" * (30 * 1024 * 1024))},
        data={"session_id": session},
    )
    assert response.status_code == 413


def test_a_json_body_is_held_to_a_much_smaller_ceiling():
    """A megabyte of JSON is not an upload, it is work for the parser."""
    response = client.post(
        "/api/session/import",
        content=b'{"snapshot": {"x": "' + b"A" * (2 * 1024 * 1024) + b'"}}',
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413


def test_an_honest_json_body_still_gets_through():
    response = client.post(
        "/api/help/ask", json={"message": "what is a room limit", "screen": "cover"}
    )
    assert response.status_code == 200


# --- how often, and by whom ------------------------------------------------


def test_reading_a_document_is_priced_as_expensive():
    for path in (
        "/api/policy/upload",
        "/api/policy/upload-many",
        "/api/journey/abc/bill",
        "/api/health/providers",
        "/api/session/abc/report.pdf",
        "/api/session/import",
    ):
        assert bucket_for("POST", path) is HEAVY, path


def test_the_help_desk_is_priced_for_a_conversation():
    # A model call each, but somebody legitimately asks several in a row.
    assert bucket_for("POST", "/api/help/ask") is ASK
    assert ASK.burst >= 8


def test_what_a_caregiver_does_repeatedly_is_not_priced_as_expensive():
    """Entering the day's charges at a counter is several actions in a minute.

    Pricing those as expensive is not a protected app, it is a broken one: the
    limit would be met with the day half entered.
    """
    for path in (
        "/api/journey/abc/cost",
        "/api/search/abc",
        "/api/policy/manual",
        "/api/journey/abc/advance",
        "/api/policy/abc/field",
    ):
        assert bucket_for("POST", path) is WRITE, path


def test_a_days_charges_fit_inside_one_allowance():
    # A long admission is a dozen or so charges, entered in one sitting.
    assert WRITE.burst >= 25


def test_reading_reference_data_is_not():
    assert bucket_for("GET", "/api/reference") is READ
    assert bucket_for("GET", "/api/health") is READ


def test_the_event_stream_is_not_metered_by_the_second():
    # It is one connection held open, so a per-second allowance means nothing.
    # It is bounded by how many can be open at once instead.
    assert bucket_for("GET", "/api/events/abc") is None


def test_a_bucket_refills_rather_than_resetting_on_a_boundary():
    bucket = Bucket("t", rate=10.0, burst=3)
    limiter = RateLimiter()
    assert [limiter.take("ip", bucket) for _ in range(4)] == [True, True, True, False]
    # A fixed window would let the whole burst through again the instant the
    # window turned. A bucket hands back one token at a time.
    import time

    time.sleep(0.15)
    assert limiter.take("ip", bucket) is True
    assert limiter.take("ip", bucket) is False


def test_one_caller_running_out_does_not_stop_another():
    bucket = Bucket("t", rate=0.0001, burst=1)
    limiter = RateLimiter()
    assert limiter.take("1.1.1.1", bucket) is True
    assert limiter.take("1.1.1.1", bucket) is False
    assert limiter.take("2.2.2.2", bucket) is True


def test_the_limiter_cannot_be_grown_without_bound():
    bucket = Bucket("t", rate=1.0, burst=1)
    limiter = RateLimiter()
    limiter.MAX_ENTRIES = 100
    for i in range(500):
        limiter.take(f"10.0.0.{i}", bucket)
    assert len(limiter._state) <= limiter.MAX_ENTRIES


def test_a_forwarded_address_is_trusted_only_where_a_proxy_really_is():
    """Otherwise anyone can mint themselves a fresh allowance per request."""
    headers = {"x-forwarded-for": "9.9.9.9, 10.0.0.1"}
    socket = ("172.16.0.4", 51234)

    assert client_key(socket, headers, trust_proxy=False) == "172.16.0.4"
    assert client_key(socket, headers, trust_proxy=True) == "9.9.9.9"


def test_the_limit_actually_bites(rate_limited):
    codes = [client.get("/api/reference").status_code for _ in range(READ.burst + 15)]
    assert 429 in codes
    refused = client.get("/api/reference")
    assert refused.status_code == 429
    assert "Retry-After" in refused.headers


def test_being_refused_still_says_why_in_a_sentence(rate_limited):
    for _ in range(READ.burst + 15):
        client.get("/api/reference")
    body = client.get("/api/reference").json()
    assert "detail" in body
    assert body["detail"][0].isupper()


# --- what the browser is told to do with what we send ---------------------


def test_every_response_is_marked_as_data_and_not_a_document():
    headers = client.get("/api/health").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in headers["content-security-policy"]
    assert "default-src 'none'" in headers["content-security-policy"]


def test_a_refusal_carries_the_same_headers_as_an_answer():
    """A 404 is still a response a browser will act on."""
    headers = client.get("/api/session/!!!").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"


def test_nothing_promises_https_from_a_server_that_does_not_speak_it():
    # Sent from a development server it would pin localhost to HTTPS in the
    # developer's browser for a year.
    assert not settings.tls_terminated
    assert "strict-transport-security" not in client.get("/api/health").headers


def test_a_managed_host_is_recognised_without_being_told(monkeypatch):
    """The setting that fails silently should not have to be remembered.

    Behind a proxy with nothing configured, every request arrives from the
    proxy's address, everybody shares one rate-limit allowance, and the first
    few users lock out the rest. Nothing errors, so nobody finds out until
    people are being refused.
    """
    for platform in ("RENDER", "RAILWAY_ENVIRONMENT", "FLY_APP_NAME", "DYNO"):
        monkeypatch.setenv(platform, "true")
        assert settings.on_managed_host, platform
        assert settings.proxy_trusted, platform
        assert settings.tls_terminated, platform
        monkeypatch.delenv(platform)

    assert not settings.on_managed_host
    assert not settings.proxy_trusted


def test_saying_so_explicitly_still_wins(monkeypatch):
    """Detection is a default, not a decision taken out of anybody's hands."""
    from app.core.config import Settings

    monkeypatch.setenv("RENDER", "true")
    assert Settings(trust_proxy=False).proxy_trusted is False
    assert Settings(behind_tls=False).tls_terminated is False

    monkeypatch.delenv("RENDER")
    assert Settings(trust_proxy=True).proxy_trusted is True


def test_the_api_reference_is_not_served_unless_it_was_asked_for():
    assert not settings.enable_docs
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 404, path


def test_an_unknown_origin_is_not_allowed_to_call_this():
    response = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_the_frontend_origin_is():
    response = client.get(
        "/api/health", headers={"Origin": "http://localhost:5173"}
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_credentials_are_not_invited(monkeypatch):
    """There are no cookies here, so allowing them would widen the surface
    without buying anything."""
    response = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert "access-control-allow-credentials" not in response.headers


# --- errors say what happened without saying how it works -----------------


def test_a_failure_does_not_hand_back_the_inside_of_the_program():
    session = client.post("/api/session").json()["session_id"]
    response = client.post(
        "/api/policy/upload",
        files={"file": ("x.pdf", b"not a pdf at all", "application/pdf")},
        data={"session_id": session},
    )
    body = response.text
    for leak in ("Traceback", "File \"/", "app/pipeline", "fitz", ".venv"):
        assert leak not in body, leak


def test_a_saved_stay_that_cannot_be_read_is_refused_plainly():
    response = client.post("/api/session/import", json={"snapshot": {"bad": True}})
    assert response.status_code == 400
    assert "Traceback" not in response.text


def _proxy_warnings(trust_proxy: bool, *header_sets) -> list[str]:
    """What the guard says when requests arrive with the given headers."""
    from structlog.testing import capture_logs

    from app.core.middleware import RequestGuard

    guard = RequestGuard(None, trust_proxy=trust_proxy)
    with capture_logs() as entries:
        for headers in header_sets:
            guard._warn_once_about_the_proxy(headers)
    return [e["event"] for e in entries if "TRUST_PROXY" in e.get("event", "")]


def test_a_proxy_in_front_with_nothing_configured_says_so():
    """The misconfiguration that looks like the app being broken.

    Behind a proxy with TRUST_PROXY unset, every request arrives from the
    proxy's address, so everybody shares one allowance and the first busy user
    locks out the rest. Nothing errors, it just starts refusing people, which
    is why it has to announce itself rather than wait to be noticed.
    """
    forwarded = {"x-forwarded-for": "9.9.9.9"}
    said = _proxy_warnings(False, forwarded, forwarded, forwarded)
    assert len(said) == 1, "said once, not on every request"


def test_nothing_is_said_when_the_deployment_is_configured():
    assert _proxy_warnings(True, {"x-forwarded-for": "9.9.9.9"}) == []


def test_nothing_is_said_when_there_is_no_proxy():
    assert _proxy_warnings(False, {}, {"host": "localhost"}) == []
