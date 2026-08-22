from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4


class DataVariable(BaseModel):
    """Representa uma grandeza física (Temperatura, Vibração, etc)"""

    id: UUID = Field(default_factory=uuid4)
    name: str
    unit: str
    description: Optional[str] = None


class SensorHardware(BaseModel):
    """Representa um modelo de sensor físico"""

    id: UUID = Field(default_factory=uuid4)
    model_name: str
    manufacturer: str
    protocol: str  # MQTT, OPC-UA, Modbus
    accuracy: Optional[float] = None


class MotorModel(BaseModel):
    """Representa um modelo de catálogo de motor (ex: WEG W22)"""

    id: UUID = Field(default_factory=uuid4)
    brand: str
    model: str
    power_hp: float
    spec_reference: str  # Link para PDF ou ID no R2
    default_thresholds: Dict[str, Any] = {}  # Ex: {"temp": {"max": 90}}


class ActiveAsset(BaseModel):
    """Um motor real operando em campo"""

    id: UUID = Field(default_factory=uuid4)
    name: str
    location: str
    motor_model_id: UUID
    status: str = "operational"  # operational, maintenance, alert
    applied_thresholds: Dict[str, Any] = {}


class TelemetryMapping(BaseModel):
    """O 'vínculo' entre o Ativo, o Dado e o Sensor que o coleta"""

    id: UUID = Field(default_factory=uuid4)
    asset_id: UUID
    variable_id: UUID
    sensor_id: UUID
    mqtt_topic: str  # Onde este sensor publica este dado específico


class MotorEnrichmentRequest(BaseModel):
    """Entrada do usuário para o cadastro de um novo ativo assistido por IA (POST /api/assets)"""

    name: str = Field(..., min_length=1, max_length=120)
    location: str = Field(..., min_length=1, max_length=120)
    description: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Marca/modelo ou descrição livre do motor (ex.: 'WEG W22 100cv trifásico IP55')",
    )


class MotorSpecEnrichment(BaseModel):
    """Saída estruturada exigida do LLM — nunca persistida sem passar por esta validação"""

    brand: str = Field(..., min_length=1, max_length=80)
    model: str = Field(..., min_length=1, max_length=80)
    power_hp: float = Field(..., gt=0, le=100000)
    rpm_nominal: float = Field(..., gt=0, le=20000)
    ip_rating: str = Field(..., min_length=2, max_length=10)
    threshold_suggestions: Dict[str, Dict[str, float]] = Field(default_factory=dict)
