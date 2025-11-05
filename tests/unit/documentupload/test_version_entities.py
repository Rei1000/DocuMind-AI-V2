"""
Unit Tests für Document Versioning - Entities.

Test-Driven Development: RED Phase für Document Series und Version Relationships.
"""

import pytest
from datetime import datetime
from contexts.documentupload.domain.entities import UploadedDocument
from contexts.documentupload.domain.value_objects import (
    FileType, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus,
    WorkflowStatus, FileHash
)


class TestDocumentVersionRelationships:
    """Tests für Document Version Relationships."""
    
    def test_uploaded_document_has_version_fields(self):
        """UploadedDocument hat Felder für Versionierung"""
        # Arrange
        metadata = DocumentMetadata(
            filename="test_v1.0.pdf",
            original_filename="test.pdf",
            qm_chapter="1.2",
            version="v1.0"
        )
        
        # Act
        document = UploadedDocument(
            id=1,
            file_type=FileType.PDF,
            file_size_bytes=1024,
            document_type_id=1,
            metadata=metadata,
            file_path=FilePath("data/uploads/test.pdf"),
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.PENDING,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            document_series_id=100,  # NEU
            parent_document_id=None,  # NEU: Erste Version
            is_current_version=True  # NEU
        )
        
        # Assert
        assert document.document_series_id == 100
        assert document.parent_document_id is None
        assert document.is_current_version is True
    
    def test_uploaded_document_child_version(self):
        """UploadedDocument kann als Child-Version erstellt werden"""
        # Arrange
        metadata = DocumentMetadata(
            filename="test_v2.0.pdf",
            original_filename="test.pdf",
            qm_chapter="1.2",
            version="v2.0"
        )
        
        # Act: Neue Version (v2.0) mit Parent (v1.0)
        child_document = UploadedDocument(
            id=2,
            file_type=FileType.PDF,
            file_size_bytes=2048,
            document_type_id=1,
            metadata=metadata,
            file_path=FilePath("data/uploads/test_v2.pdf"),
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.PENDING,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            document_series_id=100,  # Gleiche Serie
            parent_document_id=1,  # NEU: Parent = v1.0
            is_current_version=True  # NEU: Neue Version ist aktuell
        )
        
        # Assert
        assert child_document.document_series_id == 100
        assert child_document.parent_document_id == 1
        assert child_document.is_current_version is True
    
    def test_uploaded_document_archived_version(self):
        """UploadedDocument kann als archivierte Version markiert werden"""
        # Arrange
        metadata = DocumentMetadata(
            filename="test_v1.0.pdf",
            original_filename="test.pdf",
            qm_chapter="1.2",
            version="v1.0"
        )
        
        # Act: Alte Version (nach Upload von v2.0)
        archived_document = UploadedDocument(
            id=1,
            file_type=FileType.PDF,
            file_size_bytes=1024,
            document_type_id=1,
            metadata=metadata,
            file_path=FilePath("data/uploads/test.pdf"),
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.COMPLETED,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            workflow_status=WorkflowStatus.APPROVED,
            document_series_id=100,
            parent_document_id=None,
            is_current_version=False  # NEU: Nicht mehr aktuell
        )
        
        # Assert
        assert archived_document.document_series_id == 100
        assert archived_document.is_current_version is False

