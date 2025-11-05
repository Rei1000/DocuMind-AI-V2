"""
Unit Tests für GetArchivedDocumentsUseCase.

Test-Driven Development: Tests für Archiv-System.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from typing import List

from contexts.documentupload.application.use_cases import GetArchivedDocumentsUseCase
from contexts.documentupload.domain.entities import UploadedDocument
from contexts.documentupload.domain.value_objects import (
    FileType, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus,
    WorkflowStatus
)
from contexts.documentupload.domain.repositories import UploadRepository


class TestGetArchivedDocumentsUseCase:
    """Tests für GetArchivedDocumentsUseCase."""
    
    @pytest.fixture
    def mock_upload_repo(self):
        """Mock UploadRepository."""
        return Mock(spec=UploadRepository)
    
    @pytest.fixture
    def use_case(self, mock_upload_repo):
        """GetArchivedDocumentsUseCase mit Mock."""
        return GetArchivedDocumentsUseCase(upload_repository=mock_upload_repo)
    
    @pytest.fixture
    def sample_archived_documents(self):
        """Erstelle Beispieldokumente für Tests."""
        return [
            UploadedDocument(
                id=1,
                file_type=FileType.PDF,
                file_size_bytes=1024,
                document_type_id=1,
                metadata=DocumentMetadata(
                    filename="test1.pdf",
                    original_filename="test1.pdf",
                    qm_chapter="1.2",
                    version="v1.0"
                ),
                file_path=FilePath("data/uploads/test1.pdf"),
                processing_method=ProcessingMethod.OCR,
                processing_status=ProcessingStatus.COMPLETED,
                uploaded_by_user_id=1,
                uploaded_at=datetime.utcnow(),
                workflow_status=WorkflowStatus.DELETED,
                deleted_at=datetime.utcnow(),
                deleted_by_user_id=1,
                deletion_reason="Test deletion"
            ),
            UploadedDocument(
                id=2,
                file_type=FileType.PDF,
                file_size_bytes=2048,
                document_type_id=2,
                metadata=DocumentMetadata(
                    filename="test2.pdf",
                    original_filename="test2.pdf",
                    qm_chapter="2.1",
                    version="v2.0"
                ),
                file_path=FilePath("data/uploads/test2.pdf"),
                processing_method=ProcessingMethod.VISION,
                processing_status=ProcessingStatus.COMPLETED,
                uploaded_by_user_id=2,
                uploaded_at=datetime.utcnow(),
                workflow_status=WorkflowStatus.DELETED,
                deleted_at=datetime.utcnow(),
                deleted_by_user_id=2,
                deletion_reason="Old version"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_get_archived_documents_returns_list(self, use_case, mock_upload_repo, sample_archived_documents):
        """GetArchivedDocumentsUseCase gibt Liste zurück."""
        # Arrange
        mock_upload_repo.find_archived = AsyncMock(return_value=sample_archived_documents)
        
        # Act
        result = await use_case.execute(limit=100, offset=0)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
        mock_upload_repo.find_archived.assert_called_once_with(
            limit=100,
            offset=0,
            document_type_id=None,
            deleted_before=None,
            deleted_after=None
        )
    
    @pytest.mark.asyncio
    async def test_get_archived_documents_with_filters(self, use_case, mock_upload_repo, sample_archived_documents):
        """GetArchivedDocumentsUseCase filtert korrekt."""
        # Arrange
        mock_upload_repo.find_archived = AsyncMock(return_value=[sample_archived_documents[0]])
        deleted_before = datetime.utcnow()
        deleted_after = datetime(2024, 1, 1)
        
        # Act
        result = await use_case.execute(
            limit=50,
            offset=10,
            document_type_id=1,
            deleted_before=deleted_before,
            deleted_after=deleted_after
        )
        
        # Assert
        assert len(result) == 1
        mock_upload_repo.find_archived.assert_called_once_with(
            limit=50,
            offset=10,
            document_type_id=1,
            deleted_before=deleted_before,
            deleted_after=deleted_after
        )
    
    @pytest.mark.asyncio
    async def test_get_archived_documents_empty_list(self, use_case, mock_upload_repo):
        """GetArchivedDocumentsUseCase gibt leere Liste zurück wenn keine Dokumente."""
        # Arrange
        mock_upload_repo.find_archived = AsyncMock(return_value=[])
        
        # Act
        result = await use_case.execute()
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 0
        mock_upload_repo.find_archived.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_archived_documents_passes_through_parameters(self, use_case, mock_upload_repo):
        """GetArchivedDocumentsUseCase übergibt Parameter korrekt an Repository."""
        # Arrange
        mock_upload_repo.find_archived = AsyncMock(return_value=[])
        
        # Act
        await use_case.execute(
            limit=200,
            offset=20,
            document_type_id=5,
            deleted_before=datetime(2025, 12, 31),
            deleted_after=datetime(2025, 1, 1)
        )
        
        # Assert
        mock_upload_repo.find_archived.assert_called_once_with(
            limit=200,
            offset=20,
            document_type_id=5,
            deleted_before=datetime(2025, 12, 31),
            deleted_after=datetime(2025, 1, 1)
        )


