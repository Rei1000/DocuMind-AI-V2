"""
Unit Tests für Workflow Entities

Testet WorkflowStatusChange, DocumentComment und erweiterte UploadedDocument.
"""

import pytest
from datetime import datetime
from contexts.documentupload.domain.entities import (
    WorkflowStatusChange, 
    DocumentComment, 
    UploadedDocument
)
from contexts.documentupload.domain.value_objects import (
    WorkflowStatus, 
    FileType, 
    ProcessingMethod, 
    ProcessingStatus,
    DocumentMetadata,
    FilePath
)


class TestWorkflowStatusChange:
    """Tests für WorkflowStatusChange Entity."""
    
    def test_create_workflow_status_change(self):
        """Test: WorkflowStatusChange erstellen mit allen Feldern."""
        timestamp = datetime.utcnow()
        
        change = WorkflowStatusChange(
            id=1,
            upload_document_id=123,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=456,
            changed_at=timestamp,
            change_reason="Teamleiter-Freigabe",
            comment="Alle Prüfpunkte erfolgreich"
        )
        
        assert change.id == 1
        assert change.upload_document_id == 123
        assert change.from_status == WorkflowStatus.DRAFT
        assert change.to_status == WorkflowStatus.REVIEWED
        assert change.changed_by_user_id == 456
        assert change.changed_at == timestamp
        assert change.change_reason == "Teamleiter-Freigabe"
        assert change.comment == "Alle Prüfpunkte erfolgreich"
    
    def test_create_workflow_status_change_without_from_status(self):
        """Test: WorkflowStatusChange ohne from_status (Initial-Upload)."""
        timestamp = datetime.utcnow()
        
        change = WorkflowStatusChange(
            id=1,
            upload_document_id=123,
            from_status=None,
            to_status=WorkflowStatus.DRAFT,
            changed_by_user_id=456,
            changed_at=timestamp,
            change_reason="Initial upload",
            comment=None
        )
        
        assert change.from_status is None
        assert change.to_status == WorkflowStatus.DRAFT
        assert change.comment is None
    
    def test_workflow_status_change_validation(self):
        """Test: WorkflowStatusChange Validierung."""
        timestamp = datetime.utcnow()
        
        # Valid change
        change = WorkflowStatusChange(
            id=1,
            upload_document_id=123,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=456,
            changed_at=timestamp,
            change_reason="Teamleiter-Freigabe",
            comment="OK"
        )
        assert change is not None
        
        # Invalid: gleicher Status
        with pytest.raises(ValueError):
            WorkflowStatusChange(
                id=1,
                upload_document_id=123,
                from_status=WorkflowStatus.DRAFT,
                to_status=WorkflowStatus.DRAFT,
                changed_by_user_id=456,
                changed_at=timestamp,
                change_reason="Invalid",
                comment=None
            )


class TestDocumentComment:
    """Tests für DocumentComment Entity."""
    
    def test_create_document_comment(self):
        """Test: DocumentComment erstellen mit allen Feldern."""
        timestamp = datetime.utcnow()
        
        comment = DocumentComment(
            id=1,
            upload_document_id=123,
            comment_text="Das Dokument ist unvollständig",
            comment_type="rejection",
            page_number=2,
            created_by_user_id=456,
            created_at=timestamp,
            status_change_id=789
        )
        
        assert comment.id == 1
        assert comment.upload_document_id == 123
        assert comment.comment_text == "Das Dokument ist unvollständig"
        assert comment.comment_type == "rejection"
        assert comment.page_number == 2
        assert comment.created_by_user_id == 456
        assert comment.created_at == timestamp
        assert comment.status_change_id == 789
    
    def test_create_document_comment_without_page_number(self):
        """Test: DocumentComment ohne page_number (allgemeiner Kommentar)."""
        timestamp = datetime.utcnow()
        
        comment = DocumentComment(
            id=1,
            upload_document_id=123,
            comment_text="Allgemeiner Kommentar",
            comment_type="general",
            page_number=None,
            created_by_user_id=456,
            created_at=timestamp,
            status_change_id=None
        )
        
        assert comment.page_number is None
        assert comment.status_change_id is None
    
    def test_document_comment_validation(self):
        """Test: DocumentComment Validierung."""
        timestamp = datetime.utcnow()
        
        # Valid comment
        comment = DocumentComment(
            id=1,
            upload_document_id=123,
            comment_text="Valid comment",
            comment_type="general",
            page_number=None,
            created_by_user_id=456,
            created_at=timestamp,
            status_change_id=None
        )
        assert comment is not None
        
        # Invalid: leerer Kommentar
        with pytest.raises(ValueError):
            DocumentComment(
                id=1,
                upload_document_id=123,
                comment_text="",
                comment_type="general",
                page_number=None,
                created_by_user_id=456,
                created_at=timestamp,
                status_change_id=None
            )
        
        # Invalid: ungültiger comment_type
        with pytest.raises(ValueError):
            DocumentComment(
                id=1,
                upload_document_id=123,
                comment_text="Valid comment",
                comment_type="invalid_type",
                page_number=None,
                created_by_user_id=456,
                created_at=timestamp,
                status_change_id=None
            )


class TestUploadedDocumentWorkflow:
    """Tests für erweiterte UploadedDocument mit Workflow-Funktionalität."""
    
    def test_uploaded_document_workflow_status(self):
        """Test: UploadedDocument hat workflow_status Property."""
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="Test Document.pdf",
            qm_chapter="5.2",
            version="v1.0"
        )
        
        document = UploadedDocument(
            id=1,
            file_type=FileType.PDF,
            file_size_bytes=1024,
            document_type_id=1,
            metadata=metadata,
            file_path=FilePath("uploads/test.pdf"),
            processing_method=ProcessingMethod.VISION,
            processing_status=ProcessingStatus.COMPLETED,
            uploaded_by_user_id=456,
            uploaded_at=datetime.utcnow(),
            pages=[],
            interest_group_ids=[1, 2]
        )
        
        # Default workflow_status sollte DRAFT sein
        assert document.workflow_status == WorkflowStatus.DRAFT
    
    def test_change_workflow_status(self):
        """Test: change_workflow_status Methode."""
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="Test Document.pdf",
            qm_chapter="5.2",
            version="v1.0"
        )
        
        document = UploadedDocument(
            id=1,
            file_type=FileType.PDF,
            file_size_bytes=1024,
            document_type_id=1,
            metadata=metadata,
            file_path=FilePath("uploads/test.pdf"),
            processing_method=ProcessingMethod.VISION,
            processing_status=ProcessingStatus.COMPLETED,
            uploaded_by_user_id=456,
            uploaded_at=datetime.utcnow(),
            pages=[],
            interest_group_ids=[1, 2]
        )
        
        # Ändere Status
        document.change_workflow_status(
            new_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=789,
            reason="Teamleiter-Freigabe",
            comment="Alle Prüfpunkte OK"
        )
        
        assert document.workflow_status == WorkflowStatus.REVIEWED
    
    def test_change_workflow_status_validation(self):
        """Test: change_workflow_status Validierung."""
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="Test Document.pdf",
            qm_chapter="5.2",
            version="v1.0"
        )
        
        document = UploadedDocument(
            id=1,
            file_type=FileType.PDF,
            file_size_bytes=1024,
            document_type_id=1,
            metadata=metadata,
            file_path=FilePath("uploads/test.pdf"),
            processing_method=ProcessingMethod.VISION,
            processing_status=ProcessingStatus.COMPLETED,
            uploaded_by_user_id=456,
            uploaded_at=datetime.utcnow(),
            pages=[],
            interest_group_ids=[1, 2]
        )
        
        # Gleicher Status sollte Fehler werfen
        with pytest.raises(ValueError):
            document.change_workflow_status(
                new_status=WorkflowStatus.DRAFT,
                changed_by_user_id=789,
                reason="Invalid",
                comment=None
            )
