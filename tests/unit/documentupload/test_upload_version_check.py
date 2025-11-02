"""
Unit Tests für UploadDocumentUseCase - Version Check.

Test-Driven Development: RED Phase für Version-Prüfung im Upload-Use Case.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import hashlib
import os
import tempfile

from contexts.documentupload.application.use_cases import UploadDocumentUseCase
from contexts.documentupload.domain.entities import UploadedDocument
from contexts.documentupload.domain.value_objects import (
    FileType, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus, FileHash
)
from contexts.documentupload.domain.repositories import UploadRepository


class TestUploadDocumentVersionCheck:
    """Tests für Version-Prüfung im UploadDocumentUseCase."""
    
    @pytest.fixture
    def mock_upload_repo(self):
        """Mock UploadRepository."""
        repo = Mock(spec=UploadRepository)
        repo.save = AsyncMock()
        repo.find_by_hash = AsyncMock(return_value=None)
        repo.find_by_document_type_and_chapter = AsyncMock(return_value=[])  # NEU
        return repo
    
    @pytest.fixture
    def use_case(self, mock_upload_repo):
        """UploadDocumentUseCase mit Mocks."""
        return UploadDocumentUseCase(mock_upload_repo)
    
    @pytest.mark.asyncio
    async def test_upload_warns_if_version_exists(self, use_case, mock_upload_repo):
        """Upload warnt wenn Version bereits existiert (gleicher document_type_id + qm_chapter)"""
        # Arrange
        test_content = b"test content"
        test_file_path = "data/uploads/test.pdf"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        # Mock: Existierendes Dokument mit gleicher Version
        existing_doc = UploadedDocument(
            id=1,
            file_type=FileType.PDF,
            file_size_bytes=len(test_content),
            document_type_id=1,
            metadata=DocumentMetadata(
                filename="existing.pdf",
                original_filename="existing.pdf",
                qm_chapter="1.2",
                version="v1.0"
            ),
            file_path=FilePath(test_file_path),
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.COMPLETED,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_hash=FileHash(expected_hash)
        )
        
        # Mock: find_by_document_type_and_chapter findet existierendes Dokument
        mock_upload_repo.find_by_document_type_and_chapter = AsyncMock(
            return_value=[existing_doc]
        )
        
        # Mock: Save
        saved_document = UploadedDocument(
            id=2,
            file_type=FileType.PDF,
            file_size_bytes=len(test_content),
            document_type_id=1,
            metadata=DocumentMetadata(
                filename="new.pdf",
                original_filename="new.pdf",
                qm_chapter="1.2",
                version="v1.0"  # Gleiche Version!
            ),
            file_path=FilePath(test_file_path),
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.PENDING,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_hash=FileHash(expected_hash)
        )
        mock_upload_repo.save = AsyncMock(return_value=saved_document)
        
        # Mock: File-Lesen (Chunk-basiert)
        with patch('builtins.open', create=True) as mock_open, \
             patch('os.path.exists', return_value=True):
            mock_file = MagicMock()
            mock_file.read.side_effect = [test_content, b'']
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Act
            result = await use_case.execute(
                original_filename="new.pdf",
                file_size_bytes=len(test_content),
                document_type_id=1,
                qm_chapter="1.2",
                version="v1.0",  # Gleiche Version wie existing_doc
                file_path=test_file_path,
                processing_method="ocr",
                uploaded_by_user_id=1
            )
        
        # Assert: Upload sollte trotzdem funktionieren (nur Warnung)
        assert result.id == 2
        
        # Verify: find_by_document_type_and_chapter wurde aufgerufen
        mock_upload_repo.find_by_document_type_and_chapter.assert_called_once_with(
            document_type_id=1,
            qm_chapter="1.2"
        )
    
    @pytest.mark.asyncio
    async def test_upload_no_warning_if_version_unique(self, use_case, mock_upload_repo):
        """Upload warnt nicht wenn Version eindeutig ist"""
        # Arrange
        test_content = b"unique content"
        test_file_path = "data/uploads/unique.pdf"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        # Mock: Keine existierenden Dokumente mit gleicher Version
        mock_upload_repo.find_by_document_type_and_chapter = AsyncMock(
            return_value=[]  # Keine existierenden Dokumente
        )
        
        # Mock: Save
        saved_document = UploadedDocument(
            id=1,
            file_type=FileType.PDF,
            file_size_bytes=len(test_content),
            document_type_id=1,
            metadata=DocumentMetadata(
                filename="unique.pdf",
                original_filename="unique.pdf",
                qm_chapter="1.2",
                version="v2.0"  # Neue Version
            ),
            file_path=FilePath(test_file_path),
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.PENDING,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_hash=FileHash(expected_hash)
        )
        mock_upload_repo.save = AsyncMock(return_value=saved_document)
        
        # Mock: File-Lesen
        with patch('builtins.open', create=True) as mock_open, \
             patch('os.path.exists', return_value=True):
            mock_file = MagicMock()
            mock_file.read.side_effect = [test_content, b'']
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Act
            result = await use_case.execute(
                original_filename="unique.pdf",
                file_size_bytes=len(test_content),
                document_type_id=1,
                qm_chapter="1.2",
                version="v2.0",  # Neue Version
                file_path=test_file_path,
                processing_method="ocr",
                uploaded_by_user_id=1
            )
        
        # Assert: Upload erfolgreich
        assert result.id == 1
        assert result.metadata.version == "v2.0"
        
        # Verify: find_by_document_type_and_chapter wurde aufgerufen
        mock_upload_repo.find_by_document_type_and_chapter.assert_called_once_with(
            document_type_id=1,
            qm_chapter="1.2"
        )

