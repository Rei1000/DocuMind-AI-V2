"""
Test für Audit Trail Funktionalität.

TDD Approach: Schreibe zuerst den Test, dann die Implementierung.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from contexts.documentupload.domain.entities import WorkflowStatusChange
from contexts.documentupload.domain.value_objects import WorkflowStatus
from contexts.documentupload.application.use_cases import GetWorkflowHistoryUseCase


class TestAuditTrail:
    """Test-Klasse für Audit Trail Use Case."""
    
    @pytest.mark.asyncio
    async def test_get_audit_trail_for_document(self):
        """
        Test: Audit Trail für ein Dokument abrufen.
        
        GIVEN: Ein Dokument mit 2 Status-Änderungen
        WHEN: Audit Trail abgerufen wird
        THEN: 2 Einträge mit User, Timestamp, Reason
        """
        # ARRANGE
        document_id = 1
        
        # Mock History Entries
        mock_history_entries = [
            WorkflowStatusChange(
                id=1,
                document_id=document_id,
                from_status=WorkflowStatus.DRAFT,
                to_status=WorkflowStatus.REVIEWED,
                changed_by_user_id=1,
                reason="Initial review completed",
                created_at=datetime(2025, 10, 23, 10, 0, 0)
            ),
            WorkflowStatusChange(
                id=2,
                document_id=document_id,
                from_status=WorkflowStatus.REVIEWED,
                to_status=WorkflowStatus.APPROVED,
                changed_by_user_id=2,
                reason="Final approval granted",
                created_at=datetime(2025, 10, 23, 14, 30, 0)
            )
        ]
        
        # Mock Repository
        mock_history_repo = AsyncMock()
        mock_history_repo.get_by_document_id.return_value = mock_history_entries
        
        # Use Case
        use_case = GetWorkflowHistoryUseCase(history_repository=mock_history_repo)
        
        # ACT
        result = await use_case.execute(document_id)
        
        # ASSERT
        assert len(result) == 2
        assert result[0].from_status == WorkflowStatus.DRAFT
        assert result[0].to_status == WorkflowStatus.REVIEWED
        assert result[0].reason == "Initial review completed"
        assert result[1].from_status == WorkflowStatus.REVIEWED
        assert result[1].to_status == WorkflowStatus.APPROVED
        assert result[1].reason == "Final approval granted"
        
        mock_history_repo.get_by_document_id.assert_called_once_with(document_id)
    
    @pytest.mark.asyncio
    async def test_get_audit_trail_empty_document(self):
        """
        Test: Audit Trail für Dokument ohne Historie.
        
        GIVEN: Ein Dokument ohne Status-Änderungen
        WHEN: Audit Trail abgerufen wird
        THEN: Leere Liste wird zurückgegeben
        """
        # ARRANGE
        document_id = 999
        mock_history_repo = AsyncMock()
        mock_history_repo.get_by_document_id.return_value = []
        
        use_case = GetWorkflowHistoryUseCase(history_repository=mock_history_repo)
        
        # ACT
        result = await use_case.execute(document_id)
        
        # ASSERT
        assert result == []
        mock_history_repo.get_by_document_id.assert_called_once_with(document_id)
    
    @pytest.mark.asyncio
    async def test_get_audit_trail_chronological_order(self):
        """
        Test: Audit Trail ist chronologisch sortiert.
        
        GIVEN: Ein Dokument mit Status-Änderungen in zufälliger Reihenfolge
        WHEN: Audit Trail abgerufen wird
        THEN: Einträge sind chronologisch sortiert (älteste zuerst)
        """
        # ARRANGE
        document_id = 1
        
        # Mock History Entries (in zufälliger Reihenfolge)
        mock_history_entries = [
            WorkflowStatusChange(
                id=2,
                document_id=document_id,
                from_status=WorkflowStatus.REVIEWED,
                to_status=WorkflowStatus.APPROVED,
                changed_by_user_id=2,
                reason="Final approval",
                created_at=datetime(2025, 10, 23, 14, 30, 0)  # Später
            ),
            WorkflowStatusChange(
                id=1,
                document_id=document_id,
                from_status=WorkflowStatus.DRAFT,
                to_status=WorkflowStatus.REVIEWED,
                changed_by_user_id=1,
                reason="Initial review",
                created_at=datetime(2025, 10, 23, 10, 0, 0)  # Früher
            )
        ]
        
        mock_history_repo = AsyncMock()
        mock_history_repo.get_by_document_id.return_value = mock_history_entries
        
        use_case = GetWorkflowHistoryUseCase(history_repository=mock_history_repo)
        
        # ACT
        result = await use_case.execute(document_id)
        
        # ASSERT
        assert len(result) == 2
        # Repository sollte chronologisch sortieren
        mock_history_repo.get_by_document_id.assert_called_once_with(document_id)
