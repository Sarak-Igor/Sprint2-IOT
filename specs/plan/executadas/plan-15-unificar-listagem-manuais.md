---
tipo: "plan"
titulo: "Unificar a listagem de manuais da aba Knowledge com o que está de fato indexado no RAG"
dominio: "ai_knowledge"
status: "🟢 Aprovada"
prioridade: "Alta"
tags: ["plan", "ai_knowledge", "rag", "correcao"]
relacionados: ["[[specs/06-agente-conversacional]]"]
depende_de: "—"
destino_sintese: "specs/05-ai-knowledge.md"
---

# 1. Objetivo
A aba "Knowledge" (e qualquer outro consumidor de `GET /api/manuals`) passa a listar exatamente os
manuais que estão de fato indexados no vetor-store do RAG — nenhum valor fixo no código, nenhuma
divergência entre "o que a UI mostra" e "o que o RAG/o agente conversacional realmente enxergam".

# 2. Contexto
`GET /api/manuals` (`api/index.py:492-508`) é **hardcoded**: sempre devolve uma única entrada fixa
("Manual Técnico WEG W22") com uma URL de download real do Cloudflare R2
(`storage_client.get_download_url`), completamente desconectada do pipeline real de RAG
(`POST /api/knowledge/ingest` → `vector_store.add_chunks` → ChromaDB local). Esse endpoint já existia
antes da `plan-04` (RAG) e nunca foi ligado a ela — achado já registrado no veredito da `plan-04`
(2026-08-22): *"`/api/manuals` continua mockado... convivem dois sistemas de 'manuais' na mesma
página... sem nenhuma ligação entre eles... pode valer uma plan futura de unificação"*.

O problema ficou visível na prática agora: um usuário via o card do "Manual WEG W22" na aba Knowledge
e presumiu que ele compunha o RAG — mas como o card nunca passou pelo `/knowledge/ingest`, o
ChromaDB está vazio (confirmado por leitura direta: `collection.count() == 0`, nenhum arquivo em
`backend/apps/ai_knowledge/storage/pdfs/`) e o agente conversacional (`plan-14`, aprovada) respondeu
corretamente "nenhum manual indexado" — o agente não tem bug, a listagem é que mente.

Dados reais já disponíveis para montar a listagem, sem inventar nada novo:
- Cada chunk indexado no ChromaDB (`vector_store.py::add_chunks`) já carrega metadata
  `{"source": filename, "page": chunk.page, "manual_id": manual_id}` (`ai_knowledge/router.py:56-59`).
- O PDF original de cada manual já fica salvo em
  `settings.knowledge_storage_path/pdfs/{manual_id}.pdf` (`ai_knowledge/router.py:17-24`,
  `_save_pdf_locally`) — dá para ler o tamanho real do arquivo em disco dali.
- `ai_knowledge` já é 100% local por decisão do usuário (`00-contexto.md §8`) — a nova listagem e o
  download **não devem** usar `storage_client`/Cloudflare R2; servir o PDF direto do disco local é
  consistente com essa decisão já tomada.

# 3. Escopo

## 3.1 Dentro
- `api/index.py` — remover o endpoint `GET /api/manuals` hardcoded (linhas 492-508) e o import de
  `storage_client` que só ele usava (confirmar por leitura antes de remover o import).
- `backend/apps/ai_knowledge/vector_store.py` — nova função de leitura (ex.:
  `list_indexed_manuals()`) que deriva a lista de manuais a partir dos metadados já gravados no
  ChromaDB (agrupar por `manual_id`: `source`, maior `page` = total de páginas com chunk, contagem
  de chunks). Não duplicar o que o Chroma já guarda em nenhuma estrutura paralela.
- `backend/apps/ai_knowledge/router.py` — duas rotas novas, dentro do prefixo `/knowledge` já
  existente: uma de listagem (ex.: `GET /knowledge/manuals`) e uma de download do PDF local (ex.:
  `GET /knowledge/manuals/{manual_id}/download`, lendo de
  `settings.knowledge_storage_path/pdfs/{manual_id}.pdf` — 404 se o arquivo não existir).
- `backend/apps/ai_knowledge/schemas.py` — schema de resposta da listagem (ex.: `ManualInfo`) —
  reaproveitar o padrão de `IngestResponse`, não duplicar campo que já exista em outro schema.
- `frontend/src/pages/Knowledge.tsx` — trocar a chamada de `GET /api/manuals` pela nova rota real;
  ajustar a interface `Manual` e a renderização do card ao schema real. **Remover `tags`/`category`
  da interface e da UI** — não há fonte real para esses dois campos (zero-hardcode); o filtro de
  busca passa a considerar só o título/nome do arquivo.

## 3.2 Fora
- `POST /api/knowledge/ingest` — comportamento de ingestão não muda. Reenviar o mesmo manual duas
  vezes ainda duplica chunks no índice (achado já registrado no veredito da `plan-04`) — **não
  corrigir aqui**, é um problema diferente (deduplicação), não de listagem.
- `backend/shared_infra/storage_client.py` — não editar nem remover. Se ficar sem nenhum chamador
  depois desta plan, **registre como achado fora do escopo** — não apague por conta própria.
- `backend/apps/ai_knowledge/agent/*` (`plan-14`, aprovada) — o agente já consome `answer_question()`
  corretamente; esta plan não muda a conversa, só a listagem visual de manuais na aba Knowledge.
- `backend/apps/ai_knowledge/rag_engine.py`, `pdf_ingestion.py` — não mudam.
- Qualquer outra aba do frontend, `backend/apps/digital_twin_core/*`, `asset_manager/*`,
  `ingestion_service/*` — não mudam.

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Spec fixa | `specs/06-agente-conversacional.md` | contexto de por que o problema apareceu (a resposta correta do agente expôs a divergência) |
| Contexto | `00-contexto.md §8` (decisão de manter `ai_knowledge` 100% local, sem R2) · `00-knowledge.md` | sempre |
| Skill | `padrao-escrita` + `padrao-python` + `padrao-typescript` | backend e frontend |
| Skill | `test-unitario` | cobrir `list_indexed_manuals()` (agrupamento por `manual_id`), a rota de listagem e a de download (arquivo existente/ausente) |
| Código | `api/index.py:492-508` | o endpoint hardcoded a remover — ler antes |
| Código | `backend/apps/ai_knowledge/router.py`, `vector_store.py`, `schemas.py` | contrato real de ingestão a reaproveitar — ler antes de codificar |
| Código | `backend/shared_infra/config.py` (`knowledge_storage_path`) | onde os PDFs reais estão salvos |
| Código | `frontend/src/pages/Knowledge.tsx` | ler o componente inteiro antes de editar a listagem |

# 5. Instruções de execução
1. Ler `api/index.py:492-508`, `ai_knowledge/router.py`, `vector_store.py` e `schemas.py` por
   completo antes de codificar.
2. Criar `list_indexed_manuals()` em `vector_store.py`: ler todos os metadados da coleção
   (`collection.get(include=["metadatas"])`), agrupar por `manual_id`, calcular páginas (maior
   `page` visto) e nº de chunks (contagem) por manual. Devolver lista vazia se a coleção estiver
   vazia (mesmo espírito de `query_similar_chunks`, não é um erro).
3. Criar `ManualInfo` em `schemas.py` (ex.: `manual_id`, `filename`, `paginas`,
   `chunks_indexados`, `tamanho_bytes`, `download_url`).
4. Criar `GET /knowledge/manuals` em `router.py`: monta a resposta a partir de
   `list_indexed_manuals()`, lendo o tamanho real de cada arquivo em
   `settings.knowledge_storage_path/pdfs/{manual_id}.pdf` (`0` ou omitir o campo se o arquivo não
   existir por algum motivo — não deve quebrar a listagem inteira por um arquivo faltando).
5. Criar `GET /knowledge/manuals/{manual_id}/download` em `router.py`: serve o PDF local
   (`FileResponse` ou equivalente do FastAPI/Starlette) — 404 se o arquivo não existir. Sem
   `storage_client`/R2.
6. Remover `GET /api/manuals` de `api/index.py` e o import de `storage_client` se ele não for mais
   usado em nenhum outro lugar do arquivo (confirmar por leitura/grep antes de remover o import).
7. No frontend, trocar `fetch('/api/manuals')` por `fetch('/api/knowledge/manuals')` em
   `Knowledge.tsx`; ajustar a interface `Manual` ao schema real; remover a renderização de
   `tags`/`category`; ajustar `handleDownload`/`handleOpen` para a nova `download_url`.
8. Escrever os testes: `list_indexed_manuals()` (coleção vazia; múltiplos manuais com chunks
   intercalados agrupando corretamente); a rota de listagem (com `vector_store` mockado); a rota de
   download (arquivo existente devolve o PDF, arquivo ausente devolve 404).
9. Rodar a suíte completa e confirmar verde.
10. Verificação manual sugerida (não bloqueia os critérios automatizáveis): subir o backend, enviar
    um PDF real pelo "Novo Manual" da aba Knowledge, confirmar que ele aparece na listagem (sem
    reload manual do card antigo) e que o agente conversacional (`plan-14`) passa a responder com
    base nele.

# 6. Critérios de aceite
- [ ] `GET /api/manuals` (hardcoded) não existe mais; a aba Knowledge lista os manuais via uma rota
  que lê o estado real do RAG.
- [ ] Coleção vazia → listagem vazia (nenhum manual fantasma), consistente com o que o agente e o
  RAG já reportam ("nenhum manual indexado").
- [ ] Manual indexado via `POST /knowledge/ingest` aparece na listagem sem nenhuma ação manual
  adicional (sem hardcode, sem cache que precise ser invalidado à mão).
- [ ] Download de um manual real funciona a partir do arquivo local, sem depender de
  `storage_client`/Cloudflare R2.
- [ ] `Knowledge.tsx` não renderiza `tags`/`category` fabricados — só dados reais devolvidos pela API.
- [ ] Testes unitários de `list_indexed_manuals()` e das duas rotas novas verdes; suíte completa sem
  regressão.

# 7. Como verificar (uso do revisor)
- `git diff --stat` → só os caminhos de §3.1; nada em `ingest`/`rag_engine.py`/`pdf_ingestion.py`/
  `agent/*`.
- Ler `list_indexed_manuals()` e conferir o agrupamento contra um exemplo mental (2 manuais, chunks
  intercalados) antes de rodar o teste.
- Rodar a suíte e ler a saída real.
- Testar manualmente (ou via `TestClient`) o fluxo completo: ingest de um PDF real → listagem reflete
  → download funciona → agente conversacional responde com fonte.
- Confirmar por leitura que `storage_client`/R2 não é mais referenciado em `api/index.py` nem no
  `router.py` de `ai_knowledge`.

# 8. Destino da síntese
**Destino:** `specs/05-ai-knowledge.md`
Documentar que a listagem de manuais é derivada do estado real do vetor-store (não mais um valor
fixo), e que o download de manuais é 100% local — reforça a mesma decisão já registrada pela
`plan-04`.

---

# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

## Resumo da execução — 2026-08-23

**Resultado:** Concluído

**O que foi feito**
- `backend/apps/ai_knowledge/vector_store.py:42-68` — criada `list_indexed_manuals()`: lê
  `collection.get(include=["metadatas"])`, agrupa por `manual_id` (dict acumulador),
  `paginas` = maior `page` visto, `chunks_indexados` = contagem de chunks daquele manual.
  Devolve `[]` se a coleção estiver vazia, sem chamar `.get()` nesse caso (mesmo espírito de
  `query_similar_chunks`). Não duplica nenhuma estrutura paralela — só deriva do que o
  Chroma já guarda.
- `backend/apps/ai_knowledge/schemas.py:28-34` — `ManualInfo` (`manual_id`, `filename`,
  `paginas`, `chunks_indexados`, `tamanho_bytes`, `download_url`), reaproveitando os
  mesmos nomes de campo já usados em `IngestResponse`.
- `backend/apps/ai_knowledge/router.py:23-40` — helpers `_pdf_dir()` (compartilhado com
  `_save_pdf_locally`, que antes duplicava esse cálculo — refatorado para reusar),
  `_pdf_size_or_zero()` e `_resolve_manual_pdf_path()` (resolve o caminho do PDF a partir
  do `manual_id` da URL e confirma que o resultado continua dentro de `pdf_dir` antes de
  servir — defesa contra path traversal via o parâmetro vindo do cliente).
- `backend/apps/ai_knowledge/router.py:104-128` — duas rotas novas: `GET
  /knowledge/manuals` (monta `ManualInfo` a partir de `list_indexed_manuals()` + tamanho
  real do arquivo em disco, `0` se o arquivo não existir — não quebra a listagem inteira) e
  `GET /knowledge/manuals/{manual_id}/download` (serve o PDF local via `FileResponse`, 404
  se o arquivo não existir). Nenhuma das duas usa `storage_client`/R2.
- `api/index.py` — removido `GET /api/manuals` (hardcoded, linhas 492-508 da versão lida
  antes de editar) e o import de `storage_client` (confirmado por grep: era o único uso
  real dele no arquivo).
- `frontend/src/pages/Knowledge.tsx` — interface `Manual` trocada para os campos reais
  (`manual_id`, `filename`, `paginas`, `chunks_indexados`, `tamanho_bytes`,
  `download_url`); **removidos `title`/`category`/`url`/`tags`** da interface e de toda a
  renderização (card não mostra mais tags fabricadas); `fetch('/api/manuals')` trocado por
  `fetch('/api/knowledge/manuals')`; filtro de busca agora considera só `filename`;
  `handleDownload`/`handleOpen` ajustados para `download_url`; adicionado helper
  `formatBytes()` (só formata `tamanho_bytes` real, não inventa dado) e a linha inferior do
  card passou a mostrar tamanho real + páginas + chunks indexados (dados reais devolvidos
  pela API, no lugar das tags fabricadas).
- Testes novos (skill `test-unitario`):
  `backend/apps/ai_knowledge/tests/test_vector_store.py` (coleção vazia → `[]`; 2 manuais
  com chunks intercalados agrupados corretamente, `paginas`/`chunks_indexados` conferidos
  por manual) e 5 casos novos em `test_knowledge_endpoints.py` (listagem deriva do
  vetor-store mockado com tamanho real de arquivo; listagem vazia; tamanho `0` quando o
  PDF não existe em disco; download devolve o PDF quando o arquivo existe; download
  devolve 404 quando o arquivo não existe).

**Arquivos alterados**
| Arquivo | Natureza | O que mudou |
|---|---|---|
| `backend/apps/ai_knowledge/vector_store.py` | alterado | `+list_indexed_manuals()` |
| `backend/apps/ai_knowledge/schemas.py` | alterado | `+ManualInfo` |
| `backend/apps/ai_knowledge/router.py` | alterado | `+GET /manuals`, `+GET /manuals/{id}/download`, helpers de path |
| `api/index.py` | alterado | `-GET /api/manuals` hardcoded, `-import storage_client` |
| `frontend/src/pages/Knowledge.tsx` | alterado | listagem real, sem `tags`/`category` |
| `backend/apps/ai_knowledge/tests/test_vector_store.py` | criado | testes de `list_indexed_manuals()` |
| `backend/apps/ai_knowledge/tests/test_knowledge_endpoints.py` | alterado | +5 testes das rotas novas |

**Verificações executadas**
- `python -m pytest backend/apps/ai_knowledge/tests/test_vector_store.py
  backend/apps/ai_knowledge/tests/test_knowledge_endpoints.py -v` → 14 passed.
- `python -m pytest backend/ -v` (suíte completa) → **71 passed**, 0 falhas, 0 regressão
  (inclui os 64 testes já verdes antes desta plan, mais os 7 novos — 2 de
  `test_vector_store.py` e 5 novos em `test_knowledge_endpoints.py`).
- `grep -rn "storage_client" api/index.py` → nenhum resultado (import e uso removidos).
- `grep -rln "from backend.shared_infra.storage_client|import storage_client|storage_client\."
  --glob "*.py"` no repo inteiro → nenhum resultado — `storage_client.py` ficou sem
  nenhum chamador real (ver "Achados fora do escopo").
- `grep -n "\.title|\.tags|\.category|doc\.url|m\.tags" frontend/src/pages/Knowledge.tsx` →
  nenhum resultado (campos fabricados removidos de fato, não só da interface).
- `npx vite build` (frontend) → build concluído sem erros (4708 módulos); `dist/` gerado só
  para a verificação foi removido em seguida.
- `git status`/`git diff --stat` restrito aos caminhos de §3.1 → só os arquivos da tabela
  acima entraram como alterados por esta execução; nada em `ingest`, `rag_engine.py`,
  `pdf_ingestion.py` ou `agent/*` (confirmado — `rag_engine.py` aparece como `M` no
  `git status` geral, mas é resíduo pré-existente da `plan-13`, não tocado nesta execução).

**Critérios de aceite**
- [x] `GET /api/manuals` (hardcoded) não existe mais; a aba Knowledge lista via rota que lê
  o estado real do RAG — evidência: `api/index.py` sem a rota; `Knowledge.tsx` chama
  `/api/knowledge/manuals`.
- [x] Coleção vazia → listagem vazia — evidência:
  `test_list_indexed_manuals_returns_empty_when_collection_empty`,
  `test_list_manuals_returns_empty_list_when_no_manual_indexed`.
- [x] Manual indexado via `POST /knowledge/ingest` aparece na listagem sem ação manual —
  evidência: `list_manuals()` chama `list_indexed_manuals()` a cada requisição, sem cache;
  nenhuma estrutura paralela a invalidar.
- [x] Download funciona a partir do arquivo local, sem `storage_client`/R2 — evidência:
  `test_download_manual_returns_pdf_when_file_exists`; grep confirma zero uso de
  `storage_client` nas rotas novas.
- [x] `Knowledge.tsx` não renderiza `tags`/`category` fabricados — evidência: grep acima,
  campos removidos da interface `Manual` e da renderização do card.
- [x] Testes de `list_indexed_manuals()` e das duas rotas novas verdes; suíte completa sem
  regressão — evidência: 71/71 passed.

**Decisões e suposições**
- `_resolve_manual_pdf_path()` inclui uma checagem de contenção de caminho (o candidato
  resolvido precisa continuar dentro de `pdf_dir`) mesmo sabendo que o parâmetro de rota
  `{manual_id}` do FastAPI/Starlette não aceita `/` por padrão (não dá pra escapar do
  diretório só com `..` sem separador de caminho). Mantive a checagem como defesa em
  profundidade barata (3 linhas, mesmo espírito do comentário já existente em
  `_save_pdf_locally` sobre path traversal) — mas **não** escrevi um teste dedicado para
  esse cenário porque ele não é alcançável pela rota real hoje (testar exigiria chamar a
  função interna diretamente, o que testaria a implementação, não o comportamento
  observável). Se o revisor considerar isso validação para um cenário inatingível, é uma
  decisão reversível de 3 linhas.
- Refatorei `_save_pdf_locally()` para reusar o novo helper `_pdf_dir()` em vez de repetir
  `Path(settings.knowledge_storage_path) / "pdfs"` — mesma função, zero mudança de
  comportamento, elimina duplicação introduzida pelas rotas novas no mesmo arquivo. Não
  estava listado literalmente em §3.1, mas é a mesma responsabilidade (caminho dos PDFs
  locais) tocada pela própria mudança pedida, não uma extensão de escopo.
- `download_url` é montado como caminho relativo `/api/knowledge/manuals/{manual_id}/download`
  (não uma URL assinada com expiração, como a antiga do R2) — consistente com "100% local,
  sem R2" (§2 da plan); o navegador resolve contra a própria origem do backend.
- O card do frontend passou a mostrar "tamanho · páginas · chunks" no lugar das tags — não
  pedido explicitamente pela plan, mas decisão conservadora para não deixar a linha vazia
  depois de remover as tags fabricadas, usando só campos reais que a API já devolve (sem
  inventar dado novo).

**Achados fora do escopo (não corrigidos)**
- `backend/shared_infra/storage_client.py` ficou sem nenhum chamador real no repositório
  (confirmado por grep — só resta seu próprio `import boto3`/definição da classe). Não
  removido, conforme instrução explícita da plan (§3.2: "não apague por conta própria").
  Fica candidato a uma plan futura de remoção, se o revisor/usuário confirmar que não há
  uso planejado a curto prazo (ex.: schematics, outros tipos de arquivo).
- (Já registrado no resumo da `plan-14`, ainda não corrigido): o projeto não tem
  `tsconfig.json` — `npm run build` (`tsc && vite build`) falha no passo `tsc` hoje,
  independente desta plan. `npx vite build` isolado segue funcionando e confirma que o
  `Knowledge.tsx` alterado não tem erro de sintaxe/import.

**Pendências / riscos**
- A verificação manual sugerida pela plan (passo 10: subir o backend, enviar um PDF real
  pela aba Knowledge, confirmar listagem sem reload manual, confirmar que o agente
  `plan-14` passa a responder com base nele) **não foi executada** — não bloqueia os
  critérios automatizáveis (a própria plan marca esse passo como não-bloqueante), mas fica
  como verificação end-to-end recomendada antes de considerar o fluxo 100% validado em
  produção.

---

# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->

## Veredito — 2026-08-23 — 🟢 Aprovado

**Verificado diretamente no worktree:**

- `git status`/`git diff --stat` → bate com o alegado: `vector_store.py`, `schemas.py`, `router.py`
  (`ai_knowledge`), `api/index.py`, `Knowledge.tsx` alterados; `test_vector_store.py` novo,
  `test_knowledge_endpoints.py` com os 5 casos novos. `rag_engine.py` segue com o mesmo diff da
  `plan-13` (30 linhas, 10 inserções/20 remoções) — confirmei que não ganhou nenhuma linha nova
  nesta rodada. Nada em `pdf_ingestion.py` ou `agent/*`.
- Li `vector_store.py::list_indexed_manuals()`, `router.py` (as duas rotas novas + os 3 helpers de
  path) e `schemas.py::ManualInfo` por completo: agrupamento por `manual_id` correto (`paginas` =
  maior página vista, `chunks_indexados` = contagem), lista vazia sem chamar `.get()` quando a
  coleção está vazia, `_resolve_manual_pdf_path` com defesa de contenção de caminho antes de servir
  o arquivo, zero uso de `storage_client`/R2 nas rotas novas.
- Rodei a suíte eu mesmo: `python -m pytest backend/ -q` → **71 passed**, bate exatamente com o
  alegado.
- Fui além do que a própria plan marcou como "não bloqueante" (passo 10) e rodei o **fluxo real
  completo contra o app de verdade** (`TestClient` sobre `api.index.app`, sem nenhum mock): gerei um
  PDF mínimo válido com texto real ("Vibração máxima permitida 4.5 mm/s RMS motor W22"),
  `POST /api/knowledge/ingest` → 200, indexou 1 chunk; `GET /api/knowledge/manuals` → 200, o manual
  apareceu na listagem com `tamanho_bytes`/`paginas`/`chunks_indexados` reais;
  `GET /api/knowledge/manuals/{id}/download` → 200, 579 bytes, `content-type: application/pdf`,
  conteúdo baixado bate com o PDF enviado. **Prova real de ponta a ponta de que a divergência que
  motivou esta plan está corrigida** — não só em teste mockado. Limpei os dados de teste depois
  (removi o chunk do ChromaDB e o PDF do disco) para não poluir a base do usuário.
- `grep` confirma zero referência a `storage_client` em `api/index.py` e zero `tags`/`category`/
  `title`/`doc.url` restantes em `Knowledge.tsx`.
- Rodei `npx vite build` eu mesmo → build limpo, confirma o alegado.

**Critérios de aceite — 6 de 6 atendidos, com evidência real (minha, além da do executor):**
- [x] `GET /api/manuals` hardcoded removido; listagem via estado real do RAG.
- [x] Coleção vazia → listagem vazia.
- [x] Manual ingerido aparece na listagem sem ação manual — confirmado com dado real, não só mock.
- [x] Download funciona a partir do disco local, sem R2 — confirmado com dado real.
- [x] `Knowledge.tsx` sem campos fabricados.
- [x] Testes verdes, suíte sem regressão — 71/71.

**Sobre a decisão de manter a checagem de contenção de caminho sem teste dedicado:** aceito o
raciocínio do executor — o parâmetro de rota do FastAPI não permite `/` no valor, então o cenário
não é alcançável pela rota real hoje; é defesa em profundidade barata, não uma lacuna de cobertura
real.

**Achado fora do escopo, registrado, correto (não corrigido agora):** `storage_client.py` ficou sem
nenhum chamador real no repositório — não removido, por instrução explícita da própria plan.
Candidato a uma plan futura de remoção, se confirmado que não há uso planejado.

**Liberação:** nenhuma plan da fila depende de `plan-15`. O caso original que abriu esta investigação
está resolvido: o usuário pode reenviar o manual real pelo "Novo Manual" e tanto a listagem quanto o
agente conversacional (`plan-14`) vão refletir isso corretamente — comportamento que acabei de
confirmar funciona de ponta a ponta.
