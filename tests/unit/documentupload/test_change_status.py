"""
Test für Status-Änderung Funktionalität.

TDD Approach: Schreibe zuerst den Test, dann die Implementierung.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from contexts.documentupload.domain.entities import UploadedDocument, DocumentMetadata
from contexts.documentupload.domain.value_objects import WorkflowStatus
from contexts.documentupload.application.use_cases import ChangeDocumentWorkflowStatusUseCase


class TestChangeDocumentStatus:
    """Test-Klasse für Status-Änderung Use Case."""
    
    @pytest.mark.asyncio
    async def test_change_status_draft_to_reviewed_success(self):
        """
        Test: Status-Änderung von Draft zu Reviewed erfolgreich.
        
        GIVEN: Ein Dokument im Draft-Status
        WHEN: Status auf "reviewed" geändert wird
        THEN: Status ist "reviewed" und Audit-Eintrag existiert
        """
        # ARRANGE
        document_id = 1
        user_id = 1
        reason = "Document reviewed and approved for next stage"
        
        # Mock Document
        mock_document = Mock(spec=UploadedDocument)
        mock_document.id = document_id
        mock_document.workflow_status = WorkflowStatus.DRAFT
        
        # Mock Repositories
        mock_upload_repo = AsyncMock()
        mock_history_repo = AsyncMock()
        mock_permission_service = AsyncMock()
        
        mock_upload_repo.get_by_id.return_value = mock_document
        mock_upload_repo.update_workflow_status.return_value = True
        mock_permission_service.can_change_status.return_value = True
        
        # Use Case
        use_case = ChangeDocumentWorkflowStatusUseCase(
            upload_repository=mock_upload_repo,
            history_repository=mock_history_repo,
            permission_service=mock_permission_service
        )
        
        # ACT
        result = await use_case.execute(
            document_id=document_id,
            new_status=WorkflowStatus.REVIEWED,
            user_id=user_id,
            reason=reason
        )
        
        # ASSERT
        assert result is not None
        assert result.workflow_status == WorkflowStatus.REVIEWED
        mock_upload_repo.update_workflow_status.assert_called_once()
        mock_history_repo.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_status_document_not_found(self):
        """
        Test: Status-Änderung schlägt fehl wenn Dokument nicht existiert.
        
        GIVEN: Dokument ID existiert nicht
        WHEN: Status geändert werden soll
        THEN: ValueError wird geworfen
        """
        # ARRANGE
        mock_upload_repo = AsyncMock()
        mock_history_repo = AsyncMock()
        mock_permission_service = AsyncMock()
        
        mock_upload_repo.get_by_id.return_value = None
        
        use_case = ChangeDocumentWorkflowStatusUseCase(
            upload_repository=mock_upload_repo,
            history_repository=mock_history_repo,
            permission_service=mock_permission_service
        )
        
        # ACT & ASSERT
        with pytest.raises(ValueError, match="Document .* not found"):
            await use_case.execute(
                document_id=999,
                new_status=WorkflowStatus.REVIEWED,
                user_id=1,
                reason="Test"
            )
    
    @pytest.mark.asyncio
    async def test_change_status_permission_denied(self):
        """
        Test: Status-Änderung schlägt fehl bei fehlenden Permissions.
        
        GIVEN: User hat keine Permission
        WHEN: Status geändert werden soll
        THEN: PermissionError wird geworfen
        """
        # ARRANGE
        mock_document = Mock(spec=UploadedDocument)
        mock_document.id = 1
        mock_document.workflow_status = WorkflowStatus.DRAFT
        
        mock_upload_repo = AsyncMock()
        mock_history_repo = AsyncMock()
        mock_permission_service = AsyncMock()
        
        mock_upload_repo.get_by_id.return_value = mock_document
        mock_permission_service.can_change_status.return_value = False
        
        use_case = ChangeDocumentWorkflowStatusUseCase(
            upload_repository=mock_upload_repo,
            history_repository=mock_history_repo,
            permission_service=mock_permission_service
        )
        
        # ACT & ASSERT
        with pytest.raises(PermissionError, match="User .* does not have permission"):
            await use_case.execute(
                document_id=1,
                new_status=WorkflowStatus.REVIEWED,
                user_id=1,
                reason="Test"
            )
    
    @pytest.mark.asyncio
    async def test_change_status_invalid_transition(self):
        """
        Test: Status-Änderung schlägt fehl bei ungültiger Transition.
        
        GIVEN: Dokument im Approved-Status
        WHEN: Status auf Draft zurückgesetzt werden soll
        THEN: ValueError wird geworfen
        """
        # ARRANGE
        mock_document = Mock(spec=UploadedDocument)
        mock_document.id = 1
        mock_document.workflow_status = WorkflowStatus.APPROVED
        
        mock_upload_repo = AsyncMock()
        mock_history_repo = AsyncMock()
        mock_permission_service = AsyncMock()
        
        mock_upload_repo.get_by_id.return_value = mock_document
        mock_permission_service.can_change_status.return_value = True
        mock_permission_service.is_valid_transition.return_value = False
        
        use_case = ChangeDocumentWorkflowStatusUseCase(
            upload_repository=mock_upload_repo,
            history_repository=mock_history_repo,
            permission_service=mock_permission_service
        )
        
        # ACT & ASSERT
        with pytest.raises(ValueError, match="Invalid status transition"):
            await use_case.execute(
                document_id=1,
                new_status=WorkflowStatus.DRAFT,
                user_id=1,
                reason="Test"
            )

