"""Keyless fallback provider.

This provider deliberately serves nothing. Its purpose is to let the application
boot, run, and be demonstrated with no credentials at all: the pipeline detects
that no language model is reachable and runs its deterministic path only — the
grammar-based clause extractor, the rule engine, the cost simulator, matching
and ranking are all pure Python and need no model.

What is lost without a model is recall on unusual policy phrasings, the
adversarial verification loop, and vision-based OCR escalation. The system says
so plainly rather than silently degrading.
"""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from app.agents.base import LLMProvider, LLMResponse, LLMUnavailable

T = TypeVar("T", bound=BaseModel)

_MESSAGE = (
    "No language model is configured. Set OLLAMA_API_KEY (or ANTHROPIC_API_KEY) "
    "in backend/.env to enable model-assisted extraction and verification."
)


class OfflineProvider(LLMProvider):
    name = "offline"

    def available(self) -> bool:
        # Always "available" in the sense that it can be selected — it is the
        # terminal fallback — but it never serves a completion.
        return True

    def probe(self, model: str) -> bool:
        return False

    def complete(self, **kwargs: object) -> LLMResponse:
        raise LLMUnavailable(_MESSAGE)

    def complete_structured(self, **kwargs: object) -> T:
        raise LLMUnavailable(_MESSAGE)
