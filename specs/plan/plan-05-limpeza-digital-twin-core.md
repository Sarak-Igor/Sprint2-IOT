---
tipo: "plan"
titulo: "Remover código órfão de digital_twin_core e reconciliar listener MQTT duplicado"
dominio: "digital_twin_core"
status: "🔴 A executar"
prioridade: "Média"
tags: ["plan", "limpeza", "arquitetura"]
relacionados: ["[[specs/01-digital-twin-core]]", "[[arquitetura/02-backend-eda]]"]
depende_de: "—"
destino_sintese: "arquitetura/02-backend-eda.md"
---

# 1. Objetivo
O repositório deixa de conter código-fonte órfão em `digital_twin_core/`, e a duplicação de listener MQTT
entre `persistence_handler.py` e `api/index.py` fica resolvida ou explicitamente justificada.

# 2. Contexto
Diagnóstico de 2026-08-22 (`00-contexto.md §8`) confirmou, por varredura de importações e dos scripts de
subida (`RUN_FORZY.bat`, `package.json`, `docker-compose.yml`):
- `backend/apps/digital_twin_core/main.py` — FastAPI app na porta 8010 com todos os endpoints retornando
  `random.*`; nenhum script o inicializa (`RUN_FORZY.bat:43` sobe `api.index:app`, não este arquivo).
- `backend/apps/digital_twin_core/anomaly_logger.py` — `AnomalyEventLogger`, não importado por
  `persistence_handler.py` nem por nenhum outro módulo.
- `backend/apps/digital_twin_core/converters/metric_converter.py` — `MetricConverter`, idem, não importado.
- `backend/apps/digital_twin_core/models.py` — só um comentário `# Deprecated. All models moved to
  asset_manager.infrastructure.models` (linha 1); não precisa de ação, já se autodocumenta.

Em paralelo, existem **dois processos MQTT independentes** assinando `Forzy/telemetry/#`:
`persistence_handler.py` (grava `TelemetryReadingDB`/`OperationalAnomalyDB`) e `api/index.py:282-358`
(`mqtt_client`, só faz broadcast via WebSocket, não persiste nada). Cada um resolve o tópico
independentemente — risco de divergência se a lógica de resolução mudar num lado e não no outro.

**Confirmado com o usuário:** `digital_twin_core` (via `persistence_handler.py`) é a funcionalidade central do
sistema e **não deve ser removido** — só o código comprovadamente órfão acima.

# 3. Escopo

## 3.1 Dentro
- `backend/apps/digital_twin_core/main.py` — remover, ou mover para `backend/apps/digital_twin_core/_legacy/`
  com um `README.md` de uma linha explicando o motivo, se o executor preferir preservar histórico local em vez
  de depender só do `git log` (decisão do executor, registrar no resumo).
- `backend/apps/digital_twin_core/anomaly_logger.py` — idem.
- `backend/apps/digital_twin_core/converters/metric_converter.py` — idem.
- `api/index.py:282-358` (o listener MQTT de broadcast) — **investigar antes de decidir**: ver passo 1 das
  instruções. Só editar se a investigação confirmar que dá para eliminar a duplicação sem quebrar o
  broadcast WebSocket que `Dashboard.tsx`/`DigitalTwin.tsx` consomem.

## 3.2 Fora
- `backend/apps/digital_twin_core/persistence_handler.py` — o motor real, não toque na lógica de negócio dele
  (só pode importar dele, se a consolidação do listener duplicado escolher esse caminho).
- `backend/apps/digital_twin_core/models.py` — já se autodocumenta como deprecated, não precisa de ação.
- `backend/apps/asset_manager/*` — nenhuma rota nem modelo muda.
- Qualquer lógica de negócio de detecção de anomalia — permanece exatamente como está.

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Spec fixa | `specs/01-digital-twin-core.md` | Confirma que `persistence_handler.py` é o motor oficial |
| Spec fixa | `arquitetura/02-backend-eda.md` | Descreve os dois processos e a duplicação encontrada |
| Contexto | `00-contexto.md §8` · `00-knowledge.md` | Achados desta rodada de diagnóstico |
| Skill | `padrao-escrita` + `padrao-python` | sempre |
| Skill | `test-unitario` | Cobrir a consolidação do listener, se ela mudar comportamento observável do WebSocket |
| Código | `backend/apps/digital_twin_core/persistence_handler.py` | ler antes — é o padrão de referência para MQTT |
| Código | `api/index.py:282-373` | ler o bloco inteiro do listener + do `ConnectionManager`/WebSocket antes de tocar |

# 5. Instruções de execução
1. **Investigar antes de agir** no listener duplicado: confirmar que `api/index.py:282-358` de fato não grava
   nada no banco (o diagnóstico já indica isso, mas confirme lendo o arquivo). Se confirmado, avalie duas
   opções e escolha uma, registrando o motivo no resumo:
   - (a) manter os dois listeners, mas fazendo o de `api/index.py` reaproveitar `TopicResolver` de
     `persistence_handler.py` em vez de reimplementar a resolução; ou
   - (b) fazer `persistence_handler.py` publicar o resultado (via um canal interno — fila em memória, Redis
     pub/sub, ou o próprio broadcast do `ConnectionManager` se ele puder ser importado sem acoplar módulos) e
     `api/index.py` deixar de assinar o broker diretamente.
   Se nenhuma das duas for viável sem risco alto, **não force** — documente o porquê no resumo em "Achados
   fora do escopo" e deixe o listener duplicado como está; isso não bloqueia o resto da plan.
2. Confirmar, por `grep` no repositório inteiro (não só `backend/apps/digital_twin_core/`), que `main.py`,
   `anomaly_logger.py` e `converters/metric_converter.py` não são importados em nenhum lugar.
3. Remover (ou arquivar, conforme decisão registrada em §3.1) os três arquivos confirmados órfãos.
4. Rodar a suíte de testes existente e confirmar que nada quebrou (esses arquivos não deveriam ter nenhum
   teste dependente, já que são órfãos — se houver, investigue antes de remover).

# 6. Critérios de aceite
- [ ] `main.py`, `anomaly_logger.py`, `converters/metric_converter.py` removidos ou arquivados com
  justificativa registrada.
- [ ] `grep` confirma zero import remanescente desses três arquivos em qualquer lugar do repositório.
- [ ] Decisão sobre o listener duplicado tomada e registrada (consolidado, ou justificativa para manter como
  está) — não pode ficar em silêncio.
- [ ] Suíte de testes verde após a remoção.
- [ ] `persistence_handler.py` e o WebSocket de telemetria continuam funcionando sem regressão observável.

# 7. Como verificar (uso do revisor)
- `git diff --stat` → só os caminhos de §3.1.
- `grep -r` pelos três símbolos removidos → zero ocorrência fora do histórico do Git.
- Ler o resumo da decisão sobre o listener duplicado e confirmar que faz sentido tecnicamente.
- Rodar a suíte de testes e conferir a saída.

# 8. Destino da síntese
**Destino:** `arquitetura/02-backend-eda.md`
Remover a nota de "reconciliação pendente" adicionada em 2026-08-22 e substituir pela descrição final de como
o listener duplicado foi resolvido (ou pela justificativa formal de mantê-lo como está).

---

# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

---

# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->
