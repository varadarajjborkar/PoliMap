"""Where a user's working state lives between requests.

A session holds the compiled policy, the options found for it, and the journey.
Two stores implement the same interface:

* `MemorySessionStore` keeps them in a dict. Fast, isolated, and what the tests
  use, but everything is lost when the process restarts and nothing is shared
  between processes.
* `SqliteSessionStore` writes them to a single file. A restart no longer drops
  the tab the user had open, and every worker in a deployment reads the same
  rows, which is the difference between the app working behind one process and
  working behind several.

Persistence is possible at all because every piece of session state is a
Pydantic model that round trips through JSON without loss, decimals included.
Rupee amounts stay decimals rather than becoming floats, which matters when they
are later summed in a claim waterfall.
"""

from __future__ import annotations

import json
import re
import secrets
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

from app.core.logging import get_logger
from app.schemas.bill import BillReview
from app.schemas.journey import JourneyState
from app.schemas.match import MatchResult
from app.schemas.phrasing import Phrase
from app.schemas.policy import NormalizedPolicy

log = get_logger(__name__)


@dataclass
class Session:
    session_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    policy: NormalizedPolicy | None = None
    document_name: str = ""
    read_quality: float = 1.0
    needed_ocr: bool = False
    warnings: list[Phrase] = field(default_factory=list)
    match: MatchResult | None = None
    journey: JourneyState | None = None
    insurer_id: str = ""
    clarification_rounds: int = 0
    """How many questions this session has already put to the user. Bounded, so
    the loop cannot keep asking and keep costing."""

    pre_existing: bool | None = None
    """Whether the condition being treated existed before the policy did. Not
    in any document; only the patient knows, and it decides whether a
    pre-existing waiting period applies to them."""
    accident: bool = False
    """Whether this admission follows accidental injury, which the initial
    waiting period does not apply to."""
    patient_index: int | None = None
    """Which of the people named on the policy is being admitted."""

    second_policy: NormalizedPolicy | None = None
    """A second policy covering the same admission.

    Very common in India: an employer's group cover beside a personal policy,
    or a base policy with a top-up above it. Held separately rather than merged
    into the first, because they settle in sequence against their own terms and
    a merged policy would be one that exists nowhere."""

    bill_review: BillReview | None = None
    """The final bill, read and checked. Kept on the session rather than
    recomputed, because the document it came from is not kept: a hospital bill
    names the patient, the treatment and the ward, and holding the page after
    the answer has been taken off it buys nothing."""

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC)

    # --- serialisation ----------------------------------------------------

    def to_json(self) -> str:
        return json.dumps(
            {
                "session_id": self.session_id,
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
                "document_name": self.document_name,
                "read_quality": self.read_quality,
                "needed_ocr": self.needed_ocr,
                "warnings": [w.model_dump() for w in self.warnings],
                "insurer_id": self.insurer_id,
                "clarification_rounds": self.clarification_rounds,
                "pre_existing": self.pre_existing,
                "accident": self.accident,
                "patient_index": self.patient_index,
                "second_policy": (
                    self.second_policy.model_dump(mode="json")
                    if self.second_policy else None
                ),
                "policy": self.policy.model_dump(mode="json") if self.policy else None,
                "match": self.match.model_dump(mode="json") if self.match else None,
                "journey": (
                    self.journey.model_dump(mode="json") if self.journey else None
                ),
                "bill_review": (
                    self.bill_review.model_dump(mode="json")
                    if self.bill_review else None
                ),
            }
        )

    @classmethod
    def from_json(cls, raw: str) -> Session:
        data: dict[str, Any] = json.loads(raw)
        return cls(
            session_id=data["session_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            document_name=data.get("document_name", ""),
            read_quality=data.get("read_quality", 1.0),
            needed_ocr=data.get("needed_ocr", False),
            warnings=[Phrase.model_validate(w) for w in data.get("warnings", [])],
            insurer_id=data.get("insurer_id", ""),
            clarification_rounds=data.get("clarification_rounds", 0),
            pre_existing=data.get("pre_existing"),
            accident=data.get("accident", False),
            patient_index=data.get("patient_index"),
            second_policy=(
                NormalizedPolicy.model_validate(data["second_policy"])
                if data.get("second_policy") else None
            ),
            policy=(
                NormalizedPolicy.model_validate(data["policy"])
                if data.get("policy") else None
            ),
            match=(
                MatchResult.model_validate(data["match"])
                if data.get("match") else None
            ),
            journey=(
                JourneyState.model_validate(data["journey"])
                if data.get("journey") else None
            ),
            bill_review=(
                BillReview.model_validate(data["bill_review"])
                if data.get("bill_review") else None
            ),
        )


class SessionStore(Protocol):
    """What the API needs from a session store, and nothing more."""

    kind: str

    def create(self) -> Session: ...
    def get(self, session_id: str) -> Session | None: ...
    def save(self, session: Session) -> None: ...
    def delete(self, session_id: str) -> None: ...
    def count(self) -> int: ...


# The id is the only thing standing between a stay and anybody else, because
# there is no account and no password by design. That makes it a secret, and it
# was being cut to twelve hex characters: 48 bits, which is short enough to be
# worth attacking and short enough for two to collide once traffic is real.
# 32 URL-safe characters is 192 bits, still fits in a path segment, and costs
# nothing. `secrets` rather than `uuid4` because the point is unguessability
# rather than uniqueness, and only one of the two says so.
ID_BYTES = 24
_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


def _new_id() -> str:
    return secrets.token_urlsafe(ID_BYTES)


def is_well_formed(session_id: str) -> bool:
    """Whether a string could be one of our ids at all.

    Session ids name directories holding page images, so a lookup miss is not
    the only thing that must stop a hostile one: this is checked before the id
    reaches any store or any path, so a traversal attempt is refused on its
    shape rather than on the accident of finding no such session.
    """
    return bool(_ID_PATTERN.match(session_id))


class MemorySessionStore:
    kind = "memory"

    def __init__(self, limit: int = 500) -> None:
        self._limit = limit
        self._lock = threading.Lock()
        self._sessions: dict[str, Session] = {}

    def create(self) -> Session:
        session = Session(session_id=_new_id())
        with self._lock:
            # Bounded so a long running instance cannot grow without limit.
            while len(self._sessions) >= self._limit:
                oldest = min(self._sessions.values(), key=lambda s: s.updated_at)
                self._sessions.pop(oldest.session_id, None)
            self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is not None:
            session.touch()
        return session

    def save(self, session: Session) -> None:
        session.touch()
        with self._lock:
            self._sessions[session.session_id] = session

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def count(self) -> int:
        with self._lock:
            return len(self._sessions)


class SqliteSessionStore:
    """Session state in a single SQLite file.

    A connection is opened per call rather than shared. SQLite is quick to open,
    the alternative is a connection pool guarded across the thread pool that
    requests already run in, and the write volume here is a handful of rows per
    user. WAL mode is set so a reader is never blocked by the write that follows
    a slow document read.
    """

    kind = "sqlite"

    _SCHEMA = """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            payload    TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS sessions_updated_at ON sessions (updated_at);
    """

    def __init__(
        self, path: Path, *, ttl_minutes: int = 720, limit: int = 500
    ) -> None:
        self._path = path
        self._ttl = timedelta(minutes=ttl_minutes)
        self._limit = limit
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(self._SCHEMA)
        log.info("session store ready", kind=self.kind, path=str(path))

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def create(self) -> Session:
        session = Session(session_id=_new_id())
        self.save(session)
        return session

    def get(self, session_id: str) -> Session | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        if row is None:
            return None
        try:
            session = Session.from_json(row[0])
        except Exception:
            # A row written by an older schema is worse than no row: it would
            # surface as a confusing failure deep in a pipeline instead of an
            # honest "upload a policy first".
            log.warning("dropping unreadable session", session_id=session_id)
            self.delete(session_id)
            return None
        session.touch()
        return session

    def save(self, session: Session) -> None:
        session.touch()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions (session_id, created_at, updated_at, payload) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(session_id) DO UPDATE SET "
                "  updated_at = excluded.updated_at, payload = excluded.payload",
                (
                    session.session_id,
                    session.created_at.isoformat(),
                    session.updated_at.isoformat(),
                    session.to_json(),
                ),
            )
            self._evict(conn)

    def delete(self, session_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))

    def count(self) -> int:
        with self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0])

    def _evict(self, conn: sqlite3.Connection) -> None:
        """Drop expired rows, then the oldest if still over the limit.

        Health data should not sit on disk longer than it is useful, so age is
        the first criterion and the row cap is only a backstop.
        """
        cutoff = (datetime.now(UTC) - self._ttl).isoformat()
        conn.execute("DELETE FROM sessions WHERE updated_at < ?", (cutoff,))
        conn.execute(
            "DELETE FROM sessions WHERE session_id IN ("
            "  SELECT session_id FROM sessions"
            "  ORDER BY updated_at DESC LIMIT -1 OFFSET ?"
            ")",
            (self._limit,),
        )


def build_store(
    kind: str, *, path: Path, ttl_minutes: int, limit: int
) -> SessionStore:
    if kind == "memory":
        return MemorySessionStore(limit=limit)
    return SqliteSessionStore(path, ttl_minutes=ttl_minutes, limit=limit)
