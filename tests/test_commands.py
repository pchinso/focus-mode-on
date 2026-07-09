"""Tests for the AI command layer's heuristic fallback (no API key)."""

from __future__ import annotations

import pytest

from app.ai.commands import AICommandLayer, Intent


@pytest.fixture(autouse=True)
def _no_openai_env(monkeypatch):
    """Ensure a real OPENAI_API_KEY in the environment can't leak into tests."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def make_layer() -> AICommandLayer:
    """A command layer with no API key -> always heuristic mode."""
    return AICommandLayer(api_key=None)


def test_not_available_without_key():
    assert make_layer().available is False


def test_new_project_intent():
    layer = make_layer()
    result = layer.interpret("start a new work project called Migration", [])
    assert result.source == "heuristic"
    assert result.intents
    intent = result.intents[0]
    assert intent.action == "create_thread"
    assert intent.thread_path == "work"
    assert "migration" in intent.title.lower()


def test_completion_intent_targets_known_thread():
    layer = make_layer()
    result = layer.interpret(
        "finished the landing page hero copy", ["work/website/landing-page"]
    )
    intent = result.intents[0]
    assert intent.action == "complete_task"
    assert intent.thread_path == "work/website/landing-page"


def test_new_thread_recognized_despite_typo():
    """'new thead DEV' (misspelled) is still a create_thread, not 'nothing'."""
    layer = make_layer()
    result = layer.interpret("new thead DEV", [])
    assert result.intents, "must not be dropped as nothing-to-do"
    intent = result.intents[0]
    assert intent.action == "create_thread"
    assert "dev" in intent.title.lower()


def test_default_is_create_task():
    layer = make_layer()
    result = layer.interpret("email the accountant", [])
    assert result.intents[0].action == "create_task"


def test_low_confidence_needs_confirmation():
    intent = Intent("create_task", "work", "x", confidence=0.5)
    assert intent.needs_confirmation is True
    high = Intent("create_task", "work", "x", confidence=0.9)
    assert high.needs_confirmation is False


def test_empty_input_yields_nothing():
    result = make_layer().interpret("   ", [])
    assert result.intents == []
