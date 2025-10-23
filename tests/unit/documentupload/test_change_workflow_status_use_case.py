"""
Unit Tests für ChangeDocumentWorkflowStatusUseCase.

Tests für den Use Case zur Änderung des Workflow-Status eines Dokuments.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from contexts.documentupload.application.use_cases import ChangeDocumentWorkflowStatusUseCase
from contexts.documentupload.domain.entities import UploadedDocument, WorkflowStatusChange
from contexts.documentupload.domain.value_objects import WorkflowStatus, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus
from contexts.documentupload.domain.repositories import UploadRepository, WorkflowHistoryRepository
from contexts.documentupload.application.ports import WorkflowPermissionService
from datetime import datetime


class TestChangeDocumentWorkflowStatusUseCase:
    """Tests für ChangeDocumentWorkflowStatusUseCase."""
    
    @pytest.fixture
    def mock_upload_repository(self):
        """Mock UploadRepository."""
        return Mock(spec=UploadRepository)
    
    @pytest.fixture
    def mock_history_repository(self):
        """Mock WorkflowHistoryRepository."""
        return Mock(spec=WorkflowHistoryRepository)
    
    @pytest.fixture
    def mock_permission_service(self):
        """Mock WorkflowPermissionService."""
        return Mock(spec=WorkflowPermissionService)
    
    @pytest.fixture
    def use_case(self, mock_upload_repository, mock_history_repository, mock_permission_service):
        """ChangeDocumentWorkflowStatusUseCase mit Mocks."""
        return ChangeDocumentWorkflowStatusUseCase(
            upload_repository=mock_upload_repository,
            history_repository=mock_history_repository,
            permission_service=mock_permission_service
        )
    
    @pytest.fixture
    def sample_document(self):
        """Sample UploadedDocument für Tests."""
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="5.2",
            version="v1.0.0"
        )
        
        return UploadedDocument(
            id=1,
            file_type="pdf",
            file_size_bytes=1024,
            document_type_id=1,
            metadata=metadata,
            file_path=FilePath("uploads/test.pdf"),
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.COMPLETED,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_change_workflow_status_success(
        self,
        use_case,
        mock_upload_repository,
        mock_history_repository,
        mock_permission_service,
        sample_document
    ):
        """Test erfolgreiche Status-Änderung."""
        # Arrange
        mock_upload_repository.get_by_id.return_value = sample_document
        mock_permission_service.can_change_status.return_value = True
        mock_upload_repository.save.return_value = sample_document
        mock_history_repository.add.return_value = WorkflowStatusChange(
            id=1,
            document_id=1,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=2,
            reason="Reviewed"
        )
        
        # Act
        result = await use_case.execute(
            document_id=1,
            new_status=WorkflowStatus.REVIEWED,
            user_id=2,
            reason="Reviewed"
        )
        
        # Assert
        assert result.workflow_status == WorkflowStatus.REVIEWED
        mock_upload_repository.get_by_id.assert_called_once_with(1)
        mock_permission_service.can_change_status.assert_called_once_with(
            2, WorkflowStatus.DRAFT, WorkflowStatus.REVIEWED
        )
        mock_upload_repository.save.assert_called_once()
        mock_history_repository.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_workflow_status_document_not_found(
        self,
        use_case,
        mock_upload_repository,
        mock_permission_service
    ):
        """Test Status-Änderung bei nicht existierendem Dokument."""
        # Arrange
        mock_upload_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Document 1 not found"):
            await use_case.execute(
                document_id=1,
                new_status=WorkflowStatus.REVIEWED,
                user_id=2,
                reason="Reviewed"
            )
    
    @pytest.mark.asyncio
    async def test_change_workflow_status_permission_denied(
        self,
        use_case,
        mock_upload_repository,
        mock_permission_service,
        sample_document
    ):
        """Test Status-Änderung bei fehlender Berechtigung."""
        # Arrange
        mock_upload_repository.get_by_id.return_value = sample_document
        mock_permission_service.can_change_status.return_value = False
        
        # Act & Assert
        with pytest.raises(PermissionError, match="User 2 cannot change status from WorkflowStatus.DRAFT to WorkflowStatus.REVIEWED"):
            await use_case.execute(
                document_id=1,
                new_status=WorkflowStatus.REVIEWED,
                user_id=2,
                reason="Reviewed"
            )
    
    @pytest.mark.asyncio
    async def test_change_workflow_status_same_status(
        self,
        use_case,
        mock_upload_repository,
        mock_permission_service,
        sample_document
    ):
        """Test Status-Änderung auf gleichen Status."""
        # Arrange
        mock_upload_repository.get_by_id.return_value = sample_document
        mock_permission_service.can_change_status.return_value = True
        
        # Act & Assert
        with pytest.raises(ValueError, match="new_status must be different from current status"):
            await use_case.execute(
                document_id=1,
                new_status=WorkflowStatus.DRAFT,  # Gleicher Status
                user_id=2,
                reason="Reviewed"
            )
    
    @pytest.mark.asyncio
    async def test_change_workflow_status_invalid_user_id(
        self,
        use_case,
        mock_upload_repository,
        sample_document
    ):
        """Test Status-Änderung mit ungültiger user_id."""
        # Arrange
        mock_upload_repository.get_by_id.return_value = sample_document
        
        # Act & Assert
        with pytest.raises(ValueError, match="user_id must be positive"):
            await use_case.execute(
                document_id=1,
                new_status=WorkflowStatus.REVIEWED,
                user_id=0,  # Ungültig
                reason="Reviewed"
            )
    
    @pytest.mark.asyncio
    async def test_change_workflow_status_empty_reason(
        self,
        use_case,
        mock_upload_repository,
        sample_document
    ):
        """Test Status-Änderung mit leerem Grund."""
        # Arrange
        mock_upload_repository.get_by_id.return_value = sample_document
        
        # Act & Assert
        with pytest.raises(ValueError, match="reason cannot be empty"):
            await use_case.execute(
                document_id=1,
                new_status=WorkflowStatus.REVIEWED,
                user_id=2,
                reason=""  # Leer
            )
    
    @pytest.mark.asyncio
    async def test_change_workflow_status_multiple_transitions(
        self,
        use_case,
        mock_upload_repository,
        mock_history_repository,
        mock_permission_service,
        sample_document
    ):
        """Test mehrere Status-Änderungen."""
        # Arrange
        mock_upload_repository.get_by_id.return_value = sample_document
        mock_permission_service.can_change_status.return_value = True
        mock_upload_repository.save.return_value = sample_document
        mock_history_repository.add.return_value = WorkflowStatusChange(
            id=1,
            document_id=1,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=2,
            reason="Reviewed"
        )
        
        # Act - Draft → Reviewed
        result1 = await use_case.execute(
            document_id=1,
            new_status=WorkflowStatus.REVIEWED,
            user_id=2,
            reason="Reviewed"
        )
        
        # Assert
        assert result1.workflow_status == WorkflowStatus.REVIEWED
        mock_history_repository.add.assert_called_once()
        
        # Reset mocks for second transition
        mock_history_repository.reset_mock()
        mock_history_repository.add.return_value = WorkflowStatusChange(
            id=2,
            document_id=1,
            from_status=WorkflowStatus.REVIEWED,
            to_status=WorkflowStatus.APPROVED,
            changed_by_user_id=1,
            reason="Approved"
        )
        
        # Act - Reviewed → Approved
        result2 = await use_case.execute(
            document_id=1,
            new_status=WorkflowStatus.APPROVED,
            user_id=1,
            reason="Approved"
        )
        
        # Assert
        assert result2.workflow_status == WorkflowStatus.APPROVED
        mock_history_repository.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_workflow_status_repository_error(
        self,
        use_case,
        mock_upload_repository,
        mock_permission_service,
        sample_document
    ):
        """Test Repository-Fehler bei Status-Änderung."""
        # Arrange
        mock_upload_repository.get_by_id.return_value = sample_document
        mock_permission_service.can_change_status.return_value = True
        mock_upload_repository.save.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await use_case.execute(
                document_id=1,
                new_status=WorkflowStatus.REVIEWED,
                user_id=2,
                reason="Reviewed"
            )
