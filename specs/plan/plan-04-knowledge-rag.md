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
| Spec fixa | `adr/005-integracoes-iniciais.md` | Cloudflare R2 já é a integração aceita para armazenamento de objetos — reaproveitar para os PDFs, não inventar outro storage |
| Contexto | `00-contexto.md` (Fail-Fast de Configurações, §2) · `00-knowledge.md` | sempre |
| Skill | `cyber-ia` | proteção contra prompt injection (conteúdo de PDF não é confiável) |
| Skill | `padrao-python` + `padrao-typescript` | regras base |
| Skill | `test-unitario` | Cobrir ingestão e busca (mock do LLM e do vetor-store) |
| Código | `backend/apps/ai_knowledge/` | módulo hoje sem nenhum código-fonte — ler `ocr_plan.md`/`structure_guide.md` antes, são só planejamento textual, não implementação |

# 5. Instruções de execução
1. Adicionar a variável da chave de API do LLM em `backend/shared_infra/config.py` (mesmo padrão de `plan-02`,
   reaproveitar se já existir) — nunca hardcoded.
2. Preencher `backend/apps/ai_knowledge/requirements.txt` (hoje vazio) com as dependências reais escolhidas.
3. Criar backend RAG em `ai_knowledge` usando ChromaDB/FAISS e OpenRouter; armazenar os PDFs originais via
   Cloudflare R2 (`adr/005-integracoes-iniciais.md`), não em disco local.
4. Endpoint de ingestão de PDF e endpoint de Pergunta.
5. Front-end consumindo as respostas.
6. Escrever teste unitário de ingestão e de busca, com o LLM e o vetor-store mockados.

# 6. Critérios de aceite
- [ ] Chave de API do LLM configurada via `shared_infra/config.py`/`.env`, sem valor hardcoded.
- [ ] Usuário pode enviar novo manual e ele é indexado.
- [ ] Busca natural devolve a resposta gerada por IA com fonte (página do PDF).
- [ ] PDFs armazenados via Cloudflare R2, não em disco local do servidor.
- [ ] Testes unitários de ingestão e busca verdes.

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
