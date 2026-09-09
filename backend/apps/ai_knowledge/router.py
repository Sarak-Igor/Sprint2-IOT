import uuid
from io import BytesIO

from fastapi import APIRouter, File, HTTPException, UploadFile, Response
from sqlalchemy import select

from backend.apps.ai_knowledge.pdf_ingestion import extract_and_chunk_pdf
from backend.apps.ai_knowledge.rag_engine import KnowledgeQueryError, answer_question
from backend.apps.ai_knowledge.schemas import (
    AskRequest,
    AskResponse,
    IngestResponse,
    ManualInfo,
    AutoIngestRequest,
)
from backend.apps.ai_knowledge.vector_store import add_chunks_async, list_indexed_manuals_async
from backend.shared_infra.database_client.postgresql import AsyncSessionLocal
from backend.apps.ai_knowledge.models import KnowledgeManualDB

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base (RAG)"])

MAX_PDF_BYTES = 100 * 1024 * 1024  # 100MB

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
    
    # Salva no banco de dados (vetores + arquivo binário)
    await add_chunks_async(chunk_ids, documents, metadatas, pdf_bytes)

    return IngestResponse(
        manual_id=manual_id,
        filename=filename,
        paginas=extraction.total_pages,
        chunks_indexados=len(extraction.chunks),
    )


@router.post("/auto-ingest-manual", response_model=IngestResponse)
async def auto_ingest_manual(request: AutoIngestRequest):
    import httpx
    
    filename = f"manual_{request.marca.lower().replace(' ', '_')}_{request.modelo.lower().replace(' ', '_')}.pdf"
    
    # 1. Verifica se já não foi indexado para evitar duplicatas
    indexed = await list_indexed_manuals_async()
    for manual in indexed:
        if manual["filename"] == filename:
            return IngestResponse(
                manual_id=manual["manual_id"],
                filename=manual["filename"],
                paginas=manual["paginas"],
                chunks_indexados=manual["chunks_indexados"],
            )

    # 2. Pesquisa na web (DuckDuckGo Search)
    import anyio
    query = f"{request.marca} {request.modelo} motor filetype:pdf"
    urls = []
    
    def _search_ddg():
        from duckduckgo_search import DDGS
        ddgs = DDGS()
        return ddgs.text(query, max_results=10)

    try:
        results = await anyio.to_thread.run_sync(_search_ddg)
        urls = [r["href"] for r in results if "href" in r]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro na busca via DDGS: {exc}")
    
    if not urls:
        raise HTTPException(status_code=404, detail="Nenhum resultado encontrado para o manual")

    pdf_url = None
    pdf_bytes = b""
    
    # 3. Validação Real via HTTP HEAD/GET
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        for url in urls:
            try:
                head_resp = await client.head(url)
                if head_resp.status_code == 405:
                    async with client.stream("GET", url) as stream_resp:
                        content_type = stream_resp.headers.get("Content-Type", "")
                else:
                    content_type = head_resp.headers.get("Content-Type", "")
                
                if "application/pdf" in content_type.lower() or url.lower().endswith(".pdf"):
                    resp = await client.get(url)
                    resp.raise_for_status()
                    candidate_bytes = resp.content
                    if b"%PDF" in candidate_bytes[:10]:
                        pdf_url = url
                        pdf_bytes = candidate_bytes
                        break
            except Exception:
                continue

    if not pdf_url or not pdf_bytes:
        raise HTTPException(status_code=404, detail="Manual em PDF não encontrado nos links verificados")
        
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF muito grande")

    # 4. Extrai e indexa 
    try:
        extraction = extract_and_chunk_pdf(pdf_bytes)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"PDF inválido: {exc}")

    if not extraction.chunks:
        raise HTTPException(status_code=422, detail="Não foi possível extrair texto do PDF baixado")

    manual_id = str(uuid.uuid4())

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
    
    await add_chunks_async(chunk_ids, documents, metadatas, pdf_bytes)

    return IngestResponse(
        manual_id=manual_id,
        filename=filename,
        paginas=extraction.total_pages,
        chunks_indexados=len(extraction.chunks),
    )


@router.post("/ask", response_model=AskResponse)
async def ask_knowledge_base(request: AskRequest):
    try:
        # A resposta pode bloquear um pouco o event loop pela inferência (se for local)
        # Idealmente deveria rodar num thread ou usar endpoint async completo
        import anyio
        return await anyio.to_thread.run_sync(answer_question, request.pergunta)
    except KnowledgeQueryError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/manuals", response_model=list[ManualInfo])
async def list_manuals():
    """Lista os manuais realmente indexados no banco Neon."""
    indexed = await list_indexed_manuals_async()
    
    # Busca tamanho e preenche o restante
    results = []
    async with AsyncSessionLocal() as session:
        for manual in indexed:
            # Pegando o tamanho do PDF a partir do banco de dados para popular o schema
            stmt = select(KnowledgeManualDB).where(KnowledgeManualDB.manual_id == manual["manual_id"])
            res = await session.execute(stmt)
            manual_db = res.scalar_one_or_none()
            size = len(manual_db.pdf_bytes) if manual_db and manual_db.pdf_bytes else 0
            
            results.append(
                ManualInfo(
                    manual_id=manual["manual_id"],
                    filename=manual["filename"],
                    paginas=manual["paginas"],
                    chunks_indexados=manual["chunks_indexados"],
                    tamanho_bytes=size,
                    download_url=f"/api/knowledge/manuals/{manual['manual_id']}/download",
                )
            )
    return results


@router.get("/manuals/{manual_id}/download")
async def download_manual(manual_id: str):
    """Serve o PDF original a partir da coluna bytea do banco Neon."""
    async with AsyncSessionLocal() as session:
        stmt = select(KnowledgeManualDB).where(KnowledgeManualDB.manual_id == manual_id)
        res = await session.execute(stmt)
        manual_db = res.scalar_one_or_none()
        
        if not manual_db or not manual_db.pdf_bytes:
            raise HTTPException(status_code=404, detail="Manual não encontrado")
            
        return Response(
            content=manual_db.pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{manual_db.filename}"'
            }
        )
