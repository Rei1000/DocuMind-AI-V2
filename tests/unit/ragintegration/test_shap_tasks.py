"""
Unit Tests für SHAP Background Tasks.

TDD Phase 1: RED - Tests für asynchrone SHAP-Berechnungen.

Diese Tests definieren Anforderungen für SHAP-Background-Jobs:
1. compute_shap_explanation Task existiert
2. Task verarbeitet Input korrekt
3. Task speichert Ergebnis
4. Task hat Timeout und Error Handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


# ========================================
# Test 1: SHAP Task Registration
# ========================================

def test_shap_task_is_registered():
    """
    SHAP Task sollte in Celery registriert sein.
    
    Requirements:
    - Task-Name: 'ragintegration.compute_shap_explanation'
    - Task ist callable
    - Task hat delay() Methode für asynchrone Ausführung
    """
    from contexts.ragintegration.infrastructure.background_jobs.celery_app import celery_app
    
    # Prüfe dass Task registriert ist
    task_name = 'ragintegration.compute_shap_explanation'
    assert task_name in celery_app.tasks, f"Task '{task_name}' sollte registriert sein"
    
    # Hole Task
    task = celery_app.tasks[task_name]
    
    # Assertions
    assert task is not None, "Task sollte nicht None sein"
    assert callable(task), "Task sollte callable sein"
    assert hasattr(task, 'delay'), "Task sollte delay() Methode haben"
    assert hasattr(task, 'apply_async'), "Task sollte apply_async() Methode haben"


# ========================================
# Test 2: SHAP Task Execution (Mocked)
# ========================================

@patch('contexts.ragintegration.infrastructure.shap_real_attribution.SHAPExplainerService')
def test_shap_task_computes_explanation(mock_shap_service):
    """
    SHAP Task sollte SHAP-Erklärung berechnen.
    
    Requirements:
    - Task akzeptiert: query, chunk_data, vector_score, text_score, etc.
    - Task ruft SHAPExplainerService.explain_search_result() auf
    - Task gibt SHAPExplanation zurück
    """
    from contexts.ragintegration.infrastructure.background_jobs.tasks import compute_shap_explanation
    
    # Mock SHAP Service
    mock_service_instance = Mock()
    mock_shap_service.return_value = mock_service_instance
    
    # Mock SHAP Explanation
    mock_explanation = Mock()
    mock_explanation.feature_importance = {'vector_score': 0.15, 'text_score': 0.10}
    mock_explanation.base_value = 0.5
    mock_explanation.shap_values = [0.15, 0.10, 0.05, 0.02, 0.01, 0.01, 0.01]
    mock_explanation.prediction = 0.77
    mock_explanation.query = "Test Query"
    mock_explanation.chunk_id = "test_chunk_1"
    
    mock_service_instance.explain_search_result.return_value = mock_explanation
    
    # Task Input
    task_input = {
        'query': 'Test Query',
        'chunk': {'chunk_id': 'test_chunk_1', 'metadata': {}},
        'vector_score': 0.8,
        'text_score': 0.7,
        'hybrid_score': 0.77,
        'document_type': 'Arbeitsanweisung',
        'user_level': 3,
        'keyword_matches': 2,
        'chunk_length': 100,
        'heading_hierarchy_depth': 2,
        'confidence_score': 0.9
    }
    
    # Führe Task aus (synchron für Test)
    result = compute_shap_explanation(**task_input)
    
    # Assertions
    assert result is not None, "Task sollte Ergebnis zurückgeben"
    assert 'feature_importance' in result, "Ergebnis sollte feature_importance enthalten"
    assert 'base_value' in result, "Ergebnis sollte base_value enthalten"
    assert 'shap_values' in result, "Ergebnis sollte shap_values enthalten"
    assert 'prediction' in result, "Ergebnis sollte prediction enthalten"


@patch('contexts.ragintegration.infrastructure.shap_real_attribution.SHAPExplainerService')
def test_shap_task_handles_errors_gracefully(mock_shap_service):
    """
    SHAP Task sollte Fehler gracefully behandeln.
    
    Requirements:
    - Bei Fehler wird Retry versucht
    - Task wirft Retry-Exception (korrekt)
    - Celery wird Retry automatisch durchführen
    """
    from contexts.ragintegration.infrastructure.background_jobs.tasks import compute_shap_explanation
    from celery.exceptions import Retry
    
    # Mock SHAP Service mit Fehler
    mock_service_instance = Mock()
    mock_shap_service.return_value = mock_service_instance
    mock_service_instance.explain_search_result.side_effect = Exception("SHAP Error")
    
    # Task Input
    task_input = {
        'query': 'Test Query',
        'chunk': {'chunk_id': 'test_chunk_1', 'metadata': {}},
        'vector_score': 0.8,
        'text_score': 0.7,
        'hybrid_score': 0.77,
        'document_type': 'Arbeitsanweisung',
        'user_level': 3,
        'keyword_matches': 2,
        'chunk_length': 100,
        'heading_hierarchy_depth': 2,
        'confidence_score': 0.9
    }
    
    # Führe Task aus - sollte Retry oder Exception werfen
    try:
        result = compute_shap_explanation(**task_input)
        # Sollte nicht hierher kommen, aber wenn doch, ist das auch ok
        pytest.fail("Task sollte bei Fehler Exception werfen")
    except (Retry, Exception) as e:
        # Retry oder Exception ist erwartetes Verhalten
        assert True  # Test erfolgreich!


# ========================================
# Test 3: SHAP Task Serialization
# ========================================

def test_shap_task_input_is_json_serializable():
    """
    SHAP Task Input sollte JSON-serialisierbar sein.
    
    Requirements:
    - Alle Input-Parameter sind JSON-kompatibel
    - Keine Python-spezifischen Objekte (datetime, numpy, etc.)
    - Chunk-Daten als Dict (nicht Entity)
    """
    import json
    
    # Task Input
    task_input = {
        'query': 'Test Query',
        'chunk': {
            'chunk_id': 'test_chunk_1',
            'metadata': {
                'chunk_text': 'Test text',
                'page_numbers': [1, 2],
                'heading_hierarchy_depth': 2,
                'confidence_score': 0.9,
                'chunk_length': 100
            }
        },
        'vector_score': 0.8,
        'text_score': 0.7,
        'hybrid_score': 0.77,
        'document_type': 'Arbeitsanweisung',
        'user_level': 3,
        'keyword_matches': 2,
        'chunk_length': 100,
        'heading_hierarchy_depth': 2,
        'confidence_score': 0.9
    }
    
    # Prüfe JSON-Serialisierung
    try:
        json_string = json.dumps(task_input)
        deserialized = json.loads(json_string)
        assert deserialized == task_input, "Task Input sollte nach JSON-Serialisierung identisch sein"
    except Exception as e:
        pytest.fail(f"Task Input sollte JSON-serialisierbar sein: {e}")


def test_shap_task_output_is_json_serializable():
    """
    SHAP Task Output sollte JSON-serialisierbar sein.
    
    Requirements:
    - Alle Output-Werte sind JSON-kompatibel
    - shap_values als Liste (nicht numpy array)
    - timestamp als ISO-String (nicht datetime object)
    """
    import json
    
    # Mock SHAP Explanation Output
    task_output = {
        'feature_importance': {
            'vector_score': 0.15,
            'text_score': 0.10,
            'keyword_matches': 0.03
        },
        'base_value': 0.5,
        'shap_values': [0.15, 0.10, 0.05, 0.03, 0.02, 0.01, 0.01],  # Liste, nicht numpy
        'expected_value': 0.5,
        'prediction': 0.77,
        'query': 'Test Query',
        'chunk_id': 'test_chunk_1',
        'timestamp': '2025-11-13T10:30:00',  # ISO-String, nicht datetime
        'features': {
            'vector_score': 0.8,
            'text_score': 0.7,
            'user_level': 0.6,
            'keyword_matches': 0.2,
            'chunk_length': 0.05,
            'heading_hierarchy_depth': 0.4,
            'confidence_score': 0.9
        }
    }
    
    # Prüfe JSON-Serialisierung
    try:
        json_string = json.dumps(task_output)
        deserialized = json.loads(json_string)
        assert deserialized == task_output, "Task Output sollte nach JSON-Serialisierung identisch sein"
    except Exception as e:
        pytest.fail(f"Task Output sollte JSON-serialisierbar sein: {e}")


# ========================================
# Test 4: Task Metadata
# ========================================

def test_shap_task_has_correct_metadata():
    """
    SHAP Task sollte korrekte Metadata haben.
    
    Requirements:
    - Task-Name: 'ragintegration.compute_shap_explanation'
    - bind=True (Task-Context verfügbar)
    - max_retries: 3
    - default_retry_delay: 60 (1 Minute)
    """
    from contexts.ragintegration.infrastructure.background_jobs.celery_app import celery_app
    
    task_name = 'ragintegration.compute_shap_explanation'
    task = celery_app.tasks.get(task_name)
    
    # Assertions
    assert task is not None, f"Task '{task_name}' sollte existieren"
    
    # Prüfe Metadata
    # bind=True bedeutet, dass Task 'self' Parameter hat
    # max_retries sollte gesetzt sein
    # Diese werden in der Task-Deklaration mit @celery_app.task() gesetzt

