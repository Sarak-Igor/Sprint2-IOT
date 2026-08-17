---
tipo: "adr"
titulo: "Infraestrutura e Deploy"
status: "🟢 Aceito"
tags: ["adr", "infra"]
relacionados: []
substitui: ""
substituido_por: ""
---

# 1. Contexto e Problema
Precisamos definir como o projeto será entregue em ambientes de homologação ou produção.

# 2. Decisão
Manter o projeto rodando exclusivamente em ambiente de desenvolvimento local (sem deploy automático na nuvem por enquanto). O foco primário é o desenvolvimento da lógica de negócio e validação inicial, rodando backend com scripts locais (Python) e frontend com `vite`.

# 3. Consequências
- **Positivas:** Maior velocidade de desenvolvimento iterativo sem overhead de infraestrutura e pipelines de CI/CD.
- **Negativas (Trade-offs):** O projeto não fica acessível online para stakeholders imediatamente.
