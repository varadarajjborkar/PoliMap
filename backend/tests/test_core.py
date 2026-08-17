"""M0: configuration, telemetry and caching."""

from __future__ import annotations

import asyncio

import pytest

from app.agents.cache import ResponseCache
from app.core.config import DEFAULT_MODEL_CHAINS, ModelRole, Settings
from app.core.events import EventBus
from app.schemas.events import EventStatus, PipelineEvent, PipelineStage


# --- config ---------------------------------------------------------------


def test_every_role_has_a_default_chain():
    for role in ModelRole:
        assert DEFAULT_MODEL_CHAINS.get(role), f"{role} has no fallback chain"


def test_chain_falls_back_to_defaults_when_unset():
    s = Settings(model_extract="", ollama_api_key="k")
    assert s.chain_for(ModelRole.EXTRACT) == DEFAULT_MODEL_CHAINS[ModelRole.EXTRACT]


def test_chain_override_is_parsed_as_a_list():
    s = Settings(model_extract="a:1, b:2 ,, c:3")
    assert s.chain_for(ModelRole.EXTRACT) == ["a:1", "b:2", "c:3"]


@pytest.mark.parametrize("raw", ['  "sk-abc"  ', "'sk-abc'", "sk-abc\n"])
def test_pasted_keys_are_cleaned(raw):
    # Keys copied out of a browser routinely carry quotes or trailing newlines.
    assert Settings(ollama_api_key=raw).ollama_api_key == "sk-abc"


def test_vision_role_chain_contains_only_vision_models():
    from app.agents.ollama_provider import VISION_CAPABLE_PREFIXES

    for model in DEFAULT_MODEL_CHAINS[ModelRole.VISION_OCR]:
        assert model.lower().startswith(VISION_CAPABLE_PREFIXES), model


# --- event bus ------------------------------------------------------------


def test_step_times_and_reports_success():
    b = EventBus()
    with b.step(PipelineStage.INTAKE, "rasterize", session_id="s1") as st:
        st.ok("Rendered 3 pages", pages=3)

    started, done = b.history("s1")
    assert started.status is EventStatus.STARTED
    assert done.status is EventStatus.OK
    assert done.summary == "Rendered 3 pages"
    assert done.detail["pages"] == 3
    assert done.duration_ms is not None


def test_step_records_failure_and_reraises():
    b = EventBus()
    with pytest.raises(ValueError), b.step(PipelineStage.ATOMIZE, "parse"):
        raise ValueError("bad clause")

    assert b.history()[-1].status is EventStatus.FAILED
    assert "bad clause" in b.history()[-1].summary


def test_history_is_filtered_by_session():
    b = EventBus()
    b.publish(PipelineStage.MATCH, "a", session_id="s1")
    b.publish(PipelineStage.MATCH, "b", session_id="s2")
    assert [e.step for e in b.history("s1")] == ["a"]


def test_replay_buffer_is_bounded():
    from app.core.events import REPLAY_BUFFER_SIZE

    b = EventBus()
    for i in range(REPLAY_BUFFER_SIZE + 50):
        b.publish(PipelineStage.SYSTEM, f"step{i}")
    assert len(b.history()) == REPLAY_BUFFER_SIZE


async def test_subscriber_receives_live_events():
    b = EventBus()
    b.bind_loop(asyncio.get_running_loop())
    q, backlog = b.subscribe()
    assert backlog == []

    b.publish(PipelineStage.RANK, "ranked", summary="5 options")
    event = await asyncio.wait_for(q.get(), timeout=1.0)
    assert event.step == "ranked"

    b.unsubscribe(q)
    assert b.subscriber_count == 0


async def test_emitting_from_a_worker_thread_reaches_subscribers():
    # OCR and rasterisation run off the loop but must still report progress.
    b = EventBus()
    b.bind_loop(asyncio.get_running_loop())
    q, _ = b.subscribe()

    await asyncio.to_thread(b.publish, PipelineStage.INTAKE, "ocr_page", summary="page 1")
    event = await asyncio.wait_for(q.get(), timeout=2.0)
    assert event.step == "ocr_page"


def test_console_line_is_readable():
    line = PipelineEvent(
        stage=PipelineStage.SIMULATE,
        step="waterfall",
        summary="out-of-pocket 42,000",
        duration_ms=12.4,
    ).console_line()
    assert "S6_SIMULATE/waterfall" in line
    assert "12ms" in line


def test_every_stage_has_a_human_label():
    for stage in PipelineStage:
        assert stage.label and stage.label != stage.value


# --- cache ----------------------------------------------------------------


def test_cache_roundtrip(tmp_path):
    c = ResponseCache(tmp_path / "c.db")
    key = ResponseCache.make_key(model="m", prompt="p")
    assert c.get(key) is None
    c.set(key, "m", '{"ok":true}')
    assert c.get(key) == '{"ok":true}'
    assert c.stats()["hits"] == 1


def test_cache_key_changes_with_any_input(tmp_path):
    base = ResponseCache.make_key(model="m", prompt="p", schema={"a": 1})
    assert base != ResponseCache.make_key(model="m2", prompt="p", schema={"a": 1})
    assert base != ResponseCache.make_key(model="m", prompt="p2", schema={"a": 1})
    # A changed schema must invalidate, otherwise prompt edits silently reuse.
    assert base != ResponseCache.make_key(model="m", prompt="p", schema={"a": 2})


def test_disabled_cache_never_stores(tmp_path):
    c = ResponseCache(tmp_path / "c.db", enabled=False)
    key = ResponseCache.make_key(prompt="p")
    c.set(key, "m", "value")
    assert c.get(key) is None
