"""
Unit Tests für HardDeleteDocumentUseCase.

Test-Driven Development: Tests für Archiv-System.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import os

from contexts.documentupload.application.use_cases import HardDeleteDocumentUseCase
from contexts.documentupload.domain.entities import UploadedDocument, DocumentPage
from contexts.documentupload.domain.value_objects import (
    FileType, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus,
    WorkflowStatus
)
from contexts.documentupload.domain.repositories import UploadRepository, DocumentPageRepository


class TestHardDeleteDocumentUseCase:
    """Tests für HardDeleteDocumentUseCase."""
    
    @pytest.fixture
    def mock_upload_repo(self):
        """Mock UploadRepository."""
        return Mock(spec=UploadRepository)
    
    @pytest.fixture
    def mock_page_repo(self):
        """Mock DocumentPageRepository."""
        return Mock(spec=DocumentPageRepository)
    
    @pytest.fixture
    def mock_event_publisher(self):
        """Mock Event Publisher."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        return publisher
    
    @pytest.fixture
    def use_case(self, mock_upload_repo, mock_page_repo):
        """HardDeleteDocumentUseCase mit Mock."""
        use_case = HardDeleteDocumentUseCase(
            upload_repository=mock_upload_repo,
            page_repository=mock_page_repo
        )
        # Stelle sicher, dass page_repository gesetzt ist
        use_case.page_repository = mock_page_repo
        return use_case
    
    @pytest.fixture
    def use_case_with_events(self, mock_upload_repo, mock_page_repo, mock_event_publisher):
        """HardDeleteDocumentUseCase mit Event Publisher."""
        use_case = HardDeleteDocumentUseCase(
            upload_repository=mock_upload_repo,
            page_repository=mock_page_repo,
            event_publisher=mock_event_publisher
        )
        # Stelle sicher, dass page_repository gesetzt ist
        use_case.page_repository = mock_page_repo
        return use_case
    
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
    
    @pytest.fixture
    def sample_pages(self):
        """Erstelle Beispieldokumentenseiten für Tests."""
        return [
            DocumentPage(
                id=None,
                upload_document_id=1,
                page_number=1,
                preview_image_path=FilePath("data/uploads/previews/test_1.png"),
                thumbnail_path=FilePath("data/uploads/thumbnails/test_1_thumb.png"),
                dimensions=None,
                created_at=datetime.utcnow()
            ),
            DocumentPage(
                id=None,
                upload_document_id=1,
                page_number=2,
                preview_image_path=FilePath("data/uploads/previews/test_2.png"),
                thumbnail_path=FilePath("data/uploads/thumbnails/test_2_thumb.png"),
                dimensions=None,
                created_at=datetime.utcnow()
            )
        ]
    
    @pytest.mark.asyncio
    async def test_hard_delete_validates_confirmation(self, use_case, mock_upload_repo, deleted_document):
        """HardDelete validiert confirmation == 'LÖSCHEN'."""
        # Arrange
        mock_upload_repo.get_by_id = AsyncMock(return_value=deleted_document)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Bestätigung fehlgeschlagen"):
            await use_case.execute(
                document_id=1,
                deleted_by_user_id=1,
                confirmation="FALSCH"
            )
    
    @pytest.mark.asyncio
    async def test_hard_delete_accepts_correct_confirmation(self, use_case, mock_upload_repo, mock_page_repo, deleted_document, sample_pages):
        """HardDelete akzeptiert 'LÖSCHEN' als confirmation."""
        # Arrange
        mock_upload_repo.get_by_id = AsyncMock(return_value=deleted_document)
        mock_page_repo.get_by_document_id = AsyncMock(return_value=sample_pages)
        mock_upload_repo.delete = AsyncMock(return_value=True)
        
        # Mock file operations
        with patch('os.path.exists', return_value=True):
            with patch('os.remove') as mock_remove:
                # Act
                result = await use_case.execute(
                    document_id=1,
                    deleted_by_user_id=1,
                    confirmation="LÖSCHEN"
                )
                
                # Assert
                assert result["success"] is True
                mock_upload_repo.delete.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_hard_delete_case_insensitive_confirmation(self, use_case, mock_upload_repo, mock_page_repo, deleted_document, sample_pages):
        """HardDelete akzeptiert confirmation case-insensitive."""
        # Arrange
        mock_upload_repo.get_by_id = AsyncMock(return_value=deleted_document)
        mock_page_repo.get_by_document_id = AsyncMock(return_value=sample_pages)
        mock_upload_repo.delete = AsyncMock(return_value=True)
        
        # Mock file operations
        with patch('contexts.documentupload.application.use_cases.os.path.exists', return_value=True):
            with patch('contexts.documentupload.application.use_cases.os.remove'):
                # Act
                result = await use_case.execute(
                    document_id=1,
                    deleted_by_user_id=1,
                    confirmation="löschen"  # lowercase
                )
                
                # Assert
                assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_hard_delete_removes_files(self, use_case, mock_upload_repo, mock_page_repo, deleted_document, sample_pages):
        """HardDelete entfernt physische Dateien."""
        # Arrange
        mock_upload_repo.get_by_id = AsyncMock(return_value=deleted_document)
        mock_page_repo.get_by_document_id = AsyncMock(return_value=sample_pages)
        mock_upload_repo.delete = AsyncMock(return_value=True)
        
        # Mock file operations
        with patch('contexts.documentupload.application.use_cases.os.path.exists', return_value=True) as mock_exists:
            with patch('contexts.documentupload.application.use_cases.os.remove') as mock_remove:
                # Act
                result = await use_case.execute(
                    document_id=1,
                    deleted_by_user_id=1,
                    confirmation="LÖSCHEN"
                )
                
                # Assert
                assert result["success"] is True
                # Datei sollte gelöscht werden
                assert mock_remove.called
                # files_deleted sollte Dateien enthalten
                assert len(result.get("files_deleted", [])) > 0
    
    @pytest.mark.asyncio
    async def test_hard_delete_removes_preview_files(self, use_case, mock_upload_repo, mock_page_repo, deleted_document, sample_pages):
        """HardDelete entfernt Preview- und Thumbnail-Dateien."""
        # Arrange
        mock_upload_repo.get_by_id = AsyncMock(return_value=deleted_document)
        mock_page_repo.get_by_document_id = AsyncMock(return_value=sample_pages)
        mock_upload_repo.delete = AsyncMock(return_value=True)
        
        # Mock file operations
        with patch('os.path.exists', return_value=True):
            with patch('os.remove') as mock_remove:
                # Act
                result = await use_case.execute(
                    document_id=1,
                    deleted_by_user_id=1,
                    confirmation="LÖSCHEN"
                )
                
                # Assert
                assert result["success"] is True
                # Mindestens 3 Dateien sollten entfernt werden (1 Hauptdatei + 2 Previews + 2 Thumbnails)
                files_deleted = result.get("files_deleted", [])
                assert len(files_deleted) >= 3
    
    @pytest.mark.asyncio
    async def test_hard_delete_not_found_raises_error(self, use_case, mock_upload_repo):
        """HardDelete wirft Fehler wenn Dokument nicht gefunden."""
        # Arrange
        mock_upload_repo.get_by_id = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Dokument 1 nicht gefunden"):
            await use_case.execute(
                document_id=1,
                deleted_by_user_id=1,
                confirmation="LÖSCHEN"
            )
    
    @pytest.mark.asyncio
    async def test_hard_delete_publishes_event(self, use_case_with_events, mock_upload_repo, mock_page_repo, mock_event_publisher, deleted_document, sample_pages):
        """HardDelete publiziert DocumentHardDeletedEvent."""
        # Arrange
        mock_upload_repo.get_by_id = AsyncMock(return_value=deleted_document)
        # use_case_with_events hat bereits mock_page_repo, aber wir müssen es trotzdem mocken
        use_case_with_events.page_repository.get_by_document_id = AsyncMock(return_value=sample_pages)
        mock_upload_repo.delete = AsyncMock(return_value=True)
        
        # Mock file operations
        with patch('contexts.documentupload.application.use_cases.os.path.exists', return_value=True):
            with patch('contexts.documentupload.application.use_cases.os.remove'):
                # Act
                result = await use_case_with_events.execute(
                    document_id=1,
                    deleted_by_user_id=1,
                    confirmation="LÖSCHEN"
                )
                
                # Assert
                assert result["success"] is True
                mock_event_publisher.publish.assert_called_once()
                # Prüfe Event-Argumente
                call_args = mock_event_publisher.publish.call_args[0][0]
                assert call_args.document_id == 1
                assert call_args.deleted_by_user_id == 1
                assert call_args.deletion_reason == "Test deletion"
                assert len(call_args.files_deleted) > 0

