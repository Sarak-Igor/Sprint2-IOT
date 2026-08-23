from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from backend.apps.ai_knowledge.agent import engine, tools
from backend.apps.ai_knowledge.agent.engine import AgentChatError, chat
from backend.apps.ai_knowledge.schemas import AskResponse, SourceCitation


def _fake_llm_returning(ai_message: AIMessage) -> MagicMock:
    bound_llm = MagicMock()
    bound_llm.invoke.return_value = ai_message
    llm = MagicMock()
    llm.bind_tools.return_value = bound_llm
    return llm


@pytest.fixture(autouse=True)
def _clear_sessions():
    engine._sessions.clear()
    yield
    engine._sessions.clear()


def test_chat_calls_rag_tool_and_repasses_answer_with_sources_intact():
    fake_ask_response = AskResponse(
        resposta="O limite de vibração é 4.5 mm/s RMS.",
        fontes=[
            SourceCitation(manual="manual_w22.pdf", pagina=12, trecho="vibracao...")
        ],
    )
    tool_call_message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "consultar_manuais_tecnicos",
                "args": {"pergunta": "Qual o limite de vibração?"},
                "id": "call_1",
            }
        ],
    )
    fake_llm = _fake_llm_returning(tool_call_message)

    with (
        patch.object(
            engine.llm_client,
            "invoke_with_fallback",
            side_effect=lambda run, **kwargs: run(fake_llm),
        ),
        patch.object(tools, "answer_question", return_value=fake_ask_response),
    ):
        resposta, fontes = chat("sessao-1", "Qual o limite de vibração?")

    assert resposta == "O limite de vibração é 4.5 mm/s RMS."
    assert fontes == fake_ask_response.fontes


def test_chat_responds_directly_without_calling_tool_for_off_domain_question():
    direct_message = AIMessage(
        content="Não sei responder isso, só consulto manuais técnicos."
    )
    fake_llm = _fake_llm_returning(direct_message)

    with (
        patch.object(
            engine.llm_client,
            "invoke_with_fallback",
            side_effect=lambda run, **kwargs: run(fake_llm),
        ),
        patch.object(tools, "answer_question") as mock_answer_question,
    ):
        resposta, fontes = chat("sessao-1", "Qual é a capital da França?")

    assert resposta == direct_message.content
    assert fontes == []
    mock_answer_question.assert_not_called()


def test_chat_raises_agent_chat_error_when_llm_config_missing(monkeypatch):
    monkeypatch.setattr(engine.llm_client.settings, "openrouter_api_key", "")

    with pytest.raises(AgentChatError):
        chat("sessao-1", "Qual o limite de vibração?")


def test_chat_uses_and_updates_session_history_across_calls():
    first_message = AIMessage(content="Entendido, motor W22.")
    second_message = AIMessage(content="A vibração máxima do W22 é 4.5 mm/s RMS.")
    fake_llm = MagicMock()
    bound_llm = MagicMock()
    fake_llm.bind_tools.return_value = bound_llm
    bound_llm.invoke.side_effect = [first_message, second_message]

    with patch.object(
        engine.llm_client,
        "invoke_with_fallback",
        side_effect=lambda run, **kwargs: run(fake_llm),
    ):
        chat("sessao-2", "Estou falando do motor W22.")
        chat("sessao-2", "Qual a vibração máxima dele?")

    second_call_messages = bound_llm.invoke.call_args_list[1][0][0]
    human_contents = [m.content for m in second_call_messages if m.type == "human"]
    assert "Estou falando do motor W22." in human_contents
    assert "Qual a vibração máxima dele?" in human_contents


def test_chat_trims_session_history_to_max_messages():
    fake_llm = MagicMock()
    bound_llm = MagicMock()
    fake_llm.bind_tools.return_value = bound_llm
    bound_llm.invoke.side_effect = [
        AIMessage(content=f"resposta {i}")
        for i in range(engine.MAX_HISTORY_MESSAGES + 5)
    ]

    with patch.object(
        engine.llm_client,
        "invoke_with_fallback",
        side_effect=lambda run, **kwargs: run(fake_llm),
    ):
        for i in range(engine.MAX_HISTORY_MESSAGES + 5):
            chat("sessao-3", f"mensagem {i}")

    assert len(engine._sessions["sessao-3"]) == engine.MAX_HISTORY_MESSAGES
