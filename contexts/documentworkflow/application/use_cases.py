"""
Document Workflow Use Cases.

Orchestriert die Geschäftslogik für Document Workflow Management.
"""

from typing import List, Optional, Dict
from datetime import datetime

from ..domain.entities import (
    DocumentWorkflow,
    StatusChange,
    DocumentComment,
    WorkflowStatus,
    CommentType,
    WorkflowPermissions
)
from ..domain.repositories import (
    IDocumentWorkflowRepository,
    IStatusChangeRepository,
    IDocumentCommentRepository
)


class ChangeDocumentStatusUseCase:
    """
    Use Case: Ändere Document Status.
    
    Prüft Berechtigungen und führt Status-Änderung mit Audit Trail durch.
    """
    
    def __init__(
        self,
        workflow_repo: IDocumentWorkflowRepository,
        status_change_repo: IStatusChangeRepository,
        comment_repo: IDocumentCommentRepository
    ):
        self.workflow_repo = workflow_repo
        self.status_change_repo = status_change_repo
        self.comment_repo = comment_repo
    
    async def execute(
        self,
        document_id: int,
        new_status: WorkflowStatus,
        user_id: int,
        user_level: int,
        user_interest_groups: List[int],
        document_interest_groups: List[int],
        reason: Optional[str] = None,
        comment_text: Optional[str] = None
    ) -> Dict:
        """
        Führe Status-Änderung durch.
        
        Args:
            document_id: Document ID
            new_status: Neuer Status
            user_id: User der die Änderung macht
            user_level: User Level (1-4)
            user_interest_groups: Interest Groups des Users
            document_interest_groups: Interest Groups des Dokuments
            reason: Grund für Änderung
            comment_text: Optionaler Kommentar
            
        Returns:
            Dict mit workflow, status_change, comment
            
        Raises:
            PermissionError: Wenn keine Berechtigung
            ValueError: Wenn Übergang nicht erlaubt
        """
        # Erstelle Permissions Object
        permissions = WorkflowPermissions(
            user_id=user_id,
            user_level=user_level,
            interest_group_ids=user_interest_groups
        )
        
        # Prüfe ob User Dokument sehen darf
        if not permissions.can_view_document(document_interest_groups):
            raise PermissionError("User cannot access this document")
        
        # Hole aktuellen Workflow
        workflow = await self.workflow_repo.get_by_document_id(document_id)
        if not workflow:
            # Erstelle neuen Workflow wenn noch nicht vorhanden
            workflow = DocumentWorkflow(
                document_id=document_id,
                current_status=WorkflowStatus.DRAFT
            )
        
        # Prüfe ob Status-Änderung erlaubt
        old_status = workflow.current_status
        allowed, transition_reason = workflow.can_transition_to(new_status, user_level)
        if not allowed:
            raise ValueError(f"Status transition not allowed: {transition_reason}")
        
        # Führe Transition durch
        workflow.transition_to(new_status, user_level)
        
        # Speichere Workflow
        workflow = await self.workflow_repo.update_status(
            document_id=document_id,
            new_status=new_status,
            user_id=user_id,
            reason=reason,
            comment=comment_text
        )
        
        # Erstelle Status Change für Audit Trail
        status_change = StatusChange(
            document_id=document_id,
            from_status=old_status,
            to_status=new_status,
            changed_by_user_id=user_id,
            change_reason=reason,
            comment=comment_text
        )
        status_change = await self.status_change_repo.create(status_change)
        
        # Erstelle Kommentar wenn vorhanden
        comment = None
        if comment_text:
            # Bestimme Comment Type basierend auf Status
            comment_type = CommentType.GENERAL
            if new_status == WorkflowStatus.REVIEWED:
                comment_type = CommentType.REVIEW
            elif new_status == WorkflowStatus.APPROVED:
                comment_type = CommentType.APPROVAL
            elif new_status == WorkflowStatus.REJECTED:
                comment_type = CommentType.REJECTION
            
            comment = DocumentComment(
                document_id=document_id,
                comment_text=comment_text,
                comment_type=comment_type,
                created_by_user_id=user_id,
                status_change_id=status_change.id
            )
            comment = await self.comment_repo.create(comment)
        
        return {
            "workflow": workflow,
            "status_change": status_change,
            "comment": comment,
            "transition_reason": transition_reason
        }


class AddDocumentCommentUseCase:
    """
    Use Case: Füge Kommentar zu Dokument hinzu.
    
    Erlaubt Kommentare mit optionalem Seitenbezug.
    """
    
    def __init__(
        self,
        comment_repo: IDocumentCommentRepository
    ):
        self.comment_repo = comment_repo
    
    async def execute(
        self,
        document_id: int,
        comment_text: str,
        user_id: int,
        user_level: int,
        user_interest_groups: List[int],
        document_interest_groups: List[int],
        page_number: Optional[int] = None,
        comment_type: CommentType = CommentType.GENERAL
    ) -> DocumentComment:
        """
        Füge Kommentar hinzu.
        
        Args:
            document_id: Document ID
            comment_text: Kommentar Text
            user_id: User ID
            user_level: User Level (1-4)
            user_interest_groups: User's Interest Groups
            document_interest_groups: Document's Interest Groups
            page_number: Optional Seitennummer
            comment_type: Typ des Kommentars
            
        Returns:
            Erstellter Kommentar
            
        Raises:
            PermissionError: Wenn keine Berechtigung
            ValueError: Wenn Validierung fehlschlägt
        """
        # Prüfe Berechtigungen
        permissions = WorkflowPermissions(
            user_id=user_id,
            user_level=user_level,
            interest_group_ids=user_interest_groups
        )
        
        if not permissions.can_view_document(document_interest_groups):
            raise PermissionError("User cannot access this document")
        
        # Erstelle und validiere Kommentar
        comment = DocumentComment(
            document_id=document_id,
            comment_text=comment_text,
            comment_type=comment_type,
            page_number=page_number,
            created_by_user_id=user_id
        )
        
        comment.validate()
        
        # Speichere Kommentar
        return await self.comment_repo.create(comment)


class GetDocumentWorkflowUseCase:
    """
    Use Case: Hole Workflow-Informationen für ein Dokument.
    
    Inkludiert Status, History, Kommentare und erlaubte Aktionen.
    """
    
    def __init__(
        self,
        workflow_repo: IDocumentWorkflowRepository,
        status_change_repo: IStatusChangeRepository,
        comment_repo: IDocumentCommentRepository
    ):
        self.workflow_repo = workflow_repo
        self.status_change_repo = status_change_repo
        self.comment_repo = comment_repo
    
    async def execute(
        self,
        document_id: int,
        user_id: int,
        user_level: int,
        user_interest_groups: List[int],
        document_interest_groups: List[int]
    ) -> Dict:
        """
        Hole komplette Workflow-Information.
        
        Args:
            document_id: Document ID
            user_id: User ID
            user_level: User Level
            user_interest_groups: User's Interest Groups
            document_interest_groups: Document's Interest Groups
            
        Returns:
            Dict mit workflow, history, comments, allowed_actions
            
        Raises:
            PermissionError: Wenn keine Berechtigung
        """
        # Prüfe Berechtigungen
        permissions = WorkflowPermissions(
            user_id=user_id,
            user_level=user_level,
            interest_group_ids=user_interest_groups
        )
        
        if not permissions.can_view_document(document_interest_groups):
            raise PermissionError("User cannot access this document")
        
        # Hole Workflow
        workflow = await self.workflow_repo.get_by_document_id(document_id)
        if not workflow:
            workflow = DocumentWorkflow(
                document_id=document_id,
                current_status=WorkflowStatus.DRAFT
            )
        
        # Hole History
        history = await self.status_change_repo.get_by_document_id(document_id, limit=50)
        
        # Hole Kommentare
        comments = await self.comment_repo.get_by_document_id(document_id, limit=100)
        
        # Bestimme erlaubte Aktionen
        allowed_transitions = permissions.get_allowed_transitions(workflow.current_status)
        
        return {
            "workflow": workflow,
            "current_status": workflow.current_status,
            "history": history,
            "comments": comments,
            "allowed_transitions": allowed_transitions,
            "can_comment": True,  # Jeder der das Dokument sehen kann, kann kommentieren
            "user_permissions": {
                "is_qm": permissions.is_qm,
                "user_level": user_level,
                "can_approve": user_level >= 4,
                "can_review": user_level >= 3
            }
        }


class GetDocumentsByStatusUseCase:
    """
    Use Case: Hole Dokumente nach Workflow-Status.
    
    Filtert nach User-Berechtigungen und Interest Groups.
    """
    
    def __init__(self, workflow_repo: IDocumentWorkflowRepository):
        self.workflow_repo = workflow_repo
    
    async def execute(
        self,
        status: Optional[WorkflowStatus],
        user_id: int,
        user_level: int, 
        user_interest_groups: List[int],
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        Hole Dokumente nach Status.
        
        Args:
            status: Filter nach Status (None = alle)
            user_id: User ID
            user_level: User Level
            user_interest_groups: User's Interest Groups
            limit: Max Anzahl Ergebnisse
            offset: Offset für Pagination
            
        Returns:
            Liste von Dokumenten mit Workflow-Info
        """
        # QM sieht alle, andere nur ihre Interest Groups
        filter_groups = None if user_level >= 4 else user_interest_groups
        
        # Level 1 sieht keine Dokumente
        if user_level < 2:
            return []
        
        documents = []
        
        if status:
            # Hole Dokumente für einen spezifischen Status
            documents = await self.workflow_repo.get_documents_by_status(
                status=status,
                interest_group_ids=filter_groups,
                limit=limit,
                offset=offset
            )
        else:
            # Hole Dokumente für alle Status
            for workflow_status in WorkflowStatus:
                status_docs = await self.workflow_repo.get_documents_by_status(
                    status=workflow_status,
                    interest_group_ids=filter_groups,
                    limit=limit,
                    offset=offset
                )
                documents.extend(status_docs)
        
        # Füge Permissions Info hinzu
        permissions = WorkflowPermissions(
            user_id=user_id,
            user_level=user_level,
            interest_group_ids=user_interest_groups
        )
        
        for doc in documents:
            if "workflow_status" in doc:
                current_status = WorkflowStatus(doc["workflow_status"])
                doc["allowed_transitions"] = permissions.get_allowed_transitions(current_status)
        
        return documents
