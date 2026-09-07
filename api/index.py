import os
import sys
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import aiohttp

# Adiciona o diretório raiz ao path para que possamos importar de 'backend'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.apps.asset_manager.web.router import router as asset_router
import logging

try:
    from backend.apps.asset_manager.vision.router import router as vision_router
except ImportError as e:
    logging.warning(f"Vision router omitted: {e}")
    vision_router = None

try:
    from backend.apps.ai_knowledge.router import router as knowledge_router
except ImportError as e:
    logging.warning(f"Knowledge router omitted: {e}")
    knowledge_router = None

try:
    from backend.apps.ai_knowledge.agent.router import router as agent_router
except ImportError as e:
    logging.warning(f"Agent router omitted: {e}")
    agent_router = None
from backend.shared_infra.database_client import AsyncSessionLocal
from backend.apps.asset_manager.infrastructure.models import (
    TelemetryMappingDB,
    ActiveAssetDB,
    MotorModelDB,
    DataVariableDB,
    SensorHardwareDB,
    TelemetryReadingDB,
)
from backend.apps.asset_manager.domain.entities import (
    MotorModel,
    DataVariable,
    SensorHardware,
)
from backend.shared_infra.config import settings
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List

app = FastAPI()
app.include_router(asset_router, prefix="/api")
if vision_router:
    app.include_router(vision_router, prefix="/api")
if knowledge_router:
    app.include_router(knowledge_router, prefix="/api")
if agent_router:
    app.include_router(agent_router, prefix="/api")


@app.middleware("http")
async def log_requests(request, call_next):
    # Logs desativados em produção para performance
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import json


@app.get("/api/health")
async def health():
    return {"status": "online", "system": "Forzy Digital Twin"}


@app.get("/api/assets")
async def get_assets():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ActiveAssetDB))
            assets = result.scalars().all()

            formatted = []
            for asset in assets:
                formatted.append(
                    {
                        "id": str(asset.id),
                        "tag": asset.name,
                        "name": asset.name,
                        "location": asset.location,
                        "status": "Ativo"
                        if asset.status == "operational"
                        else "Alerta",
                        "health": "98%",
                    }
                )
            return formatted
    except Exception as e:
        print(f"ERRO GET /api/assets: {e}")
        return []


from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "backend" / "simulator_config.json"


def get_sys_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"running": True, "interval": 5}


@app.get("/api/config")
async def get_config():
    return get_sys_config()


@app.post("/api/config")
async def update_config(config: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f)

        # Publica no MQTT para notificar o ESP32 real ou Wokwi
        if "interval" in config:
            # Converte segundos do front para ms no ESP32
            payload = json.dumps({"measurement_interval_ms": config["interval"] * 1000})
            mqtt_client.publish("Forzy/config/device", payload)

    except Exception as e:
        # No Vercel o sistema de arquivos é read-only, então ignoramos o erro de escrita
        # O estado 'running' será gerenciado pelo próprio frontend
        print(f"Aviso: Não foi possível salvar no arquivo (ambiente serverless): {e}")
    return config


# @app.post("/api/telemetry")
# async def ingest_telemetry(data: dict):
#     """
#     ROTA DESATIVADA: Esta é uma rota legada para compatibilidade.
#     Na arquitetura nova, a ingestão é feita via MQTT para maior performance e escalabilidade.
#     """
#     return JSONResponse(
#         status_code=410,
#         content={"status": "gone", "message": "Esta rota foi desativada em favor da ingestão via MQTT."}
#     )


@app.get("/api/telemetry")
async def get_telemetry(limit: int = 50):
    try:
        async with AsyncSessionLocal() as session:
            # Busca as leituras mais recentes com join para pegar nomes amigáveis
            stmt = (
                select(
                    TelemetryReadingDB.id,
                    TelemetryReadingDB.value,
                    TelemetryReadingDB.timestamp,
                    ActiveAssetDB.name.label("asset_name"),
                    DataVariableDB.name.label("variable_name"),
                    DataVariableDB.unit,
                )
                .join(ActiveAssetDB, TelemetryReadingDB.asset_id == ActiveAssetDB.id)
                .join(
                    DataVariableDB, TelemetryReadingDB.variable_id == DataVariableDB.id
                )
                .order_by(TelemetryReadingDB.timestamp.desc())
                .limit(limit)
            )

            result = await session.execute(stmt)
            rows = result.all()

            # Formata para o frontend
            history = []
            for row in rows:
                # Busca o ativo para pegar os thresholds (poderia ser otimizado com cache ou join, mas para o histórico está ok)
                result_asset = await session.execute(
                    select(ActiveAssetDB).where(ActiveAssetDB.name == row.asset_name)
                )
                asset = result_asset.scalars().first()

                status = "Normal"
                thresholds = {}
                if asset and asset.applied_thresholds:
                    # Tenta encontrar a variável específica nos mapeamentos para buscar o ID correto da variável
                    # No histórico, row.variable é o NOME, mas o threshold é indexado pelo UUID (string)
                    # Vamos buscar o ID da variável pelo nome
                    var_res = await session.execute(
                        select(DataVariableDB).where(
                            DataVariableDB.name == row.variable_name
                        )
                    )
                    var_obj = var_res.scalars().first()

                    if var_obj:
                        thresholds = asset.applied_thresholds.get(str(var_obj.id), {})
                        val = row.value
                        crit = thresholds.get("critical")
                        warn = thresholds.get("warning")

                        if crit is not None and val >= crit:
                            status = "Perigo"
                        elif warn is not None and val >= warn:
                            status = "Aviso"

                history.append(
                    {
                        "id": str(row.id),
                        "timestamp": row.timestamp.isoformat(),
                        "device_id": row.asset_name,
                        "variable": row.variable_name,
                        "value": row.value,
                        "unit": row.unit,
                        "status": status,
                        "thresholds": thresholds,
                    }
                )
            return history
    except Exception as e:
        print(f"ERRO GET /api/telemetry: {e}")
        return JSONResponse(
            status_code=500, content={"status": "error", "message": str(e)}
        )


@app.get("/api/telemetry/stats")
async def get_telemetry_stats():
    try:
        async with AsyncSessionLocal() as session:
            # Busca o último registro de telemetria
            result = await session.execute(
                select(TelemetryReadingDB)
                .order_by(TelemetryReadingDB.timestamp.desc())
                .limit(1)
            )
            latest = result.scalars().first()

            if latest:
                return {
                    "temp": f"{latest.value:.1f} °C",
                    "vibration": "0.00 mm/s",
                    "power": "0.00 kW",
                    "rpm": "0 RPM",
                    "current": "0.00 A",
                    "status": "Nominal",
                }

            return {
                "temp": "0.0 °C",
                "vibration": "0.00 mm/s",
                "power": "0.00 kW",
                "rpm": "0 RPM",
                "current": "0.00 A",
                "status": "Offline",
            }
    except Exception as e:
        print(f"ERRO GET /api/telemetry/stats: {e}")
        return {"temp": "N/A", "vibration": "N/A", "power": "N/A", "status": "Error"}


@app.post("/api/alerts/telegram")
async def trigger_telegram_alert(payload: dict):
    token = settings.telegram_bot_token
    chat_id = settings.telegram_chat_id

    if not token or not chat_id:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Telegram Token ou Chat ID não configurados",
            },
        )

    asset_name = payload.get("asset_name", "Desconhecido")
    variable = payload.get("variable", "N/A")
    value = payload.get("value", 0)
    status = payload.get("status", "PERIGO")
    limit = payload.get("limit", "N/A")
    unit = payload.get("unit", "")

    icon = "⚠️" if status.upper() == "ATENÇÃO" else "🚨"
    status_text = (
        "ATENÇÃO DETECTADA" if status.upper() == "ATENÇÃO" else "PERIGO DETECTADO"
    )

    message = (
        f"{icon} *ALERTA DO GÊMEO DIGITAL* {icon}\n\n"
        f"Ativo: `{asset_name}`\n"
        f"Variável: `{variable}`\n"
        f"Valor Atual: `{value} {unit}`\n"
        f"Limite de Alarme: `{limit} {unit}`\n"
        f"Status: *{status_text}*"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    tg_payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=tg_payload) as response:
                if response.status != 200:
                    return JSONResponse(
                        status_code=500,
                        content={
                            "status": "error",
                            "message": "Falha na API do Telegram",
                        },
                    )
                return {
                    "status": "success",
                    "message": "Alerta disparado pelo Gêmeo Digital",
                }
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"status": "error", "message": str(e)}
        )


import json
import paho.mqtt.client as mqtt


# Gerenciador de conexões WebSocket para Broadcast
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                continue


manager = ConnectionManager()
main_loop = None

# Configuração do Cliente MQTT para a API
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)


def on_mqtt_connect(client, userdata, flags, rc, properties):
    print("[DEBUG] API: Conectado ao Broker MQTT para Tempo Real")
    client.subscribe("Forzy/telemetry/#")


# Cache para resolução de tópicos na API
topic_cache = {}


async def resolve_topic_api(topic: str):
    if topic in topic_cache:
        return topic_cache[topic]

    async with AsyncSessionLocal() as session:
        stmt = select(TelemetryMappingDB).where(TelemetryMappingDB.mqtt_topic == topic)
        result = await session.execute(stmt)
        mapping = result.scalars().first()
        if mapping:
            topic_cache[topic] = (mapping.asset_id, mapping.variable_id)
            return topic_cache[topic]
    return None


def on_mqtt_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode()
        try:
            payload = json.loads(payload_str)
        except:
            try:
                payload = {"value": float(payload_str)}
            except:
                return

        # Busca resolução assíncrona
        if main_loop and main_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                process_and_broadcast(msg.topic, payload), main_loop
            )

    except Exception as e:
        print(f"[ERROR] API MQTT Callback: {e}")


async def process_and_broadcast(topic, payload):
    # 1. Resolução Genérica
    resolution = await resolve_topic_api(topic)

    # Prepara o pacote de broadcast agnóstico
    broadcast_data = {"topic": topic, "payload": payload, "is_generic": False}

    if resolution:
        asset_id, variable_id = resolution
        value = payload.get("value") if isinstance(payload, dict) else payload
        broadcast_data.update(
            {
                "asset_id": str(asset_id),
                "variable_id": str(variable_id),
                "value": value,
                "is_generic": True,
            }
        )
    else:
        print(f"[WARNING] Topic resolution failed for: {topic}")

    # 2. Envio via WebSocket (Sistema 100% Asset-Agnostic)
    await manager.broadcast(broadcast_data)


mqtt_client.on_connect = on_mqtt_connect
mqtt_client.on_message = on_mqtt_message


@app.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop()
    broker_url = settings.mqtt_broker_url.replace("mqtt://", "")
    host, port = broker_url.split(":")
    mqtt_client.connect(host, int(port))
    mqtt_client.loop_start()


@app.websocket("/api/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await manager.connect(websocket)
    print(
        f"[DEBUG] WS: Novo cliente conectado. Total: {len(manager.active_connections)}"
    )
    try:
        while True:
            # Mantém a conexão viva
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(
            f"[DEBUG] WS: Cliente desconectado. Total: {len(manager.active_connections)}"
        )
    except Exception as e:
        print(f"[ERROR] WS Error: {e}")
        manager.disconnect(websocket)


@app.get("/api/assets/stats")
async def get_assets_stats():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(func.count(ActiveAssetDB.id)))
            count = result.scalar()
            return {"total": f"{count}", "alerts": "0", "health_score": "98.5%"}
    except Exception as e:
        print(f"ERRO GET /api/assets/stats: {e}")
        return {"total": "0", "alerts": "0", "health_score": "100%"}


@app.get("/api/assets/variables", response_model=List[DataVariable])
async def list_variables():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(DataVariableDB))
            return result.scalars().all()
    except Exception as e:
        print(f"ERRO GET /api/assets/variables: {e}")
        return []


@app.get("/api/assets/sensors", response_model=List[SensorHardware])
async def list_sensors():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(SensorHardwareDB))
            return result.scalars().all()
    except Exception as e:
        print(f"ERRO GET /api/assets/sensors: {e}")
        return []


@app.get("/api/assets/models", response_model=List[MotorModel])
async def list_models():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(MotorModelDB))
            return result.scalars().all()
    except Exception as e:
        print(f"ERRO GET /api/assets/models: {e}")
        return []


# Para o Vercel, o objeto 'app' deve estar disponível no nível do módulo
