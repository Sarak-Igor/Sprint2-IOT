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
    technology_tag: str


@dataclass
class PdfExtractionResult:
    total_pages: int
    chunks: List[PdfChunk]


def extract_and_chunk_pdf(pdf_bytes: bytes) -> PdfExtractionResult:
    """Extrai o texto e aplica heurística de cabeçalhos (Header-based splitting):
    - Identifica linhas curtas em maiúsculas como possíveis novos tópicos/tecnologias.
    - Anexa essa tag ao chunk para evitar conflação de contexto (ex: PTC vs Bimetálicos)."""
    reader = PdfReader(io.BytesIO(pdf_bytes), strict=False)
    chunks: List[PdfChunk] = []

    current_tag = "Geral"

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if not page_text.strip():
            continue
        
        lines = page_text.split("\n")
        current_block = []
        
        for line in lines:
            line_stripped = line.strip()
            # Heurística de Cabeçalho: Curto, em MAIÚSCULAS e não é uma frase comum.
            if (
                line_stripped 
                and len(line_stripped) < 60 
                and line_stripped.isupper() 
                and not line_stripped.endswith((".", ":", ";"))
            ):
                # Descarrega o bloco anterior com a tag antiga
                if current_block:
                    block_text = "\n".join(current_block)
                    for piece in _SPLITTER.split_text(block_text):
                        chunks.append(PdfChunk(text=piece, page=page_number, technology_tag=current_tag))
                    current_block = []
                current_tag = line_stripped
                current_block.append(line_stripped)
            else:
                current_block.append(line)
        
        # Descarrega o resto da página
        if current_block:
            block_text = "\n".join(current_block)
            for piece in _SPLITTER.split_text(block_text):
                chunks.append(PdfChunk(text=piece, page=page_number, technology_tag=current_tag))

    return PdfExtractionResult(total_pages=len(reader.pages), chunks=chunks)
