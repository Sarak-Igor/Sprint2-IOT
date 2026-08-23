---
tipo: "plan"
titulo: "Aumentar o limite de tamanho de PDF na ingestão de manuais de 20MB para 100MB"
dominio: "ai_knowledge"
status: "🟢 Aprovada"
prioridade: "Baixa"
tags: ["plan", "ai_knowledge", "config", "ajuste"]
relacionados: []
depende_de: "—"
destino_sintese: "—"
---

# 1. Objetivo
`POST /api/knowledge/ingest` passa a aceitar PDFs de até 100MB (hoje rejeita acima de 20MB com
413), para comportar manuais técnicos completos maiores (instalação/operação/manutenção,
escaneados, com muita diagramação).

# 2. Contexto
Pedido direto do usuário: o teto atual de 20MB é baixo demais para os manuais técnicos completos
que ele pretende indexar (diferente do catálogo comercial pequeno já testado). O limite é uma
constante local em `backend/apps/ai_knowledge/router.py:20`
(`MAX_PDF_BYTES = 20 * 1024 * 1024`), no mesmo padrão já usado para o limite de imagem da
`plan-03`/`plan-12` (constante de módulo, não `Settings`/`.env` — não é segredo nem varia por
ambiente). A mensagem de erro (`router.py:62`, `"PDF maior que 20MB"`) está com o número escrito à
mão, solto do valor real da constante — ficaria errada silenciosamente nesta mudança se não for
ajustada junto.

# 3. Escopo

## 3.1 Dentro
- `backend/apps/ai_knowledge/router.py` — `MAX_PDF_BYTES` de `20 * 1024 * 1024` para
  `100 * 1024 * 1024`; a mensagem de erro em `ingest_manual` (413) passa a refletir o valor real da
  constante (não um número escrito à mão — evita a mesma dessincronia que existe hoje).
- `backend/apps/ai_knowledge/tests/test_knowledge_endpoints.py` — ajustar o teste que constrói um
  PDF de "20MB + 1 byte" para o novo teto (100MB + 1 byte), mantendo a cobertura do caminho 413.

## 3.2 Fora
- Qualquer outro limite de tamanho do repositório (ex.: imagem de 10MB em `vision/router.py`,
  mensagem do agente/chat) — não citado pelo pedido, não mexer.
- Lógica de ingestão, chunking, extração de PDF — nenhuma mudança de comportamento além do teto.
- Frontend (`Knowledge.tsx`) — não impõe nenhum limite de tamanho hoje (confirmado por leitura), não
  precisa de alteração.

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Contexto | `00-contexto.md` · `00-knowledge.md` | sempre |
| Skill | `padrao-escrita` + `padrao-python` | sempre |
| Skill | `test-unitario` | ajustar o teste existente do teto, sem perder cobertura do 413 |
| Código | `backend/apps/ai_knowledge/router.py:20,53-62` | ler antes de editar |
| Código | `backend/apps/ai_knowledge/tests/test_knowledge_endpoints.py` | teste do teto atual a ajustar |

# 5. Instruções de execução
1. Alterar `MAX_PDF_BYTES` para `100 * 1024 * 1024` em `router.py`.
2. Trocar a mensagem de erro fixa `"PDF maior que 20MB"` por uma que derive do valor real da
   constante (ex.: f-string com `MAX_PDF_BYTES // (1024*1024)`), para não voltar a dessincronizar se
   o teto mudar de novo no futuro.
3. Ajustar o teste que hoje constrói um payload de "20MB + 1 byte" para o novo teto.
4. Rodar a suíte completa e confirmar verde.

# 6. Critérios de aceite
- [ ] `MAX_PDF_BYTES == 100 * 1024 * 1024`.
- [ ] Upload de PDF entre 20MB e 100MB é aceito (não rejeitado mais por tamanho).
- [ ] Upload acima de 100MB continua rejeitado com 413, mensagem de erro consistente com o valor
  real do teto.
- [ ] Teste do teto atualizado e verde; suíte completa sem regressão.

# 7. Como verificar (uso do revisor)
- `git diff --stat` → só `router.py` e o teste correspondente.
- Ler o novo valor e a mensagem de erro, confirmar que não há número solto dessincronizado da
  constante.
- Rodar a suíte e ler a saída real.

# 8. Destino da síntese
**Destino:** `—`
Ajuste de configuração/limite operacional, sem mudança de regra de negócio ou de arquitetura — nada
para sintetizar em spec fixa.

---

# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

## Resumo da execução — 2026-08-23

**Resultado:** Concluído

**O que foi feito**
- `backend/apps/ai_knowledge/router.py:20` — `MAX_PDF_BYTES` alterado de `20 * 1024 * 1024`
  para `100 * 1024 * 1024` (comentário do lado ajustado de `# 20MB` para `# 100MB`).
- `backend/apps/ai_knowledge/router.py:60-63` — a mensagem de erro do 413 deixou de ser o
  literal fixo `"PDF maior que 20MB"` e passou a derivar do valor real da constante:
  `max_mb = MAX_PDF_BYTES // (1024 * 1024)` seguido de `f"PDF maior que {max_mb}MB"` — não
  há mais número solto dessincronizado da constante, mesma causa raiz descrita no
  contexto da plan.
- `backend/apps/ai_knowledge/tests/test_knowledge_endpoints.py::test_ingest_rejects_oversized_pdf`
  — o payload de teste passou de `20 * 1024 * 1024 + 1` (hardcoded) para
  `knowledge_router_module.MAX_PDF_BYTES + 1` (lê a constante real do router, não repete o
  número) — além de cobrir o novo teto, evita que o teste volte a dessincronizar se o teto
  mudar de novo no futuro (mesmo raciocínio da correção pedida na plan). Adicionei também
  uma asserção sobre o conteúdo da mensagem (`"100MB" in response.json()["detail"]`), que
  o teste anterior não verificava — cobre o critério de aceite "mensagem de erro
  consistente com o valor real do teto" de forma direta, não só o `status_code`.

**Arquivos alterados**
| Arquivo | Natureza | O que mudou |
|---|---|---|
| `backend/apps/ai_knowledge/router.py` | alterado | `MAX_PDF_BYTES` 20MB→100MB; mensagem de erro derivada da constante |
| `backend/apps/ai_knowledge/tests/test_knowledge_endpoints.py` | alterado | teste do teto ajustado ao novo valor (via constante, não número solto) + asserção da mensagem |

**Verificações executadas**
- `python -m pytest backend/apps/ai_knowledge/tests/test_knowledge_endpoints.py -v` → 12
  passed.
- `python -m pytest backend/ -v` (suíte completa) → **75 passed**, 0 falhas, 0 regressão
  (mesmos 75 já verdes antes desta plan — esta plan não somou nem removeu casos de teste,
  só ajustou um existente).
- `git diff -- backend/apps/ai_knowledge/router.py
  backend/apps/ai_knowledge/tests/test_knowledge_endpoints.py` → só as linhas descritas
  acima, conforme §7 da plan ("só `router.py` e o teste correspondente").
- Leitura confirma: nenhum outro número solto de "20MB"/`20 * 1024 * 1024` restante em
  `router.py` (grep visual no diff completo do arquivo).

**Critérios de aceite**
- [x] `MAX_PDF_BYTES == 100 * 1024 * 1024` — evidência: `router.py:20`.
- [x] Upload de PDF entre 20MB e 100MB é aceito — evidência: a única checagem de tamanho é
  `len(pdf_bytes) > MAX_PDF_BYTES`, agora 100MB; nenhuma outra lógica de rejeição por
  tamanho existe no caminho de ingestão (confirmado por leitura de `ingest_manual`
  inteiro).
- [x] Upload acima de 100MB continua rejeitado com 413, mensagem consistente — evidência:
  `test_ingest_rejects_oversized_pdf` (payload de `MAX_PDF_BYTES + 1`, status 413, detail
  contém "100MB").
- [x] Teste do teto atualizado e verde; suíte completa sem regressão — evidência: 75/75
  passed.

**Decisões e suposições**
- Nenhuma decisão fora do que a plan já especificou literalmente — o valor (100MB), a
  forma da mensagem derivada (`MAX_PDF_BYTES // (1024*1024)`) e o arquivo de teste a
  ajustar já vinham definidos na plan (§5, passos 1-3); segui ao pé da letra.
- Troquei o hardcoded `20 * 1024 * 1024 + 1` do teste por
  `knowledge_router_module.MAX_PDF_BYTES + 1` em vez de simplesmente escrever
  `100 * 1024 * 1024 + 1` — não pedido explicitamente na letra do passo 3 ("ajustar o
  teste... para o novo teto"), mas é a leitura mais literal do próprio motivo da plan
  existir (evitar número solto dessincronizado da constante); decisão de baixo risco, no
  mesmo arquivo/mesma linha já dentro do escopo declarado.

**Achados fora do escopo (não corrigidos)**
- Nenhum novo. `vision/router.py` (limite de imagem de 10MB) e qualquer limite do
  agente/chat foram explicitamente citados pela plan como fora de escopo (§3.2) — não
  tocados, não investigados além da leitura já feita por plans anteriores.

**Pendências / riscos**
- Nenhuma. Mudança de constante local, sem efeito colateral fora do endpoint de ingestão
  (confirmado por grep: `MAX_PDF_BYTES` só é referenciado dentro de `router.py`).

---

# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->

## Veredito — 2026-08-23 — 🟢 Aprovado

**Verificado diretamente no worktree:**

- `git diff` de `router.py` e `test_knowledge_endpoints.py` → exatamente as linhas descritas no
  resumo: `MAX_PDF_BYTES` 20MB → 100MB, mensagem de erro derivada da constante
  (`f"PDF maior que {max_mb}MB"`), teste ajustado para ler `knowledge_router_module.MAX_PDF_BYTES`
  em vez de repetir o número, mais a asserção nova sobre o conteúdo da mensagem ("100MB" no detail).
  Nenhum outro arquivo tocado.
- `grep` mental confirmado por leitura do diff completo: nenhum número solto de "20MB"/
  `20 * 1024 * 1024` remanescente em `router.py`.
- Rodei a suíte eu mesmo: `python -m pytest backend/ -q` → **75 passed**, bate exatamente com o
  alegado (mesma contagem de antes — a plan só ajustou um teste existente, não adicionou nem
  removeu casos).

**Critérios de aceite — 4 de 4 atendidos:**
- [x] `MAX_PDF_BYTES == 100 * 1024 * 1024` — confirmado por leitura.
- [x] Aceita entre 20MB e 100MB — única checagem de tamanho no caminho é contra a constante nova.
- [x] Acima de 100MB continua 413, mensagem consistente — teste dedicado, mensagem derivada da
  constante (não pode dessincronizar de novo).
- [x] Teste atualizado e verde, suíte sem regressão — 75/75.

**Sobre a decisão de ler a constante no teste em vez de escrever `100 * 1024 * 1024 + 1`:** correta
— é exatamente o motivo que fez esta plan existir (mensagem antiga dessincronizada do valor real);
mudança de baixo risco, mesmo arquivo já dentro do escopo. Não é achado.

**Liberação:** nenhuma plan da fila depende de `plan-17`.
