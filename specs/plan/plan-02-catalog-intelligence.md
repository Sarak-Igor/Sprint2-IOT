---
tipo: "plan"
titulo: "Inteligência de Catálogo de Ativos com LLM"
dominio: "asset_manager"
status: "🔴 A executar"
prioridade: "Alta"
tags: ["plan", "llm", "assets"]
relacionados: ["[[arquitetura/03-asset-manager]]"]
depende_de: "—"
destino_sintese: "specs/03-asset-manager.md"
---
# 1. Objetivo
Implementar o módulo `asset_manager` criando endpoints de adição de motor que usam LLM via OpenRouter para identificar e preencher as informações base estruturais a partir de inputs básicos.

# 2. Contexto
A aba "Assets" atualmente só lista e deleta. Precisamos da capacidade de inputar um novo motor e deixar o LLM enriquecer os dados técnicos cruciais (RPM nominal, potência, IP) antes de gravar no DB, criando assim perfis de máquina reais.

# 3. Escopo
## 3.1 Dentro
- `backend/apps/asset_manager/*` (Endpoints FastAPI e integração Langchain/OpenRouter)
- `frontend/src/pages/Assets.tsx` (Formulário/Modal de novo ativo)

## 3.2 Fora
- Domínios de Telemetria e Vision.

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Contexto | `00-contexto.md` (Fail-Fast de Configurações, §2) · `00-knowledge.md` | sempre |
| Skill | `cyber-ia` | segurança na chamada ao LLM (prompt injection via texto livre do usuário) |
| Skill | `padrao-python` + `padrao-typescript` | regras base |
| Skill | `test-unitario` | Cobrir o endpoint novo (mock da chamada ao LLM, não da rota) |
| Código | `backend/shared_infra/config.py` | onde a chave da API do LLM deve ser lida via Pydantic — nunca hardcoded |

# 5. Instruções de execução
1. Adicionar a variável da chave de API do LLM (ex.: `OPENROUTER_API_KEY`) em `backend/shared_infra/config.py`
   via `pydantic-settings`, com entrada correspondente em `.env.example` — Fail-Fast, zero valor inferido ou
   hardcoded (`00-contexto.md §2`).
2. Criar o endpoint `POST /api/assets` no `asset_manager` acoplado ao LangChain (OpenRouter).
3. O prompt de LLM deve deduzir informações do motor a partir de marca/modelo ou texto livre.
4. No Frontend, adicionar botão "Novo Ativo" e modal em `Assets.tsx`.
5. Escrever teste unitário do endpoint com a chamada ao LLM mockada (não gastar chamada real em CI).

# 6. Critérios de aceite
- [ ] Chave de API do LLM configurada via `shared_infra/config.py`/`.env`, sem valor hardcoded.
- [ ] Cadastro no Frontend chama o Backend.
- [ ] Backend chama OpenRouter e processa payload.
- [ ] Ativo é salvo na tabela e listado.
- [ ] Teste unitário do endpoint verde.

# 7. Como verificar (uso do revisor)
- Avaliar os arquivos tocados (só frontend e asset_manager).
- Inspecionar a segurança do prompt (Skill `cyber-ia`).

# 8. Destino da síntese
**Destino:** `specs/03-asset-manager.md`
Criação da spec oficial de Catálogo Inteligente.

---
# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

---
# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->
