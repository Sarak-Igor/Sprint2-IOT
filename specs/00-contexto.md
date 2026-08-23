---
tipo: "processo"
titulo: "Contexto do Repositório — Briefing de Entrada"
dominio: "Governança de Specs (SDD)"
status: "🟢 Vigente"
tags: ["processo", "contexto", "sdd"]
relacionados: ["[[00-knowledge]]", "[[00-indice]]", "[[00-prompt-revisor]]", "[[00-prompt-executor]]"]
---

# 0. O que é este arquivo

Esta é a **porta de entrada de qualquer agente** neste repositório. Um agente que leu esta spec — e só ela —
deve saber: **o que** o repositório é, **quais regras** governam qualquer alteração, **onde** está cada
informação e **como** se trabalha aqui.

> ⚠️ **Este arquivo é um molde com instruções embutidas.** Ele chega ao repositório **vazio de conteúdo
> específico**: cada seção traz um bloco `> **Como escrever:**` (a instrução, que **permanece** no arquivo como
> contrato de manutenção) e um bloco `<!-- PREENCHER -->` (o conteúdo real, que o **agente revisor** escreve).
> Preencher esta spec é a **primeira** plan de qualquer repositório novo.

**Quem escreve/atualiza:** exclusivamente o **agente revisor** ([[00-prompt-revisor]]).
**Quando atualizar:** sempre que uma plan aprovada mudar stack, arquitetura, fronteiras de módulo, regra
inegociável ou o mapa de roteamento. Nunca por conta própria fora de uma plan.

---

# 1. Identidade do repositório

> **Como escrever:** 3 a 6 linhas, em prosa direta. Responda: **o que este repositório é** (produto? base de
> conhecimento? biblioteca? site?), **qual problema resolve**, **quem consome** (usuário final, outros repos,
> agentes) e **o que ele explicitamente NÃO é**. Sem marketing, sem histórico. Um agente lê isto e para de
> supor. Proibido descrever a estrutura de pastas aqui — isso é da §3.

O repositório **Forzy | Industrial Intelligence** é o ecossistema de software de um Gêmeo Digital (Digital Twin) e monitoramento preditivo para motores elétricos industriais (Challenge FIAP). Ele consome dados de hardware na ponta (IoT Firmware no ESP32), processa-os e exibe tudo numa interface de altíssima fidelidade voltada para operadores e gestores de manutenção. **Não é um simples dashboard monolítico**, mas uma arquitetura baseada em eventos (EDA) que abstrai rigorosamente as especificações de hardware através de perfis JSON carregados em tempo de execução.

---

# 2. Regras inegociáveis (resumo operante)

> **Como escrever:** liste **apenas** as regras que um agente pode violar sem perceber, em forma de bullets
> curtos e verificáveis. Duas fontes, nesta ordem:
> 1. **Universais do ecossistema** — não reescreva: aponte para `CLAUDE.md` (raiz) e para a skill
>    `padrao-escrita`. Cite no máximo os limiares que causam reprovação imediata (SRP; função ≤ 40 linhas;
>    aninhamento ≤ 3; ≤ 4 parâmetros; zero hardcoded; segredos só em `.env`; nenhuma exceção engolida).
> 1b. **Arquitetura de módulos** — se este projeto adota o template, **não descreva a anatomia**: aponte para
>    `arquitetura/04-regras.md` e diga a única coisa que o agente precisa saber sem abrir o arquivo — que ela
>    é cobrada por máquina, com `node tools/gate/validate.mjs`.
> 2. **Específicas deste repositório** — o que só vale aqui (convenções de nomes locais, uma biblioteca
>    proibida, um diretório que não se toca, um formato de retorno obrigatório).
>
> **Regra de ouro: referencie, nunca duplique.** Se uma regra já está numa spec fixa ou numa skill, escreva
> uma linha e o ponteiro. Conteúdo duplicado desatualiza e passa a mentir.

- **Universais do ecossistema:** Aja guiado pelo `CLAUDE.md` raiz (limiares curtos, responsabilidade única, segredos nunca expostos, etc).
- **Soberania do Frontend e UI Core:** A interface delega sua renderização principal à biblioteca `@sarak/lib-ui-core`. NUNCA recrie ou altere componentes puramente visuais da base no repositório. Toda atualização do design system vem de bump no GitHub Hash no `package.json`.
- **Zero-Hardcode Industrial:** Nenhuma métrica ou característica do motor (RPM nominal, tolerância a vibração, eficiência) pode estar hardcoded nos arquivos `.py` ou `.ts`. Obtenha esses dados estritamente via `settings.specs` derivados dos JSONs em `backend/device_profiles/`.
- **Fail-Fast de Configurações:** Dependências externas (Broker, DB) são injetadas exclusivamente através do Pydantic (`backend/shared_infra/config.py`). Nada é inferido ocultamente.

---

# 3. Stack e arquitetura em uma página

> **Como escrever:** o mínimo para orientar, com ponteiro para o detalhe. Inclua:
> - **Stack**: linguagens + versões, frameworks, banco, runtime, gerenciador de pacotes.
> - **Camada de padrão da linguagem**: qual skill `padrao-*` se aplica (`padrao-python`, `padrao-typescript`).
>   Outra linguagem não tem camada de Nível 2, mas pode ter automação de limiar: o hook `padrao-limiares`
>   cobre `.go` e `.java` além de `.py` e `.ts`/`.js`. Registre qual dos dois cobre a stack — e, se nenhum
>   cobrir, que ali vale o Nível 0 do `padrao-escrita` conferido por leitura.
> - **Mapa de módulos/domínios**: tabela `módulo → papel → responsabilidade`. Projeto com o template de
>   módulos: os papéis são `domain` / `gateway` / `connector` (a forma do `module.json` de cada um, campo
>   `role`) — não transcreva, aponte.
> - **Fronteiras**: quem pode chamar quem, e por onde. No template, a resposta é sempre a mesma — pelo
>   **contrato HTTP** da `api/` do dono, declarado em `module.json:consumes`.
> - **Comandos vitais**: instalar, rodar, testar, lintar, buildar — copiáveis, verificados.
>
> Cada item aponta para a spec fixa em `arquitetura/` que o detalha. Esta seção é o índice, não o tratado.

- **Stack e Padrão (`padrao-python` / `padrao-typescript`):**
  - Backend: Python 3.10+ (FastAPI, SQLAlchemy Async, LangChain).
  - Frontend: React 18+ com TypeScript e Vite. ECharts para BI. TailwindCSS.
  - Dados: NeonDB PostgreSQL, Mosquitto MQTT, OPC UA.
- **Mapa de Domínios:**
  - `backend/apps/ingestion_service` (Gateway): Porta de entrada crua de dados MQTT/OPC UA para a plataforma.
  - `backend/apps/digital_twin_core` (Domain): Processa anomalias em tempo real e orquestra acesso a dados.
  - `backend/apps/ai_knowledge` (Domain): Motor RAG.
  - `backend/apps/asset_manager` (Domain): Gestão dos ativos físicos.
  - `frontend` (Connector): UI Soberana que agrega as respostas dos backends em dashboards visuais.
  - `iot_firmware` (Edge): Código microcontrolador que interage via hardware. Já contém esqueleto PlatformIO
    (`platformio.ini`, `include/config.h`, `src/main.cpp`) — não parte do zero.
  - `api/index.py` (Gateway HTTP real, fora de `backend/apps/`): função serverless (formato Vercel) na raiz do
    repo. É quem de fato atende `/api/*` consumido pelo frontend (assets, telemetry, config, alertas
    Telegram, manuais, WebSocket) — monta o router do `asset_manager` e implementa rotas adicionais direto
    nela. Nenhuma spec fixa descrevia este arquivo até 2026-08-22; ver §8.
- **Fronteiras:** O frontend é passivo e nunca assume regras de negócio das máquinas (delega ao backend). Integrações entre as partes do backend acontecem através de importações isoladas, porém todas buscam o `shared_infra` para configs.
- **Comandos vitais:**
  - **Subir ecossistema em Windows:** `.\RUN_FORZY.bat`
  - **Subir infra Docker (MQTT, etc):** `docker-compose up -d`
  - **Rodar Frontend Isolado:** `cd frontend && npm install && npm run dev`

---

# 4. Mapa de roteamento — "que spec eu leio para esta tarefa?"

> **Como escrever:** esta é a seção **mais valiosa** do arquivo e a razão de ele existir. Uma tabela que
> responde à pergunta que todo agente faz ao receber uma tarefa. Uma linha por tipo de tarefa recorrente
> no repositório, com caminhos **relativos a `specs/`** e clicáveis.
>
> Preencha a coluna "Leia antes" com **specs fixas** (`arquitetura/`, `specs/`, `adr/`) — para skills e
> commands, aponte para [[00-knowledge]], que é o roteador de capacidades.
>
> | Tipo de tarefa | Leia antes (specs fixas) | Capacidade |
> |---|---|---|
> | Alterar regra de negócio de \<módulo\> | `specs/NN-<modulo>.md` | [[00-knowledge]] |
> | Criar/alterar endpoint | `arquitetura/NN-api.md` + spec do módulo | [[00-knowledge]] |
> | Mexer em schema/migration | `arquitetura/NN-dados.md` + ADR relevante | [[00-knowledge]] |
> | Mudar decisão estrutural | todos os `adr/` + `arquitetura/` | [[00-knowledge]] |
>
> Mantenha entre 6 e 15 linhas. Se passar disso, o repositório precisa de specs melhores, não de mais linhas
> aqui. **Ponteiro órfão é defeito**: toda spec citada tem de existir.

| Tipo de tarefa | Leia antes (specs fixas) | Capacidade |
|---|---|---|
| Mudar interface/páginas web do Forzy | `adr/001-stack-principal.md` | [[00-knowledge]] |
| Alterar métricas base, limiares ou processamento do Twin | `adr/001-stack-principal.md` | [[00-knowledge]] |
| Ajustar perfis técnicos / especificações de motor (hardware) | (Diretório físico: `backend/device_profiles/`) | [[00-knowledge]] |
| Adicionar entidades de Banco ou Repositórios SQLAlchemy | `adr/002-banco-de-dados.md` | [[00-knowledge]] |
| Integrar novo serviço MQTT / IoT | `adr/005-integracoes-iniciais.md` | [[00-knowledge]] |
| Planejar/implementar o agente conversacional de IA | `06-agente-conversacional.md` | [[00-knowledge]] |
| Pivotar decisões globais da arquitetura | `arquitetura/00-fundacao-tecnologica.md` | [[00-knowledge]] |

---

# 5. Como se trabalha aqui (ciclo SDD)

> **Como escrever:** esta seção é **universal — copie o bloco abaixo como está**. Só acrescente desvios reais
> deste repositório (por exemplo: "toda plan que toca `pagamentos/` exige ADR"). Não reescreva o ciclo.

**Toda e qualquer alteração passa por uma spec.** Nada é alterado "direto no código".

```
revisor escreve  specs/plan/plan-NN-<slug>.md
      ↓
executor lê  00-prompt-executor  +  plan-NN  e executa
      ↓
alterações ficam no worktree (nenhum agente commita)
      ↓
revisor VERIFICA diretamente (não confia no resumo do executor)
      ├─ reprovado → prompt de correção → executor corrige → repete
      └─ aprovado  → status 🟢 + plan movida para plan/executadas/ + [[00-indice]] atualizado
      ↓
usuário commita
      ↓
periodicamente: spec-atualizar sintetiza as plans 🟢 de plan/executadas/ nas specs
fixas (adr/ · arquitetura/ · specs/) e REMOVE a plan (arquivo + linha do índice) —
a spec fixa passa a ser a única fonte viva dessa verdade
```

**`specs/plan/`** é a fila **ativa**; **`specs/plan/executadas/`** é a fila de **espera de síntese** — só
`🟢 Aprovada`, esvaziada a cada rodada de `spec-atualizar`.

| Papel | Spec de entrada | Pode escrever | Nunca faz |
|---|---|---|---|
| **Revisor** | [[00-prompt-revisor]] | specs, prompts, mensagens | tocar código · commitar |
| **Executor** | [[00-prompt-executor]] | código + resumo na própria plan | criar/alterar outras specs · commitar |
| **Usuário** | — | qualquer coisa | — (é quem commita e dispara `/spec-atualizar`) |

- **Desvio Arquitetural Sarak:** Embora utilize o ciclo SDD rigoroso e as specs base, este repositório não adotou a divisão de pacotes por `packages/` ou `adapters/` via CLI. Ele possui backend e frontend estruturados na raiz. Respeite esta divisão existente.

---

# 6. Capacidades disponíveis

> **Como escrever:** seção **universal — não a preencha com conteúdo**. Apenas mantenha o ponteiro. As
> skills, commands, agents e hooks **não vivem neste repositório**: vêm da memória/plugin do agente. O
> catálogo e as regras de roteamento estão em [[00-knowledge]].

Antes de escolher **como** fazer algo, leia **[[00-knowledge]]** — é o roteador de capacidades
(situação → skill/command/agent/hook) e o único lugar onde esse catálogo é mantido.

---

# 7. Fronteiras — o que nunca fazer neste repositório

> **Como escrever:** bullets no imperativo negativo, cada um com o **porquê** em meia linha. Só o que é
> específico deste repositório (as proibições de papel já estão na §5 e nas specs de prompt). Exemplos do
> tipo de item: diretórios gerados que não se editam à mão; arquivos que só o usuário altera; operações
> irreversíveis que exigem confirmação; integrações que não podem ser chamadas em desenvolvimento.

- **Nunca altere a lib UI externa diretamente no código fonte do projeto:** O sistema é agnóstico em UI, buscando de `@sarak/lib-ui-core` no github. Faça a correção no repo da UI e depois de bump aqui.
- **Nunca coloque senhas e tokens da NeonDB ou Cloudflare no código em formato string literal:** A segurança depende de que o Pydantic puxe de `os.getenv` exclusivamente pelo `.env`.
- **Nunca insira regras de validação ou inferência baseada no nome do "Motor" dentro da UI:** O frontend não deve "saber" sobre os detalhes físicos da máquina, apenas desenhar o que o Gateway lhe der.

---

# 8. Estado e pendências conhecidas

> **Como escrever:** o que um agente descobriria do jeito difícil. Dívidas técnicas aceitas, áreas em
> migração, incoerências conhecidas entre código e spec, decisões em aberto. **Datas sempre absolutas**
> (`2026-07-31`, nunca "semana passada"). Item resolvido sai daqui — esta seção não é histórico; o histórico
> é o `git` e os `adr/`.

- **2026-08-17:** A funcionalidade de login/autenticação está bloqueada/postergada (`adr/003-autenticacao.md`).
  Não tente implementar middleware JWT — decisão fechada, sem plan associada, não revisitar sem pedido explícito.
- **2026-08-17:** Não existe CI/CD ou pipeline de deploy na nuvem ativo (`adr/004-infra-deploy.md`), o projeto
  roda majoritariamente via script local e `docker-compose`. Decisão fechada, sem plan associada.
- **2026-08-22:** `digital_twin_core/persistence_handler.py` (não `main.py`) é o processo real que ouve MQTT e
  grava anomalias; o gateway HTTP consumido pelo frontend é `api/index.py` + `asset_manager`. Corrigido em
  `arquitetura/02-backend-eda.md` e `specs/01-digital-twin-core.md`. `persistence_handler.py` é o núcleo do
  sistema (confirmado com o usuário) — a origem dos dados (mock hoje, Wokwi/PlatformIO depois) é só a camada
  de adaptador.
- **2026-08-22:** `docs/PLANEJAMENTO.md` (fora de `specs/`) propunha migrar o consumo MQTT→Postgres para
  Node-RED — **decisão fechada com o usuário: descartada**. O fluxo permanece em Python; só a camada de
  **produção** de dados muda (mock → Wokwi/PlatformIO/ESP32), via `plan-01`. `docs/PLANEJAMENTO.md` ficou
  desatualizado nos itens 1-2; não editado por mim (fora de `specs/`, fora da minha autoridade direta).
- **2026-08-22:** `/vision/stats` (endpoint de `digital_twin_core/main.py`) está confirmado por grep como não
  chamado em nenhum lugar do frontend — a antiga pendência de "aguardar hardware de câmera" para esse endpoint
  específico não se aplica mais; ele é código órfão coberto pela remoção da `plan-05`, não por uma feature a
  construir. A visão computacional de verdade (leitura de placa por foto) é escopo da `plan-03`.
- **2026-08-22:** `plan-03` (Visão Computacional) pivotou de LLM multimodal (OpenRouter) para
  **OCR 100% local** (`easyocr`/`opencv-python-headless`, já declarados em `requirements.txt` sob
  "Preparação Sprint 2", nunca usados até então) — decisão do usuário, mesma linha da `plan-04`
  (projeto roda local por padrão). Aprovada com verificação real (executor e revisor, cada um com
  imagem sintética própria, EasyOCR de verdade). Limitação conhecida, aceita como débito de baixo
  risco: quando dois campos da placa caem na mesma linha detectada pelo OCR, `plate_parser.py`
  atribui o texto ao primeiro campo da ordem de prioridade e deixa o outro como "Não legível" —
  nunca inventa valor, só perde recall. Só uma foto real de placa revela se isso é comum na
  prática; não vira plan a menos que se confirme como problema real de uso.
- **2026-08-22:** Verificação real (revisor, com chave de teste do usuário) confirmou 2 de 3
  chamadas de LLM funcionando de ponta a ponta (`ai_enrichment` da `plan-02`, `rag_engine` da
  `plan-04`). A terceira (`plate_llm_structurer` da `plan-12`) falhou com o modelo gratuito de
  raciocínio testado (`nvidia/nemotron-3-ultra-550b-a55b:free`) — estourou o teto de tokens de
  saída "pensando" antes de responder; o fallback automático para regex (já aprovado) funcionou
  como projetado, sem quebrar a feature. Decisão do usuário: `plan-13` move a escolha de modelo
  de `OPENROUTER_MODEL`/`.env` para um arquivo de config JSON versionado, com lista de fallback
  entre modelos — resolve a causa raiz, não só o sintoma.
- **2026-08-22:** Resolvido — `plan-13` implementou `backend/shared_infra/llm_client.py`
  (`invoke_with_fallback`, Fail-Fast de config, tentativa em ordem pela lista de
  `backend/shared_infra/llm_models.json`) e migrou os três módulos duplicados
  (`ai_enrichment`, `plate_llm_structurer`, `rag_engine`). **Confirmado com chamada real, sem
  mock, contra a lista de produção**: o modelo primário (`openai/gpt-5.6-luna`) falhou por
  falta de crédito, o helper avançou automaticamente e um modelo gratuito da lista completou
  com sucesso — prova de que o problema real desta sessão (modelo de raciocínio estourando
  teto de tokens) tem correção estrutural, não só coberta por teste mockado. **Correção de
  registro:** o resumo da execução alegou (erroneamente) que `openai/gpt-4o-mini` e
  `openrouter/free` não existem mais no catálogo do OpenRouter — o revisor consultou a API
  pública e confirmou que **os dois existem**. `openrouter/free` foi testado de verdade contra
  `with_structured_output` e falhou (devolve texto livre, não JSON) — por isso, apesar de
  existir, não é escolha funcional para os módulos que exigem saída estruturada; a lista final
  de modelos da `plan-13` permanece correta, só a justificativa registrada estava errada.
- **2026-08-22:** Confirmado com foto real de placa (não só imagem sintética): confiança baixa e
  campos errados/"Não legível" em excesso — a fragilidade do regex de `plate_parser.py` contra
  ruído real de OCR (não só o overlap já registrado acima) é o gargalo principal. Decisão do
  usuário: caminho híbrido — `plan-12` troca a estruturação por regex por um LLM de **texto**
  (nunca a imagem) via OpenRouter, tolerante a ruído, mantendo `ocr_engine.py` (EasyOCR) intocado
  e sem custo de tokens de imagem. Pré-processamento de imagem (CLAHE, correção de perspectiva)
  foi avaliado e **não escolhido** nesta rodada — fica como opção não explorada se o híbrido não
  for suficiente.
- **2026-08-22:** Apesar de `adr/005-integracoes-iniciais.md` aceitar Cloudflare R2 e de já existir
  `backend/shared_infra/storage_client.py` (usado hoje só pelo endpoint mockado `GET /api/manuals`, com
  credenciais reais já presentes no `.env`), **decisão explícita do usuário: o projeto roda majoritariamente
  local e novas features não devem depender de rede externa por padrão**. A `plan-04` (RAG/Knowledge Base) foi
  corrigida para armazenar manuais e vetor-store 100% em disco local, não via R2. Não decidir sozinho por R2
  em nenhuma plan nova sem pedido explícito — perguntar antes.

- **2026-08-23:** Confirmado com manual real ("WEG W22 Easy Maintenance Motofreio", indexado pelo
  usuário via `plan-15`): a qualidade de resposta do RAG (e por extensão do agente conversacional,
  `plan-14`) caía para perguntas técnicas específicas, enquanto um agente externo lendo o mesmo PDF
  achava a informação sem dificuldade. Diagnóstico direto na base real (revisor): o manual tem só 6
  chunks indexados; `query_similar_chunks()` usa `n_results=4` fixo, e o embedding local padrão do
  ChromaDB não rankeou o chunk mais denso em dados (tabela de torque/tensão/rotação/energia) acima
  de um parágrafo de marketing — o trecho com a resposta simplesmente não entrava no contexto do
  LLM. Não é bug de extração nem de geração — o dado estava corretamente indexado; é recuperação
  (quantos trechos entram no top-N) que falhava para bases pequenas. `plan-16` corrige de forma
  adaptativa (base pequena → recupera tudo; base grande → mantém o teto). Melhoria de chunking
  consciente de tabela foi avaliada e **não escolhida** nesta rodada — decisão do usuário, fica como
  opção não explorada se o ajuste de recuperação não for suficiente.

## Pendências cobertas pela fila ativa (ver `00-indice.md` para status corrente)
- Código órfão em `digital_twin_core` (`main.py`, `anomaly_logger.py`, `converters/metric_converter.py`) e o
  listener MQTT duplicado em `api/index.py:282-358` → `plan-05`.
- `ai_knowledge` sem nenhum código-fonte (RAG/OCR 100% a implementar) → `plan-04`.
- Botões de UI sem handler ("Marcar como Lido"/filtro em `Anomalies.tsx`, "Novo Item" em `Catalogs.tsx`,
  "Filtros"/"Exportar CSV" em `History.tsx`, `Telemetry.tsx` 100% estático) → `plan-08`, `plan-09`, `plan-10`,
  `plan-07`, respectivamente.
- Alerta Telegram disparado só quando o Dashboard está aberto no navegador (viola Frontend Soberano, §7) →
  `plan-06`.
- `specs/specs/02-notificacao-telegram.md` corrigida (sem Node-RED) e `specs/specs/03-migracao-simulador-esp32.md`
  absorvida por `plan-01` — sem sobreposição remanescente.

## Fechado — aceito como está, sem plan (2026-08-22)
- **`frontend/src/pages/simulator/FlowSimulator.tsx`** (10ª aba, registrada como `simulator` em `main.tsx`,
  não coberta pelo diagnóstico inicial): diagrama de arquitetura animado já funcional, consome `/api/config` e
  `/api/ws/telemetry` de verdade. Tem uma comparação de threshold hardcoded (`:61-64`, valores `90`/`75`) só
  para decidir qual nó do diagrama acende — mesma família do achado corrigido pela `plan-06` em
  `Dashboard.tsx`, mas sem side-effect de rede (não dispara nada, é puramente cosmético). **Decisão: aceito
  como débito técnico de baixo risco, não entra em plan.** Reabrir só sob pedido explícito.
- **2026-08-22:** Confirmado por grep: `/vision/stats` (endpoint órfão de `digital_twin_core/main.py`,
  candidato a remoção pela `plan-05`) **não é chamado em nenhum lugar do frontend** — a pendência de
  2026-08-17 sobre esse endpoint aguardar hardware de câmera fica sem efeito prático assim que a `plan-05` for
  executada.

---

# 9. Contrato de manutenção desta spec

- **Alvo de tamanho:** ≤ 200 linhas preenchidas. Estourou? O conteúdo pertence a uma spec fixa — mova e aponte.
- **Referencie, nunca duplique.** Esta spec é um **mapa**, não território.
- **Ponteiro órfão é defeito.** Toda spec citada existe; todo comando citado roda.
- **Só o revisor edita**, e só no contexto de uma plan aprovada.
- **Sincronia obrigatória:** se uma plan mudou stack, fronteira ou regra, a mesma plan atualiza esta spec.
  Contexto desatualizado é pior que contexto ausente — o agente confia nele.
