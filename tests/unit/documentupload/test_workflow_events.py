"""
Unit Tests für Workflow Domain Events.

Tests für DocumentWorkflowChangedEvent.
"""

import pytest
from datetime import datetime
from contexts.documentupload.domain.events import DocumentWorkflowChangedEvent
from contexts.documentupload.domain.value_objects import WorkflowStatus


class TestDocumentWorkflowChangedEvent:
    """Tests für DocumentWorkflowChangedEvent."""
    
    def test_document_workflow_changed_event_creation(self):
        """Test Erstellung eines DocumentWorkflowChangedEvent."""
        event = DocumentWorkflowChangedEvent(
            document_id=1,
            old_status=WorkflowStatus.DRAFT,
            new_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=1,
            reason="Reviewed successfully"
        )
        
        assert event.document_id == 1
        assert event.old_status == WorkflowStatus.DRAFT
        assert event.new_status == WorkflowStatus.REVIEWED
        assert event.changed_by_user_id == 1
        assert event.reason == "Reviewed successfully"
        assert isinstance(event.timestamp, datetime)
    
    def test_document_workflow_changed_event_immutability(self):
        """Test dass DocumentWorkflowChangedEvent immutable ist."""
        event = DocumentWorkflowChangedEvent(
            document_id=1,
            old_status=WorkflowStatus.DRAFT,
            new_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=1,
            reason="Reviewed successfully"
        )
        
        # Versuche Attribute zu ändern (sollte fehlschlagen)
        with pytest.raises(AttributeError):
            event.document_id = 2
        
        with pytest.raises(AttributeError):
            event.old_status = WorkflowStatus.APPROVED
    
    def test_document_workflow_changed_event_validation(self):
        """Test Validierung von DocumentWorkflowChangedEvent."""
        # Gültige Werte
        event = DocumentWorkflowChangedEvent(
            document_id=1,
            old_status=WorkflowStatus.DRAFT,
            new_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=1,
            reason="Valid reason"
        )
        assert event.document_id == 1
        
        # Ungültige document_id
        with pytest.raises(ValueError):
            DocumentWorkflowChangedEvent(
                document_id=0,  # Ungültig
                old_status=WorkflowStatus.DRAFT,
                new_status=WorkflowStatus.REVIEWED,
                changed_by_user_id=1,
                reason="Test"
            )
        
        # Ungültige user_id
        with pytest.raises(ValueError):
            DocumentWorkflowChangedEvent(
                document_id=1,
                old_status=WorkflowStatus.DRAFT,
                new_status=WorkflowStatus.REVIEWED,
                changed_by_user_id=0,  # Ungültig
                reason="Test"
            )
        
        # Leerer Grund
        with pytest.raises(ValueError):
            DocumentWorkflowChangedEvent(
                document_id=1,
                old_status=WorkflowStatus.DRAFT,
                new_status=WorkflowStatus.REVIEWED,
                changed_by_user_id=1,
                reason=""  # Leer
            )
    
    def test_document_workflow_changed_event_timestamp(self):
        """Test Timestamp-Verhalten von DocumentWorkflowChangedEvent."""
        before = datetime.utcnow()
        
        event = DocumentWorkflowChangedEvent(
            document_id=1,
            old_status=WorkflowStatus.DRAFT,
            new_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=1,
            reason="Test"
        )
        
        after = datetime.utcnow()
        
        # Timestamp sollte zwischen before und after liegen
        assert before <= event.timestamp <= after
    
    def test_document_workflow_changed_event_equality(self):
        """Test Gleichheit von DocumentWorkflowChangedEvent."""
        event1 = DocumentWorkflowChangedEvent(
            document_id=1,
            old_status=WorkflowStatus.DRAFT,
            new_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=1,
            reason="Test"
        )
        
        event2 = DocumentWorkflowChangedEvent(
            document_id=1,
            old_status=WorkflowStatus.DRAFT,
            new_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=1,
            reason="Test"
        )
        
        # Events mit gleichen Werten sollten gleich sein
        # (außer timestamp, das wird ignoriert)
        assert event1.document_id == event2.document_id
        assert event1.old_status == event2.old_status
        assert event1.new_status == event2.new_status
        assert event1.changed_by_user_id == event2.changed_by_user_id
        assert event1.reason == event2.reason
    
    def test_document_workflow_changed_event_different_statuses(self):
        """Test DocumentWorkflowChangedEvent mit verschiedenen Status-Kombinationen."""
        # Draft → Reviewed
        draft_to_reviewed = DocumentWorkflowChangedEvent(
            document_id=1,
            old_status=WorkflowStatus.DRAFT,
            new_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=2,
            reason="Reviewed by level 3 user"
        )
        assert draft_to_reviewed.old_status == WorkflowStatus.DRAFT
        assert draft_to_reviewed.new_status == WorkflowStatus.REVIEWED
        
        # Reviewed → Approved
        reviewed_to_approved = DocumentWorkflowChangedEvent(
            document_id=1,
            old_status=WorkflowStatus.REVIEWED,
            new_status=WorkflowStatus.APPROVED,
            changed_by_user_id=1,
            reason="Approved by admin"
        )
        assert reviewed_to_approved.old_status == WorkflowStatus.REVIEWED
        assert reviewed_to_approved.new_status == WorkflowStatus.APPROVED
        
        # Reviewed → Draft (Rejection)
        reviewed_to_draft = DocumentWorkflowChangedEvent(
            document_id=1,
            old_status=WorkflowStatus.REVIEWED,
            new_status=WorkflowStatus.DRAFT,
            changed_by_user_id=1,
            reason="Rejected, needs revision"
        )
        assert reviewed_to_draft.old_status == WorkflowStatus.REVIEWED
        assert reviewed_to_draft.new_status == WorkflowStatus.DRAFT
    
    def test_document_workflow_changed_event_edge_cases(self):
        """Test Edge Cases für DocumentWorkflowChangedEvent."""
        # Sehr langer Grund
        long_reason = "A" * 1000
        event = DocumentWorkflowChangedEvent(
            document_id=1,
            old_status=WorkflowStatus.DRAFT,
            new_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=1,
            reason=long_reason
        )
        assert event.reason == long_reason
        
        # Spezielle Zeichen im Grund
        special_reason = "Status changed: Draft → Reviewed (Level 3) ✅"
        event = DocumentWorkflowChangedEvent(
            document_id=1,
            old_status=WorkflowStatus.DRAFT,
            new_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=1,
            reason=special_reason
        )
        assert event.reason == special_reason
