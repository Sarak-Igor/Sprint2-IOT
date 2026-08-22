---
tipo: "spec"
titulo: "Agente Conversacional de IA (ligado à base de conhecimento RAG)"
dominio: "ai_knowledge / agente"
status: "🔴 A Implementar"
prioridade: "Média"
tags: ["spec", "agente", "ia", "rag", "futuro"]
relacionados: []
---

# 1. Visão Geral
Um agente de IA conversacional para os operadores do Forzy — nesta primeira fase, com uma única
capacidade obrigatória: consultar a base de conhecimento (RAG) sobre os manuais técnicos já
implementada (`backend/apps/ai_knowledge/rag_engine.py`, `POST /api/knowledge/ask`). O agente
**não reimplementa** recuperação nem geração de texto — ele **usa** o que já existe como uma
capacidade/ferramenta entre outras que possa vir a ganhar depois. O RAG em si permanece
deliberadamente simples (retrieve-then-generate direto, sem múltiplos saltos de raciocínio); toda
sofisticação de orquestração (decidir quando consultar manuais, o que fazer com a resposta, se
combinar com outras fontes) vive na camada do agente, não no RAG.

> **Nota de maturidade:** esta spec nasce com propósito, não com todos os detalhes decididos —
> ver §5 "Em aberto". É o registro formal de uma decisão de arquitetura já tomada (o RAG fica
> simples e desacoplado) mais o espaço reservado para as decisões que ainda faltam, para não se
> perderem antes de uma plan ser escrita.

# 2. Regras de Negócio
- **Regra 1 (RAG como capacidade, não como agente):** o agente consome `answer_question()` (ou o
  endpoint `POST /api/knowledge/ask`) tal como já implementado e aprovado — nenhuma mudança no
  RAG é pré-requisito para o agente existir.
- **Regra 2 (RAG permanece simples):** qualquer necessidade de raciocínio em múltiplos passos,
  múltiplas fontes ou decisão sobre *quando* consultar os manuais é responsabilidade do agente,
  nunca uma responsabilidade nova empurrada para dentro do RAG.
- **Regra 3 (citação preservada):** toda resposta do agente que se apoiar na base de manuais deve
  preservar a citação de fonte (manual + página) que `AskResponse.fontes` já fornece — o agente
  não pode "resumir" a resposta do RAG de um jeito que perca a rastreabilidade da fonte.

# 3. Critérios de Aceite
- [ ] O agente responde a uma pergunta usando a base de manuais e cita a fonte (manual + página).
- [ ] O agente não reimplementa nenhuma parte do pipeline de RAG (extração de PDF, chunking,
  vetor-store) — só consome a função/endpoint já existente.
- [ ] *(demais critérios dependem das decisões em aberto abaixo — a preencher quando a plan for escrita)*

# 4. Plano de Testes (Quality Gate)

## Testes Unitários
- [ ] **Deve** chamar a capacidade de RAG (mockada) e repassar a resposta com fontes intactas.
- [ ] **Deve** tratar graciosamente a ausência de manuais indexados (mesmo comportamento que
  `answer_question` já tem hoje: mensagem informativa, não erro).

## Testes E2E (Integração)
- [ ] *(a definir quando o escopo completo do agente — interface, outras capacidades — estiver decidido)*

# 5. Em aberto — decisões pendentes, não inventadas aqui
Estas perguntas não têm resposta ainda; ficam registradas para quando o usuário decidir e uma
plan for escrita — nenhuma delas foi assumida ou implementada.

- **Escopo de capacidades:** o agente só responde perguntas sobre manuais, ou também consulta
  telemetria/anomalias/ativos, ou pode agir sobre o sistema (ex.: criar um ativo, disparar um
  alerta)? Cada capacidade nova é uma decisão de superfície de risco diferente.
- **Interface:** vive dentro da aba Knowledge (evoluindo o painel "Assistente de Conhecimento"
  já existente), ou ganha uma aba própria?
- **Memória de conversa:** cada pergunta é isolada (como o RAG hoje) ou o agente mantém contexto
  entre mensagens de uma sessão?
- **Modelo/orquestração:** um único LLM com function-calling sobre as capacidades disponíveis, ou
  uma orquestração mais explícita (roteador de intenção → capacidade)?
- **Autenticação/autorização:** como login está postergado (`adr/003-autenticacao.md`), o agente
  herda essa mesma limitação — sem diferenciação de operador por enquanto.

# 6. Contrato de manutenção desta spec
Quando as decisões da §5 forem tomadas, o agente revisor atualiza esta spec (regras de negócio e
critérios de aceite ficam completos) na mesma ação em que escreve a primeira plan de
implementação — spec e plan nascem juntas nesse momento, não uma sem a outra.
