---
tipo: "arquitetura"
titulo: "Frontend e UI Soberana"
dominio: "Infraestrutura / Design"
status: "🟢 Vigente"
tags: ["arquitetura", "frontend", "ui"]
relacionados: []
---

# 1. Propósito
O Frontend do Forzy atua como um *Connector* visual. Ele é responsável exclusivamente por renderizar dados fornecidos pela API (Gêmeo Digital) de forma visualmente rica para operadores industriais. Ele é "passivo", ou seja, não processa regras de negócio sobre falhas de motores ou limites de vibração; apenas reage ao estado devolvido pelo backend.

# 2. Stack e Ferramentas
- **Linguagem e Framework:** React 18, TypeScript, Vite.
- **Gráficos e Visualização:** ECharts e Recharts para plotagem de telemetria em alta performance.
- **Design System:** Delega a estilização base ao `@sarak/lib-ui-core` via NPM (linkado direto ao repositório git). Usa TailwindCSS (via `tailwind-merge` e `clsx`) para ajustes de layout locais.

# 3. Diagramas / Estruturas
A renderização obedece a um fluxo unidirecional:
1. React busca `/telemetry/stats` no `digital_twin_core`.
2. A resposta alimenta os componentes do ECharts.
3. Se o componente recebe severidade "critical", ele aplica estilos visuais de alerta (cores, ícones), consumindo tokens da lib-ui-core.
