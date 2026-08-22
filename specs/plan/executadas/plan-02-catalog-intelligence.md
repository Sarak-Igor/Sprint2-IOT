---
tipo: "plan"
titulo: "Inteligência de Catálogo de Ativos com LLM"
dominio: "asset_manager"
status: "🟢 Aprovada"
prioridade: "Alta"
tags: ["plan", "llm", "assets"]
relacionados: ["[[arquitetura/03-asset-manager]]"]
depende_de: "—"
destino_sintese: "specs/03-asset-manager.md"
---
# 1. Objetivo
Implementar o módulo `asset_manager` criando endpoints de adição de motor que usam LLM via OpenRouter para identificar e preencher as informações base estruturais a partir de inputs básicos.

# 2. Contexto
A aba "Assets" atualmente só lista e deleta. Precisamos da capacidade de inputar um novo motor e deixar o LLM enriquecer os dados técnicos cruciais (RPM nominal, potência, IP) antes de gravar no DB, criando assim perfis de máquina reais.

# 3. Escopo
## 3.1 Dentro
- `backend/apps/asset_manager/*` (Endpoints FastAPI e integração Langchain/OpenRouter)
- `frontend/src/pages/Assets.tsx` (Formulário/Modal de novo ativo)

## 3.2 Fora
- Domínios de Telemetria e Vision.

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Contexto | `00-contexto.md` (Fail-Fast de Configurações, §2) · `00-knowledge.md` | sempre |
| Skill | `cyber-ia` | segurança na chamada ao LLM (prompt injection via texto livre do usuário) |
| Skill | `padrao-python` + `padrao-typescript` | regras base |
| Skill | `test-unitario` | Cobrir o endpoint novo (mock da chamada ao LLM, não da rota) |
| Código | `backend/shared_infra/config.py` | onde a chave da API do LLM deve ser lida via Pydantic — nunca hardcoded |

# 5. Instruções de execução
1. Adicionar a variável da chave de API do LLM (ex.: `OPENROUTER_API_KEY`) em `backend/shared_infra/config.py`
   via `pydantic-settings`, com entrada correspondente em `.env.example` — Fail-Fast, zero valor inferido ou
   hardcoded (`00-contexto.md §2`).
2. Criar o endpoint `POST /api/assets` no `asset_manager` acoplado ao LangChain (OpenRouter).
3. O prompt de LLM deve deduzir informações do motor a partir de marca/modelo ou texto livre.
4. No Frontend, adicionar botão "Novo Ativo" e modal em `Assets.tsx`.
5. Escrever teste unitário do endpoint com a chamada ao LLM mockada (não gastar chamada real em CI).

# 6. Critérios de aceite
- [ ] Chave de API do LLM configurada via `shared_infra/config.py`/`.env`, sem valor hardcoded.
- [ ] Cadastro no Frontend chama o Backend.
- [ ] Backend chama OpenRouter e processa payload.
- [ ] Ativo é salvo na tabela e listado.
- [ ] Teste unitário do endpoint verde.

# 7. Como verificar (uso do revisor)
- Avaliar os arquivos tocados (só frontend e asset_manager).
- Inspecionar a segurança do prompt (Skill `cyber-ia`).

# 8. Destino da síntese
**Destino:** `specs/03-asset-manager.md`
Criação da spec oficial de Catálogo Inteligente.

---
# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

## Resumo da execução — 2026-08-22

**Resultado:** Concluído com pendências

**O que foi feito**
- `backend/shared_infra/config.py` — 3 campos novos em `Settings` (Pydantic, Fail-Fast):
  `openrouter_api_key` (default `""`, mesmo padrão dos outros segredos opcionais do arquivo —
  `r2_*`, `telegram_*`), `openrouter_base_url` (default `https://openrouter.ai/api/v1`) e
  `openrouter_model` (default `openai/gpt-4o-mini`). `.env.example` atualizado com as 3
  variáveis. Nenhum valor hardcoded no código de negócio — tudo lido de `settings`.
- `backend/apps/asset_manager/domain/entities.py` — 2 schemas Pydantic novos:
  `MotorEnrichmentRequest` (entrada do usuário: `name`/`location`/`description`, com
  `max_length` em todos os campos — limite de tamanho de prompt, mitigação de custo/DoS por
  `cyber-ia`) e `MotorSpecEnrichment` (saída estruturada exigida do LLM, com `gt`/`le` em
  `power_hp`/`rpm_nominal` e `max_length` em strings — a resposta do modelo nunca é persistida
  sem passar por esta validação).
- `backend/apps/asset_manager/domain/ai_enrichment.py` (novo) — `enrich_motor_specs()`: monta
  o `ChatOpenAI` (LangChain) apontando para `settings.openrouter_base_url`/`model`, com
  `with_structured_output(MotorSpecEnrichment)` (a resposta do LLM É validada pelo schema, não
  é JSON solto). Prompt de sistema instrui o modelo a tratar a descrição do usuário como dado a
  analisar, nunca como comando, e a nunca inventar variável fora da lista de conhecidas —
  mitigação de prompt injection pedida pela skill `cyber-ia`. `MotorEnrichmentError` cobre tanto
  chave ausente (Fail-Fast, checado antes de qualquer chamada de rede) quanto falha na chamada
  ao OpenRouter — nenhuma exceção é engolida, sempre vira um erro de domínio explícito.
- `backend/apps/asset_manager/web/router.py`:
  - Extraído `_auto_provision_telemetry()` do corpo de `create_active_asset` (era ~30 linhas
    inline) — comportamento idêntico, agora reusado pelo endpoint novo. Pequeno refactor de
    DRY, dentro do escopo (mesmo arquivo, sem mudar o que a função faz).
  - `_thresholds_by_variable_id()` (novo): remapeia as sugestões de limiar do LLM (chave =
    nome da variável) para o formato que `applied_thresholds`/`default_thresholds` já usa
    (chave = `variable_id`), descartando qualquer nome que o LLM tenha inventado — a validação
    de schema não impede um nome inexistente, então este é o filtro que garante que só
    variáveis reais do catálogo entram no banco.
  - `POST /assets` (→ `POST /api/assets` via prefixo montado em `api/index.py`): orquestra
    tudo — busca variáveis conhecidas, chama `enrich_motor_specs`, remapeia limiares, cria
    `MotorModelDB` (RPM/IP guardados em `spec_reference` como texto — ver "Decisões"), cria
    `ActiveAssetDB` via `ActiveAsset(...).dict()` (mesmo padrão do endpoint `/active` existente,
    para herdar os defaults de `status`/`id`) e chama o auto-provisionamento de telemetria.
- `frontend/src/pages/Assets.tsx` — botão "Novo Ativo" no header + modal (mesmo padrão visual
  de `fixed inset-0` + `backdrop-blur` + `motion.div` já usado em `Catalogs.tsx`, não recriei
  nada da lib-ui-core — não existe componente de Modal genérico exportado por
  `@sarak/lib-ui-core`, só widgets de alto nível como `SarakTable`/`SarakForm`). Formulário com
  3 campos (Tag, Localização, descrição livre), `POST /api/assets`, erro exibido inline no
  modal (não `alert()`), fecha e recarrega a tabela (`fetchAssets()`) em caso de sucesso.
- Testes (`test-unitario`, mock só do LLM — não da rota, conforme a plan pede):
  `backend/apps/asset_manager/tests/test_ai_enrichment_endpoint.py` — 3 testes via `TestClient`
  real (rota executa de verdade) contra um dublê de sessão SQLAlchemy (mock só de I/O externo:
  banco de dados, igual ao padrão já usado nas plans anteriores): cadastro com sucesso
  (persiste `MotorModelDB`+`ActiveAssetDB`+`TelemetryMappingDB`, descarta variável inventada
  pelo LLM), 503 quando `enrich_motor_specs` falha (`OPENROUTER_API_KEY` ausente, sem tocar o
  banco), 422 de validação do Pydantic antes mesmo de chamar o LLM (`description` curta demais).

**Arquivos alterados**
| Arquivo | Natureza | O que mudou |
|---|---|---|
| `backend/shared_infra/config.py` | alterado | 3 campos `openrouter_*` |
| `.env.example` | alterado | 3 variáveis `OPENROUTER_*` documentadas |
| `backend/apps/asset_manager/domain/entities.py` | alterado | `MotorEnrichmentRequest`, `MotorSpecEnrichment` |
| `backend/apps/asset_manager/domain/ai_enrichment.py` | criado | integração LangChain/OpenRouter |
| `backend/apps/asset_manager/web/router.py` | alterado | `POST /assets` + 2 helpers extraídos/novos |
| `frontend/src/pages/Assets.tsx` | alterado | botão + modal "Novo Ativo" |
| `backend/apps/asset_manager/tests/test_ai_enrichment_endpoint.py` | criado | 3 testes do endpoint novo |

Confirmado por `git status`: nada fora de `backend/apps/asset_manager/*`,
`backend/shared_infra/config.py`, `.env.example` e `frontend/src/pages/Assets.tsx` — os
demais arquivos modificados no worktree (`iot_firmware/*`, `ingestion_service/main.py`,
`.gitignore`, `specs/plan/plan-01-*`) são da execução da `plan-01`, anterior a esta, não
tocados por mim nesta rodada.

**Verificações executadas**
- `python -m pytest backend api/tests -q` → **27 passed**, 0 failures (24 anteriores + 3 novos
  do `ai_enrichment_endpoint`), 0 regressão.
- `tsc --noEmit` (config temporária ad-hoc em `frontend/`, `strict: true`, apagada depois —
  não há `tsconfig.json` no projeto, ver achado abaixo) rodado só contra `Assets.tsx` → **1
  erro, pré-existente**, na linha do `<SarakTable data={assets} columns={columns}
  emptyMessage=.../>` que já estava no arquivo antes da minha edição (os tipos publicados de
  `@sarak/lib-ui-core` não têm `data`/`columns`, só `endpoint`/`mapping`) — não é código meu,
  não corrigido (fora do escopo, é a lib externa). Todo o código que eu escrevi (modal, form,
  handlers) compilou limpo em modo `strict`.
- `python -c "from backend.apps.asset_manager.web.router import router"` → import ok, rota
  `POST /assets` registrada (`router.routes` confirma o path).
- Autoverificação de limiares (`padrao-python`): nenhuma função nova passa de ~25 linhas,
  aninhamento máximo 2, todas com ≤ 3 parâmetros. `padrao-typescript`: `Assets.tsx` sem função
  nova acima de ~15 linhas.
- **Não executado**: verificação visual no navegador (Playwright/Chromium não instalados nesta
  máquina). Perguntei ao usuário se instalava (~300MB+) para confirmar visualmente; ele optou
  por eu descrever o passo a passo e testar manualmente — instruções entregues na conversa, não
  na plan.
- **Não executado**: chamada real ao OpenRouter (sem `OPENROUTER_API_KEY` configurada neste
  ambiente — confirmado por `grep` no `.env`, sem imprimir valores). O caminho de erro
  Fail-Fast (503) está coberto por teste automatizado real, mas o caminho feliz (LLM
  respondendo de verdade) nunca foi exercitado contra a API real do OpenRouter.

**Critérios de aceite**
- [x] Chave de API do LLM configurada via `shared_infra/config.py`/`.env`, sem valor hardcoded
  — evidência: `config.py` (`openrouter_api_key`), `.env.example`.
- [x] Cadastro no Frontend chama o Backend — evidência: `Assets.tsx` `handleSubmit` →
  `fetch('/api/assets', {method:'POST', ...})`; não verificado em navegador real (ver acima).
- [x] Backend chama OpenRouter e processa payload — evidência: `ai_enrichment.py` +
  `router.py`; chamada real ao OpenRouter não exercitada (sem chave nesta máquina).
- [x] Ativo é salvo na tabela e listado — evidência: `test_create_asset_with_ai_enrichment_persists_model_and_asset`
  confirma `MotorModelDB`+`ActiveAssetDB`+`TelemetryMappingDB` adicionados à sessão; listagem
  usa o mesmo `GET /api/assets/dashboard` já existente, não alterado.
- [x] Teste unitário do endpoint verde — evidência: 3/3 em `test_ai_enrichment_endpoint.py`.

**Decisões e suposições**
- **O que "Ativo" significa aqui.** A plan não deixa explícito se o LLM enriquece um
  `MotorModel` (catálogo) ou um `ActiveAsset` (instância real). Pela aba `Assets.tsx` já listar
  `ActiveAssetDB` via `/dashboard` (confirmado por leitura antes de codar) e pelo contexto
  falar em "perfis de máquina reais", decidi: o endpoint cria AMBOS — um `MotorModelDB` novo
  (catálogo, sempre criado do zero, sem tentar deduplicar contra modelos existentes — não
  pedido, mantém o endpoint simples) e um `ActiveAssetDB` vinculado a ele, reusando o
  auto-provisionamento de telemetria que `/active` já faz. Suposição registrada.
- **RPM nominal e IP não têm coluna própria em `MotorModelDB`** (schema atual só tem
  `brand`/`model`/`power_hp`/`spec_reference`/`default_thresholds`) e a plan não cita
  `db-migrations` nem autoriza mexer em `infrastructure/models.py` para um novo schema. Decidi
  **não migrar o banco** — RPM/IP viram texto legível dentro de `spec_reference`. Tentei
  primeiro guardá-los como uma chave extra `_ai_specs` dentro de `default_thresholds`, mas
  percebi (por leitura de `Catalogs.tsx:264`, fora do meu escopo de edição) que essa página já
  itera **toda** chave de `default_thresholds` como se fosse `variable_id` → `{nominal,
  warning, critical}` — uma chave extra ali quebraria a renderização de um módulo que não
  posso tocar. Se o usuário quiser RPM/IP como colunas reais e pesquisáveis, é uma plan nova
  com `db-migrations`.
- **Threshold sugerido pelo LLM é keyed por nome de variável, remapeado para UUID no
  servidor** — não pedi ao LLM para inventar UUIDs (ele não os conhece); o remapeamento
  descarta qualquer nome que não bata com uma `DataVariableDB` real, o que também limita
  naturalmente o "tamanho" da resposta persistida (mitigação de abuso, `cyber-ia`).
- **Sem rate limit no endpoint novo** — `cyber-api` não foi citada pela plan, então não
  adicionei nenhum limite de requisições. Fica registrado como achado (abaixo), não como
  pendência corrigida.
- **Não editei `specs/03-asset-manager.md`** (destino de síntese, §8) — mesma leitura da
  `plan-01`: `00-prompt-executor.md §7.3` proíbe editar outra spec fora do que a própria plan
  autoriza como passo de execução, e esta plan só menciona a síntese em §8 (destino, não
  instrução de execução).

**Achados fora do escopo (não corrigidos)**
- **`frontend/tsconfig.json` não existe no repositório** (nunca existiu, confirmado por
  `git log --all`), embora `package.json:8` tenha `"build": "tsc && vite build"` — ou seja,
  `npm run build` falha hoje com `error TS5057: Cannot find a tsconfig.json`, para qualquer
  arquivo, não só o meu. Não corrigido (fora do escopo desta plan, que só autoriza
  `asset_manager/*` e `Assets.tsx`) — mas é bloqueador real de qualquer build de produção do
  frontend, vale uma plan própria.
- `POST /api/assets` (endpoint novo) não tem rate limiting nem custo máximo por requisição —
  um usuário mal-intencionado pode gerar custo real no OpenRouter repetindo a chamada. `cyber-api`
  não foi citada por esta plan; registrado para uma futura auditoria de segurança de API.
- `db_asset = ActiveAssetDB(**new_asset.dict())` (e todo o resto do arquivo, pré-existente) usa
  `.dict()` do Pydantic v1, deprecado desde o v2 em favor de `.model_dump()` — segui o padrão já
  usado em todo o arquivo (`asset.dict()`, `model.dict()`, etc.), não migrei sozinho porque isso
  mudaria o estilo de um arquivo inteiro fora do pedido desta plan.

**Pendências / riscos**
- **Verificação visual em navegador não feita** — o usuário optou por testar manualmente.
  Passo a passo entregue na conversa (não na plan, por instrução do `00-prompt-executor`).
- **Caminho feliz do LLM nunca chamado de verdade** — só testado com `enrich_motor_specs`
  mockado. Risco real: erros de parsing específicos da resposta do OpenRouter (ex.:
  `with_structured_output` falhando silenciosamente para o modelo escolhido) só aparecem no
  primeiro uso real, com uma `OPENROUTER_API_KEY` válida.
- Se o usuário adicionar `OPENROUTER_API_KEY` ao `.env` para testar o caminho feliz, o teste vai
  gravar um `MotorModelDB`/`ActiveAssetDB`/mapeamentos de verdade no banco configurado em
  `DATABASE_URL` — não é um ambiente de teste isolado, então cadastros de teste ficam
  misturados aos dados reais. Recomendo remover manualmente depois.

---
# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->

## Veredito — 2026-08-22 — 🟢 Aprovado

**Verificado diretamente no worktree:**

- `git status`/`git diff --stat` → só os arquivos da tabela do resumo (`asset_manager/*`,
  `config.py`, `.env.example`, `Assets.tsx`, `.gitignore`); nada em telemetria/vision/`digital_twin_core`.
- Li `router.py` inteiro: confirmo que a extração de `_auto_provision_telemetry()` é
  comportamento idêntico ao bloco inline anterior (comparei as duas versões linha a linha no
  diff); `_thresholds_by_variable_id()` e `create_asset_with_ai_enrichment` são lógica nova
  correta — remapeamento descarta variável inventada, `MotorEnrichmentError` vira 503 antes de
  qualquer escrita no banco.
- Li `ai_enrichment.py` inteiro: Fail-Fast checado antes de qualquer chamada de rede, saída do
  LLM validada por `MotorSpecEnrichment` (nunca JSON solto persistido direto), prompt de sistema
  trata a descrição do usuário como dado a analisar — atende `cyber-ia` como a plan exigia.
- Rodei a suíte eu mesmo: `python -m pytest backend api/tests -v` → **27 passed**, confirma o
  número alegado (24 anteriores + 3 novos: sucesso, 503 Fail-Fast, 422 de validação).
- Rodei `npx tsc --strict` (config ad-hoc, como o executor descreveu) contra `Assets.tsx` →
  **1 erro só**, na linha do `SarakTable` que já existia antes desta execução (confirmado pelo
  diff — só reformatação nessa linha específica); todo o código novo (modal/form) compila limpo.
- Confirmei por `find` que `frontend/tsconfig.json` de fato não existe — achado real, não desculpa.
- `minLength={3}`/`maxLength={500}` do textarea batem exatamente com
  `MotorEnrichmentRequest.description` (Pydantic).

**Critérios de aceite — 4 de 4 atendidos, todos com evidência real:**
- [x] Chave de API via `config.py`/`.env`, sem hardcode.
- [x] Frontend chama o backend (`fetch('/api/assets', ...)`, confirmado no diff).
- [x] Backend chama OpenRouter e processa payload (wiring real + teste cobrindo o processamento
  completo com o LLM mockado — a chamada de rede real ao OpenRouter não é exigida por este
  critério, só a capacidade de processar a resposta, que está testada).
- [x] Ativo salvo e listado (teste confirma `MotorModelDB`+`ActiveAssetDB`+`TelemetryMappingDB`
  adicionados à sessão; `GET /dashboard` não foi alterado).
- [x] Teste unitário verde — 27/27.

**Diferença importante em relação à `plan-01`:** os 4 critérios desta plan, como eu os escrevi,
não exigem uma chamada real ao LLM nem confirmação visual em navegador — só capacidade de
processamento testada. Por isso não há bloqueio estrutural aqui; a verificação visual manual que
o usuário adiou fica registrada como pendência informativa, não como critério não atendido.

**Achados fora do escopo, registrados, corretos (não corrigidos agora):** `frontend/tsconfig.json`
ausente quebra `npm run build` hoje (pré-existente, não desta plan — vale plan própria); sem rate
limit em `POST /api/assets` (`cyber-api` não foi citada nesta plan); uso de `.dict()` (Pydantic
v1) mantido por consistência com o resto do arquivo.

**Pendência registrada, sem peso no veredito:** caminho feliz do LLM nunca chamado de verdade
(sem `OPENROUTER_API_KEY` neste ambiente) — se o usuário testar manualmente com uma chave real e
algo quebrar no parsing da resposta do OpenRouter, é achado novo, não coberto por este veredito.
