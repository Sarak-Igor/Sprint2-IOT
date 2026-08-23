from unittest.mock import patch

from backend.apps.ai_knowledge.agent import tools
from backend.apps.ai_knowledge.agent.tools import consultar_manuais_tecnicos
from backend.apps.ai_knowledge.schemas import AskResponse, SourceCitation


def test_tool_delegates_to_answer_question_and_preserves_sources():
    fake_ask_response = AskResponse(
        resposta="O limite de vibração é 4.5 mm/s RMS.",
        fontes=[
            SourceCitation(manual="manual_w22.pdf", pagina=12, trecho="vibracao...")
        ],
    )

    with patch.object(
        tools, "answer_question", return_value=fake_ask_response
    ) as mock_answer:
        result = consultar_manuais_tecnicos.invoke(
            {"pergunta": "Qual o limite de vibração?"}
        )

    mock_answer.assert_called_once_with("Qual o limite de vibração?")
    assert result == fake_ask_response
    assert result.fontes[0].pagina == 12
