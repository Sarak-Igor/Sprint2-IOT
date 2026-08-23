import io
from dataclasses import dataclass
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import pypdf.filters

# Desabilita o limite rigoroso de descompressão (zip bomb defense) do pypdf para arquivos grandes/pesados
pypdf.filters.ZLIB_MAX_OUTPUT_LENGTH = 1_000_000_000
pypdf.filters.MAX_ARRAY_BASED_STREAM_OUTPUT_LENGTH = 1_000_000_000
pypdf.filters.MAX_DECLARED_STREAM_LENGTH = 1_000_000_000

_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=300,
    separators=["\n\n", "\n", " ", ""]
)


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
    reader = PdfReader(io.BytesIO(pdf_bytes), strict=False)
    chunks: List[PdfChunk] = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if not page_text.strip():
            continue
        for piece in _SPLITTER.split_text(page_text):
            chunks.append(PdfChunk(text=piece, page=page_number))

    return PdfExtractionResult(total_pages=len(reader.pages), chunks=chunks)
