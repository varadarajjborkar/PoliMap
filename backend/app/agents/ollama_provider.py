"""Ollama provider (cloud and self-hosted).

A note on structured output, because it shapes the whole extraction design:

Ollama's documented `format=<json-schema>` parameter constrains generation to a
schema. Self-hosted Ollama honours it. **Ollama Cloud currently ignores it**,
verified against the live API, where even `format="json"` returns markdown
prose. We therefore cannot treat schema conformance as a guarantee.

The response is instead steered by prompt, then defensively parsed: strip code
fences, salvage the outermost JSON object by brace-matching, validate against
the Pydantic model, and on failure re-prompt once with the validation error
attached. `format` is still sent, so a self-hosted deployment gets the stronger
guarantee for free.

The practical consequence is that a returned value can be well-formed yet wrong.
That is exactly what the verbatim-grounding check (a clause must quote text that
really exists in the document) and the adversarial verification loop are for.
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import Iterator
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.agents.base import LLMProvider, LLMResponse, LLMUnavailable
from app.agents.cache import ResponseCache
from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 1.5
STRUCTURED_REPAIR_ATTEMPTS = 2

# Errors that mean "this model will never work on this account", as opposed to
# transient failures worth retrying.
_PERMANENT_MARKERS = ("subscription", "not found", "upgrade for access")

# Models on the cloud catalogue that accept image input.
VISION_CAPABLE_PREFIXES = (
    "gemma4",
    "minimax-m3",
    "kimi-k3",
    "kimi-k2.6",
    "kimi-k2.7",
    "qwen3.5",
    "mistral-large-3",
)

_JSON_SYSTEM = (
    "You are a precise data extraction engine. You reply with a single raw JSON "
    "object and nothing else: no markdown, no code fences, no commentary, no "
    "explanation before or after. Every string you emit must be copied from the "
    "source material rather than paraphrased."
)


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, cache: ResponseCache | None = None) -> None:
        self._cache = cache or ResponseCache(enabled=settings.llm_cache_enabled)
        self._client: Any = None
        self._probe_results: dict[str, bool] = {}

    # -- plumbing -----------------------------------------------------------

    def _get_client(self) -> Any:
        if self._client is None:
            from ollama import Client

            if not settings.ollama_api_key:
                raise LLMUnavailable("OLLAMA_API_KEY is not set. Add it to backend/.env")
            self._client = Client(
                host=settings.ollama_host,
                headers={"Authorization": f"Bearer {settings.ollama_api_key}"},
                timeout=settings.llm_timeout_seconds,
            )
        return self._client

    def available(self) -> bool:
        return bool(settings.ollama_api_key)

    def supports_vision(self, model: str) -> bool:
        return model.lower().startswith(VISION_CAPABLE_PREFIXES)

    def list_catalogue(self) -> list[str]:
        """Every model the endpoint advertises.

        The catalogue is not the same as what this account may call, plan gating
        only surfaces on an actual request, so this is a starting point for
        probing, not an availability answer.
        """
        try:
            resp = self._get_client().list()
            models = resp.get("models") if isinstance(resp, dict) else resp.models
            names = []
            for m in models or []:
                name = m.get("model") if isinstance(m, dict) else getattr(m, "model", None)
                if name:
                    names.append(name)
            return sorted(names)
        except Exception as exc:
            log.debug("catalogue listing failed", error=str(exc)[:200])
            return []

    def probe(self, model: str) -> bool:
        """One-token call confirming this account may actually call the model."""
        if model in self._probe_results:
            return self._probe_results[model]
        ok = False
        try:
            self._get_client().chat(
                model=model,
                messages=[{"role": "user", "content": "hi"}],
                stream=False,
                options={"num_predict": 1, "temperature": 0},
            )
            ok = True
        except Exception as exc:
            detail = str(exc)
            reason = next(
                (m for m in _PERMANENT_MARKERS if m in detail.lower()), "transient"
            )
            log.debug("model probe failed", model=model, reason=reason)
            # Only cache permanent verdicts; a 429 shouldn't blacklist a model.
            if reason == "transient":
                return False
        self._probe_results[model] = ok
        return ok

    @staticmethod
    def _content(response: Any) -> str:
        message = (
            response.get("message")
            if isinstance(response, dict)
            else getattr(response, "message", None)
        )
        if message is None:
            return ""
        content = (
            message.get("content")
            if isinstance(message, dict)
            else getattr(message, "content", "")
        )
        return content or ""

    @staticmethod
    def _build_messages(
        prompt: str, system: str, images: list[bytes] | None
    ) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        user: dict[str, Any] = {"role": "user", "content": prompt}
        if images:
            user["images"] = images
        messages.append(user)
        return messages

    def _chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        fmt: Any | None,
        temperature: float,
        max_tokens: int | None,
    ) -> str:
        options: dict[str, Any] = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": options,
        }
        if fmt is not None:
            # Honoured by self-hosted Ollama, ignored by the cloud. Sent either
            # way; correctness never depends on it.
            kwargs["format"] = fmt

        last_error: Exception | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                return self._content(self._get_client().chat(**kwargs))
            except Exception as exc:
                last_error = exc
                if any(m in str(exc).lower() for m in _PERMANENT_MARKERS):
                    raise LLMUnavailable(f"{model} unavailable: {exc}") from exc
                if attempt < MAX_ATTEMPTS:
                    wait = RETRY_BACKOFF_SECONDS * attempt
                    log.warning(
                        "llm call failed, retrying",
                        model=model,
                        attempt=attempt,
                        wait_s=wait,
                        error=str(exc)[:200],
                    )
                    time.sleep(wait)
        raise LLMUnavailable(
            f"Ollama call to {model} failed after {MAX_ATTEMPTS} attempts: {last_error}"
        ) from last_error

    # -- interface ----------------------------------------------------------

    def complete(
        self,
        *,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.0,
        images: list[bytes] | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        key = ResponseCache.make_key(
            provider=self.name,
            model=model,
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            images=[len(i) for i in images] if images else None,
        )
        if (hit := self._cache.get(key)) is not None:
            return LLMResponse(
                text=hit,
                model=model,
                provider=self.name,
                cached=True,
                prompt_chars=len(prompt),
            )

        started = time.perf_counter()
        text = self._chat(
            model=model,
            messages=self._build_messages(prompt, system, images),
            fmt=None,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self._cache.set(key, model, text)
        return LLMResponse(
            text=text,
            model=model,
            provider=self.name,
            latency_ms=(time.perf_counter() - started) * 1000,
            prompt_chars=len(prompt),
        )

    def stream(
        self,
        *,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        """Completion in pieces, as the model writes them.

        No retry loop, unlike `complete`. A retry after the first piece has
        left the building would repeat text somebody has already read, so a
        stream that breaks is a stream that ends: the caller has the failure
        and can fall back to something written down, which is exactly what the
        help desk does.
        """
        key = ResponseCache.make_key(
            provider=self.name,
            model=model,
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            images=None,
        )
        if (hit := self._cache.get(key)) is not None:
            yield hit
            return

        options: dict[str, Any] = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        pieces: list[str] = []
        try:
            for chunk in self._get_client().chat(
                model=model,
                messages=self._build_messages(prompt, system, None),
                stream=True,
                options=options,
            ):
                piece = self._content(chunk)
                if piece:
                    pieces.append(piece)
                    yield piece
        except Exception as exc:
            raise LLMUnavailable(f"Ollama stream from {model} failed: {exc}") from exc

        # Cached on the whole answer, so the same question asked twice costs
        # one call and the second one streams out of the cache in one piece.
        if pieces:
            self._cache.set(key, model, "".join(pieces))

    def complete_structured(
        self,
        *,
        model: str,
        prompt: str,
        schema: type[T],
        system: str = "",
        temperature: float = 0.0,
        images: list[bytes] | None = None,
    ) -> T:
        json_schema = schema.model_json_schema()
        key = ResponseCache.make_key(
            provider=self.name,
            model=model,
            prompt=prompt,
            system=system,
            temperature=temperature,
            schema=json_schema,
            images=[len(i) for i in images] if images else None,
        )
        if (hit := self._cache.get(key)) is not None:
            try:
                return schema.model_validate_json(hit)
            except ValidationError:
                log.debug("stale cached payload, refetching", model=model)

        instructed = _with_schema_instruction(prompt, json_schema)
        effective_system = f"{_JSON_SYSTEM}\n\n{system}".strip() if system else _JSON_SYSTEM

        last_error: str = ""
        for attempt in range(1, STRUCTURED_REPAIR_ATTEMPTS + 1):
            body = instructed
            if attempt > 1:
                body = (
                    f"{instructed}\n\n"
                    f"Your previous reply could not be parsed: {last_error}\n"
                    f"Reply again with ONLY the raw JSON object."
                )
            raw = self._chat(
                model=model,
                messages=self._build_messages(body, effective_system, images),
                fmt=json_schema,
                temperature=temperature,
                max_tokens=None,
            )
            obj = extract_json_object(raw)
            if obj is None:
                last_error = "no JSON object found in the response"
                continue
            try:
                parsed = schema.model_validate(obj)
            except ValidationError as exc:
                last_error = "; ".join(
                    f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}"
                    for e in exc.errors()[:4]
                )
                continue
            self._cache.set(key, model, parsed.model_dump_json())
            return parsed

        raise LLMUnavailable(
            f"{model} could not produce valid {schema.__name__} "
            f"after {STRUCTURED_REPAIR_ATTEMPTS} attempts: {last_error}"
        )


def _with_schema_instruction(prompt: str, json_schema: dict[str, Any]) -> str:
    return (
        f"{prompt}\n\n"
        f"Respond with a single JSON object conforming exactly to this schema:\n"
        f"{json.dumps(json_schema, indent=2)}\n\n"
        f"Output the raw JSON object only."
    )


_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.MULTILINE)


def extract_json_object(text: str) -> dict[str, Any] | None:
    """Salvage the outermost JSON object from a possibly noisy response.

    Brace-matched rather than regex-based so that braces inside string literals
    (common in `verbatim` fields quoting policy text) don't truncate the object.
    """
    if not text:
        return None
    cleaned = _FENCE_RE.sub("", text).strip()

    start = cleaned.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(cleaned)):
        ch = cleaned[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(cleaned[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None
