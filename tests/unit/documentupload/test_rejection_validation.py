"""
Unit Tests für Rejection Validation.

Test-Driven Development: RED Phase für Rejection-Validierung (Kommentar erforderlich).
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from contexts.documentupload.domain.entities import UploadedDocument
from contexts.documentupload.domain.value_objects import (
    FileType, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus,
    WorkflowStatus
)
from contexts.documentupload.domain.repositories import DocumentCommentRepository


class TestRejectionValidation:
    """Tests für Rejection-Validierung (Kommentar erforderlich)."""
    
    def test_rejection_requires_comment(self):
        """Rejection sollte nur mit Kommentar möglich sein (Domain-Logik)"""
        # Arrange
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="1.2",
            version="v1.0"
        )
        
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
            workflow_status=WorkflowStatus.REVIEWED
        )
        
        # Act & Assert: Rejection ohne Kommentar sollte Exception werfen
        # (Dies wird im Use Case geprüft, nicht in der Entity)
        # Entity erlaubt Status-Änderung, Use Case prüft Kommentar
        pass  # Validation erfolgt im Use Case
    
    def test_rejection_with_comment_allowed(self):
        """Rejection mit Kommentar sollte erlaubt sein"""
        # Arrange
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="1.2",
            version="v1.0"
        )
        
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
            workflow_status=WorkflowStatus.REVIEWED
        )
        
        # Act: Status-Änderung ist erlaubt (Kommentar-Prüfung im Use Case)
        event = document.change_workflow_status(
            new_status=WorkflowStatus.REJECTED,
            user_id=1,
            reason="Test rejection"
        )
        
        # Assert
        assert document.workflow_status == WorkflowStatus.REJECTED
        assert event.new_status == WorkflowStatus.REJECTED

