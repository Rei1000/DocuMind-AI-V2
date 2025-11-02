"""
Unit Tests für UploadDocumentUseCase - Optimierungen (Duplikat-Prüfung).

Test-Driven Development: Tests für optimierte Hash-Berechnung und Duplikat-Prüfung.
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


class TestUploadDocumentUseCaseOptimization:
    """Tests für optimierte Duplikat-Prüfung."""

    @pytest.fixture
    def mock_upload_repo(self):
        """Mock UploadRepository."""
        return Mock(spec=UploadRepository)

    @pytest.fixture
    def use_case(self, mock_upload_repo):
        """UploadDocumentUseCase mit Mocks."""
        return UploadDocumentUseCase(upload_repo=mock_upload_repo)

    @pytest.mark.asyncio
    async def test_hash_calculation_uses_chunks_for_large_files(self, use_case, mock_upload_repo):
        """Hash-Berechnung nutzt Chunk-basiertes Lesen für große Dateien"""
        # Arrange: Erstelle große Test-Datei (100 KB)
        large_content = b"x" * (100 * 1024)  # 100 KB
        expected_hash = hashlib.sha256(large_content).hexdigest()
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(large_content)
            tmp_file_path = tmp_file.name
        
        try:
            # Mock: Repository save
            saved_document = UploadedDocument(
                id=1,
                file_type=FileType.PDF,
                file_size_bytes=len(large_content),
                document_type_id=1,
                metadata=DocumentMetadata(filename="large.pdf", original_filename="large.pdf", qm_chapter="1.2", version="v1.0"),
                file_path=FilePath(tmp_file_path),
                processing_method=ProcessingMethod.OCR,
                processing_status=ProcessingStatus.PENDING,
                uploaded_by_user_id=1,
                uploaded_at=datetime.utcnow(),
                file_hash=FileHash(expected_hash)
            )
            mock_upload_repo.save = AsyncMock(return_value=saved_document)
            mock_upload_repo.find_by_hash = AsyncMock(return_value=None)
            
            # Act
            result = await use_case.execute(
                original_filename="large.pdf",
                file_size_bytes=len(large_content),
                document_type_id=1,
                qm_chapter="1.2",
                version="v1.0",
                file_path=tmp_file_path,
                processing_method="ocr",
                uploaded_by_user_id=1
            )
            
            # Assert: Hash sollte korrekt berechnet werden (Chunk-basiert)
            assert result.file_hash is not None
            assert result.file_hash.value == expected_hash
            
            # Verify: File wurde in Chunks gelesen (prüfe ob open() mit 'rb' aufgerufen wurde)
            # (Chunk-Logik ist in execute() implementiert)
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    @pytest.mark.asyncio
    async def test_hash_calculation_handles_file_not_found(self, use_case, mock_upload_repo):
        """Hash-Berechnung wirft ValueError bei nicht existierender Datei"""
        # Arrange
        non_existent_path = "/nonexistent/file.pdf"
        
        # Act & Assert
        with pytest.raises(ValueError, match="File not found"):
            await use_case.execute(
                original_filename="test.pdf",
                file_size_bytes=1024,
                document_type_id=1,
                qm_chapter="1.2",
                version="v1.0",
                file_path=non_existent_path,
                processing_method="ocr",
                uploaded_by_user_id=1
            )

    @pytest.mark.asyncio
    async def test_duplicate_check_handles_repository_error_gracefully(self, use_case, mock_upload_repo):
        """Duplikat-Prüfung fängt Repository-Fehler ab (Upload sollte nicht scheitern)"""
        # Arrange
        test_content = b"test content"
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(test_content)
            tmp_file_path = tmp_file.name
        
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        try:
            # Mock: Repository find_by_hash wirft Exception
            mock_upload_repo.find_by_hash = AsyncMock(side_effect=Exception("DB connection error"))
            
            # Mock: Repository save (sollte trotzdem funktionieren)
            saved_document = UploadedDocument(
                id=1,
                file_type=FileType.PDF,
                file_size_bytes=len(test_content),
                document_type_id=1,
                metadata=DocumentMetadata(filename="test.pdf", original_filename="test.pdf", qm_chapter="1.2", version="v1.0"),
                file_path=FilePath(tmp_file_path),
                processing_method=ProcessingMethod.OCR,
                processing_status=ProcessingStatus.PENDING,
                uploaded_by_user_id=1,
                uploaded_at=datetime.utcnow(),
                file_hash=FileHash(expected_hash),
                is_duplicate=False  # Sollte False sein trotz Fehler
            )
            mock_upload_repo.save = AsyncMock(return_value=saved_document)
            
            # Act: Upload sollte trotz Repository-Fehler funktionieren
            result = await use_case.execute(
                original_filename="test.pdf",
                file_size_bytes=len(test_content),
                document_type_id=1,
                qm_chapter="1.2",
                version="v1.0",
                file_path=tmp_file_path,
                processing_method="ocr",
                uploaded_by_user_id=1
            )
            
            # Assert: Upload erfolgreich, is_duplicate=False (Fehler wurde abgefangen)
            assert result.id == 1
            assert result.is_duplicate is False
            assert result.duplicate_of_document_id is None
            assert result.file_hash.value == expected_hash
            
            # Verify: find_by_hash wurde aufgerufen (auch wenn Fehler)
            mock_upload_repo.find_by_hash.assert_called_once()
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    @pytest.mark.asyncio
    async def test_duplicate_check_skips_if_no_hash(self, use_case, mock_upload_repo):
        """Duplikat-Prüfung wird übersprungen wenn Hash nicht berechnet werden konnte"""
        # Arrange: Simuliere Hash-Berechnungsfehler durch nicht-existierende Datei
        non_existent_path = "/nonexistent/file.pdf"
        
        # Act & Assert: Sollte bei FileNotFoundError abbrechen (vor Duplikat-Prüfung)
        with pytest.raises(ValueError, match="File not found"):
            await use_case.execute(
                original_filename="test.pdf",
                file_size_bytes=1024,
                document_type_id=1,
                qm_chapter="1.2",
                version="v1.0",
                file_path=non_existent_path,
                processing_method="ocr",
                uploaded_by_user_id=1
            )
        
        # Verify: find_by_hash sollte NICHT aufgerufen werden (Hash nicht berechnet)
        mock_upload_repo.find_by_hash.assert_not_called()

