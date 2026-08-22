from pydantic import BaseModel, Field


class PlateExtractionResult(BaseModel):
    """Saída estruturada da heurística de OCR local (`plate_parser`) — nunca retornada ao
    cliente sem passar por esta validação. Campos como string (não numéricos) porque uma
    placa real mistura formatos (ex.: tensão tripla '220/380/440V', carcaça '132S')."""

    modelo: str = Field(..., min_length=1, max_length=120)
    potencia: str = Field(..., min_length=1, max_length=60)
    rpm: str = Field(..., min_length=1, max_length=30)
    carcaca: str = Field(..., min_length=1, max_length=30)
    tensao: str = Field(..., min_length=1, max_length=60)
    corrente: str = Field(..., min_length=1, max_length=60)
    ip: str = Field(..., min_length=1, max_length=20)
    classe_isol: str = Field(..., min_length=1, max_length=30)
    confianca: float = Field(..., ge=0, le=100)
