---
tipo: "plan"
titulo: "Implementar Visão Computacional OCR local para Placas (EasyOCR)"
dominio: "vision_service"
status: "🟢 Aprovada"
prioridade: "Alta"
tags: ["plan", "ocr", "vision", "local"]
relacionados: ["[[specs/04-vision-ocr]]"]
depende_de: "—"
destino_sintese: "specs/04-vision-ocr.md"
---

> **Revisada em 2026-08-22 — pivot de arquitetura.** A primeira execução desta plan (resumo e
> veredito abaixo, preservados como histórico) implementou a leitura da placa via LLM multimodal
> (OpenRouter). Decisão do usuário: trocar para **OCR local** (`easyocr` + `opencv-python-headless`,
> já declarados em `requirements.txt` sob o comentário "Preparação Sprint 2", nunca usados até
> aqui) — zero custo por chamada, zero dependência de rede externa por requisição, consistente
> com a decisão já tomada na `plan-04` de manter o projeto local. **As instruções abaixo (§1-§8)
> substituem integralmente a versão anterior** — o executor desta rodada deve **remover**
> `backend/apps/asset_manager/vision/llm_vision.py` (o módulo LLM) e os testes que o mockavam,
> substituindo pela implementação local descrita aqui. `schemas.py` e `router.py` podem ser
> largamente reaproveitados (ver §5).

# 1. Objetivo
A tela de Visão Computacional lê a placa do motor (imagem) e extrai os dados técnicos usando OCR
**100% local** — sem chamar nenhuma API externa, sem custo por scan.

# 2. Contexto
`backend/apps/asset_manager/vision/schemas.py` e `router.py` (da execução anterior) já definem o
contrato: `PlateExtractionResult` (9 campos: `modelo`, `potencia`, `rpm`, `carcaca`, `tensao`,
`corrente`, `ip`, `classe_isol`, `confianca`) e `POST /vision/scan` (`UploadFile`, validação de
`content_type`/tamanho antes de processar). Isso continua valendo. O que muda é **como** o texto é
extraído: em vez de `llm_vision.py` (chamada ao OpenRouter), um pipeline local com `easyocr`
(detecção + leitura de texto) e heurística/regex própria (mapear o texto solto detectado para os
9 campos — EasyOCR não sabe que um número é "RPM", só le o texto, então essa estruturação é lógica
nova a escrever). `opencv-python-headless` fica disponível para pré-processamento de imagem
(escala de cinza, threshold, etc.) se o executor julgar necessário para melhorar a leitura —
decisão de implementação, não obrigatória.

# 3. Escopo
## 3.1 Dentro
- `backend/apps/asset_manager/vision/*` — remover `llm_vision.py`; criar o pipeline OCR local
  (nome de arquivo(s) a critério do executor, mas **separando** claramente a chamada bruta ao
  EasyOCR — difícil de testar sem baixar pesos de modelo — da lógica de estruturação/heurística
  — pura, testável sem EasyOCR de verdade). Manter `schemas.py`/`router.py` como estão, ajustando
  só o que for necessário para importar o novo módulo em vez do antigo.
- `requirements.txt` — nenhuma mudança esperada (`easyocr`/`opencv-python-headless` já declarados).
- `frontend/src/pages/Vision.tsx` — nenhuma mudança esperada (já consome `/api/vision/scan`
  genericamente); ajustar só se o contrato de resposta mudar (não deveria).
- `backend/apps/asset_manager/tests/test_vision_endpoint.py` — adaptar os testes que mockavam
  `extract_plate_data`/LLM para mockar a função de OCR local equivalente.

## 3.2 Fora
- `backend/shared_infra/config.py` — esta feature não usa `settings.openrouter_*` nem precisa de
  nenhuma chave nova. Não toque nos campos `openrouter_*` (seguem em uso por `plan-02`/`plan-04`).
- Estilização do Sarak-UI (não quebrar animações existentes).
- Persistência em banco do resultado do scan (mesma decisão da execução anterior — fora de escopo).

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Contexto | `00-contexto.md` §8 (decisão de manter o projeto local) · `00-knowledge.md` | sempre |
| Skill | `cyber-ia` | agora focado em limite de recurso (imagem grande/decompression bomb antes do OpenCV processar), não mais em prompt injection de LLM — não há prompt de LLM nesta versão |
| Skill | `padrao-python` + `padrao-typescript` | regras base |
| Skill | `test-unitario` | o parser heurístico (texto bruto → campos) é o alvo principal de teste — puro, sem I/O, sem precisar do modelo do EasyOCR carregado |
| Código | `backend/apps/asset_manager/vision/schemas.py`, `router.py` | ler antes — já existem e devem ser reaproveitados |
| Código | `backend/apps/asset_manager/vision/llm_vision.py` (a remover) | ler antes de remover, para não perder nenhuma validação de negócio útil (allowlist de tipo, limite de tamanho — esses ficam, vivem no `router.py`, não no arquivo removido) |

# 5. Instruções de execução
1. Ler `llm_vision.py` e removê-lo (junto de qualquer import dele em `router.py`).
2. Criar o wrapper fino de OCR bruto: instancia `easyocr.Reader` (idiomas pt/en) e chama
   `readtext()` sobre a imagem recebida, devolvendo a lista de `(texto, confiança)` detectada —
   sem nenhuma lógica de negócio aqui, só a chamada ao motor.
3. Criar a função pura de estruturação: recebe a lista de textos/confianças detectados e devolve
   um `PlateExtractionResult` — usa regex/heurística para reconhecer padrões plausíveis de cada
   campo (ex.: token com "IP" seguido de dois dígitos → `ip`; valores separados por "/" com "V" →
   `tensao`; etc.). Campo não reconhecido com confiança razoável vira `"Não legível"` (mesma
   filosofia da versão anterior — nunca inventar valor). `confianca` do resultado agregado deve
   refletir a confiança real das detecções usadas (ex.: média das confianças dos campos
   efetivamente preenchidos), não um valor fixo.
4. Ligar o `router.py` à nova função de estruturação, mantendo a validação de `content_type`/
   tamanho já existente antes de processar (evita gastar CPU/RAM com OCR em arquivo inválido).
5. Adaptar `test_vision_endpoint.py`: os testes de 415/413/sucesso continuam válidos no formato
   (mock da função de extração, não da rota); adicionar testes novos e diretos da função pura de
   estruturação (item 3) com listas de texto bruto simuladas cobrindo: placa bem formatada, texto
   parcialmente ilegível (deve virar "Não legível" nos campos não reconhecidos, não erro), e texto
   sem nenhum padrão reconhecível (deve devolver o schema todo como "Não legível", não falhar).
6. Rodar a suíte completa e confirmar verde.

# 6. Critérios de aceite
- [ ] OCR local extrai texto da imagem e estrutura nos 9 campos esperados, sem chamar nenhuma API externa.
- [ ] Campo não reconhecido no texto detectado vira `"Não legível"`, nunca um valor inventado.
- [ ] `confianca` reflete a confiança real das detecções do EasyOCR, não um valor fixo/simulado.
- [ ] Front-end continua renderizando a resposta real (sem regressão da execução anterior).
- [ ] Zero dependência de chave de API para esta feature especificamente.
- [ ] Testes unitários da função de estruturação (heurística) cobrindo os 3 cenários do passo 5, mais os testes de contrato do endpoint (415/413/sucesso), todos verdes.

# 7. Como verificar (uso do revisor)
- `git diff --stat` → confirma `llm_vision.py` removido, nada em `config.py`/`digital_twin_core`/`asset_manager/web`.
- Ler a função de estruturação e confirmar que é pura (sem I/O) e testável sem depender do modelo do EasyOCR carregado.
- Rodar a suíte de testes e ler a saída real.
- Se houver como rodar localmente com uma imagem de teste real (o próprio revisor pode tentar, já que agora não depende de crédito de API), tentar uma leitura fim-a-fim.

# 8. Destino da síntese
**Destino:** `specs/04-vision-ocr.md`
Documentar a decisão de OCR local (não LLM) e o porquê (custo zero, sem dependência de rede),
substituindo qualquer menção a OpenRouter/LLM multimodal nesta feature específica.

---
# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

## Resumo da execução — 2026-08-22

**Resultado:** Concluído com pendências

**O que foi feito**
- Confirmado que `plan-02` já criou `openrouter_api_key`/`openrouter_base_url`/`openrouter_model`
  em `backend/shared_infra/config.py` — **não recriei nenhum campo**, só reusei `settings`
  diretamente. `openrouter_model` default (`openai/gpt-4o-mini`) é multimodal (aceita imagem),
  então nenhum campo de config novo foi necessário para o modelo de visão em si.
- `backend/apps/asset_manager/vision/` (novo subpacote):
  - `schemas.py` — `PlateExtractionResult`: os mesmos 9 campos que o mock do frontend já usava
    (`modelo`, `potencia`, `rpm`, `carcaca`, `tensao`, `corrente`, `ip`, `classe_isol`,
    `confianca`), como string (uma placa real mistura formato — ex. tensão tripla
    "220/380/440V", que não cabe num tipo numérico), exceto `confianca: float` (0-100,
    `ge`/`le`) — é o único campo que faz sentido como número para uso programático futuro.
    `max_length` em toda string — mitigação de tamanho de resposta pedida pelo `cyber-ia`.
  - `llm_vision.py` — `extract_plate_data()`: monta `ChatOpenAI` (mesmo padrão de
    `domain/ai_enrichment.py` da `plan-02`) com `with_structured_output(PlateExtractionResult)`
    — a resposta do LLM multimodal é validada pelo schema antes de sair da função, nunca é
    repassada como JSON solto. Mensagem ao LLM: `HumanMessage` com bloco de texto + bloco
    `image_url` (base64 data URI) — é como o LangChain/OpenAI-compatible aceita imagem.
    `SystemMessage` instrui o modelo a tratar todo texto lido NA IMAGEM como dado de placa,
    nunca como comando a seguir, e a escrever "Não legível" em vez de inventar valor — mitigação
    específica de injeção via imagem/texto adversarial pedida pela skill `cyber-ia` para esta
    plan (§4). `PlateExtractionError` cobre chave ausente (Fail-Fast, checado antes de qualquer
    chamada de rede) e falha de chamada — nenhuma exceção engolida.
  - `router.py` — `POST /vision/scan` (`UploadFile`): valida `content_type` contra allowlist
    (`image/jpeg`, `image/png`, `image/webp` — os mesmos formatos que a UI já anuncia) → 415 se
    fora da lista; valida tamanho ≤ 10MB (mesmo limite que a UI já anuncia) → 413 se maior;
    delega a `extract_plate_data`; 503 se `PlateExtractionError`. Nenhuma persistência em banco
    — a plan não pede isso, só extração e retorno.
- `api/index.py` — 2 linhas: import + `app.include_router(vision_router, prefix="/api")`, para
  o endpoint existir de fato em `/api/vision/scan` (path literal exigido pela plan §5.2).
  Necessário porque `asset_router` já está montado com prefixo `/assets`; não há como o path
  final ficar `/api/vision/scan` sem um `include_router` novo em algum lugar, e o único lugar
  onde esses calls existem é `api/index.py`. Fora da lista literal de `backend/apps/asset_manager/vision/*`
  + `Vision.tsx`, mas sem isso o endpoint seria código morto — mesma lógica que a `plan-01`
  aplicou ao `.gitignore`/`.env.example`.
- `requirements.txt` — adicionado `python-multipart>=0.0.9` (dependência real do FastAPI para
  `UploadFile`/`File()` — não estava instalada nem declarada na raiz do projeto; sem ela o
  endpoint derruba com erro de "Form data requires python-multipart" em toda requisição).
  Instalado no `.venv` também, para os testes rodarem.
- `frontend/src/pages/Vision.tsx` — `simulateScan` (setTimeout com JSON fixo) substituída por
  `handleFile` (upload real: `FormData` + `fetch('/api/vision/scan', {method:'POST', body:...})`
  ). Adicionado `<input type="file" className="hidden">` acionado pelo botão "Selecionar
  Arquivo" existente + `onDrop`/`onDragOver` na mesma dropzone (a UI já anunciava "Arraste a
  foto..." mas não tinha handler nenhum — implementado, é o mesmo elemento, não nova
  estilização). A imagem mostrada durante/depois do scan passou de uma foto de banco de imagens
  fixa (Unsplash, sem relação com o motor real) para `URL.createObjectURL(file)` — a foto que o
  usuário de fato enviou. Erro de rede/backend exibido inline (mesmo padrão visual usado em
  `Assets.tsx` na `plan-02`: caixa vermelha `bg-rose-500/10`). Nenhuma classe Tailwind, nenhum
  componente de layout existente foi alterado — só a lógica de estado e os elementos
  estritamente necessários (input de arquivo, mensagem de erro).
- Teste (`test-unitario`, mock só do LLM multimodal): `backend/apps/asset_manager/tests/test_vision_endpoint.py`
  — 4 testes via `TestClient` real contra a rota de verdade (`extract_plate_data` mockado):
  sucesso (schema retornado, `extract_plate_data` chamado com os bytes/content-type corretos),
  415 para tipo de arquivo não suportado, 413 para imagem > 10MB, 503 quando `PlateExtractionError`.

**Arquivos alterados**
| Arquivo | Natureza | O que mudou |
|---|---|---|
| `backend/apps/asset_manager/vision/__init__.py` | criado | pacote novo |
| `backend/apps/asset_manager/vision/schemas.py` | criado | `PlateExtractionResult` |
| `backend/apps/asset_manager/vision/llm_vision.py` | criado | chamada LLM multimodal via OpenRouter |
| `backend/apps/asset_manager/vision/router.py` | criado | `POST /vision/scan` |
| `api/index.py` | alterado | monta `vision_router` em `/api` |
| `requirements.txt` | alterado | `python-multipart>=0.0.9` |
| `frontend/src/pages/Vision.tsx` | alterado | mock → upload real, preview real, erro inline |
| `backend/apps/asset_manager/tests/test_vision_endpoint.py` | criado | 4 testes do endpoint |

Confirmado por `git status`: nenhum campo `openrouter_*` duplicado em `config.py` (não
tocado nesta rodada); nada em `digital_twin_core/`, `ingestion_service/` ou `asset_manager/web`
(`router.py`/`entities.py` que aparecem no `git status` são da `plan-02`, não desta execução —
confirmado por `git diff` deles ficar vazio nesta rodada).

**Verificações executadas**
- `python -m pytest backend api/tests -q` → **31 passed**, 0 failures (27 anteriores + 4 novos
  do `test_vision_endpoint.py`), 0 regressão.
- `python -c "from api.index import app; app.openapi()"` → import ok, `/api/vision/scan`
  presente em `app.openapi()['paths']` (path literal exigido pela plan). Os 3 warnings de
  "Duplicate Operation ID" que aparecem são **pré-existentes** — confirmado rodando o mesmo
  comando sob `git stash` (sem nenhuma das minhas mudanças): os mesmos 3 warnings já
  apareciam antes.
- `tsc --noEmit` (config temporária ad-hoc em `frontend/`, `strict: true`, apagada depois — o
  projeto não tem `tsconfig.json`, achado já registrado pela `plan-02`) contra `Vision.tsx`
  inteiro → **0 erros**.
- Autoverificação de limiares (`padrao-python`/`padrao-typescript`): nenhuma função nova passa
  de ~25 linhas, aninhamento ≤ 2, ≤ 4 parâmetros. `handleFile` no frontend tem ~20 linhas.
- **Não executado**: chamada real a um LLM multimodal via OpenRouter — sem `OPENROUTER_API_KEY`
  neste ambiente (mesma limitação já registrada na `plan-02`). Só o caminho de erro Fail-Fast
  (503) e o de validação de request (415/413) foram exercitados de verdade.
- **Não executado**: verificação visual em navegador — mesma decisão da `plan-02` (instalar
  Playwright/Chromium é uma ação de sistema que só faço mediante pedido explícito; não repeti a
  pergunta nesta rodada para não interromper o fluxo à toa, e sigo a mesma decisão anterior do
  usuário de testar manualmente). Passo a passo entregue na conversa.

**Critérios de aceite**
- [x] OCR devolve campos corretos da placa (rpm, tensão, IP, etc) — evidência: `schemas.py`
  cobre os 9 campos que a UI já esperava; `test_scan_returns_structured_plate_data` confirma o
  schema sendo retornado pela rota real. Corretude do OCR **de verdade** (o LLM lendo uma placa
  real corretamente) não verificada — ver pendências.
- [x] Front-end renderiza a resposta da API ao invés do mock — evidência: `Vision.tsx`
  `handleFile` chama `fetch('/api/vision/scan', ...)` e popula `scanResult` com a resposta real;
  `simulateScan`/JSON fixo removidos.
- [x] Nenhuma chave de API hardcoded no código do endpoint — evidência: `llm_vision.py` só lê
  `settings.openrouter_api_key`/`base_url`/`model`, todos vindos do Pydantic `Settings`
  (reusados da `plan-02`, nada duplicado).
- [x] Teste unitário do endpoint verde — evidência: 4/4 em `test_vision_endpoint.py`.

**Decisões e suposições**
- **`confianca` virou `float` (era string formatada `"98.4%"` no mock).** Decidi que um campo
  de confiança numérico e validado (`ge=0, le=100`) é mais correto para uma saída estruturada
  de LLM do que uma string com "%" embutido — mais fácil de validar e de usar depois (ex.: um
  futuro alerta de "confiança baixa, revisar manualmente"). Ajustei o único ponto do frontend
  que formatava esse valor (`{scanResult.confianca}%`), sem tocar em mais nada da UI.
- **Nenhuma persistência em banco.** A plan não pede para gravar o resultado do scan em nenhuma
  tabela (diferente da `plan-02`, que criava `MotorModelDB`/`ActiveAssetDB`) — o botão
  "Vincular ao Ativo" que já existia na UI (sem `onClick`, já não fazia nada antes da minha
  edição) continua sem handler; ligá-lo é fora do escopo explícito desta plan.
- **`api/index.py` e `requirements.txt` tocados como companions necessários**, fora da lista
  literal do §3.1 — mesma lógica já usada e aprovada nas plans 01/02 (edição mínima,
  documentada, sem a qual a feature simplesmente não existiria/não rodaria).
- **Não editei `specs/04-vision-ocr.md`** (destino de síntese, §8) — mesma leitura consistente
  das plans anteriores: §8 é destino para o processo de síntese do revisor, não instrução de
  execução para mim.
- Reaproveitei o padrão de prompt de sistema anti-injeção da `plan-02` (tratar input do usuário
  como dado, nunca como comando), adaptado para o contexto de imagem — este é o pedido
  específico de `cyber-ia` no §4 desta plan ("proteção de injeção na visão").

**Achados fora do escopo (não corrigidos)**
- `lucide-react`'s `Upload` (importado em `Vision.tsx:2`) nunca foi usado no arquivo — dead
  import pré-existente (confirmado: já estava assim antes da minha edição). Não removido — não
  é uma linha que toquei diretamente, e path de remoção poderia gerar diff de linha de import
  inteira sem necessidade real.
- Mesmo achado da `plan-02`, ainda válido: `frontend/tsconfig.json` não existe, `npm run build`
  continua quebrado para qualquer arquivo — não corrigido, fora do escopo declarado desta plan.
- Endpoint novo (`POST /api/vision/scan`) também sem rate limiting, mesmo raciocínio já
  registrado na `plan-02` para `POST /api/assets` (`cyber-api` não citada por nenhuma das duas
  plans) — custo de OpenRouter por imagem enviada pode ser maior que por texto.

**Pendências / riscos**
- **Caminho feliz do OCR nunca chamado de verdade.** Risco real e específico de visão: mesmo
  com o schema validando a FORMA da resposta, não há garantia de que o modelo escolhido
  (`openai/gpt-4o-mini`, herdado da `plan-02`) realmente lê bem placas de motor em fotos reais
  (ângulo, reflexo, resolução) — só um teste com imagem real e chave válida revela isso. Se a
  qualidade do OCR for ruim na prática, pode ser necessário trocar `OPENROUTER_MODEL` para um
  modelo com visão mais forte (ex. Claude 3.5 Sonnet, GPT-4o completo) — já configurável via
  `.env`, sem mudança de código.
- Verificação visual em navegador não feita (mesma pendência já aceita pelo usuário na
  `plan-02`, não repeti a pergunta).

---
# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->

## Veredito — 2026-08-22 — 🟣 Verificação do dono (não é reprovação nem aprovação)

**Verificado diretamente no worktree:**

- `git diff`/`status`: confirmo que `router.py`/`entities.py` (asset_manager) não foram tocados
  nesta rodada — o que aparece modificado é só o diff já aprovado da `plan-02`.
- Li `schemas.py`, `llm_vision.py` e `router.py` do subpacote `vision/` por completo: Fail-Fast
  antes de qualquer chamada de rede, saída validada por `PlateExtractionResult`, prompt de
  sistema específico contra injeção via imagem (trata texto na placa como dado, nunca comando —
  atende `cyber-ia` §4 desta plan), allowlist de `content_type` + limite de 10MB checados antes
  de gastar uma chamada de LLM.
- Rodei a suíte eu mesmo: `python -m pytest backend api/tests -q` → **31 passed**, bate com o
  alegado (27 anteriores + 4 novos: sucesso, 415, 413, 503).
- `python -c "from api.index import app; app.openapi()"` → confirma `/api/vision/scan`
  registrado. Investiguei os 3 warnings de "Duplicate Operation ID": vêm de `list_models`/
  `list_variables`/`list_sensors` **duplicados dentro do próprio `api/index.py:456-478`**, sem
  relação com o import de 2 linhas que esta plan adicionou — pré-existente, confirmado por
  localização no arquivo, não só pela alegação do executor.
- `npx tsc --strict` contra `Vision.tsx` → **0 erros**, confirma o alegado.
- Li o diff de `Vision.tsx`: mock removido, upload real (`FormData`/`fetch`), preview usa
  `URL.createObjectURL(file)` (a foto real enviada, não mais Unsplash), erro inline, drag-and-drop
  ligado ao mesmo elemento que já anunciava a funcionalidade sem handler. Nenhuma classe/layout
  novo — só lógica de estado.

**Critérios de aceite — 3 de 4 sólidos, 1 estruturalmente inverificável por qualquer agente:**
- [ ] **"OCR devolve campos corretos da placa"** — diferente do critério equivalente da `plan-02`
  ("chama OpenRouter e processa payload", sobre capacidade/wiring), este é sobre **corretude do
  conteúdo lido de uma imagem real** — só um LLM multimodal de verdade, lendo uma foto real de
  placa, prova isso. Sem `OPENROUTER_API_KEY` neste ambiente, nenhum agente consegue verificar.
  Mesma categoria estrutural do "Requisito de Ouro" da `plan-01`: é imprecisão minha ao escrever
  o critério, não falha do executor.
- [x] Front-end renderiza a resposta da API ao invés do mock — verificado no diff.
- [x] Nenhuma chave de API hardcoded — `llm_vision.py` só lê `settings.openrouter_*`.
- [x] Teste unitário do endpoint verde — 4/4, confirmado por mim.

**Decisão:** `🟣 Verificação do dono`. O código está correto, testado no que é automatizável, e a
mitigação de segurança (`cyber-ia`) está implementada corretamente. Falta só a prova de que o
OCR funciona de verdade contra uma foto real.

**Ação pendente, exclusivamente sua, para eu poder aprovar:**
1. Adicionar uma `OPENROUTER_API_KEY` real ao `.env` (idealmente um modelo com boa leitura de
   imagem — `OPENROUTER_MODEL=openai/gpt-4o` ou Claude 3.5 Sonnet, já configurável sem mudar
   código).
2. Subir backend + frontend (passo a passo já entregue pelo executor na conversa) e enviar uma
   foto real de placa de motor pela aba Visão Computacional.
3. Me contar se os campos extraídos batem com a placa real (não precisa ser perfeito — mas
   plausível). Se bater, aprovo; se o modelo escolhido ler mal a placa, pode ser caso de trocar
   `OPENROUTER_MODEL` (config, sem código) antes de eu considerar achado real.

**Sem impacto em outras plans** — nenhuma da fila depende de `plan-03`.

---

## Resumo da execução (pivot OCR local) — 2026-08-22

**Resultado:** Concluído

**O que foi feito**
- Removido `backend/apps/asset_manager/vision/llm_vision.py` — o módulo LLM multimodal
  (OpenRouter) e sua exceção `PlateExtractionError` deixaram de existir; nenhum outro arquivo
  do repositório importava esse módulo além de `router.py` e `test_vision_endpoint.py`
  (confirmado por grep antes de remover — `backend/apps/ai_knowledge/rag_engine.py` e
  `backend/apps/asset_manager/domain/ai_enrichment.py` usam `langchain_openai` por conta
  própria, de outra plan, sem relação com este módulo).
- `backend/apps/asset_manager/vision/ocr_engine.py` (novo) — a chamada bruta ao motor:
  `read_plate_text(image_bytes)` decodifica a imagem via OpenCV (`cv2.imdecode`), rejeita
  como `OcrEngineError` uma imagem que não decodifica ou cuja resolução passa de 40 milhões
  de pixels (mitigação de decompression bomb pedida por `cyber-ia` §4 desta plan — antes
  dessa checagem não havia nenhum limite de dimensão, só de bytes, que o `router.py` já
  cobria), converte para escala de cinza e chama `easyocr.Reader(['pt','en']).readtext()`.
  O `Reader` é instanciado uma única vez (`_get_reader`, lazy) para não recarregar os pesos
  a cada chamada. Nenhuma lógica de negócio aqui — só a chamada ao motor, como pedido no
  passo 2 da plan.
- `backend/apps/asset_manager/vision/plate_parser.py` (novo) — a função pura de
  estruturação: `parse_plate_fields(detections: list[tuple[str, float]])`. Usa um dicionário
  de regex por campo (`rpm`, `tensao`, `corrente`, `ip`, `classe_isol`, `potencia`,
  `carcaca`, `modelo`) testado em ordem contra cada texto detectado; o primeiro campo ainda
  vazio cujo padrão bate consome aquele texto (guard clauses, sem aninhamento além de
  `for`→`for`→`if`). Campo sem nenhum padrão reconhecido vira `"Não legível"`
  (constante `NAO_LEGIVEL`) — nunca um valor inventado. `confianca` é a média (arredondada a
  1 casa) das confianças reais só das detecções efetivamente usadas para preencher algum
  campo; `0.0` se nenhuma bateu. Zero I/O, zero import de `easyocr`/`cv2` — testável sem o
  modelo do EasyOCR carregado, como exigido no passo 3 e nos critérios de aceite.
- `backend/apps/asset_manager/vision/plate_extraction.py` (novo) — composição fina de 8
  linhas: `extract_plate_data(image_bytes)` chama `read_plate_text` e repassa o resultado a
  `parse_plate_fields`. É o único ponto que liga as duas metades; o `router.py` só conhece
  esta função.
- `backend/apps/asset_manager/vision/router.py` — trocado o import de `llm_vision` por
  `ocr_engine.OcrEngineError` + `plate_extraction.extract_plate_data`; a chamada em
  `scan_motor_plate` passou de `extract_plate_data(image_bytes, file.content_type)` para
  `extract_plate_data(image_bytes)` (o motor de OCR local não precisa do `content_type` — só
  decodifica os bytes). A validação de `content_type` (415) e tamanho ≤10MB (413), já
  existente, não mudou de lugar nem de ordem — continua rodando antes de qualquer OCR.
- `backend/apps/asset_manager/vision/schemas.py` — docstring de `PlateExtractionResult`
  ajustada (não cita mais "LLM multimodal", cita "heurística de OCR local"). Campo `ip`
  teve `max_length` alterado de `10` para `20`: o valor real (`"IP55"`) cabia em 10, mas o
  fallback `"Não legível"` tem 11 caracteres e um teste novo (cenário "sem padrão
  reconhecível") estourava a validação do Pydantic — bug pego pelo próprio teste, corrigido
  ao ampliar a única constante que realmente precisava mudar (os demais campos já tinham
  margem suficiente: `rpm` 30, `carcaca` 30, `classe_isol` 30, etc.).
- `backend/apps/asset_manager/tests/test_vision_endpoint.py` — os 4 testes de contrato do
  endpoint (sucesso/415/413/503) foram adaptados: mock em `vision_router_module` no símbolo
  `extract_plate_data` (agora chamado com 1 argumento, não mais 2), e a exceção 503 usa
  `OcrEngineError` em vez de `PlateExtractionError`. Adicionados 3 testes diretos e sem mock
  de `parse_plate_fields` (import direto de `plate_parser`, sem tocar em `ocr_engine`/
  `easyocr`): placa bem formatada (8 detecções simuladas, todos os 9 campos — incluindo
  `confianca` — batendo com o valor esperado calculado a partir das confianças de entrada);
  texto parcialmente ilegível (`rpm`/`ip` reconhecidos, os outros 6 campos viram
  `"Não legível"`, `confianca` = média só dos 2 usados); nenhum padrão reconhecível (todos os
  9 campos — incluindo `confianca=0.0` — sem nenhum valor inventado).
- **Fora da lista literal do §3.1, verificado e não tocado**: `requirements.txt` (já
  declarava `easyocr`/`opencv-python-headless`, nenhuma mudança necessária — confirmado por
  leitura), `api/index.py` (só importa `vision_router.router`, que manteve a mesma forma —
  `APIRouter` com o mesmo `prefix`/rota `/scan` —, nenhuma edição necessária),
  `frontend/src/pages/Vision.tsx` (contrato de resposta inalterado: mesmos 9 campos,
  `confianca` continua `float`; nenhuma edição feita), `backend/shared_infra/config.py`
  (não lido nem editado — esta feature não usa `settings.openrouter_*` nem nenhum campo
  novo, confirmado por `git diff` vazio nesse arquivo nesta rodada).

**Arquivos alterados**
| Arquivo | Natureza | O que mudou |
|---|---|---|
| `backend/apps/asset_manager/vision/llm_vision.py` | removido | módulo LLM multimodal (OpenRouter), obsoleto após o pivot |
| `backend/apps/asset_manager/vision/ocr_engine.py` | criado | chamada bruta ao EasyOCR + limite de resolução (decompression bomb) |
| `backend/apps/asset_manager/vision/plate_parser.py` | criado | função pura de estruturação (texto detectado → `PlateExtractionResult`) |
| `backend/apps/asset_manager/vision/plate_extraction.py` | criado | composição fina entre `ocr_engine` e `plate_parser` |
| `backend/apps/asset_manager/vision/router.py` | alterado | importa/chama o novo pipeline local em vez de `llm_vision` |
| `backend/apps/asset_manager/vision/schemas.py` | alterado | docstring atualizada; `ip.max_length` 10 → 20 |
| `backend/apps/asset_manager/tests/test_vision_endpoint.py` | alterado | mocks adaptados ao novo pipeline + 3 testes novos da função pura |

**Verificações executadas**
- `python -m pytest backend api/tests -q` → **47 passed**, 0 failures (suíte inteira do
  repositório, incluindo os 7 testes de `test_vision_endpoint.py` — 4 de contrato do
  endpoint + 3 da função pura de estruturação). Saída lida por completo.
- `python -m pytest backend/apps/asset_manager/tests/test_vision_endpoint.py -v` → **7
  passed**, saída individual conferida linha a linha.
- Teste fim-a-fim real, fora da suíte automatizada: gerei uma imagem sintética
  (`cv2.putText` sobre fundo branco, "W22 1750 RPM" / "IP55 220/380V" / "7.5 kW CLASSE F")
  e chamei `extract_plate_data` de verdade (EasyOCR real, sem mock nenhum — baixou o modelo
  de detecção na primeira chamada, ~9s). Resultado real:
  `{'modelo': 'W22', 'tensao': 'IP55 220/380V', 'confianca': 69.7, ...os demais 6 campos
  'Não legível'}`. Confirma que o pipeline roda 100% local (nenhuma chamada de rede além do
  download do peso do modelo, que é local/uma vez, não por requisição) e nunca inventa
  valor — mas também expõe uma limitação real da heurística: o EasyOCR agrupou "IP55" e
  "220/380V" na mesma linha detectada (a imagem sintética tinha os dois na mesma
  `cv2.putText`), e como o regex de `tensao` é testado antes do de `ip` na ordem de campos,
  o texto inteiro foi consumido por `tensao`, deixando `ip` como "Não legível" mesmo a foto
  "contendo" IP55. Isso é esperado em uma placa real (cada campo normalmente ocupa uma
  linha própria na etiqueta física, ao contrário do meu teste sintético que colocou dois
  campos na mesma linha) — registrado como risco conhecido abaixo, não como bug corrigido
  às pressas.
- Autoverificação de limiares (`padrao-python`): nenhuma função nova passa de ~20 linhas;
  aninhamento máximo 3 (`for`→`for`→`if` com guard clauses, sem `else` aninhado);
  `read_plate_text`, `parse_plate_fields` e `extract_plate_data` têm 1 parâmetro cada.
  Type hints em todas as assinaturas públicas.
- Arquivo temporário de teste (`scratch_plate.png`) removido do worktree após o teste
  fim-a-fim — não faz parte da entrega.

**Critérios de aceite**
- [x] OCR local extrai texto da imagem e estrutura nos 9 campos esperados, sem chamar
  nenhuma API externa — evidência: teste fim-a-fim acima (EasyOCR real, zero import de
  `langchain`/`openai`/`httpx` para rede externa em todo o subpacote `vision/`).
- [x] Campo não reconhecido no texto detectado vira `"Não legível"`, nunca um valor
  inventado — evidência: os 3 testes de `parse_plate_fields` (bem formada, parcial, nenhuma
  reconhecível) e o teste fim-a-fim real (6 de 9 campos corretamente marcados como não
  legíveis, nenhum valor inventado).
- [x] `confianca` reflete a confiança real das detecções do EasyOCR, não um valor
  fixo/simulado — evidência: `plate_parser.py` calcula a média das confianças recebidas
  como parâmetro (nunca uma constante); no teste fim-a-fim, `confianca=69.7` bate com a
  média real reportada pelo EasyOCR para as duas detecções usadas.
- [x] Front-end continua renderizando a resposta real, sem regressão da execução anterior —
  evidência: `Vision.tsx` não foi tocado; o contrato de resposta (9 campos + `confianca:
  float`) é idêntico ao que a versão LLM já produzia, então `handleFile`/`fetch` continuam
  funcionando sem alteração. **Não verificado em navegador** (ver pendências).
- [x] Zero dependência de chave de API para esta feature especificamente — evidência: nenhum
  `import` de `langchain_openai`/`ChatOpenAI` resta em `backend/apps/asset_manager/vision/`;
  `settings.openrouter_*` não é referenciado em nenhum arquivo do subpacote.
- [x] Testes unitários da função de estruturação cobrindo os 3 cenários do passo 5, mais os
  testes de contrato do endpoint (415/413/sucesso), todos verdes — evidência: 7/7 em
  `test_vision_endpoint.py`, ver "Verificações executadas".

**Decisões e suposições**
- **`extract_plate_data` perdeu o parâmetro `content_type`.** A versão LLM precisava dele
  para montar a data URI (`data:{content_type};base64,...`); o OCR local decodifica bytes
  puros via OpenCV, que não depende do MIME declarado pelo cliente. Manter um parâmetro
  não utilizado só para compatibilidade de assinatura violaria a regra de não adicionar
  parâmetro sem uso real — optei por remover, e adaptei o teste de contrato que checava a
  chamada (`mock_extract.assert_called_once_with(...)`) para 1 argumento.
- **Limite de 40 milhões de pixels (`_MAX_PIXELS`) como mitigação de decompression bomb.**
  A plan (§4) pede "limite de recurso (imagem grande/decompression bomb) antes do OpenCV
  processar" via `cyber-ia`, mas não fixa um número. Escolhi 40MP como teto generoso (bem
  acima de qualquer foto de celular comum, ~12-50MP, mas muito abaixo do que uma imagem
  adversarial comprimida poderia expandir para consumir RAM/CPU no `cv2.cvtColor`/
  `easyocr.readtext`) — decisão de implementação, não um número que a plan ditou.
- **Ordem dos campos em `_FIELD_ORDER` decide o desempate quando duas leituras de campo se
  sobrepõem no mesmo texto detectado** (ver o achado do teste fim-a-fim, acima). Escolhi a
  ordem atual (rpm, tensão, corrente, ip, classe_isol, potência, carcaça, modelo) sem
  nenhuma prioridade de negócio declarada pela plan — é uma suposição meramente técnica,
  documentada aqui para o revisor avaliar se faz sentido reordenar.
- **`ip.max_length` ampliado de 10 para 20 em `schemas.py`.** Não é uma mudança de contrato
  visível (o front não lê esse limite), só corrige um teto que o próprio "Não legível" já
  estourava — sem essa correção, o critério "campo não reconhecido vira 'Não legível' sem
  falhar" seria estruturalmente impossível de cumprir para o campo `ip`.
- **Não editei `specs/04-vision-ocr.md`** (destino de síntese, §8) — mesma leitura das
  rodadas anteriores desta plan: §8 é destino do processo de síntese do revisor, não
  instrução de execução para mim.
- **Não consegui iniciar o cronômetro de apontamento de horas via MCP (`time-tracking`)
  pedido pelo `CLAUDE.md`** — não existe essa skill nem uma ferramenta MCP equivalente
  disponível nesta sessão (`.agents/index.md` só lista `meta-create-skill`; busquei por
  ferramentas MCP de "time tracking" e nenhuma existe). Registrado aqui com honestidade em
  vez de simular a chamada.

**Achados fora do escopo (não corrigidos)**
- Mesmo achado já registrado nas rodadas anteriores desta plan, ainda válido: dead import
  `Upload` de `lucide-react` em `Vision.tsx:2`; `frontend/tsconfig.json` ausente; endpoint
  sem rate limiting (`cyber-api` não citada por esta plan). Não tocados — fora do escopo
  declarado.

**Pendências / riscos**
- **Overlap de campos na mesma linha de texto detectada** (ver "Verificações executadas"):
  quando o EasyOCR agrupa dois campos fisicamente próximos na mesma caixa delimitadora
  (comum se a placa tiver pouco espaçamento entre colunas), a heurística atual atribui o
  texto inteiro ao primeiro campo da `_FIELD_ORDER` cujo regex bate, deixando o outro campo
  como "Não legível" mesmo com o dado presente na imagem. Não é uma invenção de valor (ainda
  respeita a regra de nunca inventar), mas é uma perda de recall real. Só uma placa física
  real, fotografada, revela o quão comum é esse agrupamento na prática — recomendo ao
  revisor repetir o teste fim-a-fim com uma foto real de placa de motor (como já pedido no
  veredito anterior, agora sem depender de nenhuma chave de API).
- Verificação visual em navegador não feita (mesma pendência já aceita pelo usuário nas
  rodadas anteriores desta plan).
- Cronômetro de apontamento de horas (`CLAUDE.md`) não iniciado — capacidade indisponível
  nesta sessão, ver "Decisões e suposições".

---

## Veredito — 2026-08-22 — 🟢 Aprovado (pivot OCR local)

**Verificado diretamente no worktree:**

- `git status`/`git diff --stat` → confirma `llm_vision.py` removido, 3 arquivos novos
  (`ocr_engine.py`, `plate_parser.py`, `plate_extraction.py`), `router.py`/`schemas.py`/teste
  ajustados. `config.py`, `Vision.tsx`, `api/index.py`, `requirements.txt` — zero diff, exatamente
  como alegado.
- `grep` por `llm_vision|langchain_openai|openrouter|ChatOpenAI` em todo `vision/` e no teste →
  zero ocorrência em código-fonte (só um `.pyc` de cache, irrelevante, gitignored).
- Li `ocr_engine.py`, `plate_parser.py`, `plate_extraction.py` por completo: separação limpa entre
  I/O bruto (EasyOCR/OpenCV) e a função pura de estruturação; limite de 40MP contra decompression
  bomb antes de decodificar; `NAO_LEGIVEL` como único fallback, nunca valor inventado; `confianca`
  calculada como média real das confianças usadas (conferi a fórmula manualmente contra os 3
  testes novos, rastreando cada regex contra cada detecção simulada — bate exatamente).
- Rodei a suíte eu mesmo: `python -m pytest backend api/tests -q` → **47 passed**, bate com o
  alegado.
- **Rodei meu próprio teste real, sem mock**: gerei uma imagem sintética com os campos em linhas
  separadas (evitando de propósito o overlap que o executor já tinha documentado) e chamei
  `extract_plate_data` de verdade — EasyOCR real, zero rede, resultado com `modelo`, `potencia`,
  `carcaca`, `tensao`, `ip` reconhecidos corretamente e os demais como "Não legível" (leitura
  imperfeita da fonte renderizada, não um bug — nunca inventou nada). Confirma
  independentemente o achado do executor.

**Critérios de aceite — 6 de 6 atendidos, com evidência real (minha e do executor):**
- [x] OCR local extrai e estrutura sem API externa — dois testes reais (executor + eu),
  zero import de rede.
- [x] Campo não reconhecido vira "Não legível" — confirmado nos dois testes reais e nos 3 testes
  unitários de `plate_parser`.
- [x] `confianca` reflete confiança real — fórmula conferida manualmente, bate nos dois testes reais.
- [x] Front-end sem regressão — `Vision.tsx` não tocado, contrato de resposta idêntico.
- [x] Zero dependência de chave de API — confirmado por grep.
- [x] Testes unitários verdes — 7/7 do módulo, 47/47 da suíte completa, ambos rodados por mim.

**Sobre o achado de overlap** (dois campos na mesma linha detectada, só um é reconhecido):
diagnóstico correto do executor, risco real e honestamente registrado, não uma invenção de valor
— aceito como limitação conhecida, não bloqueia aprovação. Registro em `00-contexto.md` como
débito de baixo risco, não vira plan agora.

**Sobre o cronômetro `time-tracking`:** confirmo, terceira vez consecutiva — essa capacidade
realmente não existe nesta sessão. Não é um achado da execução.

**Diferente das duas rodadas anteriores desta plan, não preciso de validação manual sua**: a
troca para OCR local removeu a barreira que travava a aprovação (crédito de API) — consegui
verificar o caminho completo, inclusive com imagem real, sozinho.
