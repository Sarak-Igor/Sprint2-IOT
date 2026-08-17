---
tipo: "adr"
titulo: "Integrações Críticas Iniciais"
status: "🟢 Aceito"
tags: ["adr", "integrations"]
relacionados: []
substitui: ""
substituido_por: ""
---

# 1. Contexto e Problema
Identificar serviços de terceiros e protocolos vitais para a operação do sistema.

# 2. Decisão
Habilitar as seguintes integrações críticas na fundação do sistema:
- **Cloudflare R2** para armazenamento e gestão de objetos e assets (S3-compatible).
- **Telegram Bot API** para sistema de alertas e notificações.
- **Broker MQTT e Servidor OPC UA** como gateways para comunicação IoT com equipamentos industriais.

# 3. Consequências
- **Positivas:** Arquitetura já preparada para lidar com os principais protocolos IoT (MQTT/OPC UA) e armazenamento em nuvem escalável, centralizando alertas via mensageria popular (Telegram).
- **Negativas (Trade-offs):** Aumento da complexidade e da superfície de dependências externas para rodar o projeto completamente.
