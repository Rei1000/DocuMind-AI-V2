"""
Unit Tests für Soft Delete Entity Felder.

Test-Driven Development: RED Phase für Soft Delete Entity-Felder.
"""

import pytest
from datetime import datetime
from contexts.documentupload.domain.entities import UploadedDocument
from contexts.documentupload.domain.value_objects import (
    FileType, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus,
    WorkflowStatus
)


class TestUploadedDocumentSoftDeleteFields:
    """Tests für Soft Delete Felder in UploadedDocument."""
    
    def test_uploaded_document_soft_delete_fields(self):
        """UploadedDocument hat Soft Delete Felder"""
        # Arrange
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="1.2",
            version="v1.0"
        )
        deleted_at = datetime.utcnow()
        
        # Act
        document = UploadedDocument(
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
            deleted_at=deleted_at,  # NEU Phase 1.3
            deleted_by_user_id=1,  # NEU Phase 1.3
            deletion_reason="Test deletion"  # NEU Phase 1.3
        )
        
        # Assert
        assert document.deleted_at == deleted_at
        assert document.deleted_by_user_id == 1
        assert document.deletion_reason == "Test deletion"
    
    def test_uploaded_document_soft_delete_fields_optional(self):
        """Soft Delete Felder sind optional (Rückwärtskompatibilität)"""
        # Arrange
        metadata = DocumentMetadata(
            filename="test.pdf",
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
            processing_status=ProcessingStatus.COMPLETED,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            workflow_status=WorkflowStatus.APPROVED
            # deleted_at, deleted_by_user_id, deletion_reason nicht angegeben
        )
        
        # Assert
        assert document.deleted_at is None
        assert document.deleted_by_user_id is None
        assert document.deletion_reason is None
    
    def test_uploaded_document_is_deleted_property(self):
        """is_deleted Property prüft workflow_status"""
        # Arrange
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="1.2",
            version="v1.0"
        )
        
        # Act: Dokument mit DELETED Status
        document = UploadedDocument(
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
            workflow_status=WorkflowStatus.DELETED  # NEU Phase 1.3
        )
        
        # Assert
        assert document.is_deleted is True
        
        # Nicht gelöscht
        document.workflow_status = WorkflowStatus.APPROVED
        assert document.is_deleted is False
    
    def test_uploaded_document_is_deleted_property_other_statuses(self):
        """is_deleted Property ist False für alle anderen Status"""
        # Arrange
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="1.2",
            version="v1.0"
        )
        
        # Act & Assert: Alle anderen Status sollten is_deleted=False haben
        for status in [WorkflowStatus.DRAFT, WorkflowStatus.REVIEWED, WorkflowStatus.APPROVED, WorkflowStatus.REJECTED]:
            document = UploadedDocument(
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
                workflow_status=status
            )
            
            assert document.is_deleted is False

