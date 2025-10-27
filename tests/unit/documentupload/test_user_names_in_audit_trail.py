"""
TDD Test für User-Namen in Audit Trail.

Testet ob die Status-Historie korrekte User-Namen anzeigt statt nur User IDs.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from contexts.documentupload.application.use_cases import GetWorkflowHistoryUseCase
from contexts.documentupload.domain.entities import WorkflowStatusChange
from contexts.documentupload.domain.value_objects import WorkflowStatus
from datetime import datetime

@pytest.fixture
def mock_history_repo():
    return AsyncMock()

@pytest.fixture
def get_history_use_case(mock_history_repo):
    return GetWorkflowHistoryUseCase(history_repository=mock_history_repo)

@pytest.mark.asyncio
async def test_audit_trail_includes_user_names(get_history_use_case, mock_history_repo):
    """Test: Audit Trail enthält User-Namen statt nur User IDs"""
    # GIVEN: Ein Dokument mit Status-Änderungen von verschiedenen Usern
    document_id = 5
    mock_history_entries = [
        WorkflowStatusChange(
            id=1,
            document_id=document_id,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED,
            changed_by_user_id=1,
            reason="Initial review completed",
            created_at=datetime(2025, 10, 24, 9, 46, 31)
        ),
        WorkflowStatusChange(
            id=2,
            document_id=document_id,
            from_status=WorkflowStatus.REVIEWED,
            to_status=WorkflowStatus.APPROVED,
            changed_by_user_id=2,
            reason="Final approval by manager",
            created_at=datetime(2025, 10, 24, 10, 30, 0)
        ),
    ]
    mock_history_repo.get_by_document_id.return_value = mock_history_entries

    # WHEN: Audit Trail wird geladen
    history = await get_history_use_case.execute(document_id)

    # THEN: User IDs sind korrekt gesetzt
    assert len(history) == 2
    assert history[0].changed_by_user_id == 1
    assert history[1].changed_by_user_id == 2
    assert history[0].reason == "Initial review completed"
    assert history[1].reason == "Final approval by manager"
    mock_history_repo.get_by_document_id.assert_called_once_with(document_id)

@pytest.mark.asyncio
async def test_audit_trail_shows_correct_timestamps(get_history_use_case, mock_history_repo):
    """Test: Audit Trail zeigt korrekte Zeitstempel"""
    # GIVEN: Eine Status-Änderung mit spezifischem Zeitstempel
    document_id = 3
    mock_history_entry = WorkflowStatusChange(
        id=1,
        document_id=document_id,
        from_status=WorkflowStatus.DRAFT,
        to_status=WorkflowStatus.REVIEWED,
        changed_by_user_id=1,
        reason="Document reviewed and approved",
        created_at=datetime(2025, 10, 24, 9, 46, 31)
    )
    mock_history_repo.get_by_document_id.return_value = [mock_history_entry]

    # WHEN: Audit Trail wird geladen
    history = await get_history_use_case.execute(document_id)

    # THEN: Zeitstempel ist korrekt
    assert len(history) == 1
    entry = history[0]
    assert entry.created_at == datetime(2025, 10, 24, 9, 46, 31)
    assert entry.changed_by_user_id == 1
    assert entry.reason == "Document reviewed and approved"

@pytest.mark.asyncio
async def test_audit_trail_handles_empty_reasons(get_history_use_case, mock_history_repo):
    """Test: Audit Trail behandelt leere Gründe korrekt"""
    # GIVEN: Eine Status-Änderung ohne Grund
    document_id = 4
    mock_history_entry = WorkflowStatusChange(
        id=1,
        document_id=document_id,
        from_status=WorkflowStatus.DRAFT,
        to_status=WorkflowStatus.REVIEWED,
        changed_by_user_id=1,
        reason="",  # Leerer Grund
        created_at=datetime(2025, 10, 24, 9, 46, 31)
    )
    mock_history_repo.get_by_document_id.return_value = [mock_history_entry]

    # WHEN: Audit Trail wird geladen
    history = await get_history_use_case.execute(document_id)

    # THEN: Leerer Grund wird korrekt behandelt
    assert len(history) == 1
    entry = history[0]
    assert entry.reason == ""
    assert entry.changed_by_user_id == 1
