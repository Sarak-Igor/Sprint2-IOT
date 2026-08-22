---
tipo: "plan"
titulo: "Caracterizar o motor de anomalias e o provedor mock antes de qualquer refactor"
dominio: "digital_twin_core / ingestion_service"
status: "🟢 Aprovada"
prioridade: "Alta"
tags: ["plan", "teste", "caracterizacao", "legado"]
relacionados: ["[[specs/01-digital-twin-core]]", "[[specs/02-ingestion-service]]"]
depende_de: "—"
destino_sintese: "specs/01-digital-twin-core.md · specs/02-ingestion-service.md"
---

# 1. Objetivo
`persistence_handler.py` (motor de anomalias) e `mock_provider.py`/`chaos_generator.py` (produtor de
telemetria) passam a ter suíte de testes automatizados que documenta o comportamento **atual**, sem alterar
nenhuma linha de código de produção — fechando os checklists de "Plano de Testes" já escritos em
`specs/01-digital-twin-core.md §4` e `specs/02-ingestion-service.md §4`.

# 2. Contexto
Ambas as specs estão `🟢 Implementado`, mas nenhuma tem teste automatizado — os checklists de "Plano de
Testes" seguem 100% desmarcados (achado do diagnóstico de 2026-08-22, registrado em `00-contexto.md §8`). Isso
é risco concreto agora: `plan-01` (revisada) edita `ingestion_service/main.py` e o produtor mock; `plan-06`
(nova) edita `persistence_handler.py` diretamente — ambas tocam este código sem nenhuma rede de segurança
hoje. Por regra do ciclo SDD (`00-prompt-revisor.md §5.4`): "Toca legado sem cobertura? A caracterização vem
antes, em plan própria ou como primeiro passo explícito." Esta é essa plan — e `plan-01`/`plan-06` passam a
depender dela.

Comportamento a caracterizar (não duplicado aqui — já descrito nos §2 "Regras de Negócio" das duas specs
fixas referenciadas em §4):
- `TopicResolver.resolve()` e `MqttPersistenceHandler.save_telemetry()` (`persistence_handler.py`) — os dois
  itens do checklist de `specs/01-digital-twin-core.md §4`.
- `MqttMockProvider` e `ChaosGenerator.apply_chaos()` (`ingestion_service/adapters/`) — os dois itens do
  checklist de `specs/02-ingestion-service.md §4`.

# 3. Escopo

## 3.1 Dentro
- Arquivos de teste novos para `backend/apps/digital_twin_core/persistence_handler.py` (ex.:
  `backend/apps/digital_twin_core/tests/test_persistence_handler.py`).
- Arquivos de teste novos para `backend/apps/ingestion_service/adapters/mock_provider.py` e
  `chaos_generator.py` (ex.: `backend/apps/ingestion_service/tests/test_mock_provider.py`).
- Marcar (`- [x]`) os itens correspondentes do checklist "Plano de Testes" nas duas specs fixas — só depois de
  o teste estar verde.

## 3.2 Fora
- Qualquer alteração de comportamento em `persistence_handler.py`, `mock_provider.py` ou `chaos_generator.py`.
  Encontrou um bug real testando? **Não corrija** — registre em "Achados fora do escopo".
- `asset_manager/*`, `api/index.py`, frontend — nada disso é tocado aqui.
- Não é refactor de conformidade ao `padrao-python`. Se algo violar o padrão, registre como achado; não
  corrija agora — isso vira plan de adequação separada, se o revisor decidir que vale a pena.
- `digital_twin_core/main.py`, `anomaly_logger.py`, `converters/metric_converter.py` — confirmados órfãos
  (`00-contexto.md §8`), cobertos pela `plan-05` (remoção), não por testes.

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Spec fixa | `specs/01-digital-twin-core.md §4` | Checklist exato de comportamento a caracterizar do motor de anomalias |
| Spec fixa | `specs/02-ingestion-service.md §4` | Checklist exato de comportamento a caracterizar do produtor mock |
| Contexto | `00-contexto.md` · `00-knowledge.md` | sempre |
| Skill | `padrao-escrita` + `padrao-python` | sempre |
| Skill | `test-unitario` | Testes pela borda pública, mock só de I/O externo (broker MQTT, sessão de banco) |
| Código | `backend/apps/digital_twin_core/persistence_handler.py` | ler o arquivo inteiro antes de escrever teste |
| Código | `backend/apps/ingestion_service/adapters/mock_provider.py`, `chaos_generator.py` | ler antes de escrever teste |

# 5. Instruções de execução
1. Ler `persistence_handler.py` por completo e escrever os testes que atendem aos dois itens do checklist de
   `specs/01-digital-twin-core.md §4`: (a) payload MQTT inválido (não JSON ou não float) é tratado sem
   exceção não tratada; (b) o limiar inferior (`critical < nominal`) é identificado corretamente, gerando
   alerta quando `valor <= critical`. Mock só do cliente MQTT e da sessão de banco — não mock a lógica sob
   teste (`TopicResolver`, cálculo de severidade).
2. Ler `mock_provider.py` e `chaos_generator.py` por completo e escrever os testes que atendem aos dois itens
   do checklist de `specs/02-ingestion-service.md §4`: (a) o script não gera nenhuma mensagem quando o modo
   mock está desabilitado; (b) conecta ao broker e inicia o loop assíncrono de publicação quando habilitado.
3. Rodar a suíte completa do backend e confirmar verde, sem nenhuma mudança de comportamento no código de
   produção.
4. Marcar (`- [x]`) os itens correspondentes nos dois checklists das specs fixas — só depois do passo 3 verde.
5. Qualquer comportamento estranho ou bug real encontrado durante a escrita dos testes vai para "Achados fora
   do escopo" no resumo — não corrigir aqui.

# 6. Critérios de aceite
- [ ] Os dois itens do checklist de `specs/01-digital-twin-core.md §4` cobertos por teste automatizado verde.
- [ ] Os dois itens do checklist de `specs/02-ingestion-service.md §4` cobertos por teste automatizado verde.
- [ ] Nenhuma linha de `persistence_handler.py`, `mock_provider.py` ou `chaos_generator.py` foi alterada — só
  arquivos de teste novos e os checklists das duas specs fixas.
- [ ] Suíte de testes completa do repositório continua verde (nenhuma regressão).

# 7. Como verificar (uso do revisor)
- `git diff --stat` → só arquivos de teste novos + os `- [ ]` → `- [x]` nas duas specs fixas.
- Rodar a suíte de testes e ler a saída real, item por item contra os dois checklists.
- Confirmar por leitura que nenhum arquivo de produção (`persistence_handler.py`, `mock_provider.py`,
  `chaos_generator.py`) aparece no diff.

# 8. Destino da síntese
**Destino:** `specs/01-digital-twin-core.md` · `specs/02-ingestion-service.md`
Os dois checklists de "Plano de Testes" passam de 100% desmarcados para 100% marcados — a síntese só precisa
confirmar que o `- [x]` já gravado pelo executor bate com o teste real, sem transportar texto novo.

---

# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

## Resumo da execução — 2026-08-22

**Resultado:** Concluído

**O que foi feito**
- Lido `persistence_handler.py` por completo e escritos 8 testes cobrindo `on_message` (payload inválido e
  válido), `TopicResolver.resolve()` (cache hit/miss) e `save_telemetry` (limiar inferior: crítico, aviso e
  dentro do nominal) — `backend/apps/digital_twin_core/tests/test_persistence_handler.py`.
- Lido `mock_provider.py` e `chaos_generator.py` por completo. Descoberto que o gate de `MOCK_ENABLED` citado
  no checklist de `specs/02-ingestion-service.md §4` vive em `ingestion_service/main.py`, não em
  `mock_provider.py`/`chaos_generator.py` (ver "Decisões e suposições"). Escritos:
  - `backend/apps/ingestion_service/tests/test_main.py` — 2 testes para o gate `MOCK_ENABLED` (script
    principal), cobrindo os dois itens literais do checklist.
  - `backend/apps/ingestion_service/tests/test_mock_provider.py` — 4 testes para `MqttMockProvider.connect()`
    e `.publish()` (conexão ao broker e publicação, comportamento citado pelo item (b) do checklist).
  - `backend/apps/ingestion_service/tests/test_chaos_generator.py` — 6 testes para
    `ChaosGenerator.apply_chaos()` (nomeado explicitamente na plan §2), cobrindo os 4 ramos de sensor, o
    ramo "sem chaos roll" e o ramo de `sensor_type` desconhecido.
- Rodada a suíte completa do backend (`python -m pytest backend`) — único diretório de testes do repositório
  hoje é o que acabei de criar; 20/20 testes verdes, 0 warnings, 0 falhas.
- Marcados `- [x]` os 2 itens do checklist de `specs/01-digital-twin-core.md §4` e os 2 itens do checklist de
  `specs/02-ingestion-service.md §4` — autorizado explicitamente pela própria plan (§3.1 e §5.4).

**Arquivos alterados**
| Arquivo | Natureza | O que mudou |
|---|---|---|
| `backend/apps/digital_twin_core/tests/test_persistence_handler.py` | criado | 8 testes de caracterização de `TopicResolver`/`MqttPersistenceHandler` |
| `backend/apps/ingestion_service/tests/test_main.py` | criado | 2 testes do gate `MOCK_ENABLED` em `main.py` |
| `backend/apps/ingestion_service/tests/test_mock_provider.py` | criado | 4 testes de `MqttMockProvider.connect()`/`.publish()` |
| `backend/apps/ingestion_service/tests/test_chaos_generator.py` | criado | 6 testes de `ChaosGenerator.apply_chaos()` |
| `specs/01-digital-twin-core.md` | alterado | 2 itens do checklist "Testes Unitários" `- [ ]` → `- [x]` (linhas 38-39 antes da edição) |
| `specs/02-ingestion-service.md` | alterado | 2 itens do checklist "Testes Unitários" `- [ ]` → `- [x]` (linhas 25-26 antes da edição) |

Nenhuma linha de `persistence_handler.py`, `mock_provider.py` ou `chaos_generator.py` foi tocada — confirmado
por `git diff --stat` (não aparecem no diff).

**Verificações executadas**
- `python -m pytest backend/apps/digital_twin_core/tests backend/apps/ingestion_service/tests -v` → 20 passed,
  1 warning (coroutine não aguardada em `process_message`, corrigida em seguida com `.close()` explícito no
  teste).
- `python -m pytest backend -v` (suíte completa do repositório, rodada depois da correção acima) → **20
  passed, 0 warnings, 0 failures**, 0.68s. Não há nenhum outro diretório de teste no repositório hoje (só
  pacotes em `.venv`), então esta é de fato a suíte completa.
- `git diff --stat -- specs/01-digital-twin-core.md specs/02-ingestion-service.md` e `git diff` (conteúdo) →
  conferido linha a linha; meu diff em `specs/01-digital-twin-core.md` é só as 2 linhas do checklist (o
  arquivo já tinha alterações não commitadas de sessão anterior — bloco "Correção (2026-08-22)" e a frase do
  Telegram — presentes desde antes de eu começar, não escritas por mim). Em `specs/02-ingestion-service.md`
  meu diff é o arquivo inteiro do diff (só as 2 linhas do checklist).
- Leitura manual dos 4 arquivos de teste contra os limiares do `padrao-python`/`padrao-escrita` (função ≤ 40
  linhas, aninhamento ≤ 3, ≤ 4 parâmetros, sem hardcoded de configuração/segredo): nenhuma função passa de ~25
  linhas, aninhamento máximo é 2 (função → `with`/`async with`). O hook `padrao-limiares`/`padrao-format`
  rodou automaticamente em cada `Write`/`Edit` (PostToolUse) e não bloqueou nenhum deles — só avisou que não
  há config de `ruff` na raiz (modo "warn", repositório fora do template de módulos). Não rodei o script
  `validate.py` da skill `padrao-python` manualmente: uma busca por ele no disco não terminou a tempo (comando
  em background, sem impacto no resultado, não usado como evidência).

**Critérios de aceite**
- [x] Os dois itens do checklist de `specs/01-digital-twin-core.md §4` cobertos por teste automatizado verde
  — evidência: `test_persistence_handler.py::test_on_message_invalid_payload_does_not_raise` e
  `::test_save_telemetry_lower_limit_critical_triggers_alert` (+ 2 testes de suporte para o mesmo item),
  todos verdes na saída do pytest acima.
- [x] Os dois itens do checklist de `specs/02-ingestion-service.md §4` cobertos por teste automatizado verde
  — evidência: `test_main.py::test_main_disabled_mock_never_starts_provider` e
  `::test_main_enabled_mock_starts_provider_loop`, verdes na saída do pytest acima.
- [x] Nenhuma linha de `persistence_handler.py`, `mock_provider.py` ou `chaos_generator.py` foi alterada — só
  arquivos de teste novos e os checklists das duas specs fixas — evidência: `git status`/`git diff` acima, os
  três arquivos de produção não aparecem no diff.
- [x] Suíte de testes completa do repositório continua verde (nenhuma regressão) — evidência: `python -m
  pytest backend` → 20 passed, 0 failures.

**Decisões e suposições**
- **Onde testar o gate `MOCK_ENABLED` (achado de ambiguidade na plan, resolvido de forma conservadora).** A
  plan §5.2 manda "ler `mock_provider.py` e `chaos_generator.py`" para atender aos dois itens do checklist
  de `specs/02-ingestion-service.md §4`, mas a lógica real desses dois itens ("não gera mensagem se
  `MOCK_ENABLED == false`" / "conecta e inicia loop se `MOCK_ENABLED == true`") vive em
  `ingestion_service/main.py`, não nos dois arquivos nomeados — confirmado por leitura de `main.py:12-21`.
  `mock_provider.py` não lê `MOCK_ENABLED` em lugar nenhum. Segui a interpretação mais conservadora e de
  menor impacto: escrevi o teste desse comportamento contra `main.py`, mas mantive o arquivo dentro do mesmo
  diretório `backend/apps/ingestion_service/tests/` que a plan já autoriza em §3.1 (não criei teste em nenhum
  módulo fora do escopo declarado). Registrado como comentário no topo de `test_main.py` também.
- **`ChaosGenerator.apply_chaos()` testado apesar de não ser exercitado pelo fluxo real hoje.** A plan nomeia
  `ChaosGenerator.apply_chaos()` explicitamente em §2 como um dos itens a caracterizar; escrevi os 6 testes
  mesmo assim, contra a classe isolada (função pura, sem I/O) — ver achado abaixo sobre o motivo de isso ser,
  na prática, código não usado pelo restante do sistema.
- Testei `save_telemetry` chamando o método diretamente (com `AsyncSessionLocal` trocado por um dublê de
  sessão em memória via `monkeypatch`) em vez de subir um Postgres real — não mockei `TopicResolver` nem o
  cálculo de severidade (a lógica sob teste), só o cliente MQTT (não instanciado em rede) e a sessão de banco,
  como a plan pede em §5.1.
- Não marquei `status: "🟡 Em execução"` no frontmatter *antes* da primeira edição, como manda
  `00-prompt-executor.md §2` — só percebi a omissão depois de já ter escrito os 4 arquivos de teste. Não
  houve impacto no resultado (nenhuma edição concorrente aconteceu), mas registro a falha de processo por
  honestidade.
- O MCP `time-tracking` citado em `CLAUDE.md` ("Regra de Ouro") não apareceu disponível nesta sessão (busca
  por ferramenta não encontrou nenhum MCP correspondente) — não consegui iniciar o cronômetro. Sinalizado ao
  usuário na entrega.

**Achados fora do escopo (não corrigidos)**
- `backend/apps/ingestion_service/adapters/chaos_generator.py` (`ChaosGenerator`, arquivo inteiro) — não é
  importado por nenhum outro módulo do repositório (confirmado por
  `grep -rn "ChaosGenerator|chaos_generator" backend`: só a própria definição da classe aparece).
  `MqttMockProvider._generate_value()` (`mock_provider.py:34-77`) reimplementa uma lógica de caos equivalente
  e independente, sem usar `ChaosGenerator`. É código morto/duplicado — candidato a remoção (junto com a
  `plan-05`, que já remove outros órfãos de `digital_twin_core`) ou a uma plan de consolidação que faça
  `MqttMockProvider` reusar `ChaosGenerator` de fato. Não corrigido aqui — fora do escopo desta plan.
- `MqttMockProvider.publish()` (`mock_provider.py:30-32`) descarta a mensagem silenciosamente quando
  `is_connected == False`, sem log de erro nem tentativa de reconexão — caracterizado por
  `test_publish_is_noop_when_not_connected`. Comportamento atual documentado, não é bug óbvio (é o design
  atual), mas é um ponto de fragilidade silenciosa que um futuro refactor deveria considerar corrigir com
  log/retry. Não corrigido aqui.

**Pendências / riscos**
- Nenhuma pendência conhecida nos 4 critérios de aceite. Risco residual: os testes de `save_telemetry`/
  `TopicResolver` usam um dublê de sessão assíncrona escrito à mão (não uma sessão SQLAlchemy real nem
  Testcontainers) — caracteriza o comportamento de negócio corretamente, mas não pega uma eventual regressão
  de SQL/schema real; isso é escopo de `test-integracao-api`, não desta plan de caracterização unitária.

---

# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->

## Veredito — 2026-08-22 — 🟢 Aprovado

**Verificado diretamente no worktree** (o resumo do executor foi conferido, não tomado como evidência):

- `git status`/`git diff --stat` da árvore inteira, isolando a contribuição desta execução das minhas próprias
  edições de rodadas anteriores (que já estavam no worktree antes do executor começar).
- `git diff --stat` direcionado a `persistence_handler.py`, `mock_provider.py`, `chaos_generator.py` e
  `ingestion_service/main.py` → **vazio nos quatro** — nenhuma linha de produção foi tocada.
- `git diff` completo de `specs/01-digital-twin-core.md` e `specs/02-ingestion-service.md` → em cada um, a
  única contribuição do executor são os 2 checkboxes `- [ ]` → `- [x]` do "Plano de Testes"; o resto do diff
  (bloco "Correção (2026-08-22)", frase do Telegram) já era meu, de antes desta execução.
- Li os 4 arquivos de teste novos por completo e conferi cada asserção linha a linha contra o código real de
  `save_telemetry`, `apply_chaos` e o gate `MOCK_ENABLED` de `main.py` — todas corretas, sem mockar a lógica
  sob teste (só cliente MQTT e sessão de banco).
- Rodei a suíte eu mesmo: `python -m pytest backend -v` → **20 passed, 0 failed**, confirma o número alegado.
- Busca por `test_*.py`/`*_test.py` em todo o repositório → confirma que são de fato os únicos 4 arquivos de
  teste hoje; a alegação "suíte completa = 20 testes" procede.
- Sem `TODO`/`FIXME`/skip/debug nos arquivos novos; nenhuma função passa de ~25 linhas nem de 2 níveis de
  aninhamento (dentro dos limiares do `padrao-escrita`).

**Critérios de aceite:** os 4 — todos atendidos, com evidência (ver tabela acima do próprio resumo, conferida
por mim linha a linha).

**Sobre o desvio de mapeamento de arquivo** (`main.py` testado em vez de só `mock_provider.py`/
`chaos_generator.py` para o item do `MOCK_ENABLED`): correto. Confirmei por leitura que o gate realmente vive
em `main.py:12-21` — imprecisão minha ao escrever a plan §2/§5.2, não desvio do executor. Interpretação
conservadora, declarada explicitamente, dentro do diretório de teste já autorizado. Não é achado.

**Achados fora do escopo registrados (não corrigidos, corretamente):** `ChaosGenerator` é código morto
duplicado por `MqttMockProvider._generate_value()`; `MqttMockProvider.publish()` descarta mensagem
silenciosamente quando desconectado, sem log/retry. Ambos ficam como candidatos a plan futura — não abro plan
agora, registro aqui para não se perder.

**Pendências sem peso no veredito:** executor não marcou `🟡 Em execução` antes da primeira edição
(autorreportado, sem impacto no resultado); cronômetro MCP `time-tracking` indisponível nesta sessão (já
sinalizado por mim antes da execução começar).

**Liberação:** `plan-01-iot-ingestion` e `plan-06-alerta-telegram-backend` dependiam desta plan — ambas
liberadas para execução a partir de agora.
