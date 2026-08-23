from functools import lru_cache
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

from backend.shared_infra.config import settings

_COLLECTION_NAME = "manuais_tecnicos_v2"

# Teto de "coleção pequena": abaixo disso, a busca recupera todos os chunks (ignora o
# ranking do embedding) em vez de só o top-N — um manual técnico de ~4 páginas já indexa
# ~6 chunks com o splitter atual (chunk_size=1000, overlap=200); 50 chunks cobre
# confortavelmente um manual pequeno/médio inteiro (dezenas de páginas) sem estourar
# custo/latência quando a base crescer com mais manuais (plan-16).
SMALL_COLLECTION_CHUNK_THRESHOLD = 150

# Modelo multilingue 100% local e open-source para suportar o Português perfeitamente
_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)


@lru_cache(maxsize=1)
def _get_collection():
    """Coleção ChromaDB persistida em disco local, sem telemetria — 100% offline após o
    primeiro download do modelo de embedding padrão (onnxruntime, cacheado localmente)."""
    storage_path = Path(settings.knowledge_storage_path) / "vector_store"
    storage_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(storage_path), settings=ChromaSettings(anonymized_telemetry=False)
    )
    return client.get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=_embedding_fn
    )


def add_chunks(chunk_ids, documents, metadatas):
    _get_collection().add(ids=chunk_ids, documents=documents, metadatas=metadatas)


def query_similar_chunks(question: str, n_results: int = 15):
    """Retorna pares (texto, metadata) relevantes à pergunta, ou lista vazia se nenhum
    manual foi indexado ainda. Recuperação adaptativa: quando a coleção tem no máximo
    SMALL_COLLECTION_CHUNK_THRESHOLD chunks, recupera todos (um embedding local pequeno
    pode rankear mal um trecho denso — ex.: tabela técnica — abaixo do top-N); acima do
    teto, mantém o comportamento de sempre (até `n_results`), para não estourar
    custo/latência quando a base de manuais crescer."""
    collection = _get_collection()
    count = collection.count()
    if count == 0:
        return []

    effective_n_results = (
        count if count <= SMALL_COLLECTION_CHUNK_THRESHOLD else min(n_results, count)
    )
    result = collection.query(query_texts=[question], n_results=effective_n_results)
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    return list(zip(documents, metadatas))


def list_indexed_manuals() -> list[dict]:
    """Deriva a lista de manuais realmente indexados a partir dos metadados já gravados no
    ChromaDB (`source`, `page`, `manual_id`, gravados por `router.py` na ingestão) —
    agrupa os chunks por `manual_id`, sem duplicar esse estado em nenhuma estrutura
    paralela. `paginas` é a maior página vista (nº de páginas com pelo menos um chunk
    indexado); `chunks_indexados` é a contagem de chunks daquele manual. Lista vazia se
    nenhum manual foi indexado ainda (mesmo espírito de `query_similar_chunks`)."""
    collection = _get_collection()
    if collection.count() == 0:
        return []

    metadatas = collection.get(include=["metadatas"])["metadatas"]
    manuals: dict[str, dict] = {}
    for metadata in metadatas:
        manual_id = metadata["manual_id"]
        manual = manuals.setdefault(
            manual_id,
            {
                "manual_id": manual_id,
                "filename": metadata["source"],
                "paginas": 0,
                "chunks_indexados": 0,
            },
        )
        manual["paginas"] = max(manual["paginas"], metadata["page"])
        manual["chunks_indexados"] += 1

    return list(manuals.values())
