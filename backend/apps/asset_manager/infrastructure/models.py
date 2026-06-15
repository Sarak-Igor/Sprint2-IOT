from sqlalchemy import Column, String, Float, JSON, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.shared_infra.database_client.postgresql import Base
import uuid

class MotorModelDB(Base):
    """Cadastro Técnico: Armazena os dados de placa e limites padrão de cada modelo de motor."""
    __tablename__ = "motor_models"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    power_hp = Column(Float)
    spec_reference = Column(String)
    default_thresholds = Column(JSON, default={})

class DataVariableDB(Base):
    """Dicionário de Variáveis: Define o que pode ser medido (Temperatura, RPM, etc) e suas unidades."""
    __tablename__ = "data_variables"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    unit = Column(String, nullable=False)
    description = Column(String)

class SensorHardwareDB(Base):
    """Catálogo de Sensores: Especificações do hardware físico utilizado para coleta."""
    __tablename__ = "sensor_hardware"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String, nullable=False)
    manufacturer = Column(String)
    protocol = Column(String)
    accuracy = Column(Float)

class ActiveAssetDB(Base):
    """Gêmeo Digital: A instância virtual ativa de um motor em operação na planta."""
    __tablename__ = "active_assets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    location = Column(String)
    motor_model_id = Column(UUID(as_uuid=True), ForeignKey("motor_models.id"))
    status = Column(String, default="operational")
    applied_thresholds = Column(JSON, default={}) # Configuração customizada de limites para este ativo
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos com deleção em cascata para integridade referencial
    mappings = relationship("TelemetryMappingDB", back_populates="asset", cascade="all, delete-orphan", passive_deletes=True)
    anomalies = relationship("OperationalAnomalyDB", cascade="all, delete-orphan", passive_deletes=True)
    readings = relationship("TelemetryReadingDB", cascade="all, delete-orphan", passive_deletes=True)

class TelemetryMappingDB(Base):
    """Contrato de Conectividade: Vincula um Ativo + Variável a um tópico MQTT específico."""
    __tablename__ = "telemetry_mappings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("active_assets.id"), index=True)
    variable_id = Column(UUID(as_uuid=True), ForeignKey("data_variables.id"))
    sensor_id = Column(UUID(as_uuid=True), ForeignKey("sensor_hardware.id"))
    mqtt_topic = Column(String, nullable=False)

    asset = relationship("ActiveAssetDB", back_populates="mappings")

class OperationalAnomalyDB(Base):
    """Log de Incidentes: Registro histórico de violações de thresholds (Warning/Critical)."""
    __tablename__ = "operational_anomalies"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("active_assets.id"))
    variable_id = Column(UUID(as_uuid=True), ForeignKey("data_variables.id"))
    value = Column(Float)
    severity = Column(String) 
    threshold_value = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_resolved = Column(Boolean, default=False)

class TelemetryReadingDB(Base):
    """Histórico de Telemetria (Big Data): Base para análise temporal e treinamento de IA."""
    __tablename__ = "telemetry_readings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("active_assets.id"), index=True)
    variable_id = Column(UUID(as_uuid=True), ForeignKey("data_variables.id"), index=True)
    value = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
