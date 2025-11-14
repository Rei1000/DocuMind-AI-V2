"""
Unit Tests für SQLAlchemy Models: ML/SHAP SQLite-Persistenz

Tests für die neuen SQLite-Models:
- TrainingSampleModel (training_samples)
- SHAPBackgroundDataModel (shap_background_data)
- SHAPCacheEntryModel (shap_cache)

TDD Phase 1: Tests ZUERST (RED), dann Implementierung (GREEN)
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
import json
import os
import tempfile


# ============================================================================
# Test Setup
# ============================================================================

@pytest.fixture
def db_session():
    """Erstelle Test-DB-Session mit separater Test-DB."""
    # Importiere nur die Models die wir testen wollen
    from backend.app.models import (
        TrainingSampleModel,
        SHAPBackgroundDataModel,
        SHAPCacheEntryModel,
        User  # Für Foreign Key
    )
    
    # Erstelle temporäre Test-DB
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Erstelle Engine für Test-DB
    test_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )
    
    # Erstelle nur die benötigten Tabellen (ohne Foreign Key Constraints)
    # Erstelle User-Tabelle zuerst (für Foreign Key)
    User.__table__.create(bind=test_engine, checkfirst=True)
    # Dann die neuen Tabellen
    TrainingSampleModel.__table__.create(bind=test_engine, checkfirst=True)
    SHAPBackgroundDataModel.__table__.create(bind=test_engine, checkfirst=True)
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
# Test 1: TrainingSampleModel
# ============================================================================

def test_training_sample_model_creation(db_session: Session):
    """
    Test: TrainingSampleModel kann erstellt und gespeichert werden.
    
    Requirements:
    - Alle Felder können gesetzt werden
    - JSON-Serialisierung für features_json funktioniert
    - created_at wird automatisch gesetzt
    """
    from backend.app.models import TrainingSampleModel
    
    # Erstelle Sample
    features = {
        'vector_score': 0.85,
        'text_score': 0.72,
        'hybrid_score': 0.81,
        'keyword_matches': 2,
        'chunk_length': 150
    }
    
    sample = TrainingSampleModel(
        query="Was sind die wichtigsten Schritte?",
        chunk_id="chunk_123",
        features_json=json.dumps(features),
        relevance_score=0.9,
        source="feedback",
        user_id=1,
        feedback_id=5,
        created_at=datetime.now().isoformat()
    )
    
    db_session.add(sample)
    db_session.commit()
    db_session.refresh(sample)
    
    # Assertions
    assert sample.id is not None
    assert sample.query == "Was sind die wichtigsten Schritte?"
    assert sample.chunk_id == "chunk_123"
    assert sample.relevance_score == 0.9
    assert sample.source == "feedback"
    assert sample.user_id == 1
    assert sample.feedback_id == 5
    assert sample.created_at is not None
    
    # JSON-Deserialisierung testen
    loaded_features = json.loads(sample.features_json)
    assert loaded_features['vector_score'] == 0.85
    assert loaded_features['hybrid_score'] == 0.81


def test_training_sample_json_serialization(db_session: Session):
    """
    Test: TrainingSampleModel features_json Property funktioniert.
    
    Requirements:
    - @property features gibt dict zurück
    - JSON wird korrekt deserialisiert
    """
    from backend.app.models import TrainingSampleModel
    
    features = {
        'vector_score': 0.75,
        'text_score': 0.68,
        'hybrid_score': 0.72
    }
    
    sample = TrainingSampleModel(
        query="Test Query",
        chunk_id="chunk_1",
        features_json=json.dumps(features),
        relevance_score=0.8,
        source="system",
        created_at=datetime.now().isoformat()
    )
    
    db_session.add(sample)
    db_session.commit()
    db_session.refresh(sample)
    
    # Test @property features
    assert hasattr(sample, 'features'), "TrainingSampleModel sollte 'features' Property haben"
    loaded_features = sample.features
    assert isinstance(loaded_features, dict)
    assert loaded_features['vector_score'] == 0.75
    assert loaded_features['hybrid_score'] == 0.72


def test_training_sample_optional_fields(db_session: Session):
    """
    Test: TrainingSampleModel optional fields (user_id, feedback_id) funktionieren.
    
    Requirements:
    - user_id kann None sein
    - feedback_id kann None sein
    """
    from backend.app.models import TrainingSampleModel
    
    sample = TrainingSampleModel(
        query="Auto-generated sample",
        chunk_id="chunk_auto",
        features_json=json.dumps({'vector_score': 0.5}),
        relevance_score=0.5,
        source="auto",
        created_at=datetime.now().isoformat()
        # user_id und feedback_id nicht gesetzt (sollten None sein)
    )
    
    db_session.add(sample)
    db_session.commit()
    db_session.refresh(sample)
    
    assert sample.id is not None
    assert sample.user_id is None
    assert sample.feedback_id is None


# ============================================================================
# Test 2: SHAPBackgroundDataModel
# ============================================================================

def test_shap_background_data_model(db_session: Session):
    """
    Test: SHAPBackgroundDataModel kann erstellt und gespeichert werden.
    
    Requirements:
    - Alle Felder können gesetzt werden
    - created_at wird automatisch gesetzt
    """
    from backend.app.models import SHAPBackgroundDataModel
    
    record = SHAPBackgroundDataModel(
        query="Test Query",
        vector_score=0.85,
        text_score=0.72,
        user_level=5,
        keyword_matches=2,
        chunk_length=150,
        heading_hierarchy_depth=2,
        confidence_score=0.95,
        created_at=datetime.now().isoformat()
    )
    
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    
    # Assertions
    assert record.id is not None
    assert record.query == "Test Query"
    assert record.vector_score == 0.85
    assert record.text_score == 0.72
    assert record.user_level == 5
    assert record.keyword_matches == 2
    assert record.chunk_length == 150
    assert record.heading_hierarchy_depth == 2
    assert record.confidence_score == 0.95
    assert record.created_at is not None


def test_shap_background_data_multiple_records(db_session: Session):
    """
    Test: Mehrere SHAPBackgroundDataModel Records können gespeichert werden.
    
    Requirements:
    - Rolling Window Simulation (mehrere Records)
    """
    from backend.app.models import SHAPBackgroundDataModel
    
    # Erstelle 5 Records
    records = []
    for i in range(5):
        record = SHAPBackgroundDataModel(
            query=f"Query {i}",
            vector_score=0.5 + i * 0.1,
            text_score=0.4 + i * 0.1,
            user_level=1 + i,
            keyword_matches=i,
            chunk_length=100 + i * 10,
            heading_hierarchy_depth=i % 3,
            confidence_score=0.5 + i * 0.1,
            created_at=datetime.now().isoformat()
        )
        records.append(record)
        db_session.add(record)
    
    db_session.commit()
    
    # Prüfe alle Records
    for i, record in enumerate(records):
        db_session.refresh(record)
        assert record.id is not None
        assert record.query == f"Query {i}"


# ============================================================================
# Test 3: SHAPCacheEntryModel
# ============================================================================

def test_shap_cache_model(db_session: Session):
    """
    Test: SHAPCacheEntryModel kann erstellt und gespeichert werden.
    
    Requirements:
    - cache_key ist UNIQUE
    - shap_values_json wird als JSON gespeichert
    - expires_at wird gesetzt
    """
    from backend.app.models import SHAPCacheEntryModel
    from datetime import timedelta
    
    shap_values = {
        'feature_importances': [0.3, 0.25, 0.2, 0.15, 0.1],
        'base_value': 0.5,
        'values': [0.1, 0.05, -0.02, 0.03, -0.01]
    }
    
    cache_entry = SHAPCacheEntryModel(
        cache_key="query_chunk_123",
        shap_values_json=json.dumps(shap_values),
        created_at=datetime.now().isoformat(),
        expires_at=(datetime.now() + timedelta(hours=1)).isoformat()
    )
    
    db_session.add(cache_entry)
    db_session.commit()
    db_session.refresh(cache_entry)
    
    # Assertions
    assert cache_entry.id is not None
    assert cache_entry.cache_key == "query_chunk_123"
    assert cache_entry.shap_values_json is not None
    
    # JSON-Deserialisierung testen
    loaded_values = json.loads(cache_entry.shap_values_json)
    assert loaded_values['base_value'] == 0.5
    assert len(loaded_values['feature_importances']) == 5


def test_shap_cache_unique_constraint(db_session: Session):
    """
    Test: SHAPCacheEntryModel cache_key ist UNIQUE.
    
    Requirements:
    - Duplikate cache_key sollten Fehler werfen
    """
    from backend.app.models import SHAPCacheEntryModel
    from datetime import timedelta
    from sqlalchemy.exc import IntegrityError
    
    cache_key = "unique_key_123"
    
    # Erster Eintrag
    entry1 = SHAPCacheEntryModel(
        cache_key=cache_key,
        shap_values_json=json.dumps({'value': 1}),
        created_at=datetime.now().isoformat(),
        expires_at=(datetime.now() + timedelta(hours=1)).isoformat()
    )
    db_session.add(entry1)
    db_session.commit()
    
    # Zweiter Eintrag mit gleichem Key (sollte fehlschlagen)
    entry2 = SHAPCacheEntryModel(
        cache_key=cache_key,  # Gleicher Key!
        shap_values_json=json.dumps({'value': 2}),
        created_at=datetime.now().isoformat(),
        expires_at=(datetime.now() + timedelta(hours=1)).isoformat()
    )
    db_session.add(entry2)
    
    # Sollte IntegrityError werfen
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    # Rollback nach Fehler (für saubere Session)
    db_session.rollback()


def test_shap_cache_expires_at(db_session: Session):
    """
    Test: SHAPCacheEntryModel expires_at wird korrekt gesetzt.
    
    Requirements:
    - expires_at ist in der Zukunft
    - Kann für TTL-Checks verwendet werden
    """
    from backend.app.models import SHAPCacheEntryModel
    from datetime import timedelta
    
    now = datetime.now()
    expires_at = now + timedelta(hours=1)
    
    cache_entry = SHAPCacheEntryModel(
        cache_key="test_key",
        shap_values_json=json.dumps({'value': 1}),
        created_at=now.isoformat(),
        expires_at=expires_at.isoformat()
    )
    
    db_session.add(cache_entry)
    db_session.commit()
    db_session.refresh(cache_entry)
    
    # Parse zurück zu datetime für Vergleich
    expires_dt = datetime.fromisoformat(cache_entry.expires_at)
    created_dt = datetime.fromisoformat(cache_entry.created_at)
    
    assert expires_dt > created_dt
    assert (expires_dt - created_dt).total_seconds() == pytest.approx(3600, abs=1)  # ~1 Stunde

