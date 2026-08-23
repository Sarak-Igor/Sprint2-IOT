from fastapi import APIRouter, HTTPException

from backend.apps.ai_knowledge.agent.engine import AgentChatError, chat
from backend.apps.ai_knowledge.agent.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/agent", tags=["Agente Conversacional"])


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    try:
        resposta, fontes = chat(request.session_id, request.mensagem)
    except AgentChatError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return ChatResponse(resposta=resposta, fontes=fontes)
