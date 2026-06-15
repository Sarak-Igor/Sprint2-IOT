import json
from pathlib import Path
from pydantic import BaseModel

class AssetInfo(BaseModel):
    """Metadados de Identificação: Fabricante e Modelo."""
    manufacturer: str
    model: str
    frame_size: str

class NominalData(BaseModel):
    """Dados de Placa: Especificações nominais de operação do motor."""
    power_cv: float
    power_kw: float
    voltage_v: list[int]
    current_a: dict[str, float]
    rpm: int
    frequency_hz: int
    service_factor: float
    min_eff: float = 85.0
    max_eff: float = 98.0

class TemperatureThresholds(BaseModel):
    """Limites Térmicos: Define quando a temperatura se torna crítica."""
    warning: float
    critical: float

class VibrationThresholds(BaseModel):
    """Limites Vibratórios: Define os thresholds de aceleração/velocidade."""
    warning: float
    critical: float

class AlertsThresholds(BaseModel):
    """Mapa de Alertas: Consolida os limites de todos os sensores monitorados."""
    temperature_windings_c: TemperatureThresholds
    temperature_bearings_c: TemperatureThresholds
    vibration_rms_mm_s: VibrationThresholds

class MotorTechnicalSpecs(BaseModel):
    """
    O Contrato de Soberania Tecnológica Forzy.
    Esta classe garante que qualquer novo motor adicionado ao sistema siga 
    rigorosamente o padrão de dados esperado, permitindo a agnostia de hardware.
    """
    asset_info: AssetInfo
    nominal_data: NominalData
    alerts_thresholds: AlertsThresholds

    @classmethod
    def load_from_json(cls, file_path: Path) -> "MotorTechnicalSpecs":
        """
        Carregador Dinâmico: Transforma o arquivo JSON bruto em um objeto tipado 
        e validado (Fail-Fast) pelo Pydantic.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo de especificação não encontrado: {file_path}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        return cls(**data)
