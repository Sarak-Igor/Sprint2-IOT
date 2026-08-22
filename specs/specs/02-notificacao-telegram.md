---
tipo: "spec"
titulo: "Notificação e Alertas via Telegram"
dominio: "Monitoramento e Alertas"
status: "🟡 Em Progresso" # Opções: 🔴 A Implementar, 🟡 Em Progresso, 🟢 Implementado
prioridade: "Alta"
tags: ["spec", "sprint2", "alerta", "telegram"]
relacionados: ["[[01-digital-twin-core]]"]
---

# 1. Visão Geral
Para fornecer monitoramento proativo aos operadores industriais, o sistema deve enviar alertas operacionais
sempre que as variáveis lidas excederem os thresholds críticos (limites da máquina), via bot do Telegram.

> **Correção (2026-08-22):** esta spec descrevia originalmente uma arquitetura via Node-RED
> (`node-red-contrib-telegrambot`). O repositório não tem Node-RED em lugar nenhum — `docs/PLANEJAMENTO.md`
> chegou a propor essa migração, mas a decisão do projeto (confirmada com o responsável) é **manter o fluxo em
> Python**: o envio já está implementado via chamada HTTP direta à API do Telegram, dentro do gateway
> `api/index.py` (`POST /api/alerts/telegram`, `api/index.py:213-254`), usando `telegram_bot_token`/
> `telegram_chat_id` de `backend/shared_infra/config.py`. Esta spec passa a descrever essa implementação real.
>
> **Defeito de confiabilidade encontrado:** o gatilho (comparação do valor contra o threshold) não vive no
> backend — está em `frontend/src/pages/Dashboard.tsx:213-246`, dentro de um `useEffect` que reage ao
> WebSocket de telemetria e usa `localStorage` como cooldown de 60s por sensor/status. Consequência: **se
> nenhum operador estiver com a aba do Dashboard aberta, nenhum alerta é enviado** — a Regra 1 abaixo não é
> garantida hoje. Além disso, essa comparação de threshold no frontend viola a regra de "Frontend Soberano"
> (`arquitetura/01-frontend-soberano.md`, `00-contexto.md §7`: a UI não decide regra de negócio do motor,
> apenas reage ao que o backend devolve). O motor correto para esse gatilho é
> `backend/apps/digital_twin_core/persistence_handler.py`, que já calcula a severidade
> (`save_telemetry`, linhas 96-110) mas hoje não aciona o Telegram.

# 2. Regras de Negócio
- **Regra 1 (Gatilho de Anomalia):** O alerta deve ser disparado caso as medições excedam o parâmetro crítico
  (por exemplo, `tempW > 156.0`) — **independente de haver ou não um navegador com o Dashboard aberto**. O
  gatilho deve mover-se para o backend (`persistence_handler.py`, junto ao cálculo de severidade existente).
- **Regra 2 (Formatação da Mensagem):** A mensagem do Telegram deve conter as informações operacionais mínimas: identificação do ativo, qual variável está em estado crítico e o valor atual lido — já atendida pelo payload de `POST /api/alerts/telegram`.
- **Regra 3 (Caminho da Solução):** Chamada HTTP direta à API do Telegram a partir do backend Python — sem Node-RED.

# 3. Critérios de Aceite
- [x] Um bot do Telegram foi criado no BotFather e o token está configurado via `.env`/`shared_infra/config.py`.
- [x] A mensagem chega formatada com ativo, variável, valor e limite (`api/index.py:231-238`).
- [ ] O alerta dispara mesmo sem nenhum navegador com o Dashboard aberto (gatilho movido para o backend).
- [ ] A mensagem chega em menos de 10 segundos da emissão do evento no broker MQTT, medida a partir do
  `persistence_handler.py` (e não de um `fetch` do frontend).

# 4. Plano de Testes (Quality Gate)

## Testes Unitários
- [ ] **Deve** disparar o alerta quando `persistence_handler.py` calcula severidade "alert"/"warning", sem depender do frontend.
- [ ] **Deve** respeitar cooldown por ativo/variável no backend (evitar flood), substituindo o cooldown por `localStorage` do frontend.

## Testes de Contrato (API)
- [ ] `POST /api/alerts/telegram`: mantém o schema atual (compatibilidade com qualquer chamador remanescente).

## Testes E2E (Integração)
- [ ] **Fluxo Feliz (Normal):** Enviar telemetria nominal e garantir que nenhuma mensagem do Telegram seja disparada.
- [ ] **Fluxo Crítico (Anomalia):** Publicar no broker MQTT um valor que cruze o threshold crítico, sem nenhum navegador aberto, e confirmar a chegada da mensagem no Telegram em até 10s.
