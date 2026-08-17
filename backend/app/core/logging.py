"""Console logging setup.

Human-readable and colourised when attached to a terminal, JSON lines when
piped — so `uvicorn ... | tee run.log` produces something machine-parseable
while the live console stays readable during a demo.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

_configured = False


def configure_logging(level: str = "INFO", *, force_json: bool = False) -> None:
    global _configured
    if _configured:
        return

    use_json = force_json or not sys.stderr.isatty()

    renderer: Any = (
        structlog.processors.JSONRenderer()
        if use_json
        else structlog.dev.ConsoleRenderer(colors=True, event_key="event")
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%H:%M:%S", utc=False),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )

    # Quiet the noisy libraries; our own events carry the signal.
    for noisy in ("httpx", "httpcore", "urllib3", "PIL", "watchfiles"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    if not _configured:
        configure_logging()
    return structlog.get_logger(name)
