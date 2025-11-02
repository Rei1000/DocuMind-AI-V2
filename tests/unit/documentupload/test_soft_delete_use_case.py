"""
Unit Tests für SoftDeleteDocumentUseCase.

Test-Driven Development: RED Phase für Soft Delete Use Case.
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
from contexts.documentupload.domain.repositories import UploadRepository


class TestSoftDeleteDocumentUseCase:
    """Tests für SoftDeleteDocumentUseCase."""
    
    @pytest.fixture
    def mock_upload_repo(self):
        """Mock UploadRepository."""
        return Mock(spec=UploadRepository)
    
    @pytest.fixture
    def use_case(self, mock_upload_repo):
        """SoftDeleteDocumentUseCase mit Mock."""
        return SoftDeleteDocumentUseCase(upload_repository=mock_upload_repo)
    
    @pytest.mark.asyncio
    async def test_soft_delete_document_sets_status_deleted(self, use_case, mock_upload_repo):
        """Soft Delete setzt Status auf DELETED"""
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
        deleted_document = UploadedDocument(
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
        mock_upload_repo.save = AsyncMock(return_value=deleted_document)
        
        # Act
        result = await use_case.execute(
            document_id=1,
            deleted_by_user_id=1,
            reason="Test deletion"
        )
        
        # Assert
        assert result.workflow_status == WorkflowStatus.DELETED
        assert result.is_deleted is True
        mock_upload_repo.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_soft_delete_document_sets_deleted_fields(self, use_case, mock_upload_repo):
        """Soft Delete setzt deleted_at, deleted_by_user_id, deletion_reason"""
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
        deleted_document = UploadedDocument(
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
        mock_upload_repo.save = AsyncMock(return_value=deleted_document)
        
        # Act
        result = await use_case.execute(
            document_id=1,
            deleted_by_user_id=1,
            reason="Test deletion"
        )
        
        # Assert
        assert result.deleted_at is not None
        assert result.deleted_by_user_id == 1
        assert result.deletion_reason == "Test deletion"
    
    @pytest.mark.asyncio
    async def test_soft_delete_document_not_found_raises_error(self, use_case, mock_upload_repo):
        """Soft Delete wirft Fehler wenn Dokument nicht gefunden"""
        # Arrange
        mock_upload_repo.get_by_id = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Document 1 not found"):
            await use_case.execute(
                document_id=1,
                deleted_by_user_id=1,
                reason="Test deletion"
            )
    
    @pytest.mark.asyncio
    async def test_soft_delete_document_invalid_user_id_raises_error(self, use_case, mock_upload_repo):
        """Soft Delete wirft Fehler bei ungültiger user_id"""
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
        with pytest.raises(ValueError, match="deleted_by_user_id must be positive"):
            await use_case.execute(
                document_id=1,
                deleted_by_user_id=0,  # Ungültig
                reason="Test deletion"
            )
    
    @pytest.mark.asyncio
    async def test_soft_delete_document_empty_reason_raises_error(self, use_case, mock_upload_repo):
        """Soft Delete wirft Fehler bei leerem reason"""
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
        with pytest.raises(ValueError, match="reason cannot be empty"):
            await use_case.execute(
                document_id=1,
                deleted_by_user_id=1,
                reason=""  # Leer
            )
    
    @pytest.mark.asyncio
    async def test_soft_delete_already_deleted_document_allowed(self, use_case, mock_upload_repo):
        """Soft Delete eines bereits gelöschten Dokuments ist erlaubt (Update)"""
        # Arrange
        deleted_document = UploadedDocument(
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
            deletion_reason="Old reason"
        )
        mock_upload_repo.get_by_id = AsyncMock(return_value=deleted_document)
        
        # Mock: Save gibt aktualisiertes Dokument zurück
        updated_deleted_document = UploadedDocument(
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
            deleted_by_user_id=2,  # Anderer User
            deletion_reason="Updated reason"
        )
        mock_upload_repo.save = AsyncMock(return_value=updated_deleted_document)
        
        # Act
        result = await use_case.execute(
            document_id=1,
            deleted_by_user_id=2,
            reason="Updated reason"
        )
        
        # Assert
        assert result.workflow_status == WorkflowStatus.DELETED
        assert result.deleted_by_user_id == 2
        assert result.deletion_reason == "Updated reason"

