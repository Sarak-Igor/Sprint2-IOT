from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.apps.asset_manager.vision.plate_extraction import extract_plate_data
from backend.apps.asset_manager.vision.plate_llm_structurer import LlmStructuringError
from backend.apps.asset_manager.vision.schemas import PlateExtractionResult

router = APIRouter(prefix="/vision", tags=["Vision OCR"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB — mesmo limite anunciado em Vision.tsx


@router.post("/scan", response_model=PlateExtractionResult)
async def scan_motor_plate(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415, detail=f"Formato não suportado: {file.content_type}"
        )

    image_bytes = await file.read()
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Imagem maior que 10MB")

    try:
        return extract_plate_data(image_bytes)
    except LlmStructuringError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
