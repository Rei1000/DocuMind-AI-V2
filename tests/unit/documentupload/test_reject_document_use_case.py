"""
Unit Tests für RejectDocumentUseCase.

Test-Driven Development: RED Phase für Rejection Use Case (Kommentar erforderlich).
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from contexts.documentupload.application.use_cases import RejectDocumentUseCase
from contexts.documentupload.domain.entities import UploadedDocument
from contexts.documentupload.domain.value_objects import (
    FileType, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus,
    WorkflowStatus
)
from contexts.documentupload.domain.repositories import (
    UploadRepository, DocumentCommentRepository
)


class TestRejectDocumentUseCase:
    """Tests für RejectDocumentUseCase."""
    
    @pytest.fixture
    def mock_upload_repo(self):
        """Mock UploadRepository."""
        return Mock(spec=UploadRepository)
    
    @pytest.fixture
    def mock_comment_repo(self):
        """Mock DocumentCommentRepository."""
        return Mock(spec=DocumentCommentRepository)
    
    @pytest.fixture
    def use_case(self, mock_upload_repo, mock_comment_repo):
        """RejectDocumentUseCase mit Mocks."""
        return RejectDocumentUseCase(
            upload_repository=mock_upload_repo,
            comment_repository=mock_comment_repo
        )
    
    @pytest.mark.asyncio
    async def test_reject_document_without_comment_raises_error(self, use_case, mock_upload_repo, mock_comment_repo):
        """Rejection ohne Kommentar wirft ValueError"""
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
        
        # Mock: Keine Kommentare vorhanden
        mock_comment_repo.get_by_document_id_and_type = AsyncMock(return_value=[])
        mock_comment_repo.add = AsyncMock()  # Für Kommentar-Erstellung
        
        # Act & Assert: Leerer rejection_reason sollte Fehler werfen
        with pytest.raises(ValueError, match="Rejection requires a comment"):
            await use_case.execute(
                document_id=1,
                rejected_by_user_id=1,
                rejection_reason=""  # Leerer Grund = kein Kommentar
            )
    
    @pytest.mark.asyncio
    async def test_reject_document_with_comment_succeeds(self, use_case, mock_upload_repo, mock_comment_repo):
        """Rejection mit Kommentar ist erfolgreich"""
        # Arrange
        from contexts.documentupload.domain.entities import DocumentComment
        
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
        
        # Mock: Kommentar vorhanden
        rejection_comment = DocumentComment(
            id=1,
            document_id=1,
            user_id=1,
            comment_text="Dokument entspricht nicht den Anforderungen",
            comment_type="rejection",
            created_at=datetime.utcnow()
        )
        mock_comment_repo.get_by_document_id_and_type = AsyncMock(
            return_value=[rejection_comment]
        )
        
        # Mock: Save
        rejected_document = UploadedDocument(
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
            workflow_status=WorkflowStatus.REJECTED
        )
        mock_upload_repo.save = AsyncMock(return_value=rejected_document)
        
        # Act
        result = await use_case.execute(
            document_id=1,
            rejected_by_user_id=1,
            rejection_reason="Dokument entspricht nicht den Anforderungen"
        )
        
        # Assert
        assert result.workflow_status == WorkflowStatus.REJECTED
        
        # Verify: Save wurde aufgerufen
        mock_upload_repo.save.assert_called_once()
        
        # Verify: Kommentar-Prüfung wurde durchgeführt
        mock_comment_repo.get_by_document_id_and_type.assert_called_once_with(
            document_id=1,
            comment_type="rejection"
        )
    
    @pytest.mark.asyncio
    async def test_reject_document_checks_existing_rejection_comment(self, use_case, mock_upload_repo, mock_comment_repo):
        """Rejection prüft ob bereits ein Rejection-Kommentar existiert"""
        # Arrange
        from contexts.documentupload.domain.entities import DocumentComment
        
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
        
        # Mock: Rejection-Kommentar existiert bereits
        existing_comment = DocumentComment(
            id=1,
            document_id=1,
            user_id=1,
            comment_text="Bereits vorhandener Rejection-Kommentar",
            comment_type="rejection",
            created_at=datetime.utcnow()
        )
        mock_comment_repo.get_by_document_id_and_type = AsyncMock(
            return_value=[existing_comment]
        )
        
        # Mock: Save
        rejected_document = UploadedDocument(
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
            workflow_status=WorkflowStatus.REJECTED
        )
        mock_upload_repo.save = AsyncMock(return_value=rejected_document)
        
        # Act
        result = await use_case.execute(
            document_id=1,
            rejected_by_user_id=1,
            rejection_reason="Dokument entspricht nicht den Anforderungen"
        )
        
        # Assert
        assert result.workflow_status == WorkflowStatus.REJECTED

