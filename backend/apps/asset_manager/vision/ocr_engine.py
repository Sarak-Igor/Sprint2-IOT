import cv2
import easyocr
import numpy as np

_LANGUAGES = ["pt", "en"]
_MAX_PIXELS = 40_000_000  # ~40MP — barreira contra decompression bomb antes do OpenCV/EasyOCR processar

_reader: easyocr.Reader | None = None


class OcrEngineError(Exception):
    """Levantada quando a imagem não pôde ser decodificada ou excede as dimensões
    seguras para processamento (mitigação de decompression bomb pedida por cyber-ia)."""


def _get_reader() -> easyocr.Reader:
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(_LANGUAGES, gpu=False)
    return _reader


def read_plate_text(image_bytes: bytes) -> list[tuple[str, float]]:
    """Chamada bruta ao motor de OCR: decodifica a imagem e devolve a lista
    (texto, confiança 0-100) detectada pelo EasyOCR — sem nenhuma lógica de negócio."""
    buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise OcrEngineError("Não foi possível decodificar a imagem enviada")

    height, width = image.shape[:2]
    if height * width > _MAX_PIXELS:
        raise OcrEngineError("Imagem excede a resolução máxima permitida para OCR")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    detections = _get_reader().readtext(gray)
    return [(text, confidence * 100) for _, text, confidence in detections]
