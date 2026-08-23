---
tipo: "processo"
titulo: "Índice de Execução — Mapa das Plans"
dominio: "Governança de Specs (SDD)"
status: "🟢 Vigente"
tags: ["processo", "indice", "sdd"]
relacionados: ["[[00-contexto]]", "[[00-prompt-revisor]]", "[[00-prompt-executor]]"]
proximo_numero_plan: "18" # NN da próxima plan a nascer. Só sobe. Nunca reaproveitado, mesmo que uma plan
                           # seja depois removida por síntese — ver §5.
---

# 0. O que é este arquivo

O **mapa de execução** do repositório: a ordem em que as specs de `plan/` devem ser executadas, suas
dependências e o estado de cada uma. Responde a três perguntas, sempre:

1. **O que executo agora?** (a primeira `🔴 A executar` da §1 sem dependência pendente)
2. **O que já foi aprovado e está esperando síntese?** (as `🟢 Aprovada` da §4)
3. **Para onde cada plan vai depois?** (coluna *Destino*)

A estrutura reflete a das pastas — **duas tabelas, duas pastas**:

| Seção | Pasta | Contém |
|---|---|---|
| **§1 Fila de execução** | `plan/` | O que está em jogo: 🔴 🟡 🟠 🔵 ⛔ |
| **§4 Aguardando síntese** | `plan/executadas/` | Só `🟢 Aprovada`. Fila de espera, **não histórico** — a linha some daqui no instante em que a plan é sintetizada (§2) |

> ⚠️ **Este arquivo é um molde com instruções embutidas.** Os blocos `> **Como escrever:**` **permanecem** no
> arquivo como contrato de manutenção; as tabelas começam vazias e são mantidas pelo **agente revisor**.

**Quem escreve/atualiza:** o **agente revisor** ([[00-prompt-revisor]]) — mais a skill `spec-atualizar`, que
**remove** a linha da §4 (e o arquivo do disco) ao concluir a síntese.
**Quando atualizar:** ao criar uma plan (nova linha na §1 + `proximo_numero_plan` sobe), ao reprovar (status),
ao **aprovar** (linha migra para a §4 junto com o arquivo) e ao sintetizar (linha e arquivo **removidos** —
§2). **Toda mudança de status vive aqui e na própria plan — as duas, sempre, na mesma ação, exceto a remoção
final, que apaga a própria plan.**

---

# 1. Fila de execução — plans **ativas** (`plan/`)

> **Como escrever:** uma linha por plan que ainda está em jogo, **em ordem de execução** — a ordem da tabela
> **é** o plano; não use a numeração para ordenar. Espelha exatamente os arquivos na **raiz** de `plan/`.
> Colunas obrigatórias, nesta ordem:
>
> - **#** — posição na fila (1, 2, 3…). Reordenável.
> - **Plan** — link relativo: `[plan-NN-slug](plan/plan-NN-slug.md)`.
> - **Objetivo** — uma linha, no infinitivo. O que muda no sistema.
> - **Depende de** — `plan-NN` que precisa estar `🟢 Aprovada` antes, ou `—`.
> - **Status** — um dos valores da §2. **Igual** ao frontmatter da plan.
> - **Destino** — para onde o conteúdo é sintetizado depois (§3).
>
> Ao aprovar uma plan, a linha **sai desta tabela e vai para a §4** — junto com o arquivo, que é movido para
> `plan/executadas/`. **Localização física e seção deste índice andam sempre juntas.**

| # | Plan | Objetivo | Depende de | Status | Destino |
|---|---|---|---|---|---|
| 1 | [plan-01-iot-ingestion](plan/plan-01-iot-ingestion.md) | Migrar produtor de telemetria do Mock Python para ESP32 real — código pronto e testado (24+3 testes verificados por mim), falta só o dono validar no Wokwi/hardware o "Requisito de Ouro" (slider→ESP32 sem reboot) | plan-11-caracterizar-legado-telemetria 🟢 | 🟣 Verificação do dono | specs/02-ingestion-service.md |
| 2 | [plan-05-limpeza-digital-twin-core](plan/plan-05-limpeza-digital-twin-core.md) | Remover código órfão de `digital_twin_core` e reconciliar listener MQTT duplicado | — | 🔴 A executar | arquitetura/02-backend-eda.md |
| 3 | [plan-06-alerta-telegram-backend](plan/plan-06-alerta-telegram-backend.md) | Mover o gatilho do alerta Telegram do frontend para `persistence_handler.py` | plan-11-caracterizar-legado-telemetria 🟢 | 🔴 A executar | specs/specs/02-notificacao-telegram.md · specs/01-digital-twin-core.md |
| 4 | [plan-07-telemetry-tempo-real](plan/plan-07-telemetry-tempo-real.md) | Ligar a aba Telemetria ao WebSocket real | — | 🔴 A executar | — |
| 5 | [plan-08-anomalias-marcar-lido](plan/plan-08-anomalias-marcar-lido.md) | Implementar resolução de anomalias e filtro em Anomalies | — | 🔴 A executar | specs/03-asset-manager.md |
| 6 | [plan-09-catalogs-novo-item](plan/plan-09-catalogs-novo-item.md) | Implementar formulário de criação de item em Catalogs | — | 🔴 A executar | specs/03-asset-manager.md |
| 7 | [plan-10-history-filtros-export](plan/plan-10-history-filtros-export.md) | Implementar filtros e exportação CSV em History | — | 🔴 A executar | — |

---

# 2. Legenda de status

| Status | Significado | Pasta | Quem move para cá |
|---|---|---|---|
| 🔴 A executar | Spec escrita e liberada. Aguarda executor. | `plan/` | revisor (ao criar) |
| 🟡 Em execução | Executor trabalhando. | `plan/` | executor (ao iniciar) |
| 🟠 Em revisão | Execução concluída no worktree, aguardando veredito. | `plan/` | executor (ao entregar) |
| 🔵 Em correção | Reprovada. Prompt de correção emitido, executor refazendo. | `plan/` | revisor (ao reprovar) |
| ⛔ Bloqueada | Impedida por dependência externa/decisão pendente. **Exige motivo** na coluna Objetivo. | `plan/` | revisor |
| 🟣 Verificação do dono | Execução e verificação automática do revisor **esgotadas** (código correto, testado, nada mais que um agente alcance) — falta só validação manual do dono em ambiente que nenhum agente atinge (hardware físico, simulador visual, serviço externo interativo). **Exige o passo a passo exato** que o dono precisa fazer, escrito no veredito. | `plan/` | revisor |
| 🟢 Aprovada | Verificada pelo revisor. Pronta para o usuário commitar e para a síntese. | **`plan/executadas/`** | revisor (ao aprovar — move o arquivo) |
| ⚪ Sintetizada | Absorvida nas specs fixas pela skill `spec-atualizar`. Estado **transitório**: existe só no instante entre "acrescentar o bloco de síntese" e "remover o arquivo", na mesma passada — ver [[spec-atualizar]] | — (arquivo removido) | quem conduziu a síntese |

> Um status só avança na ordem `🔴 → 🟡 → 🟠 → (🔵 ⇄ 🟠) → 🟣 → 🟢 → ⚪`. **🔵 não volta para 🔴** — correção não
> é execução nova; a plan e o histórico de vereditos são os mesmos. **🟣 é diferente de ⛔**: ⛔ é dependência ou
> decisão que trava o **início ou a continuação** do trabalho (nada rodou ainda, ou não pode rodar); 🟣 é
> quando o trabalho **já rodou e já foi verificado** até o limite do que um agente alcança, e só falta o dono
> confirmar com as próprias mãos. 🟣 volta para `🟢` (dono confirma que funcionou) ou para `🔵` (dono reporta
> que não funcionou — vira achado real, prompt de correção).
>
> **A aprovação move o arquivo; a síntese o remove.** `plan/` guarda o que está em jogo; `plan/executadas/`
> guarda só o que terminou e ainda não foi sintetizado. É isso que impede a raiz de `plan/` de virar um
> depósito. O rastro completo de uma plan já sintetizada (contexto, resumo do executor, veredito) só existe
> depois no histórico do **Git** — a spec fixa de destino é a verdade vigente; a plan removida é a evidência
> de como se chegou lá, recuperável com `git log --diff-filter=D -- specs/plan/executadas/plan-NN-*.md`.

---

# 3. Coluna *Destino* — valores válidos

Toda plan declara, **desde o momento em que é escrita**, para onde seu conteúdo será sintetizado:

| Valor | Quando usar |
|---|---|
| `arquitetura/NN-<nome>.md` | Mudou design estrutural, stack, fronteira de módulo, contrato de API. |
| `adr/NNN-<nome>.md` | Foi tomada uma decisão técnica com trade-off. **ADR é imutável** — decisão nova = ADR novo. |
| `specs/NN-<nome>.md` | Mudou regra de negócio ou comportamento de funcionalidade. |
| `00-contexto.md` | Mudou regra inegociável, stack ou mapa de roteamento. |
| **`—` (nenhum)** | Execução que não altera verdade documentada: correção de bug sem mudança de regra, refactor de conformidade, ajuste de build/CI, limpeza. |

> Vários destinos são permitidos (`arquitetura/03-api.md` + `adr/004-...`). `—` é uma resposta legítima e
> comum — **não invente destino** só para preencher a coluna.

---

# 4. Aguardando síntese — plans aprovadas (`plan/executadas/`)

> **Como escrever:** duas etapas — mas a segunda **remove** a linha em vez de completá-la.
>
> 1. **Ao aprovar** (revisor): mova a linha da §1 para cá, preencha *Aprovada em* com a **data absoluta**
>    (`AAAA-MM-DD`), status `🟢`, ajuste o link para `plan/executadas/…` e carregue o `destino_sintese` da
>    plan para a coluna *Destino declarado* (já estava preenchido desde a criação — só migra junto).
> 2. **Ao sintetizar** (skill `spec-atualizar`): a plan recebe o bloco `## Síntese` e o status `⚪` **no
>    arquivo**, a skill remove o arquivo do disco (`git rm`, sem commit) e, na mesma passada, **apaga esta
>    linha da tabela**. Nada fica marcado `⚪` aqui — a linha simplesmente deixa de existir.
>
> Esta tabela é uma **fila de espera**, não histórico: só contém `🟢` aguardando processamento. Espelha
> exatamente os arquivos hoje presentes em `plan/executadas/`. O histórico de por que o repositório é como é
> vive na spec fixa de destino (verdade consolidada) e, em detalhe, no **Git** — não nesta tabela.

| Plan | Status | Aprovada em | Destino declarado |
|---|---|---|---|
| [plan-11-caracterizar-legado-telemetria](plan/executadas/plan-11-caracterizar-legado-telemetria.md) | 🟢 | 2026-08-22 | specs/01-digital-twin-core.md · specs/02-ingestion-service.md |
| [plan-02-catalog-intelligence](plan/executadas/plan-02-catalog-intelligence.md) | 🟢 | 2026-08-22 | specs/03-asset-manager.md |
| [plan-04-knowledge-rag](plan/executadas/plan-04-knowledge-rag.md) | 🟢 | 2026-08-22 | specs/05-ai-knowledge.md |
| [plan-03-vision-ocr](plan/executadas/plan-03-vision-ocr.md) | 🟢 | 2026-08-22 | specs/04-vision-ocr.md |
| [plan-12-vision-estruturacao-llm](plan/executadas/plan-12-vision-estruturacao-llm.md) | 🟢 | 2026-08-22 | specs/04-vision-ocr.md |
| [plan-13-llm-fallback-config](plan/executadas/plan-13-llm-fallback-config.md) | 🟢 | 2026-08-22 | specs/03-asset-manager.md · specs/04-vision-ocr.md · specs/05-ai-knowledge.md |
| [plan-14-agente-conversacional](plan/executadas/plan-14-agente-conversacional.md) | 🟢 | 2026-08-22 | specs/05-ai-knowledge.md · specs/06-agente-conversacional.md |
| [plan-15-unificar-listagem-manuais](plan/executadas/plan-15-unificar-listagem-manuais.md) | 🟢 | 2026-08-23 | specs/05-ai-knowledge.md |
| [plan-16-rag-recuperacao-completa-base-pequena](plan/executadas/plan-16-rag-recuperacao-completa-base-pequena.md) | 🟢 | 2026-08-23 | specs/05-ai-knowledge.md |
| [plan-17-aumentar-limite-upload-manual](plan/executadas/plan-17-aumentar-limite-upload-manual.md) | 🟢 | 2026-08-23 | — |

> Exemplo de linha, enquanto aguarda síntese:
> `| [plan-05-tabela-sessions](plan/executadas/plan-05-tabela-sessions.md) | 🟢 | 2026-07-28 | arquitetura/04-dados.md · adr/003-jwt-vs-sessao.md |`
>
> Assim que `spec-atualizar` processa esta plan, a linha inteira desaparece da tabela — não vira `⚪`.

---

# 5. Regras de manutenção

- **Numeração é monotônica e definitiva.** `plan-07` é `plan-07` para sempre, mesmo depois de removida por
  síntese. **Nunca renumere** nem reaproveite um `NN`. O próximo número livre é **sempre** o valor do campo
  `proximo_numero_plan` no frontmatter deste arquivo — nunca o descubra escaneando `plan/` e
  `plan/executadas/`, porque plans já sintetizadas somem das duas. Ao criar uma plan: use o valor atual do
  campo e **incremente-o** na mesma ação.
- **Linha da §1 nunca é removida em silêncio.** Plan abandonada vira `⛔ Bloqueada` com o motivo (e fica em
  `plan/`); plan aprovada migra para a §4. A **única** remoção de linha deste índice é a da §4, e só acontece
  no instante da síntese (§2, §4) — é uma remoção **esperada**, não uma exceção à regra.
- **Mover o arquivo e mover a linha é uma só ação.** Aprovou → `git mv` para `plan/executadas/` **e** linha da
  §1 para a §4, na mesma passada. Arquivo em `executadas/` com linha na §1 (ou o inverso) é índice quebrado.
  A mesma disciplina vale na síntese: `git rm` do arquivo **e** remoção da linha da §4, juntos — nunca um sem
  o outro.
- **`plan/executadas/` é esvaziada a cada rodada de síntese.** Só guarda `🟢` aguardando processamento — nunca
  acumula `⚪`. Isso é intencional (ver [[spec-atualizar]]), não uma limpeza avulsa: a única rotina autorizada
  a remover arquivo de plan é essa, e só depois de a síntese estar de fato aplicada e confirmada por HITL.
- **Status duplicado é status divergente.** O valor aqui e no frontmatter da plan são atualizados na **mesma
  ação**. Divergiu? A **plan** é a fonte da verdade e este índice está errado — corrija aqui. (Exceção: depois
  de removida, a plan não existe mais para consultar — a última verdade fica no commit de remoção, no Git.)
- **Dependência é contrato:** não libere (`🔴`) uma plan cuja dependência não esteja `🟢` (ainda em
  `plan/executadas/`) — uma vez sintetizada e removida, a dependência já está embutida na spec fixa de
  destino, então deixa de ser um "plan-NN" e passa a ser essa spec.
- **Uma plan `🟡 Em execução` por vez**, salvo plans comprovadamente disjuntas (arquivos sem interseção) — o
  revisor declara a disjunção ao liberar as duas.
- **Só o revisor edita este arquivo** — exceto a remoção de linha da §4, feita por quem conduz a skill
  `spec-atualizar`. O **executor nunca o toca**; ele escreve apenas na plan que executou.
