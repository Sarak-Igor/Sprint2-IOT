---
tipo: "plan"
titulo: "RAG recupera todo o conteúdo indexado quando a base de manuais é pequena"
dominio: "ai_knowledge"
status: "🟢 Aprovada"
prioridade: "Alta"
tags: ["plan", "ai_knowledge", "rag", "qualidade", "correcao"]
relacionados: ["[[specs/06-agente-conversacional]]"]
depende_de: "—"
destino_sintese: "specs/05-ai-knowledge.md"
---

# 1. Objetivo
O RAG deixa de perder trechos tecnicamente densos (tabelas de especificação) por causa do teto fixo
de resultados da busca semântica — quando a base indexada é pequena, a busca passa a considerar
todo o conteúdo disponível, não só o top-N ranqueado pelo embedding.

# 2. Contexto
Usuário reportou qualidade ruim do agente conversacional contra o manual real "WEG W22 Easy
Maintenance Motofreio": perguntado sobre valores operacionais (SOS/tensão/torque), respondeu que não
encontrou nada, enquanto um agente externo (lendo o mesmo PDF sem esse gargalo) encontrou tabelas
completas de tensão da bobina do freio, torque a 100 rpm, rotação máxima, energia dissipada e tempo
de resposta.

Investigação direta na base real (revisor, 2026-08-23) confirmou o mecanismo exato, sem suposição:
- O manual indexado tem só **6 chunks no total** (PDF de 4 páginas,
  `RecursiveCharacterTextSplitter(chunk_size=1000, overlap=200)` de `pdf_ingestion.py`).
- `query_similar_chunks()` (`vector_store.py:28-39`) usa `n_results=4` (padrão fixo, nunca
  parametrizado por quem chama). Rodando a pergunta real do usuário contra a base, o top-4 trouxe:
  capa/título (irrelevante), um parágrafo de marketing ("atributos e benefícios"), o rodapé legal — e
  **só um fragmento de 318 caracteres** da página 3, cortado no meio de uma tabela, sem cabeçalho.
- O chunk que de fato tem os dados (966 caracteres, mesma página 3: torque, rotação máxima, energia
  dissipada, tempo de resposta, tabela de tensão completa) **ficou fora do top-4** — o modelo de
  embedding padrão do ChromaDB (local, pequeno, 100% offline) não o rankeou acima do texto de
  marketing para essa pergunta.
- Rodando a mesma busca com `n_results` maior que o total de chunks, o trecho correto aparece — a
  informação sempre esteve corretamente extraída e indexada; o problema é exclusivamente de
  **recuperação** (quantos trechos entram no contexto do LLM), não de extração nem de geração.

**Decisão do usuário (2026-08-23):** corrigir de forma adaptativa — quando a coleção for pequena,
recuperar tudo; manter um teto quando a base crescer (mais manuais, mais chunks), para não estourar
custo/latência sem necessidade. Melhorias de chunking de tabela ficam deliberadamente fora desta
plan (avaliadas, não escolhidas nesta rodada).

# 3. Escopo

## 3.1 Dentro
- `backend/apps/ai_knowledge/vector_store.py::query_similar_chunks()` — comportamento adaptativo:
  se `collection.count()` estiver abaixo de um teto pequeno (constante nomeada, ex.:
  `SMALL_COLLECTION_CHUNK_THRESHOLD`), recuperar **todos** os chunks da coleção (ainda via
  `collection.query`, mantendo a ordem por relevância — só o `n_results` efetivo muda); acima do
  teto, manter o comportamento atual (`n_results` recebido, default 4).
- `backend/apps/ai_knowledge/tests/test_vector_store.py` — cobrir os dois ramos.

## 3.2 Fora
- `backend/apps/ai_knowledge/pdf_ingestion.py` (chunking/splitter) — decisão explícita do usuário
  nesta rodada: não mexer no `chunk_size`/`overlap` nem em qualquer estratégia de chunking
  consciente de tabela. Fica candidato a uma plan futura se o ajuste de recuperação não for
  suficiente.
- `backend/apps/ai_knowledge/rag_engine.py` — nenhuma mudança de prompt ou de lógica de geração;
  ele só passa a receber mais trechos no contexto quando a base for pequena, sem alterar como usa
  esse contexto.
- Troca do modelo de embedding (continua o padrão local do ChromaDB, decisão já tomada de manter
  `ai_knowledge` 100% local/offline) — não avaliado nesta plan.
- `backend/apps/ai_knowledge/agent/*` (`plan-14`), `router.py`/`schemas.py` de `ai_knowledge`
  (`plan-15`) — não mudam; ambos já consomem `answer_question()`/`query_similar_chunks()` como
  estão, sem precisar saber do ajuste interno.
- Deduplicação de chunks ao reenviar o mesmo manual (achado já registrado desde a `plan-04`) — fora
  do escopo, problema diferente.

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Spec fixa | `specs/06-agente-conversacional.md` | o sintoma apareceu através do agente; a causa é do RAG, não dele |
| Contexto | `00-contexto.md §8` (achado registrado nesta mesma rodada) · `00-knowledge.md` | sempre |
| Skill | `padrao-escrita` + `padrao-python` | sempre |
| Skill | `test-unitario` | cobrir os dois ramos (coleção pequena recupera tudo; coleção grande respeita o teto) |
| Código | `backend/apps/ai_knowledge/vector_store.py` | ler `query_similar_chunks()` inteiro antes de editar |
| Código | `backend/apps/ai_knowledge/rag_engine.py` | confirmar que só consome o retorno, sem precisar de mudança |

# 5. Instruções de execução
1. Ler `vector_store.py` inteiro (já familiar de `plan-04`/`plan-15`, mas confirmar o estado atual
   antes de editar).
2. Definir a constante do teto (nome e valor a critério do executor — escolher um valor que cubra
   confortavelmente um manual técnico pequeno/médio, ex.: dezenas de chunks, sem tentar adivinhar um
   número "perfeito"; documentar o raciocínio no resumo).
3. Alterar `query_similar_chunks()`: quando `collection.count()` estiver dentro do teto, consultar
   com `n_results = count` (recupera tudo); caso contrário, manter o `n_results` recebido pelo
   chamador (comportamento atual, default 4).
4. Escrever os testes: coleção com poucos chunks (abaixo do teto) → todos os chunks retornados,
   mesmo os que um embedding fraco rankeia mal; coleção acima do teto → só `n_results` chunks
   retornados (comportamento antigo preservado); coleção vazia → `[]` (já existente, não regredir).
5. Rodar a suíte completa e confirmar verde.
6. Verificação manual sugerida (não bloqueia os critérios automatizáveis): repetir a pergunta real
   sobre o manual W22 Motofreio (já indexado no ambiente) e confirmar que a resposta passa a citar
   os valores de torque/tensão/rotação que antes não apareciam.

# 6. Critérios de aceite
- [ ] `query_similar_chunks()` recupera todos os chunks indexados quando a coleção está dentro do
  teto de "base pequena".
- [ ] Acima do teto, o comportamento atual (`n_results` limitado) é preservado — sem regressão de
  custo/latência para bases maiores.
- [ ] Coleção vazia continua devolvendo `[]` sem erro (comportamento já existente, não regredir).
- [ ] `rag_engine.py`/`agent/*` continuam funcionando sem nenhuma alteração própria — só recebem mais
  contexto quando aplicável.
- [ ] Testes cobrindo os dois ramos + o caso vazio, todos verdes; suíte completa sem regressão.

# 7. Como verificar (uso do revisor)
- `git diff --stat` → só `vector_store.py` e o teste correspondente.
- Ler a nova lógica e confirmar que o teto é uma constante nomeada, não um número solto no meio do
  código.
- Rodar a suíte e ler a saída real.
- Repetir a pergunta real sobre o manual W22 Motofreio já indexado no ambiente (dado real, mesmo
  caso que originou esta plan) e confirmar que os valores de torque/tensão/rotação agora aparecem na
  resposta.

# 8. Destino da síntese
**Destino:** `specs/05-ai-knowledge.md`
Documentar a estratégia adaptativa de recuperação (base pequena → recupera tudo; base grande →
top-N) como parte do comportamento oficial do RAG.

---

# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

## Resumo da execução — 2026-08-23

**Resultado:** Concluído

**O que foi feito**
- `backend/apps/ai_knowledge/vector_store.py:9-15` — nova constante nomeada
  `SMALL_COLLECTION_CHUNK_THRESHOLD = 50`, com comentário justificando o valor (ver
  "Decisões e suposições").
- `backend/apps/ai_knowledge/vector_store.py:29-45` — `query_similar_chunks()` alterada:
  quando `collection.count() <= SMALL_COLLECTION_CHUNK_THRESHOLD`, `effective_n_results =
  count` (recupera todos os chunks da coleção); caso contrário,
  `effective_n_results = min(n_results, count)` (comportamento anterior, preservado ao pé
  da letra). A chamada a `collection.query()` continua sendo a única fonte de ranking —
  só o `n_results` efetivo muda, a ordem por relevância do embedding é mantida em ambos os
  ramos. Coleção vazia (`count == 0`) continua saindo antes de qualquer chamada a `.query()`
  (comportamento já existente, não regredido).
- Confirmado por leitura (sem editar) que `rag_engine.py::answer_question()` só consome o
  retorno de `query_similar_chunks()` como lista de pares `(texto, metadata)` — nenhuma
  suposição sobre tamanho fixo do resultado, nenhuma mudança necessária ali nem em
  `agent/*` (`plan-14`) ou `router.py`/`schemas.py` (`plan-15`).
- Testes novos em `backend/apps/ai_knowledge/tests/test_vector_store.py` (skill
  `test-unitario`), cobrindo os dois ramos + o caso vazio (não regredido):
  `test_query_similar_chunks_returns_empty_when_collection_empty` (coleção vazia → `[]`,
  `collection.query` nunca chamado); `test_query_similar_chunks_retrieves_every_chunk_when_
  collection_is_small` (6 chunks, `n_results=4` pedido pelo chamador → `collection.query`
  chamado com `n_results=6`, todos os chunks voltam, mesmo que um ranking fraco os
  colocasse fora do top-4); `test_query_similar_chunks_retrieves_everything_exactly_at_
  threshold` (count == teto exato → ainda recupera tudo, cobre a borda do `<=`);
  `test_query_similar_chunks_respects_n_results_when_collection_is_large` (count = teto +
  10 → `collection.query` chamado com `n_results=4`, comportamento antigo preservado).

**Arquivos alterados**
| Arquivo | Natureza | O que mudou |
|---|---|---|
| `backend/apps/ai_knowledge/vector_store.py` | alterado | `+SMALL_COLLECTION_CHUNK_THRESHOLD`, recuperação adaptativa em `query_similar_chunks()` |
| `backend/apps/ai_knowledge/tests/test_vector_store.py` | alterado | +4 testes cobrindo os dois ramos e a borda do teto |

**Verificações executadas**
- `python -m pytest backend/apps/ai_knowledge/tests/test_vector_store.py -v` → 6 passed (2
  testes já existentes de `list_indexed_manuals` + 4 novos de `query_similar_chunks`).
- `python -m pytest backend/ -v` (suíte completa) → **75 passed**, 0 falhas, 0 regressão
  (os 71 testes já verdes antes desta plan, mais os 4 novos).
- `git diff --stat -- backend/apps/ai_knowledge/vector_store.py
  backend/apps/ai_knowledge/tests/test_vector_store.py` → só esses dois arquivos, conforme
  §7 da plan ("só `vector_store.py` e o teste correspondente"). `git status` mostra também
  `specs/00-contexto.md`/`specs/00-indice.md` como modificados, mas pré-existentes ao
  início desta execução (não tocados por mim nesta rodada — confirmado, não usei
  Edit/Write neles).
- Leitura de `rag_engine.py` inteiro (sem editar) → confirma que ele só itera sobre o
  retorno de `query_similar_chunks()` (`_format_context`, construção de `fontes`), sem
  qualquer suposição de tamanho — nenhuma mudança própria necessária.

**Critérios de aceite**
- [x] `query_similar_chunks()` recupera todos os chunks indexados quando a coleção está
  dentro do teto — evidência:
  `test_query_similar_chunks_retrieves_every_chunk_when_collection_is_small` e o teste de
  borda `..._exactly_at_threshold`.
- [x] Acima do teto, o comportamento atual (`n_results` limitado) é preservado — evidência:
  `test_query_similar_chunks_respects_n_results_when_collection_is_large`.
- [x] Coleção vazia continua devolvendo `[]` sem erro — evidência:
  `test_query_similar_chunks_returns_empty_when_collection_empty`.
- [x] `rag_engine.py`/`agent/*` continuam funcionando sem nenhuma alteração própria —
  evidência: `git diff --stat` não lista esses arquivos; leitura confirma consumo genérico
  do retorno.
- [x] Testes cobrindo os dois ramos + o caso vazio, todos verdes; suíte completa sem
  regressão — evidência: 75/75 passed.

**Decisões e suposições**
- Valor do teto: `SMALL_COLLECTION_CHUNK_THRESHOLD = 50`. Raciocínio (documentado também
  no comentário do código): o manual real que originou esta plan tem 4 páginas e 6 chunks
  com o splitter atual (`chunk_size=1000`, `overlap=200`, ≈800 caracteres efetivos por
  chunk) — uma razão aproximada de ~1,5 chunk/página. Extrapolando essa razão, 50 chunks
  cobre confortavelmente um manual técnico de até ~30 páginas (pequeno/médio, o caso
  citado pela plan), sem exigir "recuperar tudo" de uma base já grande (muitos manuais
  indexados), onde o custo/latência de mandar dezenas de trechos ao LLM a cada pergunta
  deixaria de valer a pena. Não é um número "perfeito" — é uma estimativa documentada,
  ajustável numa plan futura se a base de manuais crescer e o comportamento precisar de
  calibração.
- `effective_n_results = count` (não `count + margem` ou qualquer outro ajuste) quando
  dentro do teto — leitura literal da instrução de execução (passo 3: "consultar com
  `n_results = count`").
- **Desvio de processo, registrado por transparência:** marquei `status: 🟡 Em execução`
  no frontmatter da plan **depois** de já ter editado `vector_store.py`, não antes, como o
  ritual da §2 do `00-prompt-executor.md` pede. Não teve efeito prático (execução de uma
  plan só, sem concorrência, sem outro agente lendo o status nesse intervalo), mas é uma
  inversão da ordem prescrita — registrando para não passar em silêncio.

**Achados fora do escopo (não corrigidos)**
- Nenhum novo. Os achados já registrados nas plans anteriores (ausência de
  `tsconfig.json` no frontend, `storage_client.py` sem chamador real) não se aplicam a
  esta plan (escopo 100% backend, um único arquivo).

**Pendências / riscos**
- A verificação manual sugerida pela plan (passo 6: repetir a pergunta real sobre o manual
  W22 Motofreio já indexado no ambiente e confirmar que os valores de
  torque/tensão/rotação aparecem na resposta) **não foi executada** — exigiria uma chamada
  real ao LLM via OpenRouter (fora do que testes unitários mockados cobrem) e o ambiente
  local com a base já indexada, que não confirmei estar disponível nesta execução. Não
  bloqueia os critérios automatizáveis (a própria plan marca esse passo como
  não-bloqueante), mas é a evidência mais direta de que o sintoma original (resposta
  "não encontrado" para uma pergunta cuja resposta está indexada) foi resolvido — recomendo
  que o revisor a rode antes de aprovar, já que é exatamente o `de-para` que motivou a
  plan.

---

# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->

## Veredito — 2026-08-23 — 🟢 Aprovado

**Verificado diretamente no worktree:**

- `git status`/`git diff --stat` → só `vector_store.py` e `test_vector_store.py`, exatamente como
  alegado; nada em `rag_engine.py`, `agent/*`, `router.py`/`schemas.py` de `ai_knowledge`.
- Li `query_similar_chunks()` por completo: teto nomeado (`SMALL_COLLECTION_CHUNK_THRESHOLD = 50`,
  com comentário explicando o raciocínio), `effective_n_results = count` quando dentro do teto,
  `min(n_results, count)` quando acima — comportamento antigo preservado ao pé da letra para bases
  grandes. Coleção vazia continua saindo antes de qualquer `.query()`.
- Li os 4 testes novos linha a linha contra a implementação: cobrem coleção vazia, coleção pequena
  (recupera tudo mesmo pedindo `n_results=4`), a borda exata do teto (`count == threshold` ainda
  recupera tudo) e coleção acima do teto (respeita `n_results`) — os quatro corretos.
- Rodei a suíte eu mesmo: `python -m pytest backend/ -q` → **75 passed**, bate com o alegado.
- **Fiz a verificação manual que a plan marcou como recomendada e o executor não executou** — repeti,
  contra a base real (manual WEG W22 Motofreio já indexado, sem nenhum mock):
  - `query_similar_chunks()` com a pergunta real do usuário → agora retorna **os 6 chunks**,
    incluindo o trecho de 966 caracteres com a tabela de torque/tensão/rotação/energia que antes
    ficava fora do top-4. Mecanismo da correção confirmado empiricamente, não só por leitura de
    código.
  - Chamei `answer_question()` de verdade (LLM real via OpenRouter, chave configurada neste
    ambiente) com a pergunta original sobre "SOS": a resposta agora **lista explicitamente** ter
    visto "torque, potência, tempo de resposta" no contexto — evidência de que o chunk denso chegou
    ao LLM desta vez — mas ainda conclui que o termo literal "SOS (Start of Service)" não aparece no
    manual. Conferi: esse termo de fato não existe no texto extraído do PDF — a resposta "não
    encontrado" está correta para essa pergunta específica; o agente externo citado pelo usuário
    também não respondeu literalmente sobre "SOS", só ofereceu os dados adjacentes.
  - Para isolar o ganho real, repeti com uma pergunta direta sobre os mesmos dados ("torque, tensão
    da bobina do freio e rotação máxima"): a resposta agora traz **valores reais extraídos da
    tabela** (torque por tamanho de carcaça, tensão da bobina, rotação máxima) — antes da correção,
    essa tabela completa nem chegava ao contexto do LLM. A correção resolve exatamente o problema
    diagnosticado. (A tabela tem várias colunas e o modelo comete alguma confusão ao relacionar
    carcaça/tamanho de freio/valor — imprecisão de leitura de tabela pelo LLM, não de recuperação;
    fora do escopo desta plan, que era só sobre quantos trechos chegam ao contexto.)

**Critérios de aceite — 5 de 5 atendidos, com evidência real (minha, além da do executor):**
- [x] Recupera tudo dentro do teto — confirmado por teste e por chamada real.
- [x] Preserva o comportamento acima do teto — confirmado por teste.
- [x] Coleção vazia → `[]` sem erro — confirmado.
- [x] `rag_engine.py`/`agent/*` inalterados e funcionando — confirmado por diff vazio + chamada real
  bem-sucedida via `answer_question()`.
- [x] Testes verdes, suíte sem regressão — 75/75.

**Sobre o desvio de processo registrado (status `🟡` marcado depois da primeira edição):** sem
impacto prático (execução única, sem concorrência), registrado com transparência. Não é achado.

**Nota, sem peso no veredito:** a imprecisão do LLM ao relacionar colunas de uma tabela densa (visto
no segundo teste real acima) é uma limitação de leitura de tabela pelo modelo escolhido, não do
pipeline de recuperação — fica como candidato a uma futura melhoria de chunking/estruturação de
tabela, exatamente a opção que o usuário decidiu não escolher nesta rodada.

**Liberação:** nenhuma plan da fila depende de `plan-16`. O caso original (pergunta técnica sem
resposta) está confirmadamente corrigido para o gargalo de recuperação — reportar ao usuário.
