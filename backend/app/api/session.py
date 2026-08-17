"""In-memory session store.

Everything a user is working on lives here: their compiled policy, the options
found for them, and their journey. Kept in process rather than in a database
because a session is short-lived working state, and because insurance data being
held only for as long as the tab is open is a reasonable default for a decision
support tool that never needed to keep it.

The datasets are loaded once at import and shared read-only.
"""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.config import GENERATED_DIR
from app.core.logging import get_logger
from app.schemas.hospital import Hospital, Insurer
from app.schemas.journey import JourneyState
from app.schemas.match import MatchResult
from app.schemas.policy import NormalizedPolicy
from app.schemas.procedure import Procedure

log = get_logger(__name__)

SESSION_LIMIT = 200


class DatasetMissing(RuntimeError):
    """The generated corpus has not been built yet."""


@dataclass
class Session:
    session_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    policy: NormalizedPolicy | None = None
    document_name: str = ""
    read_quality: float = 1.0
    needed_ocr: bool = False
    warnings: list[str] = field(default_factory=list)
    match: MatchResult | None = None
    journey: JourneyState | None = None
    insurer_id: str = ""

    def touch(self) -> None:
        self.created_at = datetime.now(UTC)


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
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sessions: dict[str, Session] = {}

    def create(self) -> Session:
        session = Session(session_id=uuid.uuid4().hex[:12])
        with self._lock:
            # Bounded so a long-running demo cannot grow without limit.
            if len(self._sessions) >= SESSION_LIMIT:
                oldest = min(self._sessions.values(), key=lambda s: s.created_at)
                self._sessions.pop(oldest.session_id, None)
            self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        with self._lock:
            session = self._sessions.get(session_id)
        if session:
            session.touch()
        return session

    def require(self, session_id: str) -> Session:
        session = self.get(session_id)
        if session is None:
            raise KeyError(session_id)
        return session

    def count(self) -> int:
        with self._lock:
            return len(self._sessions)


datasets = _Datasets()
sessions = _Sessions()
