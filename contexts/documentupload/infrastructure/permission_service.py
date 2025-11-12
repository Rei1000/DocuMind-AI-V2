"""
Workflow Permission Service Implementation.

Implementiert Level-basierte Berechtigungen für Workflow-Status-Änderungen.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..application.ports import WorkflowPermissionService
from ..domain.value_objects import WorkflowStatus
from backend.app.models import User, UserGroupMembership, InterestGroup


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
            WorkflowStatus.APPROVED: 4,  # Level 4+ (QM) - Direkte Freigabe möglich
        },
        WorkflowStatus.REVIEWED: {
            WorkflowStatus.APPROVED: 4,  # Level 4+ (QM)
            WorkflowStatus.REJECTED: 4,  # Level 4+ (QM)
        },
        WorkflowStatus.APPROVED: {
            WorkflowStatus.REJECTED: 4,  # Level 4+ (QM) - NEU: Approved → Rejected für Validierung/Fehlerkorrektur
        },
        WorkflowStatus.REJECTED: {
            WorkflowStatus.DRAFT: 3,  # Level 3+ (Abteilungsleiter)
        },
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_level(self, user_id: int) -> int:
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
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return 0
        
        if user.is_qms_admin:
            return 5
        
        # Hole höchstes approval_level aus UserGroupMembership (nur aktive!)
        membership = (
            self.db.query(UserGroupMembership)
            .filter(
                UserGroupMembership.user_id == user_id,
                UserGroupMembership.is_active == True
            )
            .order_by(UserGroupMembership.approval_level.desc())
            .first()
        )
        
        if membership:
            return membership.approval_level
        
        return 0  # Kein Zugriff
    
    def can_change_status(
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
        user_level = self.get_user_level(user_id)
        required_level = self.WORKFLOW_RULES.get(from_status, {}).get(to_status)
        
        if required_level is None:
            return False  # Ungültige Transition
        
        return user_level >= required_level
    
    def get_allowed_transitions(
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
        user_level = self.get_user_level(user_id)
        allowed_transitions = []
        
        for to_status, required_level in self.WORKFLOW_RULES.get(current_status, {}).items():
            if user_level >= required_level:
                allowed_transitions.append(to_status)
        
        return allowed_transitions
    
    def get_user_interest_groups(self, user_id: int) -> List[int]:
        """
        Hole Interest Groups eines Users.
        
        RBAC-Logik:
        - Level 4-5: Leere Liste = Alle Interest Groups (keine Filterung)
        - Level 1-3: Nur eigene Interest Groups aus aktiven Memberships
        
        Args:
            user_id: User ID
            
        Returns:
            Liste der Interest Group IDs (leere Liste = alle IG)
        """
        user_level = self.get_user_level(user_id)
        
        # Level 4+ (QM Mitarbeiter, QMS Admin): Alle Interest Groups
        if user_level >= 4:
            return []  # Leere Liste = keine Filterung = alle IG
        
        # Level 1-3: Nur eigene Interest Groups aus aktiven Memberships
        memberships = (
            self.db.query(UserGroupMembership)
            .filter(
                UserGroupMembership.user_id == user_id,
                UserGroupMembership.is_active == True
            )
            .all()
        )
        
        # Extrahiere Interest Group IDs
        interest_group_ids = [m.interest_group_id for m in memberships]
        
        return interest_group_ids
    
    def get_user_interest_groups_with_levels(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Hole Interest Groups mit deren Approval Levels.
        
        RBAC Multi-Level Support:
        - Level 4-5: Leere Liste = Alle Interest Groups (keine Filterung)
        - Level 1-3: Nur eigene Interest Groups aus aktiven Memberships mit Levels
        
        Returns:
            Liste von Dictionaries mit:
            {
                "interest_group_id": int,
                "approval_level": int,
                "interest_group_name": str
            }
            Oder leere Liste [] für Level 4-5 (alle IG)
        
        Args:
            user_id: User ID
            
        Returns:
            Liste der Interest Groups mit Levels (leere Liste = alle IG)
        """
        user_level = self.get_user_level(user_id)
        
        # Level 4+ (QM Mitarbeiter, QMS Admin): Alle IG (keine Filterung)
        if user_level >= 4:
            return []  # Leere Liste = alle IG
        
        # Level 1-3: Nur eigene Interest Groups aus aktiven Memberships
        memberships = (
            self.db.query(UserGroupMembership, InterestGroup)
            .join(InterestGroup, UserGroupMembership.interest_group_id == InterestGroup.id)
            .filter(
                UserGroupMembership.user_id == user_id,
                UserGroupMembership.is_active == True
            )
            .order_by(UserGroupMembership.approval_level.desc())  # Höchstes Level zuerst
            .all()
        )
        
        return [
            {
                "interest_group_id": m.interest_group_id,
                "approval_level": m.approval_level,
                "interest_group_name": ig.name
            }
            for m, ig in memberships
        ]
    
    def can_perform_action_on_document(
        self,
        user_id: int,
        document_interest_group_ids: List[int],
        action: str,
        required_level: int
    ) -> bool:
        """
        Prüfe ob User Aktion für Dokument mit bestimmten IGs ausführen darf.
        
        Context-Specific Permission Check (RBAC Multi-Level):
        - Level 4-5: Immer True (Vollzugriff) - WICHTIG: Auch wenn Dokument keine IGs hat!
        - Level 1-3: Prüfe ob User mindestens eine IG des Dokuments mit Level >= required_level hat
        
        Beispiel:
            User: Level 3 (Produktion), Level 2 (Service)
            Dokument: Produktion (IG-ID: 1)
            Aktion: view_kanban (required_level: 3)
            → True (User hat Level 3 für Produktion)
            
            User: Level 3 (Produktion), Level 2 (Service)
            Dokument: Service (IG-ID: 2)
            Aktion: view_kanban (required_level: 3)
            → False (User hat nur Level 2 für Service)
        
        Args:
            user_id: User ID
            document_interest_group_ids: Interest Groups des Dokuments (kann leer sein!)
            action: Aktion (zur Dokumentation, z.B. "view_kanban", "change_status_draft_to_reviewed")
            required_level: Benötigtes Level für Aktion
        
        Returns:
            True wenn berechtigt, False sonst
        """
        user_level = self.get_user_level(user_id)
        
        # Level 4+ (QM, QMS Admin): Immer berechtigt (auch wenn Dokument keine IGs hat!)
        # WICHTIG: Level 4+ haben Vollzugriff auf alle Dokumente, unabhängig von IGs
        if user_level >= 4:
            return True
        
        # Level 1-3: Prüfe IG-Level
        user_igs_with_levels = self.get_user_interest_groups_with_levels(user_id)
        
        # Erstelle Mapping: IG-ID → Level
        user_ig_level_map = {
            ig["interest_group_id"]: ig["approval_level"]
            for ig in user_igs_with_levels
        }
        
        # Prüfe ob User für mindestens eine IG des Dokuments das required_level hat
        for doc_ig_id in document_interest_group_ids:
            user_level_for_ig = user_ig_level_map.get(doc_ig_id, 0)
            if user_level_for_ig >= required_level:
                return True
        
        # User hat für keine IG des Dokuments das required_level
        return False
