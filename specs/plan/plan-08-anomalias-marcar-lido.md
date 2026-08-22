---
tipo: "plan"
titulo: "Implementar resolução de anomalias (marcar como lido) e filtro em Anomalies"
dominio: "asset_manager"
status: "🔴 A executar"
prioridade: "Média"
tags: ["plan", "asset_manager", "anomalias"]
relacionados: ["[[specs/01-digital-twin-core]]"]
depende_de: "—"
destino_sintese: "specs/03-asset-manager.md"
---

# 1. Objetivo
O operador consegue marcar uma anomalia como resolvida pela aba "Anomalias", e filtrar a lista por
status/severidade — ambas ações hoje são botões sem efeito.

# 2. Contexto
`frontend/src/pages/Anomalies.tsx` já lista dados reais via `GET /api/assets/anomalies` (polling a cada 5s).
O campo `is_resolved` já existe no modelo (`backend/apps/asset_manager/infrastructure/models.py:72`,
`OperationalAnomalyDB`), mas **nenhuma rota grava nele** — o botão "Marcar como Lido"
(`Anomalies.tsx:100-102`) não tem handler, e o botão de filtro (`Anomalies.tsx:47-49`) também não.

# 3. Escopo

## 3.1 Dentro
- `backend/apps/asset_manager/web/router.py` — nova rota `PATCH /anomalies/{id}` que grava `is_resolved=true`
  (e opcionalmente `resolved_at`, se o modelo tiver ou puder ganhar esse campo — decida com base no schema
  atual, sem inventar coluna nova sem necessidade).
- `backend/apps/asset_manager/domain/entities.py` — schema Pydantic de request/response da nova rota, se
  necessário.
- `frontend/src/pages/Anomalies.tsx` — ligar o botão "Marcar como Lido" à nova rota (atualização otimista ou
  refetch); implementar o filtro (por severidade e/ou por resolvido/não resolvido) usando os dados já
  carregados no cliente (não precisa de rota nova para o filtro, é client-side sobre o resultado do polling).

## 3.2 Fora
- `backend/apps/digital_twin_core/persistence_handler.py` — não muda; ele continua sendo quem *cria*
  anomalias, esta plan só adiciona a capacidade de *resolver*.
- Qualquer outra rota de `asset_manager` além da nova `PATCH /anomalies/{id}`.
- `Catalogs.tsx` e `History.tsx` — cobertos por plans separadas (plan-09, plan-10).

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Spec fixa | `specs/01-digital-twin-core.md` | Regra de negócio de criação de anomalia, que esta plan complementa com a resolução |
| Contexto | `00-contexto.md` · `00-knowledge.md` | sempre |
| Skill | `padrao-escrita` + `padrao-python` + `padrao-typescript` | Backend e frontend |
| Skill | `test-unitario` | Cobrir a nova rota `PATCH` |
| Skill | `test-integracao-api` | Validar a rota contra banco real (padrão já usado pelas outras rotas do módulo) |
| Código | `backend/apps/asset_manager/web/router.py:116-180` | Padrão de `PATCH` já existente (`/active/{id}`) a seguir |
| Código | `backend/apps/asset_manager/infrastructure/models.py:72` | Campo `is_resolved` já existente |
| Código | `frontend/src/pages/Anomalies.tsx` | ler o componente inteiro antes de editar |

# 5. Instruções de execução
1. Seguir o padrão de `PATCH /active/{id}` (`router.py:116-180`) para criar `PATCH /anomalies/{id}`, gravando
   `is_resolved=true`.
2. No frontend, ligar o botão "Marcar como Lido" (`Anomalies.tsx:100-102`) à nova rota, com atualização da
   lista (otimista ou refetch — decida e registre no resumo).
3. Implementar o filtro (`Anomalies.tsx:47-49`) sobre os dados já em memória (severidade e/ou resolvido).
4. Escrever teste unitário e de integração da nova rota.

# 6. Critérios de aceite
- [ ] `PATCH /anomalies/{id}` grava `is_resolved=true` no banco.
- [ ] O botão "Marcar como Lido" chama a rota e reflete a mudança na UI.
- [ ] O filtro reduz a lista visível conforme o critério escolhido, sem nova chamada de rede desnecessária.
- [ ] Testes unitário e de integração da nova rota verdes.

# 7. Como verificar (uso do revisor)
- `git diff --stat` → só os caminhos de §3.1.
- Ler o diff da nova rota e conferir que segue o padrão de `PATCH /active/{id}`.
- Rodar os testes e ler a saída real.
- Confirmar visualmente (ou por leitura do componente) que o botão e o filtro têm handler funcional.

# 8. Destino da síntese
**Destino:** `specs/03-asset-manager.md`
Esta plan pode ser sintetizada antes ou depois de `plan-02-catalog-intelligence` (mesma spec de destino, ainda
não criada) — a skill `spec-atualizar` acumula os blocos na mesma spec fixa conforme cada plan aprovada for
processada.

---

# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

---

# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->
