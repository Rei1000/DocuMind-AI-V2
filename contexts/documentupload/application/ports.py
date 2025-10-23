"""
Application Ports für Document Upload Context

Ports definieren die Schnittstellen zwischen Application und Infrastructure Layer.
Sie abstrahieren externe Abhängigkeiten und ermöglichen Dependency Injection.
"""

from abc import ABC, abstractmethod
from typing import Protocol
from ..domain.value_objects import WorkflowStatus


class WorkflowPermissionService(Protocol):
    """
    Port: Workflow Permission Service
    
    Definiert die Schnittstelle für Workflow-Berechtigungen.
    Implementierung: SQLAlchemyWorkflowPermissionService (in infrastructure/)
    """
    
    async def can_change_status(
        self,
        user_id: int,
        from_status: WorkflowStatus,
        to_status: WorkflowStatus
    ) -> bool:
        """
        Prüfe ob User Status-Änderung durchführen darf.
        
        Args:
            user_id: User ID
            from_status: Ausgangs-Status
            to_status: Ziel-Status
            
        Returns:
            True wenn erlaubt, False sonst
        """
        ...
    
    async def get_user_level(self, user_id: int) -> int:
        """
        Hole User-Level (1-5, wobei 5 = Admin).
        
        Args:
            user_id: User ID
            
        Returns:
            User-Level (1-5)
            
        Raises:
            ValueError: Wenn User nicht existiert
        """
        ...


class EventPublisher(Protocol):
    """
    Port: Event Publisher
    
    Definiert die Schnittstelle für Domain Event Publishing.
    Implementierung: InMemoryEventPublisher oder MessageQueueEventPublisher
    """
    
    async def publish(self, event) -> None:
        """
        Publiziere Domain Event.
        
        Args:
            event: Domain Event (z.B. DocumentWorkflowChangedEvent)
        """
        ...


class NotificationService(Protocol):
    """
    Port: Notification Service
    
    Definiert die Schnittstelle für Benachrichtigungen.
    Implementierung: EmailNotificationService, SlackNotificationService, etc.
    """
    
    async def notify_workflow_status_change(
        self,
        document_id: int,
        old_status: WorkflowStatus,
        new_status: WorkflowStatus,
        changed_by_user_id: int,
        reason: str
    ) -> None:
        """
        Benachrichtige betroffene User über Status-Änderung.
        
        Args:
            document_id: Dokument ID
            old_status: Vorheriger Status
            new_status: Neuer Status
            changed_by_user_id: User ID des Änderers
            reason: Grund für die Änderung
        """
        ...


class RAGIndexingService(Protocol):
    """
    Port: RAG Indexing Service
    
    Definiert die Schnittstelle für RAG-Indexierung.
    Implementierung: VectorDBIndexingService, ElasticsearchIndexingService, etc.
    """
    
    async def index_document_for_rag(
        self,
        document_id: int,
        content: str,
        metadata: dict
    ) -> None:
        """
        Indexiere Dokument für RAG-System.
        
        Args:
            document_id: Dokument ID
            content: Dokumenten-Inhalt
            metadata: Metadaten für Indexierung
        """
        ...
    
    async def remove_document_from_rag(self, document_id: int) -> None:
        """
        Entferne Dokument aus RAG-Index.
        
        Args:
            document_id: Dokument ID
        """
        ...
