import json
from pathlib import Path
from pydantic import BaseModel

class AssetInfo(BaseModel):
    manufacturer: str
    model: str
    frame_size: str

class NominalData(BaseModel):
    power_cv: float
    power_kw: float
    voltage_v: list[int]
    current_a: dict[str, float]
    rpm: int
    frequency_hz: int
    service_factor: float

class TemperatureThresholds(BaseModel):
    warning: float
    critical: float

class VibrationThresholds(BaseModel):
    warning: float
    critical: float

class AlertsThresholds(BaseModel):
    temperature_windings_c: TemperatureThresholds
    temperature_bearings_c: TemperatureThresholds
    vibration_rms_mm_s: VibrationThresholds

class MotorTechnicalSpecs(BaseModel):
    """
    A representação Pydantic do arquivo technical_specs.json.
    Atua como fronteira Fail-Fast: se o arquivo JSON for adulterado 
    com dados que não batem com a tipagem, a aplicação quebra imediatamente.
    """
    asset_info: AssetInfo
    nominal_data: NominalData
    alerts_thresholds: AlertsThresholds

    @classmethod
    def load_from_json(cls, file_path: Path) -> "MotorTechnicalSpecs":
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo de especificação não encontrado: {file_path}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # O Pydantic valida os dados e injeta nos tipos estritos automaticamente
        return cls(**data)
