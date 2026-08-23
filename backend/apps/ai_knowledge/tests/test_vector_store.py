from unittest.mock import MagicMock, patch

from backend.apps.ai_knowledge import vector_store
from backend.apps.ai_knowledge.vector_store import (
    list_indexed_manuals,
    query_similar_chunks,
)


def test_list_indexed_manuals_returns_empty_when_collection_empty():
    fake_collection = MagicMock()
    fake_collection.count.return_value = 0

    with patch.object(vector_store, "_get_collection", return_value=fake_collection):
        result = list_indexed_manuals()

    assert result == []


def test_list_indexed_manuals_groups_interleaved_chunks_by_manual_id():
    fake_collection = MagicMock()
    fake_collection.count.return_value = 4
    fake_collection.get.return_value = {
        "metadatas": [
            {"source": "manual_a.pdf", "page": 1, "manual_id": "id-a"},
            {"source": "manual_b.pdf", "page": 1, "manual_id": "id-b"},
            {"source": "manual_a.pdf", "page": 3, "manual_id": "id-a"},
            {"source": "manual_b.pdf", "page": 2, "manual_id": "id-b"},
        ]
    }

    with patch.object(vector_store, "_get_collection", return_value=fake_collection):
        result = list_indexed_manuals()

    by_id = {manual["manual_id"]: manual for manual in result}
    assert set(by_id) == {"id-a", "id-b"}
    assert by_id["id-a"]["filename"] == "manual_a.pdf"
    assert by_id["id-a"]["paginas"] == 3
    assert by_id["id-a"]["chunks_indexados"] == 2
    assert by_id["id-b"]["filename"] == "manual_b.pdf"
    assert by_id["id-b"]["paginas"] == 2
    assert by_id["id-b"]["chunks_indexados"] == 2


def test_query_similar_chunks_returns_empty_when_collection_empty():
    fake_collection = MagicMock()
    fake_collection.count.return_value = 0

    with patch.object(vector_store, "_get_collection", return_value=fake_collection):
        result = query_similar_chunks("qual o torque a 100 rpm?")

    assert result == []
    fake_collection.query.assert_not_called()


def test_query_similar_chunks_retrieves_every_chunk_when_collection_is_small():
    count = 6
    fake_collection = MagicMock()
    fake_collection.count.return_value = count
    fake_collection.query.return_value = {
        "documents": [[f"chunk {i}" for i in range(count)]],
        "metadatas": [[{"source": "manual_w22.pdf", "page": 3}] * count],
    }

    with patch.object(vector_store, "_get_collection", return_value=fake_collection):
        result = query_similar_chunks("qual o torque a 100 rpm?", n_results=4)

    fake_collection.query.assert_called_once_with(
        query_texts=["qual o torque a 100 rpm?"], n_results=count
    )
    assert len(result) == count


def test_query_similar_chunks_retrieves_everything_exactly_at_threshold():
    count = vector_store.SMALL_COLLECTION_CHUNK_THRESHOLD
    fake_collection = MagicMock()
    fake_collection.count.return_value = count
    fake_collection.query.return_value = {"documents": [[]], "metadatas": [[]]}

    with patch.object(vector_store, "_get_collection", return_value=fake_collection):
        query_similar_chunks("pergunta", n_results=4)

    fake_collection.query.assert_called_once_with(
        query_texts=["pergunta"], n_results=count
    )


def test_query_similar_chunks_respects_n_results_when_collection_is_large():
    count = vector_store.SMALL_COLLECTION_CHUNK_THRESHOLD + 10
    fake_collection = MagicMock()
    fake_collection.count.return_value = count
    fake_collection.query.return_value = {
        "documents": [["c1", "c2", "c3", "c4"]],
        "metadatas": [[{"source": "manual.pdf", "page": i} for i in range(1, 5)]],
    }

    with patch.object(vector_store, "_get_collection", return_value=fake_collection):
        result = query_similar_chunks("pergunta", n_results=4)

    fake_collection.query.assert_called_once_with(query_texts=["pergunta"], n_results=4)
    assert len(result) == 4
