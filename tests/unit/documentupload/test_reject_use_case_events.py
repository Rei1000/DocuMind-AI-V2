"""
Unit Tests für Event Publishing in RejectDocumentUseCase.

Test-Driven Development: RED Phase für Event Publishing.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from contexts.documentupload.application.use_cases import RejectDocumentUseCase
from contexts.documentupload.domain.entities import UploadedDocument, DocumentComment
from contexts.documentupload.domain.value_objects import (
    FileType, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus,
    WorkflowStatus
)
from contexts.documentupload.domain.events import DocumentRejectedEvent
from contexts.documentupload.domain.repositories import UploadRepository, DocumentCommentRepository


class TestRejectDocumentUseCaseEventPublishing:
    """Tests für Event Publishing in RejectDocumentUseCase."""
    
    @pytest.fixture
    def mock_upload_repo(self):
        """Mock UploadRepository."""
        return Mock(spec=UploadRepository)
    
    @pytest.fixture
    def mock_comment_repo(self):
        """Mock DocumentCommentRepository."""
        return Mock(spec=DocumentCommentRepository)
    
    @pytest.fixture
    def mock_event_publisher(self):
        """Mock EventPublisher."""
        return Mock()
    
    @pytest.fixture
    def use_case(self, mock_upload_repo, mock_comment_repo, mock_event_publisher):
        """RejectDocumentUseCase mit Event Publisher."""
        return RejectDocumentUseCase(
            upload_repository=mock_upload_repo,
            comment_repository=mock_comment_repo,
            event_publisher=mock_event_publisher
        )
    
    @pytest.mark.asyncio
    async def test_reject_publishes_document_rejected_event(self, use_case, mock_upload_repo, mock_comment_repo, mock_event_publisher):
        """Reject publiziert DocumentRejectedEvent"""
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
            workflow_status=WorkflowStatus.REVIEWED
        )
        mock_upload_repo.get_by_id = AsyncMock(return_value=document)
        mock_comment_repo.get_by_document_id_and_type = AsyncMock(return_value=[])
        mock_comment_repo.add = AsyncMock()
        mock_upload_repo.save = AsyncMock(return_value=document)
        mock_event_publisher.publish = AsyncMock()
        
        # Act
        await use_case.execute(
            document_id=1,
            rejected_by_user_id=2,
            rejection_reason="Incomplete information"
        )
        
        # Assert: Event sollte publiziert werden
        assert mock_event_publisher.publish.called
        published_event = mock_event_publisher.publish.call_args[0][0]
        assert isinstance(published_event, DocumentRejectedEvent)
        assert published_event.document_id == 1
        assert published_event.rejected_by_user_id == 2
        assert published_event.rejection_reason == "Incomplete information"
    
    @pytest.mark.asyncio
    async def test_reject_without_event_publisher_works(self, mock_upload_repo, mock_comment_repo):
        """Reject funktioniert auch ohne Event Publisher (optional)"""
        # Arrange
        use_case = RejectDocumentUseCase(
            upload_repository=mock_upload_repo,
            comment_repository=mock_comment_repo,
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
            workflow_status=WorkflowStatus.REVIEWED
        )
        mock_upload_repo.get_by_id = AsyncMock(return_value=document)
        mock_comment_repo.get_by_document_id_and_type = AsyncMock(return_value=[])
        mock_comment_repo.add = AsyncMock()
        mock_upload_repo.save = AsyncMock(return_value=document)
        
        # Act & Assert: Sollte ohne Fehler funktionieren
        result = await use_case.execute(
            document_id=1,
            rejected_by_user_id=2,
            rejection_reason="Incomplete information"
        )
        
        assert result.workflow_status == WorkflowStatus.REJECTED

