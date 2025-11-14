"""
Unit Tests für SHAPBackgroundDataRepositorySQLite

Tests für SQLite-basiertes SHAP Background Data Repository.
Ersetzt In-Memory Storage in SHAPBackgroundDataService.

TDD Phase 5: Tests ZUERST (RED), dann Implementierung (GREEN)
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models import SHAPBackgroundDataModel
import os
import tempfile


# ============================================================================
# Test Setup
# ============================================================================

@pytest.fixture
def db_session():
    """Erstelle Test-DB-Session mit separater Test-DB."""
    # Importiere Models
    from backend.app.models import SHAPBackgroundDataModel
    
    # Erstelle temporäre Test-DB
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Erstelle Engine für Test-DB
    test_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )
    
    # Erstelle Tabellen
    SHAPBackgroundDataModel.__table__.create(bind=test_engine, checkfirst=True)
    
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
# Test 1: add_record
# ============================================================================

def test_add_record_to_db(db_session: Session):
    """
    Test: Search-Record kann in DB gespeichert werden.
    
    Requirements:
    - add_record() speichert Record
    - Record hat ID nach Speichern
    - Alle Felder werden korrekt gespeichert
    """
    from contexts.ragintegration.infrastructure.shap_background_data_repository_sqlite import (
        SHAPBackgroundDataRepositorySQLite
    )
    
    repo = SHAPBackgroundDataRepositorySQLite(db_session, max_records=1000)
    
    # Erstelle Record
    result = repo.add_record(
        query="Test Query",
        vector_score=0.85,
        text_score=0.72,
        user_level=5,
        keyword_matches=2,
        chunk_length=150,
        heading_hierarchy_depth=2,
        confidence_score=0.95
    )
    
    # Assertions
    assert result is True, "Add sollte erfolgreich sein"
    
    # Prüfe ob Record in DB ist
    db_record = db_session.query(SHAPBackgroundDataModel).filter(
        SHAPBackgroundDataModel.query == "Test Query"
    ).first()
    
    assert db_record is not None, "Record sollte in DB sein"
    assert db_record.vector_score == 0.85
    assert db_record.text_score == 0.72
    assert db_record.user_level == 5
    assert db_record.keyword_matches == 2
    assert db_record.chunk_length == 150
    assert db_record.heading_hierarchy_depth == 2
    assert db_record.confidence_score == 0.95
    assert db_record.created_at is not None


def test_add_record_optional_fields(db_session: Session):
    """
    Test: Record kann mit optionalen Feldern gespeichert werden.
    
    Requirements:
    - Optional fields können None sein
    """
    from contexts.ragintegration.infrastructure.shap_background_data_repository_sqlite import (
        SHAPBackgroundDataRepositorySQLite
    )
    
    repo = SHAPBackgroundDataRepositorySQLite(db_session, max_records=1000)
    
    # Record mit None-Werten
    result = repo.add_record(
        query="Test Query",
        vector_score=None,
        text_score=None,
        user_level=None,
        keyword_matches=None,
        chunk_length=None,
        heading_hierarchy_depth=None,
        confidence_score=None
    )
    
    assert result is True
    
    # Prüfe DB
    db_record = db_session.query(SHAPBackgroundDataModel).filter(
        SHAPBackgroundDataModel.query == "Test Query"
    ).first()
    
    assert db_record.vector_score is None
    assert db_record.text_score is None


# ============================================================================
# Test 2: get_background_data
# ============================================================================

def test_get_background_data_returns_numpy_array(db_session: Session):
    """
    Test: get_background_data() gibt numpy array zurück.
    
    Requirements:
    - Returns numpy.ndarray
    - Shape: (n_samples, 7) für 7 Features
    - Features sind normalisiert (0-1)
    """
    from contexts.ragintegration.infrastructure.shap_background_data_repository_sqlite import (
        SHAPBackgroundDataRepositorySQLite
    )
    
    repo = SHAPBackgroundDataRepositorySQLite(db_session, max_records=1000)
    
    # Erstelle 5 Records
    for i in range(5):
        repo.add_record(
            query=f"Query {i}",
            vector_score=0.5 + i * 0.1,
            text_score=0.4 + i * 0.1,
            user_level=1 + i,
            keyword_matches=i,
            chunk_length=100 + i * 10,
            heading_hierarchy_depth=i % 3,
            confidence_score=0.5 + i * 0.1
        )
    
    # Get Background Data
    background_data = repo.get_background_data(n_samples=5)
    
    # Assertions
    assert isinstance(background_data, np.ndarray), "Sollte numpy array sein"
    assert background_data.shape == (5, 7), "Shape sollte (5, 7) sein"
    assert background_data.dtype == np.float64, "Dtype sollte float64 sein"


def test_get_background_data_with_feature_extractor(db_session: Session):
    """
    Test: get_background_data() verwendet FeatureExtractor wenn vorhanden.
    
    Requirements:
    - Wenn feature_extractor vorhanden, wird er verwendet
    - Features werden korrekt extrahiert
    """
    from contexts.ragintegration.infrastructure.shap_background_data_repository_sqlite import (
        SHAPBackgroundDataRepositorySQLite
    )
    
    # Mock FeatureExtractor
    class MockFeatureExtractor:
        def extract(self, query, chunk, vector_score, text_score, user_level, keyword_matches):
            return np.array([
                vector_score,
                text_score,
                user_level / 5.0,
                min(keyword_matches / 10.0, 1.0),
                min(chunk['metadata']['chunk_length'] / 2000.0, 1.0),
                min(chunk['metadata']['heading_hierarchy_depth'] / 5.0, 1.0),
                chunk['metadata']['confidence_score']
            ])
    
    feature_extractor = MockFeatureExtractor()
    repo = SHAPBackgroundDataRepositorySQLite(
        db_session,
        max_records=1000,
        feature_extractor=feature_extractor
    )
    
    # Erstelle Record
    repo.add_record(
        query="Test Query",
        vector_score=0.8,
        text_score=0.7,
        user_level=5,
        keyword_matches=2,
        chunk_length=150,
        heading_hierarchy_depth=2,
        confidence_score=0.9
    )
    
    # Get Background Data
    background_data = repo.get_background_data(n_samples=1)
    
    # Assertions
    assert background_data.shape == (1, 7)
    # Prüfe erste Feature (vector_score)
    assert background_data[0][0] == pytest.approx(0.8, abs=0.01)


def test_get_background_data_manual_extraction(db_session: Session):
    """
    Test: get_background_data() verwendet manuelle Feature-Extraktion wenn kein FeatureExtractor.
    
    Requirements:
    - Fallback zu manueller Feature-Extraktion
    - Features werden normalisiert (0-1)
    """
    from contexts.ragintegration.infrastructure.shap_background_data_repository_sqlite import (
        SHAPBackgroundDataRepositorySQLite
    )
    
    repo = SHAPBackgroundDataRepositorySQLite(db_session, max_records=1000)
    
    # Erstelle Record
    repo.add_record(
        query="Test Query",
        vector_score=0.8,
        text_score=0.7,
        user_level=5,
        keyword_matches=2,
        chunk_length=150,
        heading_hierarchy_depth=2,
        confidence_score=0.9
    )
    
    # Get Background Data
    background_data = repo.get_background_data(n_samples=1)
    
    # Assertions
    assert background_data.shape == (1, 7)
    # Prüfe Features (normalisiert)
    assert 0.0 <= background_data[0][0] <= 1.0  # vector_score
    assert 0.0 <= background_data[0][1] <= 1.0  # text_score
    assert 0.0 <= background_data[0][2] <= 1.0  # user_level (normalisiert)


def test_get_background_data_n_samples_limit(db_session: Session):
    """
    Test: get_background_data() respektiert n_samples Parameter.
    
    Requirements:
    - n_samples begrenzt Anzahl zurückgegebener Samples
    - Zufällige Auswahl wenn n_samples < total
    """
    from contexts.ragintegration.infrastructure.shap_background_data_repository_sqlite import (
        SHAPBackgroundDataRepositorySQLite
    )
    
    repo = SHAPBackgroundDataRepositorySQLite(db_session, max_records=1000)
    
    # Erstelle 10 Records
    for i in range(10):
        repo.add_record(
            query=f"Query {i}",
            vector_score=0.5,
            text_score=0.5,
            user_level=1,
            keyword_matches=0,
            chunk_length=100,
            heading_hierarchy_depth=0,
            confidence_score=0.5
        )
    
    # Get mit limit
    background_data = repo.get_background_data(n_samples=5)
    
    # Assertions
    assert background_data.shape[0] == 5, "Sollte nur 5 Samples zurückgeben"


# ============================================================================
# Test 3: Rolling Window
# ============================================================================

def test_rolling_window_deletes_old_records(db_session: Session):
    """
    Test: Rolling Window löscht alte Records wenn max_records überschritten.
    
    Requirements:
    - Wenn > max_records Records, werden älteste gelöscht
    - Nur die neuesten max_records bleiben erhalten
    """
    from contexts.ragintegration.infrastructure.shap_background_data_repository_sqlite import (
        SHAPBackgroundDataRepositorySQLite
    )
    
    max_records = 5
    repo = SHAPBackgroundDataRepositorySQLite(db_session, max_records=max_records)
    
    # Erstelle 10 Records (mehr als max_records)
    for i in range(10):
        repo.add_record(
            query=f"Query {i}",
            vector_score=0.5,
            text_score=0.5,
            user_level=1,
            keyword_matches=0,
            chunk_length=100,
            heading_hierarchy_depth=0,
            confidence_score=0.5
        )
    
    # Prüfe DB
    total_records = db_session.query(SHAPBackgroundDataModel).count()
    
    # Assertions
    assert total_records == max_records, f"Sollte nur {max_records} Records haben (Rolling Window)"
    
    # Prüfe ob die neuesten Records vorhanden sind
    records = db_session.query(SHAPBackgroundDataModel).order_by(
        SHAPBackgroundDataModel.created_at.desc()
    ).all()
    
    # Die letzten 5 Queries sollten vorhanden sein (Query 5-9)
    queries = [r.query for r in records]
    assert "Query 9" in queries, "Neueste Query sollte vorhanden sein"
    assert "Query 0" not in queries, "Älteste Query sollte gelöscht sein"


def test_rolling_window_preserves_newest_records(db_session: Session):
    """
    Test: Rolling Window behält die neuesten Records.
    
    Requirements:
    - Neueste Records bleiben erhalten
    - Älteste werden gelöscht
    """
    from contexts.ragintegration.infrastructure.shap_background_data_repository_sqlite import (
        SHAPBackgroundDataRepositorySQLite
    )
    import time
    
    max_records = 3
    repo = SHAPBackgroundDataRepositorySQLite(db_session, max_records=max_records)
    
    # Erstelle Records mit Pause (für verschiedene Timestamps)
    for i in range(5):
        repo.add_record(
            query=f"Query {i}",
            vector_score=0.5,
            text_score=0.5,
            user_level=1,
            keyword_matches=0,
            chunk_length=100,
            heading_hierarchy_depth=0,
            confidence_score=0.5
        )
        time.sleep(0.01)  # Kleine Pause für verschiedene Timestamps
    
    # Prüfe DB
    records = db_session.query(SHAPBackgroundDataModel).order_by(
        SHAPBackgroundDataModel.created_at.desc()
    ).all()
    
    # Assertions
    assert len(records) == max_records
    # Neueste Queries sollten vorhanden sein
    queries = [r.query for r in records]
    assert "Query 4" in queries, "Neueste Query sollte vorhanden sein"
    assert "Query 3" in queries, "Zweite neueste Query sollte vorhanden sein"
    assert "Query 2" in queries, "Dritte neueste Query sollte vorhanden sein"


# ============================================================================
# Test 4: get_statistics
# ============================================================================

def test_get_statistics(db_session: Session):
    """
    Test: get_statistics() gibt korrekte Statistiken zurück.
    
    Requirements:
    - total_records: Anzahl Records
    - background_data_shape: Shape des Background-Arrays
    - last_update: Letzte Aktualisierung
    """
    from contexts.ragintegration.infrastructure.shap_background_data_repository_sqlite import (
        SHAPBackgroundDataRepositorySQLite
    )
    
    repo = SHAPBackgroundDataRepositorySQLite(db_session, max_records=1000)
    
    # Erstelle Records
    for i in range(5):
        repo.add_record(
            query=f"Query {i}",
            vector_score=0.5,
            text_score=0.5,
            user_level=1,
            keyword_matches=0,
            chunk_length=100,
            heading_hierarchy_depth=0,
            confidence_score=0.5
        )
    
    # Aktualisiere Background-Daten (durch get_background_data)
    repo.get_background_data()
    
    # Get Statistics
    stats = repo.get_statistics()
    
    # Assertions
    assert stats['total_records'] == 5
    assert stats['background_data_shape'] == (5, 7)  # 5 Records, 7 Features
    assert stats['last_update'] is not None

