"""
Unit Tests für Document Lifecycle Event Handler.

Test-Driven Development: RED Phase für Event Handler.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from contexts.ragintegration.application.event_handlers import (
    DocumentRejectedEventHandler,
    DocumentDeletedEventHandler,
    DocumentArchivedEventHandler,
    DocumentVersionArchivedEventHandler
)
from contexts.documentupload.domain.events import (
    DocumentRejectedEvent,
    DocumentDeletedEvent,
    DocumentArchivedEvent,
    DocumentVersionArchivedEvent
)
from contexts.ragintegration.application.use_cases import RemoveDocumentFromRAGUseCase


class TestDocumentRejectedEventHandler:
    """Tests für DocumentRejectedEventHandler."""
    
    @pytest.fixture
    def mock_remove_use_case(self):
        """Mock RemoveDocumentFromRAGUseCase."""
        return Mock(spec=RemoveDocumentFromRAGUseCase)
    
    @pytest.fixture
    def handler(self, mock_remove_use_case):
        """DocumentRejectedEventHandler mit Mock."""
        return DocumentRejectedEventHandler(remove_document_use_case=mock_remove_use_case)
    
    @pytest.mark.asyncio
    async def test_handle_calls_remove_document_use_case(self, handler, mock_remove_use_case):
        """Handler ruft RemoveDocumentFromRAGUseCase auf"""
        # Arrange
        event = DocumentRejectedEvent(
            document_id=1,
            rejected_by_user_id=2,
            rejection_reason="Incomplete information",
            timestamp=datetime.utcnow()
        )
        mock_remove_use_case.execute = Mock(return_value={"success": True, "removed_chunks": 5})
        
        # Act
        await handler.handle(event)
        
        # Assert
        mock_remove_use_case.execute.assert_called_once_with(upload_document_id=1)


class TestDocumentDeletedEventHandler:
    """Tests für DocumentDeletedEventHandler."""
    
    @pytest.fixture
    def mock_remove_use_case(self):
        """Mock RemoveDocumentFromRAGUseCase."""
        return Mock(spec=RemoveDocumentFromRAGUseCase)
    
    @pytest.fixture
    def handler(self, mock_remove_use_case):
        """DocumentDeletedEventHandler mit Mock."""
        return DocumentDeletedEventHandler(remove_document_use_case=mock_remove_use_case)
    
    @pytest.mark.asyncio
    async def test_handle_calls_remove_document_use_case(self, handler, mock_remove_use_case):
        """Handler ruft RemoveDocumentFromRAGUseCase auf"""
        # Arrange
        event = DocumentDeletedEvent(
            document_id=1,
            deleted_by_user_id=2,
            deletion_reason="Obsolete document",
            timestamp=datetime.utcnow()
        )
        mock_remove_use_case.execute = Mock(return_value={"success": True, "removed_chunks": 3})
        
        # Act
        await handler.handle(event)
        
        # Assert
        mock_remove_use_case.execute.assert_called_once_with(upload_document_id=1)


class TestDocumentArchivedEventHandler:
    """Tests für DocumentArchivedEventHandler."""
    
    @pytest.fixture
    def mock_remove_use_case(self):
        """Mock RemoveDocumentFromRAGUseCase."""
        return Mock(spec=RemoveDocumentFromRAGUseCase)
    
    @pytest.fixture
    def handler(self, mock_remove_use_case):
        """DocumentArchivedEventHandler mit Mock."""
        return DocumentArchivedEventHandler(remove_document_use_case=mock_remove_use_case)
    
    @pytest.mark.asyncio
    async def test_handle_calls_remove_document_use_case(self, handler, mock_remove_use_case):
        """Handler ruft RemoveDocumentFromRAGUseCase auf"""
        # Arrange
        event = DocumentArchivedEvent(
            document_id=1,
            archived_by_user_id=2,
            archive_reason="Old version replaced",
            timestamp=datetime.utcnow()
        )
        mock_remove_use_case.execute = Mock(return_value={"success": True, "removed_chunks": 8})
        
        # Act
        await handler.handle(event)
        
        # Assert
        mock_remove_use_case.execute.assert_called_once_with(upload_document_id=1)


class TestDocumentVersionArchivedEventHandler:
    """Tests für DocumentVersionArchivedEventHandler."""
    
    @pytest.fixture
    def mock_remove_use_case(self):
        """Mock RemoveDocumentFromRAGUseCase."""
        return Mock(spec=RemoveDocumentFromRAGUseCase)
    
    @pytest.fixture
    def handler(self, mock_remove_use_case):
        """DocumentVersionArchivedEventHandler mit Mock."""
        return DocumentVersionArchivedEventHandler(remove_document_use_case=mock_remove_use_case)
    
    @pytest.mark.asyncio
    async def test_handle_calls_remove_document_use_case_for_old_version(self, handler, mock_remove_use_case):
        """Handler ruft RemoveDocumentFromRAGUseCase für alte Version auf"""
        # Arrange
        event = DocumentVersionArchivedEvent(
            old_version_id=1,
            new_version_id=2,
            document_series_id=10,
            archived_by_user_id=3,
            timestamp=datetime.utcnow()
        )
        mock_remove_use_case.execute = Mock(return_value={"success": True, "removed_chunks": 12})
        
        # Act
        await handler.handle(event)
        
        # Assert: Sollte alte Version (old_version_id) entfernen, nicht neue
        mock_remove_use_case.execute.assert_called_once_with(upload_document_id=1)

