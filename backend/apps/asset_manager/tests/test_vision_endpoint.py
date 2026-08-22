import io
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.apps.asset_manager.vision import router as vision_router_module
from backend.apps.asset_manager.vision.ocr_engine import OcrEngineError
from backend.apps.asset_manager.vision.plate_parser import (
    NAO_LEGIVEL,
    parse_plate_fields,
)
from backend.apps.asset_manager.vision.schemas import PlateExtractionResult


def _build_client():
    app = FastAPI()
    app.include_router(vision_router_module.router, prefix="/api")
    return TestClient(app)


def _sample_result():
    return PlateExtractionResult(
        modelo="W22 Super Premium",
        potencia="7.5 kW (10 HP)",
        rpm="1750",
        carcaca="132S",
        tensao="220/380/440V",
        corrente="25.4/14.7/12.7 A",
        ip="IP55",
        classe_isol="F (ΔT 80K)",
        confianca=98.4,
    )


def test_scan_returns_structured_plate_data():
    client = _build_client()
    image = io.BytesIO(b"fake-jpeg-bytes")

    with patch.object(
        vision_router_module, "extract_plate_data", return_value=_sample_result()
    ) as mock_extract:
        response = client.post(
            "/api/vision/scan", files={"file": ("plate.jpg", image, "image/jpeg")}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["modelo"] == "W22 Super Premium"
    assert body["confianca"] == 98.4
    mock_extract.assert_called_once_with(b"fake-jpeg-bytes")


def test_scan_rejects_unsupported_content_type():
    client = _build_client()
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake")

    with patch.object(vision_router_module, "extract_plate_data") as mock_extract:
        response = client.post(
            "/api/vision/scan",
            files={"file": ("plate.pdf", fake_pdf, "application/pdf")},
        )

    assert response.status_code == 415
    mock_extract.assert_not_called()


def test_scan_rejects_oversized_image():
    client = _build_client()
    huge_image = io.BytesIO(b"0" * (10 * 1024 * 1024 + 1))

    with patch.object(vision_router_module, "extract_plate_data") as mock_extract:
        response = client.post(
            "/api/vision/scan", files={"file": ("plate.jpg", huge_image, "image/jpeg")}
        )

    assert response.status_code == 413
    mock_extract.assert_not_called()


def test_scan_returns_503_when_ocr_engine_fails():
    client = _build_client()
    image = io.BytesIO(b"fake-jpeg-bytes")

    with patch.object(
        vision_router_module,
        "extract_plate_data",
        side_effect=OcrEngineError("Não foi possível decodificar a imagem enviada"),
    ):
        response = client.post(
            "/api/vision/scan", files={"file": ("plate.jpg", image, "image/jpeg")}
        )

    assert response.status_code == 503


def test_parse_plate_fields_recognizes_well_formed_plate():
    detections = [
        ("W22 Super Premium", 92.0),
        ("7.5 kW", 88.0),
        ("1750 RPM", 95.0),
        ("132S", 90.0),
        ("220/380/440V", 93.0),
        ("25.4/14.7/12.7 A", 91.0),
        ("IP55", 89.0),
        ("CLASSE F", 87.0),
    ]

    result = parse_plate_fields(detections)

    assert result.modelo == "W22 Super Premium"
    assert result.potencia == "7.5 kW"
    assert result.rpm == "1750 RPM"
    assert result.carcaca == "132S"
    assert result.tensao == "220/380/440V"
    assert result.corrente == "25.4/14.7/12.7 A"
    assert result.ip == "IP55"
    assert result.classe_isol == "CLASSE F"
    assert result.confianca == round(sum(c for _, c in detections) / len(detections), 1)


def test_parse_plate_fields_marks_unrecognized_fields_as_nao_legivel():
    detections = [
        ("1750 RPM", 95.0),
        ("###@@@ borrão", 40.0),
        ("IP55", 89.0),
        ("xyz", 30.0),
    ]

    result = parse_plate_fields(detections)

    assert result.rpm == "1750 RPM"
    assert result.ip == "IP55"
    assert result.tensao == NAO_LEGIVEL
    assert result.corrente == NAO_LEGIVEL
    assert result.classe_isol == NAO_LEGIVEL
    assert result.potencia == NAO_LEGIVEL
    assert result.carcaca == NAO_LEGIVEL
    assert result.modelo == NAO_LEGIVEL
    assert result.confianca == round((95.0 + 89.0) / 2, 1)


def test_parse_plate_fields_returns_all_nao_legivel_without_recognizable_pattern():
    detections = [("borrão ilegível", 20.0), ("###", 10.0)]

    result = parse_plate_fields(detections)

    assert result.modelo == NAO_LEGIVEL
    assert result.potencia == NAO_LEGIVEL
    assert result.rpm == NAO_LEGIVEL
    assert result.carcaca == NAO_LEGIVEL
    assert result.tensao == NAO_LEGIVEL
    assert result.corrente == NAO_LEGIVEL
    assert result.ip == NAO_LEGIVEL
    assert result.classe_isol == NAO_LEGIVEL
    assert result.confianca == 0.0
