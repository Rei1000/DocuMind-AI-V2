"""
Integration Tests für Event Handler Registration.

Test-Driven Development: RED Phase für Handler Registration.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from contexts.documentupload.infrastructure.event_publisher import InMemoryEventPublisher
from contexts.documentupload.domain.events import (
    DocumentRejectedEvent,
    DocumentDeletedEvent,
    DocumentArchivedEvent,
    DocumentVersionArchivedEvent
)
from contexts.ragintegration.application.event_handlers import (
    DocumentRejectedEventHandler,
    DocumentDeletedEventHandler,
    DocumentArchivedEventHandler,
    DocumentVersionArchivedEventHandler
)
from contexts.ragintegration.application.use_cases import RemoveDocumentFromRAGUseCase


class TestEventHandlerRegistration:
    """Tests für Event Handler Registration."""
    
    @pytest.fixture
    def mock_remove_use_case(self):
        """Mock RemoveDocumentFromRAGUseCase."""
        use_case = Mock(spec=RemoveDocumentFromRAGUseCase)
        use_case.execute = Mock(return_value={"success": True, "removed_chunks": 5})
        return use_case
    
    @pytest.fixture
    def event_publisher(self):
        """Event Publisher Instanz."""
        return InMemoryEventPublisher()
    
    @pytest.fixture
    def registered_handlers(self, event_publisher, mock_remove_use_case):
        """Registriere alle Handler."""
        # Erstelle Handler
        handler1 = DocumentRejectedEventHandler(mock_remove_use_case)
        handler2 = DocumentDeletedEventHandler(mock_remove_use_case)
        handler3 = DocumentArchivedEventHandler(mock_remove_use_case)
        handler4 = DocumentVersionArchivedEventHandler(mock_remove_use_case)
        
        # Registriere
        event_publisher.subscribe(DocumentRejectedEvent, handler1)
        event_publisher.subscribe(DocumentDeletedEvent, handler2)
        event_publisher.subscribe(DocumentArchivedEvent, handler3)
        event_publisher.subscribe(DocumentVersionArchivedEvent, handler4)
        
        return event_publisher
    
    @pytest.mark.asyncio
    async def test_document_rejected_event_triggers_rag_cleanup(self, registered_handlers, mock_remove_use_case):
        """DocumentRejectedEvent triggert RAG Cleanup"""
        # Arrange
        event = DocumentRejectedEvent(
            document_id=1,
            rejected_by_user_id=2,
            rejection_reason="Incomplete",
            timestamp=datetime.utcnow()
        )
        
        # Act
        await registered_handlers.publish(event)
        
        # Assert
        mock_remove_use_case.execute.assert_called_once_with(upload_document_id=1)
    
    @pytest.mark.asyncio
    async def test_document_deleted_event_triggers_rag_cleanup(self, registered_handlers, mock_remove_use_case):
        """DocumentDeletedEvent triggert RAG Cleanup"""
        # Arrange
        event = DocumentDeletedEvent(
            document_id=2,
            deleted_by_user_id=3,
            deletion_reason="Obsolete",
            timestamp=datetime.utcnow()
        )
        
        # Act
        await registered_handlers.publish(event)
        
        # Assert
        mock_remove_use_case.execute.assert_called_once_with(upload_document_id=2)
    
    @pytest.mark.asyncio
    async def test_document_archived_event_triggers_rag_cleanup(self, registered_handlers, mock_remove_use_case):
        """DocumentArchivedEvent triggert RAG Cleanup"""
        # Arrange
        event = DocumentArchivedEvent(
            document_id=3,
            archived_by_user_id=4,
            archive_reason="Old version",
            timestamp=datetime.utcnow()
        )
        
        # Act
        await registered_handlers.publish(event)
        
        # Assert
        mock_remove_use_case.execute.assert_called_once_with(upload_document_id=3)
    
    @pytest.mark.asyncio
    async def test_document_version_archived_event_triggers_rag_cleanup(self, registered_handlers, mock_remove_use_case):
        """DocumentVersionArchivedEvent triggert RAG Cleanup für alte Version"""
        # Arrange
        event = DocumentVersionArchivedEvent(
            old_version_id=10,
            new_version_id=11,
            document_series_id=100,
            archived_by_user_id=5,
            timestamp=datetime.utcnow()
        )
        
        # Act
        await registered_handlers.publish(event)
        
        # Assert: Sollte alte Version (old_version_id) entfernen, nicht neue
        mock_remove_use_case.execute.assert_called_once_with(upload_document_id=10)

