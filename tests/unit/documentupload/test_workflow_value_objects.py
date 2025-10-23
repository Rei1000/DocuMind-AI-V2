"""
Unit Tests für Workflow Value Objects.

Tests für WorkflowStatus und WorkflowTransition Value Objects.
"""

import pytest
from contexts.documentupload.domain.value_objects import WorkflowStatus, WorkflowTransition


class TestWorkflowStatus:
    """Tests für WorkflowStatus Enum."""
    
    def test_workflow_status_values(self):
        """Test dass alle WorkflowStatus Werte korrekt sind."""
        assert WorkflowStatus.DRAFT.value == "draft"
        assert WorkflowStatus.REVIEWED.value == "reviewed"
        assert WorkflowStatus.APPROVED.value == "approved"
        assert WorkflowStatus.REJECTED.value == "rejected"
    
    def test_workflow_status_string_conversion(self):
        """Test String-Konvertierung von WorkflowStatus."""
        status = WorkflowStatus.DRAFT
        assert status.value == "draft"
        assert status == "draft"
    
    def test_workflow_status_equality(self):
        """Test Gleichheit von WorkflowStatus."""
        assert WorkflowStatus.DRAFT == WorkflowStatus.DRAFT
        assert WorkflowStatus.DRAFT != WorkflowStatus.REVIEWED
        assert WorkflowStatus.DRAFT == "draft"


class TestWorkflowTransition:
    """Tests für WorkflowTransition Value Object."""
    
    def test_workflow_transition_creation(self):
        """Test Erstellung einer WorkflowTransition."""
        transition = WorkflowTransition(
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            required_level=3
        )
        
        assert transition.from_status == WorkflowStatus.DRAFT
        assert transition.to_status == WorkflowStatus.REVIEWED
        assert transition.required_level == 3
    
    def test_workflow_transition_validation(self):
        """Test Validierung von WorkflowTransition für verschiedene User-Level."""
        transition = WorkflowTransition(
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            required_level=3
        )
        
        # Level 3 kann die Transition durchführen
        assert transition.is_valid_for_level(3)
        assert transition.is_valid_for_level(4)
        assert transition.is_valid_for_level(5)
        
        # Level 2 kann die Transition NICHT durchführen
        assert not transition.is_valid_for_level(2)
        assert not transition.is_valid_for_level(1)
    
    def test_workflow_transition_immutability(self):
        """Test dass WorkflowTransition immutable ist."""
        transition = WorkflowTransition(
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            required_level=3
        )
        
        # Versuche Attribute zu ändern (sollte fehlschlagen)
        with pytest.raises(AttributeError):
            transition.required_level = 4
    
    def test_workflow_transition_edge_cases(self):
        """Test Edge Cases für WorkflowTransition."""
        # Level 0 (ungültig)
        transition = WorkflowTransition(
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            required_level=3
        )
        assert not transition.is_valid_for_level(0)
        
        # Sehr hohes Level
        assert transition.is_valid_for_level(999)
    
    def test_workflow_transition_different_statuses(self):
        """Test WorkflowTransition mit verschiedenen Status-Kombinationen."""
        # Draft → Reviewed (Level 3)
        draft_to_reviewed = WorkflowTransition(
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            required_level=3
        )
        assert draft_to_reviewed.is_valid_for_level(3)
        assert not draft_to_reviewed.is_valid_for_level(2)
        
        # Reviewed → Approved (Level 4)
        reviewed_to_approved = WorkflowTransition(
            from_status=WorkflowStatus.REVIEWED,
            to_status=WorkflowStatus.APPROVED,
            required_level=4
        )
        assert reviewed_to_approved.is_valid_for_level(4)
        assert not reviewed_to_approved.is_valid_for_level(3)
        
        # Reviewed → Draft (Level 4) - Rejection
        reviewed_to_draft = WorkflowTransition(
            from_status=WorkflowStatus.REVIEWED,
            to_status=WorkflowStatus.DRAFT,
            required_level=4
        )
        assert reviewed_to_draft.is_valid_for_level(4)
        assert not reviewed_to_draft.is_valid_for_level(3)
