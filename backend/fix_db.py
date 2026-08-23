import asyncio
from sqlalchemy import select, update
from backend.shared_infra.database_client.postgresql import AsyncSessionLocal
from backend.apps.asset_manager.infrastructure.models import DataVariableDB

async def run():
    async with AsyncSessionLocal() as session:
        # Pega as variaveis atuais
        res = await session.execute(select(DataVariableDB))
        vars_db = res.scalars().all()
        print("Atuais:")
        for v in vars_db:
            print(f"- {v.name}")

        # O CSV tem 6 grandezas: 1.1 Velocidade, 1.2 Aceleração, 1.3 Temp, 2.1 Vel, 2.2 Acel, 2.3 Temp.
        # Vamos renomear as 6 variáveis existentes para corresponder ao CSV.
        
        # Mapeamento desejado (de 6 para 6):
        new_names = [
            ("Velocidade - Porta 1", "mm/s"),
            ("Aceleração - Porta 1", "mm/s²"),
            ("Temperatura - Porta 1", "°C"),
            ("Velocidade - Porta 2", "mm/s"),
            ("Aceleração - Porta 2", "mm/s²"),
            ("Temperatura - Porta 2", "°C")
        ]
        
        if len(vars_db) >= 6:
            for i in range(6):
                vars_db[i].name = new_names[i][0]
                vars_db[i].unit = new_names[i][1]
            await session.commit()
            print("Atualizado com sucesso para paridade do CSV.")
        else:
            print("Não há variáveis suficientes para mapear as 6 do CSV.")

if __name__ == "__main__":
    asyncio.run(run())
