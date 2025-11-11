"""
Domain Entities für RAG Integration Context.

Entities sind Objekte mit einer eindeutigen Identität, die sich über die Zeit ändern können.
Sie repräsentieren die Kerngeschäftslogik des Systems.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from .value_objects import ChunkMetadata, SourceReference


@dataclass
class IndexedDocument:
    """
    Indexiertes Dokument Entity.
    
    Repräsentiert ein Dokument, das in das RAG-System indexiert wurde.
    
    Attributes:
        id: Eindeutige ID (None bei neuen Entities)
        upload_document_id: FK zu UploadedDocument
        collection_name: Name der Qdrant Collection
        total_chunks: Anzahl erstellter Chunks
        indexed_at: Zeitstempel der Indexierung
        last_updated_at: Zeitstempel der letzten Aktualisierung
        embedding_model: Name des verwendeten Embedding-Modells (z.B. "text-embedding-ada-002", "text-embedding-004")
    """
    id: Optional[int]
    upload_document_id: int
    collection_name: str
    total_chunks: int
    indexed_at: datetime
    last_updated_at: datetime  # Geändert von last_updated
    embedding_model: str = "text-embedding-ada-002"  # NEU: Embedding-Modell für konsistente Suche (Default für alte Dokumente)
    
    def __post_init__(self):
        """Validiere Entity nach Initialisierung."""
        if self.upload_document_id <= 0:
            raise ValueError("upload_document_id must be positive")
        
        if not self.collection_name or not self.collection_name.strip():
            raise ValueError("collection_name cannot be empty")
        
        # total_chunks kann 0 sein (z.B. wenn noch nicht indexiert)
        if self.total_chunks < 0:
            raise ValueError("total_chunks cannot be negative")


@dataclass
class DocumentChunk:
    """
    Document Chunk Entity.
    
    Repräsentiert einen einzelnen Text-Chunk eines indexierten Dokuments.
    
    Attributes:
        id: Eindeutige ID (None bei neuen Entities)
        indexed_document_id: FK zu IndexedDocument
        chunk_id: Eindeutige Chunk-ID (z.B. 'doc_42_chunk_0')
        chunk_text: Text-Inhalt des Chunks
        metadata: Strukturierte Metadaten (Value Object)
        qdrant_point_id: UUID in Qdrant Vector Store
        created_at: Zeitstempel der Erstellung
    """
    id: Optional[int]
    indexed_document_id: int
    chunk_id: str
    chunk_text: str
    metadata: ChunkMetadata
    qdrant_point_id: str
    created_at: datetime
    
    def __post_init__(self):
        """Validiere Entity nach Initialisierung."""
        if self.indexed_document_id <= 0:
            raise ValueError("indexed_document_id must be positive")
        
        if not self.chunk_id or not self.chunk_id.strip():
            raise ValueError("chunk_id cannot be empty")
        
        if not self.chunk_text or not self.chunk_text.strip():
            raise ValueError("chunk_text cannot be empty")
        
        if not self.qdrant_point_id or not self.qdrant_point_id.strip():
            raise ValueError("qdrant_point_id cannot be empty")
    
    def get_page_count(self) -> int:
        """Returniere Anzahl Seiten aus Metadata."""
        return self.metadata.get_page_count()
    
    def is_multi_page(self) -> bool:
        """Prüfe ob Chunk über mehrere Seiten geht."""
        return self.metadata.is_multi_page()


@dataclass
class ChatSession:
    """
    Chat Session Entity.
    
    Repräsentiert eine Chat-Session eines Users.
    
    Attributes:
        id: Eindeutige ID (None bei neuen Entities)
        user_id: FK zu User
        session_name: Name der Session
        created_at: Zeitstempel der Erstellung
        last_message_at: Zeitstempel der letzten Nachricht
        is_active: Ob Session aktiv ist
    """
    id: Optional[int]
    user_id: int
    session_name: str
    created_at: datetime
    last_message_at: datetime
    is_active: bool
    
    def __post_init__(self):
        """Validiere Entity nach Initialisierung."""
        if self.user_id <= 0:
            raise ValueError("user_id must be positive")
        
        if not self.session_name or not self.session_name.strip():
            raise ValueError("session_name cannot be empty")
    
    def deactivate(self) -> None:
        """Deaktiviere Session (Business Logic)."""
        self.is_active = False
    
    def activate(self) -> None:
        """Aktiviere Session (Business Logic)."""
        self.is_active = True


@dataclass
class ChatMessage:
    """
    Chat Message Entity.
    
    Repräsentiert eine einzelne Nachricht in einer Chat-Session.
    
    Attributes:
        id: Eindeutige ID (None bei neuen Entities)
        session_id: FK zu ChatSession
        role: Rolle der Nachricht ('user' oder 'assistant')
        content: Inhalt der Nachricht
        created_at: Zeitstempel der Erstellung
        source_references: Liste der Source References (optional)
        ai_model_used: AI Model das für diese Nachricht verwendet wurde (nur für assistant messages)
        metadata: Metadaten (processing_time_ms, tokens_used, query_params) - nur für assistant messages
    """
    id: Optional[int]
    session_id: int
    role: str
    content: str
    created_at: datetime
    source_references: List[SourceReference] = field(default_factory=list)
    ai_model_used: Optional[str] = None  # z.B. 'gpt-4o-mini', 'gpt-5-mini', 'gemini-2.5-flash'
    metadata: Dict[str, Any] = field(default_factory=dict)  # Metadaten für Transparency Layer
    
    def __post_init__(self):
        """Validiere Entity nach Initialisierung."""
        if self.session_id <= 0:
            raise ValueError("session_id must be positive")
        
        valid_roles = ["user", "assistant"]
        if self.role not in valid_roles:
            raise ValueError(f"role must be 'user' or 'assistant'")
        
        if not self.content or not self.content.strip():
            raise ValueError("content cannot be empty")
    
    def is_user_message(self) -> bool:
        """Prüfe ob es eine User-Nachricht ist."""
        return self.role == "user"
    
    def is_assistant_message(self) -> bool:
        """Prüfe ob es eine Assistant-Nachricht ist."""
        return self.role == "assistant"
    
    def has_sources(self) -> bool:
        """Prüfe ob Nachricht Quellen hat."""
        return len(self.source_references) > 0
    
    def get_source_references(self) -> List[SourceReference]:
        """Returniere Source References."""
        return self.source_references
    
    def get_confidence_for_chunk(self, chunk_id: str) -> Optional[float]:
        """
        Returniere Confidence Score für einen Chunk aus source_references.
        
        Args:
            chunk_id: Chunk-ID
            
        Returns:
            Confidence Score oder None
        """
        for ref in self.source_references:
            if str(ref.chunk_id) == str(chunk_id):
                return ref.relevance_score
        return None


@dataclass
class RAGAuditLog:
    """
    Audit-Trail für RAG-Operationen.
    
    Vollständige Historie aller Indexierungs-, Chunking- und Query-Operationen
    für Compliance und Transparenz.
    
    Attributes:
        id: Eindeutige ID (None bei neuen Entities)
        indexed_document_id: FK zu IndexedDocument (NULL bei Chat-Queries)
        action: Action-Type (z.B. "chunking_started", "query_executed")
        user_id: User der die Aktion ausgeführt hat
        timestamp: Zeitstempel der Aktion
        details: JSON-Details mit allen Parametern
        status: Status der Aktion ("success", "failed", "in_progress")
        error_message: Fehler-Message (nur bei failed)
        duration_ms: Dauer der Operation in Millisekunden
        tokens_used: Anzahl verwendeter Tokens (bei AI-Calls)
        cost_usd: Geschätzte Kosten in USD
    """
    id: Optional[int]
    indexed_document_id: Optional[int]  # NULL bei Chat-Queries
    action: str
    user_id: int
    timestamp: datetime
    details: Dict[str, Any]
    status: str  # "success", "failed", "in_progress"
    error_message: Optional[str]
    
    # Metadata für ML/Analytics
    duration_ms: Optional[int]
    tokens_used: Optional[int]
    cost_usd: Optional[float]
    
    # Valide Action-Types
    VALID_ACTIONS = {
               "chunking_started",
               "chunking_completed",
               "chunking_failed",
               "chunk_created",
               "chunk_edited",
               "chunk_deleted",
               "embedding_started",
               "embedding_completed",
               "embedding_failed",
               "indexing_started",
               "indexing_completed",
               "indexing_failed",
               "query_executed",
               "feedback_submitted"  # PHASE 4.1: User Feedback
           }
    
    # Valide Status-Types
    VALID_STATUSES = {"success", "failed", "in_progress"}
    
    def __post_init__(self):
        """Validiere Entity nach Initialisierung."""
        # Validiere Action
        if self.action not in self.VALID_ACTIONS:
            raise ValueError(
                f"Invalid action: {self.action}. "
                f"Must be one of: {', '.join(sorted(self.VALID_ACTIONS))}"
            )
        
        # Validiere Status
        if self.status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid status: {self.status}. "
                f"Must be one of: {', '.join(sorted(self.VALID_STATUSES))}"
            )
        
        # Validiere User ID
        if self.user_id <= 0:
            raise ValueError("user_id must be positive")
        
        # Validiere Details (muss JSON-serialisierbar sein)
        if not isinstance(self.details, dict):
            raise ValueError("details must be a dictionary")


# ============================================================================
# RAG FEEDBACK ENTITY (PHASE 4.1)
# ============================================================================

@dataclass
class RAGFeedback:
    """
    User Feedback für RAG Chat-Antworten.

    Ermöglicht es Usern, Feedback zu RAG-Antworten zu geben für:
    - Qualitätsverbesserung
    - ML-Training
    - Analytics

    Attributes:
        id: Eindeutige ID (None bei neuen Entities)
        chat_message_id: FK zu ChatMessage (Assistant-Message)
        user_id: User der das Feedback gegeben hat
        rating: Bewertung ("positive", "negative", "neutral")
        comment: Optionaler Kommentar (max 2000 Zeichen)
        submitted_at: Zeitstempel der Abgabe
    """
    id: Optional[int]
    chat_message_id: int
    user_id: int
    rating: str  # "positive", "negative", "neutral"
    comment: Optional[str]
    submitted_at: datetime

    # Valide Rating-Types
    VALID_RATINGS = {"positive", "negative", "neutral"}

    # Max-Länge für Kommentar
    MAX_COMMENT_LENGTH = 2000

    def __post_init__(self):
        """Validiere Entity nach Initialisierung."""
        # Validiere Rating
        if self.rating not in self.VALID_RATINGS:
            raise ValueError(
                f"Invalid rating: {self.rating}. "
                f"Must be one of: {', '.join(sorted(self.VALID_RATINGS))}"
            )

        # Validiere User ID
        if self.user_id <= 0:
            raise ValueError("user_id must be positive")

        # Validiere Chat Message ID
        if self.chat_message_id <= 0:
            raise ValueError("chat_message_id must be positive")

        # Validiere Kommentar-Länge
        if self.comment and len(self.comment) > self.MAX_COMMENT_LENGTH:
            raise ValueError(
                f"comment must not exceed {self.MAX_COMMENT_LENGTH} characters"
            )

        # Trimme Kommentar
        if self.comment:
            self.comment = self.comment.strip()
            if not self.comment:
                self.comment = None
