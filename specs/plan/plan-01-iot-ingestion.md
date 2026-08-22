---
tipo: "plan"
titulo: "Migrar produtor de telemetria do Mock Python para ESP32 real (Wokwi/PlatformIO)"
dominio: "ingestion_service"
status: "🟣 Verificação do dono"
prioridade: "Alta"
tags: ["plan", "iot", "mqtt", "esp32", "wokwi"]
relacionados: ["[[specs/02-ingestion-service]]", "[[specs/specs/03-migracao-simulador-esp32]]"]
depende_de: "plan-11-caracterizar-legado-telemetria"
destino_sintese: "specs/02-ingestion-service.md"
---

> **Revisado em 2026-08-22.** Esta plan foi reescrita antes de qualquer execução (status seguia 🔴) para
> absorver o escopo de `specs/specs/03-migracao-simulador-esp32.md`, que descrevia o mesmo objetivo
> (mock → Wokwi/PlatformIO) sem se referenciar à plan original. Consolidação decidida com o usuário — não
> execute a partir da versão antiga desta plan, se ela estiver em cache de alguma conversa anterior.
> Passou a depender de `plan-11-caracterizar-legado-telemetria`: esta plan edita `ingestion_service/main.py` e
> o produtor mock, código legado hoje sem nenhum teste automatizado — a caracterização vem primeiro.

# 1. Objetivo
O sistema passa a receber telemetria de um firmware ESP32 real (via Wokwi ou hardware físico com
PlatformIO), publicando em MQTT no lugar do `MqttMockProvider` em Python — com o slider de intervalo de
medição do Painel Geral continuando a controlar a cadência do hardware virtual em tempo real, sem
reinicialização.

# 2. Contexto
O `digital_twin_core/persistence_handler.py` (o motor real de anomalias — ver `specs/01-digital-twin-core.md`,
corrigida em 2026-08-22) já consome qualquer publicação em `Forzy/telemetry/#`, seja ela do mock ou de
hardware real — a mudança é só na ponta produtora. Hoje `backend/apps/ingestion_service/main.py` sempre
instancia `MqttMockProvider` (`adapters/mock_provider.py`), que só publica, nunca consome. `iot_firmware/` já
tem um esqueleto PlatformIO (`platformio.ini`, `include/config.h`, `src/main.cpp`) — não é código a criar do
zero, é a base a completar. O Frontend já publica `POST /api/config` (`api/index.py:80-100`), hoje só
gravando `backend/simulator_config.json`; falta ele também publicar em MQTT para o ESP32 ouvir.

# 3. Escopo
## 3.1 Dentro
- `backend/apps/ingestion_service/main.py` e `adapters/*` — condicionar `MqttMockProvider` a uma flag de
  ambiente (ex.: `SIMULATION_MODE=MOCK|HARDWARE`) que, em `HARDWARE`, desliga o publisher Python sem derrubar
  o processo (Regra 4 da spec referenciada).
- `backend/shared_infra/config.py` — adicionar a variável de ambiente nova ao `pydantic-settings`, com
  `.env.example` atualizado (Fail-Fast, zero valor inferido).
- `api/index.py` — rota `POST /api/config`: além de gravar `simulator_config.json`, publicar o novo intervalo
  no tópico de controle MQTT (Regra 1 da spec referenciada — ex.: `forzy/config/device`).
- `iot_firmware/src/main.cpp`, `iot_firmware/include/config.h` — assinar o tópico de controle, decodificar o
  payload com `ArduinoJson`, ajustar o timer/`delay` sem reboot, manter a geração de caos autônoma (Regras 2 e
  3 da spec referenciada).

## 3.2 Fora
- `backend/apps/digital_twin_core/persistence_handler.py` — o motor de anomalias não muda; ele já é agnóstico
  à origem da publicação MQTT.
- `backend/apps/asset_manager/*` — nenhuma rota nem modelo muda.
- O slider em si no frontend (`Dashboard.tsx`) — não altere sua UI, só valide que continua funcionando fim-a-fim.

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Spec fixa | `specs/specs/03-migracao-simulador-esp32.md` | Regras de negócio 1-4, critérios de aceite e plano de testes completos do firmware/config — não duplicados aqui |
| Spec fixa | `specs/02-ingestion-service.md` | Regra atual do `MOCK_ENABLED`, a ser substituída/complementada |
| Spec fixa | `specs/01-digital-twin-core.md` | Confirma que `persistence_handler.py` é agnóstico à origem MQTT |
| Contexto | `00-contexto.md` (Fail-Fast de Configurações, §2) · `00-knowledge.md` | sempre |
| Skill | `padrao-escrita` + `padrao-python` | Backend (Nível 0 e 2) |
| Skill | `test-unitario` | Testes do callback MQTT no firmware e da lógica de flag no `ingestion_service` |
| Skill | `test-integracao-api` | Validar que `POST /api/config` de fato publica no broker MQTT (não só grava o JSON) |
| Código | `backend/apps/ingestion_service/main.py`, `adapters/mock_provider.py` | ler antes de editar |
| Código | `iot_firmware/src/main.cpp`, `include/config.h` | ler antes de editar — não é um esqueleto vazio |

# 5. Instruções de execução
1. Implementar a Regra 4 da spec referenciada: nova variável `SIMULATION_MODE` em `shared_infra/config.py`
   (Pydantic, com default seguro documentado) — em `HARDWARE`, `ingestion_service/main.py` não instancia
   `MqttMockProvider`, mas permanece rodando (loop inofensivo) para não derrubar o container/processo.
2. Implementar a Regra 1: `POST /api/config` em `api/index.py` publica o payload de configuração no tópico
   MQTT de controle, além de gravar `simulator_config.json` como já faz hoje.
3. Implementar as Regras 2 e 3 no firmware (`iot_firmware/src/main.cpp`): assinar o tópico de controle no
   boot, decodificar com `ArduinoJson`, atualizar a variável de atraso sem reboot, manter a lógica autônoma de
   caos/ruído já existente.
4. Escrever os testes descritos no §4 "Plano de Testes" de `specs/specs/03-migracao-simulador-esp32.md`
   (unitário do callback MQTT do firmware — payload válido e malformado; contrato do `POST /api/config`).
5. Validar manualmente (Wokwi ou hardware físico) que alterar o slider no Painel Geral reflete no ritmo de
   publicação do ESP32 em até poucos segundos, sem reinicialização.
6. Não tocar em `digital_twin_core` nem `asset_manager`.

# 6. Critérios de aceite
- [ ] `SIMULATION_MODE=HARDWARE` desliga o `MqttMockProvider` sem derrubar o processo de ingestão.
- [ ] `POST /api/config` publica no tópico MQTT de controle com o schema que o ESP32 espera.
- [ ] O ESP32 (Wokwi/PlatformIO) assina o tópico no boot e ajusta a frequência de envio sem reboot.
- [ ] O slider do Painel Geral continua controlando a cadência do hardware virtual de forma transparente.
- [ ] Testes unitários (firmware — payload válido/malformado) e de contrato (`POST /api/config`) verdes.

# 7. Como verificar (uso do revisor)
- `git diff --stat` → apenas os caminhos de §3.1; nada em `digital_twin_core/` ou `asset_manager/`.
- Ler `specs/specs/03-migracao-simulador-esp32.md`, critério por critério, contra o diff.
- Rodar os testes indicados e ler a saída real.
- Conferir que `SIMULATION_MODE` está documentada em `.env.example` e lida via `shared_infra/config.py`
  (nenhum valor hardcoded).

# 8. Destino da síntese
**Destino:** `specs/02-ingestion-service.md` + `specs/specs/03-migracao-simulador-esp32.md`
Atualizar `02-ingestion-service.md` trocando a regra do `MOCK_ENABLED` binário pela nova flag `SIMULATION_MODE`
e o fluxo de sincronização de config via MQTT. Mudar o status de `specs/specs/03-migracao-simulador-esp32.md`
para `🟢 Implementado` (ela deixa de precisar de plan própria — esta a supera integralmente).

---

# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

## Resumo da execução — 2026-08-22

**Resultado:** Concluído com pendências

**O que foi feito**
- **Achado inicial, antes de editar qualquer coisa:** por leitura completa do código-alvo (§4 da plan),
  confirmei que as Regras 1, 2 e 3 de `specs/specs/03-migracao-simulador-esp32.md` **já estavam
  implementadas** no worktree, antes desta execução — não escritas por mim:
  - Regra 1 (`api/index.py:84-100`, `update_config`): já publica `{"measurement_interval_ms": interval*1000}`
    em `Forzy/config/device` via `mqtt_client.publish`, além de gravar `simulator_config.json`.
  - Regras 2 e 3 (`iot_firmware/src/main.cpp`, original): `reconnect()` já assinava
    `MQTT_CONFIG_TOPIC` no boot; `mqtt_callback` já decodificava o JSON com `ArduinoJson` e atualizava
    `delay_interval` sem reboot, guardado por `!error && containsKey(...)`; o `loop()` já mantinha a
    geração de caos autônoma. Só a **Regra 4** (`SIMULATION_MODE`) realmente faltava.
  - Só toquei nesse código já-pronto para o mínimo necessário: extrair a lógica de parsing do
    `mqtt_callback` para uma função pura testável (ver abaixo) — comportamento idêntico, não uma reescrita.
- **Regra 4** — `backend/shared_infra/config.py`: novo campo `simulation_mode: Literal["MOCK", "HARDWARE"]`
  (Pydantic, Fail-Fast — valor fora do enum derruba `Settings()` na inicialização), lido de `SIMULATION_MODE`
  via `os.getenv`, default `"MOCK"` (preserva o comportamento atual sem a variável definida).
- `backend/apps/ingestion_service/main.py:12-19` — trocado `os.getenv("MOCK_ENABLED", "true").lower() ==
  "false"` (lido direto, fora do Pydantic — violava "Fail-Fast de Configurações" do `00-contexto.md §2`) por
  `settings.simulation_mode == "HARDWARE"`. Removido `import os`, que ficou sem uso.
- `backend/apps/ingestion_service/tests/test_main.py` — reescrito para testar o novo gate (mesma cobertura:
  2 testes, "HARDWARE não inicia o provider" / "MOCK inicia e aguarda `start_loop`"), já que o comportamento
  que os testes de caracterização da `plan-11` documentavam (`MOCK_ENABLED`) deixou de existir por decisão
  explícita desta plan (§8: "trocando a regra do `MOCK_ENABLED` binário pela nova flag"). Não reduzi a
  cobertura: são os dois mesmos cenários, só adaptados ao mecanismo novo. `test_mock_provider.py` e
  `test_chaos_generator.py` (também da `plan-11`) ficaram intocados — o comportamento que eles caracterizam
  não mudou.
- `iot_firmware/lib/config_parser/{config_parser.h,config_parser.cpp}` (novo) — extraí a lógica de parsing do
  `mqtt_callback` para `try_parse_measurement_interval(payload, length, out_interval_ms)`: mesmo guard clause
  (`error || !containsKey(...)` → `false`, não altera `out_interval_ms`), agora testável isoladamente e
  reusada por `main.cpp`. Fica em `lib/` (não `src/`/`include/`) porque é a única forma de o PlatformIO linkar
  o mesmo código tanto no build normal quanto no build de teste sem duplicar/filtrar fontes.
- `iot_firmware/src/main.cpp` — `mqtt_callback` passa a chamar `try_parse_measurement_interval`; resto do
  arquivo (WiFi, reconnect, loop de telemetria/caos) intocado.
- `iot_firmware/platformio.ini` — novo `[env:native]` (`platform = native`) para rodar os testes de
  `config_parser` no desktop, sem hardware/Wokwi.
- `iot_firmware/test/test_config_parser/test_main.cpp` (novo) — 3 testes Unity: payload válido atualiza o
  intervalo; JSON malformado mantém o valor original; JSON válido sem a chave esperada também mantém o valor
  original (os dois itens do "Plano de Testes" de `specs/specs/03-migracao-simulador-esp32.md §4`, com um
  caso extra para o segundo ramo do guard clause).
- `api/tests/test_config_endpoint.py` (novo) — 3 testes de contrato para `POST /api/config` com
  `mqtt_client.publish` mockado: schema exato publicado quando há `interval`; nada publicado quando não há;
  `simulator_config.json` continua sendo gravado.
- `api/tests/test_config_mqtt_integration.py` (novo) — 1 teste de integração **contra o broker Mosquitto real**
  que já estava rodando neste ambiente (`docker ps` mostrou `Forzy_mqtt_broker` ativo em `localhost:1883`):
  sobe um subscriber MQTT de verdade no tópico `Forzy/config/device`, dispara `POST /api/config` via
  `TestClient` (usado como context manager para acionar o `startup_event` real da API, que conecta o
  `mqtt_client` de produção ao broker), e confirma que a mensagem `{"measurement_interval_ms": 7000}` chega de
  fato no assinante — não só que `.publish()` foi chamado. Pulado automaticamente
  (`pytest.mark.skipif`) se o broker não estiver acessível, para não quebrar a suíte em ambiente sem
  `docker-compose up -d`.
- `.env.example` (novo) — todas as variáveis de `Settings` documentadas, incluindo `SIMULATION_MODE`.
- `.gitignore:12` — adicionada a exceção `!.env.example`; o padrão `.env.*` (linha 11) ignorava até o próprio
  `.env.example` que a plan pede para manter atualizado — sem a exceção, o arquivo nunca seria versionado.

**Instalação de ferramenta (ação de sistema, fora do repositório)**
- Não havia nenhum compilador C++ nesta máquina (nem `g++`, nem `cl.exe`/MSVC) — só o PlatformIO em si. Sem
  compilador, eu não conseguiria rodar `pio test -e native` e teria que entregar os 3 testes do firmware como
  pendência não verificada. **Perguntei ao usuário como proceder** (`AskUserQuestion`); ele escolheu instalar
  um toolchain. Rodei `winget install --id=BrechtSanders.WinLibs.POSIX.UCRT` (MinGW-w64, ~poucos minutos) e,
  com isso, **rodei `pio test -e native` de verdade** — ver Verificações abaixo. O toolchain fica instalado na
  máquina (fora do repositório, não versionado, não faz parte do diff) — avise se quiser que eu o remova.

**Arquivos alterados**
| Arquivo | Natureza | O que mudou |
|---|---|---|
| `backend/shared_infra/config.py` | alterado | campo `simulation_mode: Literal["MOCK","HARDWARE"]` (Regra 4) |
| `backend/apps/ingestion_service/main.py` | alterado | gate `MOCK_ENABLED` → `settings.simulation_mode`, `import os` removido |
| `backend/apps/ingestion_service/tests/test_main.py` | alterado | 2 testes adaptados ao novo gate (mesma cobertura) |
| `iot_firmware/src/main.cpp` | alterado | `mqtt_callback` usa `try_parse_measurement_interval` |
| `iot_firmware/platformio.ini` | alterado | `[env:native]` para testes desktop |
| `.gitignore` | alterado | exceção `!.env.example` |
| `iot_firmware/lib/config_parser/config_parser.h` | criado | assinatura da função pura extraída |
| `iot_firmware/lib/config_parser/config_parser.cpp` | criado | lógica de parsing extraída, comportamento idêntico ao original |
| `iot_firmware/test/test_config_parser/test_main.cpp` | criado | 3 testes Unity (payload válido/malformado/sem chave) |
| `api/tests/test_config_endpoint.py` | criado | 3 testes de contrato (mock) de `POST /api/config` |
| `api/tests/test_config_mqtt_integration.py` | criado | 1 teste de integração contra o broker MQTT real |
| `.env.example` | criado | template de todas as env vars de `Settings`, incluindo `SIMULATION_MODE` |

Confirmado por `git status`: nada em `backend/apps/digital_twin_core/` nem `backend/apps/asset_manager/`.
`api/index.py` não aparece no diff (Regra 1 já existia — só ganhou teste).

**Verificações executadas**
- `python -m pytest backend api/tests -v` → **24 passed**, 0 failures (inclui os 20 testes de caracterização
  da `plan-11`, intocados e ainda verdes, mais os 4 novos: 2 do gate `SIMULATION_MODE`, 3 de contrato de
  `POST /api/config` — 1 já contado acima é o de integração real).
- `pio test -e native` (PlatformIO + MinGW-w64 recém-instalado, rodado via PowerShell) → **3 testes Unity
  passaram de verdade**: `test_valid_payload_with_key_updates_interval`,
  `test_malformed_json_keeps_original_interval`, `test_valid_json_without_expected_key_keeps_original_interval`
  — `native:test_config_parser [PASSED]`. Únicos avisos: deprecação do `StaticJsonDocument`/`containsKey` do
  ArduinoJson 7.4.3 (a própria lib recomenda `JsonDocument`/`.is<T>()`) — mesmo padrão já usado no código
  original antes da minha extração, não é regressão minha; registrado como achado abaixo.
- `git status`/`git diff --stat` da árvore inteira → conferido que o diff bate exatamente com a tabela acima;
  nada em `digital_twin_core/`, `asset_manager/` ou fora do §3.1 da plan além dos testes e do `.env.example`/
  `.gitignore` (companions necessários, ver "Decisões e suposições").
- Leitura manual dos arquivos Python/C++ novos ou alterados contra os limiares do `padrao-python`/
  `padrao-escrita` (função ≤ 40 linhas, aninhamento ≤ 3, ≤ 4 parâmetros, zero hardcoded): nenhuma função
  passa de ~15 linhas; `simulation_mode` é Pydantic Fail-Fast, não um valor hardcoded. Hooks
  `padrao-format`/`padrao-limiares` rodaram em cada `Write`/`Edit` (Python) sem bloquear nada — só reformatou
  automaticamente `config.py` (black-style: quebra de linha, espaçamento), sem mudança semântica além da
  minha própria edição (conferido linha a linha no `git diff`).
- **Não executado:** passo 5 da plan ("Validar manualmente via Wokwi ou hardware físico que o slider reflete
  no ritmo do ESP32 em poucos segundos, sem reboot") — sem acesso a Wokwi/hardware físico neste ambiente. Ver
  "Pendências" abaixo.
- **Não executado:** build completo do firmware para o alvo real `esp32dev` (só o `native`, com a lib
  isolada). Buildar `esp32dev` exigiria baixar o toolchain Xtensa/Espressif (pacote grande, não instalado);
  não é exigido pelos critérios de aceite da plan (que pedem os testes unitários + validação manual via
  Wokwi/hardware, não uma compilação cruzada nesta máquina) — não pedi autorização para isso por não ser
  necessário para nenhum critério.

**Critérios de aceite**
- [x] `SIMULATION_MODE=HARDWARE` desliga o `MqttMockProvider` sem derrubar o processo de ingestão — evidência:
  `test_main.py::test_main_hardware_mode_never_starts_provider`, verde.
- [x] `POST /api/config` publica no tópico MQTT de controle com o schema que o ESP32 espera — evidência: os 3
  testes de `test_config_endpoint.py` (contrato) + `test_config_mqtt_integration.py` (broker real), todos
  verdes; já era comportamento existente, agora coberto por teste.
- [x] O ESP32 (Wokwi/PlatformIO) assina o tópico no boot e ajusta a frequência sem reboot — comportamento já
  existia em `main.cpp` (`reconnect()`/`mqtt_callback`); a lógica de decodificação agora está isolada e
  **testada de verdade** via `pio test -e native` (3/3 verdes). A assinatura no boot em si (linha
  `client.subscribe(MQTT_CONFIG_TOPIC)` dentro de `reconnect()`) não mudou e não tem teste unitário próprio
  (depende de rede real) — validação real é o passo 5, não executado (ver Pendências).
- [ ] O slider do Painel Geral continua controlando a cadência do hardware virtual de forma transparente —
  **não verificado**: exige Wokwi ou hardware físico rodando `main.cpp` de ponta a ponta, indisponível neste
  ambiente. O teste de integração real (`test_config_mqtt_integration.py`) prova a metade backend do fluxo
  (o comando chega ao broker no formato certo); a metade firmware (ESP32 realmente reagindo) não foi validada
  end-to-end.
- [x] Testes unitários (firmware) e de contrato (`POST /api/config`) verdes — evidência: `pio test -e native`
  (3/3) e `pytest api/tests` (4/4), ambos rodados de verdade, saída lida.

**Decisões e suposições**
- **Regras 1-3 já implementadas — não refeitas.** A plan instruía "Implementar as Regras 1, 2 e 3", mas eram
  código de produção já existente no worktree antes desta execução (não escrito por mim, nem por uma execução
  anterior desta mesma plan — o `git log`/histórico não mostra commit dessa plan, então presumo que o
  time/usuário já tinha avançado essa parte fora do ciclo SDD). Decisão: **não reescrever o que já está
  correto** — só adicionei cobertura de teste e, no firmware, o refactor mínimo para tornar a lógica testável.
  Isso é uma leitura, não uma suposição arriscada: confirmada por leitura linha a linha do código antes de
  qualquer edição.
- **`lib/` em vez de `src/`/`include/` para `config_parser`.** Tentei primeiro `include/config_parser.h` +
  `src/config_parser.cpp` com `build_src_filter` no `[env:native]`; `pio test -e native` compilou os dois
  `.o` mas **falhou no link** (`undefined reference`) porque o build de teste do PlatformIO, por padrão, não
  inclui `src/` (para não colidir com `setup()/loop()` do `main.cpp`, ausentes no ambiente `native`). Migrei
  para `lib/config_parser/` — convenção oficial do PlatformIO para código compartilhado entre `src/` e
  `test/` — e o link passou a funcionar. Confirmado empiricamente, não é uma escolha estética.
- **Instalação do MinGW-w64**, depois de perguntar e o usuário escolher essa opção (ver seção própria acima).
- **Teste de integração real contra o broker** (`test_config_mqtt_integration.py`) foi decisão minha, não
  pedida explicitamente linha a linha pela plan além de citar a skill `test-integracao-api` e o texto "de fato
  publica no broker MQTT (não só grava o JSON)". Descobri que o Mosquitto do `docker-compose.yml` já estava
  rodando neste ambiente (`docker ps`) e aproveitei para validar contra infraestrutura real, não só mock —
  mais fiel ao que a skill pede. O teste se autopula (`skipif`) se o broker não estiver no ar, para não
  quebrar a suíte em outra máquina.
- **`.gitignore`/`.env.example` fora da lista literal do §3.1**, mas necessários para cumprir a instrução
  explícita "com `.env.example` atualizado" do próprio passo 1 da plan — sem a exceção no `.gitignore`, o
  arquivo pedido nunca seria rastreável. Interpretação conservadora, menor mudança possível (uma linha).
- **Não editei `specs/02-ingestion-service.md` nem `specs/specs/03-migracao-simulador-esp32.md`**, apesar do
  §8 "Destino da síntese" da plan descrever o que deveria mudar neles. Diferente da `plan-11` (que autorizava
  explicitamente, em §3.1 e como passo de execução em §5, marcar checkboxes nas specs fixas), esta plan só
  menciona a síntese em §8 — que é destino para o processo de síntese do revisor/`spec-atualizar`, não uma
  instrução de execução para mim (`00-prompt-executor.md §7.3`: nunca editar outra spec fora do que a própria
  plan autoriza explicitamente como passo). Deixo para o revisor decidir/fazer isso na aprovação.

**Achados fora do escopo (não corrigidos)**
- `iot_firmware/lib/config_parser/config_parser.cpp` usa `StaticJsonDocument`/`doc.containsKey(...)` — API do
  ArduinoJson 7.x marcada como **deprecated** (o próprio compilador avisa: usar `JsonDocument` e
  `doc["k"].is<T>()`). Preservei porque é exatamente a API que o `mqtt_callback` original já usava — mudar
  agora seria alterar comportamento/estilo fora do pedido desta plan. Candidato a uma limpeza futura pequena.
- `api/index.py:351` usa `@app.on_event("startup")`, depreciado pelo FastAPI em favor de `lifespan` — não é
  novo (já existia), só ficou visível como warning nos meus testes novos (`TestClient` o exercita). Não
  corrigido — fora do escopo desta plan (Regra 1 já funcionava; não pedi para modernizar o ciclo de vida da
  app).
- `api/index.py:282-358` continua com o listener MQTT duplicado (a própria API reimplementa resolução de
  tópico e broadcast, paralelo ao `persistence_handler.py`) — já registrado em `00-contexto.md §8` como
  pendência coberta pela `plan-05`, não tocado aqui (fora do escopo declarado, e a `plan-05` é quem deve
  reconciliar isso).

**Pendências / riscos**
- **Passo 5 da plan (validação manual via Wokwi/hardware) não executado** — risco real: o backend está
  provadamente correto (teste de integração contra broker real) e o parsing do firmware está provadamente
  correto (teste unitário nativo), mas ninguém validou o **caminho completo** (ESP32 de verdade recebendo o
  comando MQTT, reagindo sem reboot, e o slider do Dashboard refletindo isso em poucos segundos). Isso cobre
  a maior fatia de risco que sobra nesta plan; recomendo que o revisor trate isso como bloqueio para
  aprovação plena, ou aprove com essa pendência explícita a critério do usuário.
- Toolchain MinGW-w64 instalado nesta máquina fora do controle do repositório — não é um risco para o
  código, mas é uma mudança de ambiente que o usuário deve saber que ficou.
- `main.cpp` nunca foi compilado para o alvo real `esp32dev` nesta execução (só a lib isolada em `native`) —
  risco baixo (o arquivo mudou pouco, só a chamada à função extraída), mas não é uma prova de compilação para
  hardware real.

---

# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->

## Veredito — 2026-08-22 — 🟣 Verificação do dono (não é reprovação nem aprovação)

**Verificado diretamente no worktree:**

- `git status`/`git diff --stat` → só os arquivos da tabela do resumo; nada em `digital_twin_core/` nem
  `asset_manager/`; `api/index.py` de fato fora do diff.
- Li `api/index.py:79-100` e `iot_firmware/src/main.cpp` (versão anterior, via `git diff`) por completo:
  confirmo que as Regras 1, 2 e 3 de `specs/specs/03-migracao-simulador-esp32.md` já existiam antes desta
  execução, exatamente como o resumo alega. A decisão de não reescrever o que já funcionava é a correta.
- Reproduzi o Fail-Fast da Regra 4 eu mesmo: `SIMULATION_MODE=BOGUS python -c "from backend.shared_infra.config
  import Settings; Settings()"` → `pydantic_core.ValidationError: Input should be 'MOCK' or 'HARDWARE'`.
  Confirma a Regra 4 de verdade, não só por leitura de código.
- Rodei a suíte Python eu mesmo: `python -m pytest backend api/tests -v` → **24 passed** — bate com o alegado,
  inclusive o teste de integração contra o broker Mosquitto real (não foi pulado; broker estava acessível).
- Rodei o teste do firmware eu mesmo: `pio test -e native` → **3/3 passed**, mesmos avisos de depreciação do
  ArduinoJson citados no resumo. (Nota operacional: o MinGW-w64 instalado pelo executor está mesmo no disco —
  só não estava no `PATH` desta sessão nova; adicionei manualmente para rodar o teste. Não é um achado sobre a
  execução, é uma particularidade de sessões novas não herdarem PATH atualizado pelo instalador.)
- Li os 4 testes Python novos/alterados e os 3 testes Unity do firmware linha a linha contra o código real —
  todos corretos, sem mockar a lógica sob teste.
- `.env.example` conferido: sem segredo, todos os campos batem com `Settings`.

**Critérios de aceite — 4 de 5 atendidos com evidência real:**
- [x] `SIMULATION_MODE=HARDWARE` desliga o publisher sem derrubar o processo.
- [x] `POST /api/config` publica no tópico MQTT com o schema esperado.
- [x] Parsing do firmware testado de verdade (`pio test -e native`, 3/3) — mas a assinatura no boot e a reação
  do hardware real não têm teste unitário possível (dependem de rede/hardware).
- [x] Testes unitários e de contrato verdes — confirmado por mim, não só pelo resumo.
- [ ] **Slider do Painel Geral → ESP32 real, sem reboot** ("Requisito de Ouro" da spec original) — não
  verificado, e **nenhum agente tem como verificar neste ambiente** (sem Wokwi, sem hardware físico; nem existe
  ainda um projeto Wokwi pronto no repo — não há `diagram.json`). Isso não é um achado no código: é uma
  lacuna estrutural do próprio critério que eu escrevi na plan, sem prever que seria inexecutável por um
  agente.

**Decisão:** não aprovo (o critério de ouro segue sem evidência) nem reprovo/mando corrigir (não há nada de
código para o executor corrigir — o gap é de ambiente, não de implementação). Marco `🟣 Verificação do dono`
(status novo, criado nesta rodada em `00-indice.md §2` — distinto de `⛔ Bloqueada`: aqui o trabalho já rodou e
já foi verificado até o limite do que um agente alcança). O trabalho de código desta plan está correto e
testado; falta só a validação humana abaixo.

**Ação pendente, exclusivamente sua (usuário), para eu poder aprovar:**
1. Montar um projeto Wokwi (ou hardware físico) com `iot_firmware/src/main.cpp` + `platformio.ini` do
   ambiente real (`esp32dev`), apontando para o broker MQTT deste ambiente.
2. Alterar o intervalo pelo slider do Painel Geral e confirmar visualmente, pelo monitor serial do
   Wokwi/hardware, que o novo intervalo chega e é aplicado sem reboot, em poucos segundos.
3. Me contar o resultado (ou colar o log serial) — se bater, aprovo direto sem precisar de nova rodada de
   execução; se não bater, é achado real e viro reprovação com prompt de correção.

**Sem liberar `plan-05` a `plan-10`** — nenhuma delas depende de `plan-01`, seguem liberadas normalmente.
