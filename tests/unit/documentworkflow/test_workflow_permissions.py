"""
Unit Tests für Workflow Permissions.

Testet die Berechtigungslogik für verschiedene User-Level.
"""

import pytest
from contexts.documentworkflow.domain.entities import (
    WorkflowPermissions,
    WorkflowStatus,
    DocumentWorkflow
)


class TestWorkflowPermissions:
    """Tests für WorkflowPermissions Value Object."""
    
    def test_level_1_cannot_view_documents(self):
        """Level 1 (Mitarbeiter) kann keine Dokumente sehen."""
        permissions = WorkflowPermissions(
            user_id=1,
            user_level=1,
            interest_group_ids=[1, 2]
        )
        
        # Kann keine Dokumente sehen, auch nicht in eigenen Interest Groups
        assert not permissions.can_view_document([1])
        assert not permissions.can_view_document([2])
        assert not permissions.can_view_document([1, 2])
    
    def test_level_2_can_view_own_interest_groups(self):
        """Level 2 (Teamleiter) kann nur eigene Interest Groups sehen."""
        permissions = WorkflowPermissions(
            user_id=2,
            user_level=2,
            interest_group_ids=[1, 3]
        )
        
        # Kann eigene Interest Groups sehen
        assert permissions.can_view_document([1])
        assert permissions.can_view_document([3])
        assert permissions.can_view_document([1, 3])
        
        # Kann fremde Interest Groups nicht sehen
        assert not permissions.can_view_document([2])
        assert not permissions.can_view_document([4])
        
        # Kann keine Status-Änderungen durchführen
        assert not permissions.can_change_status(WorkflowStatus.DRAFT, WorkflowStatus.REVIEWED)
    
    def test_level_3_can_review_documents(self):
        """Level 3 (Abteilungsleiter) kann Dokumente prüfen."""
        permissions = WorkflowPermissions(
            user_id=3,
            user_level=3,
            interest_group_ids=[1, 2]
        )
        
        # Kann eigene Interest Groups sehen
        assert permissions.can_view_document([1])
        assert permissions.can_view_document([2])
        
        # Kann Draft → Reviewed
        assert permissions.can_change_status(WorkflowStatus.DRAFT, WorkflowStatus.REVIEWED)
        
        # Kann Reviewed → Draft (Prüfung zurückziehen)
        assert permissions.can_change_status(WorkflowStatus.REVIEWED, WorkflowStatus.DRAFT)
        
        # Kann nicht freigeben
        assert not permissions.can_change_status(WorkflowStatus.REVIEWED, WorkflowStatus.APPROVED)
    
    def test_level_4_qm_can_approve_all(self):
        """Level 4 (QM) kann alle Dokumente freigeben."""
        permissions = WorkflowPermissions(
            user_id=4,
            user_level=4,
            interest_group_ids=[1]
        )
        
        # Ist QM
        assert permissions.is_qm
        
        # Kann alle Dokumente sehen (auch außerhalb eigener Interest Groups)
        assert permissions.can_view_document([1])
        assert permissions.can_view_document([2, 3, 4])
        assert permissions.can_view_document([])
        
        # Kann alle Status-Übergänge durchführen
        assert permissions.can_change_status(WorkflowStatus.REVIEWED, WorkflowStatus.APPROVED)
        assert permissions.can_change_status(WorkflowStatus.REVIEWED, WorkflowStatus.REJECTED)
        assert permissions.can_change_status(WorkflowStatus.DRAFT, WorkflowStatus.REJECTED)
        assert permissions.can_change_status(WorkflowStatus.APPROVED, WorkflowStatus.DRAFT)
    
    def test_level_5_admin_has_all_permissions(self):
        """Level 5 (QMS Admin) hat Sonderstatus."""
        permissions = WorkflowPermissions(
            user_id=5,
            user_level=5,
            interest_group_ids=[]
        )
        
        # Ist Admin und QM
        assert permissions.is_admin
        assert permissions.is_qm
        
        # Kann alle Dokumente sehen
        assert permissions.can_view_document([1, 2, 3, 4, 5])
        assert permissions.can_view_document([])
        
        # Kann QM-spezifische Status-Übergänge durchführen
        assert permissions.can_change_status(WorkflowStatus.REVIEWED, WorkflowStatus.APPROVED)
        assert permissions.can_change_status(WorkflowStatus.REVIEWED, WorkflowStatus.REJECTED)
        assert permissions.can_change_status(WorkflowStatus.DRAFT, WorkflowStatus.REJECTED)
        assert permissions.can_change_status(WorkflowStatus.APPROVED, WorkflowStatus.DRAFT)
    
    def test_get_allowed_transitions(self):
        """Test erlaubte Übergänge für verschiedene Level."""
        # Level 3 (Abteilungsleiter)
        permissions_l3 = WorkflowPermissions(user_id=3, user_level=3, interest_group_ids=[1])
        transitions_l3 = permissions_l3.get_allowed_transitions(WorkflowStatus.DRAFT)
        assert WorkflowStatus.REVIEWED in transitions_l3
        assert WorkflowStatus.APPROVED not in transitions_l3
        
        # Level 4 (QM)
        permissions_l4 = WorkflowPermissions(user_id=4, user_level=4, interest_group_ids=[1])
        transitions_l4 = permissions_l4.get_allowed_transitions(WorkflowStatus.REVIEWED)
        assert WorkflowStatus.APPROVED in transitions_l4
        assert WorkflowStatus.REJECTED in transitions_l4


class TestDocumentWorkflow:
    """Tests für DocumentWorkflow Entity."""
    
    def test_can_transition_to_valid_transitions(self):
        """Test erlaubte Status-Übergänge."""
        workflow = DocumentWorkflow(
            document_id=1,
            current_status=WorkflowStatus.DRAFT
        )
        
        # Level 3 kann Draft → Reviewed
        allowed, reason = workflow.can_transition_to(WorkflowStatus.REVIEWED, user_level=3)
        assert allowed
        assert "Abteilungsleiter prüft" in reason
        
        # Level 2 kann nicht Draft → Reviewed
        allowed, reason = workflow.can_transition_to(WorkflowStatus.REVIEWED, user_level=2)
        assert not allowed
        assert "Insufficient permissions" in reason
    
    def test_transition_to_success(self):
        """Test erfolgreiche Status-Transition."""
        workflow = DocumentWorkflow(
            document_id=1,
            current_status=WorkflowStatus.DRAFT
        )
        
        old_updated_at = workflow.updated_at
        
        # Führe Transition durch
        workflow.transition_to(WorkflowStatus.REVIEWED, user_level=3)
        
        assert workflow.current_status == WorkflowStatus.REVIEWED
        assert workflow.updated_at > old_updated_at
    
    def test_transition_to_invalid_fails(self):
        """Test dass ungültige Transitionen fehlschlagen."""
        workflow = DocumentWorkflow(
            document_id=1,
            current_status=WorkflowStatus.DRAFT
        )
        
        # Level 2 kann nicht Draft → Reviewed
        with pytest.raises(ValueError, match="Status transition not allowed"):
            workflow.transition_to(WorkflowStatus.REVIEWED, user_level=2)
        
        # Status bleibt unverändert
        assert workflow.current_status == WorkflowStatus.DRAFT
    
    def test_invalid_status_transition(self):
        """Test ungültiger Status-Übergang."""
        workflow = DocumentWorkflow(
            document_id=1,
            current_status=WorkflowStatus.APPROVED
        )
        
        # Approved → Reviewed ist nicht erlaubt
        allowed, reason = workflow.can_transition_to(WorkflowStatus.REVIEWED, user_level=4)
        assert not allowed
        assert "not allowed" in reason
