"""
Backend SQLAlchemy Models für RAG Integration

Erweitert die bestehenden Models um RAG-spezifische Tabellen.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Verwende die bestehende Base aus dem Hauptsystem
from app.models import Base


class RAGIndexedDocument(Base):
    """SQLAlchemy Model für IndexedDocument."""
    
    __tablename__ = 'rag_indexed_documents'
    
    id = Column(Integer, primary_key=True, index=True)
    upload_document_id = Column(Integer, nullable=False, unique=True, index=True)
    document_title = Column(String(500), nullable=False)
    document_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, default='indexed', index=True)
    indexed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_chunks = Column(Integer, nullable=False, default=0)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    chunks = relationship("RAGDocumentChunk", back_populates="indexed_document", cascade="all, delete-orphan")
    
    # Indizes
    __table_args__ = (
        Index('idx_rag_indexed_documents_upload_id', 'upload_document_id'),
        Index('idx_rag_indexed_documents_status', 'status'),
        Index('idx_rag_indexed_documents_type', 'document_type'),
        Index('idx_rag_indexed_documents_indexed_at', 'indexed_at'),
    )


class RAGDocumentChunk(Base):
    """SQLAlchemy Model für DocumentChunk."""
    
    __tablename__ = 'rag_document_chunks'
    
    id = Column(Integer, primary_key=True, index=True)
    indexed_document_id = Column(Integer, ForeignKey('rag_indexed_documents.id'), nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_numbers = Column(JSON, nullable=False)  # List[int]
    heading_hierarchy = Column(JSON, nullable=True)  # List[str]
    document_type = Column(String(100), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False, default=1.0)
    chunk_type = Column(String(50), nullable=False, default='text')
    token_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    indexed_document = relationship("RAGIndexedDocument", back_populates="chunks")
    
    # Indizes
    __table_args__ = (
        Index('idx_rag_document_chunks_document_id', 'indexed_document_id'),
        Index('idx_rag_document_chunks_type', 'document_type'),
        Index('idx_rag_document_chunks_chunk_type', 'chunk_type'),
        Index('idx_rag_document_chunks_confidence', 'confidence_score'),
        Index('idx_rag_document_chunks_created_at', 'created_at'),
    )


class RAGChatSession(Base):
    """SQLAlchemy Model für ChatSession."""
    
    __tablename__ = 'rag_chat_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    session_name = Column(String(200), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_activity = Column(DateTime, nullable=False, default=datetime.utcnow)
    message_count = Column(Integer, nullable=False, default=0)
    
    # Relationships
    messages = relationship("RAGChatMessage", back_populates="chat_session", cascade="all, delete-orphan")
    
    # Indizes
    __table_args__ = (
        Index('idx_rag_chat_sessions_user_id', 'user_id'),
        Index('idx_rag_chat_sessions_last_activity', 'last_activity'),
        Index('idx_rag_chat_sessions_created_at', 'created_at'),
    )


class RAGChatMessage(Base):
    """SQLAlchemy Model für ChatMessage."""
    
    __tablename__ = 'rag_chat_messages'
    
    id = Column(Integer, primary_key=True, index=True)
    chat_session_id = Column(Integer, ForeignKey('rag_chat_sessions.id'), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' oder 'assistant'
    content = Column(Text, nullable=False)
    source_references = Column(JSON, nullable=True)  # List[Dict] mit SourceReference Daten
    structured_data = Column(JSON, nullable=True)  # Dict mit strukturierten Daten
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    chat_session = relationship("RAGChatSession", back_populates="messages")
    
    # Indizes
    __table_args__ = (
        Index('idx_rag_chat_messages_session_id', 'chat_session_id'),
        Index('idx_rag_chat_messages_role', 'role'),
        Index('idx_rag_chat_messages_created_at', 'created_at'),
    )


# Utility Functions für die Models
def get_rag_models():
    """Gibt alle RAG Models zurück."""
    return [
        RAGIndexedDocument,
        RAGDocumentChunk,
        RAGChatSession,
        RAGChatMessage
    ]


def create_rag_tables(engine):
    """Erstellt alle RAG Tabellen."""
    for model in get_rag_models():
        model.__table__.create(engine, checkfirst=True)


def drop_rag_tables(engine):
    """Löscht alle RAG Tabellen."""
    for model in reversed(get_rag_models()):
        model.__table__.drop(engine, checkfirst=True)
