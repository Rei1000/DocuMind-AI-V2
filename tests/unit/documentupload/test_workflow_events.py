"""
Unit Tests für Workflow Events

Testet DocumentWorkflowChangedEvent und Event-Serialisierung.
"""

import pytest
from datetime import datetime
from contexts.documentupload.domain.events import DocumentWorkflowChangedEvent
from contexts.documentupload.domain.value_objects import WorkflowStatus


class TestDocumentWorkflowChangedEvent:
    """Tests für DocumentWorkflowChangedEvent."""
    
    def test_create_workflow_changed_event(self):
        """Test: DocumentWorkflowChangedEvent erstellen mit allen Feldern."""
        timestamp = datetime.utcnow()
        
        event = DocumentWorkflowChangedEvent(
            document_id=123,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=456,
            reason="Teamleiter-Freigabe",
            comment="Alle Prüfpunkte erfolgreich",
            timestamp=timestamp
        )
        
        assert event.document_id == 123
        assert event.from_status == WorkflowStatus.DRAFT
        assert event.to_status == WorkflowStatus.REVIEWED
        assert event.changed_by_user_id == 456
        assert event.reason == "Teamleiter-Freigabe"
        assert event.comment == "Alle Prüfpunkte erfolgreich"
        assert event.timestamp == timestamp
    
    def test_create_workflow_changed_event_without_from_status(self):
        """Test: Event ohne from_status (Initial-Upload)."""
        timestamp = datetime.utcnow()
        
        event = DocumentWorkflowChangedEvent(
            document_id=123,
            from_status=None,
            to_status=WorkflowStatus.DRAFT,
            changed_by_user_id=456,
            reason="Initial upload",
            comment=None,
            timestamp=timestamp
        )
        
        assert event.document_id == 123
        assert event.from_status is None
        assert event.to_status == WorkflowStatus.DRAFT
        assert event.changed_by_user_id == 456
        assert event.reason == "Initial upload"
        assert event.comment is None
        assert event.timestamp == timestamp
    
    def test_create_workflow_changed_event_without_comment(self):
        """Test: Event ohne Kommentar."""
        timestamp = datetime.utcnow()
        
        event = DocumentWorkflowChangedEvent(
            document_id=123,
            from_status=WorkflowStatus.REVIEWED,
            to_status=WorkflowStatus.APPROVED,
            changed_by_user_id=789,
            reason="QM-Freigabe",
            comment=None,
            timestamp=timestamp
        )
        
        assert event.document_id == 123
        assert event.from_status == WorkflowStatus.REVIEWED
        assert event.to_status == WorkflowStatus.APPROVED
        assert event.changed_by_user_id == 789
        assert event.reason == "QM-Freigabe"
        assert event.comment is None
        assert event.timestamp == timestamp
    
    def test_event_serialization(self):
        """Test: Event kann serialisiert werden (für Event Bus)."""
        timestamp = datetime.utcnow()
        
        event = DocumentWorkflowChangedEvent(
            document_id=123,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=456,
            reason="Teamleiter-Freigabe",
            comment="Alle Prüfpunkte erfolgreich",
            timestamp=timestamp
        )
        
        # Test dass alle Felder serialisierbar sind
        event_dict = {
            'document_id': event.document_id,
            'from_status': event.from_status.value if event.from_status else None,
            'to_status': event.to_status.value,
            'changed_by_user_id': event.changed_by_user_id,
            'reason': event.reason,
            'comment': event.comment,
            'timestamp': event.timestamp.isoformat()
        }
        
        assert event_dict['document_id'] == 123
        assert event_dict['from_status'] == 'draft'
        assert event_dict['to_status'] == 'reviewed'
        assert event_dict['changed_by_user_id'] == 456
        assert event_dict['reason'] == "Teamleiter-Freigabe"
        assert event_dict['comment'] == "Alle Prüfpunkte erfolgreich"
        assert event_dict['timestamp'] == timestamp.isoformat()
    
    def test_event_string_representation(self):
        """Test: Event String-Repräsentation."""
        timestamp = datetime.utcnow()
        
        event = DocumentWorkflowChangedEvent(
            document_id=123,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=456,
            reason="Teamleiter-Freigabe",
            comment="Alle Prüfpunkte erfolgreich",
            timestamp=timestamp
        )
        
        event_str = str(event)
        assert "DocumentWorkflowChangedEvent" in event_str
        assert "123" in event_str
        assert "draft" in event_str
        assert "reviewed" in event_str
