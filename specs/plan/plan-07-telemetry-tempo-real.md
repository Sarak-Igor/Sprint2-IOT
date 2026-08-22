---
tipo: "plan"
titulo: "Ligar a aba Telemetria ao WebSocket real de telemetria"
dominio: "frontend"
status: "🔴 A executar"
prioridade: "Média"
tags: ["plan", "frontend", "telemetria", "websocket"]
relacionados: ["[[arquitetura/01-frontend-soberano]]"]
depende_de: "—"
destino_sintese: "—"
---

# 1. Objetivo
A aba "Telemetria" deixa de ser um card estático e passa a exibir dados reais de telemetria em tempo real,
como já acontece em `Dashboard.tsx` e `DigitalTwin.tsx`.

# 2. Contexto
`frontend/src/pages/Telemetry.tsx` é hoje um componente sem `useState`, sem `useEffect`, sem `fetch`, com um
card fixo contendo o texto hardcoded "Aguardando conexão com o servidor de ingestão de dados..." — apesar de o
WebSocket `/api/ws/telemetry` (`api/index.py`) já estar funcional e em uso por `Dashboard.tsx` (linhas
100-137) e `DigitalTwin.tsx` (linhas 64-101). Esta plan não cria nenhuma API nova — só conecta a aba ao que já
existe.

# 3. Escopo

## 3.1 Dentro
- `frontend/src/pages/Telemetry.tsx` — reescrever para consumir `/api/ws/telemetry` (WebSocket) e/ou
  `GET /api/assets/dashboard` para o estado inicial, seguindo o mesmo padrão de conexão/reconexão já usado em
  `Dashboard.tsx`/`DigitalTwin.tsx` (referencie o código deles, não invente um padrão novo).

## 3.2 Fora
- Qualquer rota de backend — todas as necessárias já existem.
- `Dashboard.tsx` e `DigitalTwin.tsx` — não toque neles, só leia como referência de padrão.
- Estilização base da `@sarak/lib-ui-core` — não recrie componentes visuais da lib.

# 4. Referências obrigatórias
| Tipo | Referência | Por quê |
|---|---|---|
| Spec fixa | `arquitetura/01-frontend-soberano.md` | Frontend é passivo — só renderiza o que o backend manda |
| Spec fixa | `arquitetura/02-backend-eda.md` | Confirma o WebSocket de telemetria como fonte real |
| Contexto | `00-contexto.md` · `00-knowledge.md` | sempre |
| Skill | `padrao-escrita` + `padrao-typescript` | sempre |
| Skill | `test-unitario` | Cobrir o componente novo (mock do WebSocket) |
| Código | `frontend/src/pages/Dashboard.tsx:60-137` | Padrão de conexão WebSocket + estado a replicar |
| Código | `frontend/src/pages/DigitalTwin.tsx:64-101` | Padrão alternativo, se mais adequado ao layout desta aba |

# 5. Instruções de execução
1. Ler o padrão de conexão/reconexão de WebSocket em `Dashboard.tsx` e `DigitalTwin.tsx`.
2. Reescrever `Telemetry.tsx` para abrir a mesma conexão e renderizar os valores recebidos, mantendo o
   componente "passivo" (sem regra de negócio local — só formatação de exibição).
3. Tratar o estado de "aguardando conexão" como um estado real (enquanto o WebSocket não abriu ou não chegou
   nenhuma mensagem), não mais como texto fixo permanente.
4. Cobrir com teste unitário o comportamento de conectar/receber mensagem/desconectar (mock do WebSocket).

# 6. Critérios de aceite
- [ ] `Telemetry.tsx` exibe dados reais recebidos do WebSocket, não texto hardcoded.
- [ ] O estado de espera só aparece antes da primeira mensagem chegar, não indefinidamente.
- [ ] Nenhuma regra de negócio (limiar, severidade) foi introduzida no componente.
- [ ] Teste unitário do componente verde.

# 7. Como verificar (uso do revisor)
- `git diff --stat` → só `Telemetry.tsx` (e o arquivo de teste novo).
- Ler o componente e confirmar ausência de lógica de negócio (só exibição).
- Rodar o teste novo e ler a saída.
- Subir o frontend (`npm run dev`) e abrir a aba manualmente para confirmar visualmente, se o ambiente
  permitir.

# 8. Destino da síntese
**Destino:** `—`
Não há regra de negócio nova nem mudança de arquitetura — a aba passa a consumir uma API que já está
documentada em `arquitetura/02-backend-eda.md`. Nenhuma spec fixa precisa de atualização.

---

# 9. Resumo da execução
<!-- Preenchido pelo EXECUTOR. Append-only: cada rodada acrescenta um bloco novo; nada é removido. -->

---

# 10. Veredito
<!-- Preenchido pelo REVISOR. Append-only: um bloco por rodada, com o que foi verificado e como. -->
