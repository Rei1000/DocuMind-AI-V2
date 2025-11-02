"""
Unit Tests für Schemas mit File Hash Support.

Test-Driven Development: RED Phase für file_hash Feld in UploadedDocumentSchema.
"""

import pytest
from datetime import datetime
from contexts.documentupload.interface.schemas import UploadedDocumentSchema


class TestUploadedDocumentSchemaFileHash:
    """Tests für UploadedDocumentSchema mit FileHash Feld."""
    
    def test_uploaded_document_schema_includes_file_hash(self):
        """UploadedDocumentSchema enthält file_hash Feld"""
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
            file_path="data/uploads/test.pdf",
            processing_method="ocr",
            processing_status="pending",
            workflow_status="draft",
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            page_count=0,
            file_hash="a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
            is_duplicate=False,
            duplicate_of_document_id=None
        )
        
        # Assert
        assert schema.file_hash == "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
        assert schema.is_duplicate is False
        assert schema.duplicate_of_document_id is None
    
    def test_uploaded_document_schema_file_hash_optional(self):
        """file_hash ist optional in UploadedDocumentSchema"""
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
            file_path="data/uploads/test.pdf",
            processing_method="ocr",
            processing_status="pending",
            workflow_status="draft",
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            page_count=0,
            file_hash=None  # Optional
        )
        
        # Assert
        assert schema.file_hash is None
    
    def test_uploaded_document_schema_is_duplicate_field(self):
        """UploadedDocumentSchema hat is_duplicate Feld"""
        # Arrange & Act
        schema = UploadedDocumentSchema(
            id=2,
            filename="duplicate.pdf",
            original_filename="duplicate.pdf",
            file_type="pdf",
            file_size_bytes=1024,
            document_type_id=1,
            qm_chapter="1.2",
            version="v1.0",
            file_path="data/uploads/duplicate.pdf",
            processing_method="ocr",
            processing_status="pending",
            workflow_status="draft",
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            page_count=0,
            is_duplicate=True,
            duplicate_of_document_id=1
        )
        
        # Assert
        assert schema.is_duplicate is True
        assert schema.duplicate_of_document_id == 1
    
    def test_uploaded_document_schema_default_values(self):
        """UploadedDocumentSchema hat Default-Werte für neue Felder"""
        # Arrange & Act (ohne file_hash, is_duplicate, duplicate_of_document_id)
        schema = UploadedDocumentSchema(
            id=1,
            filename="test.pdf",
            original_filename="test.pdf",
            file_type="pdf",
            file_size_bytes=1024,
            document_type_id=1,
            qm_chapter="1.2",
            version="v1.0",
            file_path="data/uploads/test.pdf",
            processing_method="ocr",
            processing_status="pending",
            workflow_status="draft",
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            page_count=0
            # file_hash, is_duplicate, duplicate_of_document_id nicht angegeben
        )
        
        # Assert
        assert schema.file_hash is None or schema.file_hash is None  # Optional
        assert schema.is_duplicate is False  # Default False
        assert schema.duplicate_of_document_id is None  # Default None

