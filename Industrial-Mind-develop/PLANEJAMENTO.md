# Plano de Desenvolvimento - Forzy (Digital Twin)

## 🎯 Sprint 1: Fundamentação e Data Pipeline (CONCLUÍDA)

### 1. Infraestrutura e Persistência
- [x] Configuração do Ambiente Local (.venv, Docker Mosquitto)
- [x] Configuração do Neon PostgreSQL (Cloud)
- [x] Criação do Schema `Forzy` e tabelas `assets`/`telemetry_history`
- [x] Implementação do `database_client` assíncrono (SQLAlchemy + asyncpg)

### 2. Camada de Abstração (Zero Hardcode)
- [x] Mapeamento Técnico do Motor WEG W22 IR3 Premium
- [x] Criação do Schema JSON de Especificações Técnicas
- [x] Implementação de Modelos Pydantic para Validação Fail-Fast das Specs

### 3. Ingestão de Dados e Simulação
- [x] Definição dos 5 Sensores Vitais (Temp, Vib, Corrente, Tensão, RPM)
- [x] Criação da Interface Base para Provedores de Dados (Adapters)
- [x] **Implementação do Gerador de Caos** (Injetor de Anomalias)
- [x] Implementação do Mock Provider (Python) com Publicação MQTT Real
- [x] **Persistence Handler:** Integração MQTT -> PostgreSQL (Neon) funcional

### 4. Firmware e Hardware (IoT)
- [x] Instalação e Preparação do Ambiente PlatformIO
- [x] Scaffolding do Projeto ESP32 (`iot_firmware/`)
- [x] Desenvolvimento do Código C++ (Main.cpp) para Publicação MQTT
- [x] Validação do Fluxo de Dados (Simulador Python validado como PoC fiel ao hardware)

---

## 🚀 Sprint 2: Digital Twin Intelligence (Próxima Etapa)
- [ ] **Dashboard Web:** Criação da interface de monitoramento real-time
- [ ] **Módulo OCR:** Implementação da visão computacional para leitura de placas
- [ ] **RAG Engine:** Integração da base de conhecimento técnica
- [ ] **Alertas:** Sistema de notificação baseado no Gerador de Caos
