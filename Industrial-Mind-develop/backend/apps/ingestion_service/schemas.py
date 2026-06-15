from pydantic import BaseModel

class RawTelemetryPayload(BaseModel):
    """Contrato Fail-Fast de entrada de dados dos sensores"""
    device_id: str
    temp_windings: float
    temp_bearings: float
    vibration_rms: float
    current: float
    voltage: float
    rpm: int
