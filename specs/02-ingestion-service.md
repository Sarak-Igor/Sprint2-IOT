---
tipo: "spec"
titulo: "Serviço de Ingestão de Dados"
dominio: "ingestion_service"
status: "🟢 Implementado"
prioridade: "Alta"
tags: ["spec", "backend", "ingestion", "mqtt"]
relacionados: ["[[01-digital-twin-core]]"]
---

# 1. Visão Geral
Gateway de entrada que simula (Mock) ou facilita a conexão do tráfego MQTT provindo do ESP32/Hardware real para o ecossistema. Funciona como um gerador de caos simulado na ausência de hardware físico.

# 2. Regras de Negócio
- **Modo Hardware Ativo vs Mock:** Controlado estritamente via variável de ambiente `MOCK_ENABLED`. Se `false`, o script desliga o gerador e entra em loop inofensivo apenas para não derrubar o container, deixando o hardware físico mandar mensagens reais.
- **Geração de Caos (Mock):** O `MqttMockProvider` instancia um loop assíncrono que publica valores aleatórios variando em torno dos parâmetros ideais dos motores, gerando eventualmente picos para acionar o detector de anomalias no core.

# 3. Critérios de Aceite
- [x] O script principal `main.py` respeita `MOCK_ENABLED`.
- [x] O provedor MQTT consegue conectar de forma estável no Eclipse Mosquitto.
- [x] Valores gerados seguem a especificação de fábrica.

# 4. Plano de Testes (Quality Gate)
## Testes Unitários
- [ ] **Deve** manter o script rodando sem gerar mensagens se `MOCK_ENABLED == false`.
- [ ] **Deve** conectar no MQTT e iniciar o loop assíncrono se `MOCK_ENABLED == true`.
