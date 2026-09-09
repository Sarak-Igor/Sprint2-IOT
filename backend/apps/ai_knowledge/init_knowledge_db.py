import asyncio
from sqlalchemy import text
from backend.shared_infra.database_client.postgresql import engine, Base
from backend.apps.ai_knowledge.models import KnowledgeManualDB, KnowledgeChunkDB

async def init_knowledge_db():
    async with engine.begin() as conn:
        print("Habilitando extensão pgvector no Neon...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        
        print("Criando tabelas da base de conhecimento...")
        await conn.run_sync(Base.metadata.create_all)
        print("Extensão habilitada e tabelas criadas!")

if __name__ == "__main__":
    asyncio.run(init_knowledge_db())
