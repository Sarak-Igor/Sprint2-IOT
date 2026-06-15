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
    default_thresholds: Dict[str, Any] = {} # Ex: {"temp": {"max": 90}}

class ActiveAsset(BaseModel):
    """Um motor real operando em campo"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    location: str
    motor_model_id: UUID
    status: str = "operational" # operational, maintenance, alert
    applied_thresholds: Dict[str, Any] = {}

class TelemetryMapping(BaseModel):
    """O 'vínculo' entre o Ativo, o Dado e o Sensor que o coleta"""
    id: UUID = Field(default_factory=uuid4)
    asset_id: UUID
    variable_id: UUID
    sensor_id: UUID
    mqtt_topic: str # Onde este sensor publica este dado específico
