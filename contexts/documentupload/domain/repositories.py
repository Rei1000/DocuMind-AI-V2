"""
Repository Interfaces (Ports) für Document Upload Context

Repositories sind Abstractions für Persistence.
Sie definieren die Schnittstelle, ohne die Implementierung festzulegen.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any
from .entities import UploadedDocument, DocumentPage, InterestGroupAssignment, AIProcessingResult, WorkflowStatusChange, DocumentComment
from .value_objects import WorkflowStatus


class UploadRepository(ABC):
    """
    Repository Interface für UploadedDocument Aggregate.
    
    Port: Definiert die Persistence-Schnittstelle für Uploads.
    Adapter: SQLAlchemyUploadRepository (in infrastructure/)
    """
    
    @abstractmethod
    async def save(self, document: UploadedDocument) -> UploadedDocument:
        """
        Speichere UploadedDocument (Create oder Update).
        
        Args:
            document: UploadedDocument Entity
            
        Returns:
            UploadedDocument mit ID (falls neu)
            
        Raises:
            RepositoryError: Bei Persistence-Fehler
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, document_id: int) -> Optional[UploadedDocument]:
        """
        Lade UploadedDocument by ID.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            UploadedDocument oder None
        """
        pass
    
    @abstractmethod
    async def get_all(
        self,
        user_id: Optional[int] = None,
        document_type_id: Optional[int] = None,
        processing_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[UploadedDocument]:
        """
        Lade alle UploadedDocuments mit optionalen Filtern.
        
        Args:
            user_id: Filter nach Uploader
            document_type_id: Filter nach Dokumenttyp
            processing_status: Filter nach Status
            limit: Max Anzahl Ergebnisse
            offset: Offset für Pagination
            
        Returns:
            Liste von UploadedDocuments
        """
        pass
    
    @abstractmethod
    async def delete(self, document_id: int) -> bool:
        """
        Lösche UploadedDocument (Soft Delete).
        
        Args:
            document_id: Dokument ID
            
        Returns:
            True wenn erfolgreich, False wenn nicht gefunden
        """
        pass
    
    @abstractmethod
    async def exists(self, document_id: int) -> bool:
        """
        Prüfe ob UploadedDocument existiert.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            True wenn existiert
        """
        pass
    
    @abstractmethod
    async def get_by_workflow_status(self, status: WorkflowStatus) -> List[UploadedDocument]:
        """
        Lade UploadedDocuments nach Workflow-Status.
        
        Args:
            status: Workflow-Status
            
        Returns:
            Liste von UploadedDocuments
        """
        pass
    
    @abstractmethod
    async def get_by_workflow_status_and_interest_groups(
        self, 
        status: WorkflowStatus, 
        interest_group_ids: List[int]
    ) -> List[UploadedDocument]:
        """
        Lade UploadedDocuments nach Workflow-Status und Interest Groups.
        
        Args:
            status: Workflow-Status
            interest_group_ids: Liste der Interest Group IDs
            
        Returns:
            Liste von UploadedDocuments
        """
        pass


class DocumentPageRepository(ABC):
    """
    Repository Interface für DocumentPage Entities.
    
    Port: Definiert die Persistence-Schnittstelle für Pages.
    Adapter: SQLAlchemyDocumentPageRepository (in infrastructure/)
    """
    
    @abstractmethod
    async def save(self, page: DocumentPage) -> DocumentPage:
        """
        Speichere DocumentPage (Create oder Update).
        
        Args:
            page: DocumentPage Entity
            
        Returns:
            DocumentPage mit ID (falls neu)
        """
        pass
    
    @abstractmethod
    async def get_by_document_id(self, document_id: int) -> List[DocumentPage]:
        """
        Lade alle Pages eines Dokuments.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            Liste von DocumentPages (sortiert nach page_number)
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, page_id: int) -> Optional[DocumentPage]:
        """
        Lade DocumentPage by ID.
        
        Args:
            page_id: Page ID
            
        Returns:
            DocumentPage oder None
        """
        pass
    
    @abstractmethod
    async def delete_by_document_id(self, document_id: int) -> int:
        """
        Lösche alle Pages eines Dokuments.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            Anzahl gelöschter Pages
        """
        pass


class InterestGroupAssignmentRepository(ABC):
    """
    Repository Interface für InterestGroupAssignment Entities.
    
    Port: Definiert die Persistence-Schnittstelle für Assignments.
    Adapter: SQLAlchemyInterestGroupAssignmentRepository (in infrastructure/)
    """
    
    @abstractmethod
    async def save(self, assignment: InterestGroupAssignment) -> InterestGroupAssignment:
        """
        Speichere InterestGroupAssignment.
        
        Args:
            assignment: InterestGroupAssignment Entity
            
        Returns:
            InterestGroupAssignment mit ID (falls neu)
        """
        pass
    
    @abstractmethod
    async def get_by_document_id(self, document_id: int) -> List[InterestGroupAssignment]:
        """
        Lade alle Assignments eines Dokuments.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            Liste von InterestGroupAssignments
        """
        pass
    
    @abstractmethod
    async def delete_by_document_id(self, document_id: int) -> int:
        """
        Lösche alle Assignments eines Dokuments.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            Anzahl gelöschter Assignments
        """
        pass
    
    @abstractmethod
    async def exists(self, document_id: int, interest_group_id: int) -> bool:
        """
        Prüfe ob Assignment existiert.
        
        Args:
            document_id: Dokument ID
            interest_group_id: Interest Group ID
            
        Returns:
            True wenn existiert
        """
        pass


class AIResponseRepository(ABC):
    """
    Repository Interface für AIProcessingResult Entities.
    
    Port: Definiert die Persistence-Schnittstelle für AI-Responses.
    Adapter: SQLAlchemyAIResponseRepository (in infrastructure/)
    """
    
    @abstractmethod
    async def save(self, ai_response: AIProcessingResult) -> AIProcessingResult:
        """
        Speichere AIProcessingResult (Create oder Update).
        
        Args:
            ai_response: AIProcessingResult Entity
            
        Returns:
            AIProcessingResult mit ID (falls neu)
        """
        pass
    
    @abstractmethod
    async def get_by_page_id(self, page_id: int) -> Optional[AIProcessingResult]:
        """
        Lade AIProcessingResult für eine Seite.
        
        Args:
            page_id: DocumentPage ID
            
        Returns:
            AIProcessingResult oder None
        """
        pass
    
    @abstractmethod
    async def get_by_document_id(self, document_id: int) -> List[AIProcessingResult]:
        """
        Lade alle AIProcessingResults eines Dokuments.
        
        Args:
            document_id: UploadDocument ID
            
        Returns:
            Liste von AIProcessingResults (sortiert nach page_number)
        """
        pass
    
    @abstractmethod
    async def exists_for_page(self, page_id: int) -> bool:
        """
        Prüfe ob AIProcessingResult für Seite existiert.
        
        Args:
            page_id: DocumentPage ID
            
        Returns:
            True wenn existiert
        """
        pass
    
    @abstractmethod
    async def update_result(self, ai_response: AIProcessingResult) -> AIProcessingResult:
        """
        Update existierendes AIProcessingResult.
        
        Args:
            ai_response: AIProcessingResult Entity (mit ID)
            
        Returns:
            Aktualisiertes AIProcessingResult
        """
        pass
    
    @abstractmethod
    async def delete_by_document_id(self, document_id: int) -> int:
        """
        Lösche alle AIProcessingResults eines Dokuments.
        
        Args:
            document_id: UploadDocument ID
            
        Returns:
            Anzahl gelöschter Responses
        """
        pass


class PromptTemplateRepository(ABC):
    """
    Repository Interface für PromptTemplate Entities.
    
    Port: Definiert die Persistence-Schnittstelle für Prompt Templates.
    Adapter: SQLAlchemyPromptTemplateRepository (in prompttemplates context)
    """
    
    @abstractmethod
    async def get_default_for_document_type(self, document_type_id: int) -> Optional[Any]:
        """
        Hole Standard-Prompt-Template für Dokumenttyp.
        
        Args:
            document_type_id: Dokumenttyp ID
            
        Returns:
            PromptTemplate oder None
        """
        pass


class WorkflowHistoryRepository(ABC):
    """
    Repository Interface für WorkflowStatusChange Entities.
    
    Port: Definiert die Persistence-Schnittstelle für Workflow-Historie.
    Adapter: SQLAlchemyWorkflowHistoryRepository (in infrastructure/)
    """
    
    @abstractmethod
    async def save(self, status_change: WorkflowStatusChange) -> WorkflowStatusChange:
        """
        Speichere WorkflowStatusChange.
        
        Args:
            status_change: WorkflowStatusChange Entity
            
        Returns:
            WorkflowStatusChange mit ID (falls neu)
        """
        pass
    
    @abstractmethod
    async def get_by_document_id(self, document_id: int) -> List[WorkflowStatusChange]:
        """
        Lade Workflow-Historie für ein Dokument.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            Liste von WorkflowStatusChanges (chronologisch sortiert)
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, change_id: int) -> Optional[WorkflowStatusChange]:
        """
        Lade WorkflowStatusChange by ID.
        
        Args:
            change_id: Change ID
            
        Returns:
            WorkflowStatusChange oder None
        """
        pass


class DocumentCommentRepository(ABC):
    """
    Repository Interface für DocumentComment Entities.
    
    Port: Definiert die Persistence-Schnittstelle für Kommentare.
    Adapter: SQLAlchemyDocumentCommentRepository (in infrastructure/)
    """
    
    @abstractmethod
    async def save(self, comment: DocumentComment) -> DocumentComment:
        """
        Speichere DocumentComment.
        
        Args:
            comment: DocumentComment Entity
            
        Returns:
            DocumentComment mit ID (falls neu)
        """
        pass
    
    @abstractmethod
    async def get_by_document_id(self, document_id: int) -> List[DocumentComment]:
        """
        Lade alle Kommentare für ein Dokument.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            Liste von DocumentComments (chronologisch sortiert)
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, comment_id: int) -> Optional[DocumentComment]:
        """
        Lade DocumentComment by ID.
        
        Args:
            comment_id: Comment ID
            
        Returns:
            DocumentComment oder None
        """
        pass
    
    @abstractmethod
    async def get_by_status_change_id(self, status_change_id: int) -> List[DocumentComment]:
        """
        Lade Kommentare für eine Status-Änderung.
        
        Args:
            status_change_id: WorkflowStatusChange ID
            
        Returns:
            Liste von DocumentComments
        """
        pass

