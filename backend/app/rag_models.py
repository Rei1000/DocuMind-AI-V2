"""
Backend SQLAlchemy Models für RAG Integration

Erweitert die bestehenden Models um RAG-spezifische Tabellen.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Verwende die bestehende Base aus dem Hauptsystem
from app.models import Base


class RAGIndexedDocument(Base):
    """SQLAlchemy Model für IndexedDocument."""
    
    __tablename__ = 'rag_indexed_documents'
    
    id = Column(Integer, primary_key=True, index=True)
    upload_document_id = Column(Integer, nullable=False, unique=True, index=True)
    qdrant_collection_name = Column(String(100), nullable=False)  # DB hat diese Spalte
    total_chunks = Column(Integer, nullable=False, default=0)
    indexed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)  # DB hat last_updated_at
    embedding_model = Column(String(100), nullable=False)  # DB hat diese Spalte
    last_updated = Column(DateTime, nullable=True)  # DB hat zusätzliche Spalte
    
    # Relationships
    chunks = relationship("RAGDocumentChunk", back_populates="indexed_document", cascade="all, delete-orphan")
    
    # Computed Properties
    @property
    def document_title(self):
        """Document title ist nicht in DB, wird aus UploadDocument geholt."""
        # TODO: Implementierung über UploadDocument Relationship
        return f"Document {self.upload_document_id}"
    
    @property
    def document_type(self):
        """Document type ist nicht in DB, wird aus UploadDocument geholt."""
        # TODO: Implementierung über UploadDocument Relationship
        return "Unknown"
    
    @property
    def status(self):
        """Status ist nicht in DB, wird berechnet."""
        return "indexed" if self.total_chunks > 0 else "processing"
    
    # Indizes
    __table_args__ = (
        Index('idx_rag_indexed_documents_upload_id', 'upload_document_id'),
        Index('idx_rag_indexed_documents_indexed_at', 'indexed_at'),
    )


class RAGDocumentChunk(Base):
    """SQLAlchemy Model für DocumentChunk."""
    
    __tablename__ = 'rag_document_chunks'
    
    id = Column(Integer, primary_key=True, index=True)
    rag_indexed_document_id = Column(Integer, ForeignKey('rag_indexed_documents.id'), nullable=False, index=True)  # DB hat rag_indexed_document_id
    chunk_id = Column(String(100), nullable=False)  # DB hat chunk_id
    chunk_text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=False)  # DB hat page_number statt page_numbers JSON
    paragraph_index = Column(Integer, nullable=True)  # DB hat paragraph_index
    chunk_index = Column(Integer, nullable=False)
    token_count = Column(Integer, nullable=True)
    sentence_count = Column(Integer, nullable=True)  # DB hat sentence_count
    has_overlap = Column(Boolean, nullable=False, default=False)  # DB hat has_overlap
    overlap_sentence_count = Column(Integer, nullable=False, default=0)  # DB hat overlap_sentence_count
    qdrant_point_id = Column(String(100), nullable=True)  # DB hat qdrant_point_id
    embedding_vector_preview = Column(Text, nullable=True)  # DB hat embedding_vector_preview
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    indexed_document = relationship("RAGIndexedDocument", back_populates="chunks", foreign_keys=[rag_indexed_document_id])
    
    # Computed Properties
    @property
    def page_numbers(self):
        """Konvertiert page_number zu List für Kompatibilität."""
        return [self.page_number] if self.page_number else []
    
    @property
    def heading_hierarchy(self):
        """Heading hierarchy ist nicht in DB, gibt leere Liste zurück."""
        return []
    
    @property
    def document_type(self):
        """Document type wird aus indexed_document geholt."""
        return self.indexed_document.document_type if self.indexed_document else "Unknown"
    
    @property
    def confidence_score(self):
        """Confidence score ist nicht in DB, gibt 1.0 zurück."""
        return 1.0
    
    @property
    def chunk_type(self):
        """Chunk type ist nicht in DB, gibt 'text' zurück."""
        return "text"
    
    # Indizes
    __table_args__ = (
        Index('idx_rag_document_chunks_chunk_id', 'chunk_id'),
        Index('idx_rag_document_chunks_qdrant_id', 'qdrant_point_id'),
        Index('idx_rag_document_chunks_created_at', 'created_at'),
    )


class RAGChatSession(Base):
    """SQLAlchemy Model für ChatSession."""
    
    __tablename__ = 'rag_chat_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    session_name = Column(String(255), nullable=True)  # DB hat VARCHAR(255), nullable=True
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_message_at = Column(DateTime, nullable=True)  # DB hat last_message_at statt last_activity
    is_active = Column(Boolean, nullable=False, default=True)  # DB hat is_active Spalte
    
    # Relationships
    messages = relationship("RAGChatMessage", back_populates="chat_session", cascade="all, delete-orphan")
    
    # Computed Properties
    @property
    def message_count(self):
        """Berechnet die Anzahl der Nachrichten aus der Relationship."""
        return len(self.messages) if self.messages else 0
    
    @property
    def last_activity(self):
        """Alias für last_message_at für Kompatibilität."""
        return self.last_message_at
    
    # Indizes
    __table_args__ = (
        Index('idx_rag_chat_sessions_user_id', 'user_id'),
        Index('idx_rag_chat_sessions_created_at', 'created_at'),
        Index('idx_rag_chat_sessions_is_active', 'is_active'),
    )


class RAGChatMessage(Base):
    """SQLAlchemy Model für ChatMessage."""
    
    __tablename__ = 'rag_chat_messages'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('rag_chat_sessions.id'), nullable=False, index=True)  # DB hat session_id statt chat_session_id
    role = Column(String(20), nullable=False)  # 'user' oder 'assistant'
    content = Column(Text, nullable=False)
    source_chunks = Column(Text, nullable=True)  # DB hat source_chunks statt source_references
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    chat_session = relationship("RAGChatSession", back_populates="messages", foreign_keys=[session_id])
    
    # Computed Properties
    @property
    def source_references(self):
        """Konvertiert source_chunks Text zu JSON für Kompatibilität."""
        if self.source_chunks:
            try:
                import json
                return json.loads(self.source_chunks)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    @property
    def structured_data(self):
        """Structured data ist in der DB nicht vorhanden, gibt leeres Dict zurück."""
        return {}
    
    # Indizes
    __table_args__ = (
        Index('idx_rag_chat_messages_session_id', 'session_id'),
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
