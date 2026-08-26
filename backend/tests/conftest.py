"""Shared test wiring.

Tests run against the in-memory session store. They want isolation from each
other, not durability, and the alternative writes a database file into the
working tree as a side effect of running the suite.
"""

from __future__ import annotations

import pytest

from app.api.session import sessions
from app.api.store import MemorySessionStore
from app.core.config import settings
from app.core.limits import limiter


@pytest.fixture(autouse=True)
def isolated_sessions():
    sessions.use(MemorySessionStore())
    yield
    sessions.use(MemorySessionStore())


@pytest.fixture(autouse=True)
def no_rate_limit():
    """The suite is a single caller making thousands of requests.

    That is precisely the traffic the limiter exists to refuse, so leaving it
    on would make every test after the first few fail for a reason that has
    nothing to do with what they are testing. `test_protection.py` turns it
    back on and points it at itself.
    """
    settings.rate_limit_enabled = False
    limiter.reset()
    yield
    settings.rate_limit_enabled = True
    limiter.reset()