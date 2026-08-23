---
tipo: "spec"
titulo: "Agente Conversacional de IA (ligado à base de conhecimento RAG)"
dominio: "ai_knowledge / agente"
status: "🔴 A Implementar"
prioridade: "Média"
tags: ["spec", "agente", "ia", "rag", "futuro"]
relacionados: []
---

# 1. Visão Geral
Um agente de IA conversacional para os operadores do Forzy — nesta primeira fase, com uma única
capacidade obrigatória: consultar a base de conhecimento (RAG) sobre os manuais técnicos já
implementada (`backend/apps/ai_knowledge/rag_engine.py`, `POST /api/knowledge/ask`). O agente
**não reimplementa** recuperação nem geração de texto — ele **usa** o que já existe como uma
capacidade/ferramenta entre outras que possa vir a ganhar depois. O RAG em si permanece
deliberadamente simples (retrieve-then-generate direto, sem múltiplos saltos de raciocínio); toda
sofisticação de orquestração (decidir quando consultar manuais, o que fazer com a resposta, se
combinar com outras fontes) vive na camada do agente, não no RAG.

> **Nota de maturidade:** esta spec nasce com propósito, não com todos os detalhes decididos —
> ver §5 "Em aberto". É o registro formal de uma decisão de arquitetura já tomada (o RAG fica
> simples e desacoplado) mais o espaço reservado para as decisões que ainda faltam, para não se
> perderem antes de uma plan ser escrita.

# 2. Regras de Negócio
- **Regra 1 (RAG como capacidade, não como agente):** o agente consome `answer_question()` (ou o
  endpoint `POST /api/knowledge/ask`) tal como já implementado e aprovado — nenhuma mudança no
  RAG é pré-requisito para o agente existir.
- **Regra 2 (RAG permanece simples):** qualquer necessidade de raciocínio em múltiplos passos,
  múltiplas fontes ou decisão sobre *quando* consultar os manuais é responsabilidade do agente,
  nunca uma responsabilidade nova empurrada para dentro do RAG.
- **Regra 3 (citação preservada):** toda resposta do agente que se apoiar na base de manuais deve
  preservar a citação de fonte (manual + página) que `AskResponse.fontes` já fornece — o agente
  não pode "resumir" a resposta do RAG de um jeito que perca a rastreabilidade da fonte.
- **Regra 4 (escopo desta primeira versão — decidido com o usuário em 2026-08-22):** a única
  capacidade do agente é a consulta a manuais via RAG. Nenhuma leitura de telemetria/anomalias/
  ativos nem ação sobre o sistema (criar ativo, disparar alerta) nesta fase — cada uma dessas
  seria uma superfície de risco nova, decidida numa plan própria e futura.
- **Regra 5 (interface — aba própria):** o agente vive em uma aba dedicada do frontend, separada
  da aba "Knowledge" (que continua sendo só a base de manuais + upload). Não evolui o painel
  "Assistente de Conhecimento" existente ali.
- **Regra 6 (memória de sessão):** o agente mantém contexto de conversa dentro de uma mesma sessão
  (mensagens anteriores influenciam a interpretação de mensagens seguintes) — diferente do RAG
  puro, que trata cada pergunta isoladamente. A sessão não precisa sobreviver a um reload de
  página nem persistir em banco (ver escopo da plan de implementação).
- **Regra 7 (orquestração por function-calling):** um único LLM decide, via tool-calling, se a
  pergunta do operador exige consultar a capacidade de RAG ou pode ser respondida diretamente
  (ou recusada, se fora do que o agente sabe fazer) — sem um roteador de intenção separado.
- **Regra 8 (autenticação):** como login está postergado (`adr/003-autenticacao.md`), o agente
  herda essa mesma limitação — sem diferenciação de operador por enquanto.

# 3. Critérios de Aceite
- [ ] O agente responde a uma pergunta usando a base de manuais e cita a fonte (manual + página).
- [ ] O agente não reimplementa nenhuma parte do pipeline de RAG (extração de PDF, chunking,
  vetor-store) — só consome a função/endpoint já existente.
- [ ] O agente vive em uma aba própria do frontend, distinta da aba "Knowledge".
- [ ] O agente mantém contexto de conversa dentro de uma sessão (uma pergunta de acompanhamento,
  sem repetir o assunto, é respondida coerentemente com a mensagem anterior).
- [ ] Um único LLM decide via function-calling quando chamar a capacidade de RAG; pergunta fora do
  domínio de manuais não aciona a capacidade indevidamente nem inventa uma capacidade inexistente.
- [ ] Nenhuma capacidade além da consulta a manuais foi implementada nesta primeira versão.

# 4. Plano de Testes (Quality Gate)

## Testes Unitários
- [ ] **Deve** chamar a capacidade de RAG (mockada) e repassar a resposta com fontes intactas.
- [ ] **Deve** tratar graciosamente a ausência de manuais indexados (mesmo comportamento que
  `answer_question` já tem hoje: mensagem informativa, não erro).
- [ ] **Deve** decidir, via LLM mockado, entre acionar a capacidade de RAG ou responder direto,
  conforme o conteúdo da pergunta.
- [ ] **Deve** manter e usar o histórico de mensagens de uma sessão ao montar a próxima chamada ao
  LLM, com um limite máximo de mensagens guardadas (mitigação de custo/Model DoS).

## Testes E2E (Integração)
- [ ] Fluxo feliz: usuário abre a aba do agente, pergunta algo coberto por um manual indexado,
  recebe resposta com fonte; faz uma segunda pergunta de acompanhamento e a resposta usa o
  contexto da primeira.

# 5. Decisões tomadas (HITL com o usuário, 2026-08-22)
As perguntas abaixo, antes em aberto, foram decididas pelo usuário na criação da primeira plan de
implementação (`plan-14-agente-conversacional`) — o resultado de cada uma virou regra de negócio
em §2:

- **Escopo de capacidades** → Regra 4: só RAG de manuais nesta primeira versão.
- **Interface** → Regra 5: aba própria.
- **Memória de conversa** → Regra 6: mantém contexto dentro da sessão.
- **Modelo/orquestração** → Regra 7: LLM único com function-calling.
- **Autenticação/autorização** → Regra 8: sem diferenciação de operador (herda `adr/003`).

**Ainda em aberto, deliberadamente fora desta primeira plan:** qualquer capacidade nova (leitura de
telemetria/anomalias/ativos, ações sobre o sistema) fica para uma decisão e uma plan futuras,
quando houver necessidade real declarada.

# 6. Contrato de manutenção desta spec
As decisões de escopo desta primeira versão estão fechadas (§5). Uma capacidade nova exige nova
rodada de decisão com o usuário e atualização desta spec (Regra 4 e §5), na mesma ação em que a
plan correspondente for escrita.
