"""
Unit Tests für Change Workflow Status Use Case

Testet ChangeDocumentWorkflowStatusUseCase mit Permission-Checks.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from contexts.documentupload.application.use_cases import ChangeDocumentWorkflowStatusUseCase
from contexts.documentupload.domain.entities import (
    UploadedDocument, 
    WorkflowStatusChange, 
    DocumentComment
)
from contexts.documentupload.domain.value_objects import (
    WorkflowStatus, 
    FileType, 
    ProcessingMethod, 
    ProcessingStatus,
    DocumentMetadata,
    FilePath
)


class TestChangeDocumentWorkflowStatusUseCase:
    """Tests für ChangeDocumentWorkflowStatusUseCase."""
    
    @pytest.mark.asyncio
    async def test_successful_status_change_with_audit_trail(self):
        """Test: Erfolgreiche Status-Änderung mit Audit Trail."""
        # Arrange
        mock_upload_repo = AsyncMock()
        mock_workflow_history_repo = AsyncMock()
        mock_comment_repo = AsyncMock()
        mock_permission_service = Mock()
        mock_event_publisher = Mock()
        
        # Mock Permission Service
        mock_permission_service.can_change_status.return_value = True
        mock_permission_service.get_user_level.return_value = 3
        
        # Mock Document
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
            interest_group_ids=[1, 2],
            workflow_status=WorkflowStatus.DRAFT
        )
        
        mock_upload_repo.get_by_id.return_value = document
        mock_upload_repo.save.return_value = document
        
        # Mock WorkflowStatusChange
        status_change = WorkflowStatusChange(
            id=1,
            upload_document_id=1,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=789,
            changed_at=datetime.utcnow(),
            change_reason="Teamleiter-Freigabe",
            comment="Alle Prüfpunkte OK"
        )
        mock_workflow_history_repo.save.return_value = status_change
        
        # Mock DocumentComment
        comment = DocumentComment(
            id=1,
            upload_document_id=1,
            comment_text="Alle Prüfpunkte OK",
            comment_type="review",
            page_number=None,
            created_by_user_id=789,
            created_at=datetime.utcnow(),
            status_change_id=1
        )
        mock_comment_repo.save.return_value = comment
        
        # Act
        use_case = ChangeDocumentWorkflowStatusUseCase(
            upload_repository=mock_upload_repo,
            workflow_history_repository=mock_workflow_history_repo,
            document_comment_repository=mock_comment_repo,
            permission_service=mock_permission_service,
            event_publisher=mock_event_publisher
        )
        
        result = await use_case.execute(
            document_id=1,
            new_status=WorkflowStatus.REVIEWED,
            user_id=789,
            reason="Teamleiter-Freigabe",
            comment="Alle Prüfpunkte OK"
        )
        
        # Assert
        assert result.workflow_status == WorkflowStatus.REVIEWED
        mock_permission_service.can_change_status.assert_called_once_with(
            789, WorkflowStatus.DRAFT, WorkflowStatus.REVIEWED
        )
        mock_upload_repo.get_by_id.assert_called_once_with(1)
        mock_upload_repo.save.assert_called_once()
        mock_workflow_history_repo.save.assert_called_once()
        mock_comment_repo.save.assert_called_once()
        mock_event_publisher.publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_permission_check_fails(self):
        """Test: Permission-Check schlägt fehl → ValueError."""
        # Arrange
        mock_upload_repo = AsyncMock()
        mock_workflow_history_repo = AsyncMock()
        mock_comment_repo = AsyncMock()
        mock_permission_service = Mock()
        mock_event_publisher = Mock()
        
        # Mock Permission Service - Permission denied
        mock_permission_service.can_change_status.return_value = False
        mock_permission_service.get_user_level.return_value = 2
        
        # Mock Document
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
            interest_group_ids=[1, 2],
            workflow_status=WorkflowStatus.DRAFT
        )
        
        mock_upload_repo.get_by_id.return_value = document
        
        # Act
        use_case = ChangeDocumentWorkflowStatusUseCase(
            upload_repository=mock_upload_repo,
            workflow_history_repository=mock_workflow_history_repo,
            document_comment_repository=mock_comment_repo,
            permission_service=mock_permission_service,
            event_publisher=mock_event_publisher
        )
        
        # Assert
        with pytest.raises(ValueError, match="Permission denied"):
            await use_case.execute(
                document_id=1,
                new_status=WorkflowStatus.REVIEWED,
                user_id=789,
                reason="Teamleiter-Freigabe",
                comment="Alle Prüfpunkte OK"
            )
    
    @pytest.mark.asyncio
    async def test_document_not_found(self):
        """Test: Dokument nicht gefunden → ValueError."""
        # Arrange
        mock_upload_repo = AsyncMock()
        mock_workflow_history_repo = AsyncMock()
        mock_comment_repo = AsyncMock()
        mock_permission_service = Mock()
        mock_event_publisher = Mock()
        
        mock_upload_repo.get_by_id.return_value = None
        
        # Act
        use_case = ChangeDocumentWorkflowStatusUseCase(
            upload_repository=mock_upload_repo,
            workflow_history_repository=mock_workflow_history_repo,
            document_comment_repository=mock_comment_repo,
            permission_service=mock_permission_service,
            event_publisher=mock_event_publisher
        )
        
        # Assert
        with pytest.raises(ValueError, match="Document not found"):
            await use_case.execute(
                document_id=999,
                new_status=WorkflowStatus.REVIEWED,
                user_id=789,
                reason="Teamleiter-Freigabe",
                comment="Alle Prüfpunkte OK"
            )
    
    @pytest.mark.asyncio
    async def test_comment_is_saved_when_provided(self):
        """Test: Kommentar wird gespeichert (optional)."""
        # Arrange
        mock_upload_repo = AsyncMock()
        mock_workflow_history_repo = AsyncMock()
        mock_comment_repo = AsyncMock()
        mock_permission_service = Mock()
        mock_event_publisher = Mock()
        
        # Mock Permission Service
        mock_permission_service.can_change_status.return_value = True
        mock_permission_service.get_user_level.return_value = 3
        
        # Mock Document
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
            interest_group_ids=[1, 2],
            workflow_status=WorkflowStatus.DRAFT
        )
        
        mock_upload_repo.get_by_id.return_value = document
        mock_upload_repo.save.return_value = document
        
        # Mock WorkflowStatusChange
        status_change = WorkflowStatusChange(
            id=1,
            upload_document_id=1,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=789,
            changed_at=datetime.utcnow(),
            change_reason="Teamleiter-Freigabe",
            comment="Wichtiger Kommentar"
        )
        mock_workflow_history_repo.save.return_value = status_change
        
        # Mock DocumentComment
        comment = DocumentComment(
            id=1,
            upload_document_id=1,
            comment_text="Wichtiger Kommentar",
            comment_type="review",
            page_number=None,
            created_by_user_id=789,
            created_at=datetime.utcnow(),
            status_change_id=1
        )
        mock_comment_repo.save.return_value = comment
        
        # Act
        use_case = ChangeDocumentWorkflowStatusUseCase(
            upload_repository=mock_upload_repo,
            workflow_history_repository=mock_workflow_history_repo,
            document_comment_repository=mock_comment_repo,
            permission_service=mock_permission_service,
            event_publisher=mock_event_publisher
        )
        
        result = await use_case.execute(
            document_id=1,
            new_status=WorkflowStatus.REVIEWED,
            user_id=789,
            reason="Teamleiter-Freigabe",
            comment="Wichtiger Kommentar"
        )
        
        # Assert
        assert result.workflow_status == WorkflowStatus.REVIEWED
        mock_comment_repo.save.assert_called_once()
        
        # Verify comment was saved with correct data
        saved_comment = mock_comment_repo.save.call_args[0][0]
        assert saved_comment.comment_text == "Wichtiger Kommentar"
        assert saved_comment.comment_type == "review"
        assert saved_comment.upload_document_id == 1
        assert saved_comment.created_by_user_id == 789
    
    @pytest.mark.asyncio
    async def test_no_comment_when_none_provided(self):
        """Test: Kein Kommentar wird gespeichert wenn None übergeben."""
        # Arrange
        mock_upload_repo = AsyncMock()
        mock_workflow_history_repo = AsyncMock()
        mock_comment_repo = AsyncMock()
        mock_permission_service = Mock()
        mock_event_publisher = Mock()
        
        # Mock Permission Service
        mock_permission_service.can_change_status.return_value = True
        mock_permission_service.get_user_level.return_value = 3
        
        # Mock Document
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
            interest_group_ids=[1, 2],
            workflow_status=WorkflowStatus.DRAFT
        )
        
        mock_upload_repo.get_by_id.return_value = document
        mock_upload_repo.save.return_value = document
        
        # Mock WorkflowStatusChange
        status_change = WorkflowStatusChange(
            id=1,
            upload_document_id=1,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=789,
            changed_at=datetime.utcnow(),
            change_reason="Teamleiter-Freigabe",
            comment=None
        )
        mock_workflow_history_repo.save.return_value = status_change
        
        # Act
        use_case = ChangeDocumentWorkflowStatusUseCase(
            upload_repository=mock_upload_repo,
            workflow_history_repository=mock_workflow_history_repo,
            document_comment_repository=mock_comment_repo,
            permission_service=mock_permission_service,
            event_publisher=mock_event_publisher
        )
        
        result = await use_case.execute(
            document_id=1,
            new_status=WorkflowStatus.REVIEWED,
            user_id=789,
            reason="Teamleiter-Freigabe",
            comment=None
        )
        
        # Assert
        assert result.workflow_status == WorkflowStatus.REVIEWED
        mock_comment_repo.save.assert_not_called()
