---
tipo: "arquitetura"
titulo: "Fundação Tecnológica e Stack"
dominio: "Infraestrutura / Design"
status: "🟢 Vigente"
tags: ["arquitetura"]
relacionados: ["001-stack-principal", "002-banco-de-dados", "003-autenticacao", "004-infra-deploy", "005-integracoes-iniciais"]
---

# 1. Propósito
Mapear as decisões fundamentais e a stack tecnológica escolhida para dar o pontapé inicial no repositório do Industrial Mind.

# 2. Stack e Ferramentas
- **Frontend:** React, Vite, TypeScript, ECharts e TailwindCSS ([[001-stack-principal]]).
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy ([[001-stack-principal]]).
- **Banco de Dados:** PostgreSQL (via NeonDB) ([[002-banco-de-dados]]).
- **Integrações e IoT:** Cloudflare R2, Telegram, Broker MQTT e Servidor OPC UA ([[005-integracoes-iniciais]]).
- **Segurança e Infra:** Sem autenticação e deploy no momento ([[003-autenticacao]], [[004-infra-deploy]]).

# 3. Diagramas / Estruturas
A fundação do projeto foi guiada pelas decisões de Design documentadas nas ADRs correspondentes:
- [[001-stack-principal]]: Linguagens e frameworks principais.
- [[002-banco-de-dados]]: Padrão de persistência adotado.
- [[003-autenticacao]]: Diretrizes de segurança.
- [[004-infra-deploy]]: Modelo de deployment.
- [[005-integracoes-iniciais]]: Comunicação com serviços e equipamentos externos.
