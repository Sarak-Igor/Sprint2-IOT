---
tipo: "spec"
titulo: "Digital Twin Core"
dominio: "digital_twin_core"
status: "🟢 Implementado"
prioridade: "Alta"
tags: ["spec", "backend", "twin"]
relacionados: ["[[02-backend-eda]]"]
---

# 1. Visão Geral
O módulo central responsável por ouvir a telemetria que entra via MQTT, identificar o ativo correspondente, gravar o dado bruto e processar anomalias dinamicamente baseando-se nos limites operacionais do motor elétrico sendo monitorado.

> **Correção (2026-08-22):** o entrypoint real deste módulo é `backend/apps/digital_twin_core/persistence_handler.py`
> (classes `TopicResolver` + `MqttPersistenceHandler`), executado como **processo Python standalone**
> (`RUN_FORZY.bat` sobe-o separado da API). Ele **não** expõe API HTTP — `digital_twin_core/main.py` é um
> resquício de protótipo com dados 100% mockados (`random.*`), não referenciado por nenhum script de subida;
> não usar como referência de comportamento. `anomaly_logger.py` e `converters/metric_converter.py` também não
> são importados pelo `persistence_handler.py` — órfãos. A API HTTP que o frontend de fato consome
> (`/api/assets/*`, dashboards) é do módulo `asset_manager`, servida pelo gateway `api/index.py` (fora de
> `backend/apps/`) — ver `specs/02-ingestion-service.md` e `arquitetura/02-backend-eda.md`.

# 2. Regras de Negócio
- **Mapeamento de Tópicos MQTT:** Tópicos dinâmicos (ex: `Forzy/telemetry/sensor1`) são traduzidos em entidades lógicas (`asset_id`, `variable_id`) via banco de dados (`TelemetryMappingDB`), utilizando cache em memória (`TopicResolver`) para alta performance.
- **Detecção Inteligente de Anomalias:** Ao receber um valor numérico, o handler compara com o limiar crítico/nominal gravado no banco (`applied_thresholds`). O módulo é inteligente o suficiente para identificar limites superiores (temperatura alta) ou inferiores (baixa eficiência/RPM).
- **Efeito Colateral de Anomalia:** Se um dado cruzar a faixa crítica, um registro em `OperationalAnomalyDB` é criado, e o status do ativo global é alterado para "alert" ou "warning". **Não** dispara alerta Telegram — ver `specs/specs/02-notificacao-telegram.md` para a lacuna de confiabilidade encontrada nesse ponto.

# 3. Critérios de Aceite
- [x] O serviço consegue conectar ao Broker MQTT e ouvir o tópico `#`.
- [x] Mensagens JSON e valores string puros são aceitos e normalizados.
- [x] Anomalias são identificadas e persistem no banco assincronamente.
- [x] O Frontend consegue chamar endpoints como `/telemetry/stats` e receber os resumos do banco (mock ou real).

# 4. Plano de Testes (Quality Gate)
Mapeamento obrigatório dos testes para validação.

## Testes Unitários
- [x] **Deve** tratar exceção graciosamente quando o payload MQTT for inválido (não JSON ou não Float).
- [x] **Deve** identificar corretamente o limiar inferior (`critical < nominal`) gerando alerta caso valor <= `critical`.

## Testes E2E (Integração)
- [ ] Fluxo feliz: Mock enviar MQTT -> Handler salvar leitura -> API FastAPI devolver no histórico.
