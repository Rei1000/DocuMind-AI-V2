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


# ============================================================================
# AUDIT-TRAIL EVENTS (PHASE 1)
# ============================================================================

@dataclass(frozen=True)
class ChunkingStartedEvent:
    """
    Event: Chunking-Prozess wurde gestartet.
    
    Wird publiziert wenn die Chunk-Generierung für ein Dokument beginnt.
    
    Attributes:
        document_id: ID des UploadDocument
        user_id: ID des Users der das Chunking initiierte
        strategy: Name der verwendeten Chunking-Strategie
        timestamp: Zeitstempel des Starts
    """
    document_id: int
    user_id: int
    strategy: str
    timestamp: datetime
    
    def get_event_type(self) -> str:
        return "ChunkingStarted"


@dataclass(frozen=True)
class ChunkingCompletedEvent:
    """
    Event: Chunking-Prozess wurde abgeschlossen.
    
    Wird publiziert wenn die Chunk-Generierung erfolgreich abgeschlossen wurde.
    
    Attributes:
        document_id: ID des UploadDocument
        indexed_document_id: ID des neu erstellten IndexedDocument
        total_chunks: Anzahl generierter Chunks
        duration_ms: Dauer des Chunking-Prozesses in Millisekunden
        timestamp: Zeitstempel des Abschlusses
    """
    document_id: int
    indexed_document_id: int
    total_chunks: int
    duration_ms: int
    timestamp: datetime
    
    def get_event_type(self) -> str:
        return "ChunkingCompleted"


@dataclass(frozen=True)
class ChunkingFailedEvent:
    """
    Event: Chunking-Prozess ist fehlgeschlagen.
    
    Wird publiziert wenn die Chunk-Generierung mit Fehler abgebrochen wurde.
    
    Attributes:
        document_id: ID des UploadDocument
        error_message: Fehler-Beschreibung
        timestamp: Zeitstempel des Fehlers
    """
    document_id: int
    error_message: str
    timestamp: datetime
    
    def get_event_type(self) -> str:
        return "ChunkingFailed"


@dataclass(frozen=True)
class IndexingStartedEvent:
    """
    Event: Indexierung in Qdrant wurde gestartet.
    
    Wird publiziert wenn Chunks in Qdrant Vector Store indexiert werden.
    
    Attributes:
        indexed_document_id: ID des IndexedDocument
        total_chunks: Anzahl zu indexierender Chunks
        timestamp: Zeitstempel des Starts
    """
    indexed_document_id: int
    total_chunks: int
    timestamp: datetime
    
    def get_event_type(self) -> str:
        return "IndexingStarted"


@dataclass(frozen=True)
class IndexingCompletedEvent:
    """
    Event: Indexierung in Qdrant wurde abgeschlossen.
    
    Wird publiziert wenn alle Chunks erfolgreich indexiert wurden.
    
    Attributes:
        indexed_document_id: ID des IndexedDocument
        total_chunks: Anzahl indexierter Chunks
        duration_ms: Dauer der Indexierung in Millisekunden
        timestamp: Zeitstempel des Abschlusses
    """
    indexed_document_id: int
    total_chunks: int
    duration_ms: int
    timestamp: datetime
    
    def get_event_type(self) -> str:
        return "IndexingCompleted"


@dataclass(frozen=True)
class IndexingFailedEvent:
    """
    Event: Indexierung in Qdrant ist fehlgeschlagen.
    
    Wird publiziert wenn die Indexierung mit Fehler abgebrochen wurde.
    
    Attributes:
        indexed_document_id: ID des IndexedDocument
        error_message: Fehler-Beschreibung
        timestamp: Zeitstempel des Fehlers
    """
    indexed_document_id: int
    error_message: str
    timestamp: datetime
    
    def get_event_type(self) -> str:
        return "IndexingFailed"


@dataclass(frozen=True)
class QueryExecutedEvent:
    """
    Event: RAG Query wurde ausgeführt.
    
    Wird publiziert wenn eine User-Query gegen das RAG-System ausgeführt wurde.
    
    Attributes:
        session_id: ID der ChatSession
        user_id: ID des Users
        question: User-Frage
        retrieved_chunks_count: Anzahl abgerufener Chunks
        response_length: Länge der generierten Antwort
        duration_ms: Dauer der Query in Millisekunden
        timestamp: Zeitstempel der Ausführung
    """
    session_id: int
    user_id: int
    question: str
    retrieved_chunks_count: int
    response_length: int
    duration_ms: int
    timestamp: datetime
    
    def get_event_type(self) -> str:
        return "QueryExecuted"


# ============================================================================
# RAG FEEDBACK EVENTS (PHASE 4.1)
# ============================================================================

@dataclass(frozen=True)
class FeedbackSubmittedEvent:
    """
    Event: User Feedback wurde abgegeben.

    Wird publiziert wenn ein User Feedback zu einer RAG Chat-Antwort gibt.

    Attributes:
        feedback_id: ID des erstellten RAGFeedback
        chat_message_id: ID der Chat-Message
        user_id: ID des Users
        rating: Bewertung ("positive", "negative", "neutral")
        timestamp: Zeitstempel der Abgabe
    """
    feedback_id: int
    chat_message_id: int
    user_id: int
    rating: str
    timestamp: datetime

    def get_event_type(self) -> str:
        return "FeedbackSubmitted"


@dataclass(frozen=True)
class ChunkFeedbackSubmittedEvent:
    """
    Event: Chunk-Level Feedback wurde abgegeben.
    
    Wird ausgelöst wenn ein User Feedback zu einem einzelnen Chunk gibt.
    
    Attributes:
        chunk_feedback_id: ID des Chunk-Feedbacks
        chunk_id: ID des Chunks
        chat_message_id: ID der Chat-Nachricht
        document_id: ID des Dokuments
        user_id: ID des Users
        rating: Bewertung (positive, negative, neutral)
        timestamp: Zeitstempel der Abgabe
    """
    chunk_feedback_id: int
    chunk_id: str
    chat_message_id: int
    document_id: int
    user_id: int
    rating: str
    timestamp: datetime

    def get_event_type(self) -> str:
        return "ChunkFeedbackSubmitted"
