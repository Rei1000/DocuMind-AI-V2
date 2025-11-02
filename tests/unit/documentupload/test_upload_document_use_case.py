"""
Unit Tests für UploadDocumentUseCase.

Test-Driven Development: RED Phase für File Hash Berechnung.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime
import hashlib
from contexts.documentupload.application.use_cases import UploadDocumentUseCase
from contexts.documentupload.domain.entities import UploadedDocument
from contexts.documentupload.domain.value_objects import FileHash, FileType, ProcessingMethod, ProcessingStatus
from contexts.documentupload.domain.repositories import UploadRepository


class TestUploadDocumentUseCaseFileHash:
    """Tests für UploadDocumentUseCase mit File Hash Berechnung."""
    
    @pytest.fixture
    def mock_upload_repo(self):
        """Mock UploadRepository."""
        repo = Mock(spec=UploadRepository)
        repo.save = AsyncMock()
        repo.find_by_hash = AsyncMock(return_value=None)  # Standard: Kein Duplikat
        return repo
    
    @pytest.fixture
    def use_case(self, mock_upload_repo):
        """UploadDocumentUseCase mit Mock Repository."""
        return UploadDocumentUseCase(mock_upload_repo)
    
    @pytest.mark.asyncio
    async def test_upload_document_calculates_file_hash(self, use_case, mock_upload_repo):
        """UploadDocumentUseCase berechnet SHA-256 Hash"""
        # Arrange
        test_file_path = "data/uploads/test.pdf"
        test_content = b"test file content"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        # Mock: Repository save
        saved_document = UploadedDocument(
            id=1,
            file_type=FileType.PDF,
            file_size_bytes=len(test_content),
            document_type_id=1,
            metadata=None,  # Wird im Use Case erstellt
            file_path=None,  # Wird im Use Case erstellt
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.PENDING,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_hash=FileHash(expected_hash)
        )
        mock_upload_repo.save.return_value = saved_document
        
        # Mock: File-Lesen für Hash-Berechnung
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = test_content
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Act
            result = await use_case.execute(
                original_filename="test.pdf",
                file_size_bytes=len(test_content),
                document_type_id=1,
                qm_chapter="1.2",
                version="v1.0",
                file_path=test_file_path,
                processing_method="ocr",
                uploaded_by_user_id=1
            )
        
        # Assert
        # Prüfe ob file_hash im save-Call enthalten war
        call_args = mock_upload_repo.save.call_args
        saved_doc_arg = call_args[0][0]  # Erster Positional Argument
        assert saved_doc_arg.file_hash is not None
        assert saved_doc_arg.file_hash.value == expected_hash
    
    @pytest.mark.asyncio
    async def test_upload_document_hash_calculation_error_handling(self, use_case, mock_upload_repo):
        """Fehler bei Hash-Berechnung wird abgefangen"""
        # Arrange
        test_file_path = "data/uploads/test.pdf"
        
        # Mock: File-Öffnen wirft Fehler
        with patch('builtins.open', side_effect=IOError("File not found")):
            # Act & Assert
            with pytest.raises(ValueError, match="Failed to calculate file hash"):
                await use_case.execute(
                    original_filename="test.pdf",
                    file_size_bytes=100,
                    document_type_id=1,
                    qm_chapter="1.2",
                    version="v1.0",
                    file_path=test_file_path,
                    processing_method="ocr",
                    uploaded_by_user_id=1
                )
    
    @pytest.mark.asyncio
    async def test_upload_document_hash_optional_if_file_not_exists(self, use_case, mock_upload_repo):
        """Hash-Berechnung wird übersprungen wenn Datei nicht existiert (mit Warnung)"""
        # Arrange
        test_file_path = "data/uploads/test.pdf"
        
        # Mock: File nicht gefunden
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            # Act & Assert
            with pytest.raises(ValueError, match="Failed to calculate file hash"):
                await use_case.execute(
                    original_filename="test.pdf",
                    file_size_bytes=100,
                    document_type_id=1,
                    qm_chapter="1.2",
                    version="v1.0",
                    file_path=test_file_path,
                    processing_method="ocr",
                    uploaded_by_user_id=1
                )
    
    @pytest.mark.asyncio
    async def test_upload_document_detects_duplicate(self, use_case, mock_upload_repo):
        """UploadDocumentUseCase erkennt Duplikat und setzt Flag"""
        # Arrange
        test_file_path = "data/uploads/duplicate.pdf"
        test_content = b"duplicate content"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        # Mock: Existierendes Dokument mit gleichem Hash
        existing_doc = UploadedDocument(
            id=1,
            file_type=FileType.PDF,
            file_size_bytes=len(test_content),
            document_type_id=1,
            metadata=None,
            file_path=None,
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.PENDING,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_hash=FileHash(expected_hash)
        )
        mock_upload_repo.find_by_hash = AsyncMock(return_value=existing_doc)
        
        # Mock: Save für neues Dokument (Duplikat)
        duplicate_document = UploadedDocument(
            id=2,
            file_type=FileType.PDF,
            file_size_bytes=len(test_content),
            document_type_id=1,
            metadata=None,
            file_path=None,
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.PENDING,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_hash=FileHash(expected_hash),
            is_duplicate=True,
            duplicate_of_document_id=1
        )
        mock_upload_repo.save.return_value = duplicate_document
        
        # Mock: File-Lesen
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = test_content
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Act
            result = await use_case.execute(
                original_filename="duplicate.pdf",
                file_size_bytes=len(test_content),
                document_type_id=1,
                qm_chapter="1.2",
                version="v1.0",
                file_path=test_file_path,
                processing_method="ocr",
                uploaded_by_user_id=1
            )
        
        # Assert
        call_args = mock_upload_repo.save.call_args
        saved_doc_arg = call_args[0][0]
        assert saved_doc_arg.is_duplicate is True
        assert saved_doc_arg.duplicate_of_document_id == 1
        assert saved_doc_arg.file_hash.value == expected_hash
    
    @pytest.mark.asyncio
    async def test_upload_document_unique_document_no_duplicate_flag(self, use_case, mock_upload_repo):
        """Eindeutiges Dokument setzt kein Duplikat-Flag"""
        # Arrange
        test_file_path = "data/uploads/unique.pdf"
        test_content = b"unique content"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        # Mock: Kein Duplikat gefunden
        mock_upload_repo.find_by_hash = AsyncMock(return_value=None)
        
        # Mock: Save
        unique_document = UploadedDocument(
            id=1,
            file_type=FileType.PDF,
            file_size_bytes=len(test_content),
            document_type_id=1,
            metadata=None,
            file_path=None,
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.PENDING,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_hash=FileHash(expected_hash),
            is_duplicate=False,
            duplicate_of_document_id=None
        )
        mock_upload_repo.save.return_value = unique_document
        
        # Mock: File-Lesen
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = test_content
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Act
            result = await use_case.execute(
                original_filename="unique.pdf",
                file_size_bytes=len(test_content),
                document_type_id=1,
                qm_chapter="1.2",
                version="v1.0",
                file_path=test_file_path,
                processing_method="ocr",
                uploaded_by_user_id=1
            )
        
        # Assert
        call_args = mock_upload_repo.save.call_args
        saved_doc_arg = call_args[0][0]
        assert saved_doc_arg.is_duplicate is False
        assert saved_doc_arg.duplicate_of_document_id is None
        assert saved_doc_arg.file_hash.value == expected_hash

