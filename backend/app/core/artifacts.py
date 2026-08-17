"""Page images written during intake, and getting rid of them again.

Reading a scanned document rasterises every page at 300 DPI and keeps the image
so a clause can be traced back to the pixels it came from. That is worth the
disk while a session is alive and is pure cost afterwards, so nothing here is
kept indefinitely.

Two mechanisms, because either alone leaves a gap:

* `purge` runs when a session is deliberately ended, which covers the common
  case immediately.
* `sweep` runs at startup and deletes anything older than the session lifetime.
  This is what catches sessions that were evicted by age or by the row cap,
  where no code path was left to do the tidying.

These are page images of a document the user handed us, so leaving them lying
around is a privacy question as much as a disk one.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


def page_dir(session_id: str | None) -> Path:
    """Directory holding the rasterised pages for one session."""
    base = settings.uploads_dir / "pages" / (session_id or "adhoc")
    base.mkdir(parents=True, exist_ok=True)
    return base


def purge(session_id: str) -> None:
    """Delete one session's page images. Safe to call when there are none."""
    target = settings.uploads_dir / "pages" / session_id
    if not target.exists():
        return
    shutil.rmtree(target, ignore_errors=True)
    log.debug("purged page images", session_id=session_id)


def sweep(max_age_minutes: int | None = None) -> int:
    """Delete page directories older than the session lifetime.

    Returns how many were removed. Age is taken from the directory's own
    modification time, which advances as pages are written into it, so a
    session being actively read is never swept out from under itself.
    """
    root = settings.uploads_dir / "pages"
    if not root.exists():
        return 0

    ttl = (max_age_minutes or settings.session_ttl_minutes) * 60
    cutoff = time.time() - ttl
    removed = 0

    for child in root.iterdir():
        if not child.is_dir():
            continue
        try:
            if child.stat().st_mtime >= cutoff:
                continue
            shutil.rmtree(child, ignore_errors=True)
            removed += 1
        except OSError:
            # A directory vanishing under us is the outcome we wanted anyway.
            continue

    if removed:
        log.info("swept stale page images", directories=removed)
    return removed


def disk_usage_bytes() -> int:
    """Total size of retained page images. Reported by the health endpoint."""
    root = settings.uploads_dir / "pages"
    if not root.exists():
        return 0
    return sum(f.stat().st_size for f in root.rglob("*") if f.is_file())
