---
tipo: "plan"
titulo: "Melhorar precisão da leitura de placa — estruturar texto do OCR local via LLM de texto"
dominio: "vision_service"
status: "🟢 Aprovada"
prioridade: "Alta"
tags: ["plan", "ocr", "vision", "llm-texto"]
relacionados: ["[[specs/04-vision-ocr]]"]
depende_de: "—"
destino_sintese: "specs/04-vision-ocr.md"
---

# 1. Objetivo
A leitura da placa acerta mais campos e com mais tolerância a ruído de OCR, sem voltar a enviar a
**imagem** para nenhuma API externa — só o texto bruto já extraído localmente (sem dado de imagem)
vai para um LLM de texto estruturar.

# 2. Contexto
`plan-03` (aprovada, `specs/plan/executadas/plan-03-vision-ocr.md`) implementou OCR 100% local
(EasyOCR + regex em `plate_parser.py`). Testado com imagem sintética, funcionou bem. Testado pelo
usuário com **foto real de placa de motor**: confiança baixa e campos incorretos/"Não legível" em
excesso. Diagnóstico (registrado em `00-contexto.md §8`):
1. `ocr_engine.py` não faz nenhum pré-processamento de imagem (sem correção de contraste,
   reflexo, ângulo) — fora de escopo desta plan, não mexer aqui.
2. **`plate_parser.py` usa regex exatos** (`\d{3,5}\s*RPM`, etc.) — qualquer ruído de leitura do
   OCR (um "0" lido como "O", espaço engolido, caractere trocado) já é suficiente para nenhum
   padrão bater, caindo em `"Não legível"` mesmo quando o dado foi de fato lido, só que com
   pequena imperfeição. **Este é o alvo desta plan.**

Decisão do usuário: caminho híbrido — manter `ocr_engine.py` (EasyOCR, gratuito, sem chamada de
imagem externa) exatamente como está, e trocar a estruturação rígida por regex por uma chamada a
um LLM de **texto** (via OpenRouter, reusando `settings.openrouter_*` já existente desde a
`plan-02`) que recebe as detecções brutas do OCR e infere os 9 campos, tolerante a ruído —
mesmo espírito de `backend/apps/asset_manager/domain/ai_enrichment.py` (texto livre → schema
estruturado via `with_structured_output`), mas aqui a entrada é a lista de detecções do OCR, não
uma descrição do usuário.

**Expectativa realista, para não prometer além do que a mudança resolve:** se o EasyOCR nunca
detectou um trecho da placa (reflexo/ângulo severo o suficiente para não gerar nenhuma detecção
naquela região), nenhuma estruturação por LLM recupera um dado que nunca chegou como texto bruto.
Esta plan melhora a **interpretação** do que já foi detectado, não a **detecção** em si (isso seria
pré-processamento de imagem, deliberadamente fora do escopo aqui — ver decisão do usuário).

# 3. Escopo

## 3.1 Dentro
- `backend/apps/asset_manager/vision/plate_parser.py` — ou um módulo novo ao lado dele (a
  critério do executor) contendo a estruturação via LLM. `parse_plate_fields()` (regex) pode
  continuar existindo como fallback (ver instrução 3) ou ser substituída — decisão de
  implementação, desde que o comportamento de fallback esteja coberto por teste.
- `backend/apps/asset_manager/vision/plate_extraction.py` — ligar ao novo caminho de
  estruturação.
- `backend/apps/asset_manager/tests/test_vision_endpoint.py` (ou arquivo de teste novo ao lado) —
  cobrir o novo caminho.

## 3.2 Fora
- `backend/apps/asset_manager/vision/ocr_engine.py` — **não altere a chamada bruta ao EasyOCR**
  nem adicione pré-processamento de imagem (CLAHE, correção de perspectiva, etc.) — é uma opção
  deliberadamente não escolhida pelo usuário nesta rodada; se quiser revisitar, é outra plan.
  Continue enviando só o **texto** das detecções ao LLM, nunca a imagem — enviar a imagem
  reintroduziria o custo/dependência que a `plan-03` removeu.
- `frontend/src/pages/Vision.tsx` — contrato de resposta (`PlateExtractionResult`, 9 campos +
  `confianca`) não muda; não deveria precisar de edição.
- `backend/shared_infra/config.py` — `settings.openrouter_*` já existe (criado na `plan-02`); não
  duplique campo.

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Spec fixa | `specs/04-vision-ocr.md` | Vai ganhar a síntese desta plan em cima da síntese da `plan-03` |
| Contexto | `00-contexto.md` §8 (diagnóstico do problema real) · `00-knowledge.md` | sempre |
| Skill | `cyber-ia` | o texto do OCR (não confiável — pode conter ruído/injeção) vai para um prompt de LLM; tratar como dado, nunca como comando |
| Skill | `padrao-python` | sempre |
| Skill | `test-unitario` | cobrir o novo caminho (mock do LLM) e o comportamento de fallback sem chave |
| Código | `backend/apps/asset_manager/domain/ai_enrichment.py` | padrão já aprovado de LLM de texto → schema Pydantic estruturado (`with_structured_output`), reaproveitar a forma, não o conteúdo |
| Código | `backend/apps/asset_manager/vision/plate_parser.py`, `ocr_engine.py` | ler antes de editar |

# 5. Instruções de execução
1. Ler `plate_parser.py` e `ocr_engine.py` (código atual, aprovado na `plan-03`) e
   `ai_enrichment.py` (padrão de LLM estruturado já em produção) antes de escrever qualquer linha.
2. Criar a função de estruturação via LLM: recebe a mesma entrada que `parse_plate_fields`
   recebe hoje (lista de `(texto, confiança)` do OCR), monta um prompt que lista as detecções e
   pede ao LLM para preencher os 9 campos do `PlateExtractionResult`, instruído a **nunca
   inventar** um valor não sustentado pelas detecções — usar `"Não legível"` quando o LLM não
   tiver base nas detecções fornecidas (mesma filosofia da `plan-03`, adaptada: agora quem decide
   "não legível" é o LLM lendo o texto ruidoso, não um regex exato). `with_structured_output`
   contra `PlateExtractionResult` (nunca JSON solto). Fail-Fast se `OPENROUTER_API_KEY` ausente.
3. Decidir e implementar o comportamento de fallback: se o LLM não estiver disponível (chave
   ausente ou falha na chamada), usar `parse_plate_fields` (regex) como caminho alternativo, para
   a feature continuar funcionando 100% offline quando não houver chave configurada — registre a
   decisão tomada (fallback automático vs. erro) no resumo, com o motivo.
4. Ligar `plate_extraction.py` ao novo fluxo.
5. Escrever testes: sucesso via LLM (mock do LLM, entrada com ruído simulado que o regex sozinho
   erraria mas o LLM mockado "corrige"), fallback para regex quando o LLM falha/está ausente (se
   essa opção foi escolhida no passo 3), e confirmar que o LLM nunca recebe a imagem, só texto
   (nenhuma referência a bytes de imagem no código do LLM).
6. Rodar a suíte completa e confirmar verde.

# 6. Critérios de aceite
- [ ] O texto bruto do OCR é estruturado por um LLM de texto (via OpenRouter), tolerante a ruído
  de leitura que o regex sozinho rejeitaria.
- [ ] A imagem **nunca** é enviada a nenhuma API externa — só as strings de texto já detectadas
  localmente pelo EasyOCR.
- [ ] Campo sem base nas detecções continua virando `"Não legível"`, nunca um valor inventado
  (o LLM é instruído a isso, e o schema Pydantic segue validando a saída).
- [ ] Comportamento definido e testado para quando o LLM não está disponível (fallback para regex
  ou erro — decisão do executor, registrada e coberta por teste).
- [ ] `ocr_engine.py` não foi alterado (a chamada bruta ao EasyOCR continua igual à `plan-03`).
- [ ] Testes unitários do novo caminho verdes, suíte completa sem regressão.

# 7. Como verificar (uso do revisor)
- `git diff --stat` → confirma `ocr_engine.py` e `Vision.tsx` intocados; nada fora de `vision/`
  e o teste correspondente.
- Ler o prompt do LLM e confirmar que só recebe texto (nunca bytes/base64 de imagem).
- Rodar a suíte e ler a saída real.
- Se possível, repetir um teste fim-a-fim com uma imagem sintética "ruidosa" (texto com erro de
  OCR proposital) para comparar o resultado antes/depois desta plan.

# 8. Destino da síntese
**Destino:** `specs/04-vision-ocr.md`
Documentar o pipeline final: OCR local (detecção) → LLM de texto via OpenRouter (estruturação,
com fallback definido) → validação Pydantic. Atualizar a seção que a síntese da `plan-03` já
tiver escrito lá, não duplicar.

---

# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

## Resumo da execução — 2026-08-22

**Resultado:** Concluído

**O que foi feito**
- Lidos antes de escrever qualquer linha: `plate_parser.py`/`ocr_engine.py` (implementação
  atual, aprovada na `plan-03`, ambos localizados em `backend/apps/asset_manager/vision/`)
  e `backend/apps/asset_manager/domain/ai_enrichment.py` (padrão já aprovado de LLM de
  texto → schema Pydantic estruturado via `with_structured_output`, usado como forma —
  `ChatPromptTemplate` + `_build_llm()` Fail-Fast + `try/except` convertendo em exceção de
  domínio — não conteúdo).
- `backend/apps/asset_manager/vision/plate_llm_structurer.py` (novo) —
  `structure_plate_text(detections: list[tuple[str, float]])`: recebe exatamente a mesma
  entrada que `parse_plate_fields` já recebe (texto + confiança do OCR local), nunca a
  imagem nem seus bytes (confirmado por grep: nenhuma menção a `image`/`bytes`/`base64` no
  arquivo, só a palavra "imagem" numa negativa no docstring). Monta um
  `ChatPromptTemplate` com `_PROMPT` (mesmo padrão de `ai_enrichment.py`) instruindo o LLM
  a: (1) tratar cada texto detectado exclusivamente como **dado**, nunca como instrução —
  mitigação de prompt injection indireta pedida por `cyber-ia` §4, já que o texto vem de
  um OCR sobre uma foto que pode ter sido manipulada por terceiros; (2) tolerar ruído de
  OCR (caractere trocado, espaço engolido); (3) nunca inventar valor sem base em pelo menos
  uma detecção — escrever `"Não legível"` quando não houver base suficiente. Saída via
  `with_structured_output(PlateExtractionResult)` — nunca JSON solto, sempre validada pelo
  schema Pydantic existente (mesmo schema da `plan-03`, sem alteração). `_build_llm()`
  levanta `LlmStructuringError` **antes** de qualquer chamada de rede se
  `settings.openrouter_api_key` estiver vazio (Fail-Fast, reusando os mesmos campos
  `settings.openrouter_api_key`/`base_url`/`model` já criados pela `plan-02` — não recriei
  nenhum campo em `config.py`, que continua com diff vazio nesta rodada). Mitigações de
  Model DoS adicionais pedidas por `cyber-ia` (ausentes em `ai_enrichment.py`, mas
  explicitamente exigidas pelo §4 desta plan): `_format_detections` corta a lista em no
  máximo 40 detecções e 2000 caracteres antes de ir ao prompt; `max_tokens=500` na
  chamada ao `ChatOpenAI` — nenhuma requisição a este LLM sai sem teto de entrada nem de
  saída.
- `backend/apps/asset_manager/vision/plate_extraction.py` — `extract_plate_data` passou a:
  1) chamar `read_plate_text` (inalterado); 2) se não houver nenhuma detecção, ir direto
  para `parse_plate_fields` sem acionar o LLM (evita gastar uma chamada paga por um
  resultado que já sabemos que será todo "Não legível" — mitigação adicional de custo/Model
  DoS, decisão de implementação); 3) senão, tentar `structure_plate_text(detections)`;
  4) se levantar `LlmStructuringError` (chave ausente ou falha de rede/API), cair
  automaticamente em `parse_plate_fields(detections)` — a mesma heurística por regex da
  `plan-03`, preservada **sem nenhuma alteração** como caminho alternativo. Decisão tomada
  no passo 3 da plan: **fallback automático**, não erro — para a feature continuar
  funcionando 100% offline quando não houver `OPENROUTER_API_KEY` configurada (mesmo
  espírito "roda local por padrão" já decidido em `00-contexto.md §8` para as `plan-03`/
  `plan-04`), em vez de quebrar o endpoint com 503 só porque a melhoria opcional de
  precisão não está disponível.
- `backend/apps/asset_manager/tests/test_plate_llm_structurer.py` (novo) — 1 teste:
  Fail-Fast sem chave configurada (`settings.openrouter_api_key = ""`) levanta
  `LlmStructuringError` **e** `ChatOpenAI` nunca é instanciado (`mock_chat_openai.assert_not_called()`)
  — prova que nenhuma chamada de rede é sequer tentada.
- `backend/apps/asset_manager/tests/test_plate_extraction.py` (novo) — 4 testes da
  composição em `plate_extraction.py`: (1) LLM disponível — `structure_plate_text` mockado
  devolvendo um resultado plausível a partir de uma entrada com ruído simulado
  (`"VV22 l75O RPM"`, que o regex sozinho rejeitaria por não bater nenhum padrão exato) —
  confirma que o resultado do LLM é usado e que `parse_plate_fields` **não** é chamado
  nesse caminho; (2) fallback — `structure_plate_text` mockado levantando
  `LlmStructuringError` — confirma que `parse_plate_fields` é chamado com as mesmas
  detecções e seu retorno é o que sai da função; (3) sem detecção nenhuma — confirma que
  `structure_plate_text` nem é chamado, direto para `parse_plate_fields`; (4) prova
  direta de que a imagem nunca chega ao LLM — `read_plate_text` é chamado com os bytes
  brutos, `structure_plate_text` é chamado só com a lista de detecções (texto+confiança),
  e os bytes brutos não aparecem em nenhum argumento posicional dessa segunda chamada.
- **Fora do escopo, confirmado intocado**: `ocr_engine.py` (`git diff --stat` vazio —
  chamada bruta ao EasyOCR idêntica à `plan-03`), `frontend/src/pages/Vision.tsx` (`git
  diff --stat` vazio — contrato de resposta inalterado), `backend/shared_infra/config.py`
  (`git diff --stat` vazio — nenhum campo `openrouter_*` novo ou duplicado), `router.py`
  e `schemas.py` (não precisaram de nenhuma edição: `router.py` já chama
  `extract_plate_data(image_bytes)`, cuja assinatura não mudou; `schemas.py` já validava
  `PlateExtractionResult`, reaproveitado tal como está pelo `with_structured_output`).

**Arquivos alterados**
| Arquivo | Natureza | O que mudou |
|---|---|---|
| `backend/apps/asset_manager/vision/plate_llm_structurer.py` | criado | estruturação via LLM de texto (OpenRouter), Fail-Fast, tetos de Model DoS |
| `backend/apps/asset_manager/vision/plate_extraction.py` | alterado | LLM como caminho principal, fallback automático para `parse_plate_fields` |
| `backend/apps/asset_manager/tests/test_plate_llm_structurer.py` | criado | teste do Fail-Fast sem chave |
| `backend/apps/asset_manager/tests/test_plate_extraction.py` | criado | 4 testes da composição (LLM, fallback, skip sem detecção, nunca envia imagem) |

**Verificações executadas**
- `python -m pytest backend api/tests -q` → **52 passed**, 0 failures (47 anteriores da
  suíte completa + 5 novos: 1 de `test_plate_llm_structurer.py` + 4 de
  `test_plate_extraction.py`). Saída lida por completo.
- `python -m pytest backend/apps/asset_manager/tests/test_plate_llm_structurer.py backend/apps/asset_manager/tests/test_plate_extraction.py backend/apps/asset_manager/tests/test_vision_endpoint.py -v`
  → **12 passed**, saída individual conferida linha a linha (inclui os 7 testes já
  existentes de `test_vision_endpoint.py`, intactos — não precisei tocar nesse arquivo
  nesta rodada, já que `extract_plate_data(image_bytes)` manteve a mesma assinatura que o
  `router.py` já chamava).
- `grep -nE "image|base64|bytes" backend/apps/asset_manager/vision/plate_llm_structurer.py`
  → só uma ocorrência, no docstring, na frase "nunca a imagem" — confirma estruturalmente
  que o módulo do LLM não referencia dado de imagem em nenhum ponto do código.
- `git diff --stat` restrito a `ocr_engine.py`, `Vision.tsx` e `config.py` → **vazio nos
  três**, confirma que nada fora do escopo declarado foi tocado.
- **Não executado**: chamada real a um LLM de texto via OpenRouter (sem
  `OPENROUTER_API_KEY` neste ambiente — mesma limitação já registrada nas `plan-02`/
  `plan-03`). O caminho Fail-Fast (sem chave) foi exercitado de verdade pelo teste; o
  caminho de sucesso via LLM real (o LLM de fato corrigindo ruído de OCR) não foi.
- **Não repeti o teste fim-a-fim com imagem sintética "ruidosa"** sugerido no §7 da plan
  (comparar resultado antes/depois): exigiria uma `OPENROUTER_API_KEY` real para exercitar
  o caminho novo de verdade (a chamada ao EasyOCR sozinha, sem chave, sempre cai no mesmo
  fallback de regex já testado na `plan-03`) — decisão consciente de não simular esse
  resultado, registrado como pendência abaixo para o revisor decidir se quer fornecer uma
  chave.

**Critérios de aceite**
- [x] O texto bruto do OCR é estruturado por um LLM de texto (via OpenRouter), tolerante a
  ruído de leitura que o regex sozinho rejeitaria — evidência: `plate_llm_structurer.py`
  usa `ChatOpenAI`/OpenRouter com um prompt que instrui tolerância a ruído; o teste
  `test_extract_plate_data_uses_llm_result_when_available` usa uma entrada com ruído
  simulado (`"VV22 l75O RPM"`) que nenhum regex de `plate_parser.py` reconheceria, e
  confirma que o caminho do LLM (mockado) é o que produz o resultado.
- [x] A imagem **nunca** é enviada a nenhuma API externa — evidência: grep estrutural sem
  ocorrência de `image`/`bytes`/`base64` em código no novo arquivo, mais
  `test_extract_plate_data_never_passes_image_bytes_to_llm` provando em runtime que
  `structure_plate_text` só recebe a lista de detecções, nunca os bytes brutos.
- [x] Campo sem base nas detecções continua virando `"Não legível"`, nunca um valor
  inventado — evidência: instrução explícita no prompt do LLM + o schema Pydantic
  (`PlateExtractionResult`, inalterado) continua validando a saída do LLM antes de
  qualquer retorno, exatamente como já fazia para o resultado do regex.
- [x] Comportamento definido e testado para quando o LLM não está disponível — evidência:
  decisão de **fallback automático** para `parse_plate_fields` (regex), registrada acima
  e coberta por `test_extract_plate_data_falls_back_to_regex_when_llm_fails` +
  `test_structure_plate_text_fails_fast_without_api_key`.
- [x] `ocr_engine.py` não foi alterado — evidência: `git diff --stat` vazio para esse
  arquivo.
- [x] Testes unitários do novo caminho verdes, suíte completa sem regressão — evidência:
  52/52 na suíte completa, 12/12 nos arquivos de teste de `vision/`.

**Decisões e suposições**
- **Fallback automático (não erro) quando o LLM falha/está ausente.** A plan (passo 3)
  deixava a escolha a critério do executor, pedindo só que fosse registrada com o motivo.
  Optei por fallback automático — e não por levantar erro (ex.: 503) — porque (a) é
  consistente com a decisão já tomada no projeto de rodar local por padrão
  (`00-contexto.md §8`), e (b) `parse_plate_fields` já é um caminho testado, aprovado e
  funcional desde a `plan-03` — não usá-lo como rede de segurança seria regressão de
  disponibilidade sem ganho nenhum. O trade-off aceito: se o LLM falhar por qualquer
  motivo (não só chave ausente — também timeout, erro 5xx do OpenRouter, resposta que não
  valida o schema), a resposta ao usuário é silenciosamente menos precisa (heurística por
  regex) em vez de um erro visível pedindo para tentar de novo. Registrado aqui para o
  revisor avaliar se esse silêncio é aceitável ou se deveria haver um sinal (ex.: campo
  extra indicando qual caminho foi usado) — não implementado, pois mudaria o contrato de
  resposta (`PlateExtractionResult`), fora do que a plan autoriza (§3.2: "contrato de
  resposta... não muda").
- **Curto-circuito para regex quando não há nenhuma detecção do OCR.** Não pedido
  explicitamente pela plan, mas decorre diretamente do objetivo dela: gastar uma chamada
  de LLM (com custo real de tokens) sobre uma lista vazia sempre produziria
  "Não legível" em todos os campos — o mesmo resultado que `parse_plate_fields([])` já
  devolve sem custo nenhum. Tratado como extensão natural da mitigação de Model DoS que o
  `cyber-ia` já pedia para esta plan, não como funcionalidade nova.
- **Tetos de Model DoS (`_MAX_DETECTIONS=40`, `_MAX_DETECTIONS_TEXT_LENGTH=2000`,
  `max_tokens=500`) são números de implementação, não determinados pela plan.** Escolhidos
  generosos o bastante para uma placa real (raramente mais de 15-20 linhas de texto) e
  reduzidos o bastante para não permitir uma entrada excessiva caso o EasyOCR, por
  qualquer motivo, devolva um número anormal de detecções. `ai_enrichment.py` (referência
  de forma desta plan) não tem tetos equivalentes — não toquei nele (fora do escopo), mas
  registro aqui como achado fora do escopo, abaixo.
- **Não criei um schema de saída "tolerante" separado do `PlateExtractionResult`.** O LLM
  usa exatamente o mesmo schema que o regex já preenchia — nenhuma duplicação de contrato,
  como pedido implicitamente pelo princípio "referencie, nunca duplique".
- **Não editei `specs/04-vision-ocr.md`** (destino de síntese, §8) — mesma leitura já
  consistente nas rodadas anteriores desta cadeia de plans: §8 é destino do processo de
  síntese do revisor, não instrução de execução para mim.

**Achados fora do escopo (não corrigidos)**
- `backend/apps/asset_manager/domain/ai_enrichment.py` (a referência de padrão desta plan)
  não declara `max_tokens` nem nenhum teto de tamanho de entrada na chamada ao
  `ChatOpenAI` — o mesmo tipo de mitigação de Model DoS que o `cyber-ia` pede e que
  implementei em `plate_llm_structurer.py` nesta rodada. Não corrigido — está fora da
  lista de arquivos desta plan (`ai_enrichment.py` é só referência de leitura, §4).
- Mesmos achados já registrados nas rodadas anteriores da `plan-03`, ainda válidos e não
  tocados por esta plan: dead import `Upload` em `Vision.tsx:2`; `frontend/tsconfig.json`
  ausente; endpoint `/api/vision/scan` sem rate limiting.

**Pendências / riscos**
- **Caminho de sucesso do LLM nunca chamado de verdade** (mesma categoria de pendência já
  registrada nas rodadas da `plan-03` para o caminho de OCR): sem `OPENROUTER_API_KEY`
  neste ambiente, não há como provar que o LLM de fato corrige ruído de OCR real melhor do
  que a heurística por regex — só os testes com LLM mockado provam que a **composição**
  (wiring) está correta. Recomendo ao revisor, se houver uma chave disponível, repetir o
  teste fim-a-fim sugerido no §7 da plan (imagem sintética ruidosa, comparar antes/depois)
  para validar o ganho de precisão prometido no objetivo desta plan.
- Verificação visual em navegador não feita (mesma pendência já aceita pelo usuário nas
  rodadas anteriores desta cadeia de plans — o contrato de resposta não muda, então o
  risco de regressão de UI é baixo, mas não foi verificado ao vivo).
- Cronômetro de apontamento de horas (`CLAUDE.md`, skill `time-tracking` via MCP) não
  iniciado — mesma capacidade ausente já confirmada e registrada em três rodadas
  consecutivas da `plan-03` (ver veredito de 2026-08-22 dessa plan, já aprovada); não
  repeti a busca por essa ferramenta nesta rodada por já estar definitivamente confirmada
  como inexistente nesta sessão.

---

# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->

## Veredito — 2026-08-22 — 🟢 Aprovado

**Verificado diretamente no worktree:**

- `git status`/`git diff --stat` → confirma o conjunto exato de arquivos alegado; `ocr_engine.py`,
  `config.py`, `Vision.tsx` com diff **vazio** (`router.py`/`schemas.py` continuam com o mesmo
  diff já aprovado na `plan-03`, nada novo nesta rodada).
- Li `plate_llm_structurer.py` e `plate_extraction.py` por completo: prompt trata cada texto do
  OCR como dado, nunca comando (mitigação de injeção indireta via foto manipulada, pedida por
  `cyber-ia`); Fail-Fast antes de qualquer chamada de rede; tetos reais de Model DoS
  (`_MAX_DETECTIONS=40`, 2000 caracteres, `max_tokens=500`) — conferi que os três realmente
  limitam o que sai para a API, não são só comentário. `structure_plate_text` recebe só
  `list[tuple[str, float]]`, nunca bytes de imagem.
- `grep -inE "image|base64|bytes"` em `plate_llm_structurer.py` → **1 ocorrência só**, no
  docstring, na negativa "nunca a imagem" — confirma estruturalmente.
- Li os 5 testes novos linha a linha contra o código: os 4 cenários de `test_plate_extraction.py`
  (LLM disponível, fallback, sem detecção, prova de que bytes nunca chegam ao LLM) e o Fail-Fast
  de `test_plate_llm_structurer.py` — todos exercitam a composição real, mockando só as bordas de
  I/O (`read_plate_text`, `structure_plate_text`/`ChatOpenAI`, `parse_plate_fields`).
- Rodei a suíte eu mesmo: `python -m pytest backend api/tests -q` → **52 passed**, bate com o
  alegado.

**Critérios de aceite — 6 de 6 atendidos:**
- [x] Estruturação via LLM de texto, tolerante a ruído — código + teste com entrada ruidosa
  (`"VV22 l75O RPM"`) que nenhum regex reconheceria.
- [x] Imagem nunca vai à API — grep estrutural + teste dedicado provando em runtime.
- [x] `"Não legível"` nunca inventado — instrução no prompt + mesmo schema Pydantic de antes,
  inalterado.
- [x] Comportamento definido para LLM indisponível — fallback automático para `parse_plate_fields`,
  decisão bem justificada (disponibilidade > erro visível), testado.
- [x] `ocr_engine.py` intocado — confirmado.
- [x] Testes verdes — 52/52 confirmados por mim.

**Sobre a decisão de fallback silencioso (sem sinalizar ao usuário qual caminho foi usado):**
concordo com o raciocínio do executor — mudar o contrato de resposta estava fora do que a plan
autorizava, e a plan não pedia esse sinal. Não é achado.

**Pendência real, sem peso no veredito:** o ganho de precisão prometido no objetivo (LLM corrige
ruído que o regex erra) não foi provado com uma chamada real — mesma limitação estrutural já
aceita nas plans anteriores desta cadeia. Fica registrada; se você tiver uma chave com crédito,
vale repetir o teste fim-a-fim sugerido no §7 da própria plan.
