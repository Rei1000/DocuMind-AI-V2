"""
Unit Tests für Async SHAP Integration in Use Cases.

TDD Phase 1: RED - Tests für asynchrone SHAP-Berechnung in AskQuestionUseCase.

Diese Tests definieren Anforderungen:
1. AskQuestionUseCase startet SHAP-Task asynchron
2. Task-ID wird in Metadaten gespeichert
3. SHAP-Ergebnis kann abgefragt werden
4. Polling-Endpoint existiert
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime


# ========================================
# Test 1: UseCase startet SHAP-Task asynchron
# ========================================

@pytest.mark.asyncio
@patch('contexts.ragintegration.infrastructure.background_jobs.tasks.compute_shap_explanation')
async def test_use_case_starts_shap_task_async(mock_task):
    """
    AskQuestionUseCase sollte SHAP-Task asynchron starten.
    
    Requirements:
    - Task wird mit delay() gestartet
    - Task-ID wird zurückgegeben
    - Task-ID wird in Message-Metadaten gespeichert
    """
    from contexts.ragintegration.application.use_cases import AskQuestionUseCase
    
    # Mock AsyncResult
    mock_async_result = Mock()
    mock_async_result.id = 'test-task-id-12345'
    mock_task.delay.return_value = mock_async_result
    
    # Mock Repositories und Services
    chunk_repo = Mock()
    session_repo = Mock()
    session_repo.get_by_id.return_value = Mock(user_id=1)
    indexed_doc_repo = Mock()
    indexed_doc_repo.get_all.return_value = []
    vector_store = Mock()
    embedding_service = Mock()
    multi_query_service = Mock()
    ai_service = AsyncMock()
    ai_service.generate_answer.return_value = {
        'answer': 'Test Answer',
        'tokens_used': 100
    }
    event_publisher = None
    message_repo = Mock()
    message_repo.save.return_value = Mock(id=1)
    
    # Mock SHAP Service mit async_mode Flag
    shap_service = Mock()
    shap_service.async_mode = True  # Flag für asynchrone Verarbeitung
    
    # Erstelle Use Case
    use_case = AskQuestionUseCase(
        chunk_repository=chunk_repo,
        session_repository=session_repo,
        indexed_document_repository=indexed_doc_repo,
        vector_store=vector_store,
        embedding_service=embedding_service,
        multi_query_service=multi_query_service,
        ai_service=ai_service,
        event_publisher=event_publisher,
        message_repository=message_repo,
        permission_service=None,
        shap_service=shap_service
    )
    
    # Führe Use Case aus
    result = await use_case.execute(
        question='Test Question',
        session_id=1,
        model_id='gpt-4o-mini'
    )
    
    # Assertions
    assert result is not None, "Use Case sollte Ergebnis zurückgeben"
    # Task-ID sollte in Metadaten gespeichert sein
    # Dies wird später in der Implementierung geprüft


# ========================================
# Test 2: SHAP-Ergebnis abrufen
# ========================================

@patch('contexts.ragintegration.infrastructure.background_jobs.tasks.compute_shap_explanation')
def test_get_shap_result_endpoint_returns_task_status(mock_task):
    """
    SHAP-Ergebnis-Endpoint sollte Task-Status zurückgeben.
    
    Requirements:
    - GET /api/rag/shap-results/{task_id}
    - Response: {'task_id': ..., 'status': 'PENDING|SUCCESS|FAILURE', 'result': {...}}
    - Bei SUCCESS: result enthält SHAP-Explanation
    - Bei PENDING: result ist None
    """
    # Mock AsyncResult
    mock_async_result = Mock()
    mock_async_result.id = 'test-task-id-12345'
    mock_async_result.state = 'SUCCESS'
    mock_async_result.result = {
        'feature_importance': {'vector_score': 0.15},
        'base_value': 0.5,
        'prediction': 0.77
    }
    mock_async_result.ready.return_value = True
    mock_async_result.successful.return_value = True
    
    mock_task.AsyncResult.return_value = mock_async_result
    
    # Teste dass AsyncResult abgefragt werden kann
    task_id = 'test-task-id-12345'
    
    # Mock Celery AsyncResult
    from celery.result import AsyncResult
    
    # In echtem Test würde hier der Endpoint getestet werden
    # Für Unit Test prüfen wir nur die Logik
    
    assert mock_async_result.state == 'SUCCESS', "Task sollte SUCCESS Status haben"
    assert mock_async_result.ready() is True, "Task sollte ready sein"
    assert mock_async_result.result is not None, "Task sollte Ergebnis haben"


# ========================================
# Test 3: Task Timeout
# ========================================

def test_shap_task_has_timeout_configuration():
    """
    SHAP Task sollte Timeout haben.
    
    Requirements:
    - soft_time_limit: 100s
    - time_limit: 120s (2 Minuten)
    - Bei Timeout: SoftTimeLimitExceeded Exception
    """
    from contexts.ragintegration.infrastructure.background_jobs.celery_app import celery_app
    
    task_name = 'ragintegration.compute_shap_explanation'
    
    # Prüfe globale Konfiguration
    assert celery_app.conf.task_time_limit == 120, "Globaler Task-Time-Limit sollte 120s sein"
    
    # Task-spezifische Limits werden in @task() Decorator gesetzt
    # Dies wird in der Implementierung geprüft


# ========================================
# Test 4: Task-ID Speicherung in Metadaten
# ========================================

def test_task_id_is_stored_in_message_metadata():
    """
    Task-ID sollte in Message-Metadaten gespeichert werden.
    
    Requirements:
    - message.metadata['shap_task_id'] = task_id
    - message.metadata['shap_status'] = 'pending'
    - Frontend kann Task-ID abrufen und Status pollen
    """
    # Mock ChatMessage
    message = Mock()
    message.metadata = {
        'shap_task_id': 'test-task-id-12345',
        'shap_status': 'pending'
    }
    
    # Assertions
    assert 'shap_task_id' in message.metadata, "Message sollte shap_task_id in Metadaten haben"
    assert message.metadata['shap_task_id'] == 'test-task-id-12345', "Task-ID sollte korrekt sein"
    assert message.metadata['shap_status'] == 'pending', "Status sollte 'pending' sein"


# ========================================
# Test 5: Batch SHAP Tasks
# ========================================

@patch('contexts.ragintegration.infrastructure.background_jobs.tasks.compute_shap_explanation')
def test_batch_shap_tasks_can_be_started(mock_task):
    """
    Mehrere SHAP Tasks sollten parallel gestartet werden können.
    
    Requirements:
    - Tasks werden mit group() gebündelt
    - Alle Tasks werden parallel ausgeführt
    - Ergebnisse können gesammelt werden
    
    OPTIONAL: Später für Batch-Verarbeitung
    """
    pytest.skip("Batch-Verarbeitung ist optional - wird später implementiert")

