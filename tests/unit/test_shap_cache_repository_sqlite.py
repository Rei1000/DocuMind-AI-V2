"""
Unit Tests für SHAPCacheRepositorySQLite

Tests für SQLite-basiertes SHAP Cache Repository.
Ersetzt In-Memory Cache in SHAPCacheService.

TDD Phase 6: Tests ZUERST (RED), dann Implementierung (GREEN)
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models import SHAPCacheEntryModel
import json
import os
import tempfile


# ============================================================================
# Test Setup
# ============================================================================

@pytest.fixture
def db_session():
    """Erstelle Test-DB-Session mit separater Test-DB."""
    # Importiere Models
    from backend.app.models import SHAPCacheEntryModel
    
    # Erstelle temporäre Test-DB
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Erstelle Engine für Test-DB
    test_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )
    
    # Erstelle Tabellen
    SHAPCacheEntryModel.__table__.create(bind=test_engine, checkfirst=True)
    
    # Erstelle Session Factory
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    
    # Erstelle Session
    session = TestSessionLocal()
    
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        # Lösche Test-DB
        try:
            os.unlink(db_path)
        except:
            pass


# ============================================================================
# Test 1: get
# ============================================================================

def test_get_cache_hit(db_session: Session):
    """
    Test: get() gibt gecachte Erklärung zurück bei Cache Hit.
    
    Requirements:
    - get() gibt Explanation zurück wenn vorhanden
    - Cache Key wird korrekt generiert
    """
    from contexts.ragintegration.infrastructure.shap_cache_repository_sqlite import (
        SHAPCacheRepositorySQLite
    )
    
    repo = SHAPCacheRepositorySQLite(db_session, max_size=100, ttl_seconds=3600)
    
    # Erstelle Cache-Eintrag
    query = "Test Query"
    features = {'vector_score': 0.8, 'text_score': 0.7}
    explanation = {
        'feature_importances': [0.3, 0.25, 0.2],
        'base_value': 0.5,
        'values': [0.1, 0.05, -0.02]
    }
    
    repo.put(query, features, explanation)
    
    # Get
    cached = repo.get(query, features)
    
    # Assertions
    assert cached is not None, "Sollte gecachte Erklärung zurückgeben"
    assert cached['feature_importances'] == [0.3, 0.25, 0.2]
    assert cached['base_value'] == 0.5


def test_get_cache_miss(db_session: Session):
    """
    Test: get() gibt None zurück bei Cache Miss.
    
    Requirements:
    - get() gibt None wenn nicht im Cache
    """
    from contexts.ragintegration.infrastructure.shap_cache_repository_sqlite import (
        SHAPCacheRepositorySQLite
    )
    
    repo = SHAPCacheRepositorySQLite(db_session, max_size=100, ttl_seconds=3600)
    
    # Get ohne vorheriges Put
    cached = repo.get("Non-existent Query", {'vector_score': 0.5})
    
    # Assertions
    assert cached is None, "Sollte None zurückgeben bei Cache Miss"


def test_get_expired_entry(db_session: Session):
    """
    Test: get() gibt None zurück für abgelaufene Einträge.
    
    Requirements:
    - TTL wird respektiert
    - Abgelaufene Einträge werden nicht zurückgegeben
    """
    from contexts.ragintegration.infrastructure.shap_cache_repository_sqlite import (
        SHAPCacheRepositorySQLite
    )
    
    repo = SHAPCacheRepositorySQLite(db_session, max_size=100, ttl_seconds=1)  # 1 Sekunde TTL
    
    # Erstelle Cache-Eintrag
    query = "Test Query"
    features = {'vector_score': 0.8}
    explanation = {'value': 1}
    
    repo.put(query, features, explanation)
    
    # Get sofort (sollte funktionieren)
    cached = repo.get(query, features)
    assert cached is not None
    
    # Warte bis TTL abgelaufen
    import time
    time.sleep(2)
    
    # Get nach TTL (sollte None sein)
    cached = repo.get(query, features)
    assert cached is None, "Sollte None zurückgeben für abgelaufene Einträge"


# ============================================================================
# Test 2: put
# ============================================================================

def test_put_stores_explanation(db_session: Session):
    """
    Test: put() speichert Erklärung im Cache.
    
    Requirements:
    - put() speichert Explanation in DB
    - Cache Key ist UNIQUE
    """
    from contexts.ragintegration.infrastructure.shap_cache_repository_sqlite import (
        SHAPCacheRepositorySQLite
    )
    
    repo = SHAPCacheRepositorySQLite(db_session, max_size=100, ttl_seconds=3600)
    
    query = "Test Query"
    features = {'vector_score': 0.8, 'text_score': 0.7}
    explanation = {
        'feature_importances': [0.3, 0.25],
        'base_value': 0.5
    }
    
    # Put
    repo.put(query, features, explanation)
    
    # Prüfe DB
    cache_entry = db_session.query(SHAPCacheEntryModel).filter(
        SHAPCacheEntryModel.cache_key.like('%')
    ).first()
    
    assert cache_entry is not None, "Cache-Eintrag sollte in DB sein"
    
    # Prüfe JSON-Deserialisierung
    loaded_explanation = json.loads(cache_entry.shap_values_json)
    assert loaded_explanation['base_value'] == 0.5


def test_put_updates_existing_entry(db_session: Session):
    """
    Test: put() aktualisiert existierenden Eintrag.
    
    Requirements:
    - Gleicher Cache Key → Update statt Duplikat
    """
    from contexts.ragintegration.infrastructure.shap_cache_repository_sqlite import (
        SHAPCacheRepositorySQLite
    )
    
    repo = SHAPCacheRepositorySQLite(db_session, max_size=100, ttl_seconds=3600)
    
    query = "Test Query"
    features = {'vector_score': 0.8}
    
    # Erster Put
    explanation1 = {'value': 1}
    repo.put(query, features, explanation1)
    
    # Zweiter Put (gleicher Key)
    explanation2 = {'value': 2}
    repo.put(query, features, explanation2)
    
    # Prüfe DB (sollte nur einen Eintrag geben)
    count = db_session.query(SHAPCacheEntryModel).count()
    assert count == 1, "Sollte nur einen Eintrag geben (Update, kein Duplikat)"
    
    # Prüfe ob aktualisiert
    cached = repo.get(query, features)
    assert cached['value'] == 2, "Sollte aktualisierte Erklärung zurückgeben"


def test_put_respects_max_size(db_session: Session):
    """
    Test: put() respektiert max_size (LRU).
    
    Requirements:
    - Wenn max_size erreicht, wird ältester Eintrag gelöscht
    """
    from contexts.ragintegration.infrastructure.shap_cache_repository_sqlite import (
        SHAPCacheRepositorySQLite
    )
    import time
    
    max_size = 5
    repo = SHAPCacheRepositorySQLite(db_session, max_size=max_size, ttl_seconds=3600)
    
    # Erstelle max_size + 2 Einträge
    for i in range(max_size + 2):
        query = f"Query {i}"
        features = {'vector_score': 0.5 + i * 0.1}
        explanation = {'value': i}
        repo.put(query, features, explanation)
        time.sleep(0.01)  # Pause für verschiedene Timestamps
    
    # Prüfe DB
    count = db_session.query(SHAPCacheEntryModel).count()
    assert count == max_size, f"Sollte nur {max_size} Einträge haben (LRU)"
    
    # Prüfe ob neueste Einträge vorhanden sind
    newest = db_session.query(SHAPCacheEntryModel).order_by(
        SHAPCacheEntryModel.created_at.desc()
    ).first()
    
    assert newest is not None
    # Neuester sollte Query max_size+1 sein
    cached = repo.get(f"Query {max_size + 1}", {'vector_score': 0.5 + (max_size + 1) * 0.1})
    assert cached is not None, "Neuester Eintrag sollte vorhanden sein"


# ============================================================================
# Test 3: get_statistics
# ============================================================================

def test_get_statistics(db_session: Session):
    """
    Test: get_statistics() gibt korrekte Statistiken zurück.
    
    Requirements:
    - cache_size: Anzahl Einträge
    - hits: Anzahl Cache Hits
    - misses: Anzahl Cache Misses
    - hit_rate: Hit-Rate (0-1)
    """
    from contexts.ragintegration.infrastructure.shap_cache_repository_sqlite import (
        SHAPCacheRepositorySQLite
    )
    
    repo = SHAPCacheRepositorySQLite(db_session, max_size=100, ttl_seconds=3600)
    
    # Erstelle Einträge
    for i in range(3):
        query = f"Query {i}"
        features = {'vector_score': 0.5 + i * 0.1}
        explanation = {'value': i}
        repo.put(query, features, explanation)
    
    # Get (Cache Hits)
    repo.get("Query 0", {'vector_score': 0.5})
    repo.get("Query 1", {'vector_score': 0.6})
    
    # Get (Cache Miss)
    repo.get("Non-existent", {'vector_score': 0.5})
    
    # Get Statistics
    stats = repo.get_statistics()
    
    # Assertions
    assert stats['cache_size'] == 3
    assert stats['hits'] == 2
    assert stats['misses'] == 1
    assert stats['hit_rate'] == pytest.approx(2/3, abs=0.01)


# ============================================================================
# Test 4: clear_expired
# ============================================================================

def test_clear_expired(db_session: Session):
    """
    Test: clear_expired() löscht abgelaufene Einträge.
    
    Requirements:
    - Abgelaufene Einträge werden gelöscht
    - Nicht-abgelaufene bleiben erhalten
    """
    from contexts.ragintegration.infrastructure.shap_cache_repository_sqlite import (
        SHAPCacheRepositorySQLite
    )
    import time
    
    repo = SHAPCacheRepositorySQLite(db_session, max_size=100, ttl_seconds=1)  # 1 Sekunde TTL
    
    # Erstelle Einträge
    query1 = "Query 1"
    features1 = {'vector_score': 0.5}
    explanation1 = {'value': 1}
    repo.put(query1, features1, explanation1)
    
    # Warte bis TTL abgelaufen
    time.sleep(2)
    
    # Erstelle neuen Eintrag (noch nicht abgelaufen)
    query2 = "Query 2"
    features2 = {'vector_score': 0.6}
    explanation2 = {'value': 2}
    repo.put(query2, features2, explanation2)
    
    # Clear Expired
    deleted_count = repo.clear_expired()
    
    # Assertions
    assert deleted_count == 1, "Sollte 1 abgelaufenen Eintrag löschen"
    
    # Prüfe DB
    count = db_session.query(SHAPCacheEntryModel).count()
    assert count == 1, "Sollte nur 1 Eintrag haben (nicht-abgelaufener)"
    
    # Prüfe ob Query2 noch vorhanden
    cached = repo.get(query2, features2)
    assert cached is not None, "Nicht-abgelaufener Eintrag sollte vorhanden sein"

