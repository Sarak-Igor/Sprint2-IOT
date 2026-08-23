from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.apps.ai_knowledge.agent import router as agent_router_module
from backend.apps.ai_knowledge.agent.engine import AgentChatError
from backend.apps.ai_knowledge.schemas import SourceCitation


def _build_client():
    app = FastAPI()
    app.include_router(agent_router_module.router, prefix="/api")
    return TestClient(app)


def test_chat_returns_answer_with_sources():
    client = _build_client()
    fake_fontes = [
        SourceCitation(manual="manual_w22.pdf", pagina=12, trecho="vibracao...")
    ]

    with patch.object(
        agent_router_module,
        "chat",
        return_value=("O limite de vibração é 4.5 mm/s RMS.", fake_fontes),
    ) as mock_chat:
        response = client.post(
            "/api/agent/chat",
            json={"session_id": "sessao-1", "mensagem": "Qual o limite de vibração?"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["resposta"] == "O limite de vibração é 4.5 mm/s RMS."
    assert body["fontes"][0]["pagina"] == 12
    mock_chat.assert_called_once_with("sessao-1", "Qual o limite de vibração?")


def test_chat_returns_503_when_llm_unavailable():
    client = _build_client()

    with patch.object(
        agent_router_module,
        "chat",
        side_effect=AgentChatError("OPENROUTER_API_KEY não configurada"),
    ):
        response = client.post(
            "/api/agent/chat",
            json={"session_id": "sessao-1", "mensagem": "Qual o limite de vibração?"},
        )

    assert response.status_code == 503


def test_chat_rejects_empty_message():
    client = _build_client()

    with patch.object(agent_router_module, "chat") as mock_chat:
        response = client.post(
            "/api/agent/chat", json={"session_id": "sessao-1", "mensagem": ""}
        )

    assert response.status_code == 422
    mock_chat.assert_not_called()


def test_chat_rejects_message_over_max_length():
    client = _build_client()

    with patch.object(agent_router_module, "chat") as mock_chat:
        response = client.post(
            "/api/agent/chat",
            json={"session_id": "sessao-1", "mensagem": "a" * 1001},
        )

    assert response.status_code == 422
    mock_chat.assert_not_called()
