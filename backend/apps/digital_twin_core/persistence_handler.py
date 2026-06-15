import asyncio
import json
import paho.mqtt.client as mqtt
from backend.shared_infra.config import settings
from backend.shared_infra.database_client.postgresql import AsyncSessionLocal
from backend.apps.asset_manager.infrastructure.models import TelemetryMappingDB, ActiveAssetDB, OperationalAnomalyDB, TelemetryReadingDB
from sqlalchemy.future import select

class TopicResolver:
    """Resolve tópicos MQTT para (asset_id, variable_id) com cache."""
    def __init__(self):
        self._cache = {}

    async def resolve(self, topic: str):
        if topic in self._cache:
            return self._cache[topic]
        
        async with AsyncSessionLocal() as session:
            # Busca o mapeamento no banco
            stmt = select(TelemetryMappingDB).where(TelemetryMappingDB.mqtt_topic == topic)
            result = await session.execute(stmt)
            mapping = result.scalars().first()
            
            if mapping:
                self._cache[topic] = (mapping.asset_id, mapping.variable_id)
                return self._cache[topic]
        return None

class MqttPersistenceHandler:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.topic = "Forzy/telemetry/#"
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.loop = None
        self.resolver = TopicResolver()

    def on_connect(self, client, userdata, flags, rc, properties):
        print(f"[PERSISTENCE] Conectado ao Broker MQTT. Escutando {self.topic}")
        client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        try:
            payload_str = msg.payload.decode()
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                # Se não for JSON, tenta tratar como valor único (float)
                try:
                    payload = {"value": float(payload_str)}
                except:
                    return

            if self.loop:
                asyncio.run_coroutine_threadsafe(self.process_message(msg.topic, payload), self.loop)
        except Exception as e:
            print(f"[PERSISTENCE] [ERROR] Falha ao processar mensagem: {e}")

    async def process_message(self, topic, data):
        # 1. Identificação do Ativo e Variável: Resolve o tópico MQTT usando o mapeamento do banco
        resolution = await self.resolver.resolve(topic)
        
        if resolution:
            asset_id, variable_id = resolution
            # Normalização: Obtém o valor numérico independente do formato do payload (JSON ou Float puro)
            value = data.get("value") if isinstance(data, dict) else data
            
            if value is not None:
                await self.save_telemetry(asset_id, variable_id, float(value))



    async def save_telemetry(self, asset_id, variable_id, value):
        async with AsyncSessionLocal() as session:
            try:
                # 1. Armazenamento de Histórico: Salva a leitura na tabela de telemetria (Requisito da Sprint)
                reading = TelemetryReadingDB(
                    asset_id=asset_id,
                    variable_id=variable_id,
                    value=value
                )
                session.add(reading)
                
                # 2. Detecção de Anomalias: Compara a leitura com os thresholds específicos de cada motor
                result = await session.execute(
                    select(ActiveAssetDB).where(ActiveAssetDB.id == asset_id)
                )
                asset = result.scalar_one_or_none()
                
                if asset and asset.applied_thresholds:
                    threshold_spec = asset.applied_thresholds.get(str(variable_id), {})
                    critical = threshold_spec.get("critical")
                    warning = threshold_spec.get("warning")
                    nominal = threshold_spec.get("nominal")
                    
                    severity = None
                    
                    # Inteligência de Limite: Identifica se é um limite superior (ex: Temp) ou inferior (ex: RPM)
                    is_lower_limit = (critical is not None and nominal is not None and critical < nominal)
                    
                    if is_lower_limit:
                        if critical is not None and value <= critical:
                            severity = "critical"
                        elif warning is not None and value <= warning:
                            severity = "warning"
                    else:
                        if critical is not None and value >= critical:
                            severity = "critical"
                        elif warning is not None and value >= warning:
                            severity = "warning"
                    
                    if severity:
                        # 3. Registro de Incidente: Caso o valor saia da faixa nominal, registra o log de anomalia
                        anomaly = OperationalAnomalyDB(
                            asset_id=asset_id,
                            variable_id=variable_id,
                            value=value,
                            severity=severity,
                            threshold_value=critical if severity == "critical" else warning
                        )
                        session.add(anomaly)
                        
                        # Atualizar status visual do ativo para refletir a saúde no Dashboard
                        if severity == "critical":
                            asset.status = "alert"
                        elif severity == "warning" and asset.status == "operational":
                            asset.status = "warning"
                
                await session.commit()
            except Exception as e:
                print(f"[DATABASE] [ERROR] Save Fail: {e}")
                await session.rollback()

    async def start(self):
        self.loop = asyncio.get_running_loop()
        broker_url = settings.mqtt_broker_url.replace("mqtt://", "")
        host, port = broker_url.split(":")
        self.client.connect(host, int(port))
        self.client.loop_start()
        
        print(f"[PERSISTENCE] Worker Multi-Ativo iniciado.")
        
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
