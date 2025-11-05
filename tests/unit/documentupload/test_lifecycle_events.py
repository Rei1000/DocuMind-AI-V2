"""
Unit Tests für Document Lifecycle Domain Events.

Test-Driven Development: RED Phase für Lifecycle Events.
"""

import pytest
from datetime import datetime

from contexts.documentupload.domain.events import (
    DocumentRejectedEvent,
    DocumentDeletedEvent,
    DocumentArchivedEvent,
    DocumentVersionArchivedEvent
)


class TestDocumentRejectedEvent:
    """Tests für DocumentRejectedEvent."""
    
    def test_document_rejected_event_creation(self):
        """DocumentRejectedEvent kann erstellt werden"""
        # Arrange & Act
        event = DocumentRejectedEvent(
            document_id=1,
            rejected_by_user_id=2,
            rejection_reason="Incomplete information",
            timestamp=datetime.utcnow()
        )
        
        # Assert
        assert event.document_id == 1
        assert event.rejected_by_user_id == 2
        assert event.rejection_reason == "Incomplete information"
        assert event.timestamp is not None


class TestDocumentDeletedEvent:
    """Tests für DocumentDeletedEvent."""
    
    def test_document_deleted_event_creation(self):
        """DocumentDeletedEvent kann erstellt werden"""
        # Arrange & Act
        event = DocumentDeletedEvent(
            document_id=1,
            deleted_by_user_id=2,
            deletion_reason="Obsolete document",
            timestamp=datetime.utcnow()
        )
        
        # Assert
        assert event.document_id == 1
        assert event.deleted_by_user_id == 2
        assert event.deletion_reason == "Obsolete document"
        assert event.timestamp is not None


class TestDocumentArchivedEvent:
    """Tests für DocumentArchivedEvent."""
    
    def test_document_archived_event_creation(self):
        """DocumentArchivedEvent kann erstellt werden"""
        # Arrange & Act
        event = DocumentArchivedEvent(
            document_id=1,
            archived_by_user_id=2,
            archive_reason="Old version replaced",
            timestamp=datetime.utcnow()
        )
        
        # Assert
        assert event.document_id == 1
        assert event.archived_by_user_id == 2
        assert event.archive_reason == "Old version replaced"
        assert event.timestamp is not None


class TestDocumentVersionArchivedEvent:
    """Tests für DocumentVersionArchivedEvent."""
    
    def test_document_version_archived_event_creation(self):
        """DocumentVersionArchivedEvent kann erstellt werden"""
        # Arrange & Act
        event = DocumentVersionArchivedEvent(
            old_version_id=1,
            new_version_id=2,
            document_series_id=10,
            archived_by_user_id=3,
            timestamp=datetime.utcnow()
        )
        
        # Assert
        assert event.old_version_id == 1
        assert event.new_version_id == 2
        assert event.document_series_id == 10
        assert event.archived_by_user_id == 3
        assert event.timestamp is not None

