"""
Document Workflow Repository Interfaces.

Abstrakte Interfaces für Datenzugriff - Implementation in Infrastructure Layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from .entities import (
    DocumentWorkflow, 
    StatusChange, 
    DocumentComment,
    WorkflowStatus,
    CommentType
)


class IDocumentWorkflowRepository(ABC):
    """Repository Interface für Document Workflow."""
    
    @abstractmethod
    async def get_by_document_id(self, document_id: int) -> Optional[DocumentWorkflow]:
        """Hole Workflow für ein Dokument."""
        pass
    
    @abstractmethod
    async def save(self, workflow: DocumentWorkflow) -> DocumentWorkflow:
        """Speichere oder update Workflow."""
        pass
    
    @abstractmethod
    async def update_status(
        self, 
        document_id: int, 
        new_status: WorkflowStatus,
        user_id: int,
        reason: Optional[str] = None,
        comment: Optional[str] = None
    ) -> DocumentWorkflow:
        """Update Workflow Status mit Audit Trail."""
        pass
    
    @abstractmethod
    async def get_documents_by_status(
        self, 
        status: WorkflowStatus,
        interest_group_ids: Optional[List[int]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[dict]:
        """Hole Dokumente nach Status, optional gefiltert nach Interest Groups."""
        pass


class IStatusChangeRepository(ABC):
    """Repository Interface für Status Changes (Audit Trail)."""
    
    @abstractmethod
    async def create(self, status_change: StatusChange) -> StatusChange:
        """Erstelle neuen Status Change Eintrag."""
        pass
    
    @abstractmethod
    async def get_by_document_id(
        self, 
        document_id: int,
        limit: int = 100
    ) -> List[StatusChange]:
        """Hole Status Change History für ein Dokument."""
        pass
    
    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: int,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[StatusChange]:
        """Hole alle Status Changes eines Users."""
        pass


class IDocumentCommentRepository(ABC):
    """Repository Interface für Document Comments."""
    
    @abstractmethod
    async def create(self, comment: DocumentComment) -> DocumentComment:
        """Erstelle neuen Kommentar."""
        pass
    
    @abstractmethod
    async def get_by_document_id(
        self,
        document_id: int,
        page_number: Optional[int] = None,
        comment_type: Optional[CommentType] = None,
        limit: int = 100
    ) -> List[DocumentComment]:
        """Hole Kommentare für ein Dokument."""
        pass
    
    @abstractmethod
    async def get_by_id(self, comment_id: int) -> Optional[DocumentComment]:
        """Hole einzelnen Kommentar."""
        pass
    
    @abstractmethod
    async def update(self, comment: DocumentComment) -> DocumentComment:
        """Update existierenden Kommentar."""
        pass
    
    @abstractmethod
    async def delete(self, comment_id: int) -> bool:
        """Lösche Kommentar."""
        pass
