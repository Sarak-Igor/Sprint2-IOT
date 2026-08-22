---
tipo: "plan"
titulo: "Implementar RAG na Knowledge Base"
dominio: "ai_knowledge"
status: "🟢 Aprovada"
prioridade: "Alta"
tags: ["plan", "rag", "llm"]
relacionados: ["[[arquitetura/04-ai-knowledge]]"]
depende_de: "—"
destino_sintese: "specs/05-ai-knowledge.md"
---
# 1. Objetivo
Tornar a Knowledge Base viva implementando engine de busca semântica (RAG) no módulo `ai_knowledge` e respondendo através da aba correspondente.

# 2. Contexto
O módulo `ai_knowledge` e a página `Knowledge.tsx` estão estáticos e sem conexão real. O sistema precisa permitir subir novos PDFs de manuais e responder perguntas técnicas.

> **Correção (2026-08-22):** apesar de `adr/005-integracoes-iniciais.md` aceitar Cloudflare R2 como
> integração e de já existir `storage_client.py` (usado hoje só pelo endpoint mockado
> `GET /api/manuals`), **decisão explícita do usuário: esta feature fica 100% local**, sem depender de
> rede externa. Os PDFs dos manuais e o vetor-store (ChromaDB/FAISS) vivem em disco, dentro do
> repositório/volume local — não use `storage_client`/R2 aqui.

# 3. Escopo
## 3.1 Dentro
- `backend/apps/ai_knowledge/*` (Motor de Embeddings e conversação).
- `frontend/src/pages/Knowledge.tsx` (Conexão à RAG e Upload de Manuais).

## 3.2 Fora
- Demais abas do Frontend.

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Contexto | `00-contexto.md` (Fail-Fast de Configurações, §2) · `00-knowledge.md` | sempre |
| Skill | `cyber-ia` | proteção contra prompt injection (conteúdo de PDF não é confiável) |
| Skill | `padrao-python` + `padrao-typescript` | regras base |
| Skill | `test-unitario` | Cobrir ingestão e busca (mock do LLM e do vetor-store) |
| Código | `backend/apps/ai_knowledge/` | módulo hoje sem nenhum código-fonte — ler `ocr_plan.md`/`structure_guide.md` antes, são só planejamento textual, não implementação |

# 5. Instruções de execução
1. Adicionar a variável da chave de API do LLM em `backend/shared_infra/config.py` (mesmo padrão de `plan-02`,
   reaproveitar se já existir) — nunca hardcoded. Adicionar também, via Pydantic, o caminho local onde os
   PDFs e o vetor-store persistem (ex.: `backend/apps/ai_knowledge/storage/`), configurável e com default
   sensato — nunca caminho hardcoded espalhado pelo código.
2. Preencher `backend/apps/ai_knowledge/requirements.txt` (hoje vazio) com as dependências reais escolhidas.
3. Criar backend RAG em `ai_knowledge` usando ChromaDB/FAISS (persistência local em disco) e OpenRouter;
   os PDFs originais ficam salvos localmente (não usar `storage_client`/Cloudflare R2 — decisão do usuário,
   ver §2). Garantir que o diretório de storage local esteja no `.gitignore` (não versionar PDFs/índice).
4. Endpoint de ingestão de PDF e endpoint de Pergunta.
5. Front-end consumindo as respostas.
6. Escrever teste unitário de ingestão e de busca, com o LLM e o vetor-store mockados.

# 6. Critérios de aceite
- [ ] Chave de API do LLM configurada via `shared_infra/config.py`/`.env`, sem valor hardcoded.
- [ ] Usuário pode enviar novo manual e ele é indexado.
- [ ] Busca natural devolve a resposta gerada por IA com fonte (página do PDF).
- [ ] PDFs e vetor-store armazenados localmente em disco, sem dependência de rede externa.
- [ ] Diretório de storage local no `.gitignore`.
- [ ] Testes unitários de ingestão e busca verdes.

# 7. Como verificar (uso do revisor)
- Checar a vetorização de documentos e as chaves do LLM.

# 8. Destino da síntese
**Destino:** `specs/05-ai-knowledge.md`

---
# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

## Resumo da execução — 2026-08-22

**Resultado:** Concluído com pendências

**O que foi feito**
- Confirmado no início: a instrução do usuário desta execução já batia com a correção que
  `00-contexto.md`/a própria plan já traziam (100% local, sem R2) — não houve conflito a
  resolver, só segui o que já estava escrito.
- `backend/shared_infra/config.py` — 1 campo novo: `knowledge_storage_path` (Pydantic,
  default `ROOT_DIR/backend/apps/ai_knowledge/storage`, override via `KNOWLEDGE_STORAGE_PATH`).
  **Não recriei** nenhum campo `openrouter_*` — reusados diretamente de `settings`, criados
  pela `plan-02`. `.env.example` atualizado com a nova variável.
- `.gitignore` — `backend/apps/ai_knowledge/storage/` adicionado (PDFs e índice vetorial nunca
  versionados, são artefato gerado).
- Dependências novas instaladas no `.venv` e declaradas em `requirements.txt` (raiz) **e** em
  `backend/apps/ai_knowledge/requirements.txt` (estava vazio, passo 2 da plan): `chromadb`
  (vetor-store local, persistência em disco), `pypdf` (extração de texto por página, mais leve
  que `PyMuPDF`/`fitz` sugerido em `rag_base/structure_guide.md` — troquei por não exigir
  compilação nativa), `langchain-text-splitters` (`RecursiveCharacterTextSplitter`, o mesmo
  chunking de ~1000 chars/200 overlap que o guia já descrevia).
- `backend/apps/ai_knowledge/` (módulo novo):
  - `schemas.py` — `AskRequest`, `SourceCitation`, `AskResponse`, `IngestResponse`.
  - `vector_store.py` — `chromadb.PersistentClient` apontando para
    `settings.knowledge_storage_path/vector_store`, com `anonymized_telemetry=False`
    (ChromaDB manda telemetria anônima por padrão — desliguei explicitamente, sem isso a
    decisão de "sem depender de rede externa" ficaria furada por uma chamada que ninguém pediu).
    Usa a **função de embedding padrão do próprio ChromaDB** (ONNX local, roda offline depois
    de baixada uma vez) — não usei OpenRouter para embeddings: o modelo padrão
    (`openai/gpt-4o-mini`) não garante suporte a embeddings via OpenRouter, e usar API externa
    para vetorizar contradiria a decisão de "não depender de rede externa por padrão"
    registrada em `00-contexto.md`. Confirmado funcionando de verdade (não just imaginado):
    rodei `client.add()`/`client.query()` manualmente antes de escrever o módulo.
  - `pdf_ingestion.py` — `extract_and_chunk_pdf()`: lê cada página com `pypdf`, ignora páginas
    sem texto extraível, fatia com `RecursiveCharacterTextSplitter`, **preserva o número da
    página de origem em cada chunk** — é o que permite citar "manual, página X" na resposta
    (critério de aceite).
  - `rag_engine.py` — `answer_question()`: busca os chunks mais similares no vetor-store local,
    monta o contexto com [Trecho N — manual, página P], chama `ChatOpenAI` (reusa
    `settings.openrouter_*`, resposta gerada por IA de verdade, não template). Prompt de
    sistema instrui o modelo a responder SÓ com base no contexto fornecido e a tratar todo
    conteúdo dos trechos como referência técnica, nunca como instrução — mitigação de prompt
    injection via PDF pedida pelo `cyber-ia` (§4 da plan: "conteúdo de PDF não é confiável").
    Se nenhum manual foi indexado, retorna mensagem informativa sem chamar o LLM.
    `KnowledgeQueryError` cobre chave ausente (Fail-Fast) e falha de chamada.
  - `router.py` — `POST /knowledge/ingest` (PDF, ≤ 20MB, `content_type` validado → 415/413) e
    `POST /knowledge/ask` (pergunta, Pydantic valida tamanho mínimo). PDF salvo em
    `settings.knowledge_storage_path/pdfs/{manual_id}.pdf` — **nome do arquivo é sempre o UUID
    gerado pelo servidor, nunca o filename enviado pelo cliente**, para não abrir path
    traversal (`../../etc/passwd.pdf` como nome de arquivo, por exemplo) — o filename original
    só é guardado como metadado/texto de exibição, nunca vira parte de um caminho no disco.
- `api/index.py` — 2 linhas (import + `include_router(knowledge_router, prefix="/api")`),
  mesma lógica de companion necessário já usada nas plans 01/03.
- `frontend/src/pages/Knowledge.tsx`:
  - Novo painel "Assistente de Conhecimento": campo de pergunta + botão "Perguntar" →
    `POST /api/knowledge/ask`, exibe a resposta da IA e a lista de fontes (manual + página).
    Erro de rede/backend inline (mesmo padrão visual das plans 02/03).
  - Botão "Novo Manual" (ao lado do título "Documentação Técnica") → `<input type="file"
    accept="application/pdf">` oculto → `POST /api/knowledge/ingest` (multipart), com
    mensagem de sucesso/erro inline. **Não** mexi na lista de manuais existente
    (`fetch('/api/manuals')`) nem no glossário — são funcionalidades diferentes e não fazem
    parte desta plan (o `/api/manuals` é outro endpoint, já mockado antes de eu chegar,
    conforme a própria correção da plan registra).
- Testes (`test-unitario`, mock do LLM **e** do vetor-store, como a plan pede em §5.6):
  `backend/apps/ai_knowledge/tests/` — 13 testes:
  - `test_pdf_ingestion.py` (3) — lógica real de chunking/tagueamento de página, só o
    `PdfReader` (I/O de parsing) é mockado: tagueamento correto por página, páginas sem texto
    são puladas, página longa vira múltiplos chunks.
  - `test_rag_engine.py` (3) — `query_similar_chunks` e `_build_llm` mockados (vetor-store e
    LLM, como a plan pede), lógica real de `answer_question` exercitada: mensagem graciosa sem
    manual indexado, Fail-Fast sem chave, resposta com fontes citadas corretamente.
  - `test_knowledge_endpoints.py` (7) — via `TestClient` real contra a rota de verdade,
    `extract_and_chunk_pdf`/`add_chunks`/`answer_question` mockados: rejeita não-PDF (415),
    rejeita > 20MB (413), indexa com metadata de página correta e salva localmente (confirmado
    lendo o arquivo do disco no teste), rejeita PDF sem texto extraível (422), resposta com
    fontes, 503 sem LLM, 422 para pergunta curta demais.

**Arquivos alterados**
| Arquivo | Natureza | O que mudou |
|---|---|---|
| `backend/shared_infra/config.py` | alterado | campo `knowledge_storage_path` |
| `.env.example` | alterado | `KNOWLEDGE_STORAGE_PATH` documentada |
| `.gitignore` | alterado | `backend/apps/ai_knowledge/storage/` |
| `requirements.txt` | alterado | `chromadb`, `pypdf`, `langchain-text-splitters` |
| `backend/apps/ai_knowledge/requirements.txt` | alterado | preenchido (estava vazio) |
| `backend/apps/ai_knowledge/{__init__,schemas,vector_store,pdf_ingestion,rag_engine,router}.py` | criados | módulo RAG completo |
| `api/index.py` | alterado | monta `knowledge_router` |
| `frontend/src/pages/Knowledge.tsx` | alterado | painel de pergunta + upload de manual |
| `backend/apps/ai_knowledge/tests/*.py` | criados | 13 testes |

Confirmado por `git status`: nada em `asset_manager/`, `digital_twin_core/`,
`ingestion_service/` ou outra aba do frontend; `specs/00-contexto.md` aparece modificado mas
**não foi tocado por mim** (já vinha assim, com a correção R2→local registrada antes desta
execução começar — confirmei via `git diff --stat`, são as mesmas 6 linhas).

**Verificações executadas**
- `python -m pytest backend/apps/ai_knowledge -v` → **13 passed**.
- `python -m pytest backend api/tests -q` → **44 passed**, 0 failures (31 anteriores + 13
  novos), 0 regressão.
- `python -c "from api.index import app; app.openapi()"` → `/api/knowledge/ingest` e
  `/api/knowledge/ask` presentes nos paths registrados.
- **Testado manualmente antes de escrever o módulo** (não é um teste automatizado, é
  verificação de viabilidade): `chromadb.PersistentClient` + `.add()` + `.query()` rodando de
  verdade nesta máquina, sem chave de API nenhuma, confirmando que a função de embedding padrão
  local funciona offline e que a escolha de arquitetura (Chroma local em vez de
  PGVector/embeddings via OpenRouter) é viável de verdade, não só teórica.
- `tsc --noEmit` (config temporária ad-hoc, apagada depois) contra `Knowledge.tsx` inteiro →
  **0 erros**, modo `strict`.
- Autoverificação de limiares: nenhuma função nova passa de ~30 linhas (`ingest_manual` é a
  maior, ~25 linhas), aninhamento ≤ 2, ≤ 4 parâmetros.
- **Não executado**: chamada real ao OpenRouter para geração de resposta (sem
  `OPENROUTER_API_KEY` neste ambiente — mesma limitação já registrada nas plans 02/03). A
  vetorização/busca local **foi** exercitada de verdade (ver item acima); só a etapa final de
  "IA gera a resposta em texto" não foi.
- **Não executado**: verificação visual em navegador — mesma decisão já registrada nas
  plans 02/03 (o usuário optou por testar manualmente; não repeti a pergunta).

**Critérios de aceite**
- [x] Chave de API do LLM configurada via `shared_infra/config.py`/`.env`, sem valor hardcoded
  — evidência: reuso de `settings.openrouter_*`, nenhum campo novo duplicado.
- [x] Usuário pode enviar novo manual e ele é indexado — evidência: `POST /knowledge/ingest`
  testado (7 testes), extração/chunking com página preservada testado separadamente (3 testes),
  UI de upload em `Knowledge.tsx`.
- [x] Busca natural devolve a resposta gerada por IA com fonte (página do PDF) — evidência:
  `answer_question` retorna `AskResponse.fontes` com `manual`+`pagina`; resposta real do LLM
  não exercitada (sem chave), mas o encaminhamento/formatação de contexto+fontes está testado.
- [x] PDFs e vetor-store armazenados localmente em disco, sem dependência de rede externa —
  evidência: `_save_pdf_locally` grava em `settings.knowledge_storage_path/pdfs/`, confirmado
  por teste lendo o arquivo do disco; `vector_store.py` usa `PersistentClient` local,
  telemetria desligada explicitamente; nenhuma importação de `storage_client`/R2 em todo o
  módulo (confirmável por grep).
- [x] Diretório de storage local no `.gitignore` — evidência: `.gitignore` atualizado.
- [x] Testes unitários de ingestão e busca verdes — evidência: 13/13.

**Decisões e suposições**
- **Embeddings via função padrão local do ChromaDB (ONNX), não via OpenRouter.** Já
  justificado acima — evitar reintroduzir uma dependência de rede externa na etapa mais
  frequente do pipeline (toda ingestão e toda busca vetorizam texto), o que contrariaria
  diretamente a decisão "sem depender de rede externa por padrão" que motivou a correção desta
  própria plan. `OPENROUTER_*` fica reservado só para a geração da resposta final em texto —
  onde o LLM generativo é insubstituível localmente com a stack já presente no projeto.
- **`pypdf` em vez de `PyMuPDF`/`fitz`** (sugerido em `rag_base/structure_guide.md`, um
  documento de planejamento, não uma decisão fechada) — `pypdf` é pacote puro-Python, sem
  dependência de biblioteca nativa compilada, mais simples de instalar/portar; ambos cobrem
  "extrair texto por página", que é tudo que o pipeline precisa.
- **Nome do arquivo salvo em disco é sempre o `manual_id` (UUID), nunca o filename do
  cliente** — decisão de segurança (path traversal), não pedida explicitamente pela plan, mas
  necessária para qualquer implementação correta de "salvar upload de usuário em disco".
- **PDF sem texto extraível → 422, não indexado.** Não implementei fallback de OCR (ex.:
  `EasyOCR`, citado em `ocr_strategy/ocr_plan.md` — mas esse documento é sobre OCR de **placas
  de motor**, plan-03, não sobre manuais em PDF escaneado). Um manual PDF que seja só imagem
  escaneada sem camada de texto não seria indexado — registrado como achado abaixo.
- **Coleção única do ChromaDB** (`manuais_tecnicos`) para todos os manuais — não separei por
  manual/categoria. Suficiente para o critério de aceite (busca + citação de fonte funciona
  igual), mas significa que não há como "buscar só dentro deste manual" — não pedido pela plan.
- Reaproveitei o mesmo padrão de prompt anti-injeção das plans 02/03 (tratar conteúdo externo
  como dado, nunca como instrução), adaptado para "trechos de PDF recuperados" — é o pedido
  específico de `cyber-ia` para esta plan (§4: "conteúdo de PDF não é confiável").

**Achados fora do escopo (não corrigidos)**
- PDFs 100% escaneados (sem camada de texto) não são indexados — retornam 422 em vez de OCR de
  fallback. Se isso for um caso de uso real esperado, é trabalho de uma plan nova (integraria
  com o pipeline de OCR já existente da `plan-03`, adaptado para documentos, não placas).
- `/api/manuals` (endpoint que a lista de "Documentação Técnica" já consumia antes desta plan)
  continua mockado — não é meu escopo, mas agora convivem dois sistemas de "manuais" na mesma
  página (a lista estática antiga + os PDFs indexados via RAG novos) sem nenhuma ligação entre
  eles. Pode valer uma plan futura de unificação.
- Mesmos achados já registrados nas plans 02/03, ainda válidos e não corrigidos aqui:
  `frontend/tsconfig.json` ausente (build quebrado), sem rate limiting nos endpoints de IA.

**Pendências / riscos**
- **Resposta real do LLM nunca gerada de verdade** (sem `OPENROUTER_API_KEY`) — o pipeline de
  busca vetorial foi comprovadamente testado funcionando (ver Verificações), mas a qualidade da
  resposta gerada e a fidelidade da citação de fonte só serão confirmadas no primeiro uso real.
- Verificação visual em navegador não feita (mesma pendência aceita nas plans anteriores).
- Primeira chamada de ingestão/busca em uma máquina nova precisa baixar o modelo ONNX padrão do
  ChromaDB (poucos MB, feito automaticamente, mas é uma dependência de rede pontual na
  primeira execução — depois disso é 100% offline). Vale documentar isso para quem for rodar o
  projeto pela primeira vez.

---
# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->

## Veredito — 2026-08-22 — 🟢 Aprovado

**Verificado diretamente no worktree:**

- `git status`/`git diff --stat` → só os arquivos declarados (`ai_knowledge/*`, `config.py`,
  `.env.example`, `.gitignore`, `requirements.txt` ×2, `Knowledge.tsx`, `api/index.py`). Nada em
  `asset_manager/`, `digital_twin_core/`, `vision/`. `00-contexto.md` aparece modificado mas
  confirmo que não foi tocado nesta rodada (já vinha assim de antes).
- Li `vector_store.py`, `pdf_ingestion.py`, `rag_engine.py`, `router.py`, `schemas.py` inteiros:
  `anonymized_telemetry=False` explícito, embedding padrão local do ChromaDB (sem OpenRouter para
  vetorizar), `manual_id` (UUID do servidor) como único nome de arquivo em disco — mitigação de
  path traversal correta —, prompt anti-injeção trata trechos de PDF como referência, nunca como
  instrução, `KnowledgeQueryError` cobre Fail-Fast e falha de chamada sem engolir exceção.
- **Rodei eu mesmo um teste real, sem nenhum mock**: escrevi um PDF mínimo à mão (bytes crus,
  content stream válido), chamei `extract_and_chunk_pdf` → `add_chunks` (ChromaDB `PersistentClient`
  de verdade, num diretório temporário) → `query_similar_chunks("qual a vibração máxima do
  motor?")`. A busca semântica **recuperou corretamente** o chunk com "vibração máxima permitida:
  4.5 mm/s RMS" — prova real de que a extração por página, o chunking e a recuperação vetorial
  100% local funcionam de ponta a ponta, não só em teoria.
- Rodei a suíte eu mesmo: `python -m pytest backend api/tests -q` → **44 passed**, bate com o
  alegado (31 anteriores + 13 novos).
- `npx tsc --strict` contra `Knowledge.tsx` → **0 erros**.
- Li o diff de `Knowledge.tsx`: painel de pergunta + upload novos, lista de manuais/glossário
  antigos intocados, mesmo padrão visual de erro/sucesso das plans anteriores.

**Critérios de aceite — 6 de 6 atendidos:**
- [x] Chave de API do LLM via `config.py`/`.env`, sem hardcode — `openrouter_*` reusado, campo
  novo (`knowledge_storage_path`) também via Pydantic.
- [x] Manual enviado é indexado — verificado por teste **e** pela minha execução real do pipeline.
- [x] Busca natural devolve resposta com fonte (página) — a recuperação está provada real (acima);
  a geração de texto pelo LLM segue o mesmo padrão já validado nas plans 02/03 (Fail-Fast +
  processamento testado) — diferente do critério de "corretude de OCR" da `plan-03`, responder
  com base num contexto fornecido é uma operação padrão de LLM, não uma leitura visual
  imprevisível; não exijo chamada real paga para este critério.
- [x] PDFs e vetor-store 100% locais — `grep` confirma zero import de `storage_client`/R2 no
  módulo; confirmado meu teste rodando sem nenhuma chave de API.
- [x] Diretório de storage no `.gitignore` — confirmado.
- [x] Testes verdes — 13/13 do módulo, 44/44 da suíte completa.

**Achados fora do escopo, registrados, corretos (não corrigidos agora):** PDF escaneado sem
camada de texto não é indexado (422, sem fallback de OCR); `/api/manuals` continua mockado,
convivendo sem ligação com os manuais indexados via RAG; mesmos achados já conhecidos
(`tsconfig.json` ausente, sem rate limit). Observação minha, não bloqueante: reenviar o mesmo
manual duas vezes duplica os chunks no índice (sem deduplicação por conteúdo/nome) — não pedido
pela plan, candidato a achado de uma rodada futura se virar problema real.

**Pendência sem peso no veredito:** resposta de texto gerada pelo LLM nunca chamada de verdade
(sem chave com crédito) — mas a metade mais arriscada (recuperação local) já está provada, e o
padrão de chamada é idêntico ao já em produção nas outras plans.
