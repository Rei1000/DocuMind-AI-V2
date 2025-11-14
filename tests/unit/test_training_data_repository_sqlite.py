"""
Unit Tests für TrainingDataRepositorySQLite

Tests für SQLite-basiertes Training Data Repository.
Ersetzt FileBasedTrainingDataRepository.

TDD Phase 4: Tests ZUERST (RED), dann Implementierung (GREEN)
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models import User, TrainingSampleModel
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
    from backend.app.models import User, TrainingSampleModel
    
    # Erstelle temporäre Test-DB
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Erstelle Engine für Test-DB
    test_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )
    
    # Erstelle Tabellen
    User.__table__.create(bind=test_engine, checkfirst=True)
    TrainingSampleModel.__table__.create(bind=test_engine, checkfirst=True)
    
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
# Test 1: save_training_sample
# ============================================================================

def test_save_training_sample_to_db(db_session: Session):
    """
    Test: Training-Sample kann in DB gespeichert werden.
    
    Requirements:
    - save_training_sample() speichert Sample
    - Sample hat ID nach Speichern
    - Alle Felder werden korrekt gespeichert
    """
    from contexts.ragintegration.infrastructure.ml.training_data_repository_sqlite import (
        TrainingDataRepositorySQLite
    )
    
    repo = TrainingDataRepositorySQLite(db_session)
    
    # Erstelle Sample
    sample = {
        'query': 'Test Query',
        'chunk_id': 'chunk_123',
        'features': {
            'vector_score': 0.85,
            'text_score': 0.72,
            'hybrid_score': 0.81
        },
        'relevance_score': 0.9,
        'source': 'feedback'
    }
    
    # Save
    result = repo.save_training_sample(sample)
    
    # Assertions
    assert result is True, "Save sollte erfolgreich sein"
    
    # Prüfe ob Sample in DB ist
    db_sample = db_session.query(TrainingSampleModel).filter(
        TrainingSampleModel.query == 'Test Query'
    ).first()
    
    assert db_sample is not None, "Sample sollte in DB sein"
    assert db_sample.chunk_id == 'chunk_123'
    assert db_sample.relevance_score == 0.9
    assert db_sample.source == 'feedback'
    
    # Prüfe JSON-Deserialisierung
    features = json.loads(db_sample.features_json)
    assert features['vector_score'] == 0.85


def test_save_training_sample_with_user_id(db_session: Session):
    """
    Test: Training-Sample kann mit user_id gespeichert werden.
    
    Requirements:
    - Optional user_id wird gespeichert
    - Optional feedback_id wird gespeichert
    """
    from contexts.ragintegration.infrastructure.ml.training_data_repository_sqlite import (
        TrainingDataRepositorySQLite
    )
    
    repo = TrainingDataRepositorySQLite(db_session)
    
    sample = {
        'query': 'Test Query',
        'chunk_id': 'chunk_1',
        'features': {'vector_score': 0.5},
        'relevance_score': 0.8,
        'source': 'feedback',
        'user_id': 1,
        'feedback_id': 5
    }
    
    result = repo.save_training_sample(sample)
    assert result is True
    
    # Prüfe DB
    db_sample = db_session.query(TrainingSampleModel).filter(
        TrainingSampleModel.query == 'Test Query'
    ).first()
    
    assert db_sample.user_id == 1
    assert db_sample.feedback_id == 5


def test_save_training_sample_auto_timestamp(db_session: Session):
    """
    Test: Training-Sample bekommt automatisch Timestamp.
    
    Requirements:
    - created_at wird automatisch gesetzt wenn nicht vorhanden
    - Timestamp ist ISO-8601 Format
    """
    from contexts.ragintegration.infrastructure.ml.training_data_repository_sqlite import (
        TrainingDataRepositorySQLite
    )
    
    repo = TrainingDataRepositorySQLite(db_session)
    
    sample = {
        'query': 'Test Query',
        'chunk_id': 'chunk_1',
        'features': {'vector_score': 0.5},
        'relevance_score': 0.8,
        'source': 'system'
        # Kein timestamp!
    }
    
    result = repo.save_training_sample(sample)
    assert result is True
    
    # Prüfe DB
    db_sample = db_session.query(TrainingSampleModel).filter(
        TrainingSampleModel.query == 'Test Query'
    ).first()
    
    assert db_sample.created_at is not None
    # Prüfe ob ISO-8601 Format
    datetime.fromisoformat(db_sample.created_at)


# ============================================================================
# Test 2: get_training_samples
# ============================================================================

def test_load_training_samples_from_db(db_session: Session):
    """
    Test: Training-Samples können aus DB geladen werden.
    
    Requirements:
    - get_training_samples() lädt alle Samples
    - Samples haben korrektes Format (Dict)
    """
    from contexts.ragintegration.infrastructure.ml.training_data_repository_sqlite import (
        TrainingDataRepositorySQLite
    )
    
    repo = TrainingDataRepositorySQLite(db_session)
    
    # Erstelle 3 Samples
    for i in range(3):
        sample = {
            'query': f'Query {i}',
            'chunk_id': f'chunk_{i}',
            'features': {'vector_score': 0.5 + i * 0.1},
            'relevance_score': 0.5 + i * 0.1,
            'source': 'system'
        }
        repo.save_training_sample(sample)
    
    # Load
    samples = repo.get_training_samples()
    
    # Assertions
    assert len(samples) == 3, "Sollte 3 Samples zurückgeben"
    assert samples[0]['query'] == 'Query 0'
    assert samples[1]['query'] == 'Query 1'
    assert samples[2]['query'] == 'Query 2'


def test_filter_by_date(db_session: Session):
    """
    Test: get_training_samples() filtert nach Datum.
    
    Requirements:
    - min_date filtert Samples
    - Nur Samples nach min_date werden zurückgegeben
    """
    from contexts.ragintegration.infrastructure.ml.training_data_repository_sqlite import (
        TrainingDataRepositorySQLite
    )
    
    repo = TrainingDataRepositorySQLite(db_session)
    
    # Erstelle Samples mit verschiedenen Timestamps
    now = datetime.now()
    
    # Sample 1: Vor 2 Tagen
    sample1 = {
        'query': 'Old Query',
        'chunk_id': 'chunk_old',
        'features': {'vector_score': 0.5},
        'relevance_score': 0.5,
        'source': 'system',
        'timestamp': (now - timedelta(days=2)).isoformat()
    }
    repo.save_training_sample(sample1)
    
    # Sample 2: Heute
    sample2 = {
        'query': 'New Query',
        'chunk_id': 'chunk_new',
        'features': {'vector_score': 0.8},
        'relevance_score': 0.8,
        'source': 'system',
        'timestamp': now.isoformat()
    }
    repo.save_training_sample(sample2)
    
    # Filter: Nur Samples von gestern bis heute
    min_date = now - timedelta(days=1)
    samples = repo.get_training_samples(min_date=min_date)
    
    # Assertions
    assert len(samples) == 1, "Sollte nur 1 Sample zurückgeben (nach min_date)"
    assert samples[0]['query'] == 'New Query'


def test_limit_parameter(db_session: Session):
    """
    Test: get_training_samples() respektiert limit Parameter.
    
    Requirements:
    - limit begrenzt Anzahl zurückgegebener Samples
    """
    from contexts.ragintegration.infrastructure.ml.training_data_repository_sqlite import (
        TrainingDataRepositorySQLite
    )
    
    repo = TrainingDataRepositorySQLite(db_session)
    
    # Erstelle 10 Samples
    for i in range(10):
        sample = {
            'query': f'Query {i}',
            'chunk_id': f'chunk_{i}',
            'features': {'vector_score': 0.5},
            'relevance_score': 0.5,
            'source': 'system'
        }
        repo.save_training_sample(sample)
    
    # Load mit limit
    samples = repo.get_training_samples(limit=5)
    
    # Assertions
    assert len(samples) == 5, "Sollte nur 5 Samples zurückgeben"


def test_json_conversion(db_session: Session):
    """
    Test: Features werden korrekt JSON-serialisiert/deserialisiert.
    
    Requirements:
    - Features werden als JSON gespeichert
    - Features werden als Dict zurückgegeben
    """
    from contexts.ragintegration.infrastructure.ml.training_data_repository_sqlite import (
        TrainingDataRepositorySQLite
    )
    
    repo = TrainingDataRepositorySQLite(db_session)
    
    # Komplexe Features
    features = {
        'vector_score': 0.85,
        'text_score': 0.72,
        'hybrid_score': 0.81,
        'keyword_matches': 2,
        'chunk_length': 150,
        'heading_hierarchy_depth': 2,
        'confidence_score': 0.95
    }
    
    sample = {
        'query': 'Test Query',
        'chunk_id': 'chunk_1',
        'features': features,
        'relevance_score': 0.9,
        'source': 'feedback'
    }
    
    repo.save_training_sample(sample)
    
    # Load
    samples = repo.get_training_samples()
    
    # Assertions
    assert len(samples) == 1
    loaded_features = samples[0]['features']
    assert isinstance(loaded_features, dict)
    assert loaded_features['vector_score'] == 0.85
    assert loaded_features['hybrid_score'] == 0.81
    assert loaded_features['keyword_matches'] == 2


# ============================================================================
# Test 3: get_statistics
# ============================================================================

def test_get_statistics(db_session: Session):
    """
    Test: get_statistics() gibt korrekte Statistiken zurück.
    
    Requirements:
    - total_samples: Anzahl aller Samples
    - oldest_sample: Ältestes Sample (ISO-8601)
    - newest_sample: Neuestes Sample (ISO-8601)
    - unique_queries: Anzahl eindeutiger Queries
    """
    from contexts.ragintegration.infrastructure.ml.training_data_repository_sqlite import (
        TrainingDataRepositorySQLite
    )
    
    repo = TrainingDataRepositorySQLite(db_session)
    
    # Erstelle Samples
    now = datetime.now()
    for i in range(5):
        sample = {
            'query': f'Query {i % 3}',  # 3 eindeutige Queries
            'chunk_id': f'chunk_{i}',
            'features': {'vector_score': 0.5},
            'relevance_score': 0.5,
            'source': 'system',
            'timestamp': (now - timedelta(days=4-i)).isoformat()  # Verschiedene Timestamps
        }
        repo.save_training_sample(sample)
    
    # Get Statistics
    stats = repo.get_statistics()
    
    # Assertions
    assert stats['total_samples'] == 5
    assert stats['unique_queries'] == 3  # Query 0, 1, 2
    assert stats['oldest_sample'] is not None
    assert stats['newest_sample'] is not None
    
    # Prüfe ISO-8601 Format
    datetime.fromisoformat(stats['oldest_sample'])
    datetime.fromisoformat(stats['newest_sample'])


def test_get_statistics_empty_db(db_session: Session):
    """
    Test: get_statistics() mit leerer DB.
    
    Requirements:
    - Gibt leere Statistiken zurück wenn keine Samples vorhanden
    """
    from contexts.ragintegration.infrastructure.ml.training_data_repository_sqlite import (
        TrainingDataRepositorySQLite
    )
    
    repo = TrainingDataRepositorySQLite(db_session)
    
    stats = repo.get_statistics()
    
    # Assertions
    assert stats['total_samples'] == 0
    assert stats['oldest_sample'] is None
    assert stats['newest_sample'] is None
    assert stats['unique_queries'] == 0

