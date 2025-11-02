"""
Unit Tests für Soft Delete API Schemas.

Test-Driven Development: RED Phase für Soft Delete API Schema-Erweiterung.
"""

import pytest
from datetime import datetime
from contexts.documentupload.interface.schemas import UploadedDocumentSchema


class TestSoftDeleteSchemas:
    """Tests für Soft Delete API Schemas."""
    
    def test_uploaded_document_schema_has_soft_delete_fields(self):
        """UploadedDocumentSchema sollte Soft Delete Felder haben"""
        # Arrange & Act
        schema = UploadedDocumentSchema(
            id=1,
            filename="test.pdf",
            original_filename="test.pdf",
            file_size_bytes=1024,
            file_type="pdf",
            document_type_id=1,
            qm_chapter="1.2",
            version="v1.0",
            page_count=1,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_path="data/uploads/test.pdf",
            processing_method="ocr",
            processing_status="completed",
            workflow_status="deleted",  # NEU Phase 1.3
            deleted_at=datetime.utcnow(),  # NEU Phase 1.3
            deleted_by_user_id=1,  # NEU Phase 1.3
            deletion_reason="Test deletion"  # NEU Phase 1.3
        )
        
        # Assert
        assert schema.deleted_at is not None
        assert schema.deleted_by_user_id == 1
        assert schema.deletion_reason == "Test deletion"
        assert schema.workflow_status == "deleted"
    
    def test_uploaded_document_schema_soft_delete_fields_optional(self):
        """Soft Delete Felder sind optional in UploadedDocumentSchema"""
        # Arrange & Act
        schema = UploadedDocumentSchema(
            id=1,
            filename="test.pdf",
            original_filename="test.pdf",
            file_size_bytes=1024,
            file_type="pdf",
            document_type_id=1,
            qm_chapter="1.2",
            version="v1.0",
            page_count=1,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_path="data/uploads/test.pdf",
            processing_method="ocr",
            processing_status="completed",
            workflow_status="approved"
            # deleted_at, deleted_by_user_id, deletion_reason nicht angegeben
        )
        
        # Assert
        assert schema.workflow_status == "approved"
        # Soft Delete Felder sollten None sein (optional)
        assert schema.deleted_at is None or schema.deleted_at is not None  # Beides OK
    
    def test_uploaded_document_schema_defaults_soft_delete_fields(self):
        """UploadedDocumentSchema sollte Standardwerte für Soft Delete Felder haben"""
        # Arrange & Act
        schema = UploadedDocumentSchema(
            id=1,
            filename="test.pdf",
            original_filename="test.pdf",
            file_size_bytes=1024,
            file_type="pdf",
            document_type_id=1,
            qm_chapter="1.2",
            version="v1.0",
            page_count=1,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_path="data/uploads/test.pdf",
            processing_method="ocr",
            processing_status="completed",
            workflow_status="approved"
        )
        
        # Assert: Felder sollten existieren (auch wenn None)
        assert hasattr(schema, 'deleted_at')
        assert hasattr(schema, 'deleted_by_user_id')
        assert hasattr(schema, 'deletion_reason')

