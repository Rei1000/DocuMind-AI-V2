"""
Unit Tests für Archive API Schemas.

Test-Driven Development: RED Phase für Archive Schema-Tests.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from contexts.documentupload.interface.schemas import (
    UploadedDocumentSchema,
    ArchiveDocumentRequest,
    ArchiveDocumentResponse
)


class TestUploadedDocumentSchemaArchiveFields:
    """Tests für Archive Felder in UploadedDocumentSchema."""
    
    def test_uploaded_document_schema_includes_archive_fields(self):
        """UploadedDocumentSchema hat Archive Felder"""
        # Arrange & Act
        schema = UploadedDocumentSchema(
            id=1,
            filename="test.pdf",
            original_filename="test.pdf",
            file_type="pdf",
            file_size_bytes=1024,
            document_type_id=1,
            qm_chapter="1.2",
            version="v1.0",
            page_count=1,
            file_path="data/uploads/test.pdf",
            processing_method="ocr",
            processing_status="completed",
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            workflow_status="approved",
            archived_at=datetime.utcnow(),  # NEU Phase 1.4
            archived_by_user_id=1,  # NEU Phase 1.4
            archive_reason="Old version"  # NEU Phase 1.4
        )
        
        # Assert
        assert schema.archived_at is not None
        assert schema.archived_by_user_id == 1
        assert schema.archive_reason == "Old version"
    
    def test_uploaded_document_schema_archive_fields_optional(self):
        """Archive Felder sind optional in UploadedDocumentSchema"""
        # Arrange & Act
        schema = UploadedDocumentSchema(
            id=1,
            filename="test.pdf",
            original_filename="test.pdf",
            file_type="pdf",
            file_size_bytes=1024,
            document_type_id=1,
            qm_chapter="1.2",
            version="v1.0",
            page_count=1,
            file_path="data/uploads/test.pdf",
            processing_method="ocr",
            processing_status="completed",
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            workflow_status="approved"
            # archived_at, archived_by_user_id, archive_reason nicht angegeben
        )
        
        # Assert
        assert schema.archived_at is None
        assert schema.archived_by_user_id is None
        assert schema.archive_reason is None


class TestArchiveDocumentRequest:
    """Tests für ArchiveDocumentRequest Schema."""
    
    def test_archive_document_request_valid(self):
        """ArchiveDocumentRequest mit gültigen Daten"""
        # Arrange & Act
        request = ArchiveDocumentRequest(
            document_id=1,
            archive_reason="Old version"
        )
        
        # Assert
        assert request.document_id == 1
        assert request.archive_reason == "Old version"
    
    def test_archive_document_request_empty_reason_allowed(self):
        """ArchiveDocumentRequest erlaubt leeren reason (optional im Gegensatz zu Soft Delete)"""
        # Arrange & Act
        request = ArchiveDocumentRequest(
            document_id=1,
            archive_reason=""  # Leer erlaubt für Archive
        )
        
        # Assert
        assert request.document_id == 1
        assert request.archive_reason == ""
    
    def test_archive_document_request_missing_document_id_raises_error(self):
        """ArchiveDocumentRequest ohne document_id wirft Fehler"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ArchiveDocumentRequest(
                archive_reason="Old version"
                # document_id fehlt
            )


class TestArchiveDocumentResponse:
    """Tests für ArchiveDocumentResponse Schema."""
    
    def test_archive_document_response_valid(self):
        """ArchiveDocumentResponse mit gültigen Daten"""
        # Arrange & Act
        response = ArchiveDocumentResponse(
            success=True,
            message="Document archived successfully",
            document_id=1,
            new_status="archived",
            archived_by="Test User",
            archived_at=datetime.utcnow()
        )
        
        # Assert
        assert response.success is True
        assert response.message == "Document archived successfully"
        assert response.document_id == 1
        assert response.new_status == "archived"
        assert response.archived_by == "Test User"
        assert response.archived_at is not None

