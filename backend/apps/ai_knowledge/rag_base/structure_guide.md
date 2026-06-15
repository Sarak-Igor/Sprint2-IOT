# 🧠 Estrutura da Base de Conhecimento (RAG) - Forzy

## 1. Arquitetura de Conhecimento
Para suportar o "Digital Twin Commander" (Agente de IA), estruturamos a base de conhecimento seguindo o padrão de **Retrieval-Augmented Generation (RAG)**.

## 2. Fontes de Dados (Contexto)
- **Manuais Técnicos (PDF):** Manuais de instalação, operação e manutenção da linha WEG W22.
- **Dicionário de Falhas:** Tabela de causas e efeitos para vibração excessiva e sobreaquecimento.
- **Normas ABNT/IEC:** Referências sobre eficiência energética e limites térmicos.

## 3. Pipeline de Indexação (Sprint 2/3)
1.  **Loading:** `PyMuPDFLoader` para extrair texto de manuais.
2.  **Splitting:** `RecursiveCharacterTextSplitter` para criar chunks de ~1000 caracteres com overlap de 200.
3.  **Embedding:** `OpenAI Embeddings` (ou local via HuggingFace).
4.  **Vector Store:** ChromaDB ou PGVector (extensão no Neon) para busca semântica.

## 4. Estrutura de Pastas
- `/rag_base/raw_docs/`: Manuais brutos em PDF.
- `/rag_base/processed_txt/`: Versões limpas em markdown para melhor leitura da LLM.
- `/rag_base/fault_codes.json`: Mapeamento rápido de códigos de erro.
