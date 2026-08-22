---
tipo: "plan"
titulo: "Acoplar ingestão MQTT a simuladores reais Wokwi/PlatformIO"
dominio: "ingestion_service"
status: "🔴 A executar"
prioridade: "Alta"
tags: ["plan", "iot", "mqtt"]
relacionados: ["[[specs/02-ingestion-service]]"]
depende_de: "—"
destino_sintese: "specs/02-ingestion-service.md"
---

# 1. Objetivo
Desativar o Mock e garantir que o serviço de ingestão se conecte ao broker MQTT preparado para receber dados do ESP32/Simulador real (Wokwi/PlatformIO).

# 2. Contexto
Atualmente, o app exibe uma aba de Painel Geral/Twin/Alertas baseada apenas nos mocks aleatórios gerados quando `MOCK_ENABLED=true`. Precisamos que o sistema receba dados externos verídicos sem quebrar o Twin Core.

# 3. Escopo
## 3.1 Dentro
- `backend/apps/ingestion_service/*`
- Arquivo `.env` ou `config.py` relacionado à flag MOCK.

## 3.2 Fora
- `backend/apps/digital_twin_core/*` (A persistência não muda)

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Spec fixa | `specs/02-ingestion-service.md` | Entender a lógica do Mock_Enabled |
| Contexto | `00-contexto.md` · `00-knowledge.md` | sempre |
| Skill | `padrao-escrita` + `padrao-python` | sempre |

# 5. Instruções de execução
1. Alterar a flag `MOCK_ENABLED` para `false` no script de inicialização / `.env`.
2. Adaptar o `ingestion_service/main.py` para não dropar a conexão MQTT quando no modo de recepção, garantindo escuta estável para o simulador externo.
3. Não tocar no `digital_twin_core`.

# 6. Critérios de aceite
- [ ] MOCK desligado.
- [ ] O broker MQTT recebe as mensagens do Wokwi e o Twin Core as consome normalmente.

# 7. Como verificar (uso do revisor)
- `git diff --stat` → Nenhuma mudança no `digital_twin_core`.
- Verificar se o script de ingestão sobe sem iniciar o loop do `MqttMockProvider`.

# 8. Destino da síntese
**Destino:** `specs/02-ingestion-service.md`
Atualizar o documento indicando que o sistema agora consome oficialmente os canais de hardware emulados.

---

# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

---

# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->
