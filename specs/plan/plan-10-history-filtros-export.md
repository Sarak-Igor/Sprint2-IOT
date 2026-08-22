---
tipo: "plan"
titulo: "Implementar filtros e exportação CSV em History"
dominio: "frontend"
status: "🔴 A executar"
prioridade: "Baixa"
tags: ["plan", "frontend", "historico"]
relacionados: []
depende_de: "—"
destino_sintese: "—"
---

# 1. Objetivo
O operador consegue filtrar o histórico de telemetria por ativo/variável/período e exportar a visualização
atual em CSV — hoje ambos os botões existem na tela sem nenhum efeito.

# 2. Contexto
`frontend/src/pages/History.tsx` já consome dados reais via `GET /api/telemetry?limit=50` (`api/index.py:
113-179`, join real com `TelemetryReadingDB`/`ActiveAssetDB`/`DataVariableDB`). Os botões "Filtros"
(`:32-34`) e "Exportar CSV" (`:35-37`) não têm handler.

# 3. Escopo

## 3.1 Dentro
- `api/index.py` — rota `GET /api/telemetry`: aceitar query params opcionais de filtro (ex.: `asset_id`,
  `variable_id`, `start`, `end`), mantendo compatibilidade com chamadas sem esses params (comportamento atual
  preservado).
- `frontend/src/pages/History.tsx` — implementar UI de filtro (chamando a rota com os novos params) e
  exportação CSV (gerada no cliente, a partir dos dados já carregados — não precisa de rota nova para o CSV).

## 3.2 Fora
- `TelemetryReadingDB`/`ActiveAssetDB`/`DataVariableDB` (schema) — nenhuma migration necessária, os filtros
  usam colunas já existentes.
- `Anomalies.tsx`, `Catalogs.tsx` — cobertos por outras plans.
- `backend/apps/asset_manager/*` — a rota de telemetria vive em `api/index.py`, não em `asset_manager`; não
  mova a rota de lugar nesta plan (fora de escopo — se achar que deveria mover, registre em "Achados fora do
  escopo").

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Contexto | `00-contexto.md` · `00-knowledge.md` | sempre |
| Skill | `padrao-escrita` + `padrao-python` + `padrao-typescript` | Backend e frontend |
| Skill | `test-unitario` | Cobrir os novos query params da rota e a geração do CSV |
| Skill | `test-integracao-api` | Validar o filtro contra banco real |
| Código | `api/index.py:113-179` | Rota atual a estender, não substituir |
| Código | `frontend/src/pages/History.tsx` | ler o componente inteiro antes de editar |

# 5. Instruções de execução
1. Estender `GET /api/telemetry` com query params opcionais de filtro, todos com default que preserva o
   comportamento atual (sem filtro = lista os últimos 50 como hoje).
2. Implementar a UI de filtro em `History.tsx`, chamando a rota com os params escolhidos pelo operador.
3. Implementar "Exportar CSV" gerando o arquivo no cliente a partir dos dados já carregados na tela (sem
   round-trip novo ao backend só para exportar).
4. Escrever testes dos novos query params (unitário/integração) e do gerador de CSV (unitário).

# 6. Critérios de aceite
- [ ] `GET /api/telemetry` sem filtro continua devolvendo exatamente o que devolve hoje (sem regressão).
- [ ] Filtro por ativo/variável/período funciona e reflete na tabela.
- [ ] "Exportar CSV" gera um arquivo com os dados atualmente visíveis na tela.
- [ ] Testes novos (backend e frontend) verdes.

# 7. Como verificar (uso do revisor)
- `git diff --stat` → só os caminhos de §3.1.
- Rodar a rota sem filtro e comparar a resposta com o comportamento documentado atual (sem regressão).
- Rodar os testes novos e ler a saída real.
- Ler o gerador de CSV e confirmar que não depende de nenhuma rota nova.

# 8. Destino da síntese
**Destino:** `—`
Filtro e exportação são extensões de uma rota já documentada (não uma regra de negócio nova) — não há spec
fixa de "histórico" para atualizar.

---

# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

---

# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->
