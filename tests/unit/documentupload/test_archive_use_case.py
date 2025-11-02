"""
Unit Tests für ArchiveDocumentUseCase.

Test-Driven Development: RED Phase für Archive Use Case.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from contexts.documentupload.application.use_cases import ArchiveDocumentUseCase
from contexts.documentupload.domain.entities import UploadedDocument
from contexts.documentupload.domain.value_objects import (
    FileType, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus,
    WorkflowStatus
)
from contexts.documentupload.domain.repositories import UploadRepository


class TestArchiveDocumentUseCase:
    """Tests für ArchiveDocumentUseCase."""
    
    @pytest.fixture
    def mock_upload_repo(self):
        """Mock UploadRepository."""
        return Mock(spec=UploadRepository)
    
    @pytest.fixture
    def use_case(self, mock_upload_repo):
        """ArchiveDocumentUseCase mit Mock."""
        return ArchiveDocumentUseCase(upload_repository=mock_upload_repo)
    
    @pytest.mark.asyncio
    async def test_archive_document_sets_status_archived(self, use_case, mock_upload_repo):
        """Archive setzt Status auf ARCHIVED"""
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
        
        # Mock: Save gibt aktualisiertes Dokument zurück
        archived_document = UploadedDocument(
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
            workflow_status=WorkflowStatus.ARCHIVED,
            archived_at=datetime.utcnow(),
            archived_by_user_id=1,
            archive_reason="Old version"
        )
        mock_upload_repo.save = AsyncMock(return_value=archived_document)
        
        # Act
        result = await use_case.execute(
            document_id=1,
            archived_by_user_id=1,
            reason="Old version"
        )
        
        # Assert
        assert result.workflow_status == WorkflowStatus.ARCHIVED
        assert result.is_archived is True
        mock_upload_repo.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_archive_document_sets_archive_fields(self, use_case, mock_upload_repo):
        """Archive setzt archived_at, archived_by_user_id, archive_reason"""
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
        
        # Mock: Save gibt aktualisiertes Dokument zurück
        archived_document = UploadedDocument(
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
            workflow_status=WorkflowStatus.ARCHIVED,
            archived_at=datetime.utcnow(),
            archived_by_user_id=1,
            archive_reason="Old version"
        )
        mock_upload_repo.save = AsyncMock(return_value=archived_document)
        
        # Act
        result = await use_case.execute(
            document_id=1,
            archived_by_user_id=1,
            reason="Old version"
        )
        
        # Assert
        assert result.archived_at is not None
        assert result.archived_by_user_id == 1
        assert result.archive_reason == "Old version"
    
    @pytest.mark.asyncio
    async def test_archive_document_not_found_raises_error(self, use_case, mock_upload_repo):
        """Archive wirft Fehler wenn Dokument nicht gefunden"""
        # Arrange
        mock_upload_repo.get_by_id = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Document 1 not found"):
            await use_case.execute(
                document_id=1,
                archived_by_user_id=1,
                reason="Old version"
            )
    
    @pytest.mark.asyncio
    async def test_archive_document_invalid_user_id_raises_error(self, use_case, mock_upload_repo):
        """Archive wirft Fehler bei ungültiger user_id"""
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
        
        # Act & Assert
        with pytest.raises(ValueError, match="archived_by_user_id must be positive"):
            await use_case.execute(
                document_id=1,
                archived_by_user_id=0,  # Ungültig
                reason="Old version"
            )
    
    @pytest.mark.asyncio
    async def test_archive_document_empty_reason_allowed(self, use_case, mock_upload_repo):
        """Archive erlaubt leeren reason (optional im Gegensatz zu Soft Delete)"""
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
        
        # Mock: Save gibt aktualisiertes Dokument zurück
        archived_document = UploadedDocument(
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
            workflow_status=WorkflowStatus.ARCHIVED,
            archived_at=datetime.utcnow(),
            archived_by_user_id=1,
            archive_reason=None  # Leer erlaubt
        )
        mock_upload_repo.save = AsyncMock(return_value=archived_document)
        
        # Act
        result = await use_case.execute(
            document_id=1,
            archived_by_user_id=1,
            reason=""  # Leer erlaubt für Archive (im Gegensatz zu Soft Delete)
        )
        
        # Assert
        assert result.workflow_status == WorkflowStatus.ARCHIVED

