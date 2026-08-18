"""The walls in front of the API.

Three of them, all at the HTTP layer rather than inside the handlers, because a
handler that has already been reached has already cost something. In order:

* a cap on the request body, applied before the body is read, so an oversized
  upload is refused on the wire instead of being spooled to disk first;
* a rate limit per caller, priced by how expensive the work behind the route
  is;
* response headers that tell the browser to treat what we return as inert
  data, which is what it is.

Written as raw ASGI rather than as `BaseHTTPMiddleware`. That helper buffers
the whole request and response to give handlers a friendlier object, which is
precisely the behaviour a body cap exists to prevent.
"""

from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.config import settings
from app.core.limits import ASK, HEAVY, READ, WRITE, Bucket, client_key, limiter
from app.core.logging import get_logger

log = get_logger(__name__)

Scope = dict[str, Any]
Receive = Callable[[], Awaitable[dict[str, Any]]]
Send = Callable[[dict[str, Any]], Awaitable[None]]


# 25 MB of document, plus the multipart framing and form fields around it. A
# request larger than this cannot be a policy under the documented limit, so
# there is nothing to gain by reading the rest of it.
MAX_UPLOAD_REQUEST_BYTES = 28 * 1024 * 1024

# Everything that is not a file. The largest honest JSON body this API takes is
# a restored session snapshot, which is a compiled policy and a journey: tens
# of kilobytes, and a few hundred for somebody who tracked a long admission.
# One megabyte is generous and still refuses a body sent to be parsed rather
# than to be read.
MAX_JSON_REQUEST_BYTES = 1024 * 1024


# Routes that rasterise pages, run OCR, or call a model. Matched on the path
# because the alternative is a decorator on every handler, and a route added
# later would then be unpriced by default, which is the wrong direction to
# fail in.
# Reading a document, or rebuilding a whole session from one. Everything here
# is something a person does once and then waits on.
#
# Recording a charge, entering a policy by hand and searching are deliberately
# not here, though an earlier pass had them. None of the three touches a model
# or a page image, and all three are things somebody does several times in a
# few minutes: a caregiver entering the day's charges at a counter would have
# met the ceiling with the day half entered.
_HEAVY_PATHS = re.compile(
    r"^/api/(?:"
    r"policy/upload(?:-many)?"
    r"|journey/[^/]+/bill"
    r"|session/[^/]+/report\.pdf"
    r"|session/import"
    r"|health/providers"
    r")"
)

# One model call each, and a conversation rather than a single action.
_ASK_PATHS = re.compile(r"^/api/help/ask")

# The event stream is a long-lived connection, not a request, so a per-second
# allowance is meaningless for it. It is bounded by a cap on how many can be
# open at once instead, applied where it is opened.
_EXEMPT = re.compile(r"^/api/events/")


def bucket_for(method: str, path: str) -> Bucket | None:
    """Which allowance a request spends from, or None if it spends nothing."""
    if _EXEMPT.match(path):
        return None
    if _HEAVY_PATHS.match(path):
        return HEAVY
    if _ASK_PATHS.match(path):
        return ASK
    if method in ("POST", "PUT", "PATCH", "DELETE"):
        return WRITE
    return READ


async def _refuse(send: Send, status: int, message: str, headers: list = None) -> None:
    """Answer without reaching the application.

    Shaped like the app's own errors so the interface, which reads `detail`,
    shows the person a sentence rather than a status code.
    """
    body = json.dumps({"detail": message}).encode()
    raw = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode()),
    ] + (headers or [])
    await send({"type": "http.response.start", "status": status, "headers": raw})
    await send({"type": "http.response.body", "body": body})


class RequestGuard:
    """Body cap and rate limit, before anything else sees the request."""

    def __init__(self, app, *, trust_proxy: bool = False,
                 max_upload_bytes: int = MAX_UPLOAD_REQUEST_BYTES,
                 max_json_bytes: int = MAX_JSON_REQUEST_BYTES) -> None:
        self.app = app
        self.trust_proxy = trust_proxy
        self.max_upload_bytes = max_upload_bytes
        self.max_json_bytes = max_json_bytes
        self._proxy_warned = False

    def _warn_once_about_the_proxy(self, headers: dict[str, str]) -> None:
        """Say so when the deployment is behind a proxy and has not said so.

        This is the misconfiguration that looks like the app being broken. With
        a proxy in front and TRUST_PROXY unset, every request in the world
        arrives from the proxy's address, so everybody shares one allowance and
        the first busy user locks out the rest. Nothing errors; the app simply
        starts refusing people. Saying it once, loudly, in the log is the
        difference between a five minute fix and an afternoon.
        """
        if self._proxy_warned or self.trust_proxy:
            return
        if "x-forwarded-for" not in headers:
            return
        self._proxy_warned = True
        log.warning(
            "requests are arriving through a proxy but TRUST_PROXY is not set, "
            "so every caller shares one rate limit allowance and one busy user "
            "will lock out the rest. Set TRUST_PROXY=true if a proxy really is "
            "in front of this."
        )

    def _ceiling(self, content_type: str) -> int:
        """How large this request is allowed to be, by what it claims to be.

        Only a multipart request can be carrying a document. Anything else is
        being parsed rather than read, and a body sized for a file arriving at
        a route that will turn it into objects is not a large upload, it is an
        attempt to make the parser the expensive part.
        """
        if content_type.startswith("multipart/form-data"):
            return self.max_upload_bytes
        return self.max_json_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            k.decode("latin-1").lower(): v.decode("latin-1")
            for k, v in scope.get("headers", [])
        }
        path = scope.get("path", "")
        method = scope.get("method", "GET")

        # --- the body cap -------------------------------------------------
        # A declared length is refused outright. A body sent without one is
        # counted as it arrives and cut off at the same ceiling, so chunked
        # encoding is not a way around it.
        ceiling = self._ceiling(headers.get("content-type", ""))
        declared = headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > ceiling:
            await _refuse(send, 413, _too_large(ceiling))
            return

        # --- the rate limit -----------------------------------------------
        bucket = bucket_for(method, path)
        if bucket is not None and method != "OPTIONS" and settings.rate_limit_enabled:
            self._warn_once_about_the_proxy(headers)
            caller = client_key(
                scope.get("client"), headers, trust_proxy=self.trust_proxy
            )
            if not limiter.take(caller, bucket):
                log.warning("rate limited", path=path, bucket=bucket.name)
                await _refuse(
                    send, 429,
                    "That is faster than this service answers. "
                    "Wait a moment and try again.",
                    headers=[(b"retry-after", str(bucket.retry_after).encode())],
                )
                return

        if not declared and method in ("POST", "PUT", "PATCH"):
            receive = _counted(receive, ceiling)

        try:
            await self.app(scope, receive, send)
        except _BodyTooLarge:
            # Raised out of `receive` once the ceiling is crossed mid-stream.
            # Nothing has been sent yet, so a refusal is still possible.
            await _refuse(send, 413, _too_large(ceiling))


def _too_large(ceiling: int) -> str:
    if ceiling >= 1024 * 1024:
        return f"That is larger than the {ceiling // (1024 * 1024)} MB this accepts."
    return f"That is larger than the {ceiling // 1024} KB this accepts."


class _BodyTooLarge(Exception):
    """An undeclared body outgrew the ceiling while it was being read."""


def _counted(receive: Receive, ceiling: int) -> Receive:
    seen = 0

    async def wrapped() -> dict[str, Any]:
        nonlocal seen
        message = await receive()
        if message["type"] == "http.request":
            seen += len(message.get("body", b""))
            if seen > ceiling:
                raise _BodyTooLarge
        return message

    return wrapped


# Everything this API returns is data. None of it is a document a browser
# should render, execute, or be talked into guessing the type of, and saying so
# costs nothing.
#
# The connect-src is 'self' rather than absent because the API's own /docs page
# talks to it. frame-ancestors 'none' matters most: it is what stops the API
# being framed by a page that then reads a response the browser attached
# credentials to.
_HEADERS: list[tuple[bytes, bytes]] = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"cross-origin-opener-policy", b"same-origin"),
    (b"cross-origin-resource-policy", b"same-site"),
    (
        b"permissions-policy",
        b"geolocation=(), microphone=(), camera=(), payment=(), usb=(), "
        b"interest-cohort=()",
    ),
    (
        b"content-security-policy",
        b"default-src 'none'; frame-ancestors 'none'; base-uri 'none'; "
        b"form-action 'none'; img-src 'self' data:; connect-src 'self'; "
        b"script-src 'self'; style-src 'self' 'unsafe-inline'; "
        b"font-src 'self' data:",
    ),
]


class SecurityHeaders:
    """Stamp the response headers that make a browser treat this as data."""

    def __init__(self, app, *, hsts: bool = False) -> None:
        self.app = app
        self.headers = list(_HEADERS)
        if hsts:
            # Only where TLS actually terminates. Sent over plain HTTP it is
            # ignored, and sent from a development server it would pin
            # localhost to HTTPS in the developer's browser for a year.
            self.headers.append(
                (b"strict-transport-security", b"max-age=31536000; includeSubDomains")
            )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def stamped(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                existing = {k.lower() for k, _ in message.get("headers", [])}
                message["headers"] = list(message.get("headers", [])) + [
                    (k, v) for k, v in self.headers if k not in existing
                ]
            await send(message)

        await self.app(scope, receive, stamped)
