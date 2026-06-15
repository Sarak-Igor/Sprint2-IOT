from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import random
from datetime import datetime, timedelta

app = FastAPI(title="Forzy Digital Twin Core API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MOCK DATA GENERATORS ---

def get_telemetry_stats():
    return {
        "efficiency": f"{random.uniform(85, 98):.1f}%",
        "power_output": f"{random.randint(400, 550)} MW",
        "vibration": f"{random.uniform(0.1, 0.5):.2f} mm/s",
        "health_score": f"{random.randint(90, 100)}%"
    }

def get_telemetry_trend():
    return {
        "daily_trend": [
            {"date": (datetime.now() - timedelta(hours=i)).strftime("%H:00"), "value": random.randint(80, 100)}
            for i in range(15, 0, -1)
        ]
    }

def get_assets():
    return [
        {"id": 1, "tag": "TRB-01", "name": "Turbina Principal", "type": "Gas Turbine", "status": "active", "last_maintenance": "2024-04-10", "health": 98},
        {"id": 2, "tag": "PMP-04", "name": "Bomba de Arrefecimento", "type": "Centrifugal Pump", "status": "active", "last_maintenance": "2024-03-20", "health": 85},
        {"id": 3, "tag": "GEN-02", "name": "Gerador Síncrono", "type": "Generator", "status": "active", "last_maintenance": "2024-05-01", "health": 99},
        {"id": 4, "tag": "VLV-12", "name": "Válvula de Controle", "type": "Control Valve", "status": "maintenance", "last_maintenance": "2024-05-02", "health": 45},
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
