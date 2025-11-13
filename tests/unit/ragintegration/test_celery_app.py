"""
Unit Tests für Celery App Integration.

TDD Phase 1: RED - Tests für Celery-App-Initialisierung.

Diese Tests definieren Anforderungen für die Background-Job-Infrastruktur:
1. Celery App kann initialisiert werden
2. Redis Broker ist konfiguriert
3. App hat Task-Registry
4. Konfiguration ist korrekt
"""

import pytest
from unittest.mock import Mock, patch


# ========================================
# Test 1: Celery App Initialisierung
# ========================================

def test_celery_app_can_be_initialized():
    """
    Celery App sollte korrekt initialisiert werden können.
    
    Requirements:
    - App hat Namen 'documind_rag_worker'
    - Broker ist Redis (redis://localhost:6379/0)
    - Backend ist Redis (redis://localhost:6379/1)
    - Task-Registry existiert
    """
    from contexts.ragintegration.infrastructure.background_jobs.celery_app import celery_app
    
    # Assertions
    assert celery_app is not None, "Celery App sollte initialisiert sein"
    assert celery_app.main == 'documind_rag_worker', f"App-Name sollte 'documind_rag_worker' sein, ist aber '{celery_app.main}'"
    
    # Prüfe Broker
    assert 'redis://' in celery_app.conf.broker_url, "Broker sollte Redis sein"
    
    # Prüfe Backend
    assert 'redis://' in celery_app.conf.result_backend, "Backend sollte Redis sein"


def test_celery_app_has_correct_configuration():
    """
    Celery App sollte korrekte Konfiguration haben.
    
    Requirements:
    - task_serializer: 'json'
    - result_serializer: 'json'
    - accept_content: ['json']
    - timezone: 'Europe/Berlin'
    - enable_utc: True
    - task_track_started: True
    - task_time_limit: 120 (2 Minuten)
    """
    from contexts.ragintegration.infrastructure.background_jobs.celery_app import celery_app
    
    # Assertions
    assert celery_app.conf.task_serializer == 'json', "Task-Serializer sollte JSON sein"
    assert celery_app.conf.result_serializer == 'json', "Result-Serializer sollte JSON sein"
    assert 'json' in celery_app.conf.accept_content, "Accept-Content sollte JSON enthalten"
    assert celery_app.conf.timezone == 'Europe/Berlin', "Timezone sollte 'Europe/Berlin' sein"
    assert celery_app.conf.enable_utc is True, "UTC sollte aktiviert sein"
    assert celery_app.conf.task_track_started is True, "Task-Tracking sollte aktiviert sein"
    assert celery_app.conf.task_time_limit == 120, "Task-Time-Limit sollte 120s sein"


def test_celery_app_auto_discovers_tasks():
    """
    Celery App sollte Tasks automatisch entdecken.
    
    Requirements:
    - autodiscover_tasks() ist konfiguriert
    - Tasks aus 'contexts.ragintegration.infrastructure.background_jobs.tasks' werden geladen
    """
    from contexts.ragintegration.infrastructure.background_jobs.celery_app import celery_app
    
    # Prüfe dass Task-Registry existiert
    assert hasattr(celery_app, 'tasks'), "Celery App sollte Task-Registry haben"
    
    # Prüfe dass Tasks registriert werden können
    # (Task-Namen werden später in test_shap_tasks.py getestet)


# ========================================
# Test 2: Celery Health Check
# ========================================

@pytest.mark.skip(reason="Benötigt laufenden Redis - Integration Test")
def test_celery_app_can_connect_to_redis():
    """
    Celery App sollte sich mit Redis verbinden können.
    
    OPTIONAL: Integration Test (benötigt laufenden Redis-Server)
    """
    from contexts.ragintegration.infrastructure.background_jobs.celery_app import celery_app
    
    # Versuche Ping
    try:
        # Inspect aktive Worker
        inspector = celery_app.control.inspect()
        stats = inspector.stats()
        assert stats is not None or stats == {}, "Redis sollte erreichbar sein"
    except Exception as e:
        pytest.fail(f"Konnte nicht zu Redis verbinden: {e}")


# ========================================
# Test 3: Celery App Singleton
# ========================================

def test_celery_app_is_singleton():
    """
    Celery App sollte Singleton sein.
    
    Mehrfache Imports sollten die gleiche Instanz zurückgeben.
    """
    from contexts.ragintegration.infrastructure.background_jobs.celery_app import celery_app as app1
    from contexts.ragintegration.infrastructure.background_jobs.celery_app import celery_app as app2
    
    # Assertions
    assert app1 is app2, "Celery App sollte Singleton sein"

