from backend.apps.asset_manager.vision.plate_llm_structurer import structure_plate_image
from backend.apps.asset_manager.vision.schemas import PlateExtractionResult


def extract_plate_data(image_bytes: bytes) -> PlateExtractionResult:
    """Extrai os dados da imagem exclusivamente via LLM Multimodal (OpenRouter)."""
    return structure_plate_image(image_bytes)
