"""
Tests für Failed Document Management

TDD: Tests FIRST für Sichtbarkeit und Management fehlgeschlagener Dokumente
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from contexts.documentupload.domain.entities import UploadedDocument, DocumentMetadata, FileHash
from contexts.documentupload.domain.value_objects import (
    FileType, ProcessingMethod, ProcessingStatus, WorkflowStatus
)


class TestFailedDocuments:
    """Test Failed Document Visibility and Management"""
    
    @pytest.mark.asyncio
    async def test_get_documents_includes_failed_status(self):
        """
        GIVEN: Repository mit Dokumenten in verschiedenen Status
        WHEN: get_all() aufgerufen
        THEN: Dokumente mit processing_status='failed' sind enthalten
        """
        # Arrange
        from contexts.documentupload.infrastructure.repositories import SQLAlchemyUploadRepository
        from backend.app.models import UploadDocumentModel
        
        mock_db = MagicMock()
        
        # Simuliere DB-Query Result
        failed_doc_model = UploadDocumentModel(
            id=1,
            filename="test.pdf",
            original_filename="test.pdf",
            file_size_bytes=1000,
            file_type="pdf",
            document_type_id=1,
            qm_chapter="1",
            version="v1",
            page_count=1,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_path="/test/test.pdf",
            processing_method="vision",
            processing_status="failed",  # FAILED!
            workflow_status="draft",
            file_hash="abc123",
            is_duplicate=False,
            duplicate_of_document_id=None,
            document_series_id=None,
            parent_document_id=None,
            is_current_version=True,
            deleted_at=None,
            deleted_by_user_id=None,
            deletion_reason=None,
            archived_at=None,
            archived_by_user_id=None,
            archive_reason=None
        )
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [failed_doc_model]
        
        mock_db.query.return_value = mock_query
        
        repository = SQLAlchemyUploadRepository(mock_db)
        
        # Act
        documents = await repository.get_all()
        
        # Assert
        assert len(documents) == 1
        assert documents[0].processing_status == ProcessingStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_failed_document_has_error_information(self):
        """
        GIVEN: Fehlgeschlagenes Dokument
        WHEN: AIProcessingResult für dieses Dokument geladen
        THEN: Error-Message und Status sind verfügbar
        """
        # Arrange
        from contexts.documentupload.infrastructure.repositories import SQLAlchemyAIResponseRepository
        from backend.app.models import AIResponseModel
        
        mock_db = MagicMock()
        
        failed_ai_response = AIResponseModel(
            id=1,
            upload_document_id=1,
            upload_document_page_id=1,
            prompt_template_id=1,
            ai_model_id="gemini-2.5-flash",
            model_name="gemini-2.5-flash",
            json_response="{}",
            processing_status="failed",
            tokens_sent=100,
            tokens_received=0,
            total_tokens=100,
            response_time_ms=500,
            error_message="Content blocked by safety filters",
            processed_at=datetime.utcnow()
        )
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [failed_ai_response]
        
        mock_db.query.return_value = mock_query
        
        repository = SQLAlchemyAIResponseRepository(mock_db)
        
        # Act
        results = await repository.get_by_document_id(1)
        
        # Assert
        assert len(results) == 1
        assert results[0].processing_status == "failed"
        assert results[0].error_message == "Content blocked by safety filters"
        assert "safety filter" in results[0].error_message.lower()
    
    @pytest.mark.asyncio
    async def test_retry_use_case_reprocesses_failed_pages(self):
        """
        GIVEN: Dokument mit fehlgeschlagenen Seiten
        WHEN: RetryDocumentProcessingUseCase.execute()
        THEN: Alle fehlgeschlagenen Seiten werden neu verarbeitet
        """
        # Dieser Test wird die Implementierung des RetryDocumentProcessingUseCase leiten
        # Zunächst nur Structure-Test
        
        # TODO: Implementierung folgt nach Use Case erstellt wurde
        pass
    
    def test_processing_status_enum_has_failed_state(self):
        """
        GIVEN: ProcessingStatus Enum
        WHEN: Zugriff auf FAILED-Status
        THEN: Status existiert und ist verwendbar
        """
        from contexts.documentupload.domain.value_objects import ProcessingStatus
        
        # Assert
        assert hasattr(ProcessingStatus, 'FAILED')
        assert ProcessingStatus.FAILED.value == "failed"
    
    def test_document_entity_can_be_marked_as_failed(self):
        """
        GIVEN: UploadedDocument Entity
        WHEN: processing_status auf FAILED gesetzt
        THEN: Entity bleibt valide
        """
        # Arrange & Act
        document = UploadedDocument(
            id=1,
            metadata=DocumentMetadata(
                filename="test.pdf",
                original_filename="test.pdf",
                qm_chapter="1",
                version="v1"
            ),
            file_size_bytes=1000,
            file_type=FileType.PDF,
            document_type_id=1,
            page_count=1,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_path="/test/test.pdf",
            processing_method=ProcessingMethod.VISION,
            processing_status=ProcessingStatus.FAILED,  # FAILED!
            workflow_status=WorkflowStatus.DRAFT,
            file_hash=FileHash("abc123"),
            is_duplicate=False,
            duplicate_of_document_id=None,
            document_series_id=None,
            parent_document_id=None,
            is_current_version=True,
            deleted_at=None,
            deleted_by_user_id=None,
            deletion_reason=None,
            archived_at=None,
            archived_by_user_id=None,
            archive_reason=None
        )
        
        # Assert
        assert document.processing_status == ProcessingStatus.FAILED
        assert document.workflow_status == WorkflowStatus.DRAFT

