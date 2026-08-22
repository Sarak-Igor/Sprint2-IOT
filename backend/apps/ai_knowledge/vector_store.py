from functools import lru_cache
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.shared_infra.config import settings

_COLLECTION_NAME = "manuais_tecnicos"


@lru_cache(maxsize=1)
def _get_collection():
    """Coleção ChromaDB persistida em disco local, sem telemetria — 100% offline após o
    primeiro download do modelo de embedding padrão (onnxruntime, cacheado localmente)."""
    storage_path = Path(settings.knowledge_storage_path) / "vector_store"
    storage_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(storage_path), settings=ChromaSettings(anonymized_telemetry=False)
    )
    return client.get_or_create_collection(_COLLECTION_NAME)


def add_chunks(chunk_ids, documents, metadatas):
    _get_collection().add(ids=chunk_ids, documents=documents, metadatas=metadatas)


def query_similar_chunks(question: str, n_results: int = 4):
    """Retorna até `n_results` pares (texto, metadata) mais similares à pergunta, ou lista
    vazia se nenhum manual foi indexado ainda."""
    collection = _get_collection()
    count = collection.count()
    if count == 0:
        return []

    result = collection.query(query_texts=[question], n_results=min(n_results, count))
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    return list(zip(documents, metadatas))
