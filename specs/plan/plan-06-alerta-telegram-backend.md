---
tipo: "plan"
titulo: "Mover o gatilho do alerta Telegram do frontend para o motor de anomalias"
dominio: "digital_twin_core"
status: "🔴 A executar"
prioridade: "Alta"
tags: ["plan", "telegram", "alertas", "confiabilidade"]
relacionados: ["[[specs/specs/02-notificacao-telegram]]", "[[specs/01-digital-twin-core]]"]
depende_de: "plan-11-caracterizar-legado-telemetria"
destino_sintese: "specs/specs/02-notificacao-telegram.md · specs/01-digital-twin-core.md"
---

# 1. Objetivo
O alerta do Telegram passa a disparar sempre que `persistence_handler.py` detecta severidade crítica/atenção
— **independente de haver algum navegador com o Dashboard aberto**.

# 2. Contexto
Depende de `plan-11-caracterizar-legado-telemetria`: esta plan edita `persistence_handler.py` diretamente,
código legado hoje sem nenhum teste automatizado — a caracterização vem primeiro, para não introduzir
regressão silenciosa no motor de anomalias.

Diagnóstico de 2026-08-22 (`specs/specs/02-notificacao-telegram.md`, seção "Correção") confirmou: o gatilho
hoje vive em `frontend/src/pages/Dashboard.tsx:213-246`, dentro de um `useEffect` que compara o valor recebido
via WebSocket contra os thresholds e usa `localStorage` como cooldown de 60s por sensor/status, chamando
`POST /api/alerts/telegram` (`api/index.py:213-254`, que já formata e envia a mensagem — essa parte não muda).
Isso viola duas coisas ao mesmo tempo: (a) confiabilidade — sem aba aberta, sem alerta; (b) a regra de
Frontend Soberano (`arquitetura/01-frontend-soberano.md`, `00-contexto.md §7`) — a UI não deveria decidir se um
valor é crítico, só reagir ao que o backend já decidiu. O backend já calcula essa decisão:
`persistence_handler.py:save_telemetry` (linhas 73-132) já determina `severity` comparando contra
`applied_thresholds` (linhas 96-110) e já grava `OperationalAnomalyDB` — só falta ele também chamar o
Telegram.

# 3. Escopo

## 3.1 Dentro
- `backend/apps/digital_twin_core/persistence_handler.py` — após persistir uma anomalia com severidade
  "alert"/"warning" (bloco das linhas 114-127), disparar a notificação Telegram. Reaproveite a lógica de
  formatação de mensagem hoje em `api/index.py:213-254` (extraia para uma função compartilhada em vez de
  duplicar o texto — decida o melhor local, ex.: `backend/shared_infra/` ou um módulo novo dentro de
  `digital_twin_core/`, mas sem duplicar o corpo da mensagem).
- Implementar cooldown por ativo/variável **no backend** (substitui o `localStorage` do frontend) — pode ser
  em memória no próprio processo (ele já roda como singleton via `RUN_FORZY.bat`).
- `frontend/src/pages/Dashboard.tsx:213-246` — remover o bloco de comparação de threshold e a chamada a
  `/api/alerts/telegram`; o Dashboard volta a só renderizar o que o backend devolve.
- `backend/shared_infra/config.py` — nenhuma variável nova esperada (o token/chat_id já existem ali), mas
  confirme que `persistence_handler.py` consegue acessar `settings.telegram_bot_token`/`telegram_chat_id` sem
  duplicar leitura de `.env`.

## 3.2 Fora
- `POST /api/alerts/telegram` em `api/index.py` — pode continuar existindo (não precisa remover a rota), mas
  deixa de ser chamada pelo frontend. Se o executor decidir removê-la por ficar sem uso, registre a decisão no
  resumo — não é obrigatório.
- Qualquer outra regra de detecção de anomalia em `persistence_handler.py` — não altere os limiares nem a
  lógica de severidade existente, só adicione o disparo do alerta.
- `backend/apps/asset_manager/*` — não muda.

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Spec fixa | `specs/specs/02-notificacao-telegram.md` | Regras de negócio, critérios de aceite e plano de testes já corrigidos para esta implementação |
| Spec fixa | `specs/01-digital-twin-core.md` | Regra de negócio do motor de anomalias que ganha este novo efeito colateral |
| Spec fixa | `arquitetura/01-frontend-soberano.md` | Por que o gatilho não pode ficar na UI |
| Contexto | `00-contexto.md §7` (Frontend não decide regra de negócio) · `00-knowledge.md` | sempre |
| Skill | `padrao-escrita` + `padrao-python` + `padrao-typescript` | Backend e frontend |
| Skill | `test-unitario` | Cobrir o disparo automático e o cooldown no backend |
| Skill | `cyber-segredos` | Confirmar que token/chat_id continuam só via `.env`/`config.py`, nunca hardcoded na nova função |
| Código | `backend/apps/digital_twin_core/persistence_handler.py` | ler antes de editar |
| Código | `api/index.py:213-254` | a lógica de formatação/envio a reaproveitar, não duplicar |
| Código | `frontend/src/pages/Dashboard.tsx:200-250` | ler o bloco inteiro antes de remover |

# 5. Instruções de execução
1. Extrair a lógica de formatação e envio da mensagem Telegram de `api/index.py:213-254` para uma função
   reutilizável (sem duplicar o texto/template), de forma que tanto a rota HTTP quanto
   `persistence_handler.py` possam chamá-la.
2. Em `persistence_handler.py`, após o bloco que já calcula `severity` e grava `OperationalAnomalyDB`
   (linhas 114-127), chamar essa função quando `severity` for "alert" ou "warning", respeitando um cooldown
   por `(asset_id, variable_id, status)` guardado em memória no processo.
3. Remover de `Dashboard.tsx` o bloco `useEffect` de comparação de threshold + chamada a
   `/api/alerts/telegram` (linhas 213-246) — o componente volta a só renderizar telemetria.
4. Escrever os testes descritos no §4 "Plano de Testes" de `specs/specs/02-notificacao-telegram.md`
   (disparo automático sem navegador aberto, cooldown no backend).
5. Validar manualmente (ou via teste E2E, se aplicável) o "Fluxo Crítico" da spec: publicar no broker um valor
   que cruze o threshold **sem nenhum navegador aberto** e confirmar a chegada da mensagem em até 10s.

# 6. Critérios de aceite
- [ ] `persistence_handler.py` dispara o alerta Telegram automaticamente ao detectar severidade crítica.
- [ ] O alerta chega mesmo sem nenhum navegador com o Dashboard aberto (validação manual registrada no resumo).
- [ ] Cooldown por ativo/variável funciona no backend, sem depender de `localStorage`.
- [ ] `Dashboard.tsx` não contém mais lógica de comparação de threshold.
- [ ] Testes unitários da spec de Telegram verdes.

# 7. Como verificar (uso do revisor)
- `git diff --stat` → só os caminhos de §3.1.
- Ler `specs/specs/02-notificacao-telegram.md` critério por critério contra o diff.
- Rodar os testes indicados e ler a saída real.
- Confirmar por leitura que `Dashboard.tsx` não tem mais o bloco de threshold/fetch removido.
- Rodar `cyber-segredos` sobre os arquivos tocados.

# 8. Destino da síntese
**Destino:** `specs/specs/02-notificacao-telegram.md` + `specs/01-digital-twin-core.md`
Marcar os critérios de aceite pendentes da spec de Telegram como atendidos e mudar seu status para
`🟢 Implementado`. Acrescentar em `specs/01-digital-twin-core.md`, na "Efeito Colateral de Anomalia", que o
disparo do alerta Telegram agora faz parte desse efeito colateral.

---

# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

---

# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->
