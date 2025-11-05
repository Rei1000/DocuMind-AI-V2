"""
Unit Tests für Archive Value Objects.

Test-Driven Development: RED Phase für WorkflowStatus.ARCHIVED.
"""

import pytest
from contexts.documentupload.domain.value_objects import WorkflowStatus


class TestWorkflowStatusArchived:
    """Tests für WorkflowStatus.ARCHIVED."""
    
    def test_workflow_status_archived_exists(self):
        """WorkflowStatus.ARCHIVED sollte existieren"""
        # Arrange & Act & Assert
        assert hasattr(WorkflowStatus, 'ARCHIVED')
        assert WorkflowStatus.ARCHIVED.value == "archived"
    
    def test_workflow_status_archived_value(self):
        """WorkflowStatus.ARCHIVED sollte den Wert 'archived' haben"""
        # Arrange & Act
        status = WorkflowStatus.ARCHIVED
        
        # Assert
        assert status.value == "archived"
        assert str(status.value) == "archived"
    
    def test_workflow_status_all_statuses_includes_archived(self):
        """Alle Workflow-Status sollten enthalten sein (inklusive ARCHIVED)"""
        # Arrange & Act
        all_statuses = [status.value for status in WorkflowStatus]
        
        # Assert
        assert "draft" in all_statuses
        assert "reviewed" in all_statuses
        assert "approved" in all_statuses
        assert "rejected" in all_statuses
        assert "deleted" in all_statuses
        assert "archived" in all_statuses  # NEU Phase 1.4

