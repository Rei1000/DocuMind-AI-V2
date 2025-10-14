"""
Document Workflow Domain Entities.

Zentrale Geschäftslogik für Document Workflow Management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class WorkflowStatus(Enum):
    """Document Workflow Status."""
    DRAFT = "draft"           # Initial nach Upload
    IN_REVIEW = "in_review"   # Zur Prüfung (veraltet - nicht mehr verwendet)
    REVIEWED = "reviewed"     # Geprüft (Abteilungsleiter)
    APPROVED = "approved"     # Freigegeben (QM)
    REJECTED = "rejected"     # Zurückgewiesen


class CommentType(Enum):
    """Types of comments."""
    GENERAL = "general"
    REVIEW = "review"
    REJECTION = "rejection"
    APPROVAL = "approval"


@dataclass
class StatusTransition:
    """
    Erlaubte Status-Übergänge mit Rollen-Requirements.
    
    Definiert welche Rollen welche Status-Änderungen durchführen dürfen.
    """
    from_status: WorkflowStatus
    to_status: WorkflowStatus
    required_level: int  # Minimum User Level
    description: str


# Definiere erlaubte Übergänge
ALLOWED_TRANSITIONS = [
    # Von Draft
    StatusTransition(WorkflowStatus.DRAFT, WorkflowStatus.REVIEWED, 3, 
                    "Abteilungsleiter prüft Dokument"),
    StatusTransition(WorkflowStatus.DRAFT, WorkflowStatus.REJECTED, 4, 
                    "QM weist direkt zurück"),
    
    # Von Reviewed  
    StatusTransition(WorkflowStatus.REVIEWED, WorkflowStatus.APPROVED, 4, 
                    "QM gibt frei"),
    StatusTransition(WorkflowStatus.REVIEWED, WorkflowStatus.REJECTED, 4, 
                    "QM weist zurück"),
    StatusTransition(WorkflowStatus.REVIEWED, WorkflowStatus.DRAFT, 3, 
                    "Abteilungsleiter zieht Prüfung zurück"),
    
    # Von Rejected zurück zu Draft
    StatusTransition(WorkflowStatus.REJECTED, WorkflowStatus.DRAFT, 4, 
                    "QM setzt auf Draft zurück"),
    
    # Von Approved (normalerweise keine Änderung, aber QM kann)
    StatusTransition(WorkflowStatus.APPROVED, WorkflowStatus.DRAFT, 4, 
                    "QM hebt Freigabe auf"),
]


@dataclass
class DocumentWorkflow:
    """
    Aggregate Root: Document Workflow.
    
    Verwaltet den Workflow-Status eines Dokuments und
    stellt sicher, dass nur erlaubte Übergänge stattfinden.
    """
    id: Optional[int] = None
    document_id: int = 0
    current_status: WorkflowStatus = WorkflowStatus.DRAFT
    
    # Audit Information
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def can_transition_to(self, new_status: WorkflowStatus, user_level: int) -> tuple[bool, str]:
        """
        Prüft ob ein Status-Übergang erlaubt ist.
        
        Args:
            new_status: Ziel-Status
            user_level: Level des Users (1-4)
            
        Returns:
            (allowed, reason): Tupel mit bool und Begründung
        """
        # Keine Änderung = immer erlaubt
        if self.current_status == new_status:
            return True, "Status unchanged"
        
        # Suche erlaubten Übergang
        for transition in ALLOWED_TRANSITIONS:
            if (transition.from_status == self.current_status and 
                transition.to_status == new_status):
                
                # Prüfe User Level
                if user_level >= transition.required_level:
                    return True, transition.description
                else:
                    return False, f"Insufficient permissions. Required level: {transition.required_level}"
        
        # Kein erlaubter Übergang gefunden
        return False, f"Transition from {self.current_status.value} to {new_status.value} not allowed"
    
    def transition_to(self, new_status: WorkflowStatus, user_level: int) -> None:
        """
        Führt Status-Übergang durch.
        
        Args:
            new_status: Ziel-Status
            user_level: Level des Users
            
        Raises:
            ValueError: Wenn Übergang nicht erlaubt
        """
        allowed, reason = self.can_transition_to(new_status, user_level)
        if not allowed:
            raise ValueError(f"Status transition not allowed: {reason}")
        
        self.current_status = new_status
        self.updated_at = datetime.utcnow()


@dataclass
class StatusChange:
    """
    Value Object: Status Change Event.
    
    Dokumentiert eine Status-Änderung für Audit Trail.
    """
    id: Optional[int] = None
    document_id: int = 0
    from_status: Optional[WorkflowStatus] = None
    to_status: WorkflowStatus = WorkflowStatus.DRAFT
    changed_by_user_id: int = 0
    changed_at: datetime = field(default_factory=datetime.utcnow)
    change_reason: Optional[str] = None
    comment: Optional[str] = None


@dataclass  
class DocumentComment:
    """
    Entity: Document Comment.
    
    Kommentar zu einem Dokument mit optionalem Seitenbezug.
    """
    id: Optional[int] = None
    document_id: int = 0
    comment_text: str = ""
    comment_type: CommentType = CommentType.GENERAL
    page_number: Optional[int] = None
    created_by_user_id: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    status_change_id: Optional[int] = None
    
    def validate(self) -> bool:
        """Validiert den Kommentar."""
        if not self.comment_text.strip():
            raise ValueError("Comment text cannot be empty")
        
        if self.page_number is not None and self.page_number < 1:
            raise ValueError("Page number must be positive")
        
        return True


@dataclass
class WorkflowPermissions:
    """
    Value Object: User Permissions for Workflow.
    
    Kapselt die Logik für Berechtigungen basierend auf User Level
    und Interest Group Zugehörigkeit.
    """
    user_id: int
    user_level: int  # 1-4
    interest_group_ids: List[int]
    is_qm: bool = False  # Level 4
    
    def __post_init__(self):
        self.is_qm = self.user_level >= 4
    
    def can_view_document(self, document_interest_groups: List[int]) -> bool:
        """Kann User das Dokument sehen?"""
        # Level 1 kann keine Dokumente sehen
        if self.user_level < 2:
            return False
        
        # QM kann alle Dokumente sehen  
        if self.is_qm:
            return True
        
        # Andere nur wenn in gleicher Interest Group
        return any(ig in self.interest_group_ids for ig in document_interest_groups)
    
    def can_change_status(self, from_status: WorkflowStatus, to_status: WorkflowStatus) -> bool:
        """Kann User diesen Status-Übergang durchführen?"""
        for transition in ALLOWED_TRANSITIONS:
            if (transition.from_status == from_status and 
                transition.to_status == to_status):
                return self.user_level >= transition.required_level
        return False
    
    def get_allowed_transitions(self, current_status: WorkflowStatus) -> List[WorkflowStatus]:
        """Welche Status-Übergänge sind für diesen User möglich?"""
        allowed = []
        for transition in ALLOWED_TRANSITIONS:
            if (transition.from_status == current_status and 
                self.user_level >= transition.required_level):
                allowed.append(transition.to_status)
        return allowed
