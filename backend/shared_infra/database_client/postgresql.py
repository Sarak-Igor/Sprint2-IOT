from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.shared_infra.config import settings

# Engine assíncrona para o Neon
# O Neon exige SSL, mas o asyncpg prefere receber isso via connect_args
engine = create_async_engine(
    settings.database_url, 
    echo=True,
    connect_args={
        "ssl": "require"
    }
)

# Fábrica de sessões assíncronas
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    """Dependência para obter sessão de banco de dados"""
    async with AsyncSessionLocal() as session:
        yield session
