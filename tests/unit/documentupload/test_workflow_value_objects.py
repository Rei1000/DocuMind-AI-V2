"""
Unit Tests für Workflow Value Objects

Testet WorkflowStatus Enum und WorkflowTransition Validierung.
"""

import pytest
from contexts.documentupload.domain.value_objects import WorkflowStatus, WorkflowTransition


class TestWorkflowStatus:
    """Tests für WorkflowStatus Enum."""
    
    def test_workflow_status_enum_values(self):
        """Test: WorkflowStatus hat 4 korrekte Werte."""
        assert WorkflowStatus.DRAFT == "draft"
        assert WorkflowStatus.REVIEWED == "reviewed"
        assert WorkflowStatus.APPROVED == "approved"
        assert WorkflowStatus.REJECTED == "rejected"
    
    def test_workflow_status_all_values(self):
        """Test: Alle WorkflowStatus Werte sind verfügbar."""
        expected_values = {"draft", "reviewed", "approved", "rejected"}
        actual_values = {status.value for status in WorkflowStatus}
        assert actual_values == expected_values
    
    def test_workflow_status_string_conversion(self):
        """Test: WorkflowStatus kann als String verwendet werden."""
        status = WorkflowStatus.DRAFT
        assert status.value == "draft"
        assert status == "draft"
    
    def test_workflow_status_invalid_value_raises_error(self):
        """Test: Ungültige Status-Strings werfen ValueError."""
        with pytest.raises(ValueError):
            WorkflowStatus("invalid_status")


class TestWorkflowTransition:
    """Tests für WorkflowTransition Validierung."""
    
    def test_valid_transitions_level_2(self):
        """Test: Level 2 (Mitarbeiter) - nur lesen, keine Transitions."""
        # Level 2 kann keine Status ändern
        assert not WorkflowTransition.is_valid_transition(
            WorkflowStatus.DRAFT, WorkflowStatus.REVIEWED, 2
        )
        assert not WorkflowTransition.is_valid_transition(
            WorkflowStatus.REVIEWED, WorkflowStatus.APPROVED, 2
        )
    
    def test_valid_transitions_level_3(self):
        """Test: Level 3 (Teamleiter) - nur draft → reviewed."""
        # Level 3 kann nur draft → reviewed
        assert WorkflowTransition.is_valid_transition(
            WorkflowStatus.DRAFT, WorkflowStatus.REVIEWED, 3
        )
        # Aber nicht andere Transitions
        assert not WorkflowTransition.is_valid_transition(
            WorkflowStatus.REVIEWED, WorkflowStatus.APPROVED, 3
        )
        assert not WorkflowTransition.is_valid_transition(
            WorkflowStatus.DRAFT, WorkflowStatus.APPROVED, 3
        )
    
    def test_valid_transitions_level_4(self):
        """Test: Level 4 (QM-Manager) - reviewed → approved, any → rejected."""
        # Level 4 kann reviewed → approved
        assert WorkflowTransition.is_valid_transition(
            WorkflowStatus.REVIEWED, WorkflowStatus.APPROVED, 4
        )
        # Level 4 kann any → rejected
        assert WorkflowTransition.is_valid_transition(
            WorkflowStatus.DRAFT, WorkflowStatus.REJECTED, 4
        )
        assert WorkflowTransition.is_valid_transition(
            WorkflowStatus.REVIEWED, WorkflowStatus.REJECTED, 4
        )
        assert WorkflowTransition.is_valid_transition(
            WorkflowStatus.APPROVED, WorkflowStatus.REJECTED, 4
        )
        # Aber nicht draft → approved (direkt)
        assert not WorkflowTransition.is_valid_transition(
            WorkflowStatus.DRAFT, WorkflowStatus.APPROVED, 4
        )
    
    def test_valid_transitions_level_5(self):
        """Test: Level 5 (QMS Admin) - alle Transitions erlaubt."""
        # Level 5 kann alle Transitions
        assert WorkflowTransition.is_valid_transition(
            WorkflowStatus.DRAFT, WorkflowStatus.REVIEWED, 5
        )
        assert WorkflowTransition.is_valid_transition(
            WorkflowStatus.REVIEWED, WorkflowStatus.APPROVED, 5
        )
        assert WorkflowTransition.is_valid_transition(
            WorkflowStatus.DRAFT, WorkflowStatus.APPROVED, 5
        )
        assert WorkflowTransition.is_valid_transition(
            WorkflowStatus.APPROVED, WorkflowStatus.REJECTED, 5
        )
    
    def test_invalid_user_level_raises_error(self):
        """Test: Ungültige User-Level werfen ValueError."""
        with pytest.raises(ValueError):
            WorkflowTransition.is_valid_transition(
                WorkflowStatus.DRAFT, WorkflowStatus.REVIEWED, 1
            )
        with pytest.raises(ValueError):
            WorkflowTransition.is_valid_transition(
                WorkflowStatus.DRAFT, WorkflowStatus.REVIEWED, 6
            )
    
    def test_same_status_transition_invalid(self):
        """Test: Gleicher Status → gleicher Status ist ungültig."""
        assert not WorkflowTransition.is_valid_transition(
            WorkflowStatus.DRAFT, WorkflowStatus.DRAFT, 5
        )
        assert not WorkflowTransition.is_valid_transition(
            WorkflowStatus.REVIEWED, WorkflowStatus.REVIEWED, 5
        )
    
    def test_get_allowed_transitions(self):
        """Test: get_allowed_transitions gibt korrekte Transitions zurück."""
        # Level 2: keine Transitions
        assert WorkflowTransition.get_allowed_transitions(WorkflowStatus.DRAFT, 2) == []
        
        # Level 3: nur draft → reviewed
        assert WorkflowTransition.get_allowed_transitions(WorkflowStatus.DRAFT, 3) == [WorkflowStatus.REVIEWED]
        assert WorkflowTransition.get_allowed_transitions(WorkflowStatus.REVIEWED, 3) == []
        
        # Level 4: reviewed → approved, any → rejected
        assert WorkflowTransition.get_allowed_transitions(WorkflowStatus.REVIEWED, 4) == [
            WorkflowStatus.APPROVED, WorkflowStatus.REJECTED
        ]
        assert WorkflowTransition.get_allowed_transitions(WorkflowStatus.DRAFT, 4) == [WorkflowStatus.REJECTED]
        
        # Level 5: alle Transitions (außer same-status)
        draft_transitions = WorkflowTransition.get_allowed_transitions(WorkflowStatus.DRAFT, 5)
        assert WorkflowStatus.REVIEWED in draft_transitions
        assert WorkflowStatus.APPROVED in draft_transitions
        assert WorkflowStatus.REJECTED in draft_transitions
        assert WorkflowStatus.DRAFT not in draft_transitions
