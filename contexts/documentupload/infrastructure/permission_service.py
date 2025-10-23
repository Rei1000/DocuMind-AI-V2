"""
Permission Service Implementation für Document Upload Context

Implementiert WorkflowPermissionService Port mit echter Datenbank-Logik.
"""

from typing import List
from sqlalchemy.orm import Session
from backend.app.models import User, UserGroupMembership
from ..application.ports import WorkflowPermissionService
from ..domain.entities import UploadedDocument
from ..domain.value_objects import WorkflowStatus


class WorkflowPermissionServiceImpl(WorkflowPermissionService):
    """
    Implementation des WorkflowPermissionService.
    
    Adapter: Implementiert WorkflowPermissionService Port mit SQLAlchemy.
    
    Args:
        db: SQLAlchemy Session
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def can_view_document(self, user_id: int, document: UploadedDocument) -> bool:
        """
        Prüfe ob User Dokument sehen darf.
        
        Args:
            user_id: User ID
            document: UploadedDocument Entity
            
        Returns:
            True wenn User Dokument sehen darf
        """
        user_level = self.get_user_level(user_id)
        
        # Level 2: Nur eigene Interest Groups
        if user_level == 2:
            user_interest_groups = self.get_user_interest_groups(user_id)
            return any(group_id in user_interest_groups for group_id in document.interest_group_ids)
        
        # Level 3+: Alle Dokumente
        return True
    
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
        user_level = self.get_user_level(user_id)
        
        # Gleicher Status ist nie erlaubt
        if from_status == to_status:
            return False
        
        # Level 2: Read-only, keine Transitions
        if user_level == 2:
            return False
        
        # Level 3: Nur draft → reviewed
        if user_level == 3:
            return from_status == WorkflowStatus.DRAFT and to_status == WorkflowStatus.REVIEWED
        
        # Level 4: reviewed → approved, any → rejected
        if user_level == 4:
            return (
                (from_status == WorkflowStatus.REVIEWED and to_status == WorkflowStatus.APPROVED) or
                to_status == WorkflowStatus.REJECTED
            )
        
        # Level 5: Alle Transitions (außer same-status, was oben geprüft wird)
        if user_level == 5:
            return True
        
        return False
    
    def get_allowed_transitions(self, user_id: int, current_status: WorkflowStatus) -> List[WorkflowStatus]:
        """
        Hole alle erlaubten Ziel-Status für User und aktuellen Status.
        
        Args:
            user_id: User ID
            current_status: Aktueller Workflow-Status
            
        Returns:
            Liste der erlaubten Ziel-Status
        """
        user_level = self.get_user_level(user_id)
        
        allowed = []
        for target_status in WorkflowStatus:
            if self.can_change_status(user_id, current_status, target_status):
                allowed.append(target_status)
        
        return allowed
    
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
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Level basierend auf Email-Domain oder explizite Zuweisung
        if user.email == "qms.admin@company.com":
            return 5
        elif "qm" in user.email.lower() or "quality" in user.email.lower():
            return 4
        elif "team" in user.email.lower() or "lead" in user.email.lower():
            return 3
        else:
            return 2
    
    def get_user_interest_groups(self, user_id: int) -> List[int]:
        """
        Hole Interest Groups des Users.
        
        Args:
            user_id: User ID
            
        Returns:
            Liste der Interest Group IDs
        """
        memberships = self.db.query(UserGroupMembership).filter(
            UserGroupMembership.user_id == user_id
        ).all()
        
        return [membership.interest_group_id for membership in memberships]
