"""M0, provider layer.

The JSON salvage parser gets the most attention here. Ollama Cloud ignores the
`format` schema parameter, so every structured extraction in the system depends
on this function surviving whatever prose a model wraps around its JSON.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from app.agents.base import LLMProvider, LLMUnavailable
from app.agents.cache import ResponseCache
from app.agents.offline_provider import OfflineProvider
from app.agents.ollama_provider import (
    VISION_CAPABLE_PREFIXES,
    OllamaProvider,
    extract_json_object,
)
from app.agents.registry import ModelRegistry, Resolution
from app.core.config import ModelRole


class Cap(BaseModel):
    amount_inr: int
    verbatim: str


# --- JSON salvage ---------------------------------------------------------


def test_plain_object():
    assert extract_json_object('{"a": 1}') == {"a": 1}


def test_strips_code_fences():
    assert extract_json_object('```json\n{"a": 1}\n```') == {"a": 1}


def test_ignores_prose_around_the_object():
    raw = 'Sure! Here is the result:\n{"a": 1}\nLet me know if you need more.'
    assert extract_json_object(raw) == {"a": 1}


def test_braces_inside_strings_do_not_truncate():
    # Policy verbatim text really does contain braces and quotes.
    raw = '{"verbatim": "Room Rent {see Annexure B} limit", "amount_inr": 5000}'
    assert extract_json_object(raw)["verbatim"] == "Room Rent {see Annexure B} limit"


def test_escaped_quotes_are_handled():
    raw = r'{"verbatim": "the \"eligible\" room", "amount_inr": 1}'
    assert extract_json_object(raw)["verbatim"] == 'the "eligible" room'


def test_nested_objects_survive():
    raw = '{"outer": {"inner": {"deep": 1}}, "n": 2}'
    assert extract_json_object(raw)["outer"]["inner"]["deep"] == 1


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "no json at all",
        "**Room rent cap:** Rs. 5,000 per day.",  # a real cloud response
        '{"unterminated": ',
        '{"bad": nope}',
    ],
)
def test_unsalvageable_input_returns_none(raw):
    assert extract_json_object(raw) is None


# --- offline provider -----------------------------------------------------


def test_offline_provider_is_selectable_but_serves_nothing():
    p = OfflineProvider()
    assert p.available() is True
    assert p.probe("anything") is False
    with pytest.raises(LLMUnavailable, match="OLLAMA_API_KEY"):
        p.complete(model="m", prompt="p")


# --- vision capability ----------------------------------------------------


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("gemma4:31b", True),
        ("minimax-m3", True),
        ("qwen3.5:397b", True),
        ("gpt-oss:120b", False),
        ("nemotron-3-super", False),
    ],
)
def test_vision_capability_detection(model, expected):
    assert OllamaProvider().supports_vision(model) is expected


def test_vision_prefix_list_is_lowercase():
    assert all(p == p.lower() for p in VISION_CAPABLE_PREFIXES)


# --- registry -------------------------------------------------------------


class FakeProvider(LLMProvider):
    """Answers only for models in `works`, and counts probes."""

    name = "fake"

    def __init__(self, works: set[str], vision: set[str] | None = None):
        self.works = works
        self.vision = vision or set()
        self.probes: list[str] = []

    def available(self) -> bool:
        return True

    def probe(self, model: str) -> bool:
        self.probes.append(model)
        return model in self.works

    def supports_vision(self, model: str) -> bool:
        return model in self.vision

    def complete(self, **kwargs):
        raise NotImplementedError

    def complete_structured(self, **kwargs):
        raise NotImplementedError


def _registry_with(provider: LLMProvider, chain: list[str]) -> ModelRegistry:
    return ModelRegistry(
        providers=[provider, OfflineProvider()],
        chain_for=lambda role: list(chain),
    )


def test_resolution_walks_the_chain_to_the_first_working_model():
    provider = FakeProvider(works={"works"})
    reg = _registry_with(provider, ["gated-a", "gated-b", "works", "never-reached"])

    res = reg.resolve(ModelRole.EXTRACT)
    assert isinstance(res, Resolution)
    assert res.model == "works"
    # Stops as soon as one answers, no wasted probes.
    assert provider.probes == ["gated-a", "gated-b", "works"]


def test_resolution_is_memoised():
    provider = FakeProvider(works={"m"})
    reg = _registry_with(provider, ["m"])

    reg.resolve(ModelRole.EXTRACT)
    reg.resolve(ModelRole.EXTRACT)
    assert provider.probes == ["m"]


def test_all_models_gated_yields_no_resolution():
    reg = _registry_with(FakeProvider(works=set()), ["a", "b"])

    assert reg.resolve(ModelRole.EXTRACT) is None
    with pytest.raises(LLMUnavailable, match="No model available"):
        reg.complete(ModelRole.EXTRACT, prompt="p")


def test_vision_role_skips_text_only_models():
    provider = FakeProvider(works={"text-only", "sees"}, vision={"sees"})
    reg = _registry_with(provider, ["text-only", "sees"])

    res = reg.resolve(ModelRole.VISION_OCR)
    assert res is not None and res.model == "sees"
    # A text-only model must never be probed for a vision role.
    assert "text-only" not in provider.probes


def test_health_reports_degraded_roles():
    reg = _registry_with(FakeProvider(works=set()), ["nope"])

    health = reg.health()
    assert health["llm_available"] is False
    assert set(health["degraded_roles"]) == {r.value for r in ModelRole}


# --- an answer that is not an answer ---------------------------------------
#
# These models occasionally return nothing at all: the call succeeds, the
# message is empty, and every layer above treats it as a reply. Both halves of
# that are covered here, because together they made one blank answer permanent.


class _Blank:
    """A client that answers with nothing, then with something."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def chat(self, **kwargs):
        self.calls += 1
        return {"message": {"content": self.replies.pop(0)}}


def test_an_empty_reply_is_asked_again_rather_than_returned(monkeypatch):
    monkeypatch.setattr("app.agents.ollama_provider.RETRY_BACKOFF_SECONDS", 0)
    provider = OllamaProvider(cache=ResponseCache(enabled=False))
    client = _Blank(["", "   ", "The policy schedule is the one that matters."])
    provider._client = client

    answer = provider.complete(model="m", prompt="which document?")

    assert answer.text == "The policy schedule is the one that matters."
    assert client.calls == 3


def test_nothing_at_all_is_a_failure_rather_than_an_answer(monkeypatch):
    monkeypatch.setattr("app.agents.ollama_provider.RETRY_BACKOFF_SECONDS", 0)
    provider = OllamaProvider(cache=ResponseCache(enabled=False))
    provider._client = _Blank(["", "", ""])

    with pytest.raises(LLMUnavailable):
        provider.complete(model="m", prompt="which document?")


def test_an_empty_answer_is_never_cached(tmp_path):
    """Cached, it would be the answer to that exact question for as long as the
    file lives, and the caller would never learn the model had given up."""
    cache = ResponseCache(tmp_path / "c.db")
    cache.set("k", "m", "")
    assert cache.get("k") is None

    cache.set("k", "m", "an answer")
    assert cache.get("k") == "an answer"
