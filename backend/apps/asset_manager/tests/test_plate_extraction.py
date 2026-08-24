from unittest.mock import patch

from backend.apps.asset_manager.vision import plate_extraction
from backend.apps.asset_manager.vision.plate_llm_structurer import LlmStructuringError
from backend.apps.asset_manager.vision.schemas import PlateExtractionResult


def _sample_result() -> PlateExtractionResult:
    return PlateExtractionResult(
        marca="WEG", 
        modelo="W22", 
        potencia="10.0 HP", 
        rpm="1750", 
        carcaca="132S",
        tensao="220V",
        corrente="10A",
        ip="IP55",
        classe_isol="F",
        confianca=95.0
    )


def test_extract_plate_data_uses_llm_result_directly():
    llm_result = _sample_result()

    with (
        patch.object(
            plate_extraction, "structure_plate_image", return_value=llm_result
        ) as mock_structure,
        patch.object(plate_extraction, "read_plate_text") as mock_read,
    ):
        result = plate_extraction.extract_plate_data(b"fake-image-bytes")

    assert result == llm_result
    mock_structure.assert_called_once_with(b"fake-image-bytes")
    # OCR não deve ser chamado se o LLM tiver sucesso
    mock_read.assert_not_called()


def test_extract_plate_data_falls_back_to_ocr_when_llm_fails():
    fallback_result = _sample_result()

    with (
        patch.object(
            plate_extraction,
            "structure_plate_image",
            side_effect=LlmStructuringError("OPENROUTER_API_KEY não configurada"),
        ) as mock_structure,
        patch.object(plate_extraction, "read_plate_text", return_value=[]) as mock_read,
        patch.object(
            plate_extraction, "parse_plate_fields", return_value=fallback_result
        ) as mock_parse,
    ):
        result = plate_extraction.extract_plate_data(b"fake-image-bytes")

    assert result == fallback_result
    mock_structure.assert_called_once_with(b"fake-image-bytes")
    mock_read.assert_called_once_with(b"fake-image-bytes")
    mock_parse.assert_called_once_with([])
