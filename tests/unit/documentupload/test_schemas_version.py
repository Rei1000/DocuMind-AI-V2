"""
Unit Tests für UploadedDocumentSchema - Version-Felder.

Test-Driven Development: RED Phase für Schema Extension mit Version-Feldern.
"""

import pytest
from datetime import datetime
from contexts.documentupload.interface.schemas import UploadedDocumentSchema


class TestUploadedDocumentSchemaVersionFields:
    """Tests für UploadedDocumentSchema mit Version-Feldern."""
    
    def test_schema_includes_version_fields(self):
        """UploadedDocumentSchema enthält Version-Felder"""
        # Arrange & Act
        schema = UploadedDocumentSchema(
            id=1,
            filename="test_v1.0.pdf",
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
            document_series_id=100,  # NEU
            parent_document_id=None,  # NEU
            is_current_version=True  # NEU
        )
        
        # Assert
        assert schema.document_series_id == 100
        assert schema.parent_document_id is None
        assert schema.is_current_version is True
    
    def test_schema_child_version_fields(self):
        """UploadedDocumentSchema hat korrekte Version-Felder für Child-Version"""
        # Arrange & Act
        schema = UploadedDocumentSchema(
            id=2,
            filename="test_v2.0.pdf",
            original_filename="test.pdf",
            file_type="pdf",
            file_size_bytes=2048,
            document_type_id=1,
            qm_chapter="1.2",
            version="v2.0",
            file_path="data/uploads/test_v2.pdf",
            processing_method="ocr",
            processing_status="pending",
            workflow_status="draft",
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            page_count=0,
            document_series_id=100,  # NEU: Gleiche Serie
            parent_document_id=1,  # NEU: Parent = v1.0
            is_current_version=True  # NEU: Aktuelle Version
        )
        
        # Assert
        assert schema.document_series_id == 100
        assert schema.parent_document_id == 1
        assert schema.is_current_version is True
    
    def test_schema_archived_version_fields(self):
        """UploadedDocumentSchema hat korrekte Version-Felder für archivierte Version"""
        # Arrange & Act
        schema = UploadedDocumentSchema(
            id=1,
            filename="test_v1.0.pdf",
            original_filename="test.pdf",
            file_type="pdf",
            file_size_bytes=1024,
            document_type_id=1,
            qm_chapter="1.2",
            version="v1.0",
            file_path="data/uploads/test.pdf",
            processing_method="ocr",
            processing_status="completed",
            workflow_status="approved",
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            page_count=10,
            document_series_id=100,
            parent_document_id=None,
            is_current_version=False  # NEU: Nicht mehr aktuell
        )
        
        # Assert
        assert schema.document_series_id == 100
        assert schema.is_current_version is False
    
    def test_schema_version_fields_optional(self):
        """Version-Felder sind optional für Rückwärtskompatibilität"""
        # Arrange & Act (ohne Version-Felder)
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
            # Version-Felder nicht angegeben
        )
        
        # Assert: Default-Werte
        assert schema.document_series_id is None
        assert schema.parent_document_id is None
        assert schema.is_current_version is True  # Default: True

