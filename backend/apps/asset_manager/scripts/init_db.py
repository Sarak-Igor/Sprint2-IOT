import asyncio
from backend.shared_infra.database_client.postgresql import engine, Base
# Importar todos os modelos para garantir que o Base os conheça
from backend.apps.asset_manager.infrastructure.models import MotorModelDB, DataVariableDB, SensorHardwareDB, ActiveAssetDB, TelemetryMappingDB

async def init_db():
    async with engine.begin() as conn:
        print("Criando tabelas no Neon...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tabelas criadas!")

if __name__ == "__main__":
    asyncio.run(init_db())
