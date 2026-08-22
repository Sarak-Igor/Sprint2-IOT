---
tipo: "plan"
titulo: "Implementar formulário de criação de item em Catalogs"
dominio: "asset_manager"
status: "🔴 A executar"
prioridade: "Média"
tags: ["plan", "asset_manager", "frontend"]
relacionados: []
depende_de: "—"
destino_sintese: "specs/03-asset-manager.md"
---

# 1. Objetivo
O operador consegue criar modelos de motor, variáveis de dado e hardware de sensor pela aba "Catálogos",
usando os endpoints que o backend já expõe.

# 2. Contexto
`frontend/src/pages/Catalogs.tsx` já lista (`GET /api/assets/models|variables|sensors`) e deleta
(`DELETE /api/assets/{type}/{id}`) — mas o botão "Novo Item" (`Catalogs.tsx:97-100`) não tem handler nem
formulário. O backend já expõe `POST /assets/models`, `POST /assets/variables` e `POST /assets/sensors`
(`backend/apps/asset_manager/web/router.py:27-53`) — não é preciso criar rota nova, só o formulário.

# 3. Escopo

## 3.1 Dentro
- `frontend/src/pages/Catalogs.tsx` — adicionar modal/formulário de criação, um por tipo de catálogo
  (modelo/variável/sensor), reaproveitando os componentes de formulário já usados em `DigitalTwin.tsx`
  (`:104-123`) como referência de padrão, se aplicável.

## 3.2 Fora
- Qualquer rota de backend em `asset_manager` — todas já existem, não altere `router.py`.
- `Assets.tsx`, `Anomalies.tsx`, `History.tsx` — cobertos por outras plans.

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Contexto | `00-contexto.md` · `00-knowledge.md` | sempre |
| Skill | `padrao-escrita` + `padrao-typescript` | sempre |
| Skill | `test-unitario` | Cobrir o formulário novo (submissão válida/inválida) |
| Código | `backend/apps/asset_manager/web/router.py:27-53` | Schema exato esperado por cada `POST` |
| Código | `backend/apps/asset_manager/domain/entities.py` | Campos obrigatórios de cada entidade a validar no formulário |
| Código | `frontend/src/pages/DigitalTwin.tsx:104-123` | Padrão de formulário/modal já usado no repositório |

# 5. Instruções de execução
1. Ler os schemas Pydantic de `POST /models`, `POST /variables`, `POST /sensors` para saber os campos
   obrigatórios exatos de cada formulário.
2. Implementar o modal/formulário de "Novo Item" em `Catalogs.tsx`, com validação client-side mínima
   (campos obrigatórios) espelhando o schema do backend — sem duplicar regra de negócio, só validação de
   formulário.
3. Ligar o botão "Novo Item" (`:97-100`) ao formulário e, no submit, chamar o `POST` correspondente ao tipo
   selecionado na aba ativa.
4. Cobrir com teste unitário o formulário (submissão válida e submissão com campo faltando).

# 6. Critérios de aceite
- [ ] "Novo Item" abre um formulário funcional para cada um dos três tipos (modelo/variável/sensor).
- [ ] O submit chama o `POST` correto e a lista é atualizada após sucesso.
- [ ] Erro de validação do backend é exibido ao usuário, não engolido silenciosamente.
- [ ] Teste unitário do formulário verde.

# 7. Como verificar (uso do revisor)
- `git diff --stat` → só `Catalogs.tsx` (e arquivo de teste novo).
- Ler o componente e conferir que os campos batem com o schema Pydantic de cada rota.
- Rodar o teste novo e ler a saída.

# 8. Destino da síntese
**Destino:** `specs/03-asset-manager.md`
Mesma spec de destino de `plan-02` e `plan-08` — acumula bloco próprio na síntese.

---

# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

---

# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->
