from unittest.mock import MagicMock, patch

from backend.apps.ai_knowledge import vector_store
from backend.apps.ai_knowledge.vector_store import list_indexed_manuals


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
