"""
Unit Tests für Soft Delete Value Objects.

Test-Driven Development: RED Phase für Soft Delete (WorkflowStatus.DELETED).
"""

import pytest
from contexts.documentupload.domain.value_objects import WorkflowStatus


class TestWorkflowStatusDeleted:
    """Tests für WorkflowStatus.DELETED."""
    
    def test_workflow_status_deleted_exists(self):
        """WorkflowStatus.DELETED sollte existieren"""
        # Arrange & Act & Assert
        assert hasattr(WorkflowStatus, 'DELETED')
        assert WorkflowStatus.DELETED.value == "deleted"
    
    def test_workflow_status_deleted_value(self):
        """WorkflowStatus.DELETED sollte den Wert 'deleted' haben"""
        # Arrange & Act
        status = WorkflowStatus.DELETED
        
        # Assert
        assert status.value == "deleted"
        assert str(status.value) == "deleted"
    
    def test_workflow_status_all_statuses(self):
        """Alle Workflow-Status sollten enthalten sein (inklusive DELETED)"""
        # Arrange & Act
        all_statuses = [status.value for status in WorkflowStatus]
        
        # Assert
        assert "draft" in all_statuses
        assert "reviewed" in all_statuses
        assert "approved" in all_statuses
        assert "rejected" in all_statuses
        assert "deleted" in all_statuses  # NEU Phase 1.3

