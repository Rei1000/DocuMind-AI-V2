"""
Unit Tests für Event Publishing in SoftDeleteDocumentUseCase.

Test-Driven Development: RED Phase für Event Publishing.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from contexts.documentupload.application.use_cases import SoftDeleteDocumentUseCase
from contexts.documentupload.domain.entities import UploadedDocument
from contexts.documentupload.domain.value_objects import (
    FileType, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus,
    WorkflowStatus
)
from contexts.documentupload.domain.events import DocumentDeletedEvent
from contexts.documentupload.domain.repositories import UploadRepository


class TestSoftDeleteDocumentUseCaseEventPublishing:
    """Tests für Event Publishing in SoftDeleteDocumentUseCase."""
    
    @pytest.fixture
    def mock_upload_repo(self):
        """Mock UploadRepository."""
        return Mock(spec=UploadRepository)
    
    @pytest.fixture
    def mock_event_publisher(self):
        """Mock EventPublisher."""
        return Mock()
    
    @pytest.fixture
    def use_case(self, mock_upload_repo, mock_event_publisher):
        """SoftDeleteDocumentUseCase mit Event Publisher."""
        return SoftDeleteDocumentUseCase(
            upload_repository=mock_upload_repo,
            event_publisher=mock_event_publisher
        )
    
    @pytest.mark.asyncio
    async def test_soft_delete_publishes_document_deleted_event(self, use_case, mock_upload_repo, mock_event_publisher):
        """SoftDelete publiziert DocumentDeletedEvent"""
        # Arrange
        document = UploadedDocument(
            id=1,
            file_type=FileType.PDF,
            file_size_bytes=1024,
            document_type_id=1,
            metadata=DocumentMetadata(
                filename="test.pdf",
                original_filename="test.pdf",
                qm_chapter="1.2",
                version="v1.0"
            ),
            file_path=FilePath("data/uploads/test.pdf"),
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.COMPLETED,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            workflow_status=WorkflowStatus.APPROVED
        )
        mock_upload_repo.get_by_id = AsyncMock(return_value=document)
        mock_upload_repo.save = AsyncMock(return_value=document)
        mock_event_publisher.publish = AsyncMock()
        
        # Act
        await use_case.execute(
            document_id=1,
            deleted_by_user_id=2,
            reason="Obsolete document"
        )
        
        # Assert: Event sollte publiziert werden
        assert mock_event_publisher.publish.called
        published_event = mock_event_publisher.publish.call_args[0][0]
        assert isinstance(published_event, DocumentDeletedEvent)
        assert published_event.document_id == 1
        assert published_event.deleted_by_user_id == 2
        assert published_event.deletion_reason == "Obsolete document"
    
    @pytest.mark.asyncio
    async def test_soft_delete_without_event_publisher_works(self, mock_upload_repo):
        """SoftDelete funktioniert auch ohne Event Publisher (optional)"""
        # Arrange
        use_case = SoftDeleteDocumentUseCase(
            upload_repository=mock_upload_repo,
            event_publisher=None  # Optional
        )
        document = UploadedDocument(
            id=1,
            file_type=FileType.PDF,
            file_size_bytes=1024,
            document_type_id=1,
            metadata=DocumentMetadata(
                filename="test.pdf",
                original_filename="test.pdf",
                qm_chapter="1.2",
                version="v1.0"
            ),
            file_path=FilePath("data/uploads/test.pdf"),
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.COMPLETED,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            workflow_status=WorkflowStatus.APPROVED
        )
        mock_upload_repo.get_by_id = AsyncMock(return_value=document)
        mock_upload_repo.save = AsyncMock(return_value=document)
        
        # Act & Assert: Sollte ohne Fehler funktionieren
        result = await use_case.execute(
            document_id=1,
            deleted_by_user_id=2,
            reason="Obsolete document"
        )
        
        assert result.workflow_status == WorkflowStatus.DELETED

