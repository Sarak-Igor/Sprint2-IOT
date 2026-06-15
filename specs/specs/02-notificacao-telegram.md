---
tipo: "spec"
titulo: "Notificação e Alertas via Telegram"
dominio: "Monitoramento e Alertas"
status: "🔴 A Implementar" # Opções: 🔴 A Implementar, 🟡 Em Progresso, 🟢 Implementado
prioridade: "Alta"
tags: ["spec", "sprint2", "alerta", "telegram", "node-red"]
relacionados: ["01-utilizacao-node-red"] 
---

# 1. Visão Geral
Para fornecer monitoramento proativo aos operadores industriais, o sistema deverá enviar alertas operacionais sempre que as variáveis lidas excederem os thresholds críticos (limites da máquina). Esta funcionalidade deverá ser acoplada à esteira de ingestão do Node-RED e utilizar um bot do Telegram para a entrega da mensagem.

# 2. Regras de Negócio
- **Regra 1 (Gatilho de Anomalia):** O alerta deve ser disparado caso as medições excedam o parâmetro crítico (por exemplo, `tempW > 156.0`).
- **Regra 2 (Formatação da Mensagem):** A mensagem do Telegram deve conter as informações operacionais mínimas: identificação do ativo (`DEVICE_ID`), qual variável está em estado crítico e o valor atual lido.
- **Regra 3 (Caminho da Solução):** Recomenda-se utilizar o próprio Node-RED (via nós do `node-red-contrib-telegrambot`) para avaliar as regras matemáticas e realizar o push da notificação, isolando a regra no fluxo visual.

# 3. Critérios de Aceite
- [ ] Um bot do Telegram foi criado no BotFather e o token adicionado com segurança ao projeto.
- [ ] Existe um nó (Function Node ou Switch Node) no Node-RED que separa as leituras críticas das normais.
- [ ] Ao enviar uma leitura simulada de superaquecimento (`tempW = 156.0`), o operador recebe a mensagem no Telegram.
- [ ] A mensagem chega em menos de 10 segundos da emissão do evento no broker MQTT.

# 4. Plano de Testes (Quality Gate)

## Testes Unitários
- [ ] N/A

## Testes de Contrato (API)
- [ ] N/A

## Testes E2E (Integração)
- [ ] **Fluxo Feliz (Normal):** Enviar telemetria nominal e garantir que nenhuma mensagem do Telegram seja disparada.
- [ ] **Fluxo Crítico (Anomalia):** Enviar um payload via script de injeção contendo o gatilho (`tempW > 156.0`) e observar a recepção exata do JSON formatado na tela do Telegram do operador.
