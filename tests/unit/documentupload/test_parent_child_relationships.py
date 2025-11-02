"""
Unit Tests für Parent-Child Relationships bei Versionierung.

Test-Driven Development: RED Phase für Parent-Child Beziehungen zwischen Dokument-Versionen.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import hashlib

from contexts.documentupload.application.use_cases import UploadDocumentUseCase
from contexts.documentupload.domain.entities import UploadedDocument
from contexts.documentupload.domain.value_objects import (
    FileType, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus, FileHash
)
from contexts.documentupload.domain.repositories import UploadRepository


class TestParentChildRelationships:
    """Tests für Parent-Child Relationships bei Versionierung."""
    
    @pytest.fixture
    def mock_upload_repo(self):
        """Mock UploadRepository."""
        repo = Mock(spec=UploadRepository)
        repo.save = AsyncMock()
        repo.find_by_hash = AsyncMock(return_value=None)
        repo.find_by_document_type_and_chapter = AsyncMock(return_value=[])
        repo.get_current_version = AsyncMock(return_value=None)  # NEU
        return repo
    
    @pytest.fixture
    def use_case(self, mock_upload_repo):
        """UploadDocumentUseCase mit Mocks."""
        return UploadDocumentUseCase(mock_upload_repo)
    
    @pytest.mark.asyncio
    async def test_upload_sets_parent_if_current_version_exists(self, use_case, mock_upload_repo):
        """Upload setzt parent_document_id wenn aktuelle Version existiert"""
        # Arrange
        test_content = b"test content"
        test_file_path = "data/uploads/test.pdf"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        # Mock: Aktuelle Version existiert bereits
        current_version = UploadedDocument(
            id=1,
            file_type=FileType.PDF,
            file_size_bytes=1024,
            document_type_id=1,
            metadata=DocumentMetadata(
                filename="test_v1.0.pdf",
                original_filename="test.pdf",
                qm_chapter="1.2",
                version="v1.0"
            ),
            file_path=FilePath(test_file_path),
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.COMPLETED,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            is_current_version=True,
            document_series_id=100
        )
        
        # Mock: find_by_document_type_and_chapter findet aktuelle Version
        mock_upload_repo.find_by_document_type_and_chapter = AsyncMock(
            return_value=[current_version]
        )
        
        # Mock: get_current_version findet aktuelle Version
        mock_upload_repo.get_current_version = AsyncMock(
            return_value=current_version
        )
        
        # Mock: Save für neue Version
        new_version = UploadedDocument(
            id=2,
            file_type=FileType.PDF,
            file_size_bytes=2048,
            document_type_id=1,
            metadata=DocumentMetadata(
                filename="test_v2.0.pdf",
                original_filename="test.pdf",
                qm_chapter="1.2",
                version="v2.0"
            ),
            file_path=FilePath(test_file_path),
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.PENDING,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            parent_document_id=1,  # NEU: Parent = v1.0
            document_series_id=100,  # NEU: Gleiche Serie
            is_current_version=True  # NEU: Neue Version ist aktuell
        )
        mock_upload_repo.save = AsyncMock(return_value=new_version)
        
        # Mock: File-Lesen (Chunk-basiert)
        with patch('builtins.open', create=True) as mock_open, \
             patch('os.path.exists', return_value=True):
            mock_file = MagicMock()
            mock_file.read.side_effect = [test_content, b'']
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Act
            result = await use_case.execute(
                original_filename="test.pdf",
                file_size_bytes=len(test_content),
                document_type_id=1,
                qm_chapter="1.2",
                file_path=test_file_path,
                processing_method="ocr",
                uploaded_by_user_id=1,
                version="v2.0"  # Neue Version
            )
        
        # Assert: Parent sollte gesetzt werden
        # (Dies wird in Phase 2.2.4 implementiert - hier nur Test)
        assert result.id == 2
        
        # Verify: get_current_version sollte aufgerufen werden
        mock_upload_repo.get_current_version.assert_called_once_with(
            document_type_id=1,
            qm_chapter="1.2"
        )
    
    @pytest.mark.asyncio
    async def test_upload_no_parent_if_first_version(self, use_case, mock_upload_repo):
        """Upload setzt kein parent_document_id wenn erste Version"""
        # Arrange
        test_content = b"test content"
        test_file_path = "data/uploads/test.pdf"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        # Mock: Keine existierende Version
        mock_upload_repo.find_by_document_type_and_chapter = AsyncMock(
            return_value=[]
        )
        mock_upload_repo.get_current_version = AsyncMock(
            return_value=None  # Keine aktuelle Version
        )
        
        # Mock: Save für erste Version
        first_version = UploadedDocument(
            id=1,
            file_type=FileType.PDF,
            file_size_bytes=len(test_content),
            document_type_id=1,
            metadata=DocumentMetadata(
                filename="test_v1.0.pdf",
                original_filename="test.pdf",
                qm_chapter="1.2",
                version="v1.0"
            ),
            file_path=FilePath(test_file_path),
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.PENDING,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            parent_document_id=None,  # NEU: Kein Parent (erste Version)
            document_series_id=None,  # NEU: Wird später gesetzt
            is_current_version=True  # NEU: Erste Version ist aktuell
        )
        mock_upload_repo.save = AsyncMock(return_value=first_version)
        
        # Mock: File-Lesen
        with patch('builtins.open', create=True) as mock_open, \
             patch('os.path.exists', return_value=True):
            mock_file = MagicMock()
            mock_file.read.side_effect = [test_content, b'']
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Act
            result = await use_case.execute(
                original_filename="test.pdf",
                file_size_bytes=len(test_content),
                document_type_id=1,
                qm_chapter="1.2",
                file_path=test_file_path,
                processing_method="ocr",
                uploaded_by_user_id=1,
                version="v1.0"  # Erste Version
            )
        
        # Assert: Kein Parent gesetzt
        assert result.id == 1
        assert result.parent_document_id is None
        
        # Verify: get_current_version sollte aufgerufen werden
        mock_upload_repo.get_current_version.assert_called_once_with(
            document_type_id=1,
            qm_chapter="1.2"
        )

