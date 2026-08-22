import io
from dataclasses import dataclass
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

_SPLITTER = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)


@dataclass
class PdfChunk:
    text: str
    page: int


@dataclass
class PdfExtractionResult:
    total_pages: int
    chunks: List[PdfChunk]


def extract_and_chunk_pdf(pdf_bytes: bytes) -> PdfExtractionResult:
    """Extrai o texto de cada página do PDF e divide em chunks (~1000 chars, overlap 200,
    conforme rag_base/structure_guide.md), preservando de qual página cada chunk veio —
    necessário para citar a fonte na resposta (critério de aceite da plan)."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    chunks: List[PdfChunk] = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if not page_text.strip():
            continue
        for piece in _SPLITTER.split_text(page_text):
            chunks.append(PdfChunk(text=piece, page=page_number))

    return PdfExtractionResult(total_pages=len(reader.pages), chunks=chunks)
