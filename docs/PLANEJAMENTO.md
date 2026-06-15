# Planejamento Sprint 2 - Ajustes Finais

## 1. Implementação do Node-RED / n8n
- **Ação:** O fluxo atual coleta as informações diretamente do broker via Python. Para atender totalmente o escopo da entrega, é necessário inserir o Node-RED ou n8n na arquitetura para ser a ponte.
- **Passos:**
  - Adicionar o Node-RED ou n8n no `docker-compose.yml`.
  - Desativar a rotina de consumo via `persistence_handler.py`.
  - Criar o fluxo no Node-RED conectando no tópico MQTT, extraindo os dados e salvando diretamente no PostgreSQL usando um nó de banco de dados.

## 2. Implementação do Alerta Visual / Telegram
- **Ação:** O enunciado exige pelo menos um alerta operacional.
- **Passos:**
  - O fluxo do Node-RED deve conter nós de função (function nodes) que comparem a variável com o threshold nominal. (ex: tempW > 156.0).
  - Em caso de anomalia, o fluxo será roteado para um nó de notificação (ex: Bot do Telegram).
  - Isso garante a entrega da automação de monitoramento de incidentes.

## 3. Revisão do Dashboard Operacional
- **Ação:** Garantir que o Dashboard apresente o status contínuo corretamente após as integrações com Node-RED.
- **Passos:**
  - Validar se o Node-RED está enviando e persistindo com a formatação idêntica que o `persistence_handler.py` usava, assim o Frontend React não vai quebrar.

## 4. Apresentação (Gravação de Vídeo)
- **Ação:** Gravar os 5 minutos demonstrando todo esse novo ciclo em atividade.
