"""
Unit Tests für RestoreDocumentUseCase.

Test-Driven Development: Tests für Archiv-System.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from contexts.documentupload.application.use_cases import RestoreDocumentUseCase
from contexts.documentupload.domain.entities import UploadedDocument
from contexts.documentupload.domain.value_objects import (
    FileType, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus,
    WorkflowStatus
)
from contexts.documentupload.domain.repositories import UploadRepository


class TestRestoreDocumentUseCase:
    """Tests für RestoreDocumentUseCase."""
    
    @pytest.fixture
    def mock_upload_repo(self):
        """Mock UploadRepository."""
        return Mock(spec=UploadRepository)
    
    @pytest.fixture
    def mock_event_publisher(self):
        """Mock Event Publisher."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        return publisher
    
    @pytest.fixture
    def use_case(self, mock_upload_repo):
        """RestoreDocumentUseCase mit Mock."""
        return RestoreDocumentUseCase(upload_repository=mock_upload_repo)
    
    @pytest.fixture
    def use_case_with_events(self, mock_upload_repo, mock_event_publisher):
        """RestoreDocumentUseCase mit Event Publisher."""
        return RestoreDocumentUseCase(
            upload_repository=mock_upload_repo,
            event_publisher=mock_event_publisher
        )
    
    @pytest.fixture
    def deleted_document(self):
        """Erstelle gelöschtes Dokument für Tests."""
        return UploadedDocument(
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
            workflow_status=WorkflowStatus.DELETED,
            deleted_at=datetime.utcnow(),
            deleted_by_user_id=1,
            deletion_reason="Test deletion"
        )
    
    @pytest.mark.asyncio
    async def test_restore_document_sets_status_to_draft_by_default(self, use_case, mock_upload_repo, deleted_document):
        """Restore setzt Status auf DRAFT wenn nicht spezifiziert."""
        # Arrange
        mock_upload_repo.get_by_id = AsyncMock(return_value=deleted_document)
        
        restored_document = UploadedDocument(
            id=1,
            file_type=deleted_document.file_type,
            file_size_bytes=deleted_document.file_size_bytes,
            document_type_id=deleted_document.document_type_id,
            metadata=deleted_document.metadata,
            file_path=deleted_document.file_path,
            processing_method=deleted_document.processing_method,
            processing_status=deleted_document.processing_status,
            uploaded_by_user_id=deleted_document.uploaded_by_user_id,
            uploaded_at=deleted_document.uploaded_at,
            workflow_status=WorkflowStatus.DRAFT,
            deleted_at=None,
            deleted_by_user_id=None,
            deletion_reason=None
        )
        mock_upload_repo.save = AsyncMock(return_value=restored_document)
        
        # Act
        result = await use_case.execute(document_id=1, restored_by_user_id=1)
        
        # Assert
        assert result.workflow_status == WorkflowStatus.DRAFT
        assert result.deleted_at is None
        assert result.deleted_by_user_id is None
        assert result.deletion_reason is None
        mock_upload_repo.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_restore_document_sets_specified_status(self, use_case, mock_upload_repo, deleted_document):
        """Restore setzt Status auf spezifizierten Status."""
        # Arrange
        mock_upload_repo.get_by_id = AsyncMock(return_value=deleted_document)
        
        restored_document = UploadedDocument(
            id=1,
            file_type=deleted_document.file_type,
            file_size_bytes=deleted_document.file_size_bytes,
            document_type_id=deleted_document.document_type_id,
            metadata=deleted_document.metadata,
            file_path=deleted_document.file_path,
            processing_method=deleted_document.processing_method,
            processing_status=deleted_document.processing_status,
            uploaded_by_user_id=deleted_document.uploaded_by_user_id,
            uploaded_at=deleted_document.uploaded_at,
            workflow_status=WorkflowStatus.APPROVED,
            deleted_at=None,
            deleted_by_user_id=None,
            deletion_reason=None
        )
        mock_upload_repo.save = AsyncMock(return_value=restored_document)
        
        # Act
        result = await use_case.execute(
            document_id=1,
            restore_to_status=WorkflowStatus.APPROVED,
            restored_by_user_id=1
        )
        
        # Assert
        assert result.workflow_status == WorkflowStatus.APPROVED
        mock_upload_repo.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_restore_document_not_found_raises_error(self, use_case, mock_upload_repo):
        """Restore wirft Fehler wenn Dokument nicht gefunden."""
        # Arrange
        mock_upload_repo.get_by_id = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Dokument 1 nicht gefunden"):
            await use_case.execute(document_id=1, restored_by_user_id=1)
    
    @pytest.mark.asyncio
    async def test_restore_document_not_deleted_raises_error(self, use_case, mock_upload_repo):
        """Restore wirft Fehler wenn Dokument nicht gelöscht ist."""
        # Arrange
        active_document = UploadedDocument(
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
            workflow_status=WorkflowStatus.APPROVED,
            deleted_at=None  # Nicht gelöscht!
        )
        mock_upload_repo.get_by_id = AsyncMock(return_value=active_document)
        
        # Act & Assert
        with pytest.raises(ValueError, match="ist nicht gelöscht"):
            await use_case.execute(document_id=1, restored_by_user_id=1)
    
    @pytest.mark.asyncio
    async def test_restore_document_publishes_event(self, use_case_with_events, mock_upload_repo, mock_event_publisher, deleted_document):
        """Restore publiziert DocumentRestoredEvent."""
        # Arrange
        mock_upload_repo.get_by_id = AsyncMock(return_value=deleted_document)
        
        restored_document = UploadedDocument(
            id=1,
            file_type=deleted_document.file_type,
            file_size_bytes=deleted_document.file_size_bytes,
            document_type_id=deleted_document.document_type_id,
            metadata=deleted_document.metadata,
            file_path=deleted_document.file_path,
            processing_method=deleted_document.processing_method,
            processing_status=deleted_document.processing_status,
            uploaded_by_user_id=deleted_document.uploaded_by_user_id,
            uploaded_at=deleted_document.uploaded_at,
            workflow_status=WorkflowStatus.DRAFT,
            deleted_at=None,
            deleted_by_user_id=None,
            deletion_reason=None
        )
        mock_upload_repo.save = AsyncMock(return_value=restored_document)
        
        # Act
        await use_case_with_events.execute(
            document_id=1,
            restore_to_status=WorkflowStatus.DRAFT,
            restored_by_user_id=1
        )
        
        # Assert
        mock_event_publisher.publish.assert_called_once()
        # Prüfe Event-Argumente
        call_args = mock_event_publisher.publish.call_args[0][0]
        assert call_args.document_id == 1
        assert call_args.restored_by_user_id == 1
        assert call_args.restored_to_status == WorkflowStatus.DRAFT


