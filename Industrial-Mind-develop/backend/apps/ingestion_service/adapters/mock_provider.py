import asyncio
import random
from pathlib import Path
import paho.mqtt.client as mqtt
from .base_provider import BaseProvider
from .chaos_generator import ChaosGenerator
from ...digital_twin_core.motor_spec import MotorTechnicalSpecs
from backend.shared_infra.config import settings, get_active_profile_path
from backend.shared_infra.database_client import AsyncSessionLocal
from backend.apps.digital_twin_core.models import TelemetryHistory
from ..schemas import RawTelemetryPayload

class MqttMockProvider(BaseProvider):
    def __init__(self):
        # Lendo abstração puramente, sem hardcode!
        profile_path = get_active_profile_path() / "technical_specs.json"
        self.specs = MotorTechnicalSpecs.load_from_json(profile_path)
        self.chaos = ChaosGenerator(self.specs.alerts_thresholds)
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.topic = f"Forzy/telemetry/{self.specs.asset_info.model.replace(' ', '_')}"

    async def connect(self):
        broker_url = settings.mqtt_broker_url.replace("mqtt://", "")
        host, port = broker_url.split(":")
        try:
            self.client.connect(host, int(port))
            self.client.loop_start()
            print(f"[SUCCESS] Conectado ao MQTT Broker em {broker_url}")
        except Exception as e:
            print(f"[ERROR] Erro ao conectar no MQTT: {e}. Verifique se o Docker está rodando.")

    async def publish(self, payload: str):
        self.client.publish(self.topic, payload)

    def generate_reading(self) -> RawTelemetryPayload:
        nom_rpm = self.specs.nominal_data.rpm
        nom_volt = self.specs.nominal_data.voltage_v[0] # Usa 220V base
        nom_curr = self.specs.nominal_data.current_a[str(nom_volt)]

        # Valores base normais (motor rodando suave)
        base_temp_w = 70.0
        base_temp_b = 60.0
        base_vib = 1.0

        # Aplica o Fail-Fast do Pydantic já na geração
        return RawTelemetryPayload(
            device_id=self.specs.asset_info.model,
            temp_windings=self.chaos.apply_chaos(base_temp_w, "temp_windings"),
            temp_bearings=self.chaos.apply_chaos(base_temp_b, "temp_bearings"),
            vibration_rms=self.chaos.apply_chaos(base_vib, "vibration"),
            current=self.chaos.apply_chaos(nom_curr, "current"),
            voltage=round(nom_volt + random.uniform(-5, 5), 1),
            rpm=int(nom_rpm + random.uniform(-10, 10))
        )

    async def start_loop(self):
        import os
        import json
        
        # Caminho absoluto: mock_provider.py -> adapters -> ingestion_service -> apps -> backend -> Forzy (Raiz)
        # Precisamos subir 5 níveis para chegar na raiz do projeto
        root_path = Path(__file__).resolve().parent.parent.parent.parent.parent
        config_path = root_path / "backend" / "simulator_config.json"
        
        print(f"[SIMULATOR] AGORA monitorando config em: {config_path}")
        
        await self.connect()
        try:
            while True:
                # Lógica de controle dinâmico (Play/Pause e Intervalo)
                running = True
                interval = 5
                
                if config_path.exists():
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            cfg = json.load(f)
                            running = cfg.get("running", True)
                            interval = cfg.get("interval", 5)
                    except Exception as e:
                        print(f"[SIMULATOR] Erro ao ler config: {e}")

                if not running:
                    await asyncio.sleep(1)
                    continue

                reading = self.generate_reading()
                payload_json = reading.model_dump_json()
                print(f"[MQTT] [TOPIC: {self.topic}] | Publicando: {payload_json}")
                await self.publish(payload_json)
                
                # Persistência AUTOMÁTICA direta no banco
                await self.persist_to_db(reading)
                
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            self.client.loop_stop()
            self.client.disconnect()
            print("[INFO] Desconectado do MQTT")

    async def persist_to_db(self, reading: RawTelemetryPayload):
        async with AsyncSessionLocal() as session:
            try:
                telemetry = TelemetryHistory(
                    asset_tag="WEG_W22_01",
                    temp_windings=reading.temp_windings,
                    temp_bearings=reading.temp_bearings,
                    vibration_rms=reading.vibration_rms,
                    current_a=reading.current,
                    voltage_v=reading.voltage,
                    rpm=reading.rpm
                )
                session.add(telemetry)
                await session.commit()
                print(f"[AUTO-PERSIST] [SUCCESS] Dados gravados no Neon")
            except Exception as e:
                print(f"[AUTO-PERSIST] [ERROR] Falha ao gravar: {e}")
                await session.rollback()
