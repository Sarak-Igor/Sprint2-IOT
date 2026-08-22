from backend.apps.asset_manager.vision.ocr_engine import read_plate_text
from backend.apps.asset_manager.vision.plate_llm_structurer import (
    LlmStructuringError,
    structure_plate_text,
)
from backend.apps.asset_manager.vision.plate_parser import parse_plate_fields
from backend.apps.asset_manager.vision.schemas import PlateExtractionResult


def extract_plate_data(image_bytes: bytes) -> PlateExtractionResult:
    """Decodifica a imagem via OCR local (`ocr_engine`) e estrutura o texto detectado —
    via LLM de texto quando disponível (`plate_llm_structurer`, tolerante a ruído de OCR;
    recebe só as strings detectadas, nunca a imagem), com fallback automático para a
    heurística por regex (`plate_parser`) quando o LLM não está configurado ou falha, para
    a feature continuar funcionando 100% offline sem chave de API."""
    detections = read_plate_text(image_bytes)
    if not detections:
        return parse_plate_fields(detections)

    try:
        return structure_plate_text(detections)
    except LlmStructuringError:
        return parse_plate_fields(detections)
