from typing import List

from pydantic import BaseModel, Field

from backend.apps.ai_knowledge.schemas import SourceCitation


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100)
    mensagem: str = Field(..., min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    resposta: str
    fontes: List[SourceCitation] = Field(default_factory=list)
