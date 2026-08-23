import io
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.apps.ai_knowledge import router as knowledge_router_module
from backend.apps.ai_knowledge.pdf_ingestion import PdfChunk, PdfExtractionResult
from backend.apps.ai_knowledge.rag_engine import KnowledgeQueryError
from backend.apps.ai_knowledge.schemas import AskResponse, SourceCitation


def _build_client():
    app = FastAPI()
    app.include_router(knowledge_router_module.router, prefix="/api")
    return TestClient(app)


def test_ingest_rejects_non_pdf():
    client = _build_client()

    with patch.object(knowledge_router_module, "extract_and_chunk_pdf") as mock_extract:
        response = client.post(
            "/api/knowledge/ingest",
            files={"file": ("m.txt", io.BytesIO(b"x"), "text/plain")},
        )

    assert response.status_code == 415
    mock_extract.assert_not_called()


def test_ingest_rejects_oversized_pdf():
    client = _build_client()
    huge = io.BytesIO(b"0" * (20 * 1024 * 1024 + 1))

    with patch.object(knowledge_router_module, "extract_and_chunk_pdf") as mock_extract:
        response = client.post(
            "/api/knowledge/ingest", files={"file": ("m.pdf", huge, "application/pdf")}
        )

    assert response.status_code == 413
    mock_extract.assert_not_called()


def test_ingest_indexes_pdf_chunks_with_page_metadata_and_saves_locally(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        knowledge_router_module.settings, "knowledge_storage_path", str(tmp_path)
    )
    client = _build_client()
    fake_extraction = PdfExtractionResult(
        total_pages=2,
        chunks=[
            PdfChunk(text="motor trifasico", page=1),
            PdfChunk(text="vibracao limite", page=2),
        ],
    )

    with (
        patch.object(
            knowledge_router_module,
            "extract_and_chunk_pdf",
            return_value=fake_extraction,
        ),
        patch.object(knowledge_router_module, "add_chunks") as mock_add,
    ):
        response = client.post(
            "/api/knowledge/ingest",
            files={
                "file": ("manual_w22.pdf", io.BytesIO(b"%PDF-fake"), "application/pdf")
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["chunks_indexados"] == 2
    assert body["paginas"] == 2
    assert body["filename"] == "manual_w22.pdf"

    _, documents, metadatas = mock_add.call_args[0]
    assert documents == ["motor trifasico", "vibracao limite"]
    assert metadatas[0] == {
        "source": "manual_w22.pdf",
        "page": 1,
        "manual_id": body["manual_id"],
    }

    # PDF salvo em disco local (settings.knowledge_storage_path), não via storage_client/R2
    saved_files = list((tmp_path / "pdfs").glob("*.pdf"))
    assert len(saved_files) == 1
    assert saved_files[0].name == f"{body['manual_id']}.pdf"


def test_ingest_rejects_pdf_with_no_extractable_text(tmp_path, monkeypatch):
    monkeypatch.setattr(
        knowledge_router_module.settings, "knowledge_storage_path", str(tmp_path)
    )
    client = _build_client()
    empty_extraction = PdfExtractionResult(total_pages=1, chunks=[])

    with (
        patch.object(
            knowledge_router_module,
            "extract_and_chunk_pdf",
            return_value=empty_extraction,
        ),
        patch.object(knowledge_router_module, "add_chunks") as mock_add,
    ):
        response = client.post(
            "/api/knowledge/ingest",
            files={
                "file": ("scan_ruim.pdf", io.BytesIO(b"%PDF-fake"), "application/pdf")
            },
        )

    assert response.status_code == 422
    mock_add.assert_not_called()


def test_ask_returns_answer_with_sources():
    client = _build_client()
    fake_answer = AskResponse(
        resposta="O limite de vibração é 4.5 mm/s RMS.",
        fontes=[
            SourceCitation(
                manual="manual_w22.pdf", pagina=12, trecho="vibracao limite..."
            )
        ],
    )

    with patch.object(
        knowledge_router_module, "answer_question", return_value=fake_answer
    ) as mock_answer:
        response = client.post(
            "/api/knowledge/ask", json={"pergunta": "Qual o limite de vibração?"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["fontes"][0]["pagina"] == 12
    mock_answer.assert_called_once_with("Qual o limite de vibração?")


def test_ask_returns_503_when_llm_unavailable():
    client = _build_client()

    with patch.object(
        knowledge_router_module,
        "answer_question",
        side_effect=KnowledgeQueryError("OPENROUTER_API_KEY não configurada"),
    ):
        response = client.post(
            "/api/knowledge/ask", json={"pergunta": "pergunta valida aqui"}
        )

    assert response.status_code == 503


def test_ask_rejects_too_short_question():
    client = _build_client()

    with patch.object(knowledge_router_module, "answer_question") as mock_answer:
        response = client.post("/api/knowledge/ask", json={"pergunta": "oi"})

    assert response.status_code == 422
    mock_answer.assert_not_called()


def test_list_manuals_returns_manuals_derived_from_vector_store(tmp_path, monkeypatch):
    monkeypatch.setattr(
        knowledge_router_module.settings, "knowledge_storage_path", str(tmp_path)
    )
    client = _build_client()
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    pdf_bytes = b"%PDF-fake-content"
    (pdf_dir / "id-a.pdf").write_bytes(pdf_bytes)

    fake_manuals = [
        {
            "manual_id": "id-a",
            "filename": "manual_a.pdf",
            "paginas": 3,
            "chunks_indexados": 5,
        }
    ]

    with patch.object(
        knowledge_router_module, "list_indexed_manuals", return_value=fake_manuals
    ):
        response = client.get("/api/knowledge/manuals")

    assert response.status_code == 200
    body = response.json()
    assert body == [
        {
            "manual_id": "id-a",
            "filename": "manual_a.pdf",
            "paginas": 3,
            "chunks_indexados": 5,
            "tamanho_bytes": len(pdf_bytes),
            "download_url": "/api/knowledge/manuals/id-a/download",
        }
    ]


def test_list_manuals_returns_empty_list_when_no_manual_indexed():
    client = _build_client()

    with patch.object(knowledge_router_module, "list_indexed_manuals", return_value=[]):
        response = client.get("/api/knowledge/manuals")

    assert response.status_code == 200
    assert response.json() == []


def test_list_manuals_returns_zero_size_when_pdf_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        knowledge_router_module.settings, "knowledge_storage_path", str(tmp_path)
    )
    client = _build_client()
    fake_manuals = [
        {
            "manual_id": "id-orfao",
            "filename": "manual.pdf",
            "paginas": 1,
            "chunks_indexados": 1,
        }
    ]

    with patch.object(
        knowledge_router_module, "list_indexed_manuals", return_value=fake_manuals
    ):
        response = client.get("/api/knowledge/manuals")

    assert response.status_code == 200
    assert response.json()[0]["tamanho_bytes"] == 0


def test_download_manual_returns_pdf_when_file_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(
        knowledge_router_module.settings, "knowledge_storage_path", str(tmp_path)
    )
    client = _build_client()
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    pdf_bytes = b"%PDF-fake-content"
    (pdf_dir / "id-a.pdf").write_bytes(pdf_bytes)

    response = client.get("/api/knowledge/manuals/id-a/download")

    assert response.status_code == 200
    assert response.content == pdf_bytes
    assert response.headers["content-type"] == "application/pdf"


def test_download_manual_returns_404_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        knowledge_router_module.settings, "knowledge_storage_path", str(tmp_path)
    )
    client = _build_client()

    response = client.get("/api/knowledge/manuals/nao-existe/download")

    assert response.status_code == 404
