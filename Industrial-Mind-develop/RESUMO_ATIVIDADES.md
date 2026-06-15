# 📝 Resumo de Atividades - Projeto Forzy

Este documento descreve detalhadamente todas as implementações realizadas para a **Sprint 1**.

---

### 1. Arquitetura do Ecossistema
Estabelecemos um monorepo seguindo os princípios de **Clean Architecture**, garantindo que a lógica de negócio seja independente de frameworks e hardware.
- **Estrutura Modular:** Organizado em `backend/apps` (serviços) e `backend/shared_infra` (configurações, banco de dados e utilitários).
- **Abordagem Agnóstica:** O backend foi desenhado para suportar múltiplos motores e sensores sem necessidade de refatoração de código (Zero Hardcode).

### 2. Camada de Abstração de Hardware
Implementamos a regra de **Zero Hardcode**. O software não "sabe" qual motor está monitorando até ler os metadados dinâmicos.
- **Motor WEG W22 IR3:** Mapeamos limites de temperatura da Classe F, correntes nominais e padrões de vibração via JSON.
- **Validação Fail-Fast:** Implementação de modelos Pydantic para garantir que nenhum dado inválido de configuração entre no sistema.

### 3. Ingestão e Gerador de Caos
Criamos um sistema de simulação de alta fidelidade para o Gêmeo Digital.
- **Broker MQTT:** Containerizado via Docker (Mosquitto), garantindo comunicação de baixa latência.
- **Simulador de Anomalias:** Algoritmo que injeta variações naturais de sensores com probabilidade configurável de eventos críticos (ex: superaquecimento), essencial para testar algoritmos de IA.

### 4. Persistência de Dados (Neon PostgreSQL)
Diferencial técnico da entrega: Implementação de base de dados em nuvem para histórico de telemetria.
- **Neon DB:** Configuração de instância PostgreSQL gerenciada.
- **SQLAlchemy Async:** Uso de ORM assíncrono para garantir que a gravação no banco não bloqueie o recebimento de mensagens MQTT.
- **Schema `Forzy`:** Estrutura organizada com tabelas de ativos (`assets`) e histórico de telemetria (`telemetry_history`).

### 5. Estratégia de Inteligência Artificial
Documentação técnica preparando o terreno para a Sprint 2.
- **Plano OCR:** Estratégia de Visão Computacional para leitura automática de placas de identificação.
- **Estrutura RAG:** Guia de organização de base de conhecimento para suporte técnico assistido por IA.
- **Logs de Eventos:** Sistema de logging preparado para alimentar dashboards de manutenção preditiva.

### 6. Firmware Embarcado (IoT)
- **PlatformIO:** Projeto C++ para ESP32 estruturado, com payloads de telemetria padronizados e idênticos aos validados no backend.
