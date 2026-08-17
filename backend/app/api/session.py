"""Session state and the shared reference datasets.

A session is everything a user is working on: their compiled policy, the options
found for them, and their journey. Where those rows live is decided in
`store.py`; this module holds the accessor the API talks to and the read-only
corpus that every session shares.

The datasets are loaded once on first use and shared read-only.
"""

from __future__ import annotations

import json
import threading
from typing import Any

from app.api.store import Session, SessionStore, build_store
from app.core import artifacts
from app.core.config import GENERATED_DIR, settings
from app.core.logging import get_logger
from app.schemas.hospital import Hospital, Insurer
from app.schemas.procedure import Procedure

log = get_logger(__name__)

__all__ = ["DatasetMissing", "Session", "datasets", "sessions"]


class DatasetMissing(RuntimeError):
    """The generated corpus has not been built yet."""


class _Datasets:
    """Lazily loaded, process-wide corpus."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._hospitals: list[Hospital] | None = None
        self._procedures: dict[str, Procedure] | None = None
        self._insurers: list[Insurer] | None = None

    def _load(self, name: str) -> Any:
        path = GENERATED_DIR / f"{name}.json"
        if not path.exists():
            raise DatasetMissing(
                f"{path.name} not found. Build the corpus first:\n"
                f"    python -m datagen.build_all"
            )
        return json.loads(path.read_text(encoding="utf-8"))

    @property
    def hospitals(self) -> list[Hospital]:
        with self._lock:
            if self._hospitals is None:
                self._hospitals = [Hospital(**h) for h in self._load("hospitals")]
                log.info("loaded hospitals", count=len(self._hospitals))
            return self._hospitals

    @property
    def procedures(self) -> dict[str, Procedure]:
        with self._lock:
            if self._procedures is None:
                self._procedures = {
                    p["code"]: Procedure(**p) for p in self._load("procedures")
                }
                log.info("loaded procedures", count=len(self._procedures))
            return self._procedures

    @property
    def insurers(self) -> list[Insurer]:
        with self._lock:
            if self._insurers is None:
                self._insurers = [Insurer(**i) for i in self._load("insurers")]
            return self._insurers

    @property
    def is_built(self) -> bool:
        return (GENERATED_DIR / "hospitals.json").exists()

    def cities(self) -> list[dict[str, Any]]:
        seen: dict[str, dict[str, Any]] = {}
        for hospital in self.hospitals:
            entry = seen.setdefault(
                hospital.city,
                {"city": hospital.city, "state": hospital.state, "count": 0,
                 "lat": 0.0, "lon": 0.0},
            )
            entry["count"] += 1
            entry["lat"] += hospital.location.lat
            entry["lon"] += hospital.location.lon
        for entry in seen.values():
            # Centroid, used as the default search origin for that city.
            entry["lat"] = round(entry["lat"] / entry["count"], 6)
            entry["lon"] = round(entry["lon"] / entry["count"], 6)
        return sorted(seen.values(), key=lambda c: -c["count"])


class _Sessions:
    """Facade over whichever store is configured.

    The store is built on first use rather than at import so that a test can
    point the settings at a temporary database, and so that importing the app
    never creates a file as a side effect.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: SessionStore | None = None

    @property
    def store(self) -> SessionStore:
        with self._lock:
            if self._store is None:
                self._store = build_store(
                    settings.session_store.value,
                    path=settings.session_db_path,
                    ttl_minutes=settings.session_ttl_minutes,
                    limit=settings.session_limit,
                )
            return self._store

    def use(self, store: SessionStore) -> None:
        """Swap the store. For tests and for explicit wiring at startup."""
        with self._lock:
            self._store = store

    def create(self) -> Session:
        return self.store.create()

    def get(self, session_id: str) -> Session | None:
        return self.store.get(session_id)

    def require(self, session_id: str) -> Session:
        session = self.get(session_id)
        if session is None:
            raise KeyError(session_id)
        return session

    def save(self, session: Session) -> Session:
        """Persist changes. A no-op for the memory store, a write for SQLite."""
        self.store.save(session)
        return session

    def delete(self, session_id: str) -> None:
        """Forget a session and the page images read for it.

        The images are the larger of the two by far, and they are pictures of
        someone's insurance document, so they go at the same moment the row
        does rather than waiting for the next sweep.
        """
        self.store.delete(session_id)
        artifacts.purge(session_id)

    def count(self) -> int:
        return self.store.count()

    @property
    def kind(self) -> str:
        return self.store.kind


datasets = _Datasets()
sessions = _Sessions()
