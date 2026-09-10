from functools import lru_cache
import os, tempfile

from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

from backend.shared_infra.database_client.postgresql import engine
from backend.apps.ai_knowledge.models import KnowledgeManualDB, KnowledgeChunkDB
import asyncio
from dotenv import load_dotenv

load_dotenv()

SMALL_COLLECTION_CHUNK_THRESHOLD = 150

# from langchain_google_genai import GoogleGenerativeAIEmbeddings

@lru_cache(maxsize=1)
def _get_embedding_model():
    """Carrega o modelo de embedding."""
    return None

def _embed_texts(texts: list[str]) -> list[list[float]]:
    # embeddings desativados
    return []


async def _run_async(coro):
    """Utilitário para rodar código assíncrono se necessário, mas como vector_store 
    é chamado por router que pode ser async, devemos idealmente refatorar tudo para async.
    Contudo, para manter paridade com a API anterior síncrona do add_chunks, 
    vamos manter a execução via loop."""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # Estamos num event loop (FastAPI). No router.py, add_chunks é chamado bloqueando.
        # Mas router.py é async def ingest_manual. Então chamar bloqueante lá era ruim.
        raise RuntimeError("Utilize a nova interface assíncrona para vector_store.")
    else:
        return loop.run_until_complete(coro)


async def add_chunks_async(chunk_ids, documents, metadatas, pdf_bytes: bytes = None):
    from backend.shared_infra.database_client.postgresql import AsyncSessionLocal
    # DESATIVADO PARA A APRESENTAÇÃO: Pulamos a vetorização (embeddings)
    # embeddings = _embed_texts(documents)

    async with AsyncSessionLocal() as session:
        # Apenas salva o arquivo PDF cru no banco de dados para listar no Frontend
        if metadatas and pdf_bytes is not None:
            first_meta = metadatas[0]
            manual_id = first_meta["manual_id"]
            
            res = await session.execute(select(KnowledgeManualDB).where(KnowledgeManualDB.manual_id == manual_id))
            manual_db = res.scalar_one_or_none()
            
            if not manual_db:
                manual_db = KnowledgeManualDB(
                    manual_id=manual_id,
                    filename=first_meta.get("source", f"{manual_id}.pdf"),
                    pdf_bytes=pdf_bytes,
                    total_pages=max([m.get("page", 0) for m in metadatas], default=0)
                )
                session.add(manual_db)

        # DESATIVADO: Não insere os chunks de texto no banco
        # for i, chunk_id in enumerate(chunk_ids): ...
            
        await session.commit()

# Retrocompatibilidade temporária ou renomear no router
async def add_chunks(*args, **kwargs):
    return await add_chunks_async(*args, **kwargs)


async def query_similar_chunks_async(question: str, n_results: int = 15):
    from backend.shared_infra.database_client.postgresql import AsyncSessionLocal
    
    question_embedding = _embed_texts([question])[0]
    
    async with AsyncSessionLocal() as session:
        # Recupera total de chunks
        count_res = await session.execute(select(func.count(KnowledgeChunkDB.chunk_id)))
        count = count_res.scalar()
        
        if count == 0:
            return []
            
        effective_n_results = (
            count if count <= SMALL_COLLECTION_CHUNK_THRESHOLD else min(n_results, count)
        )
        
        # pgvector: ordenação por distância de cosseno (<=>)
        stmt = select(KnowledgeChunkDB).order_by(KnowledgeChunkDB.embedding.cosine_distance(question_embedding)).limit(effective_n_results)
        res = await session.execute(stmt)
        chunks_db = res.scalars().all()
        
        # Formato de retorno mantendo o padrão Chroma: [(texto, metadata)]
        results = []
        for c in chunks_db:
            metadata = {
                "manual_id": c.manual_id,
                "page": c.page,
                "source": getattr(c.manual, 'filename', ''),
                "technology_tag": c.technology_tag
            }
            results.append((c.document, metadata))
            
        return results

# Retrocompatibilidade para RAG
def query_similar_chunks(question: str, n_results: int = 15):
    # O RAG engine também precisará ser async, mas por agora podemos encapsular
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # Estamos num async def answer_question ? Precisamos checar router
        raise RuntimeError("Use query_similar_chunks_async")
    return asyncio.run(query_similar_chunks_async(question, n_results))


async def list_indexed_manuals_async() -> list[dict]:
    from backend.shared_infra.database_client.postgresql import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        stmt = select(KnowledgeManualDB)
        res = await session.execute(stmt)
        manuals_db = res.scalars().all()
        
        results = []
        for m in manuals_db:
            # Conta chunks usando lazy loading ou podemos fazer subquery (otimização para o futuro)
            chunks_count_res = await session.execute(
                select(func.count(KnowledgeChunkDB.chunk_id)).where(KnowledgeChunkDB.manual_id == m.manual_id)
            )
            chunks_count = chunks_count_res.scalar()
            
            results.append({
                "manual_id": m.manual_id,
                "filename": m.filename,
                "paginas": m.total_pages,
                "chunks_indexados": chunks_count,
            })
        return results
