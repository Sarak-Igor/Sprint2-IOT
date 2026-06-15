import asyncio
import uuid
from backend.shared_infra.database_client.postgresql import AsyncSessionLocal
from backend.apps.asset_manager.infrastructure.models import (
    ActiveAssetDB, TelemetryMappingDB, MotorModelDB, DataVariableDB, SensorHardwareDB
)
from sqlalchemy.future import select

async def seed_assets():
    async with AsyncSessionLocal() as session:
        # Busca IDs necessários
        res_model = await session.execute(select(MotorModelDB))
        model = res_model.scalars().first()
        
        res_vars = await session.execute(select(DataVariableDB))
        variables = res_vars.scalars().all()
        
        res_sensor = await session.execute(select(SensorHardwareDB))
        sensor = res_sensor.scalars().first()
        
        if not all([model, variables, sensor]):
            print("Erro: Execute seed_catalog.py primeiro!")
            return

        # 1. Ativo Ativo
        asset = ActiveAssetDB(
            name="Motor W22 - Compressor 01",
            location="Planta Industrial - Setor A",
            motor_model_id=model.id,
            status="operational",
            applied_thresholds={
                str(variables[0].id): {"nominal": 70, "warning": 80, "critical": 90},
                str(variables[1].id): {"nominal": 2.0, "warning": 3.5, "critical": 4.5}
            }
        )
        session.add(asset)
        await session.flush() # Para pegar o ID do asset

        # 2. Mapeamentos
        m1 = TelemetryMappingDB(
            asset_id=asset.id,
            variable_id=variables[0].id,
            sensor_id=sensor.id,
            mqtt_topic="Forzy/telemetry/W22/temp_windings"
        )
        m2 = TelemetryMappingDB(
            asset_id=asset.id,
            variable_id=variables[1].id,
            sensor_id=sensor.id,
            mqtt_topic="Forzy/telemetry/W22/vibration"
        )
        
        session.add_all([m1, m2])
        await session.commit()
        print(f"Ativo '{asset.name}' e mapeamentos criados com sucesso!")

if __name__ == "__main__":
    asyncio.run(seed_assets())
