from sqlalchemy import Column, String, Integer, Float, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from backend.shared_infra.database_client.postgresql import Base

class KnowledgeManualDB(Base):
    __tablename__ = "knowledge_manuals"

    manual_id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    total_pages = Column(Integer, default=0)
    pdf_bytes = Column(LargeBinary, nullable=False)  # Armazena o PDF conforme Opção A

    chunks = relationship("KnowledgeChunkDB", back_populates="manual", cascade="all, delete-orphan")


class KnowledgeChunkDB(Base):
    __tablename__ = "knowledge_chunks"

    chunk_id = Column(String, primary_key=True, index=True)
    manual_id = Column(String, ForeignKey("knowledge_manuals.manual_id"), index=True)
    page = Column(Integer, nullable=False)
    technology_tag = Column(String, nullable=True)
    
    # Texto original
    document = Column(String, nullable=False)
    
    # Vetor de embedding (usando pgvector). O tamanho deve bater com o modelo usado (paraphrase-multilingual-MiniLM-L12-v2 gera vetores de 384 dimensões).
    embedding = Column(Vector(384), nullable=False)

    manual = relationship("KnowledgeManualDB", back_populates="chunks")
