"""
Unit Tests für LTR Inference Service.

TDD Phase 1: RED - Tests für ML Model Serving.

Diese Tests definieren Anforderungen für LTR Inference:
1. Model wird bei Init geladen
2. Predictions funktionieren
3. Score-Kombination (hybrid + ml) funktioniert
4. Batch-Predictions unterstützt
5. Model-Info abrufbar
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os


# ========================================
# Test 1: Inference Service Initialisierung
# ========================================

def test_inference_service_loads_model_on_init():
    """
    Inference Service sollte Model bei Initialisierung laden.
    
    Requirements:
    - load_model(path) wird aufgerufen
    - Model ist danach verfügbar
    - is_ready() gibt True zurück
    """
    from contexts.ragintegration.infrastructure.ml.inference_service import LTRInferenceService
    
    # Erstelle temporäres Mock-Model
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = os.path.join(tmpdir, 'test_model.pkl')
        
        # Erstelle einfaches Mock-Model
        from sklearn.ensemble import GradientBoostingRegressor
        mock_model = GradientBoostingRegressor(n_estimators=10, random_state=42)
        
        # Trainiere mit Dummy-Daten
        X_dummy = np.random.rand(10, 11)
        y_dummy = np.random.rand(10)
        mock_model.fit(X_dummy, y_dummy)
        
        # Speichere Model
        import pickle
        model_data = {
            'model': mock_model,
            'model_type': 'sklearn',
            'model_version': '1.0.0',
            'feature_names': ['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11']
        }
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        # Erstelle Inference Service
        service = LTRInferenceService(model_path=model_path)
        
        # Assertions
        assert service.is_ready(), "Service sollte ready sein"
        assert service.model is not None, "Model sollte geladen sein"
        assert service.model_version == '1.0.0', "Model-Version sollte korrekt sein"


def test_inference_service_can_work_without_model():
    """
    Inference Service sollte auch ohne Model funktionieren (Fallback).
    
    Requirements:
    - Service kann mit model_path=None initialisiert werden
    - is_ready() gibt False zurück
    - predict() gibt Fallback-Score zurück (hybrid_score)
    """
    from contexts.ragintegration.infrastructure.ml.inference_service import LTRInferenceService
    
    # Service ohne Model
    service = LTRInferenceService(model_path=None)
    
    # Assertions
    assert service.is_ready() is False, "Service sollte not ready sein ohne Model"
    
    # Predict sollte Fallback verwenden
    features = np.random.rand(1, 11)
    features[0, 10] = 0.77  # hybrid_score an Index 10 (2D-Array)
    
    prediction = service.predict(features)
    
    # Fallback sollte hybrid_score zurückgeben
    assert prediction is not None, "Prediction sollte nicht None sein"
    assert isinstance(prediction, (float, np.ndarray, np.floating)), "Prediction sollte float oder array sein"
    
    # Sollte hybrid_score zurückgeben (0.77)
    if isinstance(prediction, np.ndarray):
        assert prediction[0] == pytest.approx(0.77, abs=0.01), "Fallback sollte hybrid_score sein"
    else:
        assert prediction == pytest.approx(0.77, abs=0.01), "Fallback sollte hybrid_score sein"


# ========================================
# Test 2: ML Predictions
# ========================================

def test_inference_service_predicts_ml_scores():
    """
    Inference Service sollte ML-Scores berechnen.
    
    Requirements:
    - predict(features) funktioniert
    - Features ist numpy array (n_samples, 11)
    - Rückgabe ist numpy array (n_samples,) oder float
    """
    from contexts.ragintegration.infrastructure.ml.inference_service import LTRInferenceService
    
    # Erstelle Mock-Service mit trainiertem Model
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = os.path.join(tmpdir, 'test_model.pkl')
        
        from sklearn.ensemble import GradientBoostingRegressor
        mock_model = GradientBoostingRegressor(n_estimators=10, random_state=42)
        X_dummy = np.random.rand(20, 11)
        y_dummy = np.random.rand(20)
        mock_model.fit(X_dummy, y_dummy)
        
        import pickle
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': mock_model,
                'model_type': 'sklearn',
                'model_version': '1.0.0',
                'feature_names': ['f'+str(i) for i in range(11)]
            }, f)
        
        service = LTRInferenceService(model_path=model_path)
        
        # Test Features
        test_features = np.random.rand(3, 11)
        
        # Predict
        predictions = service.predict(test_features)
        
        # Assertions
        assert predictions is not None, "Predictions sollten nicht None sein"
        assert isinstance(predictions, np.ndarray), "Predictions sollten numpy array sein"
        assert predictions.shape == (3,), f"Predictions sollten (3,) sein, aber sind {predictions.shape}"


# ========================================
# Test 3: Score Combination
# ========================================

def test_inference_service_combines_scores():
    """
    Inference Service sollte Hybrid-Score und ML-Score kombinieren.
    
    Requirements:
    - combine_scores(hybrid_score, ml_score) funktioniert
    - Rückgabe ist final_score in [0, 1]
    - Gewichtung: hybrid * 0.6 + ml * 0.4 (oder konfigurierbar)
    """
    from contexts.ragintegration.infrastructure.ml.inference_service import LTRInferenceService
    
    service = LTRInferenceService(model_path=None)
    
    # Test Score-Kombination
    hybrid_score = 0.8
    ml_score = 0.6
    
    final_score = service.combine_scores(hybrid_score, ml_score)
    
    # Assertions
    assert final_score is not None, "Final Score sollte nicht None sein"
    assert isinstance(final_score, float), "Final Score sollte float sein"
    assert 0 <= final_score <= 1, f"Final Score sollte in [0, 1] sein, aber ist {final_score}"
    
    # Prüfe Gewichtung (default: 0.6 * hybrid + 0.4 * ml)
    expected = 0.6 * hybrid_score + 0.4 * ml_score
    assert final_score == pytest.approx(expected, abs=0.01), \
        f"Final Score sollte {expected} sein, aber ist {final_score}"


# ========================================
# Test 4: Model Info
# ========================================

def test_inference_service_provides_model_info():
    """
    Inference Service sollte Model-Informationen bereitstellen.
    
    Requirements:
    - get_model_info() gibt Dict zurück
    - Enthält: model_type, model_version, feature_names, is_ready
    """
    from contexts.ragintegration.infrastructure.ml.inference_service import LTRInferenceService
    
    # Service ohne Model
    service = LTRInferenceService(model_path=None)
    
    info = service.get_model_info()
    
    # Assertions
    assert isinstance(info, dict), "Model-Info sollte Dict sein"
    assert 'model_type' in info, "Info sollte model_type enthalten"
    assert 'model_version' in info, "Info sollte model_version enthalten"
    assert 'is_ready' in info, "Info sollte is_ready enthalten"
    assert info['is_ready'] is False, "is_ready sollte False sein ohne Model"


# ========================================
# Test 5: Feature Extraction Integration
# ========================================

def test_inference_service_extracts_features_from_chunk():
    """
    Inference Service sollte Features aus Chunk-Daten extrahieren können.
    
    Requirements:
    - predict_for_chunk(query, chunk, scores...) funktioniert
    - Verwendet MLFeatureExtractor intern
    - Gibt ml_score zurück
    """
    from contexts.ragintegration.infrastructure.ml.inference_service import LTRInferenceService
    
    # Service mit Mock-Model
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = os.path.join(tmpdir, 'test_model.pkl')
        
        from sklearn.ensemble import GradientBoostingRegressor
        mock_model = GradientBoostingRegressor(n_estimators=10, random_state=42)
        X_dummy = np.random.rand(20, 11)
        y_dummy = np.random.rand(20)
        mock_model.fit(X_dummy, y_dummy)
        
        import pickle
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': mock_model,
                'model_type': 'sklearn',
                'model_version': '1.0.0',
                'feature_names': ['f'+str(i) for i in range(11)]
            }, f)
        
        service = LTRInferenceService(model_path=model_path)
        
        # Mock Chunk
        chunk = {
            'chunk_id': 'test_chunk',
            'metadata': {
                'chunk_text': 'Test text',
                'document_type': 'Arbeitsanweisung',
                'chunk_length': 100,
                'heading_hierarchy_depth': 2,
                'confidence_score': 0.9
            }
        }
        
        # Predict
        ml_score = service.predict_for_chunk(
            query='Test Query',
            chunk=chunk,
            vector_score=0.8,
            text_score=0.7,
            bm25_score=0.65,
            jaccard_score=0.55,
            keyword_matches=2,
            user_level=3,
            hybrid_score=0.77
        )
        
        # Assertions
        assert ml_score is not None, "ML Score sollte nicht None sein"
        assert isinstance(ml_score, (float, np.floating)), "ML Score sollte float sein"

