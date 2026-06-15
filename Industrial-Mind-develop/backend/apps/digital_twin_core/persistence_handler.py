import asyncio
import json
import paho.mqtt.client as mqtt
from backend.shared_infra.config import settings
from backend.shared_infra.database_client import AsyncSessionLocal
from backend.apps.digital_twin_core.models import TelemetryHistory
from sqlalchemy.future import select

class MqttPersistenceHandler:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.topic = "Forzy/telemetry/#" # Escuta tudo do Forzy/telemetry
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.loop = None # Será definido no start

    def on_connect(self, client, userdata, flags, rc, properties):
        print(f"[PERSISTENCE] Conectado ao Broker MQTT. Escutando {self.topic}")
        client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            print(f"[PERSISTENCE] Mensagem recebida no tópico {msg.topic}")
            
            # Agenda a execução na thread do loop principal
            if self.loop:
                asyncio.run_coroutine_threadsafe(self.save_to_db(payload), self.loop)
        except Exception as e:
            print(f"[PERSISTENCE] [ERROR] Falha ao processar mensagem: {e}")

    async def save_to_db(self, data):
        print(f"[DEBUG] Tentando persistir dados: {data}")
        async with AsyncSessionLocal() as session:
            try:
                # Criar registro de telemetria
                telemetry = TelemetryHistory(
                    asset_tag="WEG_W22_01", # Para Sprint 1 usamos o motor fixo
                    temp_windings=data.get("temp_windings"),
                    temp_bearings=data.get("temp_bearings"),
                    vibration_rms=data.get("vibration_rms"),
                    current_a=data.get("current"),
                    voltage_v=data.get("voltage"),
                    rpm=data.get("rpm")
                )
                session.add(telemetry)
                await session.commit()
                print(f"[DATABASE] [SUCCESS] Dados persistidos no Neon para WEG_W22_01")
            except Exception as e:
                print(f"[DATABASE] [ERROR] Falha ao persistir no Neon: {e}")
                await session.rollback()

    async def start(self):
        self.loop = asyncio.get_running_loop() # CORREÇÃO: Define o loop para threads do MQTT
        broker_url = settings.mqtt_broker_url.replace("mqtt://", "")
        host, port = broker_url.split(":")
        self.client.connect(host, int(port))
        self.client.loop_start()
        
        print(f"[PERSISTENCE] Worker iniciado e pronto para persistir.")
        
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            self.client.loop_stop()
            self.client.disconnect()
            print("[PERSISTENCE] Encerrado.")

if __name__ == "__main__":
    handler = MqttPersistenceHandler()
    asyncio.run(handler.start())
