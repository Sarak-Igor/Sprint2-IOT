---
tipo: "adr"
titulo: "Stack Principal (Front-end e Back-end)"
status: "🟢 Aceito"
tags: ["adr", "stack"]
relacionados: []
substitui: ""
substituido_por: ""
---

# 1. Contexto e Problema
Necessidade de definir a linguagem e frameworks base para o frontend e backend da aplicação, garantindo produtividade, performance e tipagem segura.

# 2. Decisão
Adotar **React, Vite e TypeScript** para o Front-end, utilizando TailwindCSS para estilização e Echarts/Recharts para gráficos.
Para o Back-end, adotar **Python com FastAPI e Pydantic**, focando em alta performance e validação robusta de dados.

# 3. Consequências
- **Positivas:** Tipagem estática no frontend (TS) e backend (Pydantic/MyPy). Ecossistema moderno e rápido (Vite e FastAPI). Ecossistema rico para machine learning/IA no Python.
- **Negativas (Trade-offs):** Diferentes linguagens no front (TS) e back (Python) exigem domínio de ambas as stacks.
