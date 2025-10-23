"""
Application Ports (Interfaces) für Document Upload Context

Ports definieren die Schnittstellen zwischen Application und Infrastructure Layer.
Sie ermöglichen Dependency Inversion und Testbarkeit.
"""

from abc import ABC, abstractmethod
from typing import List, Protocol
from ..domain.entities import UploadedDocument
from ..domain.value_objects import WorkflowStatus


class WorkflowPermissionService(Protocol):
    """
    Port: Workflow Permission Service
    
    Definiert die Schnittstelle für Workflow-Berechtigungen.
    Adapter: WorkflowPermissionServiceImpl (in infrastructure/)
    
    Permission-Matrix:
    - Level 2 (Mitarbeiter): Read-only, nur eigene Interest Groups
    - Level 3 (Teamleiter): Read + draft → reviewed, nur eigene Interest Groups
    - Level 4 (QM-Manager): Read + reviewed → approved, any → rejected, alle Dokumente
    - Level 5 (QMS Admin): Vollzugriff auf alle Dokumente und Transitions
    """
    
    def can_view_document(self, user_id: int, document: UploadedDocument) -> bool:
        """
        Prüfe ob User Dokument sehen darf.
        
        Args:
            user_id: User ID
            document: UploadedDocument Entity
            
        Returns:
            True wenn User Dokument sehen darf
        """
        ...
    
    def can_change_status(self, user_id: int, from_status: WorkflowStatus, to_status: WorkflowStatus) -> bool:
        """
        Prüfe ob User Status-Transition durchführen darf.
        
        Args:
            user_id: User ID
            from_status: Quell-Status
            to_status: Ziel-Status
            
        Returns:
            True wenn Transition erlaubt
        """
        ...
    
    def get_allowed_transitions(self, user_id: int, current_status: WorkflowStatus) -> List[WorkflowStatus]:
        """
        Hole alle erlaubten Ziel-Status für User und aktuellen Status.
        
        Args:
            user_id: User ID
            current_status: Aktueller Workflow-Status
            
        Returns:
            Liste der erlaubten Ziel-Status
        """
        ...
    
    def get_user_level(self, user_id: int) -> int:
        """
        Hole User-Berechtigungslevel.
        
        Args:
            user_id: User ID
            
        Returns:
            User-Level (2-5)
            
        Raises:
            ValueError: Wenn User-Level ungültig
        """
        ...
    
    def get_user_interest_groups(self, user_id: int) -> List[int]:
        """
        Hole Interest Groups des Users.
        
        Args:
            user_id: User ID
            
        Returns:
            Liste der Interest Group IDs
        """
        ...


class EventPublisher(Protocol):
    """
    Port: Event Publisher
    
    Definiert die Schnittstelle für Event-Publishing.
    Adapter: InMemoryEventPublisher oder MessageBus (in infrastructure/)
    """
    
    def publish(self, event) -> None:
        """
        Publiziere Domain Event.
        
        Args:
            event: Domain Event
        """
        ...


class NotificationService(Protocol):
    """
    Port: Notification Service
    
    Definiert die Schnittstelle für Benachrichtigungen.
    Adapter: EmailNotificationService oder SlackNotificationService (in infrastructure/)
    """
    
    def notify_workflow_status_changed(
        self, 
        document_id: int, 
        from_status: WorkflowStatus, 
        to_status: WorkflowStatus,
        changed_by_user_id: int,
        comment: str = None
    ) -> None:
        """
        Benachrichtige über Workflow-Status-Änderung.
        
        Args:
            document_id: Dokument ID
            from_status: Vorheriger Status
            to_status: Neuer Status
            changed_by_user_id: User ID des Änderers
            comment: Optionaler Kommentar
        """
        ...
