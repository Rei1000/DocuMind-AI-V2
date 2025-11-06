"""
Domain Repository Interfaces für RAG Integration Context.

Repository Interfaces definieren die Contracts für Persistence Operations.
Sie werden von Infrastructure Layer implementiert (Ports & Adapters Pattern).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from .entities import IndexedDocument, DocumentChunk, ChatSession, ChatMessage
from .value_objects import EmbeddingVector, ChunkMetadata, RAGConfig


class IndexedDocumentRepository(ABC):
    """Repository Interface für IndexedDocument."""
    
    @abstractmethod
    def get_by_id(self, indexed_document_id: int) -> Optional[IndexedDocument]:
        """Hole IndexedDocument nach ID."""
        pass
    
    @abstractmethod
    def get_by_upload_document_id(self, upload_document_id: int) -> Optional[IndexedDocument]:
        """Hole IndexedDocument nach Upload Document ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[IndexedDocument]:
        """Hole alle IndexedDocuments."""
        pass
    
    @abstractmethod
    def save(self, indexed_document: IndexedDocument) -> IndexedDocument:
        """Speichere IndexedDocument."""
        pass
    
    @abstractmethod
    def delete(self, indexed_document_id: int) -> bool:
        """Lösche IndexedDocument."""
        pass
    
    @abstractmethod
    def exists_by_upload_document_id(self, upload_document_id: int) -> bool:
        """Prüfe ob IndexedDocument existiert."""
        pass
    
    @abstractmethod
    def count_by_document_type(
        self, 
        document_type_id: int,
        interest_group_ids: Optional[List[int]] = None
    ) -> int:
        """Zähle IndexedDocuments für einen DocumentType.
        
        Args:
            document_type_id: Document Type ID
            interest_group_ids: Optional - Filter nach Interest Groups (RBAC)
                              None/Leere Liste = alle Dokumente
                              Liste mit IDs = nur Dokumente in diesen IGs
        """
        pass


class DocumentChunkRepository(ABC):
    """Repository Interface für DocumentChunk."""
    
    @abstractmethod
    def get_by_id(self, chunk_id: int) -> Optional[DocumentChunk]:
        """Hole DocumentChunk nach ID."""
        pass
    
    @abstractmethod
    def get_by_chunk_id(self, chunk_id: str) -> Optional[DocumentChunk]:
        """Hole DocumentChunk nach Chunk ID."""
        pass
    
    @abstractmethod
    def get_by_indexed_document_id(self, indexed_document_id: int) -> List[DocumentChunk]:
        """Hole alle Chunks eines IndexedDocuments."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[DocumentChunk]:
        """Hole alle DocumentChunks."""
        pass
    
    @abstractmethod
    def save(self, chunk: DocumentChunk) -> DocumentChunk:
        """Speichere DocumentChunk."""
        pass
    
    @abstractmethod
    def save_batch(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Speichere mehrere DocumentChunks."""
        pass
    
    @abstractmethod
    def delete(self, chunk_id: int) -> bool:
        """Lösche DocumentChunk."""
        pass
    
    @abstractmethod
    def delete_by_indexed_document_id(self, indexed_document_id: int) -> int:
        """Lösche alle Chunks eines IndexedDocuments."""
        pass
    
    @abstractmethod
    def exists_by_chunk_id(self, chunk_id: str) -> bool:
        """Prüfe ob DocumentChunk existiert."""
        pass


class ChatSessionRepository(ABC):
    """Repository Interface für ChatSession und ChatMessage."""
    
    # ChatSession Methods
    @abstractmethod
    def get_by_id(self, session_id: int) -> Optional[ChatSession]:
        """Hole ChatSession nach ID."""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[ChatSession]:
        """Hole alle ChatSessions eines Users."""
        pass
    
    @abstractmethod
    def get_active_by_user_id(self, user_id: int) -> List[ChatSession]:
        """Hole aktive ChatSessions eines Users."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[ChatSession]:
        """Hole alle ChatSessions."""
        pass
    
    @abstractmethod
    def save(self, session: ChatSession) -> ChatSession:
        """Speichere ChatSession."""
        pass
    
    @abstractmethod
    def delete(self, session_id: int) -> bool:
        """Lösche ChatSession."""
        pass
    
    # ChatMessage Methods
    @abstractmethod
    def get_messages_by_session_id(self, session_id: int) -> List[ChatMessage]:
        """Hole alle Messages einer Session."""
        pass
    
    @abstractmethod
    def save_message(self, message: ChatMessage) -> ChatMessage:
        """Speichere ChatMessage."""
        pass
    
    @abstractmethod
    def delete_message(self, message_id: int) -> bool:
        """Lösche ChatMessage."""
        pass
    
    @abstractmethod
    def get_message_count_by_session_id(self, session_id: int) -> int:
        """Zähle Messages einer Session."""
        pass


class ChatMessageRepository(ABC):
    """Repository Interface für ChatMessage."""
    
    @abstractmethod
    def get_by_id(self, message_id: int) -> Optional[ChatMessage]:
        """Hole ChatMessage nach ID."""
        pass
    
    @abstractmethod
    def get_by_session_id(self, session_id: int) -> List[ChatMessage]:
        """Hole alle ChatMessages einer Session."""
        pass
    
    @abstractmethod
    def save(self, chat_message: ChatMessage) -> ChatMessage:
        """Speichere ChatMessage."""
        pass
    
    @abstractmethod
    def delete(self, message_id: int) -> bool:
        """Lösche ChatMessage."""
        pass
    
    @abstractmethod
    def get_latest_messages(self, session_id: int, limit: int = 10) -> List[ChatMessage]:
        """Hole neueste ChatMessages einer Session."""
        pass

    @abstractmethod
    async def get_all(self) -> List[ChatMessage]:
        """Hole alle ChatMessages (für Analytics)."""
        pass


class VectorStoreRepository(ABC):
    """Repository Interface für Vector Store (Qdrant)."""
    
    @abstractmethod
    def create_collection(self, collection_name: str) -> bool:
        """Erstelle neue Collection."""
        pass
    
    @abstractmethod
    def delete_collection(self, collection_name: str) -> bool:
        """Lösche Collection."""
        pass
    
    @abstractmethod
    def collection_exists(self, collection_name: str) -> bool:
        """Prüfe ob Collection existiert."""
        pass
    
    @abstractmethod
    def index_chunk(self, collection_name: str, chunk_id: str, 
                   embedding: EmbeddingVector, metadata: Dict[str, Any]) -> bool:
        """Indexiere einzelnen Chunk."""
        pass
    
    @abstractmethod
    def index_chunks_batch(self, collection_name: str, 
                          chunks_data: List[Dict[str, Any]]) -> int:
        """Indexiere mehrere Chunks."""
        pass
    
    @abstractmethod
    def search_similar(self, collection_name: str, query_embedding: EmbeddingVector,
                      filters: Dict[str, Any], top_k: int, min_score: float) -> List[Dict[str, Any]]:
        """Suche ähnliche Chunks."""
        pass
    
    @abstractmethod
    def delete_chunk(self, collection_name: str, chunk_id: str) -> bool:
        """Lösche einzelnen Chunk."""
        pass
    
    @abstractmethod
    def delete_chunks_by_document_id(self, collection_name: str, document_id: int) -> int:
        """Lösche alle Chunks eines Dokuments."""
        pass
    
    @abstractmethod
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Hole Collection-Informationen."""
        pass


class EmbeddingService(ABC):
    """Service Interface für Embedding Generation."""
    
    @abstractmethod
    def generate_embedding(self, text: str) -> EmbeddingVector:
        """Generiere Embedding für Text."""
        pass
    
    @abstractmethod
    def generate_embeddings_batch(self, texts: List[str]) -> List[EmbeddingVector]:
        """Generiere Embeddings für mehrere Texte."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Hole Modell-Informationen."""
        pass
    
    @abstractmethod
    def get_dimensions(self) -> int:
        """Returniere Anzahl Dimensionen."""
        pass


class RAGConfigRepository(ABC):
    """Repository Interface für RAG-Konfiguration."""
    
    @abstractmethod
    def save_config(self, config: RAGConfig) -> None:
        """Speichere RAG-Konfiguration."""
        pass
    
    @abstractmethod
    def get_current_config(self) -> Optional[RAGConfig]:
        """Hole aktuelle RAG-Konfiguration."""
        pass


# ============================================================================
# AUDIT-TRAIL REPOSITORY (PHASE 1.3)
# ============================================================================

class RAGAuditLogRepository(ABC):
    """
    Repository Interface für RAGAuditLog Entities.
    
    Port: Definiert die Persistence-Schnittstelle für Audit-Logs.
    Adapter: SQLAlchemyRAGAuditLogRepository (in infrastructure/)
    """
    
    @abstractmethod
    async def save(self, audit_log) -> 'RAGAuditLog':
        """
        Speichere RAGAuditLog (Create).
        
        Args:
            audit_log: RAGAuditLog Entity
            
        Returns:
            Gespeicherter RAGAuditLog mit ID
        """
        pass
    
    @abstractmethod
    async def get_by_document_id(
        self, 
        indexed_document_id: int, 
        limit: int = 100
    ) -> List['RAGAuditLog']:
        """
        Hole alle Audit-Logs für ein Dokument.
        
        Args:
            indexed_document_id: IndexedDocument ID
            limit: Maximale Anzahl Einträge
            
        Returns:
            Liste von RAGAuditLog Entities (sortiert nach timestamp DESC)
        """
        pass
    
    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: int,
        limit: int = 100
    ) -> List['RAGAuditLog']:
        """
        Hole alle Audit-Logs für einen User.

        Args:
            user_id: User ID
            limit: Maximale Anzahl Einträge

        Returns:
            Liste von RAGAuditLog Entities (sortiert nach timestamp DESC)
        """
        pass


# ============================================================================
# RAG FEEDBACK REPOSITORY (PHASE 4.1)
# ============================================================================

class RAGFeedbackRepository(ABC):
    """
    Repository Interface für RAGFeedback Entities.

    Port: Definiert die Persistence-Schnittstelle für User Feedback.
    Adapter: SQLAlchemyRAGFeedbackRepository (in infrastructure/)
    """

    @abstractmethod
    async def save(self, feedback) -> 'RAGFeedback':
        """
        Speichere RAGFeedback (Create).

        Args:
            feedback: RAGFeedback Entity

        Returns:
            Gespeicherter RAGFeedback mit ID
        """
        pass

    @abstractmethod
    async def get_by_id(self, feedback_id: int) -> Optional['RAGFeedback']:
        """
        Hole RAGFeedback nach ID.

        Args:
            feedback_id: Feedback ID

        Returns:
            RAGFeedback Entity oder None
        """
        pass

    @abstractmethod
    async def get_by_message_id(
        self,
        chat_message_id: int,
        user_id: Optional[int] = None
    ) -> Optional['RAGFeedback']:
        """
        Hole Feedback für eine Chat-Message.

        Args:
            chat_message_id: Chat Message ID
            user_id: Optional User ID Filter (wenn angegeben, nur Feedback dieses Users)

        Returns:
            RAGFeedback Entity oder None (ein User kann nur einmal pro Message Feedback geben)
        """
        pass

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: int,
        limit: int = 100
    ) -> List['RAGFeedback']:
        """
        Hole alle Feedbacks eines Users.

        Args:
            user_id: User ID
            limit: Maximale Anzahl Einträge

        Returns:
            Liste von RAGFeedback Entities (sortiert nach submitted_at DESC)
        """
        pass

    @abstractmethod
    async def get_statistics(
        self,
        chat_message_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Hole Feedback-Statistiken.

        Args:
            chat_message_id: Optional Filter nach Chat Message
            user_id: Optional Filter nach User

        Returns:
            Dict mit Statistiken (total, positive, negative, neutral, average_rating)
        """
        pass
