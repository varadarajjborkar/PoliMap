"""Application settings, loaded from environment and `backend/.env`.

Model roles are declared as *fallback chains* rather than single model names.
Cloud model availability shifts with provider plans and deprecations, so every
role names several acceptable models and the resolver (see `agents/registry.py`)
probes them at boot and keeps the first that answers.
"""

from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
GENERATED_DIR = DATA_DIR / "generated"
UPLOADS_DIR = DATA_DIR / "uploads"


class Provider(StrEnum):
    AUTO = "auto"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    OFFLINE = "offline"


class SessionStore(StrEnum):
    MEMORY = "memory"
    SQLITE = "sqlite"


class ModelRole(StrEnum):
    """What a model is being asked to do, decoupled from which model does it."""

    EXTRACT = "extract"
    CHALLENGE = "challenge"
    ADJUDICATE = "adjudicate"
    VISION_OCR = "vision_ocr"
    NARRATE = "narrate"


# Ordered preferences per role, heavier models where correctness dominates and
# lighter ones where the call is made many times per document. Chains are long
# because cloud catalogues gate models by plan: the resolver probes downward
# until it finds one this account can actually call.
#
# Measured single-call latency on the free tier (short extraction prompt):
#   nemotron-3-super 11s | nemotron-3-nano 15s | gpt-oss:20b 22s
#   gemma4:31b 23s | minimax-m3 25s | gpt-oss:120b 31s | nemotron-3-ultra 63s
# Vision transcription is far quicker: gemma4:31b 1.6s, minimax-m3 2.8s.
DEFAULT_MODEL_CHAINS: dict[ModelRole, list[str]] = {
    ModelRole.EXTRACT: [
        "gpt-oss:120b",
        "nemotron-3-super",
        "gpt-oss:20b",
        "qwen3.5:397b",
    ],
    ModelRole.CHALLENGE: [
        "nemotron-3-super",
        "gpt-oss:20b",
        "nemotron-3-nano:30b",
        "deepseek-v4-flash:0731",
    ],
    ModelRole.ADJUDICATE: [
        "gpt-oss:120b",
        "nemotron-3-ultra",
        "nemotron-3-super",
        "glm-5.2",
    ],
    # Only vision-capable models belong here.
    ModelRole.VISION_OCR: ["gemma4:31b", "minimax-m3", "kimi-k3"],
    # The help desk answers on this role, and it answers in whichever of five
    # languages it was asked in, in the script it was asked in. That turns out
    # to need the larger model: given romanised Kannada, gpt-oss:20b replies in
    # Kannada script about half the time and once picked Tamil, while the 120b
    # holds the letters it was given. It is also quicker here, 2.1s against 3
    # to 7, because the small one spends the budget reasoning about a question
    # that does not need it.
    ModelRole.NARRATE: [
        "gpt-oss:120b",
        "gpt-oss:20b",
        "nemotron-3-nano:30b",
        "gemma4:31b",
    ],
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # `model_*` env vars are ours, not pydantic's reserved namespace.
        protected_namespaces=(),
    )

    # --- provider ---
    polimap_provider: Provider = Provider.AUTO

    # `repr=False` keeps the keys out of every rendering of this object. A
    # settings object is repr'd in more places than it looks: a pytest
    # assertion that mentions `settings` prints the whole thing, and so does an
    # unhandled exception whose frame holds one. Both end up in CI logs, which
    # are public on a public repository. The value is still read normally; it
    # just stops travelling attached to every traceback.
    ollama_api_key: str = Field(default="", repr=False)
    anthropic_api_key: str = Field(default="", repr=False)
    ollama_host: str = "https://ollama.com"

    # --- model role chains (blank -> DEFAULT_MODEL_CHAINS) ---
    model_extract: str = ""
    model_challenge: str = ""
    model_adjudicate: str = ""
    model_vision_ocr: str = ""
    model_narrate: str = ""

    # --- behaviour ---
    log_level: str = "INFO"
    llm_cache_enabled: bool = True
    llm_timeout_seconds: int = 120
    max_challenge_rounds: int = Field(default=3, ge=1, le=10)
    ocr_confidence_threshold: float = Field(default=0.72, ge=0.0, le=1.0)

    # --- paths ---
    data_dir: Path = DATA_DIR
    generated_dir: Path = GENERATED_DIR
    uploads_dir: Path = UPLOADS_DIR

    # --- session storage ---
    # "sqlite" survives a restart and is shared by every worker in the process
    # group, which is what a deployed instance needs. "memory" is faster and is
    # what the tests use, since they want isolation rather than durability.
    session_store: SessionStore = SessionStore.SQLITE
    session_db_path: Path = DATA_DIR / "polimap.db"
    session_ttl_minutes: int = Field(default=720, ge=5)
    session_limit: int = Field(default=500, ge=1)

    # --- deployment ---
    # Origins allowed to call the API. The dev server and preview server are
    # always permitted; a deployed frontend adds its own origin here.
    cors_origins: str = ""

    # --- protection ---
    # Whether a reverse proxy really is in front. The forwarded address is the
    # caller's true one there, and is a free spoof anywhere else, so trusting
    # it unconditionally would hand anyone a fresh rate-limit allowance per
    # request.
    #
    # Left unset it is detected, because getting it wrong is silent and looks
    # exactly like the app being broken: behind a proxy without it, every
    # request in the world arrives from the proxy's address, everybody shares
    # one allowance, and the first few users lock out the rest. Nothing errors.
    # A managed host is not a thing anybody should have to remember to declare.
    trust_proxy: bool | None = None

    # The rate limit itself. On everywhere it matters; the test suite turns it
    # off because a suite is one caller making thousands of requests, which is
    # the exact shape the limiter exists to refuse. The limiter's own tests
    # turn it back on.
    rate_limit_enabled: bool = True

    # Whether TLS terminates at the edge. Turns on HSTS, which is a promise a
    # plain-HTTP deployment cannot keep and a development server must not make.
    # Detected the same way, since the hosts that put a proxy in front are the
    # same ones that terminate TLS.
    behind_tls: bool | None = None

    # The generated API reference. Useful while building, and a map of every
    # route and every field for anybody else, so it is off unless asked for.
    enable_docs: bool = False

    # A document is read page by page, and every page that is not already text
    # is rasterised and put through OCR. Both bound the work one upload can
    # ask for: a small file can declare thousands of pages, or one page the
    # size of a wall, and neither is a policy anybody is holding.
    max_document_pages: int = Field(default=60, ge=1, le=500)
    max_page_megapixels: float = Field(default=40.0, gt=0)

    # A photograph is decoded in full before anything can be done with it, and
    # an image file's dimensions are declared in its header rather than implied
    # by its size, so a small file can claim to be enormous. The ceiling is set
    # above what any phone camera produces so that a real photo never meets it.
    max_image_megapixels: float = Field(default=60.0, gt=0)

    # Live event streams held open at once. Each is a queue and a socket, and
    # nothing stops one caller opening them by the thousand.
    max_event_streams: int = Field(default=200, ge=1)

    @field_validator("ollama_api_key", "anthropic_api_key", mode="after")
    @classmethod
    def _strip_key(cls, v: str) -> str:
        # Pasted keys routinely carry stray whitespace or wrapping quotes.
        return v.strip().strip('"').strip("'")

    def chain_for(self, role: ModelRole) -> list[str]:
        """Resolve a role to its ordered list of candidate model names."""
        override = getattr(self, f"model_{role.value}", "")
        if override.strip():
            return [m.strip() for m in override.split(",") if m.strip()]
        return list(DEFAULT_MODEL_CHAINS[role])

    def allowed_origins(self) -> list[str]:
        """Browser origins permitted to call the API.

        The local dev and preview servers are always included so a checkout
        works with no configuration. A deployed frontend adds its own origin
        through CORS_ORIGINS, comma separated.
        """
        local = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
        ]
        extra = [o.strip().rstrip("/") for o in self.cors_origins.split(",")]
        return local + [o for o in extra if o]

    @property
    def on_managed_host(self) -> bool:
        """Whether this is running on a platform that fronts it with a proxy.

        Each of these variables is set by the platform itself and cannot be
        reached by a request, so reading one is not something a caller can
        influence. They are the same hosts that terminate TLS.
        """
        return any(
            os.environ.get(name)
            for name in ("RENDER", "RAILWAY_ENVIRONMENT", "FLY_APP_NAME", "DYNO")
        )

    @property
    def proxy_trusted(self) -> bool:
        """Whether to read the caller's address from X-Forwarded-For."""
        if self.trust_proxy is not None:
            return self.trust_proxy
        return self.on_managed_host

    @property
    def tls_terminated(self) -> bool:
        """Whether to promise HSTS."""
        if self.behind_tls is not None:
            return self.behind_tls
        return self.on_managed_host

    @property
    def has_ollama(self) -> bool:
        return bool(self.ollama_api_key)

    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key)


settings = Settings()

for _d in (DATA_DIR, GENERATED_DIR, UPLOADS_DIR):
    _d.mkdir(parents=True, exist_ok=True)
