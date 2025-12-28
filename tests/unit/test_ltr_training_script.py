"""
Tests für LTR Model Training Script.

TDD: Tests für Fix 1 - LTR-Modell Training.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Mock sklearn BEVOR Import (falls nicht verfügbar)
try:
    import sklearn
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    # Mock sklearn Module
    import types
    sklearn = types.ModuleType('sklearn')
    sklearn.model_selection = types.ModuleType('sklearn.model_selection')
    sklearn.metrics = types.ModuleType('sklearn.metrics')
    sklearn.ensemble = types.ModuleType('sklearn.ensemble')
    
    # Mock Classes
    class MockGroupKFold:
        def __init__(self, n_splits=3):
            self.n_splits = n_splits
        def split(self, X, y, groups):
            # Mock: Teile in 2 Teile
            n = len(X)
            split_point = n // 2
            yield list(range(split_point)), list(range(split_point, n))
    
    class MockGradientBoostingRegressor:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
        def fit(self, X, y):
            self.X = X
            self.y = y
            return self
        def predict(self, X):
            import numpy as np
            # Mock: Gibt Durchschnitt von y zurück
            if hasattr(self, 'y'):
                return np.full(len(X), np.mean(self.y))
            return np.full(len(X), 0.5)
    
    sklearn.model_selection.GroupKFold = MockGroupKFold
    sklearn.metrics.ndcg_score = lambda y_true, y_pred, k=10: 0.8  # Mock NDCG
    sklearn.ensemble.GradientBoostingRegressor = MockGradientBoostingRegressor
    
    # Füge zu sys.modules hinzu
    sys.modules['sklearn'] = sklearn
    sys.modules['sklearn.model_selection'] = sklearn.model_selection
    sys.modules['sklearn.metrics'] = sklearn.metrics
    sys.modules['sklearn.ensemble'] = sklearn.ensemble

# Füge Projekt-Root zum Python-Pfad hinzu
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.database import SessionLocal
from contexts.ragintegration.infrastructure.ml.training_data_repository_sqlite import (
    TrainingDataRepositorySQLite
)
from contexts.ragintegration.infrastructure.ml.training_pipeline import (
    LTRTrainingPipeline
)


@pytest.fixture
def db_session():
    """Erstelle temporäre DB-Session für Tests."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from backend.app.models import TrainingSampleModel, User
    
    # Temporäre SQLite-DB
    test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    test_db.close()
    
    test_engine = create_engine(f'sqlite:///{test_db.name}')
    
    # Erstelle nur benötigte Tabellen (nicht alle via Base.metadata.create_all)
    # WICHTIG: User zuerst (für Foreign Key)
    User.__table__.create(bind=test_engine, checkfirst=True)
    TrainingSampleModel.__table__.create(bind=test_engine, checkfirst=True)
    
    Session = sessionmaker(bind=test_engine)
    session = Session()
    
    yield session
    
    session.close()
    os.unlink(test_db.name)


@pytest.fixture
def training_repo(db_session):
    """Erstelle Training-Repository."""
    return TrainingDataRepositorySQLite(db_session)


@pytest.fixture
def sample_training_data(training_repo):
    """Erstelle Test-Training-Daten."""
    import json
    from datetime import datetime
    
    # Erstelle 5 Test-Samples
    samples = [
        {
            'query': 'Was sind Sicherheitshinweise?',
            'chunk_id': 'chunk_1',
            'features': {
                'vector_score': 0.85,
                'text_score': 0.72,
                'bm25_score': 0.65,
                'jaccard_score': 0.58,
                'keyword_matches': 3,
                'chunk_length': 250,
                'document_type_encoded': 0.5,
                'heading_hierarchy_depth': 2,
                'confidence_score': 0.9,
                'user_level': 3,
                'hybrid_score': 0.81
            },
            'relevance_score': 0.9,
            'source': 'feedback',
            'timestamp': datetime.now().isoformat()
        },
        {
            'query': 'Was sind Sicherheitshinweise?',
            'chunk_id': 'chunk_2',
            'features': {
                'vector_score': 0.65,
                'text_score': 0.55,
                'bm25_score': 0.45,
                'jaccard_score': 0.40,
                'keyword_matches': 2,
                'chunk_length': 180,
                'document_type_encoded': 0.3,
                'heading_hierarchy_depth': 1,
                'confidence_score': 0.7,
                'user_level': 3,
                'hybrid_score': 0.62
            },
            'relevance_score': 0.6,
            'source': 'feedback',
            'timestamp': datetime.now().isoformat()
        },
        {
            'query': 'Wie funktioniert die Montage?',
            'chunk_id': 'chunk_3',
            'features': {
                'vector_score': 0.75,
                'text_score': 0.68,
                'bm25_score': 0.60,
                'jaccard_score': 0.55,
                'keyword_matches': 4,
                'chunk_length': 300,
                'document_type_encoded': 0.7,
                'heading_hierarchy_depth': 3,
                'confidence_score': 0.85,
                'user_level': 2,
                'hybrid_score': 0.73
            },
            'relevance_score': 0.8,
            'source': 'feedback',
            'timestamp': datetime.now().isoformat()
        }
    ]
    
    # Speichere Samples
    for sample in samples:
        training_repo.save_training_sample(sample)
    
    return samples


def test_ltr_training_pipeline_produces_model_file(training_repo, sample_training_data, tmp_path):
    """
    Test: LTRTrainingPipeline sollte Model-File erstellen.
    
    RED → GREEN → REFACTOR
    """
    # Arrange
    model_path = tmp_path / 'ltr_ranker_test.pkl'
    pipeline = LTRTrainingPipeline(
        training_data_repo=training_repo,
        model_type='sklearn',  # Verwende sklearn Fallback (kein LightGBM nötig)
        model_version='1.0.0'
    )
    
    # Act: Trainiere Model
    pipeline.train(
        num_boost_round=10,  # Weniger Runden für schnelleren Test
        learning_rate=0.1,
        max_depth=3,
        num_leaves=10
    )
    
    # Assert: Model ist trainiert
    assert pipeline.is_trained(), "Model sollte trainiert sein"
    
    # Act: Speichere Model
    pipeline.save_model(str(model_path))
    
    # Assert: Model-File existiert
    assert model_path.exists(), f"Model-File sollte existieren: {model_path}"
    assert model_path.stat().st_size > 0, "Model-File sollte nicht leer sein"


def test_ltr_inference_after_training(training_repo, sample_training_data, tmp_path):
    """
    Test: LTRInferenceService sollte nach Training funktionieren.
    
    RED → GREEN → REFACTOR
    """
    # Arrange: Trainiere Model
    model_path = tmp_path / 'ltr_ranker_test.pkl'
    pipeline = LTRTrainingPipeline(
        training_data_repo=training_repo,
        model_type='sklearn',
        model_version='1.0.0'
    )
    
    pipeline.train(
        num_boost_round=10,
        learning_rate=0.1,
        max_depth=3,
        num_leaves=10
    )
    pipeline.save_model(str(model_path))
    
    # Act: Lade Model in Inference Service
    from contexts.ragintegration.infrastructure.ml.inference_service import (
        LTRInferenceService
    )
    
    inference_service = LTRInferenceService(model_path=str(model_path))
    
    # Assert: Service ist ready
    assert inference_service.is_ready(), "Inference Service sollte ready sein"
    
    # Act: Mache Prediction
    test_chunk = {
        'chunk_id': 'test_chunk',
        'metadata': {
            'chunk_text': 'Test chunk text',
            'document_type': 'SOP',
            'chunk_length': 200,
            'heading_hierarchy_depth': 2,
            'confidence_score': 0.8
        }
    }
    
    ml_score = inference_service.predict_for_chunk(
        query='Test query',
        chunk=test_chunk,
        vector_score=0.8,
        text_score=0.7,
        bm25_score=0.6,
        jaccard_score=0.5,
        keyword_matches=3,
        user_level=3,
        hybrid_score=0.75
    )
    
    # Assert: ML-Score ist ein float
    assert isinstance(ml_score, float), f"ML-Score sollte float sein, ist {type(ml_score)}"
    assert 0.0 <= ml_score <= 1.0, f"ML-Score sollte zwischen 0 und 1 sein, ist {ml_score}"
    
    # Act: Kombiniere Scores
    final_score = inference_service.combine_scores(
        hybrid_score=0.75,
        ml_score=ml_score
    )
    
    # Assert: Final-Score ist berechnet
    assert isinstance(final_score, float), "Final-Score sollte float sein"
    assert 0.0 <= final_score <= 1.0, f"Final-Score sollte zwischen 0 und 1 sein, ist {final_score}"


def test_training_script_with_mock():
    """
    Test: Training-Script sollte mit Mock-Dependencies funktionieren.
    
    Prüft ob Script-Struktur korrekt ist.
    """
    # Arrange: Mock sklearn
    with patch('sklearn.model_selection.GroupKFold') as mock_gkf, \
         patch('sklearn.metrics.ndcg_score') as mock_ndcg, \
         patch('sklearn.ensemble.GradientBoostingRegressor') as mock_gbr:
        
        # Mock sklearn Module
        mock_sklearn = MagicMock()
        mock_sklearn.model_selection.GroupKFold = mock_gkf
        mock_sklearn.metrics.ndcg_score = mock_ndcg
        mock_sklearn.ensemble.GradientBoostingRegressor = mock_gbr
        
        # Prüfe ob Script importierbar ist (mit Mocks)
        # Das ist ein struktureller Test - prüft ob Code kompiliert
        try:
            from scripts.train_ltr_model import train_ltr_model
            assert callable(train_ltr_model), "train_ltr_model sollte eine Funktion sein"
        except ImportError as e:
            # OK wenn sklearn nicht verfügbar ist (wird in Script geprüft)
            if 'sklearn' in str(e):
                pytest.skip("sklearn nicht verfügbar (erwartet für lokale Tests)")
            else:
                raise

