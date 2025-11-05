"""
Unit Tests für Workflow Domain Entities.

Tests für WorkflowStatusChange, DocumentComment und erweiterte UploadedDocument.
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
    DocumentMetadata, 
    FileHash,
    FileType,
    FilePath,
    ProcessingMethod,
    ProcessingStatus
)
from contexts.documentupload.domain.events import DocumentWorkflowChangedEvent


class TestWorkflowStatusChange:
    """Tests für WorkflowStatusChange Entity."""
    
    def test_workflow_status_change_creation(self):
        """Test Erstellung einer WorkflowStatusChange."""
        change = WorkflowStatusChange(
            id=1,
            document_id=1,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=1,
            reason="Reviewed successfully"
        )
        
        assert change.id == 1
        assert change.document_id == 1
        assert change.from_status == WorkflowStatus.DRAFT
        assert change.to_status == WorkflowStatus.REVIEWED
        assert change.changed_by_user_id == 1
        assert change.reason == "Reviewed successfully"
        assert isinstance(change.created_at, datetime)
    
    def test_workflow_status_change_validation(self):
        """Test Validierung von WorkflowStatusChange."""
        # Gültige Werte
        change = WorkflowStatusChange(
            id=1,
            document_id=1,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=1,
            reason="Valid reason"
        )
        assert change.id == 1
        
        # Ungültige ID
        with pytest.raises(ValueError):
            WorkflowStatusChange(
                id=-1,  # Ungültig (negative ID)
                document_id=1,
                from_status=WorkflowStatus.DRAFT,
                to_status=WorkflowStatus.REVIEWED,
                changed_by_user_id=1,
                reason="Test"
            )
        
        # Ungültige document_id
        with pytest.raises(ValueError):
            WorkflowStatusChange(
                id=1,
                document_id=0,  # Ungültig
                from_status=WorkflowStatus.DRAFT,
                to_status=WorkflowStatus.REVIEWED,
                changed_by_user_id=1,
                reason="Test"
            )
        
        # Ungültige user_id
        with pytest.raises(ValueError):
            WorkflowStatusChange(
                id=1,
                document_id=1,
                from_status=WorkflowStatus.DRAFT,
                to_status=WorkflowStatus.REVIEWED,
                changed_by_user_id=0,  # Ungültig
                reason="Test"
            )
        
        # Leerer Grund
        with pytest.raises(ValueError):
            WorkflowStatusChange(
                id=1,
                document_id=1,
                from_status=WorkflowStatus.DRAFT,
                to_status=WorkflowStatus.REVIEWED,
                changed_by_user_id=1,
                reason=""  # Leer
            )
    
    def test_workflow_status_change_different_statuses(self):
        """Test WorkflowStatusChange mit verschiedenen Status-Kombinationen."""
        # Draft → Reviewed
        draft_to_reviewed = WorkflowStatusChange(
            id=1,
            document_id=1,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=2,
            reason="Reviewed by level 3 user"
        )
        assert draft_to_reviewed.from_status == WorkflowStatus.DRAFT
        assert draft_to_reviewed.to_status == WorkflowStatus.REVIEWED
        
        # Reviewed → Approved
        reviewed_to_approved = WorkflowStatusChange(
            id=2,
            document_id=1,
            from_status=WorkflowStatus.REVIEWED,
            to_status=WorkflowStatus.APPROVED,
            changed_by_user_id=1,
            reason="Approved by admin"
        )
        assert reviewed_to_approved.from_status == WorkflowStatus.REVIEWED
        assert reviewed_to_approved.to_status == WorkflowStatus.APPROVED


class TestDocumentComment:
    """Tests für DocumentComment Entity."""
    
    def test_document_comment_creation(self):
        """Test Erstellung eines DocumentComment."""
        comment = DocumentComment(
            id=1,
            document_id=1,
            user_id=1,
            comment_text="Needs revision",
            comment_type="review"
        )
        
        assert comment.id == 1
        assert comment.document_id == 1
        assert comment.user_id == 1
        assert comment.comment_text == "Needs revision"
        assert comment.comment_type == "review"
        assert isinstance(comment.created_at, datetime)
    
    def test_document_comment_validation(self):
        """Test Validierung von DocumentComment."""
        # Gültige Werte
        comment = DocumentComment(
            id=1,
            document_id=1,
            user_id=1,
            comment_text="Valid comment",
            comment_type="general"
        )
        assert comment.id == 1
        
        # Ungültige ID
        with pytest.raises(ValueError):
            DocumentComment(
                id=-1,  # Ungültig (negative ID)
                document_id=1,
                user_id=1,
                comment_text="Test",
                comment_type="general"
            )
        
        # Ungültige document_id
        with pytest.raises(ValueError):
            DocumentComment(
                id=1,
                document_id=0,  # Ungültig
                user_id=1,
                comment_text="Test",
                comment_type="general"
            )
        
        # Ungültige user_id
        with pytest.raises(ValueError):
            DocumentComment(
                id=1,
                document_id=1,
                user_id=0,  # Ungültig
                comment_text="Test",
                comment_type="general"
            )
        
        # Leerer Kommentar
        with pytest.raises(ValueError):
            DocumentComment(
                id=1,
                document_id=1,
                user_id=1,
                comment_text="",  # Leer
                comment_type="general"
            )
        
        # Leerer Typ
        with pytest.raises(ValueError):
            DocumentComment(
                id=1,
                document_id=1,
                user_id=1,
                comment_text="Test",
                comment_type=""  # Leer
            )
    
    def test_document_comment_types(self):
        """Test verschiedene Comment-Typen."""
        comment_types = ["general", "review", "approval", "rejection"]
        
        for comment_type in comment_types:
            comment = DocumentComment(
                id=1,
                document_id=1,
                user_id=1,
                comment_text=f"Comment of type {comment_type}",
                comment_type=comment_type
            )
            assert comment.comment_type == comment_type


class TestUploadedDocumentFileHash:
    """Tests für UploadedDocument mit FileHash."""
    
    def test_uploaded_document_with_file_hash(self):
        """UploadedDocument kann mit FileHash erstellt werden"""
        # Arrange
        file_hash = FileHash("a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3")
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
            processing_status=ProcessingStatus.PENDING,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_hash=file_hash
        )
        
        # Assert
        assert document.file_hash is not None
        assert document.file_hash.value == file_hash.value
        assert document.file_hash.value == "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
    
    def test_uploaded_document_file_hash_optional(self):
        """FileHash ist optional für Rückwärtskompatibilität"""
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
            processing_status=ProcessingStatus.PENDING,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_hash=None  # Optional
        )
        
        # Assert
        assert document.file_hash is None
    
    def test_uploaded_document_file_hash_default_none(self):
        """FileHash hat Default None"""
        # Arrange
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="1.2",
            version="v1.0"
        )
        
        # Act (file_hash nicht angegeben)
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
            uploaded_at=datetime.utcnow()
            # file_hash nicht angegeben → sollte None sein
        )
        
        # Assert
        assert document.file_hash is None
    
    def test_uploaded_document_duplicate_fields(self):
        """UploadedDocument hat is_duplicate und duplicate_of_document_id Felder"""
        # Arrange
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="1.2",
            version="v1.0"
        )
        
        # Act
        document = UploadedDocument(
            id=2,
            file_type=FileType.PDF,
            file_size_bytes=1024,
            document_type_id=1,
            metadata=metadata,
            file_path=FilePath("data/uploads/test.pdf"),
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.PENDING,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            is_duplicate=True,
            duplicate_of_document_id=1
        )
        
        # Assert
        assert document.is_duplicate is True
        assert document.duplicate_of_document_id == 1


class TestUploadedDocumentWorkflow:
    """Tests für erweiterte UploadedDocument mit Workflow-Funktionalität."""
    
    def test_uploaded_document_workflow_status_default(self):
        """Test dass UploadedDocument standardmäßig DRAFT Status hat."""
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="5.2",
            version="v1.0.0"
        )
        
        document = UploadedDocument(
            id=1,
            metadata=metadata,
            file_size_bytes=1024,
            file_type="pdf",
            document_type_id=1,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_path="uploads/test.pdf",
            processing_method="ocr",
            processing_status="completed"
        )
        
        assert document.workflow_status == WorkflowStatus.DRAFT
    
    def test_uploaded_document_change_workflow_status(self):
        """Test change_workflow_status Methode."""
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="5.2",
            version="v1.0.0"
        )
        
        document = UploadedDocument(
            id=1,
            metadata=metadata,
            file_size_bytes=1024,
            file_type="pdf",
            document_type_id=1,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_path="uploads/test.pdf",
            processing_method="ocr",
            processing_status="completed"
        )
        
        # Ändere Status
        event = document.change_workflow_status(
            new_status=WorkflowStatus.REVIEWED,
            user_id=2,
            reason="Reviewed by level 3 user"
        )
        
        # Prüfe dass Status geändert wurde
        assert document.workflow_status == WorkflowStatus.REVIEWED
        
        # Prüfe dass Event korrekt erstellt wurde
        assert isinstance(event, DocumentWorkflowChangedEvent)
        assert event.document_id == 1
        assert event.old_status == WorkflowStatus.DRAFT
        assert event.new_status == WorkflowStatus.REVIEWED
        assert event.changed_by_user_id == 2
        assert event.reason == "Reviewed by level 3 user"
    
    def test_uploaded_document_multiple_status_changes(self):
        """Test mehrere Status-Änderungen."""
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="5.2",
            version="v1.0.0"
        )
        
        document = UploadedDocument(
            id=1,
            metadata=metadata,
            file_size_bytes=1024,
            file_type="pdf",
            document_type_id=1,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_path="uploads/test.pdf",
            processing_method="ocr",
            processing_status="completed"
        )
        
        # Draft → Reviewed
        event1 = document.change_workflow_status(
            new_status=WorkflowStatus.REVIEWED,
            user_id=2,
            reason="Reviewed"
        )
        assert document.workflow_status == WorkflowStatus.REVIEWED
        assert event1.old_status == WorkflowStatus.DRAFT
        assert event1.new_status == WorkflowStatus.REVIEWED
        
        # Reviewed → Approved
        event2 = document.change_workflow_status(
            new_status=WorkflowStatus.APPROVED,
            user_id=1,
            reason="Approved by admin"
        )
        assert document.workflow_status == WorkflowStatus.APPROVED
        assert event2.old_status == WorkflowStatus.REVIEWED
        assert event2.new_status == WorkflowStatus.APPROVED
    
    def test_uploaded_document_workflow_validation(self):
        """Test Validierung bei Workflow-Status-Änderung."""
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="5.2",
            version="v1.0.0"
        )
        
        document = UploadedDocument(
            id=1,
            metadata=metadata,
            file_size_bytes=1024,
            file_type="pdf",
            document_type_id=1,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            file_path="uploads/test.pdf",
            processing_method="ocr",
            processing_status="completed"
        )
        
        # Ungültige user_id
        with pytest.raises(ValueError):
            document.change_workflow_status(
                new_status=WorkflowStatus.REVIEWED,
                user_id=0,  # Ungültig
                reason="Test"
            )
        
        # Leerer Grund
        with pytest.raises(ValueError):
            document.change_workflow_status(
                new_status=WorkflowStatus.REVIEWED,
                user_id=1,
                reason=""  # Leer
            )
        
        # Gleicher Status
        with pytest.raises(ValueError):
            document.change_workflow_status(
                new_status=WorkflowStatus.DRAFT,  # Gleicher Status
                user_id=1,
                reason="Test"
            )
