"""Session persistence and the cleanup of what intake leaves on disk.

The point of persistence is that reloading the page does not throw away a
document that took a minute to read, so the tests are about survival across a
fresh store rather than about SQLite itself.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.api.store import (
    MemorySessionStore,
    Session,
    SqliteSessionStore,
    build_store,
)
from app.core import artifacts
from app.schemas.journey import JourneyStage, JourneyState
from app.schemas.phrasing import phrase
from app.schemas.policy import NormalizedPolicy, RoomLimit, RoomLimitBasis


def make_policy() -> NormalizedPolicy:
    return NormalizedPolicy(
        sum_insured=Decimal("500000"),
        room_limit=RoomLimit(
            basis=RoomLimitBasis.FLAT_PER_DAY, amount_per_day=Decimal("5000")
        ),
        copay_pct=Decimal("10"),
    )


@pytest.fixture
def sqlite_store(tmp_path):
    return SqliteSessionStore(tmp_path / "sessions.db")


@pytest.fixture(params=["memory", "sqlite"])
def store(request, tmp_path):
    return build_store(
        request.param, path=tmp_path / "s.db", ttl_minutes=720, limit=50
    )


# --- behaviour both stores must share --------------------------------------


def test_created_session_is_retrievable(store):
    session = store.create()
    assert store.get(session.session_id) is not None


def test_unknown_session_is_none(store):
    assert store.get("nosuchsession") is None


def test_saved_state_is_returned(store):
    session = store.create()
    session.policy = make_policy()
    session.document_name = "POL001.pdf"
    store.save(session)

    restored = store.get(session.session_id)
    assert restored is not None
    assert restored.document_name == "POL001.pdf"
    assert restored.policy is not None
    assert restored.policy.sum_insured == Decimal("500000")


def test_delete_removes_the_session(store):
    session = store.create()
    store.delete(session.session_id)
    assert store.get(session.session_id) is None


def test_count_tracks_live_sessions(store):
    before = store.count()
    a, b = store.create(), store.create()
    assert store.count() == before + 2
    store.delete(a.session_id)
    assert store.count() == before + 1
    store.delete(b.session_id)


# --- what only persistence buys --------------------------------------------


def test_session_survives_a_new_store_over_the_same_file(tmp_path):
    """The reload case: the process is gone, the user's work is not."""
    path = tmp_path / "sessions.db"

    first = SqliteSessionStore(path)
    session = first.create()
    session.policy = make_policy()
    session.journey = JourneyState(
        session_id=session.session_id,
        stage=JourneyStage.ADMITTED,
        hospital_name="Ashwin Multispeciality",
    )
    first.save(session)

    # A different store object over the same file stands in for a restart.
    second = SqliteSessionStore(path)
    restored = second.get(session.session_id)

    assert restored is not None
    assert restored.policy.sum_insured == Decimal("500000")
    assert restored.journey.stage is JourneyStage.ADMITTED
    assert restored.journey.hospital_name == "Ashwin Multispeciality"


def test_money_stays_decimal_through_a_round_trip(sqlite_store):
    """Rupees must not come back as floats; they get summed in a waterfall."""
    session = sqlite_store.create()
    session.policy = make_policy()
    sqlite_store.save(session)

    restored = sqlite_store.get(session.session_id)
    assert isinstance(restored.policy.sum_insured, Decimal)
    assert isinstance(restored.policy.copay_pct, Decimal)


def test_unreadable_row_is_dropped_rather_than_raised(sqlite_store):
    """A row from an older schema should read as "no session", not as a 500."""
    session = sqlite_store.create()
    with sqlite_store._connect() as conn:
        conn.execute(
            "UPDATE sessions SET payload = ? WHERE session_id = ?",
            ("{not json", session.session_id),
        )

    assert sqlite_store.get(session.session_id) is None
    assert sqlite_store.count() == 0


# --- eviction: the store must not grow without bound -----------------------


def test_expired_sessions_are_evicted(tmp_path):
    store = SqliteSessionStore(tmp_path / "s.db", ttl_minutes=60)
    stale = store.create()

    # Backdate the row past the lifetime, then trigger the eviction pass.
    old = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    with store._connect() as conn:
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
            (old, stale.session_id),
        )

    store.create()
    assert store.get(stale.session_id) is None


def test_row_cap_holds(tmp_path):
    store = SqliteSessionStore(tmp_path / "s.db", limit=5)
    for _ in range(12):
        store.create()
    assert store.count() <= 5


def test_memory_store_cap_holds():
    store = MemorySessionStore(limit=3)
    for _ in range(10):
        store.create()
    assert store.count() <= 3


def test_touch_keeps_an_active_session_alive(sqlite_store):
    session = sqlite_store.create()
    first = session.updated_at
    time.sleep(0.01)
    fetched = sqlite_store.get(session.session_id)
    assert fetched.updated_at > first


# --- page images ------------------------------------------------------------


def test_purge_removes_a_sessions_page_images(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts.settings, "uploads_dir", tmp_path)

    directory = artifacts.page_dir("abc123")
    (directory / "page0.png").write_bytes(b"not really a png")
    assert artifacts.disk_usage_bytes() > 0

    artifacts.purge("abc123")
    assert not directory.exists()
    assert artifacts.disk_usage_bytes() == 0


def test_purge_is_safe_when_there_is_nothing_to_purge(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts.settings, "uploads_dir", tmp_path)
    artifacts.purge("never-existed")


def test_sweep_removes_only_stale_directories(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts.settings, "uploads_dir", tmp_path)

    stale = artifacts.page_dir("old")
    (stale / "p0.png").write_bytes(b"x")
    fresh = artifacts.page_dir("new")
    (fresh / "p0.png").write_bytes(b"x")

    import os
    long_ago = time.time() - (60 * 60 * 48)
    os.utime(stale, (long_ago, long_ago))

    removed = artifacts.sweep(max_age_minutes=60)

    assert removed == 1
    assert not stale.exists()
    assert fresh.exists()


def test_session_delete_also_purges_images(tmp_path, monkeypatch):
    """Ending a session must take the document pictures with it."""
    from app.api.session import sessions

    monkeypatch.setattr(artifacts.settings, "uploads_dir", tmp_path)
    sessions.use(MemorySessionStore())

    session = sessions.create()
    directory = artifacts.page_dir(session.session_id)
    (directory / "p0.png").write_bytes(b"x")

    sessions.delete(session.session_id)

    assert sessions.get(session.session_id) is None
    assert not directory.exists()


def test_session_json_round_trip_is_lossless():
    session = Session(session_id="deadbeef0001")
    session.policy = make_policy()
    session.warnings = [phrase("doc.hard_to_read", "Read from a photograph")]
    session.needed_ocr = True
    session.read_quality = 0.81

    restored = Session.from_json(session.to_json())

    assert restored.session_id == session.session_id
    assert restored.warnings == session.warnings
    assert restored.needed_ocr is True
    assert restored.read_quality == pytest.approx(0.81)
    assert restored.policy.room_limit.amount_per_day == Decimal("5000")
