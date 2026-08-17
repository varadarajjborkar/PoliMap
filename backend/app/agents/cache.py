"""SQLite-backed response cache.

Development on this pipeline means re-running the same document dozens of times
while tuning prompts downstream. Caching on the exact request signature makes
every re-run after the first one free and near-instant, which is what makes the
"iterate and measure" loop practical.

The key includes the model and the full request, so changing a prompt or a
schema correctly invalidates.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

from app.core.config import BACKEND_DIR

_DEFAULT_PATH = BACKEND_DIR / "llm_cache.db"


class ResponseCache:
    def __init__(self, path: Path | None = None, *, enabled: bool = True) -> None:
        self.path = path or _DEFAULT_PATH
        self.enabled = enabled
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None
        self.hits = 0
        self.misses = 0

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.path, check_same_thread=False)
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS responses ("
                " key TEXT PRIMARY KEY,"
                " model TEXT NOT NULL,"
                " payload TEXT NOT NULL,"
                " created_at REAL DEFAULT (unixepoch())"
                ")"
            )
            self._conn.commit()
        return self._conn

    @staticmethod
    def make_key(**parts: Any) -> str:
        blob = json.dumps(parts, sort_keys=True, default=str)
        return hashlib.sha256(blob.encode()).hexdigest()

    def get(self, key: str) -> str | None:
        if not self.enabled:
            return None
        with self._lock:
            row = (
                self._connect()
                .execute("SELECT payload FROM responses WHERE key = ?", (key,))
                .fetchone()
            )
        if row is None:
            self.misses += 1
            return None
        self.hits += 1
        return str(row[0])

    def set(self, key: str, model: str, payload: str) -> None:
        if not self.enabled:
            return
        with self._lock:
            conn = self._connect()
            conn.execute(
                "INSERT OR REPLACE INTO responses (key, model, payload) VALUES (?, ?, ?)",
                (key, model, payload),
            )
            conn.commit()

    def clear(self) -> int:
        with self._lock:
            conn = self._connect()
            n = conn.execute("SELECT COUNT(*) FROM responses").fetchone()[0]
            conn.execute("DELETE FROM responses")
            conn.commit()
        return int(n)

    def stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        with self._lock:
            try:
                stored = (
                    self._connect()
                    .execute("SELECT COUNT(*) FROM responses")
                    .fetchone()[0]
                )
            except sqlite3.Error:
                stored = 0
        return {
            "enabled": self.enabled,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 3) if total else None,
            "stored": stored,
        }
