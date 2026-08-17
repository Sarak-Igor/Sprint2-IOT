---
tipo: "adr"
titulo: "Persistência e Banco de Dados"
status: "🟢 Aceito"
tags: ["adr", "database"]
relacionados: []
substitui: ""
substituido_por: ""
---

# 1. Contexto e Problema
Precisamos de um banco de dados relacional que suporte operações assíncronas e seja confiável para armazenamento do modelo de dados da aplicação.

# 2. Decisão
Adotar o **PostgreSQL** hospedado na NeonDB, com integração no backend via **SQLAlchemy e asyncpg**. Sem implementação formal de cache distribuído num primeiro momento.

# 3. Consequências
- **Positivas:** Banco relacional robusto e maduro, alta escalabilidade com NeonDB, performance assíncrona com asyncpg.
- **Negativas (Trade-offs):** Menos flexibilidade que NoSQL em esquemas mutáveis, exigência do Alembic para migrations.
