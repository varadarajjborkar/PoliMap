"""How much one caller is allowed to ask for, and how often.

Nothing in this app costs a user anything, which is exactly why it needs a
ceiling. Reading a policy runs OCR on every page and then several model calls;
one request can occupy a core for a minute and spend real money at a provider.
An open link with no ceiling is therefore not just a denial-of-service target,
it is somebody else's bill.

The limiter is a token bucket per caller per class of work. A bucket refills at
a steady rate and holds a burst, which fits how people actually use this: a
short flurry of requests while a form is filled in, then nothing for minutes.
A fixed window would reject the flurry and permit a sustained grind, which is
the wrong way round.

It is in-process on purpose. This runs as one container, so a shared store
would add a dependency and a network hop to buy coordination between workers
that do not exist. If it ever runs behind several, the correct move is a shared
counter, and the interface here does not change.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

__all__ = ["Bucket", "RateLimiter", "client_key", "limiter"]


@dataclass(frozen=True)
class Bucket:
    """A named allowance: `rate` requests a second, bursting to `burst`."""

    name: str
    rate: float
    burst: int

    @property
    def retry_after(self) -> int:
        """Seconds until one more token exists, rounded up to a whole second."""
        return max(1, int(1 / self.rate + 0.999)) if self.rate > 0 else 60


# The kinds of work this API does, priced by what each actually costs us.
#
# The pricing is set against what a real person does, not against what is easy
# to classify. A limit a caregiver meets while entering the day's charges is a
# broken app, not a protected one, so anything a person does repeatedly in a
# few minutes has to sit above the rate they can do it at.
#
# READ is reference data and session state, served from memory. Generous,
# because the interface makes several on load and a family refreshing a page
# must never be told to slow down.
#
# WRITE changes session state: recording a charge, correcting a figure,
# searching, moving a stay along. None of it touches a model or a page image.
# Somebody entering a day's charges at a counter does several in a minute, so
# the burst has to hold a whole sitting.
#
# ASK is the help desk: one model call each, and conversational, so it is the
# one expensive thing somebody legitimately does several times in a row.
#
# HEAVY is reading a document: rasterise every page, OCR each, then several
# model calls. One a person does once and then waits on. Even a burst of five
# is more than anybody produces by hand.
READ = Bucket("read", rate=10.0, burst=40)
WRITE = Bucket("write", rate=3.0, burst=30)
ASK = Bucket("ask", rate=0.5, burst=8)
HEAVY = Bucket("heavy", rate=0.2, burst=5)


@dataclass
class _Tokens:
    tokens: float
    updated: float = field(default_factory=time.monotonic)


class RateLimiter:
    """Token buckets keyed on caller and bucket name.

    Bounded in memory as well as in throughput. An attacker cycling source
    addresses would otherwise turn the limiter itself into the leak it exists
    to prevent, so idle entries are dropped once the table grows past a size no
    honest traffic reaches.
    """

    MAX_ENTRIES = 20_000

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state: dict[tuple[str, str], _Tokens] = {}

    def take(self, key: str, bucket: Bucket, *, cost: float = 1.0) -> bool:
        """Spend one token. False means the caller has had enough for now."""
        now = time.monotonic()
        with self._lock:
            entry = self._state.get((key, bucket.name))
            if entry is None:
                if len(self._state) >= self.MAX_ENTRIES:
                    self._evict(now)
                # Stamped with `now` rather than a fresh reading. A second
                # call to monotonic() here lands *after* `now`, so the refill
                # below would run over a negative interval and leave a caller
                # who has spent nothing fractionally short of a full bucket,
                # which costs them their first request.
                entry = _Tokens(tokens=float(bucket.burst), updated=now)
                self._state[(key, bucket.name)] = entry

            # Refill for the time that has passed, never above the burst size.
            entry.tokens = min(
                float(bucket.burst), entry.tokens + (now - entry.updated) * bucket.rate
            )
            entry.updated = now

            if entry.tokens < cost:
                return False
            entry.tokens -= cost
            return True

    def _evict(self, now: float) -> None:
        """Drop entries that have sat full long enough to be indistinguishable
        from a caller that never existed. Called with the lock held."""
        stale = [
            k for k, v in self._state.items()
            if now - v.updated > 300 and v.tokens >= 1.0
        ]
        for k in stale:
            del self._state[k]
        if not stale:
            # Everything is live, so age is the only fair tiebreak.
            oldest = sorted(self._state.items(), key=lambda kv: kv[1].updated)
            for k, _ in oldest[: len(oldest) // 4]:
                del self._state[k]

    def reset(self) -> None:
        """Forget every allowance. For tests, and for nothing else."""
        with self._lock:
            self._state.clear()


def client_key(scope_client, headers, *, trust_proxy: bool) -> str:
    """Which caller a request belongs to.

    Behind a proxy the socket address is the proxy's, so every user in the
    world shares one bucket and the first of them locks out the rest. The
    forwarded address is the real one there, and is also trivially spoofed by
    anyone talking to the origin directly. So it is trusted only when the
    deployment says a proxy is in front, and the leftmost entry is used because
    that is the one the edge appended for this hop.
    """
    if trust_proxy:
        forwarded = headers.get("x-forwarded-for", "")
        if forwarded:
            first = forwarded.split(",")[0].strip()
            if first:
                return first
    return scope_client[0] if scope_client else "unknown"


limiter = RateLimiter()
