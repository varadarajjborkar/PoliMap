"""In-process event bus for pipeline telemetry.

One `emit` call fans out to three places: the console, a bounded replay buffer,
and every live SSE subscriber. Emission is safe from worker threads, since OCR and
PDF rasterisation are CPU-bound and run off the event loop, but they still need
to report progress, so writes are marshalled back onto the main loop.
"""

from __future__ import annotations

import asyncio
import contextlib
import threading
import time
from collections import deque
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from app.core.logging import get_logger
from app.schemas.events import EventStatus, PipelineEvent, PipelineStage

log = get_logger(__name__)

REPLAY_BUFFER_SIZE = 500
SUBSCRIBER_QUEUE_SIZE = 1000


class StepHandle:
    """Mutable handle yielded by `EventBus.step` for annotating an in-flight step."""

    def __init__(self) -> None:
        self.summary: str = ""
        self.detail: dict[str, Any] = {}
        self.status: EventStatus = EventStatus.OK

    def ok(self, summary: str, **detail: Any) -> None:
        self.status = EventStatus.OK
        self.summary = summary
        self.detail.update(detail)

    def warn(self, summary: str, **detail: Any) -> None:
        self.status = EventStatus.WARN
        self.summary = summary
        self.detail.update(detail)

    def skip(self, summary: str, **detail: Any) -> None:
        self.status = EventStatus.SKIPPED
        self.summary = summary
        self.detail.update(detail)

    def add(self, **detail: Any) -> None:
        """Attach structured detail without changing status."""
        self.detail.update(detail)


class EventBus:
    def __init__(self) -> None:
        self._buffer: deque[PipelineEvent] = deque(maxlen=REPLAY_BUFFER_SIZE)
        self._subscribers: set[asyncio.Queue[PipelineEvent]] = set()
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Capture the serving loop so worker threads can hand events back to it."""
        self._loop = loop

    # -- publishing ---------------------------------------------------------

    def emit(self, event: PipelineEvent) -> None:
        """Publish an event. Callable from any thread."""
        with self._lock:
            self._buffer.append(event)
            subscribers = list(self._subscribers)

        log.info(event.console_line(), **_log_fields(event))

        if not subscribers:
            return

        loop = self._loop
        if loop is None or not loop.is_running():
            # No server running (tests, CLI, datagen); console output is enough.
            return

        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None

        if running is loop:
            self._fanout(subscribers, event)
        else:
            loop.call_soon_threadsafe(self._fanout, subscribers, event)

    @staticmethod
    def _fanout(
        subscribers: list[asyncio.Queue[PipelineEvent]], event: PipelineEvent
    ) -> None:
        for q in subscribers:
            # A stalled browser tab must never block the pipeline, so a full
            # queue drops the event rather than waiting for room.
            with contextlib.suppress(asyncio.QueueFull):
                q.put_nowait(event)

    def publish(
        self,
        stage: PipelineStage,
        step: str,
        *,
        status: EventStatus = EventStatus.OK,
        summary: str = "",
        session_id: str | None = None,
        duration_ms: float | None = None,
        **detail: Any,
    ) -> PipelineEvent:
        """Emit a one-shot event without timing it."""
        event = PipelineEvent(
            stage=stage,
            step=step,
            status=status,
            summary=summary,
            detail=detail,
            session_id=session_id,
            duration_ms=duration_ms,
        )
        self.emit(event)
        return event

    @contextmanager
    def step(
        self,
        stage: PipelineStage,
        step: str,
        *,
        session_id: str | None = None,
        summary: str = "",
        **detail: Any,
    ) -> Iterator[StepHandle]:
        """Time a block of work, emitting a start and a completion event.

        Exceptions are reported as FAILED and re-raised: the bus observes, it
        never swallows.
        """
        self.publish(
            stage,
            step,
            status=EventStatus.STARTED,
            summary=summary,
            session_id=session_id,
            **detail,
        )
        handle = StepHandle()
        handle.detail.update(detail)
        started = time.perf_counter()
        try:
            yield handle
        except Exception as exc:
            # The message is logged, not published. Everything published here
            # is streamed to a browser, and an exception's text is written for
            # whoever reads the log: it carries file paths, library internals
            # and third-party error bodies. The type names the failure without
            # describing the inside of the program to whoever caused it.
            log.warning(
                "step failed", step=step, stage=stage.value, error=str(exc)[:500]
            )
            self.publish(
                stage,
                step,
                status=EventStatus.FAILED,
                summary=f"{type(exc).__name__} while {step.replace('_', ' ')}",
                session_id=session_id,
                duration_ms=(time.perf_counter() - started) * 1000,
                **handle.detail,
            )
            raise
        else:
            self.publish(
                stage,
                step,
                status=handle.status,
                summary=handle.summary or summary,
                session_id=session_id,
                duration_ms=(time.perf_counter() - started) * 1000,
                **handle.detail,
            )

    # -- subscribing --------------------------------------------------------

    def subscribe(
        self, *, replay: bool = True, session_id: str | None = None
    ) -> tuple[asyncio.Queue[PipelineEvent], list[PipelineEvent]]:
        """Register a live subscriber, optionally with the recent backlog."""
        q: asyncio.Queue[PipelineEvent] = asyncio.Queue(maxsize=SUBSCRIBER_QUEUE_SIZE)
        with self._lock:
            self._subscribers.add(q)
            backlog = list(self._buffer) if replay else []
        if session_id is not None:
            backlog = [e for e in backlog if e.session_id in (session_id, None)]
        return q, backlog

    def unsubscribe(self, q: asyncio.Queue[PipelineEvent]) -> None:
        with self._lock:
            self._subscribers.discard(q)

    def history(self, session_id: str | None = None) -> list[PipelineEvent]:
        with self._lock:
            events = list(self._buffer)
        if session_id is not None:
            events = [e for e in events if e.session_id == session_id]
        return events

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)


def _log_fields(event: PipelineEvent) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "stage": event.stage.value,
        "step": event.step,
        "status": event.status.value,
    }
    if event.session_id:
        fields["session"] = event.session_id
    return fields


bus = EventBus()
