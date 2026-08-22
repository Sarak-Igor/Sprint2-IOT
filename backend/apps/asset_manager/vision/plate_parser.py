import re
from statistics import mean

from backend.apps.asset_manager.vision.schemas import PlateExtractionResult

NAO_LEGIVEL = "Não legível"

_FIELD_ORDER = [
    "rpm",
    "tensao",
    "corrente",
    "ip",
    "classe_isol",
    "potencia",
    "carcaca",
    "modelo",
]

_FIELD_PATTERNS: dict[str, re.Pattern] = {
    "rpm": re.compile(r"\b\d{3,5}\s*RPM\b", re.IGNORECASE),
    "tensao": re.compile(r"\b\d{2,3}(?:/\d{2,3}){0,2}\s*V\b", re.IGNORECASE),
    "corrente": re.compile(
        r"\b\d+(?:[.,]\d+)?(?:/\d+(?:[.,]\d+)?){0,2}\s*A\b", re.IGNORECASE
    ),
    "ip": re.compile(r"\bIP\s?\d{2}\b", re.IGNORECASE),
    "classe_isol": re.compile(
        r"\b(?:CL(?:ASSE)?|ISOL(?:AMENTO)?)\.?\s*[A-H]\b", re.IGNORECASE
    ),
    "potencia": re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:kW|CV|HP)\b", re.IGNORECASE),
    "carcaca": re.compile(r"\b\d{2,3}[A-Z]{1,2}\b"),
    "modelo": re.compile(r"\b[A-Z]{1,4}\d{1,3}\b", re.IGNORECASE),
}


def parse_plate_fields(detections: list[tuple[str, float]]) -> PlateExtractionResult:
    """Estrutura o texto bruto detectado pelo OCR nos 9 campos do schema — pura, sem I/O,
    testável sem o modelo do EasyOCR carregado. Campo sem padrão reconhecível vira
    'Não legível'; nunca inventa valor. `confianca` é a média das confianças reais das
    detecções efetivamente usadas."""
    fields: dict[str, str] = {}
    used_confidences: list[float] = []

    for text, confidence in detections:
        for field in _FIELD_ORDER:
            if field in fields:
                continue
            if not _FIELD_PATTERNS[field].search(text):
                continue
            fields[field] = text.strip()
            used_confidences.append(confidence)
            break

    resolved = {field: fields.get(field, NAO_LEGIVEL) for field in _FIELD_ORDER}
    confianca = round(mean(used_confidences), 1) if used_confidences else 0.0
    return PlateExtractionResult(confianca=confianca, **resolved)
