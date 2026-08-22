---
tipo: "plan"
titulo: "Implementar Visão Computacional OCR para Placas"
dominio: "vision_service"
status: "🔴 A executar"
prioridade: "Alta"
tags: ["plan", "ocr", "vision"]
relacionados: ["[[specs/04-vision-ocr]]"]
depende_de: "plan-02-catalog-intelligence"
destino_sintese: "specs/04-vision-ocr.md"
---
# 1. Objetivo
Conectar a tela de Visão Computacional a um modelo multimodal (OpenRouter) capaz de ler a placa do motor (imagem) e extrair os dados técnicos reais.

# 2. Contexto
A aba de Visão Computacional tem UI belíssima, mas a função `simulateScan` roda um `setTimeout` de 2.5s retornando um json fixo. Precisamos ligar isso ao LLM Visual.

# 3. Escopo
## 3.1 Dentro
- `backend/apps/asset_manager/vision/*` (Criar a rota de extração visual).
- `frontend/src/pages/Vision.tsx` (Substituir o MOCK por fetch de multipart/form-data).

## 3.2 Fora
- Estilização do Sarak-UI (Não quebrar animações existentes).

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Contexto | `00-contexto.md` (Fail-Fast de Configurações, §2) · `00-knowledge.md` | sempre |
| Skill | `cyber-ia` | proteção de injeção na visão (imagem/texto adversarial) |
| Skill | `padrao-python` + `padrao-typescript` | regras base |
| Skill | `test-unitario` | Cobrir o endpoint novo (mock da chamada multimodal) |
| Código | `backend/shared_infra/config.py` | onde a chave da API do LLM multimodal deve ser lida via Pydantic |

# 5. Instruções de execução
1. Confirmar que a variável de chave de API do LLM (mesma de `plan-02`, se `plan-02` já tiver sido executada;
   caso contrário, adicionar em `backend/shared_infra/config.py` seguindo o mesmo padrão) está disponível —
   nunca hardcoded.
2. Substituir o json hardcoded no frontend por requisição POST para `/api/vision/scan`.
3. No Backend, receber o upload e disparar requisição para OpenRouter multimodal (ex: GPT-4o ou Claude 3).
4. Retornar JSON estruturado validado via Pydantic.
5. Escrever teste unitário do endpoint com a chamada multimodal mockada.

# 6. Critérios de aceite
- [ ] OCR devolve campos corretos da placa (rpm, tensão, IP, etc).
- [ ] Front-end renderiza a resposta da API ao invés do mock.
- [ ] Nenhuma chave de API hardcoded no código do endpoint.
- [ ] Teste unitário do endpoint verde.

# 7. Como verificar (uso do revisor)
- Revisar o código Python do Langchain de Vision.
- Checar se `Vision.tsx` não quebrou estilização original.

# 8. Destino da síntese
**Destino:** `specs/04-vision-ocr.md`

---
# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

---
# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->
