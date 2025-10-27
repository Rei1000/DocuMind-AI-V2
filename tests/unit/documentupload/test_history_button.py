"""
TDD Test für Historie-Button Funktionalität.

Testet ob der Historie-Button korrekt funktioniert und die Status-Historie anzeigt.
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
async def test_history_button_loads_status_changes(get_history_use_case, mock_history_repo):
    """Test: Historie-Button lädt Status-Änderungen korrekt"""
    # GIVEN: Ein Dokument mit 2 Status-Änderungen
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
            reason="Final approval",
            created_at=datetime(2025, 10, 24, 10, 30, 0)
        ),
    ]
    mock_history_repo.get_by_document_id.return_value = mock_history_entries

    # WHEN: Historie-Button wird geklickt und Status-Änderungen werden geladen
    history = await get_history_use_case.execute(document_id)

    # THEN: 2 Status-Änderungen werden zurückgegeben
    assert len(history) == 2
    assert history[0].to_status == WorkflowStatus.REVIEWED
    assert history[1].to_status == WorkflowStatus.APPROVED
    assert history[0].reason == "Initial review completed"
    assert history[1].reason == "Final approval"
    mock_history_repo.get_by_document_id.assert_called_once_with(document_id)

@pytest.mark.asyncio
async def test_history_button_handles_empty_history(get_history_use_case, mock_history_repo):
    """Test: Historie-Button behandelt leere Historie korrekt"""
    # GIVEN: Ein Dokument ohne Status-Änderungen
    document_id = 3
    mock_history_repo.get_by_document_id.return_value = []

    # WHEN: Historie-Button wird geklickt
    history = await get_history_use_case.execute(document_id)

    # THEN: Leere Liste wird zurückgegeben
    assert len(history) == 0
    mock_history_repo.get_by_document_id.assert_called_once_with(document_id)

@pytest.mark.asyncio
async def test_history_button_displays_correct_format(get_history_use_case, mock_history_repo):
    """Test: Historie-Button zeigt korrekte Formatierung"""
    # GIVEN: Eine Status-Änderung mit allen Feldern
    document_id = 5
    mock_history_entry = WorkflowStatusChange(
        id=1,
        document_id=document_id,
        from_status=WorkflowStatus.DRAFT,
        to_status=WorkflowStatus.REVIEWED,
        changed_by_user_id=1,
        reason="Document reviewed and approved for next step",
        created_at=datetime(2025, 10, 24, 9, 46, 31)
    )
    mock_history_repo.get_by_document_id.return_value = [mock_history_entry]

    # WHEN: Historie wird geladen
    history = await get_history_use_case.execute(document_id)

    # THEN: Alle Felder sind korrekt gesetzt
    assert len(history) == 1
    entry = history[0]
    assert entry.id == 1
    assert entry.document_id == document_id
    assert entry.from_status == WorkflowStatus.DRAFT
    assert entry.to_status == WorkflowStatus.REVIEWED
    assert entry.changed_by_user_id == 1
    assert entry.reason == "Document reviewed and approved for next step"
    assert entry.created_at == datetime(2025, 10, 24, 9, 46, 31)
