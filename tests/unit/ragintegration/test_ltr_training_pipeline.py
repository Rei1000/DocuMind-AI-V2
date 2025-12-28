"""
Unit Tests für Learning-to-Rank Training Pipeline.

TDD Phase 1: RED - Tests für ML Model Training.

Diese Tests definieren Anforderungen für LTR Training:
1. Training-Daten laden und vorbereiten
2. Model trainieren (LightGBM/XGBoost)
3. Model speichern und laden
4. Cross-Validation
5. Model-Metriken (NDCG@k)
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from typing import Dict, List, Any


# ========================================
# Test 1: Training Data Preparation
# ========================================

def test_training_pipeline_prepares_data_correctly():
    """
    Training Pipeline sollte Daten korrekt vorbereiten.
    
    Requirements:
    - Lädt Training-Daten aus Repository
    - Extrahiert Features mit MLFeatureExtractor
    - Erstellt X (Features) und y (Relevance Scores)
    - Erstellt qids (Query-IDs) für Ranking
    """
    from contexts.ragintegration.infrastructure.ml.training_pipeline import LTRTrainingPipeline
    
    # Mock Training Data Repository
    mock_repo = Mock()
    mock_repo.get_training_samples.return_value = [
        {
            'query': 'Test Query 1',
            'chunk': {'chunk_id': 'chunk_1', 'metadata': {'chunk_text': 'Text 1', 'document_type': 'Arbeitsanweisung', 'chunk_length': 100}},
            'vector_score': 0.8,
            'text_score': 0.7,
            'bm25_score': 0.65,
            'jaccard_score': 0.55,
            'keyword_matches': 2,
            'user_level': 3,
            'hybrid_score': 0.77,
            'relevance_score': 0.9  # Ground Truth
        },
        {
            'query': 'Test Query 1',
            'chunk': {'chunk_id': 'chunk_2', 'metadata': {'chunk_text': 'Text 2', 'document_type': 'SOP', 'chunk_length': 200}},
            'vector_score': 0.75,
            'text_score': 0.65,
            'bm25_score': 0.60,
            'jaccard_score': 0.50,
            'keyword_matches': 1,
            'user_level': 3,
            'hybrid_score': 0.72,
            'relevance_score': 0.7
        }
    ]
    
    # Erstelle Pipeline
    pipeline = LTRTrainingPipeline(training_data_repo=mock_repo)
    
    # Prepare Data
    X, y, qids = pipeline.prepare_training_data()
    
    # Assertions
    assert X is not None, "X (Features) sollte nicht None sein"
    assert y is not None, "y (Relevance Scores) sollte nicht None sein"
    assert qids is not None, "qids (Query-IDs) sollte nicht None sein"
    
    assert isinstance(X, np.ndarray), "X sollte numpy array sein"
    assert isinstance(y, np.ndarray), "y sollte numpy array sein"
    assert isinstance(qids, np.ndarray), "qids sollte numpy array sein"
    
    assert X.shape[0] == 2, "X sollte 2 Samples haben"
    assert X.shape[1] == 11, "X sollte 11 Features haben"
    assert y.shape == (2,), "y sollte 2 Relevance Scores haben"
    assert qids.shape == (2,), "qids sollte 2 Query-IDs haben"


# ========================================
# Test 2: Model Training
# ========================================

def test_training_pipeline_trains_model():
    """
    Training Pipeline sollte LTR-Modell trainieren.
    
    Requirements:
    - Verwendet LightGBM oder XGBoost Ranker
    - fit(X, y, qids) funktioniert
    - Model ist danach trainiert
    - is_trained() gibt True zurück
    """
    from contexts.ragintegration.infrastructure.ml.training_pipeline import LTRTrainingPipeline
    
    # Mock Training Data Repository mit ausreichend Daten
    mock_repo = Mock()
    
    # Generiere Mock-Daten (mindestens 20 Samples für Training)
    training_samples = []
    for i in range(20):
        training_samples.append({
            'query': f'Query {i % 5}',  # 5 verschiedene Queries
            'chunk': {
                'chunk_id': f'chunk_{i}',
                'metadata': {
                    'chunk_text': f'Text {i}',
                    'document_type': 'Arbeitsanweisung' if i % 2 == 0 else 'SOP',
                    'chunk_length': 100 + i * 10,
                    'heading_hierarchy_depth': i % 3,
                    'confidence_score': 0.8 + (i % 10) * 0.01
                }
            },
            'vector_score': 0.7 + (i % 10) * 0.02,
            'text_score': 0.6 + (i % 10) * 0.02,
            'bm25_score': 0.5 + (i % 10) * 0.02,
            'jaccard_score': 0.4 + (i % 10) * 0.02,
            'keyword_matches': i % 5,
            'user_level': (i % 5) + 1,
            'hybrid_score': 0.65 + (i % 10) * 0.02,
            'relevance_score': 0.5 + (i % 10) * 0.03  # Ground Truth
        })
    
    mock_repo.get_training_samples.return_value = training_samples
    
    # Erstelle Pipeline
    pipeline = LTRTrainingPipeline(training_data_repo=mock_repo)
    
    # Train Model
    model = pipeline.train()
    
    # Assertions
    assert model is not None, "Model sollte nicht None sein"
    assert pipeline.is_trained(), "Pipeline sollte trainiert sein"
    assert hasattr(model, 'predict'), "Model sollte predict() Methode haben"


# ========================================
# Test 3: Model Persistence
# ========================================

def test_training_pipeline_saves_and_loads_model():
    """
    Training Pipeline sollte Model speichern und laden können.
    
    Requirements:
    - save_model(path) speichert Model
    - load_model(path) lädt Model
    - Geladenes Model funktioniert identisch
    """
    from contexts.ragintegration.infrastructure.ml.training_pipeline import LTRTrainingPipeline
    import tempfile
    import os
    
    # Mock Repository
    mock_repo = Mock()
    training_samples = []
    for i in range(20):
        training_samples.append({
            'query': f'Query {i % 5}',
            'chunk': {
                'chunk_id': f'chunk_{i}',
                'metadata': {
                    'chunk_text': f'Text {i}',
                    'document_type': 'Arbeitsanweisung',
                    'chunk_length': 100,
                    'heading_hierarchy_depth': 1,
                    'confidence_score': 0.9
                }
            },
            'vector_score': 0.8,
            'text_score': 0.7,
            'bm25_score': 0.65,
            'jaccard_score': 0.55,
            'keyword_matches': 2,
            'user_level': 3,
            'hybrid_score': 0.77,
            'relevance_score': 0.8
        })
    mock_repo.get_training_samples.return_value = training_samples
    
    # Train Model
    pipeline = LTRTrainingPipeline(training_data_repo=mock_repo)
    model = pipeline.train()
    
    # Test-Prediction vor Save
    test_features = np.random.rand(1, 11)
    prediction_before = model.predict(test_features)
    
    # Save Model
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = os.path.join(tmpdir, 'test_model.pkl')
        pipeline.save_model(model_path)
        
        # Assertions - File existiert
        assert os.path.exists(model_path), "Model-File sollte existieren"
        
        # Load Model
        loaded_model = pipeline.load_model(model_path)
        
        # Assertions - Model funktioniert
        assert loaded_model is not None, "Geladenes Model sollte nicht None sein"
        prediction_after = loaded_model.predict(test_features)
        
        # Predictions sollten identisch sein
        assert np.allclose(prediction_before, prediction_after, atol=0.001), \
            "Predictions vor und nach Load sollten identisch sein"


# ========================================
# Test 4: Model Validation
# ========================================

def test_training_pipeline_validates_model():
    """
    Training Pipeline sollte Model validieren.
    
    Requirements:
    - Cross-Validation durchführen
    - NDCG@k Metrik berechnen
    - Validation Score zurückgeben
    """
    from contexts.ragintegration.infrastructure.ml.training_pipeline import LTRTrainingPipeline
    
    # Mock Repository mit genug Daten
    mock_repo = Mock()
    training_samples = []
    for i in range(50):  # Mehr Daten für CV
        training_samples.append({
            'query': f'Query {i % 10}',
            'chunk': {
                'chunk_id': f'chunk_{i}',
                'metadata': {
                    'chunk_text': f'Text {i}',
                    'document_type': 'Arbeitsanweisung',
                    'chunk_length': 100,
                    'heading_hierarchy_depth': 1,
                    'confidence_score': 0.9
                }
            },
            'vector_score': 0.7 + (i % 10) * 0.02,
            'text_score': 0.6 + (i % 10) * 0.02,
            'bm25_score': 0.5 + (i % 10) * 0.02,
            'jaccard_score': 0.4 + (i % 10) * 0.02,
            'keyword_matches': i % 5,
            'user_level': 3,
            'hybrid_score': 0.65 + (i % 10) * 0.02,
            'relevance_score': 0.5 + (i % 10) * 0.03
        })
    mock_repo.get_training_samples.return_value = training_samples
    
    # Train und Validate
    pipeline = LTRTrainingPipeline(training_data_repo=mock_repo)
    validation_scores = pipeline.train_and_validate(n_splits=3)
    
    # Assertions
    assert validation_scores is not None, "Validation Scores sollten nicht None sein"
    assert isinstance(validation_scores, dict), "Validation Scores sollten Dict sein"
    assert 'ndcg_mean' in validation_scores, "Validation sollte ndcg_mean enthalten"
    assert 'ndcg_std' in validation_scores, "Validation sollte ndcg_std enthalten"
    
    # NDCG sollte im plausiblen Bereich sein [0, 1]
    assert 0 <= validation_scores['ndcg_mean'] <= 1, "NDCG Mean sollte in [0, 1] sein"


# ========================================
# Test 5: Model Prediction
# ========================================

def test_trained_model_can_predict():
    """
    Trainiertes Model sollte Predictions machen können.
    
    Requirements:
    - predict(X) funktioniert
    - Rückgabe ist numpy array
    - Werte sind im plausiblen Bereich
    """
    from contexts.ragintegration.infrastructure.ml.training_pipeline import LTRTrainingPipeline
    
    # Mock Repository
    mock_repo = Mock()
    training_samples = []
    for i in range(30):
        training_samples.append({
            'query': f'Query {i % 5}',
            'chunk': {
                'chunk_id': f'chunk_{i}',
                'metadata': {
                    'chunk_text': f'Text {i}',
                    'document_type': 'Arbeitsanweisung',
                    'chunk_length': 100,
                    'heading_hierarchy_depth': 1,
                    'confidence_score': 0.9
                }
            },
            'vector_score': 0.8,
            'text_score': 0.7,
            'bm25_score': 0.65,
            'jaccard_score': 0.55,
            'keyword_matches': 2,
            'user_level': 3,
            'hybrid_score': 0.77,
            'relevance_score': 0.8
        })
    mock_repo.get_training_samples.return_value = training_samples
    
    # Train
    pipeline = LTRTrainingPipeline(training_data_repo=mock_repo)
    model = pipeline.train()
    
    # Test-Features
    test_X = np.random.rand(5, 11)  # 5 Samples, 11 Features
    
    # Predict
    predictions = model.predict(test_X)
    
    # Assertions
    assert isinstance(predictions, np.ndarray), "Predictions sollten numpy array sein"
    assert predictions.shape == (5,), f"Predictions sollten (5,) sein, aber sind {predictions.shape}"
    
    # Predictions sollten plausibel sein
    # (Für Regression-Modelle können sie außerhalb [0, 1] sein, aber sollten nicht extrem sein)
    assert np.all(predictions > -5), "Predictions sollten nicht zu negativ sein"
    assert np.all(predictions < 5), "Predictions sollten nicht zu hoch sein"

