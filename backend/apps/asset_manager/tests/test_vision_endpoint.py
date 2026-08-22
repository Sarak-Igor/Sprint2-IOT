import io
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.apps.asset_manager.vision import router as vision_router_module
from backend.apps.asset_manager.vision.llm_vision import PlateExtractionError
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
    mock_extract.assert_called_once_with(b"fake-jpeg-bytes", "image/jpeg")


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


def test_scan_returns_503_when_llm_unavailable():
    client = _build_client()
    image = io.BytesIO(b"fake-jpeg-bytes")

    with patch.object(
        vision_router_module,
        "extract_plate_data",
        side_effect=PlateExtractionError("OPENROUTER_API_KEY não configurada"),
    ):
        response = client.post(
            "/api/vision/scan", files={"file": ("plate.jpg", image, "image/jpeg")}
        )

    assert response.status_code == 503
