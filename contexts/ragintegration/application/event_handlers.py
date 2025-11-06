"""
Event Handlers für RAG Integration Context

Event Handlers verarbeiten Domain Events und führen entsprechende Aktionen aus.
"""
from datetime import datetime
from typing import Optional

from ..domain.events import (
    ChunkingStartedEvent,
    ChunkingCompletedEvent,
    ChunkingFailedEvent,
    IndexingStartedEvent,
    IndexingCompletedEvent,
    IndexingFailedEvent,
    QueryExecutedEvent,
    FeedbackSubmittedEvent  # PHASE 4.1: Feedback Events
)
from .use_cases import LogRAGActionUseCase


class RAGAuditEventHandler:
    """
    Event Handler für Audit-Logging.
    
    Fängt Domain Events ab und loggt sie im Audit-Trail für Compliance
    und Transparenz.
    
    Attributes:
        log_action_use_case: Use Case zum Loggen von RAG-Aktionen
    """
    
    def __init__(self, log_action_use_case: LogRAGActionUseCase):
        """
        Initialisiere Event Handler.
        
        Args:
            log_action_use_case: LogRAGActionUseCase Instance
        """
        self.log_action_use_case = log_action_use_case
    
    async def handle_chunking_started(self, event: ChunkingStartedEvent):
        """
        Handle ChunkingStartedEvent.
        
        Loggt Start des Chunking-Prozesses.
        
        Args:
            event: ChunkingStartedEvent
        """
        await self.log_action_use_case.execute(
            action="chunking_started",
            user_id=event.user_id,
            indexed_document_id=None,  # Noch kein IndexedDocument
            details={
                "document_id": event.document_id,
                "strategy": event.strategy
            },
            status="in_progress"
        )
    
    async def handle_chunking_completed(self, event: ChunkingCompletedEvent):
        """
        Handle ChunkingCompletedEvent.
        
        Loggt erfolgreichen Abschluss des Chunking-Prozesses.
        
        Args:
            event: ChunkingCompletedEvent
        """
        await self.log_action_use_case.execute(
            action="chunking_completed",
            user_id=1,  # TODO: User ID vom Event holen
            indexed_document_id=event.indexed_document_id,
            details={
                "document_id": event.document_id,
                "total_chunks": event.total_chunks
            },
            status="success",
            duration_ms=event.duration_ms
        )
    
    async def handle_chunking_failed(self, event: ChunkingFailedEvent):
        """
        Handle ChunkingFailedEvent.
        
        Loggt fehlgeschlagenen Chunking-Prozess.
        
        Args:
            event: ChunkingFailedEvent
        """
        await self.log_action_use_case.execute(
            action="chunking_failed",
            user_id=1,  # TODO: User ID vom Event holen
            indexed_document_id=None,
            details={
                "document_id": event.document_id
            },
            status="failed",
            error_message=event.error_message
        )
    
    async def handle_indexing_started(self, event: IndexingStartedEvent):
        """
        Handle IndexingStartedEvent.
        
        Loggt Start der Qdrant-Indexierung.
        
        Args:
            event: IndexingStartedEvent
        """
        await self.log_action_use_case.execute(
            action="indexing_started",
            user_id=1,  # TODO: User ID vom Event holen
            indexed_document_id=event.indexed_document_id,
            details={
                "total_chunks": event.total_chunks
            },
            status="in_progress"
        )
    
    async def handle_indexing_completed(self, event: IndexingCompletedEvent):
        """
        Handle IndexingCompletedEvent.
        
        Loggt erfolgreichen Abschluss der Qdrant-Indexierung.
        
        Args:
            event: IndexingCompletedEvent
        """
        await self.log_action_use_case.execute(
            action="indexing_completed",
            user_id=1,  # TODO: User ID vom Event holen
            indexed_document_id=event.indexed_document_id,
            details={
                "total_chunks": event.total_chunks
            },
            status="success",
            duration_ms=event.duration_ms
        )
    
    async def handle_indexing_failed(self, event: IndexingFailedEvent):
        """
        Handle IndexingFailedEvent.
        
        Loggt fehlgeschlagene Qdrant-Indexierung.
        
        Args:
            event: IndexingFailedEvent
        """
        await self.log_action_use_case.execute(
            action="indexing_failed",
            user_id=1,  # TODO: User ID vom Event holen
            indexed_document_id=event.indexed_document_id,
            details={},
            status="failed",
            error_message=event.error_message
        )
    
    async def handle_query_executed(self, event: QueryExecutedEvent):
        """
        Handle QueryExecutedEvent.
        
        Loggt ausgeführte RAG Query.
        
        Args:
            event: QueryExecutedEvent
        """
        await self.log_action_use_case.execute(
            action="query_executed",
            user_id=event.user_id,
            indexed_document_id=None,  # Queries haben keine spezifische Document ID
            details={
                "session_id": event.session_id,
                "question": event.question,
                "retrieved_chunks_count": event.retrieved_chunks_count,
                "response_length": event.response_length
            },
            status="success",
            duration_ms=event.duration_ms
        )

    async def handle_feedback_submitted(self, event: FeedbackSubmittedEvent):
        """
        Handle FeedbackSubmittedEvent.
        
        Loggt abgegebenes User Feedback.
        
        Args:
            event: FeedbackSubmittedEvent
        """
        await self.log_action_use_case.execute(
            action="feedback_submitted",
            user_id=event.user_id,
            indexed_document_id=None,  # Feedback ist nicht direkt an ein Dokument gebunden
            details={
                "feedback_id": event.feedback_id,
                "chat_message_id": event.chat_message_id,
                "rating": event.rating
            },
            status="success"
        )
