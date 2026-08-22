from typing import List

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    pergunta: str = Field(..., min_length=3, max_length=500)


class SourceCitation(BaseModel):
    manual: str
    pagina: int
    trecho: str


class AskResponse(BaseModel):
    resposta: str
    fontes: List[SourceCitation]


class IngestResponse(BaseModel):
    manual_id: str
    filename: str
    paginas: int
    chunks_indexados: int
