"""
Domain Events für RAG Integration Context.

Domain Events repräsentieren wichtige Geschäftsereignisse.
Sie werden von Entities publiziert und von Event Handlers verarbeitet.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DocumentIndexedEvent:
    """
    Event: Dokument wurde erfolgreich indexiert.
    
    Wird publiziert wenn ein Dokument vollständig in das RAG-System indexiert wurde.
    
    Attributes:
        indexed_document_id: ID des IndexedDocument
        upload_document_id: ID des ursprünglichen UploadDocument
        total_chunks: Anzahl erstellter Chunks
        timestamp: Zeitstempel der Indexierung
    """
    indexed_document_id: int
    upload_document_id: int
    total_chunks: int
    timestamp: datetime
    
    def __post_init__(self):
        """Validiere Event nach Initialisierung."""
        if self.indexed_document_id <= 0:
            raise ValueError("indexed_document_id must be positive")
        
        if self.upload_document_id <= 0:
            raise ValueError("upload_document_id must be positive")
        
        if self.total_chunks <= 0:
            raise ValueError("total_chunks cannot be negative")
    
    def get_event_type(self) -> str:
        """Returniere Event-Typ."""
        return "DocumentIndexed"


@dataclass(frozen=True)
class ChatMessageCreatedEvent:
    """
    Event: Neue Chat-Nachricht wurde erstellt.
    
    Wird publiziert wenn eine neue Nachricht (User oder Assistant) erstellt wurde.
    
    Attributes:
        message_id: ID der ChatMessage
        session_id: ID der ChatSession
        user_id: ID des Users
        role: Rolle der Nachricht ('user' oder 'assistant')
        content: Inhalt der Nachricht
        timestamp: Zeitstempel der Erstellung
    """
    message_id: int
    session_id: int
    user_id: int
    role: str
    content: str
    timestamp: datetime
    
    def __post_init__(self):
        """Validiere Event nach Initialisierung."""
        if self.message_id <= 0:
            raise ValueError("message_id must be positive")
        
        if self.session_id <= 0:
            raise ValueError("session_id must be positive")
        
        if self.user_id <= 0:
            raise ValueError("user_id must be positive")
        
        valid_roles = ["user", "assistant"]
        if self.role not in valid_roles:
            raise ValueError(f"role must be one of {valid_roles}")
        
        if not self.content or not self.content.strip():
            raise ValueError("content cannot be empty")
    
    def get_event_type(self) -> str:
        """Returniere Event-Typ."""
        return "ChatMessageCreated"


@dataclass(frozen=True)
class ChunkCreatedEvent:
    """
    Event: Neuer Chunk wurde erstellt.
    
    Wird publiziert wenn ein neuer DocumentChunk erstellt wurde.
    
    Attributes:
        chunk_id: Eindeutige Chunk-ID
        indexed_document_id: ID des IndexedDocument
        page_number: Seitennummer
        paragraph_index: Index des Absatzes
        timestamp: Zeitstempel der Erstellung
    """
    chunk_id: str
    indexed_document_id: int
    page_number: int
    paragraph_index: int
    timestamp: datetime
    
    def __post_init__(self):
        """Validiere Event nach Initialisierung."""
        if not self.chunk_id or not self.chunk_id.strip():
            raise ValueError("chunk_id cannot be empty")
        
        if self.indexed_document_id <= 0:
            raise ValueError("indexed_document_id must be positive")
        
        if self.page_number <= 0:
            raise ValueError("page_number must be positive")
        
        if self.paragraph_index < 0:
            raise ValueError("paragraph_index must be non-negative")
    
    def get_event_type(self) -> str:
        """Returniere Event-Typ."""
        return "ChunkCreated"
