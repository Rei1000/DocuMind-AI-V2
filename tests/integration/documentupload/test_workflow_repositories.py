"""
Integration Tests für Workflow Repositories

Testet SQLAlchemy Repository Implementierungen mit echter Datenbank.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock
from contexts.documentupload.infrastructure.repositories import (
    SQLAlchemyWorkflowHistoryRepository,
    SQLAlchemyDocumentCommentRepository
)
from contexts.documentupload.domain.entities import (
    WorkflowStatusChange,
    DocumentComment
)
from contexts.documentupload.domain.value_objects import WorkflowStatus


class TestSQLAlchemyWorkflowHistoryRepository:
    """Tests für SQLAlchemyWorkflowHistoryRepository."""
    
    @pytest.mark.asyncio
    async def test_save_and_get_workflow_status_change(self):
        """Test: Status-Änderung speichern & laden."""
        # Arrange
        mock_db = Mock()
        repository = SQLAlchemyWorkflowHistoryRepository(mock_db)
        
        status_change = WorkflowStatusChange(
            id=None,
            upload_document_id=1,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=2,
            changed_at=datetime.utcnow(),
            change_reason="Teamleiter-Freigabe",
            comment="Alle Prüfpunkte OK"
        )
        
        # Act
        saved_change = await repository.save(status_change)
        
        # Assert
        assert saved_change.id is not None
        assert saved_change.upload_document_id == 1
        assert saved_change.from_status == WorkflowStatus.DRAFT
        assert saved_change.to_status == WorkflowStatus.REVIEWED
        assert saved_change.changed_by_user_id == 2
        assert saved_change.change_reason == "Teamleiter-Freigabe"
        assert saved_change.comment == "Alle Prüfpunkte OK"
    
    @pytest.mark.asyncio
    async def test_get_workflow_history_by_document_id(self):
        """Test: Workflow-Historie laden (chronologisch)."""
        # Arrange
        mock_db = Mock()
        repository = SQLAlchemyWorkflowHistoryRepository(mock_db)
        
        # Erstelle mehrere Status-Änderungen
        change1 = WorkflowStatusChange(
            id=None,
            upload_document_id=1,
            from_status=None,
            to_status=WorkflowStatus.DRAFT,
            changed_by_user_id=1,
            changed_at=datetime.utcnow(),
            change_reason="Initial upload",
            comment=None
        )
        
        change2 = WorkflowStatusChange(
            id=None,
            upload_document_id=1,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=2,
            changed_at=datetime.utcnow(),
            change_reason="Teamleiter-Freigabe",
            comment="OK"
        )
        
        # Act
        saved_change1 = await repository.save(change1)
        saved_change2 = await repository.save(change2)
        
        history = await repository.get_by_document_id(1)
        
        # Assert
        assert len(history) == 2
        # Sollte chronologisch sortiert sein (älteste zuerst)
        assert history[0].to_status == WorkflowStatus.DRAFT
        assert history[1].to_status == WorkflowStatus.REVIEWED
    
    @pytest.mark.asyncio
    async def test_get_workflow_status_change_by_id(self):
        """Test: WorkflowStatusChange by ID laden."""
        # Arrange
        mock_db = Mock()
        repository = SQLAlchemyWorkflowHistoryRepository(mock_db)
        
        status_change = WorkflowStatusChange(
            id=None,
            upload_document_id=1,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=2,
            changed_at=datetime.utcnow(),
            change_reason="Teamleiter-Freigabe",
            comment="OK"
        )
        
        # Act
        saved_change = await repository.save(status_change)
        retrieved_change = await repository.get_by_id(saved_change.id)
        
        # Assert
        assert retrieved_change is not None
        assert retrieved_change.id == saved_change.id
        assert retrieved_change.upload_document_id == 1
        assert retrieved_change.to_status == WorkflowStatus.REVIEWED


class TestSQLAlchemyDocumentCommentRepository:
    """Tests für SQLAlchemyDocumentCommentRepository."""
    
    @pytest.mark.asyncio
    async def test_save_and_get_document_comment(self):
        """Test: Kommentar speichern & laden."""
        # Arrange
        mock_db = Mock()
        repository = SQLAlchemyDocumentCommentRepository(mock_db)
        
        comment = DocumentComment(
            id=None,
            upload_document_id=1,
            comment_text="Das Dokument ist unvollständig",
            comment_type="rejection",
            page_number=2,
            created_by_user_id=3,
            created_at=datetime.utcnow(),
            status_change_id=1
        )
        
        # Act
        saved_comment = await repository.save(comment)
        
        # Assert
        assert saved_comment.id is not None
        assert saved_comment.upload_document_id == 1
        assert saved_comment.comment_text == "Das Dokument ist unvollständig"
        assert saved_comment.comment_type == "rejection"
        assert saved_comment.page_number == 2
        assert saved_comment.created_by_user_id == 3
        assert saved_comment.status_change_id == 1
    
    @pytest.mark.asyncio
    async def test_get_comments_by_document_id(self):
        """Test: Kommentare nach Dokument ID laden."""
        # Arrange
        mock_db = Mock()
        repository = SQLAlchemyDocumentCommentRepository(mock_db)
        
        comment1 = DocumentComment(
            id=None,
            upload_document_id=1,
            comment_text="Erster Kommentar",
            comment_type="general",
            page_number=None,
            created_by_user_id=2,
            created_at=datetime.utcnow(),
            status_change_id=None
        )
        
        comment2 = DocumentComment(
            id=None,
            upload_document_id=1,
            comment_text="Zweiter Kommentar",
            comment_type="review",
            page_number=1,
            created_by_user_id=3,
            created_at=datetime.utcnow(),
            status_change_id=1
        )
        
        # Act
        await repository.save(comment1)
        await repository.save(comment2)
        
        comments = await repository.get_by_document_id(1)
        
        # Assert
        assert len(comments) == 2
        # Sollte chronologisch sortiert sein
        assert comments[0].comment_text == "Erster Kommentar"
        assert comments[1].comment_text == "Zweiter Kommentar"
    
    @pytest.mark.asyncio
    async def test_get_comments_by_status_change_id(self):
        """Test: Kommentare nach Status-Change ID laden."""
        # Arrange
        mock_db = Mock()
        repository = SQLAlchemyDocumentCommentRepository(mock_db)
        
        comment = DocumentComment(
            id=None,
            upload_document_id=1,
            comment_text="Status-Change Kommentar",
            comment_type="review",
            page_number=None,
            created_by_user_id=2,
            created_at=datetime.utcnow(),
            status_change_id=5
        )
        
        # Act
        await repository.save(comment)
        
        comments = await repository.get_by_status_change_id(5)
        
        # Assert
        assert len(comments) == 1
        assert comments[0].comment_text == "Status-Change Kommentar"
        assert comments[0].status_change_id == 5
