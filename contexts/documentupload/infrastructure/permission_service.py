"""
Workflow Permission Service Implementation.

Implementiert Level-basierte Berechtigungen für Workflow-Status-Änderungen.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..application.ports import WorkflowPermissionService
from ..domain.value_objects import WorkflowStatus
from backend.app.models import User, UserGroupMembership


class SQLAlchemyWorkflowPermissionService:
    """
    Workflow Permission Service Implementation.
    
    User Level Mapping:
    - Level 5: QMS Admin (is_qms_admin=True)
    - Level 1-4: UserGroupMembership.approval_level
    - Level 0: Kein Zugriff
    
    Workflow Rules:
    - draft → reviewed: Level 3+ (Abteilungsleiter)
    - reviewed → approved: Level 4+ (QM)
    - reviewed → rejected: Level 4+ (QM)
    - rejected → draft: Level 3+ (Abteilungsleiter)
    """
    
    WORKFLOW_RULES = {
        WorkflowStatus.DRAFT: {
            WorkflowStatus.REVIEWED: 3,  # Level 3+ (Abteilungsleiter)
        },
        WorkflowStatus.REVIEWED: {
            WorkflowStatus.APPROVED: 4,  # Level 4+ (QM)
            WorkflowStatus.REJECTED: 4,  # Level 4+ (QM)
        },
        WorkflowStatus.REJECTED: {
            WorkflowStatus.DRAFT: 3,  # Level 3+ (Abteilungsleiter)
        },
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_level(self, user_id: int) -> int:
        """
        Hole User Level aus DB.
        
        Args:
            user_id: User ID
            
        Returns:
            5: QMS Admin
            1-4: approval_level aus UserGroupMembership
            0: Kein Zugriff
        """
        # Prüfe QMS Admin
        user_query = select(User).where(User.id == user_id)
        result = await self.db.execute(user_query)
        user = await result.scalar_one_or_none()
        
        if not user:
            return 0
        
        if user.is_qms_admin:
            return 5
        
        # Hole höchstes approval_level aus UserGroupMembership
        membership_query = (
            select(UserGroupMembership)
            .where(UserGroupMembership.user_id == user_id)
            .order_by(UserGroupMembership.approval_level.desc())
        )
        result = await self.db.execute(membership_query)
        membership = await result.scalar_one_or_none()
        
        if membership:
            return membership.approval_level
        
        return 0  # Kein Zugriff
    
    async def can_change_status(
        self,
        user_id: int,
        from_status: WorkflowStatus,
        to_status: WorkflowStatus
    ) -> bool:
        """
        Prüfe ob User Berechtigung für Status-Änderung hat.
        
        Args:
            user_id: User ID
            from_status: Aktueller Status
            to_status: Zielstatus
            
        Returns:
            True wenn berechtigt, False sonst
        """
        user_level = await self.get_user_level(user_id)
        required_level = self.WORKFLOW_RULES.get(from_status, {}).get(to_status)
        
        if required_level is None:
            return False  # Ungültige Transition
        
        return user_level >= required_level
    
    async def get_allowed_transitions(
        self,
        user_id: int,
        current_status: WorkflowStatus
    ) -> List[WorkflowStatus]:
        """
        Hole erlaubte Transitions für User.
        
        Args:
            user_id: User ID
            current_status: Aktueller Status
            
        Returns:
            Liste der erlaubten Ziel-Status
        """
        user_level = await self.get_user_level(user_id)
        allowed_transitions = []
        
        for to_status, required_level in self.WORKFLOW_RULES.get(current_status, {}).items():
            if user_level >= required_level:
                allowed_transitions.append(to_status)
        
        return allowed_transitions
    
    async def get_user_interest_groups(self, user_id: int) -> List[int]:
        """
        Hole Interest Groups eines Users.
        
        Args:
            user_id: User ID
            
        Returns:
            Liste der Interest Group IDs
        """
        # TODO: Implementierung wenn Interest Groups benötigt
        # Für jetzt: Alle Users sehen alle Dokumente (Level 4+)
        user_level = await self.get_user_level(user_id)
        if user_level >= 4:
            return []  # Alle Interest Groups
        
        # Für Level 2-3: Nur eigene Interest Groups
        # TODO: Implementierung basierend auf UserGroupMembership
        return []
