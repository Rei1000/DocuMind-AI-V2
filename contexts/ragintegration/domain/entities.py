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
    """
    id: Optional[int]
    upload_document_id: int
    collection_name: str
    total_chunks: int
    indexed_at: datetime
    last_updated: datetime
    
    def __post_init__(self):
        """Validiere Entity nach Initialisierung."""
        if self.upload_document_id <= 0:
            raise ValueError("upload_document_id must be positive")
        
        if not self.collection_name or not self.collection_name.strip():
            raise ValueError("collection_name cannot be empty")
        
        if self.total_chunks <= 0:
            raise ValueError("total_chunks must be positive")


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
        source_chunk_ids: Liste der verwendeten Chunk-IDs
        confidence_scores: Confidence Scores pro Chunk-ID
        created_at: Zeitstempel der Erstellung
        source_references: Liste der Source References (optional)
    """
    id: Optional[int]
    session_id: int
    role: str
    content: str
    source_chunk_ids: List[str]
    confidence_scores: Dict[str, float]
    created_at: datetime
    source_references: List[SourceReference] = field(default_factory=list)
    
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
        return len(self.source_chunk_ids) > 0
    
    def get_source_references(self) -> List[SourceReference]:
        """Returniere Source References."""
        return self.source_references
    
    def get_confidence_for_chunk(self, chunk_id: str) -> Optional[float]:
        """
        Returniere Confidence Score für einen Chunk.
        
        Args:
            chunk_id: Chunk-ID
            
        Returns:
            Confidence Score oder None
        """
        return self.confidence_scores.get(chunk_id)
