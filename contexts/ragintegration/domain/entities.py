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
        embedding_model: Name des verwendeten Embedding-Modells (Standard: "text-embedding-3-small", NEU v2.8.0)
    """
    id: Optional[int]
    upload_document_id: int
    collection_name: str
    total_chunks: int
    indexed_at: datetime
    last_updated_at: datetime  # Geändert von last_updated
    embedding_model: str = "text-embedding-3-small"  # NEU v2.8.0: Einheitliches Modell für alle Dokumente (1536 dim)
    
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


@dataclass
class RAGChatPrompt:
    """
    RAG Chat Prompt Entity (PHASE 1).
    
    Repräsentiert einen globalen, dokumenttyp-spezifischen RAG Chat Prompt.
    Level 4+ User können diese Prompts anpassen.
    
    Attributes:
        id: Eindeutige ID (None bei neuen Entities)
        document_type_id: FK zu DocumentType (UNIQUE - ein Prompt pro Dokumenttyp)
        prompt_text: RAG Chat Prompt-Text für diesen Dokumenttyp
        created_by_user_id: User ID des Erstellers (Audit-Trail)
        created_at: Zeitstempel der Erstellung
        updated_at: Zeitstempel der letzten Aktualisierung
        multi_query_prompt_text: Multi-Query Prompt-Text (optional, PHASE 2)
    """
    id: Optional[int]
    document_type_id: int
    prompt_text: str
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    multi_query_prompt_text: Optional[str] = None  # PHASE 2: Multi-Query Prompt (muss am Ende sein wegen Default-Wert)
    
    def __post_init__(self):
        """Validiere Entity nach Initialisierung."""
        if self.document_type_id <= 0:
            raise ValueError("document_type_id must be positive")
        
        if not self.prompt_text or not self.prompt_text.strip():
            raise ValueError("prompt_text cannot be empty")
        
        if self.created_by_user_id <= 0:
            raise ValueError("created_by_user_id must be positive")
        
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot be before created_at")
    
    def is_custom(self) -> bool:
        """Prüfe ob es ein Custom Prompt ist (immer True, da nur Custom Prompts gespeichert werden)."""
        return True  # Nur Custom Prompts werden in dieser Tabelle gespeichert
    
    def has_multi_query(self) -> bool:
        """Prüfe ob Multi-Query Prompt vorhanden ist."""
        return self.multi_query_prompt_text is not None and len(self.multi_query_prompt_text.strip()) > 0


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


# ============================================================================
# CHUNK FEEDBACK ENTITY (v2.9.0: Chunk-Level Feedback)
# ============================================================================

@dataclass
class ChunkFeedback:
    """
    User Feedback für einzelne Chunks in RAG Chat-Antworten.
    
    Ermöglicht es Usern, Feedback zu einzelnen Chunks zu geben für:
    - Präzise Qualitätsverbesserung (welche Chunks sind relevant/nicht relevant)
    - ML-Training (Chunk-Level Relevanz-Scores)
    - Analytics (Chunk-Level Metriken)
    
    Attributes:
        id: Eindeutige ID (None bei neuen Entities)
        chunk_id: Chunk-ID (aus source_references)
        chat_message_id: FK zu ChatMessage (Assistant-Message, für Kontext)
        document_id: Dokument-ID (für Kontext)
        user_id: User der das Feedback gegeben hat
        rating: Bewertung ("positive", "negative", "neutral")
        comment: Optionaler Kommentar (max 2000 Zeichen)
        submitted_at: Zeitstempel der Abgabe
    """
    id: Optional[int]
    chunk_id: str  # Chunk-ID (z.B. "doc_123_meta_abc123")
    chat_message_id: int  # FK zu ChatMessage (für Kontext)
    document_id: int  # Dokument-ID (für Kontext)
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
        
        # Validiere Document ID
        if self.document_id <= 0:
            raise ValueError("document_id must be positive")
        
        # Validiere Chunk ID
        if not self.chunk_id or not self.chunk_id.strip():
            raise ValueError("chunk_id must not be empty")
        
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


# ============================================================================
# TRAINING DATA ENTITY (PHASE 2: SHAP Training Data Collection)
# ============================================================================

@dataclass
class TrainingData:
    """
    Training Data Entity für ML-Model Training.
    
    Sammelt SHAP-Erklärungen + User-Feedback für Learning-to-Rank Model.
    
    Attributes:
        id: Eindeutige ID (None bei neuen Entities)
        query: Die ursprüngliche Query
        chunk_id: Chunk-ID
        document_id: Dokument-ID
        session_id: Chat-Session-ID
        user_id: User-ID
        vector_score: Vektor-Ähnlichkeits-Score (0-1)
        text_score: Text-Matching-Score (0-1)
        hybrid_score: Kombinierter Score (0-1)
        document_type: Dokumenttyp
        user_level: User-Level (1-5)
        keyword_matches: Anzahl der Keyword-Matches
        chunk_length: Chunk-Länge in Zeichen
        heading_hierarchy_depth: Tiefe der Heading-Hierarchie
        confidence_score: Confidence-Score (0-1)
        shap_explanation: SHAP-Erklärung (JSON)
        user_feedback: User-Feedback ("positive", "negative", "neutral", None)
        feedback_comment: Optionaler Feedback-Kommentar
        created_at: Zeitstempel der Erstellung
    """
    id: Optional[int]
    query: str
    chunk_id: str
    document_id: int
    session_id: int
    user_id: int
    vector_score: float
    text_score: float
    hybrid_score: float
    document_type: str
    user_level: int
    keyword_matches: int
    chunk_length: int
    heading_hierarchy_depth: int
    confidence_score: float
    shap_explanation: Optional[Dict[str, Any]]
    user_feedback: Optional[str]  # "positive", "negative", "neutral", None
    feedback_comment: Optional[str]
    created_at: datetime
    
    # Valide Feedback-Types
    VALID_FEEDBACK = {"positive", "negative", "neutral"}
    
    def __post_init__(self):
        """Validiere Entity nach Initialisierung."""
        if self.user_id <= 0:
            raise ValueError("user_id must be positive")
        
        if self.document_id <= 0:
            raise ValueError("document_id must be positive")
        
        if self.session_id <= 0:
            raise ValueError("session_id must be positive")
        
        if not 0.0 <= self.vector_score <= 1.0:
            raise ValueError("vector_score must be between 0.0 and 1.0")
        
        if not 0.0 <= self.text_score <= 1.0:
            raise ValueError("text_score must be between 0.0 and 1.0")
        
        if not 0.0 <= self.hybrid_score <= 1.0:
            raise ValueError("hybrid_score must be between 0.0 and 1.0")
        
        if self.user_feedback and self.user_feedback not in self.VALID_FEEDBACK:
            raise ValueError(
                f"Invalid feedback: {self.user_feedback}. "
                f"Must be one of: {', '.join(sorted(self.VALID_FEEDBACK))}"
            )
