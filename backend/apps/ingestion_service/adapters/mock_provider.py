import asyncio
import random
import json
from pathlib import Path
import paho.mqtt.client as mqtt
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .base_provider import BaseProvider
from backend.shared_infra.config import settings
from backend.shared_infra.database_client.postgresql import AsyncSessionLocal
from backend.apps.asset_manager.infrastructure.models import ActiveAssetDB, TelemetryMappingDB, DataVariableDB

class MqttMockProvider(BaseProvider):
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.is_connected = False

    async def connect(self):
        broker_url = settings.mqtt_broker_url.replace("mqtt://", "")
        host, port = broker_url.split(":")
        try:
            self.client.connect(host, int(port))
            self.client.loop_start()
            self.is_connected = True
            print(f"[SUCCESS] Simulador conectado ao MQTT Broker em {broker_url}")
        except Exception as e:
            print(f"[ERROR] Falha na conexão MQTT: {e}")

    async def publish(self, topic: str, value: float):
        if self.is_connected:
            self.client.publish(topic, str(round(value, 2)))

    def _generate_value(self, variable_name: str, thresholds: dict, var_id: str):
        # 1. Recuperação de Limites: Busca os thresholds específicos do ativo para guiar a simulação
        var_id_str = str(var_id)
        spec = thresholds.get(var_id_str, {})
        nominal = spec.get("nominal")
        warning = spec.get("warning")
        critical = spec.get("critical")

        # Fallbacks: Valores padrão baseados no tipo de variável caso não haja spec definida
        if nominal is None:
            defaults = {"temp": 65.0, "vib": 1.2, "curr": 42.0, "rpm": 1750.0, "volt": 220.0}
            name_lower = variable_name.lower()
            for key, val in defaults.items():
                if key in name_lower:
                    nominal = val
                    break
            if nominal is None: nominal = 50.0

        # Lógica de Direção: Define se o valor crítico é por excesso (ex: Calor) ou falta (ex: RPM)
        is_lower = (critical is not None and nominal is not None and critical < nominal)
        
        # MOTOR DE PROBABILIDADE (Sorteio de Estado):
        # 70% chance de Normalidade, 20% Aviso, 10% Crítico (Anomalia)
        chance = random.random()
        
        if chance < 0.70:
            # ESTADO NORMAL (70%) - Flutua próximo ao valor nominal (ideal)
            target = nominal
            spread = 0.05 # 5% de variação
        elif chance < 0.90:
            # ESTADO AVISO (20%) - Simula início de desgaste ou sobrecarga
            target = warning if warning is not None else (nominal * 1.15 if not is_lower else nominal * 0.85)
            spread = 0.03
        else:
            # ESTADO CRÍTICO (10%) - Simula falha iminente ou quebra
            if is_lower:
                target = critical * 0.9 if critical is not None else nominal * 0.5
            else:
                target = critical * 1.1 if critical is not None else nominal * 1.5
            spread = 0.05

        # Ruído Dinâmico: Adiciona variação estocástica para evitar valores "perfeitos" e artificiais
        noise = target * random.uniform(-spread, spread)
        return target + noise

    async def start_loop(self):
        root_path = Path(__file__).resolve().parent.parent.parent.parent.parent
        config_path = root_path / "backend" / "simulator_config.json"
        
        print("[SIMULATOR] Iniciando motor de simulação multi-ativo...")
        await self.connect()

        try:
            while True:
                # Controle de Simulação: Permite pausar/ajustar intervalo via arquivo externo (dashboard)
                running = True
                interval = 5
                if config_path.exists():
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            cfg = json.load(f)
                            running = cfg.get("running", True)
                            interval = cfg.get("interval", 5)
                    except: pass

                if not running:
                    await asyncio.sleep(1)
                    continue

                # Ciclo de Publicação: Itera sobre todos os ativos cadastrados no sistema
                async with AsyncSessionLocal() as session:
                    # Carrega dinamicamente os ativos e seus tópicos MQTT configurados
                    result = await session.execute(
                        select(ActiveAssetDB).options(selectinload(ActiveAssetDB.mappings))
                    )
                    assets = result.scalars().all()

                    total_published = 0
                    for asset in assets:
                        thresholds = asset.applied_thresholds or {}
                        
                        for mapping in asset.mappings:
                            # Identifica a variável e gera o valor correspondente (simulando o sensor físico)
                            var_result = await session.execute(
                                select(DataVariableDB).where(DataVariableDB.id == mapping.variable_id)
                            )
                            variable = var_result.scalar_one_or_none()
                            
                            if variable:
                                val = self._generate_value(variable.name, thresholds, mapping.variable_id)
                                # Dispara para o Broker MQTT (o que o ESP32 faria na prática)
                                await self.publish(mapping.mqtt_topic, val)
                                total_published += 1

                if total_published > 0:
                    print(f"[SIMULATOR] Ciclo concluído: {total_published} leituras publicadas para {len(assets)} ativos.")
                
                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            self.client.loop_stop()
            self.client.disconnect()
            print("[INFO] Simulador encerrado.")

