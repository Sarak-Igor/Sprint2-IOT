from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend.shared_infra.database_client import Base

class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = {"schema": "forzy"}

    id = Column(Integer, primary_key=True, index=True)
    tag = Column(String(50), unique=True, nullable=False)
    model = Column(String(100))
    power_kw = Column(Float)
    voltage_v = Column(Float)
    rpm_nominal = Column(Integer)
    temp_max_c = Column(Float, default=155.0)
    vib_max_mm_s = Column(Float, default=4.5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TelemetryHistory(Base):
    __tablename__ = "telemetry_history"
    __table_args__ = {"schema": "forzy"}

    id = Column(Integer, primary_key=True, index=True)
    asset_tag = Column(String(50), ForeignKey("forzy.assets.tag"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    temp_windings = Column(Float)
    temp_bearings = Column(Float)
    vibration_rms = Column(Float)
    current_a = Column(Float)
    voltage_v = Column(Float)
    rpm = Column(Integer)
