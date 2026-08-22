from unittest.mock import MagicMock, patch

from backend.apps.ai_knowledge.pdf_ingestion import extract_and_chunk_pdf


def _fake_page(text):
    page = MagicMock()
    page.extract_text.return_value = text
    return page


def test_extract_and_chunk_pdf_tags_chunks_with_page_number():
    fake_reader = MagicMock()
    fake_reader.pages = [
        _fake_page("Texto da pagina um."),
        _fake_page("Texto da pagina dois."),
    ]

    with patch(
        "backend.apps.ai_knowledge.pdf_ingestion.PdfReader", return_value=fake_reader
    ):
        result = extract_and_chunk_pdf(b"fake-pdf-bytes")

    assert result.total_pages == 2
    assert [c.page for c in result.chunks] == [1, 2]
    assert result.chunks[0].text == "Texto da pagina um."
    assert result.chunks[1].text == "Texto da pagina dois."


def test_extract_and_chunk_pdf_skips_pages_without_extractable_text():
    fake_reader = MagicMock()
    fake_reader.pages = [_fake_page(""), _fake_page("Conteudo real.")]

    with patch(
        "backend.apps.ai_knowledge.pdf_ingestion.PdfReader", return_value=fake_reader
    ):
        result = extract_and_chunk_pdf(b"fake-pdf-bytes")

    assert len(result.chunks) == 1
    assert result.chunks[0].page == 2


def test_extract_and_chunk_pdf_splits_long_page_into_multiple_chunks():
    long_text = "Frase técnica sobre o motor elétrico. " * 60  # bem além de 1000 chars
    fake_reader = MagicMock()
    fake_reader.pages = [_fake_page(long_text)]

    with patch(
        "backend.apps.ai_knowledge.pdf_ingestion.PdfReader", return_value=fake_reader
    ):
        result = extract_and_chunk_pdf(b"fake-pdf-bytes")

    assert len(result.chunks) > 1
    assert all(chunk.page == 1 for chunk in result.chunks)
