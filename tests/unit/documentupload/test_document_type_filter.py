"""
Test für Dokumententyp-Filter Funktionalität.

TDD Approach: Schreibe zuerst den Test, dann die Implementierung.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from contexts.documentupload.domain.entities import UploadedDocument, DocumentMetadata
from contexts.documentupload.domain.value_objects import WorkflowStatus, FileType, ProcessingMethod, ProcessingStatus, FilePath
from contexts.documentupload.application.use_cases import GetDocumentsByWorkflowStatusUseCase


class TestDocumentTypeFilter:
    """Test-Klasse für Dokumententyp-Filter Use Case."""
    
    @pytest.mark.asyncio
    async def test_filter_documents_by_type(self):
        """
        Test: Filter nach Dokumenttyp.
        
        GIVEN: Dokumente mit verschiedenen Typen
        WHEN: Filter auf Typ "Arbeitsbeschreibung" gesetzt wird
        THEN: Nur Dokumente dieses Typs werden angezeigt
        """
        # ARRANGE
        status = WorkflowStatus.REVIEWED
        document_type_id = 1  # Arbeitsbeschreibung
        
        # Mock Documents
        mock_documents = [
            UploadedDocument(
                id=1,
                file_type=FileType.PDF,
                file_size_bytes=1024000,
                document_type_id=1,  # Arbeitsbeschreibung
                metadata=DocumentMetadata(filename="doc1.pdf", version="v1"),
                file_path=FilePath("/uploads/doc1.pdf"),
                processing_method=ProcessingMethod.OCR,
                processing_status=ProcessingStatus.COMPLETED,
                uploaded_by_user_id=1,
                uploaded_at=datetime.now(),
                workflow_status=WorkflowStatus.REVIEWED,
                pages=[],
                interest_group_ids=[1, 2]
            ),
            UploadedDocument(
                id=2,
                file_type=FileType.PDF,
                file_size_bytes=2048000,
                document_type_id=2,  # Flussdiagramm
                metadata=DocumentMetadata(filename="doc2.pdf", version="v1"),
                file_path=FilePath("/uploads/doc2.pdf"),
                processing_method=ProcessingMethod.OCR,
                processing_status=ProcessingStatus.COMPLETED,
                uploaded_by_user_id=1,
                uploaded_at=datetime.now(),
                workflow_status=WorkflowStatus.REVIEWED,
                pages=[],
                interest_group_ids=[3]
            )
        ]
        
        # Mock Repository
        mock_repo = AsyncMock()
        mock_repo.get_by_workflow_status.return_value = mock_documents
        
        # Use Case
        use_case = GetDocumentsByWorkflowStatusUseCase(upload_repository=mock_repo)
        
        # ACT
        result = await use_case.execute(
            status=status,
            document_type_id=document_type_id
        )
        
        # ASSERT
        assert len(result) == 1
        assert result[0].document_type_id == 1
        mock_repo.get_by_workflow_status.assert_called_once_with(
            status=status,
            document_type_id=document_type_id
        )
    
    @pytest.mark.asyncio
    async def test_filter_documents_no_type_filter(self):
        """
        Test: Kein Filter - alle Dokumente werden zurückgegeben.
        
        GIVEN: Dokumente mit verschiedenen Typen
        WHEN: Kein Typ-Filter gesetzt wird
        THEN: Alle Dokumente werden zurückgegeben
        """
        # ARRANGE
        status = WorkflowStatus.REVIEWED
        
        mock_documents = [
            UploadedDocument(
                id=1,
                file_type=FileType.PDF,
                file_size_bytes=1024000,
                document_type_id=1,
                metadata=DocumentMetadata(filename="doc1.pdf", version="v1"),
                file_path=FilePath("/uploads/doc1.pdf"),
                processing_method=ProcessingMethod.OCR,
                processing_status=ProcessingStatus.COMPLETED,
                uploaded_by_user_id=1,
                uploaded_at=datetime.now(),
                workflow_status=WorkflowStatus.REVIEWED,
                pages=[],
                interest_group_ids=[1, 2]
            ),
            UploadedDocument(
                id=2,
                file_type=FileType.PDF,
                file_size_bytes=2048000,
                document_type_id=2,
                metadata=DocumentMetadata(filename="doc2.pdf", version="v1"),
                file_path=FilePath("/uploads/doc2.pdf"),
                processing_method=ProcessingMethod.OCR,
                processing_status=ProcessingStatus.COMPLETED,
                uploaded_by_user_id=1,
                uploaded_at=datetime.now(),
                workflow_status=WorkflowStatus.REVIEWED,
                pages=[],
                interest_group_ids=[3]
            )
        ]
        
        mock_repo = AsyncMock()
        mock_repo.get_by_workflow_status.return_value = mock_documents
        
        use_case = GetDocumentsByWorkflowStatusUseCase(upload_repository=mock_repo)
        
        # ACT
        result = await use_case.execute(status=status)
        
        # ASSERT
        assert len(result) == 2
        mock_repo.get_by_workflow_status.assert_called_once_with(
            status=status,
            document_type_id=None
        )
