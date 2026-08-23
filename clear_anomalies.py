import asyncio
from sqlalchemy import delete
from backend.shared_infra.database_client.postgresql import AsyncSessionLocal
from backend.apps.asset_manager.infrastructure.models import OperationalAnomalyDB

async def run():
    async with AsyncSessionLocal() as db:
        await db.execute(delete(OperationalAnomalyDB))
        await db.commit()
        print('Old anomalies deleted')

asyncio.run(run())
