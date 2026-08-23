import asyncio
import json
import csv
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
        
        # Caminho absoluto para a base de dados em CSV
        self.csv_path = Path(r"c:\Users\Igor\Desktop\Sarak\Fiap\CP - Sprint - GS\2º Ano\Sprints\Sprint 2\Industrial-Mind-develop\History_32026-05-19T11-46-10-920 (1).csv")
        self.csv_data = []
        self.current_index = 0

    async def connect(self):
        broker_url = settings.mqtt_broker_url.replace("mqtt://", "")
        host, port = broker_url.split(":")
        try:
            self.client.connect(host, int(port))
            self.client.loop_start()
            self.is_connected = True
            print(f"[SUCCESS] CSV Injector conectado ao MQTT Broker em {broker_url}")
        except Exception as e:
            print(f"[ERROR] Falha na conexão MQTT: {e}")

    async def publish(self, topic: str, value: float):
        if self.is_connected:
            self.client.publish(topic, str(round(value, 2)))

    def load_csv(self):
        try:
            if not self.csv_path.exists():
                print(f"[ERROR] Arquivo CSV não encontrado: {self.csv_path}")
                return

            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=';')
                # Ignorar as 3 primeiras linhas (Cabeçalho da Balluff)
                next(reader, None)
                next(reader, None)
                next(reader, None)
                
                for row in reader:
                    if len(row) >= 6:
                        try:
                            # Índices baseados na estrutura do arquivo:
                            # 3: 1.1. Velocidade, 4: 1.2. Aceleração, 5: 1.3. Temperatura
                            # 6: 2.1. Velocidade, 7: 2.2. Aceleração, 8: 2.3. Temperatura
                            self.csv_data.append({
                                "velocidade_p1": float(row[3].replace(',', '.')),
                                "aceleracao_p1": float(row[4].replace(',', '.')),
                                "temperatura_p1": float(row[5].replace(',', '.')),
                                "velocidade_p2": float(row[6].replace(',', '.')),
                                "aceleracao_p2": float(row[7].replace(',', '.')),
                                "temperatura_p2": float(row[8].replace(',', '.'))
                            })
                        except (ValueError, IndexError):
                            continue
            print(f"[INFO] Carregadas {len(self.csv_data)} linhas do CSV histórico.")
        except Exception as e:
            print(f"[ERROR] Erro ao ler CSV: {e}")

    async def start_loop(self):
        root_path = Path(__file__).resolve().parent.parent.parent.parent.parent
        config_path = root_path / "backend" / "simulator_config.json"
        
        print("[CSV INJECTOR] Iniciando injetor de dados a partir do histórico...")
        await self.connect()
        self.load_csv()

        try:
            while True:
                running = False
                if config_path.exists():
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            cfg = json.load(f)
                            # Se "running" for true, o histórico CSV será ejetado no MQTT
                            running = cfg.get("running", False)
                    except: pass

                if not running or len(self.csv_data) == 0:
                    await asyncio.sleep(3) # Apenas aguarda o usuário ativar no dashboard
                    continue

                # Pega a linha atual do CSV e avança o cursor (formando o loop infinito)
                current_row = self.csv_data[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.csv_data)

                # Publicar os dados nos tópicos MQTT correspondentes aos ativos
                async with AsyncSessionLocal() as session:
                    result = await session.execute(
                        select(ActiveAssetDB).options(selectinload(ActiveAssetDB.mappings))
                    )
                    assets = result.scalars().all()

                    total_published = 0
                    for asset in assets:
                        for mapping in asset.mappings:
                            var_result = await session.execute(
                                select(DataVariableDB).where(DataVariableDB.id == mapping.variable_id)
                            )
                            variable = var_result.scalar_one_or_none()
                            
                            if variable:
                                name_lower = variable.name.lower()
                                val = 0.0
                                
                                # Associa a grandeza da base com a coluna específica
                                if "velocidade" in name_lower and "porta 1" in name_lower:
                                    val = current_row["velocidade_p1"]
                                elif "acelera" in name_lower and "porta 1" in name_lower:
                                    val = current_row["aceleracao_p1"]
                                elif "temperatura" in name_lower and "porta 1" in name_lower:
                                    val = current_row["temperatura_p1"]
                                elif "velocidade" in name_lower and "porta 2" in name_lower:
                                    val = current_row["velocidade_p2"]
                                elif "acelera" in name_lower and "porta 2" in name_lower:
                                    val = current_row["aceleracao_p2"]
                                elif "temperatura" in name_lower and "porta 2" in name_lower:
                                    val = current_row["temperatura_p2"]
                                else:
                                    continue # Ignora sensores que não dão match

                                await self.publish(mapping.mqtt_topic, val)
                                total_published += 1

                if total_published > 0:
                    print(f"[CSV INJECTOR] Linha {self.current_index}/{len(self.csv_data)} injetada com sucesso (3s).")
                
                # O intervalo de simulação é estritamente 3 segundos
                await asyncio.sleep(3)

        except asyncio.CancelledError:
            self.client.loop_stop()
            self.client.disconnect()
            print("[INFO] Injetor CSV encerrado.")
