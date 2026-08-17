"""Role-to-model resolution.

Callers ask for a `ModelRole` — "give me something that can extract clauses" —
never for a named model. The registry walks that role's configured chain,
probes each candidate against the live account, and memoises the first that
answers. Plan gating and model deprecation therefore degrade gracefully instead
of raising at the call site.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel

from app.agents.base import LLMProvider, LLMResponse, LLMUnavailable
from app.agents.cache import ResponseCache
from app.agents.offline_provider import OfflineProvider
from app.agents.ollama_provider import OllamaProvider
from app.core.config import ModelRole, Provider, settings
from app.core.events import bus
from app.core.logging import get_logger
from app.schemas.events import EventStatus, PipelineStage

log = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class Resolution:
    """Which provider and model ended up serving a role."""

    role: ModelRole
    provider: LLMProvider
    model: str

    @property
    def label(self) -> str:
        return f"{self.provider.name}:{self.model}"


class ModelRegistry:
    def __init__(
        self,
        providers: list[LLMProvider] | None = None,
        chain_for: Callable[[ModelRole], list[str]] | None = None,
    ) -> None:
        self.cache = ResponseCache(enabled=settings.llm_cache_enabled)
        self._providers: list[LLMProvider] = providers or self._build_providers()
        # Injectable so tests can drive resolution without touching the
        # environment, and so an operator could supply chains from elsewhere.
        self._chain_for = chain_for or settings.chain_for
        self._resolutions: dict[ModelRole, Resolution | None] = {}
        self._lock = threading.Lock()

    def _build_providers(self) -> list[LLMProvider]:
        """Providers in preference order, honouring an explicit override."""
        wanted = settings.coverpath_provider
        providers: list[LLMProvider] = []

        if wanted in (Provider.AUTO, Provider.OLLAMA) and settings.has_ollama:
            providers.append(OllamaProvider(cache=self.cache))

        # Anthropic adapter slots in here when a key is present; the interface
        # is identical, so nothing downstream changes.

        providers.append(OfflineProvider())
        return providers

    # -- resolution ---------------------------------------------------------

    def resolve(self, role: ModelRole) -> Resolution | None:
        """First working (provider, model) for a role, or None if none work."""
        with self._lock:
            if role in self._resolutions:
                return self._resolutions[role]

        chain = self._chain_for(role)
        resolution: Resolution | None = None
        tried: list[str] = []

        for provider in self._providers:
            if isinstance(provider, OfflineProvider) or not provider.available():
                continue
            for model in chain:
                if role is ModelRole.VISION_OCR and not provider.supports_vision(model):
                    continue
                tried.append(model)
                if provider.probe(model):
                    resolution = Resolution(role=role, provider=provider, model=model)
                    break
            if resolution:
                break

        with self._lock:
            self._resolutions[role] = resolution

        if resolution:
            bus.publish(
                PipelineStage.SYSTEM,
                "resolve_model",
                summary=f"{role.value} -> {resolution.label}",
                role=role.value,
                model=resolution.model,
                provider=resolution.provider.name,
                candidates_tried=len(tried),
            )
        else:
            bus.publish(
                PipelineStage.SYSTEM,
                "resolve_model",
                status=EventStatus.WARN,
                summary=f"{role.value} -> unavailable (tried {len(tried)})",
                role=role.value,
                tried=tried,
            )
        return resolution

    def resolve_all(self) -> dict[ModelRole, Resolution | None]:
        """Resolve every role at once. Probes run in parallel."""
        roles = list(ModelRole)
        with ThreadPoolExecutor(max_workers=len(roles)) as pool:
            pool.map(self.resolve, roles)
        with self._lock:
            return dict(self._resolutions)

    def reset(self) -> None:
        """Forget resolutions so the next call re-probes."""
        with self._lock:
            self._resolutions.clear()

    @property
    def has_llm(self) -> bool:
        """Whether any language model at all is reachable."""
        return self.resolve(ModelRole.EXTRACT) is not None

    # -- invocation ---------------------------------------------------------

    def complete(
        self,
        role: ModelRole,
        *,
        prompt: str,
        system: str = "",
        temperature: float = 0.0,
        images: list[bytes] | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        resolution = self.resolve(role)
        if resolution is None:
            raise LLMUnavailable(f"No model available for role {role.value}")
        return resolution.provider.complete(
            model=resolution.model,
            prompt=prompt,
            system=system,
            temperature=temperature,
            images=images,
            max_tokens=max_tokens,
        )

    def complete_structured(
        self,
        role: ModelRole,
        *,
        prompt: str,
        schema: type[T],
        system: str = "",
        temperature: float = 0.0,
        images: list[bytes] | None = None,
    ) -> T:
        resolution = self.resolve(role)
        if resolution is None:
            raise LLMUnavailable(f"No model available for role {role.value}")
        return resolution.provider.complete_structured(
            model=resolution.model,
            prompt=prompt,
            schema=schema,
            system=system,
            temperature=temperature,
            images=images,
        )

    # -- diagnostics --------------------------------------------------------

    def health(self) -> dict[str, Any]:
        """Snapshot for the health endpoint and the startup banner."""
        resolutions = self.resolve_all()
        roles = {
            role.value: (res.label if res else None) for role, res in resolutions.items()
        }
        active = [p.name for p in self._providers if p.available()]
        return {
            "providers_configured": active,
            "llm_available": any(r is not None for r in resolutions.values()),
            "roles": roles,
            "degraded_roles": [r for r, v in roles.items() if v is None],
            "cache": self.cache.stats(),
        }


registry = ModelRegistry()
