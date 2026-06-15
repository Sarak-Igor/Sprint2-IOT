import os
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Adiciona o diretório raiz ao path para que possamos importar de 'backend'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.shared_infra.database_client import AsyncSessionLocal
from backend.apps.digital_twin_core.models import TelemetryHistory
from sqlalchemy.future import select

app = FastAPI()

@app.middleware("http")
async def log_requests(request, call_next):
    print(f"[DEBUG] API Request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"[DEBUG] API Response: {response.status_code}")
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

import json

@app.get("/api/health")
async def health():
    return {"status": "online", "system": "Forzy Digital Twin"}

@app.get("/api/assets")
async def get_assets():
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "device_profiles")
    assets = []
    
    if os.path.exists(assets_dir):
        # Percorre as subpastas ou arquivos JSON
        for root, dirs, files in os.walk(assets_dir):
            for file in files:
                if file.endswith(".json"):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Normaliza para a UI
                            assets.append({
                                "tag": data.get("tag", "Unknown"),
                                "type": data.get("type", "Industrial Asset"),
                                "model": data.get("model", "N/A"),
                                "status": "Ativo",
                                "health": "98%"
                            })
                    except:
                        continue
    
    return assets

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "backend" / "simulator_config.json"

def get_sys_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"running": True, "interval": 5}

@app.get("/api/config")
async def get_config():
    return get_sys_config()

@app.post("/api/config")
async def update_config(config: dict):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f)
    except Exception as e:
        # No Vercel o sistema de arquivos é read-only, então ignoramos o erro de escrita
        # O estado 'running' será gerenciado pelo próprio frontend
        print(f"Aviso: Não foi possível salvar no arquivo (ambiente serverless): {e}")
    return config

@app.post("/api/telemetry")
async def ingest_telemetry(data: dict):
    try:
        async with AsyncSessionLocal() as session:
            telemetry = TelemetryHistory(
                asset_tag=data.get("asset_tag", "WEG_W22_01"),
                temp_windings=data.get("temp_windings"),
                temp_bearings=data.get("temp_bearings"),
                vibration_rms=data.get("vibration_rms"),
                current_a=data.get("current_a"),
                voltage_v=data.get("voltage_v"),
                rpm=data.get("rpm")
            )
            session.add(telemetry)
            await session.commit()
            return {"status": "success", "data": data}
    except Exception as e:
        print(f"ERRO POST /api/telemetry: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/api/telemetry")
async def get_telemetry(limit: int = 20):
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(TelemetryHistory).order_by(TelemetryHistory.timestamp.desc()).limit(limit)
            )
            history = result.scalars().all()
            return history
    except Exception as e:
        print(f"ERRO GET /api/telemetry: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/api/telemetry/stats")
async def get_telemetry_stats():
    try:
        async with AsyncSessionLocal() as session:
            # Busca o último registro de telemetria
            result = await session.execute(
                select(TelemetryHistory).order_by(TelemetryHistory.timestamp.desc()).limit(1)
            )
            latest = result.scalars().first()
            
            if latest:
                return {
                    "temp": f"{latest.temp_windings:.1f} °C",
                    "vibration": f"{latest.vibration_rms:.2f} mm/s",
                    "power": f"{(latest.current_a * latest.voltage_v * 0.85 / 1000):.2f} kW", # Estimativa de potência ativa
                    "status": "Nominal" if latest.temp_windings < 50 else "Alerta"
                }
            return {
                "temp": "0.0 °C",
                "vibration": "0.00 mm/s",
                "power": "0.00 kW",
                "status": "Offline"
            }
    except Exception as e:
        print(f"ERRO GET /api/telemetry/stats: {e}")
        return {"temp": "N/A", "vibration": "N/A", "power": "N/A", "status": "Error"}

@app.get("/api/assets")
async def get_assets():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Asset))
            assets = result.scalars().all()
            return [
                {
                    "tag": a.tag,
                    "type": "Motor de Indução",
                    "model": a.model,
                    "health": 98.5, # Placeholder or calculated
                    "status": "Operacional"
                } for a in assets
            ]
    except Exception as e:
        print(f"ERRO GET /api/assets: {e}")
        return []

@app.get("/api/assets/stats")
async def get_assets_stats():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(func.count(Asset.id)))
            count = result.scalar()
            return {
                "total": f"{count}",
                "alerts": "0",
                "health_score": "98.5%"
            }
    except Exception as e:
        print(f"ERRO GET /api/assets/stats: {e}")
        return {"total": "0", "alerts": "0", "health_score": "100%"}

# Para o Vercel, o objeto 'app' deve estar disponível no nível do módulo

