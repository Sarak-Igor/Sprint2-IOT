import json
from unittest.mock import MagicMock, patch

import pytest

from backend.shared_infra import llm_client
from backend.shared_infra.llm_client import (
    LlmAllModelsFailedError,
    LlmConfigError,
    invoke_with_fallback,
)


def _fake_chat_openai_factory(models_that_fail):
    def _factory(model, **_kwargs):
        fake_llm = MagicMock(name=f"llm-{model}")
        fake_llm.model = model
        if model in models_that_fail:
            fake_llm.should_fail = True
        else:
            fake_llm.should_fail = False
        return fake_llm

    return _factory


def _run_that_fails_for_marked_llms(llm):
    if getattr(llm, "should_fail", False):
        raise RuntimeError(f"falha simulada no modelo {llm.model}")
    return f"ok:{llm.model}"


def test_invoke_with_fallback_uses_next_model_when_first_fails(tmp_path, monkeypatch):
    models_path = tmp_path / "llm_models.json"
    models_path.write_text(
        json.dumps({"models": ["modelo-a", "modelo-b"]}), encoding="utf-8"
    )
    monkeypatch.setattr(llm_client, "_MODELS_PATH", models_path)
    monkeypatch.setattr(llm_client.settings, "openrouter_api_key", "fake-key")

    with patch.object(
        llm_client, "ChatOpenAI", side_effect=_fake_chat_openai_factory({"modelo-a"})
    ):
        result = invoke_with_fallback(_run_that_fails_for_marked_llms)

    assert result == "ok:modelo-b"


def test_invoke_with_fallback_raises_when_all_models_fail(tmp_path, monkeypatch):
    models_path = tmp_path / "llm_models.json"
    models_path.write_text(
        json.dumps({"models": ["modelo-a", "modelo-b"]}), encoding="utf-8"
    )
    monkeypatch.setattr(llm_client, "_MODELS_PATH", models_path)
    monkeypatch.setattr(llm_client.settings, "openrouter_api_key", "fake-key")

    with patch.object(
        llm_client,
        "ChatOpenAI",
        side_effect=_fake_chat_openai_factory({"modelo-a", "modelo-b"}),
    ):
        with pytest.raises(LlmAllModelsFailedError):
            invoke_with_fallback(_run_that_fails_for_marked_llms)


def test_invoke_with_fallback_fails_fast_without_api_key(monkeypatch):
    monkeypatch.setattr(llm_client.settings, "openrouter_api_key", "")

    with patch.object(llm_client, "ChatOpenAI") as mock_chat_openai:
        with pytest.raises(LlmConfigError):
            invoke_with_fallback(lambda llm: llm)

    mock_chat_openai.assert_not_called()


def test_invoke_with_fallback_fails_fast_when_models_file_missing(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(llm_client, "_MODELS_PATH", tmp_path / "does-not-exist.json")
    monkeypatch.setattr(llm_client.settings, "openrouter_api_key", "fake-key")

    with patch.object(llm_client, "ChatOpenAI") as mock_chat_openai:
        with pytest.raises(LlmConfigError):
            invoke_with_fallback(lambda llm: llm)

    mock_chat_openai.assert_not_called()


def test_invoke_with_fallback_fails_fast_when_models_file_malformed(
    tmp_path, monkeypatch
):
    models_path = tmp_path / "llm_models.json"
    models_path.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(llm_client, "_MODELS_PATH", models_path)
    monkeypatch.setattr(llm_client.settings, "openrouter_api_key", "fake-key")

    with patch.object(llm_client, "ChatOpenAI") as mock_chat_openai:
        with pytest.raises(LlmConfigError):
            invoke_with_fallback(lambda llm: llm)

    mock_chat_openai.assert_not_called()


def test_invoke_with_fallback_fails_fast_when_models_list_empty(tmp_path, monkeypatch):
    models_path = tmp_path / "llm_models.json"
    models_path.write_text(json.dumps({"models": []}), encoding="utf-8")
    monkeypatch.setattr(llm_client, "_MODELS_PATH", models_path)
    monkeypatch.setattr(llm_client.settings, "openrouter_api_key", "fake-key")

    with pytest.raises(LlmConfigError):
        invoke_with_fallback(lambda llm: llm)
