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
O módulo central responsável por ouvir a telemetria que entra via MQTT, identificar o ativo correspondente, gravar o dado bruto e processar anomalias dinamicamente baseando-se nos limites operacionais do motor elétrico sendo monitorado. O módulo também expõe a API HTTP (FastAPI) para que o frontend exiba os dashboards.

# 2. Regras de Negócio
- **Mapeamento de Tópicos MQTT:** Tópicos dinâmicos (ex: `Forzy/telemetry/sensor1`) são traduzidos em entidades lógicas (`asset_id`, `variable_id`) via banco de dados (`TelemetryMappingDB`), utilizando cache em memória (`TopicResolver`) para alta performance.
- **Detecção Inteligente de Anomalias:** Ao receber um valor numérico, o handler compara com o limiar crítico/nominal gravado no banco (`applied_thresholds`). O módulo é inteligente o suficiente para identificar limites superiores (temperatura alta) ou inferiores (baixa eficiência/RPM).
- **Efeito Colateral de Anomalia:** Se um dado cruzar a faixa crítica, um registro em `OperationalAnomalyDB` é criado, e o status do ativo global é alterado para "alert" ou "warning".

# 3. Critérios de Aceite
- [x] O serviço consegue conectar ao Broker MQTT e ouvir o tópico `#`.
- [x] Mensagens JSON e valores string puros são aceitos e normalizados.
- [x] Anomalias são identificadas e persistem no banco assincronamente.
- [x] O Frontend consegue chamar endpoints como `/telemetry/stats` e receber os resumos do banco (mock ou real).

# 4. Plano de Testes (Quality Gate)
Mapeamento obrigatório dos testes para validação.

## Testes Unitários
- [ ] **Deve** tratar exceção graciosamente quando o payload MQTT for inválido (não JSON ou não Float).
- [ ] **Deve** identificar corretamente o limiar inferior (`critical < nominal`) gerando alerta caso valor <= `critical`.

## Testes E2E (Integração)
- [ ] Fluxo feliz: Mock enviar MQTT -> Handler salvar leitura -> API FastAPI devolver no histórico.
