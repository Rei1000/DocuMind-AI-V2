"""
Infrastructure Layer: SQLAlchemy Models für RAG Integration

Definiert die Datenbank-Tabellen für das RAG System.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class IndexedDocumentModel(Base):
    """SQLAlchemy Model für IndexedDocument."""
    
    __tablename__ = 'rag_indexed_documents'
    
    id = Column(Integer, primary_key=True, index=True)
    upload_document_id = Column(Integer, nullable=False, unique=True, index=True)
    qdrant_collection_name = Column(String(100), nullable=False)
    indexed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_chunks = Column(Integer, nullable=False, default=0)
    last_updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    embedding_model = Column(String(100), nullable=False, default="text-embedding-ada-002")
    
    # Relationships
    chunks = relationship("DocumentChunkModel", back_populates="indexed_document", cascade="all, delete-orphan")


class DocumentChunkModel(Base):
    """SQLAlchemy Model für DocumentChunk."""
    
    __tablename__ = 'rag_document_chunks'
    
    id = Column(Integer, primary_key=True, index=True)
    rag_indexed_document_id = Column(Integer, ForeignKey('rag_indexed_documents.id'), nullable=False, index=True)
    chunk_id = Column(String(100), nullable=False, unique=True, index=True)
    chunk_text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=False)
    paragraph_index = Column(Integer, nullable=True)
    chunk_index = Column(Integer, nullable=False)
    token_count = Column(Integer, nullable=True)
    sentence_count = Column(Integer, nullable=True)
    has_overlap = Column(Boolean, nullable=False, default=False)
    overlap_sentence_count = Column(Integer, nullable=False, default=0)
    qdrant_point_id = Column(String(100), nullable=True, unique=True, index=True)
    embedding_vector_preview = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    indexed_document = relationship("IndexedDocumentModel", back_populates="chunks")


class ChatSessionModel(Base):
    """SQLAlchemy Model für ChatSession."""
    
    __tablename__ = 'rag_chat_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    session_name = Column(String(200), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_activity = Column(DateTime, nullable=False, default=datetime.utcnow)
    message_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    messages = relationship("ChatMessageModel", back_populates="chat_session", cascade="all, delete-orphan")


class ChatMessageModel(Base):
    """SQLAlchemy Model für ChatMessage."""
    
    __tablename__ = 'rag_chat_messages'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('rag_chat_sessions.id'), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' oder 'assistant'
    content = Column(Text, nullable=False)
    source_references = Column(JSON, nullable=True)  # List[Dict] mit SourceReference Daten
    source_chunk_ids = Column(JSON, nullable=True)  # List[str] mit Chunk IDs
    confidence_scores = Column(JSON, nullable=True)  # Dict[str, float] mit Confidence Scores
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    chat_session = relationship("ChatSessionModel", back_populates="messages")
