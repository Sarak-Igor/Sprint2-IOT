import asyncio
from backend.shared_infra.database_client.postgresql import AsyncSessionLocal
from backend.apps.asset_manager.infrastructure.models import (
    MotorModelDB, DataVariableDB, SensorHardwareDB
)

async def seed():
    async with AsyncSessionLocal() as session:
        # 1. Modelos de Motor
        weg_w22 = MotorModelDB(
            brand="WEG",
            model="W22 Plus",
            power_hp=10.0,
            spec_reference="https://www.weg.net/catalog/weg/BR/pt/p/MKT_W01_472",
            default_thresholds={"temp": {"max": 90}, "vibration": {"max": 4.5}}
        )
        
        # 2. Variáveis
        temp = DataVariableDB(name="Temperatura Enrolamento", unit="°C", description="Temperatura interna das bobinas")
        vib = DataVariableDB(name="Vibração RMS", unit="mm/s", description="Velocidade de vibração global")
        
        # 3. Sensores
        iqnext = SensorHardwareDB(model_name="IQ-Next Industrial", manufacturer="Forzy Hardware", protocol="MQTT")
        
        session.add_all([weg_w22, temp, vib, iqnext])
        await session.commit()
        print("Catálogo semeado com sucesso!")

if __name__ == "__main__":
    asyncio.run(seed())
