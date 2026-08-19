"""Provider-neutral LLM interface.

The pipeline never names a vendor or a model. It asks for a `ModelRole`, and
the registry decides who serves it. That keeps Ollama Cloud, Anthropic, and the
keyless offline path interchangeable, and means a model deprecation is a config
change rather than a code change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMUnavailable(RuntimeError):
    """Raised when no configured provider can serve a request."""


class LLMResponse(BaseModel):
    text: str
    model: str
    provider: str
    cached: bool = False
    latency_ms: float = 0.0
    prompt_chars: int = 0


class LLMProvider(ABC):
    """A backend capable of serving completions."""

    name: str = "base"

    @abstractmethod
    def available(self) -> bool:
        """Whether this provider is configured well enough to attempt a call."""

    @abstractmethod
    def probe(self, model: str) -> bool:
        """Cheap liveness check for one model. Must not raise."""

    @abstractmethod
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
        """Free-text completion."""

    @abstractmethod
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
        """Completion constrained to a Pydantic schema.

        Implementations should use native grammar/JSON-schema constraints where
        the backend offers them, and fall back to parse-and-retry otherwise.
        """

    def stream(
        self,
        *,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        """The same completion, in the pieces it is written in.

        Not abstract, because a stream of one piece is a valid stream and every
        provider can produce one. Only the help desk asks for this, and only
        because a person waiting for an answer in a hospital corridor should
        watch it arrive rather than watch a spinner; nothing in the pipeline
        streams, since a half-extracted clause is not useful to anybody.
        """
        yield self.complete(
            model=model,
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        ).text

    def supports_vision(self, model: str) -> bool:
        return False
