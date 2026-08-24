import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.apps.ai_knowledge.pdf_ingestion import extract_and_chunk_pdf
from backend.apps.ai_knowledge.rag_engine import KnowledgeQueryError, answer_question
from backend.apps.ai_knowledge.schemas import (
    AskRequest,
    AskResponse,
    IngestResponse,
    ManualInfo,
    AutoIngestRequest,
)
from backend.apps.ai_knowledge.vector_store import add_chunks, list_indexed_manuals
from backend.shared_infra.config import settings

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base (RAG)"])

MAX_PDF_BYTES = 100 * 1024 * 1024  # 100MB


def _pdf_dir() -> Path:
    return Path(settings.knowledge_storage_path) / "pdfs"


def _pdf_size_or_zero(manual_id: str) -> int:
    pdf_path = _pdf_dir() / f"{manual_id}.pdf"
    return pdf_path.stat().st_size if pdf_path.exists() else 0


def _resolve_manual_pdf_path(manual_id: str) -> Path:
    """Resolve o caminho do PDF local a partir do manual_id da URL, confirmando que o
    resultado continua dentro de `pdf_dir` — defesa contra path traversal via o
    parâmetro vindo do cliente, mesmo espírito do `_save_pdf_locally` acima."""
    pdf_dir = _pdf_dir().resolve()
    candidate = (pdf_dir / f"{manual_id}.pdf").resolve()
    if pdf_dir not in candidate.parents:
        raise HTTPException(status_code=404, detail="Manual não encontrado")
    return candidate


def _save_pdf_locally(manual_id: str, pdf_bytes: bytes) -> None:
    """Salva o PDF original em disco local (settings.knowledge_storage_path) — nunca via
    storage_client/Cloudflare R2, decisão explícita do usuário para esta feature. O nome do
    arquivo usa só o manual_id (gerado pelo servidor), nunca o filename enviado pelo cliente,
    para não abrir caminho de path traversal."""
    pdf_dir = _pdf_dir()
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
        max_mb = MAX_PDF_BYTES // (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"PDF maior que {max_mb}MB")

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
        {
            "source": filename,
            "page": chunk.page,
            "manual_id": manual_id,
            "technology_tag": chunk.technology_tag,
        }
        for chunk in extraction.chunks
    ]
    add_chunks(chunk_ids, documents, metadatas)

    return IngestResponse(
        manual_id=manual_id,
        filename=filename,
        paginas=extraction.total_pages,
        chunks_indexados=len(extraction.chunks),
    )


@router.post("/auto-ingest-manual", response_model=IngestResponse)
async def auto_ingest_manual(request: AutoIngestRequest):
    import httpx
    from googlesearch import search
    
    filename = f"manual_{request.marca.lower().replace(' ', '_')}_{request.modelo.lower().replace(' ', '_')}.pdf"
    
    # 1. Verifica se já não foi indexado para evitar duplicatas
    indexed = list_indexed_manuals()
    for manual in indexed:
        if manual["filename"] == filename:
            # Já existe, retorna os dados dele sem rebaixar
            return IngestResponse(
                manual_id=manual["manual_id"],
                filename=manual["filename"],
                paginas=manual["paginas"],
                chunks_indexados=manual["chunks_indexados"],
            )

    # 2. Pesquisa na web
    query = f"{request.marca} {request.modelo} motor elétrico manual filetype:pdf"
    urls = []
    try:
        urls = list(search(query, num_results=5, sleep_interval=2))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro na busca: {exc}")
    
    pdf_url = None
    for url in urls:
        if url.lower().endswith(".pdf"):
            pdf_url = url
            break
            
    if not pdf_url:
        raise HTTPException(status_code=404, detail="Manual em PDF não encontrado na web")
        
    # 3. Baixa o PDF
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(pdf_url)
            resp.raise_for_status()
            pdf_bytes = resp.content
            if b"%PDF" not in pdf_bytes[:10]:
                raise ValueError("Arquivo não é um PDF válido")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao baixar manual: {exc}")
        
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF muito grande")

    # 4. Extrai e indexa (mesma lógica do ingest normal)
    try:
        extraction = extract_and_chunk_pdf(pdf_bytes)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"PDF inválido: {exc}")

    if not extraction.chunks:
        raise HTTPException(status_code=422, detail="Não foi possível extrair texto do PDF baixado")

    manual_id = str(uuid.uuid4())
    _save_pdf_locally(manual_id, pdf_bytes)

    chunk_ids = [f"{manual_id}-{i}" for i in range(len(extraction.chunks))]
    documents = [chunk.text for chunk in extraction.chunks]
    metadatas = [
        {
            "source": filename,
            "page": chunk.page,
            "manual_id": manual_id,
            "technology_tag": chunk.technology_tag,
        }
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


@router.get("/manuals", response_model=list[ManualInfo])
async def list_manuals():
    """Lista os manuais realmente indexados no vetor-store — nenhum valor fixo, deriva do
    estado real do RAG (`list_indexed_manuals`)."""
    return [
        ManualInfo(
            manual_id=manual["manual_id"],
            filename=manual["filename"],
            paginas=manual["paginas"],
            chunks_indexados=manual["chunks_indexados"],
            tamanho_bytes=_pdf_size_or_zero(manual["manual_id"]),
            download_url=f"/api/knowledge/manuals/{manual['manual_id']}/download",
        )
        for manual in list_indexed_manuals()
    ]


@router.get("/manuals/{manual_id}/download")
async def download_manual(manual_id: str):
    """Serve o PDF original a partir do disco local — sem storage_client/Cloudflare R2,
    decisão já tomada para `ai_knowledge` (`00-contexto.md §8`)."""
    pdf_path = _resolve_manual_pdf_path(manual_id)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Manual não encontrado")
    return FileResponse(pdf_path, media_type="application/pdf", filename=pdf_path.name)
