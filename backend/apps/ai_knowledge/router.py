import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.apps.ai_knowledge.pdf_ingestion import extract_and_chunk_pdf
from backend.apps.ai_knowledge.rag_engine import KnowledgeQueryError, answer_question
from backend.apps.ai_knowledge.schemas import AskRequest, AskResponse, IngestResponse
from backend.apps.ai_knowledge.vector_store import add_chunks
from backend.shared_infra.config import settings

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base (RAG)"])

MAX_PDF_BYTES = 20 * 1024 * 1024  # 20MB


def _save_pdf_locally(manual_id: str, pdf_bytes: bytes) -> None:
    """Salva o PDF original em disco local (settings.knowledge_storage_path) — nunca via
    storage_client/Cloudflare R2, decisão explícita do usuário para esta feature. O nome do
    arquivo usa só o manual_id (gerado pelo servidor), nunca o filename enviado pelo cliente,
    para não abrir caminho de path traversal."""
    pdf_dir = Path(settings.knowledge_storage_path) / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    (pdf_dir / f"{manual_id}.pdf").write_bytes(pdf_bytes)


@router.post("/ingest", response_model=IngestResponse)
async def ingest_manual(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=415, detail=f"Formato não suportado: {file.content_type}"
        )

    pdf_bytes = await file.read()
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF maior que 20MB")

    try:
        extraction = extract_and_chunk_pdf(pdf_bytes)
    except Exception as exc:
        raise HTTPException(
            status_code=422, detail=f"PDF inválido ou corrompido: {exc}"
        )

    if not extraction.chunks:
        raise HTTPException(
            status_code=422, detail="Não foi possível extrair texto do PDF"
        )

    manual_id = str(uuid.uuid4())
    filename = file.filename or "manual.pdf"
    _save_pdf_locally(manual_id, pdf_bytes)

    chunk_ids = [f"{manual_id}-{i}" for i in range(len(extraction.chunks))]
    documents = [chunk.text for chunk in extraction.chunks]
    metadatas = [
        {"source": filename, "page": chunk.page, "manual_id": manual_id}
        for chunk in extraction.chunks
    ]
    add_chunks(chunk_ids, documents, metadatas)

    return IngestResponse(
        manual_id=manual_id,
        filename=filename,
        paginas=extraction.total_pages,
        chunks_indexados=len(extraction.chunks),
    )


@router.post("/ask", response_model=AskResponse)
async def ask_knowledge_base(request: AskRequest):
    try:
        return answer_question(request.pergunta)
    except KnowledgeQueryError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
