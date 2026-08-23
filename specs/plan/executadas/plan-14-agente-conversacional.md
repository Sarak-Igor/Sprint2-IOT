---
tipo: "plan"
titulo: "Implementar o agente conversacional de IA (RAG como capacidade, aba própria, memória de sessão)"
dominio: "ai_knowledge / agente"
status: "🟢 Aprovada"
prioridade: "Média"
tags: ["plan", "agente", "ia", "rag", "llm"]
relacionados: ["[[specs/06-agente-conversacional]]"]
depende_de: "—"
destino_sintese: "specs/05-ai-knowledge.md · specs/06-agente-conversacional.md"
---

# 1. Objetivo
O operador consegue conversar, numa aba própria do frontend, com um agente de IA que mantém
contexto de sessão e consulta a base de manuais (RAG) quando a pergunta exigir, sempre citando a
fonte — sem reimplementar nada do pipeline de RAG já aprovado.

# 2. Contexto
`specs/06-agente-conversacional.md` registrava o propósito do agente com decisões em aberto (§5
antiga). Em HITL de 2026-08-22, o usuário decidiu: escopo restrito a RAG de manuais nesta primeira
versão (nenhuma leitura de telemetria/anomalias/ativos, nenhuma ação sobre o sistema); interface em
aba própria (não evolui o painel dentro de "Knowledge"); memória de conversa dentro da sessão;
orquestração por um único LLM com function-calling. A spec fixa já foi atualizada na mesma ação em
que esta plan foi escrita — §2 (Regras 4-8) e §3 (critérios) dela são a fonte de verdade das
decisões, não repetidas aqui além do necessário para orientar a implementação.

Infraestrutura já aprovada e disponível para reaproveitar, sem duplicar:
- `backend/apps/ai_knowledge/rag_engine.py::answer_question()` — a capacidade de RAG em si
  (retrieve-then-generate), retorna `AskResponse` com `resposta` e `fontes: list[SourceCitation]`
  (`manual`, `pagina`). Não editar.
- `backend/shared_infra/llm_client.py::invoke_with_fallback(run, **llm_kwargs)` (`plan-13`,
  aprovada) — helper compartilhado que tenta a lista de modelos de `llm_models.json` em ordem,
  Fail-Fast se a chave/config estiver ausente. Todo módulo LLM do projeto usa este helper, não
  monta `ChatOpenAI` diretamente — o agente segue o mesmo padrão.
- `backend/apps/asset_manager/domain/ai_enrichment.py` — referência de forma para Fail-Fast,
  tratamento de erro de domínio e uso de `invoke_with_fallback` (não usa tool-calling, mas o
  esqueleto de erro/validação é o mesmo a seguir).

# 3. Escopo

## 3.1 Dentro
- `backend/apps/ai_knowledge/agent/` (novo subpacote, mesmo nível de `vision/` dentro de
  `asset_manager`): schemas de request/response do chat, a tool que encapsula `answer_question()`,
  o motor do agente (decide tool-calling, gerencia memória de sessão em processo) e o router HTTP.
- `api/index.py` — montar o novo router (companion necessário, mesmo padrão já usado nas plans
  01/02/03/04: 2 linhas, import + `include_router`).
- `frontend/src/pages/` — nova página/aba dedicada ao agente (nome a critério do executor, ex.:
  `Agent.tsx`), com uma UI de chat simples (histórico de mensagens + input).
- `frontend/src/main.tsx` (ou onde quer que as abas sejam registradas hoje — ler o padrão de uma
  aba existente, ex. "knowledge"/"simulator", antes de adicionar) — registrar a nova aba.

## 3.2 Fora
- `backend/apps/ai_knowledge/rag_engine.py`, `vector_store.py`, `pdf_ingestion.py`,
  `backend/apps/ai_knowledge/router.py` (`/knowledge/ask`, `/knowledge/ingest`) — nenhuma mudança;
  o agente só consome `answer_question()` como função, não a rota HTTP.
- `backend/apps/ai_knowledge/schemas.py` — `SourceCitation`/`AskResponse` são só importados/
  reaproveitados, não duplicados nem alterados.
- `backend/shared_infra/llm_client.py`, `llm_models.json` — reaproveitados como estão; não criar
  um novo helper de fallback nem duplicar `_build_llm()`.
- Qualquer leitura de telemetria/anomalias/ativos ou ação sobre o sistema pelo agente — fora desta
  primeira versão (Regra 4 da spec, decisão explícita do usuário).
- A aba "Knowledge" existente (`frontend/src/pages/Knowledge.tsx`) — não editar; o painel
  "Assistente de Conhecimento" que já existe ali continua como está.
- `backend/apps/digital_twin_core/*`, `backend/apps/asset_manager/*` (exceto leitura de
  `ai_enrichment.py` como referência), `backend/apps/ingestion_service/*` — não mudam.
- Persistência de sessão em banco de dados — a sessão vive em memória do processo (mesmo espírito
  do cooldown em memória já usado em outra plan aprovada); não sobreviver a um restart do processo
  não é uma regressão para esta plan.
- Login/autenticação — continua postergado (`adr/003-autenticacao.md`); não implementar
  diferenciação de operador.

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Spec fixa | `specs/06-agente-conversacional.md` | Regras de negócio (4-8) e critérios de aceite completos desta plan |
| Contexto | `00-contexto.md` (Frontend Soberano, §7) · `00-knowledge.md` | sempre |
| Skill | `padrao-escrita` + `padrao-python` + `padrao-typescript` | backend e frontend |
| Skill | `test-unitario` | cobrir decisão de tool-calling, preservação de fonte, limite de memória de sessão |
| Skill | `cyber-ia` | conversa do operador chega a um LLM com tool-calling — tratar mensagens como dado, nunca como instrução ao sistema; limitar tamanho de mensagem e de histórico guardado (mitigação de Model DoS, mesmo espírito da `plan-12`) |
| Código | `backend/apps/ai_knowledge/rag_engine.py`, `schemas.py` | contrato de `answer_question()`/`AskResponse`/`SourceCitation` a reaproveitar, ler antes de codificar |
| Código | `backend/shared_infra/llm_client.py` | helper de fallback a reusar — ler `invoke_with_fallback()` inteiro antes |
| Código | `backend/apps/asset_manager/domain/ai_enrichment.py` | padrão de Fail-Fast e erro de domínio já aprovado |
| Código | `frontend/src/pages/Knowledge.tsx` | padrão visual de chamada a endpoint de IA + exibição de fonte, a seguir na nova página |
| Código | `frontend/src/main.tsx` | padrão de registro de aba existente, a seguir para a aba nova |

# 5. Instruções de execução
1. Ler por completo `rag_engine.py`, `schemas.py` (de `ai_knowledge`) e `llm_client.py`
   (`shared_infra`) antes de escrever qualquer linha — são os dois contratos que esta plan reusa
   sem duplicar.
2. Criar `backend/apps/ai_knowledge/agent/schemas.py` — schemas Pydantic de request/response do
   chat (ex.: mensagem do usuário + `session_id`; resposta com texto + `fontes` opcional),
   reaproveitando `SourceCitation` de `ai_knowledge/schemas.py` por import, não duplicação.
   `session_id` e mensagem com `max_length` (mitigação de Model DoS pedida por `cyber-ia`).
3. Criar a tool que encapsula `answer_question()` (LangChain tool/function), com uma descrição
   clara para o LLM de quando ela deve ser chamada (perguntas sobre manuais/especificações
   técnicas de equipamento) — a tool não reimplementa nada, só chama a função já existente.
4. Criar o motor do agente: recebe `session_id` + mensagem, recupera (ou inicia) o histórico da
   sessão guardado em memória do processo, monta a chamada ao LLM com a tool disponível via
   `invoke_with_fallback` (nunca montando `ChatOpenAI` diretamente), decide entre usar o resultado
   da tool (preservando `fontes`, Regra 3 da spec) ou responder direto. Limitar o histórico salvo
   por sessão a um número máximo de mensagens (ex.: as últimas 10) — mitigação de custo/Model DoS
   e requisito da Regra 6.
5. Criar o router HTTP: `POST /agent/chat` (ou nome equivalente), validando o request antes de
   chamar o motor do agente; Fail-Fast se a config de LLM estiver ausente (herdado de
   `invoke_with_fallback`, não reimplementar a checagem).
6. Montar o novo router em `api/index.py` (import + `include_router`, mesmo padrão já usado).
7. No frontend, ler o padrão de chamada a endpoint de IA + exibição de resposta/fonte já usado em
   `Knowledge.tsx`, e o padrão de registro de aba em `main.tsx`. Criar a página nova do agente:
   histórico de mensagens na tela, input de nova mensagem, geração de um `session_id` por sessão de
   aba aberta (ex.: `crypto.randomUUID()`, guardado em estado do componente). Registrar a aba nova
   seguindo exatamente o padrão já existente — não inventar uma estrutura de navegação diferente.
8. Escrever os testes unitários exigidos por `specs/06-agente-conversacional.md §4`: chamada à
   capacidade de RAG mockada com fontes intactas; mensagem informativa sem manual indexado; decisão
   de tool-calling via LLM mockado (uma entrada aciona a tool, outra não); histórico de sessão
   usado na chamada seguinte e respeitando o limite máximo configurado.
9. Rodar a suíte completa do repositório e confirmar verde, sem regressão nos módulos já aprovados.

# 6. Critérios de aceite
- [ ] Existe uma aba própria no frontend, dedicada ao agente conversacional, distinta de
  "Knowledge".
- [ ] O agente responde a uma pergunta sobre manuais citando a fonte (manual + página), sem
  reimplementar nenhuma parte do pipeline de RAG.
- [ ] O agente mantém contexto de sessão: uma segunda mensagem de acompanhamento é respondida
  coerentemente com a primeira (evidência: teste com histórico mockado).
- [ ] Um único LLM decide via function-calling quando chamar a capacidade de RAG — perguntas fora
  do domínio de manuais não acionam a tool indevidamente.
- [ ] Nenhuma capacidade além da consulta a manuais foi implementada (nenhuma leitura de
  telemetria/anomalias/ativos, nenhuma ação sobre o sistema).
- [ ] `backend/shared_infra/llm_client.py` é reusado (nenhum `_build_llm()`/`ChatOpenAI` novo fora
  dele).
- [ ] Histórico de sessão tem limite máximo de mensagens guardadas.
- [ ] Testes unitários da §4 da spec verdes; suíte completa sem regressão.

# 7. Como verificar (uso do revisor)
- `git diff --stat` → só os caminhos de §3.1 (`ai_knowledge/agent/*`, `api/index.py`, a página nova
  do frontend, `main.tsx`); nada em `rag_engine.py`, `vector_store.py`, `pdf_ingestion.py`,
  `ai_knowledge/router.py`, `ai_knowledge/schemas.py`, `llm_client.py`, `llm_models.json`,
  `Knowledge.tsx` ou fora de `ai_knowledge`/frontend.
- Ler o motor do agente e confirmar que a chamada ao LLM passa por `invoke_with_fallback` (grep por
  `ChatOpenAI` fora de `llm_client.py` deve dar zero no novo código).
- Ler o prompt/instrução da tool e confirmar que trata a mensagem do operador como dado, nunca como
  instrução privilegiada.
- Rodar a suíte de testes e ler a saída real, item por item contra os critérios de aceite.
- Ler o novo componente de frontend e confirmar ausência de regra de negócio local (Frontend
  Soberano, `00-contexto.md §7`) — só chamada de API e exibição.

# 8. Destino da síntese
**Destino:** `specs/05-ai-knowledge.md` (ainda não existe — nasce na primeira síntese do domínio
`ai_knowledge`, acumulando os blocos das `plan-04`/`plan-12`/`plan-13` já aprovadas, mais o desta)
· `specs/06-agente-conversacional.md` (marcar critérios de aceite atendidos e status
`🟢 Implementado`, já que ela é a spec de negócio deste próprio agente).

---

# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

## Resumo da execução — 2026-08-22

**Resultado:** Concluído

**O que foi feito**
- Criado o subpacote `backend/apps/ai_knowledge/agent/` (schemas, tool, motor, router) —
  implementa o agente conversacional consumindo `answer_question()` e
  `llm_client.invoke_with_fallback()` já aprovados, sem duplicar nenhuma lógica de RAG ou
  de fallback de modelo.
- `backend/apps/ai_knowledge/agent/schemas.py` — `ChatRequest` (`session_id` e `mensagem`,
  ambos com `max_length`, mitigação de Model DoS pedida por `cyber-ia`) e `ChatResponse`
  (`resposta` + `fontes: List[SourceCitation]`, `SourceCitation` importado de
  `ai_knowledge/schemas.py`, não duplicado).
- `backend/apps/ai_knowledge/agent/tools.py` — tool LangChain `consultar_manuais_tecnicos`
  (`@tool`), com descrição explícita de quando o LLM deve chamá-la (perguntas sobre
  manuais/especificações técnicas) e instrução explícita de que o argumento `pergunta` é
  dado a consultar, nunca uma instrução a seguir; delega inteiramente a
  `rag_engine.answer_question()`, retornando o `AskResponse` completo (fontes preservadas).
- `backend/apps/ai_knowledge/agent/engine.py` — função `chat(session_id, mensagem)`: monta
  o histórico da sessão (dict em memória do processo, `_sessions`), chama
  `llm_client.invoke_with_fallback` com `llm.bind_tools([consultar_manuais_tecnicos])`
  (nunca `ChatOpenAI` direto), decide entre repassar a resposta do RAG (com fontes
  intactas, quando o LLM aciona a tool) ou responder direto (sem fontes). Histórico
  trimado a `MAX_HISTORY_MESSAGES = 10` mensagens por sessão a cada turno
  (`engine.py:16-22`, `engine.py:69-72`). System prompt trata a mensagem do operador como
  dado, nunca como instrução privilegiada, e restringe o agente à única capacidade
  aprovada (Regra 4/7 da spec).
- `backend/apps/ai_knowledge/agent/router.py` — `POST /agent/chat`, validado pelo
  `ChatRequest`, Fail-Fast herdado de `invoke_with_fallback` (`AgentChatError` → HTTP 503).
- `api/index.py:15,40` — montado o novo router (`import` + `include_router`, mesmo padrão
  das rotas já existentes).
- `frontend/src/pages/Agent.tsx` (novo) — página de chat: histórico de mensagens na tela,
  input de nova mensagem, `session_id` gerado uma vez por sessão de aba via
  `crypto.randomUUID()` guardado em estado do componente; só chama `/api/agent/chat` e
  exibe resposta/fontes — nenhuma regra de negócio local (Frontend Soberano, `00-contexto.md
  §7`).
- `frontend/src/main.tsx:26,45` — registrado `registerLocalComponent('agent', Agent)`, mesmo
  padrão das abas existentes.
- `frontend/src/sarak.manifest.json` — adicionado o módulo `agent` (`label: "Agente IA"`,
  categoria "Suporte", ao lado de "knowledge") — é o mecanismo real que a
  `SarakShell`/`registerLocalComponent` usa para exibir a aba; ver "Decisões e suposições".
- Testes novos (skill `test-unitario`), cobrindo a §4 da spec:
  `backend/apps/ai_knowledge/tests/test_agent_tools.py` (tool delega a `answer_question` e
  preserva fontes), `test_agent_engine.py` (aciona a tool e repassa resposta com fontes
  intactas; responde direto sem acionar a tool para pergunta fora do domínio; Fail-Fast sem
  API key; usa e atualiza o histórico da sessão entre chamadas; histórico trimado ao
  limite máximo) e `test_agent_router.py` (200 com fontes, 503 sem LLM, 422 para mensagem
  vazia/maior que o limite).

**Arquivos alterados**
| Arquivo | Natureza | O que mudou |
|---|---|---|
| `backend/apps/ai_knowledge/agent/__init__.py` | criado | marcador de pacote (vazio, mesmo padrão de `vision/__init__.py`) |
| `backend/apps/ai_knowledge/agent/schemas.py` | criado | `ChatRequest`/`ChatResponse` |
| `backend/apps/ai_knowledge/agent/tools.py` | criado | tool `consultar_manuais_tecnicos` (encapsula `answer_question`) |
| `backend/apps/ai_knowledge/agent/engine.py` | criado | motor do agente: tool-calling + memória de sessão |
| `backend/apps/ai_knowledge/agent/router.py` | criado | `POST /agent/chat` |
| `backend/apps/ai_knowledge/tests/test_agent_tools.py` | criado | teste da tool |
| `backend/apps/ai_knowledge/tests/test_agent_engine.py` | criado | testes do motor (5 casos, §4 da spec) |
| `backend/apps/ai_knowledge/tests/test_agent_router.py` | criado | testes do endpoint HTTP |
| `frontend/src/pages/Agent.tsx` | criado | página/aba de chat do agente |
| `api/index.py` | alterado | +2 linhas: import + `include_router` do novo router |
| `frontend/src/main.tsx` | alterado | +2 linhas: import + `registerLocalComponent('agent', Agent)` |
| `frontend/src/sarak.manifest.json` | alterado | +7 linhas: novo módulo `agent` na lista de abas |

**Verificações executadas**
- `python -m pytest backend/apps/ai_knowledge/tests/test_agent_engine.py
  backend/apps/ai_knowledge/tests/test_agent_router.py
  backend/apps/ai_knowledge/tests/test_agent_tools.py -v` → 10 passed.
- `python -m pytest backend/ -v` (suíte completa do backend) → **64 passed**, 0 falhas, 0
  regressão nos módulos já aprovados (rag_engine, ai_enrichment, plate_llm_structurer,
  vision, persistence_handler, ingestion_service, llm_client).
- `grep -rn "ChatOpenAI" backend/apps/ai_knowledge/agent/` → nenhum resultado (LLM só via
  `invoke_with_fallback`).
- `grep -rn "TODO\|print(\|console.log\|debugger" backend/apps/ai_knowledge/agent/
  frontend/src/pages/Agent.tsx` → nenhum resultado.
- `npx tsc -p tsconfig.json --noEmit` → **não executável**: não existe `tsconfig.json` no
  projeto (confirmado por `Glob **/tsconfig*.json`, só há `tsconfig.json` dentro de
  `node_modules`), condição pré-existente e fora do escopo desta plan — ver "Achados fora
  do escopo".
- `npx vite build` (bundling via esbuild, sem checagem de tipos) → build concluído sem
  erros, `Agent.tsx` e o registro em `main.tsx`/`sarak.manifest.json` transformados sem
  falha (4708 módulos). `dist/` gerado só para esta verificação foi removido em seguida —
  não faz parte da entrega.
- `git status`/`git diff --stat` → conferido: só os arquivos listados na tabela acima
  entraram como novos/alterados por esta execução (arquivos já modificados/não-rastreados
  no início da conversa — `rag_engine.py`, `ai_enrichment.py`, `plate_llm_structurer.py`,
  `config.py`, `.env.example`, `llm_client.py`, `llm_models.json`,
  `specs/00-contexto.md`, `specs/00-indice.md`, `specs/06-agente-conversacional.md`,
  `specs/plan/executadas/plan-13-llm-fallback-config.md` — são da `plan-13`, pré-existentes
  ao início desta execução, não tocados por mim).

**Critérios de aceite**
- [x] Existe uma aba própria no frontend, dedicada ao agente conversacional, distinta de
  "Knowledge" — evidência: `frontend/src/pages/Agent.tsx` + registro em
  `frontend/src/main.tsx:26,45` e `frontend/src/sarak.manifest.json` (módulo `agent`).
- [x] O agente responde a uma pergunta sobre manuais citando a fonte (manual + página), sem
  reimplementar nenhuma parte do pipeline de RAG — evidência:
  `backend/apps/ai_knowledge/agent/tools.py` chama só `rag_engine.answer_question()`;
  `test_agent_engine.py::test_chat_calls_rag_tool_and_repasses_answer_with_sources_intact`.
- [x] O agente mantém contexto de sessão — evidência:
  `test_agent_engine.py::test_chat_uses_and_updates_session_history_across_calls` (histórico
  mockado, segunda chamada usa mensagens da primeira).
- [x] Um único LLM decide via function-calling quando chamar a capacidade de RAG —
  evidência: `engine.py` usa `llm.bind_tools([consultar_manuais_tecnicos])` e ramifica por
  `ai_message.tool_calls`;
  `test_agent_engine.py::test_chat_responds_directly_without_calling_tool_for_off_domain_question`.
- [x] Nenhuma capacidade além da consulta a manuais foi implementada — evidência: única tool
  registrada em `engine.py` é `consultar_manuais_tecnicos`; nenhum acesso a
  telemetria/anomalias/ativos em `agent/*`.
- [x] `backend/shared_infra/llm_client.py` é reusado (nenhum `_build_llm()`/`ChatOpenAI`
  novo fora dele) — evidência: grep acima, zero ocorrências em `agent/*`.
- [x] Histórico de sessão tem limite máximo de mensagens guardadas — evidência:
  `engine.py:16-22` (`MAX_HISTORY_MESSAGES = 10`), `engine.py:33` (`_trim_history`);
  `test_agent_engine.py::test_chat_trims_session_history_to_max_messages`.
- [x] Testes unitários da §4 da spec verdes; suíte completa sem regressão — evidência: 10
  testes novos + 64/64 da suíte completa.

**Decisões e suposições**
- A plan cita só `frontend/src/main.tsx` como "onde as abas são registradas" — ao ler o
  padrão de "knowledge"/"simulator", confirmei que a aba só aparece de fato na
  `SarakShell` porque também está listada em `frontend/src/sarak.manifest.json` (campo
  `modules`, lido por `SarakUIProvider`/`discovery.mode: 'local'`). Editei também esse
  arquivo (+7 linhas, novo módulo `agent`) — sem essa entrada, `registerLocalComponent`
  sozinho não bastaria para expor a aba na UI. Interpretação conservadora do escopo §3.1
  ("ou onde quer que as abas sejam registradas hoje"), não uma mudança de arquitetura.
- Ao acionar a tool, o agente **repassa a resposta do RAG tal como veio** (`AskResponse.
  resposta` + `fontes`), sem uma segunda chamada ao LLM para "reformular" o texto. Decisão
  para atender literalmente a Regra 3 ("nunca resumir de um jeito que perca a
  rastreabilidade da fonte") e o teste da §4 ("repassar a resposta... com fontes
  intactas") — uma reformulação por um segundo LLM arriscaria parafrasear a citação ou
  invocar custo/latência extra sem exigência explícita da spec.
- A tool `consultar_manuais_tecnicos` é invocada via `tool.invoke(tool_call["args"])`
  diretamente (não através de um `ToolNode`/`AgentExecutor` genérico), o que permite
  devolver o `AskResponse` estruturado (com `fontes` tipadas) em vez de só uma string —
  confirmado experimentalmente que `BaseTool.invoke()` devolve o retorno bruto da função
  quando chamado assim (fora de um grafo de execução), sem precisar duplicar a chamada a
  `answer_question()`.
- Histórico de sessão trimado por **contagem de mensagens** (10 = humano+assistente
  intercalados), não por "turnos" — leitura literal do texto da spec ("as últimas 10
  mensagens").
- Não instalei nem gerei um `tsconfig.json` para rodar `tsc` — a ausência do arquivo é uma
  condição pré-existente do repositório, fora do escopo desta plan (não listada em §3.1);
  registrado como achado fora do escopo abaixo.

**Achados fora do escopo (não corrigidos)**
- `frontend/package.json:"build"` roda `tsc && vite build`, mas o projeto não tem nenhum
  `tsconfig.json` na raiz do `frontend/` (confirmado por `Glob **/tsconfig*.json` — só
  existem `tsconfig.json` dentro de `node_modules`) — `npm run build` falharia hoje já no
  primeiro comando, independente desta plan. `npx vite build` (sem `tsc`) funciona e
  confirma que o bundle novo (`Agent.tsx` + registro de aba) não tem erro de sintaxe/import,
  mas nenhuma checagem de tipos roda no projeto. Sugestão: plan própria para adicionar
  `tsconfig.json` compatível com o Vite+React já configurado.

**Pendências / riscos**
- Nenhum teste E2E real (com chave OpenRouter de verdade) foi executado — só testes
  unitários com LLM mockado, conforme pedido pela §4 da spec ("Testes Unitários"); a §4
  também lista um teste E2E de fluxo feliz (usuário pergunta → resposta com fonte →
  pergunta de acompanhamento), que não foi automatizado nesta plan (não fazia parte do
  escopo `test-unitario` pedido nas instruções de execução, e a spec não define ferramenta
  de E2E para este caso). Fica como verificação manual/futura, se o revisor considerar
  necessária.
- Sessão em memória do processo: reinício do backend limpa todo o histórico de conversa em
  andamento — comportamento esperado e aceito pela spec (Regra 6), não uma regressão.

---

# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->

## Veredito — 2026-08-22 — 🟢 Aprovado

**Verificado diretamente no worktree** (o resumo do executor foi conferido, não tomado como evidência):

- `git status`/`git diff --stat` → exatamente o alegado: `api/index.py` (+2), `frontend/src/main.tsx`
  (+2), `frontend/src/sarak.manifest.json` (+7), mais o subpacote novo `ai_knowledge/agent/`
  (`schemas.py`, `tools.py`, `engine.py`, `router.py`, `__init__.py`), 3 arquivos de teste novos e
  `frontend/src/pages/Agent.tsx`. Nada em `rag_engine.py`, `vector_store.py`, `pdf_ingestion.py`,
  `ai_knowledge/router.py`, `ai_knowledge/schemas.py`, `llm_client.py`, `llm_models.json` ou
  `Knowledge.tsx` — os arquivos que já apareciam modificados no início desta conversa (`rag_engine.py`,
  `ai_enrichment.py`, `plate_llm_structurer.py`, `config.py`, `.env.example`, `specs/00-contexto.md`
  etc.) são da `plan-13`, já aprovada antes desta execução começar — confirmado que não ganharam diff
  adicional nesta rodada.
- Li os 4 arquivos novos do backend por completo (`schemas.py`, `tools.py`, `engine.py`, `router.py`):
  `consultar_manuais_tecnicos` delega inteiramente a `rag_engine.answer_question()`, sem reimplementar
  nada; `chat()` nunca monta `ChatOpenAI` diretamente, só chama `llm_client.invoke_with_fallback`
  passando um `_run(llm)` que faz `llm.bind_tools([...]).invoke(messages)`; decide entre repassar o
  `AskResponse` da tool (fontes intactas) ou o texto direto do LLM; histórico trimado para
  `MAX_HISTORY_MESSAGES = 10` a cada turno (`_trim_history`); `_SYSTEM_PROMPT` trata a mensagem do
  operador como conteúdo a interpretar, nunca como instrução para mudar papel/revelar prompt/ignorar
  regras — mitigação de prompt injection pedida por `cyber-ia`, mais explícita até do que o mínimo
  exigido pela plan. `ChatRequest`/mensagem com `max_length` (mitigação de Model DoS).
- Rodei a suíte eu mesmo: `python -m pytest backend/ -q` → **64 passed**, bate exatamente com o
  alegado; `python -m pytest backend api/tests -q` → **68 passed** (suíte completa do repositório,
  incluindo `api/tests`), sem falha.
- `grep -rn "ChatOpenAI" backend/apps/ai_knowledge/agent/` → **zero ocorrências**, confirma "helper
  compartilhado reusado, nenhum `_build_llm()` novo".
- `grep -rnE "TODO|FIXME|print\(|console\.log|debugger"` no subpacote novo e em `Agent.tsx` → **zero
  ocorrências**.
- Li os 3 arquivos de teste linha a linha contra o código real: `test_agent_tools.py` confirma que
  `consultar_manuais_tecnicos.invoke()` devolve o `AskResponse` bruto (fontes tipadas intactas) —
  validei a alegação do executor sobre o comportamento do `BaseTool.invoke()` rodando o teste de
  verdade, não só lendo a explicação; `test_agent_engine.py` cobre os 5 cenários que a §4 da spec e os
  critérios de aceite exigem (tool acionada com fontes, resposta direta sem tool para pergunta fora do
  domínio, Fail-Fast sem chave, histórico usado entre chamadas, histórico trimado ao limite);
  `test_agent_router.py` cobre 200/503/422×2 via `TestClient` real contra a rota.
- Li `frontend/src/pages/Agent.tsx` por completo: só chama `POST /api/agent/chat` e renderiza
  `resposta`/`fontes` — nenhuma regra de negócio local, nenhum limiar, nenhuma decisão sobre dado de
  motor (Frontend Soberano, `00-contexto.md §7`). `session_id` gerado uma vez por sessão de aba via
  `crypto.randomUUID()`, guardado em estado do componente.
- Li o diff de `main.tsx`/`sarak.manifest.json`: `registerLocalComponent('agent', Agent)` + entrada
  `{id: "agent", label: "Agente IA", category: "Suporte"}` seguem exatamente o padrão das abas vizinhas
  (`knowledge`, `vision`) — nenhuma estrutura nova inventada.
- Rodei `npx vite build` eu mesmo (dentro de `frontend/`): **build concluído sem erro**, 4708 módulos
  transformados — bate com o alegado. `frontend/dist/` está no `.gitignore` (`.gitignore:33`), não
  preciso limpar manualmente.

**Sobre a suposição de editar `sarak.manifest.json`** (fora da lista literal do §3.1): correta e
necessária — confirmei por leitura que `registerLocalComponent` sozinho não expõe a aba sem a entrada
correspondente no manifest; mesma categoria de decisão de "companion necessário" já aceita em plans
anteriores (`.gitignore`/`.env.example` na `plan-01`, `api/index.py` em várias). Não é achado.

**Critérios de aceite — 8 de 8 atendidos, com evidência real (minha, além da do executor):**
- [x] Aba própria, distinta de "Knowledge".
- [x] Responde citando fonte, sem reimplementar RAG.
- [x] Mantém contexto de sessão.
- [x] LLM único decide via function-calling.
- [x] Nenhuma capacidade além de RAG.
- [x] `llm_client` reusado, zero `ChatOpenAI` fora dele.
- [x] Histórico com limite máximo de mensagens.
- [x] Testes da §4 verdes; suíte completa sem regressão.

**Achado fora do escopo, registrado, correto (não corrigido agora):** ausência de `tsconfig.json` no
frontend (já conhecida desde a `plan-02`, não desta plan) — `npm run build` segue quebrado por esse
motivo pré-existente; `npx vite build` prova que o bundle desta plan em si não tem erro.

**Observação minha, sem peso no veredito:** `engine.py` só considera `ai_message.tool_calls[0]`
quando o LLM devolve múltiplas chamadas de tool no mesmo turno — com uma única tool registrada isso
não é um cenário real hoje, mas fica registrado para se um dia houver mais de uma capacidade.

**Liberação:** nenhuma plan da fila depende de `plan-14`.
