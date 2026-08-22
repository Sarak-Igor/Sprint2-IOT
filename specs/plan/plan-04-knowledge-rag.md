---
tipo: "plan"
titulo: "Implementar RAG na Knowledge Base"
dominio: "ai_knowledge"
status: "🔴 A executar"
prioridade: "Alta"
tags: ["plan", "rag", "llm"]
relacionados: ["[[arquitetura/04-ai-knowledge]]"]
depende_de: "—"
destino_sintese: "specs/05-ai-knowledge.md"
---
# 1. Objetivo
Tornar a Knowledge Base viva implementando engine de busca semântica (RAG) no módulo `ai_knowledge` e respondendo através da aba correspondente.

# 2. Contexto
O módulo `ai_knowledge` e a página `Knowledge.tsx` estão estáticos e sem conexão real. O sistema precisa permitir subir novos PDFs de manuais e responder perguntas técnicas.

# 3. Escopo
## 3.1 Dentro
- `backend/apps/ai_knowledge/*` (Motor de Embeddings e conversação).
- `frontend/src/pages/Knowledge.tsx` (Conexão à RAG e Upload de Manuais).

## 3.2 Fora
- Demais abas do Frontend.

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Contexto | `00-contexto.md` · `00-knowledge.md` | sempre |
| Skill | `cyber-ia` | proteção contra prompt injection |
| Skill | `padrao-python` + `padrao-typescript` | regras base |

# 5. Instruções de execução
1. Criar backend RAG em `ai_knowledge` usando ChromaDB/FAISS e OpenRouter.
2. Endpoint de ingestão de PDF e endpoint de Pergunta.
3. Front-end consumindo as respostas.

# 6. Critérios de aceite
- [ ] Usuário pode enviar novo manual e ele é indexado.
- [ ] Busca natural devolve a resposta gerada por IA com fonte (página do PDF).

# 7. Como verificar (uso do revisor)
- Checar a vetorização de documentos e as chaves do LLM.

# 8. Destino da síntese
**Destino:** `specs/05-ai-knowledge.md`

---
# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

---
# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->
