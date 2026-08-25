"""Application entry point.

    uvicorn app.main:app --reload --port 8000

The startup banner reports which model is serving each role and whether the
dataset has been built, so a misconfiguration is visible immediately rather than
surfacing as a confusing failure on the first upload.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.api.session import datasets
from app.core import artifacts
from app.core.config import settings
from app.core.events import bus
from app.core.guardrails import DISCLAIMER
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestGuard, SecurityHeaders

log = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    # Worker threads emit progress events; the bus needs the serving loop to
    # hand them back to.
    bus.bind_loop(asyncio.get_running_loop())

    log.info(
        "polimap starting",
        provider=settings.polimap_provider.value,
        session_store=settings.session_store.value,
    )

    # Bill photographs an older version of this app accepted and stored. It
    # does not any more: a receipt stays on the device that took it.
    await asyncio.to_thread(artifacts.drop_retired)

    # Page images from sessions that have since expired have nothing left to
    # trace back to, and they are the bulkiest thing this app writes.
    swept = await asyncio.to_thread(artifacts.sweep)
    if swept:
        log.info("cleared stale page images", directories=swept)

    if not datasets.is_built:
        log.warning(
            "dataset not built, run `python -m datagen.build_all` from the "
            "repository root before using the app"
        )

    # Probe in the background so startup is not blocked by a slow cloud round
    # trip; roles resolve lazily on first use regardless.
    asyncio.create_task(_probe_models())

    yield
    log.info("polimap stopped")


async def _probe_models() -> None:
    from app.agents.registry import registry

    health = await asyncio.to_thread(registry.health)
    if health["llm_available"]:
        for role, label in health["roles"].items():
            log.info("model role resolved", role=role, model=label)
    else:
        log.warning(
            "no language model available, running with the rule-based "
            "extractor only. Set OLLAMA_API_KEY in backend/.env to enable "
            "model-assisted extraction and verification."
        )


# The generated reference is a complete map of every route, every field and
# every accepted value. That is a gift while building and a head start for
# anybody else, so it is served only where it was asked for.
_docs = "/docs" if settings.enable_docs else None

app = FastAPI(
    title="PoliMap",
    description=(
        "Insurance-aware hospital decision support. " + DISCLAIMER
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url=_docs,
    redoc_url="/redoc" if settings.enable_docs else None,
    openapi_url="/openapi.json" if settings.enable_docs else None,
)

# Middleware is added innermost first: the last one registered is the one that
# sees a request earliest and a response last. The order that matters here is
# headers outside CORS outside the guard, so that a refusal from the guard is
# still stamped as inert data and still carries the CORS headers the browser
# needs before it will let our own page read the reason it was refused.
app.add_middleware(RequestGuard, trust_proxy=settings.proxy_trusted)

# The frontend is served from a different origin than the API, in development
# and in deployment alike, so the browser needs explicit permission to call it.
# No credentials: this API has no cookies and no browser-managed auth, so
# allowing them would only widen what a permitted origin could do on a user's
# behalf while buying nothing. The session id travels in the URL path and is
# sent deliberately by our own client.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
    max_age=600,
)

app.add_middleware(SecurityHeaders, hsts=settings.tls_terminated)

app.include_router(router)


@app.get("/")
def root() -> JSONResponse:
    return JSONResponse({
        "name": "PoliMap",
        "docs": "/docs",
        "health": "/api/health",
        "providers": "/api/health/providers",
        "disclaimer": DISCLAIMER,
    })
