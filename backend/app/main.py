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
from app.core.config import settings
from app.core.events import bus
from app.core.logging import configure_logging, get_logger
from app.core.guardrails import DISCLAIMER

log = get_logger(__name__)

# The dev server runs on a different port from the API, so the browser needs
# explicit permission to call it.
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    # Worker threads emit progress events; the bus needs the serving loop to
    # hand them back to.
    bus.bind_loop(asyncio.get_running_loop())

    log.info("coverpath starting", provider=settings.coverpath_provider.value)

    if not datasets.is_built:
        log.warning(
            "dataset not built — run `python -m datagen.build_all` from the "
            "repository root before using the app"
        )

    # Probe in the background so startup is not blocked by a slow cloud round
    # trip; roles resolve lazily on first use regardless.
    asyncio.create_task(_probe_models())

    yield
    log.info("coverpath stopped")


async def _probe_models() -> None:
    from app.agents.registry import registry

    health = await asyncio.to_thread(registry.health)
    if health["llm_available"]:
        for role, label in health["roles"].items():
            log.info("model role resolved", role=role, model=label)
    else:
        log.warning(
            "no language model available — running with the rule-based "
            "extractor only. Set OLLAMA_API_KEY in backend/.env to enable "
            "model-assisted extraction and verification."
        )


app = FastAPI(
    title="CoverPath",
    description=(
        "Insurance-aware hospital decision support. " + DISCLAIMER
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root() -> JSONResponse:
    return JSONResponse({
        "name": "CoverPath",
        "docs": "/docs",
        "health": "/api/health",
        "providers": "/api/health/providers",
        "disclaimer": DISCLAIMER,
    })
