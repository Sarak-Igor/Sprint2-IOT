from unittest.mock import patch

from backend.apps.asset_manager.vision import plate_extraction
from backend.apps.asset_manager.vision.plate_llm_structurer import LlmStructuringError
from backend.apps.asset_manager.vision.schemas import PlateExtractionResult


def _sample_result(**overrides):
    base = dict(
        modelo="W22 Super Premium",
        potencia="7.5 kW",
        rpm="1750",
        carcaca="132S",
        tensao="220/380/440V",
        corrente="25.4/14.7/12.7 A",
        ip="IP55",
        classe_isol="F",
        confianca=95.0,
    )
    base.update(overrides)
    return PlateExtractionResult(**base)


def test_extract_plate_data_uses_llm_result_when_available():
    noisy_detections = [("VV22 l75O RPM", 55.0)]  # ruído que o regex sozinho rejeitaria
    llm_result = _sample_result()

    with (
        patch.object(
            plate_extraction, "read_plate_text", return_value=noisy_detections
        ),
        patch.object(
            plate_extraction, "structure_plate_text", return_value=llm_result
        ) as mock_structure,
        patch.object(plate_extraction, "parse_plate_fields") as mock_parse,
    ):
        result = plate_extraction.extract_plate_data(b"fake-image-bytes")

    assert result == llm_result
    mock_structure.assert_called_once_with(noisy_detections)
    mock_parse.assert_not_called()


def test_extract_plate_data_falls_back_to_regex_when_llm_fails():
    detections = [("1750 RPM", 90.0)]
    fallback_result = _sample_result(rpm="1750 RPM")

    with (
        patch.object(plate_extraction, "read_plate_text", return_value=detections),
        patch.object(
            plate_extraction,
            "structure_plate_text",
            side_effect=LlmStructuringError("OPENROUTER_API_KEY não configurada"),
        ),
        patch.object(
            plate_extraction, "parse_plate_fields", return_value=fallback_result
        ) as mock_parse,
    ):
        result = plate_extraction.extract_plate_data(b"fake-image-bytes")

    assert result == fallback_result
    mock_parse.assert_called_once_with(detections)


def test_extract_plate_data_skips_llm_when_no_detections():
    fallback_result = _sample_result()

    with (
        patch.object(plate_extraction, "read_plate_text", return_value=[]),
        patch.object(plate_extraction, "structure_plate_text") as mock_structure,
        patch.object(
            plate_extraction, "parse_plate_fields", return_value=fallback_result
        ) as mock_parse,
    ):
        result = plate_extraction.extract_plate_data(b"fake-image-bytes")

    assert result == fallback_result
    mock_structure.assert_not_called()
    mock_parse.assert_called_once_with([])


def test_extract_plate_data_never_passes_image_bytes_to_llm():
    detections = [("IP55", 88.0)]
    raw_bytes = b"raw-image-bytes-should-stay-local"

    with (
        patch.object(
            plate_extraction, "read_plate_text", return_value=detections
        ) as mock_read,
        patch.object(
            plate_extraction, "structure_plate_text", return_value=_sample_result()
        ) as mock_structure,
    ):
        plate_extraction.extract_plate_data(raw_bytes)

    mock_read.assert_called_once_with(raw_bytes)
    mock_structure.assert_called_once_with(detections)
    assert raw_bytes not in mock_structure.call_args.args
