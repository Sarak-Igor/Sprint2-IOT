---
tipo: "plan"
titulo: "Migrar produtor de telemetria do Mock Python para ESP32 real (Wokwi/PlatformIO)"
dominio: "ingestion_service"
status: "🔴 A executar"
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

---

# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->
