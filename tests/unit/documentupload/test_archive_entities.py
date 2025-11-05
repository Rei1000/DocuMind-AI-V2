"""
Unit Tests für Archive Entity Felder.

Test-Driven Development: RED Phase für Archive Entity-Felder.
"""

import pytest
from datetime import datetime
from contexts.documentupload.domain.entities import UploadedDocument
from contexts.documentupload.domain.value_objects import (
    FileType, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus,
    WorkflowStatus
)


class TestUploadedDocumentArchiveFields:
    """Tests für Archive Felder in UploadedDocument."""
    
    def test_uploaded_document_archive_fields(self):
        """UploadedDocument hat Archive Felder"""
        # Arrange
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="1.2",
            version="v1.0"
        )
        archived_at = datetime.utcnow()
        
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
            archived_at=archived_at,  # NEU Phase 1.4
            archived_by_user_id=1,  # NEU Phase 1.4
            archive_reason="Old version"  # NEU Phase 1.4
        )
        
        # Assert
        assert document.archived_at == archived_at
        assert document.archived_by_user_id == 1
        assert document.archive_reason == "Old version"
    
    def test_uploaded_document_archive_fields_optional(self):
        """Archive Felder sind optional (Rückwärtskompatibilität)"""
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
            # archived_at, archived_by_user_id, archive_reason nicht angegeben
        )
        
        # Assert
        assert document.archived_at is None
        assert document.archived_by_user_id is None
        assert document.archive_reason is None
    
    def test_uploaded_document_is_archived_property(self):
        """is_archived Property prüft workflow_status"""
        # Arrange
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="1.2",
            version="v1.0"
        )
        
        # Act: Dokument mit ARCHIVED Status
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
            workflow_status=WorkflowStatus.ARCHIVED  # NEU Phase 1.4
        )
        
        # Assert
        assert document.is_archived is True
        
        # Nicht archiviert
        document.workflow_status = WorkflowStatus.APPROVED
        assert document.is_archived is False
    
    def test_uploaded_document_is_archived_property_other_statuses(self):
        """is_archived Property ist False für alle anderen Status"""
        # Arrange
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="1.2",
            version="v1.0"
        )
        
        # Act & Assert: Alle anderen Status sollten is_archived=False haben
        for status in [WorkflowStatus.DRAFT, WorkflowStatus.REVIEWED, WorkflowStatus.APPROVED, WorkflowStatus.REJECTED, WorkflowStatus.DELETED]:
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
            
            assert document.is_archived is False

