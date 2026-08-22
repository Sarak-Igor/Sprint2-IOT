---
tipo: "arquitetura"
titulo: "Event-Driven Backend"
dominio: "Infraestrutura / Design"
status: "🟢 Vigente"
tags: ["arquitetura", "backend", "eda"]
relacionados: ["[[01-digital-twin-core]]", "[[02-ingestion-service]]"]
---

# 1. Propósito
A arquitetura do backend do Forzy foi construída em torno de processamento assíncrono e orientado a eventos (Event-Driven Architecture - EDA) para suportar a alta cadência de mensagens oriundas dos sensores IoT industriais (MQTT/OPC UA).

# 2. Stack e Ferramentas
- **Linguagem e API:** Python 3.10+, FastAPI (servidor Uvicorn).
- **Gestão de Configurações:** `pydantic-settings` para carregamento de variáveis de ambiente de forma "fail-fast" (`shared_infra/config.py`).
- **Persistência Assíncrona:** SQLAlchemy 2.0 com `asyncpg` (NeonDB PostgreSQL).
- **Mensageria:** Broker Eclipse Mosquitto (MQTT), integração via `paho-mqtt`.

# 3. Diagramas / Estruturas
Fluxo de dados da telemetria:
1. Sensor de hardware (ou o Mock) publica em `Forzy/telemetry/#`.
2. O `MqttPersistenceHandler` escuta a mensagem de forma assíncrona.
3. A mensagem é resolvida contra a tabela `TelemetryMappingDB` para encontrar o id da variável e ativo.
4. O valor lido é comparado contra os parâmetros estruturais do motor lidos do JSON local (`settings.specs`).
5. Se uma anomalia for detectada, é gerada uma notificação e salva no PostgreSQL assíncrono.

> **Correção (2026-08-22):** `MqttPersistenceHandler` roda em `backend/apps/digital_twin_core/persistence_handler.py`,
> como **processo standalone** (subido por `RUN_FORZY.bat`, fora de Docker/produção) — não é o mesmo processo
> que atende `/api/*`. O gateway HTTP consumido pelo frontend é `api/index.py` (raiz, fora de
> `backend/apps/`), que monta o router de `asset_manager`. Esse gateway roda um **segundo listener MQTT
> paralelo** no mesmo tópico `Forzy/telemetry/#` (`api/index.py:282-358`) só para broadcast via WebSocket — não
> persiste nada, não cria anomalia. Os dois processos duplicam a resolução de tópico de forma independente;
> reconciliação pendente, ver `00-contexto.md §8`.
