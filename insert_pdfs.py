import asyncio
import os
import uuid
from backend.shared_infra.database_client.postgresql import AsyncSessionLocal
from backend.apps.ai_knowledge.models import KnowledgeManualDB

async def main():
    files = [
        r"C:\Users\Igor\Downloads\Industrial-Mind-develop\Industrial-Mind-develop\frontend\public\WEG-w22-motor-eletrico-trifasico-brochure.pdf",
        r"C:\Users\Igor\Downloads\8e45401c-5c24-4502-abae-94f5ea5b9e22.pdf"
    ]
    
    async with AsyncSessionLocal() as session:
        for file_path in files:
            if not os.path.exists(file_path):
                print(f"Arquivo não encontrado: {file_path}")
                continue
                
            with open(file_path, "rb") as f:
                pdf_bytes = f.read()
                
            filename = os.path.basename(file_path)
            manual_id = str(uuid.uuid4())
            
            manual_db = KnowledgeManualDB(
                manual_id=manual_id,
                filename=filename,
                pdf_bytes=pdf_bytes,
                total_pages=0
            )
            session.add(manual_db)
            print(f"Adicionado {filename} ({len(pdf_bytes)} bytes)")
            
        await session.commit()
        print("Salvo com sucesso!")

if __name__ == "__main__":
    asyncio.run(main())
