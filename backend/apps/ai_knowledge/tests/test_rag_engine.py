from unittest.mock import MagicMock, patch

import pytest

from backend.apps.ai_knowledge import rag_engine
from backend.apps.ai_knowledge.rag_engine import KnowledgeQueryError, answer_question


def test_answer_question_returns_graceful_message_when_no_manuals_indexed():
    with patch.object(rag_engine, "query_similar_chunks", return_value=[]):
        result = answer_question("Qual o limite de vibração?")

    assert result.fontes == []
    assert "indexado" in result.resposta.lower()


def test_answer_question_raises_when_api_key_missing(monkeypatch):
    monkeypatch.setattr(rag_engine.llm_client.settings, "openrouter_api_key", "")
    fake_chunks = [("vibracao limite 4.5mm/s", {"source": "manual.pdf", "page": 12})]

    with patch.object(rag_engine, "query_similar_chunks", return_value=fake_chunks):
        with pytest.raises(KnowledgeQueryError):
            answer_question("Qual o limite de vibração?")


def test_answer_question_returns_llm_answer_with_source_citations():
    fake_chunks = [
        ("vibracao limite 4.5mm/s RMS", {"source": "manual_w22.pdf", "page": 12})
    ]
    fake_llm_response = MagicMock(content="O limite de vibração é 4.5 mm/s RMS.")
    fake_llm = MagicMock()
    fake_llm.invoke.return_value = fake_llm_response

    with (
        patch.object(rag_engine, "query_similar_chunks", return_value=fake_chunks),
        patch.object(
            rag_engine.llm_client,
            "invoke_with_fallback",
            side_effect=lambda run, **kwargs: run(fake_llm),
        ),
    ):
        result = answer_question("Qual o limite de vibração?")

    assert result.resposta == "O limite de vibração é 4.5 mm/s RMS."
    assert result.fontes[0].manual == "manual_w22.pdf"
    assert result.fontes[0].pagina == 12
