from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Type, TypeVar, Generic
from uuid import UUID
from backend.apps.asset_manager.infrastructure.models import (
    MotorModelDB, DataVariableDB, SensorHardwareDB, ActiveAssetDB, TelemetryMappingDB, OperationalAnomalyDB
)

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def get_all(self) -> List[T]:
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def get_by_id(self, id: UUID) -> T:
        result = await self.session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def create(self, entity_db: T) -> T:
        self.session.add(entity_db)
        await self.session.commit()
        await self.session.refresh(entity_db)
        return entity_db

    async def delete(self, id: UUID) -> bool:
        entity = await self.get_by_id(id)
        if entity:
            await self.session.delete(entity)
            await self.session.commit()
            return True
        return False

    async def update(self, id: UUID, **kwargs) -> T:
        entity = await self.get_by_id(id)
        if entity:
            for key, value in kwargs.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            await self.session.commit()
            await self.session.refresh(entity)
        return entity

class AssetRepository:
    def __init__(self, session: AsyncSession):
        self.motors = BaseRepository(session, MotorModelDB)
        self.variables = BaseRepository(session, DataVariableDB)
        self.sensors = BaseRepository(session, SensorHardwareDB)
        self.assets = BaseRepository(session, ActiveAssetDB)
        self.mappings = BaseRepository(session, TelemetryMappingDB)
        self.anomalies = BaseRepository(session, OperationalAnomalyDB)
        self.session = session

    async def get_asset_with_telemetry(self, asset_id: UUID):
        # Lógica para buscar o ativo e seus mapeamentos de sensores
        asset = await self.assets.get_by_id(asset_id)
        if not asset:
            return None
            
        result = await self.session.execute(
            select(TelemetryMappingDB).where(TelemetryMappingDB.asset_id == asset_id)
        )
        mappings = result.scalars().all()
        return {"asset": asset, "mappings": mappings}
