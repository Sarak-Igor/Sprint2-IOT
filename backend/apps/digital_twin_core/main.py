from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import random
from datetime import datetime, timedelta

from backend.shared_infra.config import settings

app = FastAPI(title="Forzy Digital Twin Core API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AGNOSTIC DATA GENERATORS ---

def get_telemetry_stats():
    specs = settings.specs
    return {
        "efficiency": f"{random.uniform(specs.nominal_data.min_eff, specs.nominal_data.max_eff):.1f}%",
        "power_output": f"{random.randint(int(specs.nominal_data.power_kw * 0.8), int(specs.nominal_data.power_kw))} kW",
        "vibration": f"{random.uniform(0.1, specs.alerts_thresholds.vibration_rms_mm_s.warning):.2f} mm/s",
        "health_score": f"{random.randint(90, 100)}%"
    }

def get_telemetry_trend():
    specs = settings.specs
    return {
        "daily_trend": [
            {"date": (datetime.now() - timedelta(hours=i)).strftime("%H:00"), "value": random.randint(int(specs.nominal_data.rpm * 0.9), specs.nominal_data.rpm)}
            for i in range(15, 0, -1)
        ]
    }

def get_assets():
    specs = settings.specs
    return [
        {
            "id": 1, 
            "tag": "TRB-01", 
            "name": f"{specs.asset_info.manufacturer} {specs.asset_info.model}", 
            "type": "Gas Turbine", 
            "status": "active", 
            "last_maintenance": "2024-04-10", 
            "health": 98
        },
    ]

def get_history():
    events = ["Início de Ciclo", "Ajuste de Carga", "Alerta de Temperatura", "Sincronização de Rede", "Log de Operador"]
    machines = ["Turbina X1", "Gerador G2", "Bomba B4"]
    operators = ["Carlos Silva", "Ana Souza", "Roberto Lima"]
    
    return [
        {
            "id": i,
            "timestamp": (datetime.now() - timedelta(minutes=i*15)).strftime("%Y-%m-%d %H:%M"),
            "event": random.choice(events),
            "machine": random.choice(machines),
            "operator": random.choice(operators),
            "severity": random.choice(["Low", "Medium", "Info"])
        }
        for i in range(20)
    ]

# --- ENDPOINTS ---

@app.get("/telemetry/stats")
async def telemetry_stats():
    return get_telemetry_stats()

@app.get("/telemetry/trend")
async def telemetry_trend():
    return get_telemetry_trend()

@app.get("/assets")
async def list_assets():
    return get_assets()

@app.get("/assets/stats")
async def assets_stats():
    return {
        "total": 45,
        "operational": 42,
        "maintenance": 2,
        "critical": 1
    }

@app.get("/history")
async def list_history():
    return get_history()

@app.get("/history/trend")
async def history_trend():
    return {
        "daily_trend": [
            {"date": (datetime.now() - timedelta(days=i)).strftime("%d/%m"), "value": random.randint(10, 50)}
            for i in range(15, 0, -1)
        ]
    }

@app.get("/vision/stats")
async def vision_stats():
    return {
        "active_cameras": 12,
        "detections_24h": 1240,
        "unauthorized_access": 0,
        "safety_violations": 2
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
