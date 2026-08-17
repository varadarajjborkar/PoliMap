"""Shared test wiring.

Tests run against the in-memory session store. They want isolation from each
other, not durability, and the alternative writes a database file into the
working tree as a side effect of running the suite.
"""

from __future__ import annotations

import pytest

from app.api.session import sessions
from app.api.store import MemorySessionStore


@pytest.fixture(autouse=True)
def isolated_sessions():
    sessions.use(MemorySessionStore())
    yield
    sessions.use(MemorySessionStore())
