---
tipo: "spec"
titulo: "Migração do Simulador para C++ (ESP32 via Wokwi/PlatformIO)"
dominio: "Ingestion Service / Firmware"
status: "🔴 A Implementar"
prioridade: "Alta"
tags: ["spec", "iot", "firmware", "mqtt"]
relacionados: []
---

# 1. Visão Geral
Atualmente, a simulação dos nós IoT (ESP32) é feita puramente em software através de um script Python (`mock_provider.py`) no backend. O objetivo desta funcionalidade é desativar o simulador em Python e delegar a geração de dados e anomalias para o firmware C++ real do ESP32 (`iot_firmware/src/main.cpp`), rodando via simulador online Wokwi ou hardware físico via PlatformIO. 

**Requisito de Ouro:** É imperativo que a capacidade do Frontend de alterar o intervalo de medição em tempo real (via slider no painel geral) continue funcionando perfeitamente de forma integrada.

# 2. Regras de Negócio
- **Regra 1: Sincronia de Configuração (Backend -> ESP32):** Quando o Frontend enviar um `POST /api/config` para alterar o intervalo de tempo de medição (`measurement_interval_ms` / `simulation_speed`), a API (`api/index.py`), além de gravar no arquivo físico `simulator_config.json`, deve publicar um payload MQTT com as novas configurações em um tópico reservado de controle (Ex: `forzy/config/device`).
- **Regra 2: Subscrição e Ajuste Dinâmico (ESP32):** O firmware do ESP32 deve assinar (subscribe) o tópico `forzy/config/device`. Ao receber um novo comando de intervalo, ele deve processar o JSON recebido, atualizar sua variável interna do temporizador (`delay`) e aplicar a nova frequência no próximo ciclo do `loop()`.
- **Regra 3: Geração de Dados e Caos Contínua:** O script `main.cpp` manterá sua lógica autônoma de variação randômica e injeção de caos (chance de gerar alertas críticos), sem depender de comandos do backend para fabricar o "ruído" matemático.
- **Regra 4: Desativação do Mock em Python:** O `mock_provider.py` original deverá ser desativado ou condicionado a uma flag de ambiente (ex: `SIMULATION_MODE=HARDWARE`) para evitar corrida de dados ou duplicação de mensagens MQTT no tópico do motor.

# 3. Critérios de Aceite
- [ ] O backend passa a publicar atualizações de configuração via MQTT sempre que a rota `/api/config` é acionada.
- [ ] O ESP32 no Wokwi/PlatformIO assina o tópico de configuração no momento do boot.
- [ ] O ESP32 consegue decodificar o payload de configuração (usando a lib `ArduinoJson`) e ajusta a frequência de envio sem necessitar de reinicialização (reboot).
- [ ] A aba "Painel Geral" no frontend não perde funcionalidade, sendo capaz de controlar a cadência (velocidade) da telemetria do hardware virtual de forma transparente.

# 4. Plano de Testes (Quality Gate)

## Testes Unitários
- [ ] **Deve** (Firmware C++) testar se a função de `callback` MQTT no ESP32 atualiza a variável global de atraso apenas se o JSON for válido e contiver a chave correta.
- [ ] **Deve** (Firmware C++) manter o valor de tempo original caso o payload MQTT seja malformado ou inválido.

## Testes de Contrato (API)
- [ ] **Endpoint** `POST /api/config`: Validar se o disparo do método interno de publicação MQTT ocorre sempre com o schema exato que o ESP32 espera consumir.

## Testes E2E (Integração)
- [ ] Fluxo feliz: Usuário altera a "Frequência de Atualização" no slider do Dashboard; após 2 segundos, o log do ESP32 no Wokwi acusa recebimento do novo comando e altera o ritmo de publicação imediatamente.
