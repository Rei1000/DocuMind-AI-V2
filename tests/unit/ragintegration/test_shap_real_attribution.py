"""
Unit Tests für ECHTE SHAP-Attribution.

TDD Phase 1: RED - Diese Tests schlagen zunächst fehl, da die Implementierung noch nicht existiert.

Diese Tests definieren die Anforderungen für die echte SHAP-Integration:
1. RankingModelWrapper - Umhüllt Hybrid-Scoring als sklearn-kompatibles Modell
2. SHAPExplainerService - Echte SHAP-Berechnung mit KernelExplainer
3. FeatureExtractor - Konsistente Feature-Extraktion
"""

import pytest
import numpy as np
from typing import Dict, List, Any
from datetime import datetime


# ========================================
# Test 1: Feature Extractor
# ========================================

def test_feature_extractor_creates_consistent_features():
    """
    Feature Extractor sollte Features konsistent extrahieren und normalisieren.
    
    Requirements:
    - Extrahiert 7 Features: vector_score, text_score, user_level, keyword_matches, 
      chunk_length, heading_hierarchy_depth, confidence_score
    - Normalisiert alle Features auf [0, 1]
    - Gibt numpy array zurück (für SHAP)
    """
    from contexts.ragintegration.infrastructure.shap_real_attribution import FeatureExtractor
    
    extractor = FeatureExtractor()
    
    # Mock Chunk-Daten
    chunk = {
        'chunk_id': 'test_chunk_1',
        'metadata': {
            'chunk_text': 'This is a test chunk with some content',
            'page_numbers': [1],
            'heading_hierarchy_depth': 2,
            'confidence_score': 0.95,
            'chunk_length': 39
        }
    }
    
    query = "test query"
    vector_score = 0.85
    text_score = 0.72
    user_level = 4
    keyword_matches = 2
    
    # Extrahiere Features
    features = extractor.extract(
        query=query,
        chunk=chunk,
        vector_score=vector_score,
        text_score=text_score,
        user_level=user_level,
        keyword_matches=keyword_matches
    )
    
    # Assertions
    assert isinstance(features, np.ndarray), "Features sollten numpy array sein"
    assert features.shape == (7,), f"Features sollten 7 Dimensionen haben, aber haben {features.shape}"
    assert np.all((features >= 0) & (features <= 1)), "Alle Features sollten normalisiert sein [0, 1]"
    
    # Prüfe Werte
    assert features[0] == pytest.approx(0.85, abs=0.01), "vector_score sollte korrekt sein"
    assert features[1] == pytest.approx(0.72, abs=0.01), "text_score sollte korrekt sein"
    assert features[2] == pytest.approx(0.8, abs=0.01), "user_level sollte normalisiert sein (4/5 = 0.8)"
    assert features[3] == pytest.approx(0.2, abs=0.01), "keyword_matches sollte normalisiert sein (2/10 = 0.2)"
    # chunk_length: 39/2000 = 0.0195
    # heading_hierarchy_depth: 2/5 = 0.4
    # confidence_score: 0.95


def test_feature_extractor_returns_feature_names():
    """
    Feature Extractor sollte Feature-Namen zurückgeben.
    
    Wichtig für SHAP-Visualisierung.
    """
    from contexts.ragintegration.infrastructure.shap_real_attribution import FeatureExtractor
    
    extractor = FeatureExtractor()
    feature_names = extractor.feature_names
    
    assert isinstance(feature_names, list), "Feature-Namen sollten Liste sein"
    assert len(feature_names) == 7, "Feature-Namen sollten 7 Einträge haben"
    assert 'vector_score' in feature_names
    assert 'text_score' in feature_names
    assert 'user_level' in feature_names
    assert 'keyword_matches' in feature_names
    assert 'chunk_length' in feature_names
    assert 'heading_hierarchy_depth' in feature_names
    assert 'confidence_score' in feature_names


def test_feature_extractor_batch_extraction():
    """
    Feature Extractor sollte Batch-Extraktion unterstützen.
    
    Wichtig für SHAP Background-Daten.
    """
    from contexts.ragintegration.infrastructure.shap_real_attribution import FeatureExtractor
    
    extractor = FeatureExtractor()
    
    # Mock Batch von Chunks
    chunks_data = [
        {
            'query': 'test query 1',
            'chunk': {
                'chunk_id': 'chunk_1',
                'metadata': {
                    'chunk_text': 'Text 1',
                    'page_numbers': [1],
                    'heading_hierarchy_depth': 1,
                    'confidence_score': 0.9,
                    'chunk_length': 100
                }
            },
            'vector_score': 0.8,
            'text_score': 0.7,
            'user_level': 3,
            'keyword_matches': 1
        },
        {
            'query': 'test query 2',
            'chunk': {
                'chunk_id': 'chunk_2',
                'metadata': {
                    'chunk_text': 'Text 2',
                    'page_numbers': [2],
                    'heading_hierarchy_depth': 2,
                    'confidence_score': 0.85,
                    'chunk_length': 200
                }
            },
            'vector_score': 0.75,
            'text_score': 0.65,
            'user_level': 4,
            'keyword_matches': 2
        }
    ]
    
    # Batch-Extraktion
    features_batch = extractor.extract_batch(chunks_data)
    
    # Assertions
    assert isinstance(features_batch, np.ndarray), "Batch sollte numpy array sein"
    assert features_batch.shape == (2, 7), f"Batch sollte (2, 7) sein, aber ist {features_batch.shape}"
    assert np.all((features_batch >= 0) & (features_batch <= 1)), "Alle Features sollten normalisiert sein"


# ========================================
# Test 2: Ranking Model Wrapper
# ========================================

def test_ranking_model_wrapper_implements_sklearn_interface():
    """
    Ranking Model Wrapper sollte sklearn-Interface implementieren.
    
    Requirements:
    - predict(X) Methode vorhanden
    - X ist numpy array (n_samples, 7)
    - Rückgabe ist numpy array (n_samples,) mit Scores [0, 1]
    """
    from contexts.ragintegration.infrastructure.shap_real_attribution import RankingModelWrapper
    
    model = RankingModelWrapper()
    
    # Mock Features (3 Samples, 7 Features)
    X = np.array([
        [0.85, 0.72, 0.8, 0.2, 0.02, 0.4, 0.95],  # Sample 1
        [0.75, 0.65, 0.6, 0.1, 0.05, 0.2, 0.9],   # Sample 2
        [0.90, 0.80, 1.0, 0.3, 0.01, 0.6, 0.98]   # Sample 3
    ])
    
    # Predict
    predictions = model.predict(X)
    
    # Assertions
    assert isinstance(predictions, np.ndarray), "Predictions sollten numpy array sein"
    assert predictions.shape == (3,), f"Predictions sollten (3,) sein, aber sind {predictions.shape}"
    assert np.all((predictions >= 0) & (predictions <= 1)), "Predictions sollten in [0, 1] sein"


def test_ranking_model_wrapper_uses_hybrid_scoring():
    """
    Ranking Model Wrapper sollte Hybrid-Scoring korrekt implementieren.
    
    Hybrid Score = (vector_score * 0.7) + (text_score * 0.3)
    Plus optionale Boosts/Penalties.
    """
    from contexts.ragintegration.infrastructure.shap_real_attribution import RankingModelWrapper
    
    model = RankingModelWrapper()
    
    # Mock Features mit bekannten Werten
    # [vector_score=0.8, text_score=0.6, user_level=0.8, keyword_matches=0, 
    #  chunk_length=0, heading_hierarchy_depth=0, confidence_score=1.0]
    X = np.array([[0.8, 0.6, 0.8, 0.0, 0.0, 0.0, 1.0]])
    
    predictions = model.predict(X)
    
    # Erwarteter Hybrid Score: (0.8 * 0.7) + (0.6 * 0.3) = 0.56 + 0.18 = 0.74
    expected_score = 0.74
    
    assert predictions[0] == pytest.approx(expected_score, abs=0.02), \
        f"Hybrid Score sollte ~{expected_score} sein, aber ist {predictions[0]}"


def test_ranking_model_wrapper_applies_document_type_boost():
    """
    Ranking Model Wrapper sollte Document Type Boost anwenden (optional).
    
    Beispiel: Montage-Dokumente sollten bei bestimmten Queries einen Boost bekommen.
    
    OPTIONAL: Dieser Test kann später erweitert werden, wenn Document Type Boost implementiert wird.
    """
    from contexts.ragintegration.infrastructure.shap_real_attribution import RankingModelWrapper
    
    # Dieser Test ist optional und kann zunächst übersprungen werden
    pytest.skip("Document Type Boost ist optional - wird später implementiert")


# ========================================
# Test 3: SHAP Explainer Service
# ========================================

def test_shap_explainer_service_calculates_real_shap_values():
    """
    SHAP Explainer Service sollte ECHTE SHAP-Werte berechnen.
    
    Requirements:
    - Verwendet SHAP-Library (KernelExplainer)
    - Berechnet shap_values für jedes Feature
    - Berechnet base_value, expected_value
    - Rückgabe ist SHAPExplanation mit echten SHAP-Werten
    """
    from contexts.ragintegration.infrastructure.shap_real_attribution import (
        SHAPExplainerService,
        FeatureExtractor,
        RankingModelWrapper
    )
    
    # Setup
    feature_extractor = FeatureExtractor()
    model = RankingModelWrapper()
    explainer_service = SHAPExplainerService(
        model=model,
        feature_extractor=feature_extractor
    )
    
    # Mock Query & Chunk
    query = "test query"
    chunk = {
        'chunk_id': 'test_chunk_1',
        'metadata': {
            'chunk_text': 'This is a test chunk',
            'page_numbers': [1],
            'heading_hierarchy_depth': 2,
            'confidence_score': 0.95,
            'chunk_length': 20
        }
    }
    vector_score = 0.85
    text_score = 0.72
    hybrid_score = 0.806  # (0.85 * 0.7) + (0.72 * 0.3)
    user_level = 4
    keyword_matches = 2
    
    # Explain
    explanation = explainer_service.explain(
        query=query,
        chunk=chunk,
        vector_score=vector_score,
        text_score=text_score,
        hybrid_score=hybrid_score,
        document_type='Arbeitsanweisung',
        user_level=user_level,
        keyword_matches=keyword_matches
    )
    
    # Assertions
    assert explanation is not None, "Explanation sollte nicht None sein"
    assert hasattr(explanation, 'shap_values'), "Explanation sollte shap_values haben"
    assert hasattr(explanation, 'base_value'), "Explanation sollte base_value haben"
    assert hasattr(explanation, 'expected_value'), "Explanation sollte expected_value haben"
    assert hasattr(explanation, 'feature_importance'), "Explanation sollte feature_importance haben"
    
    # SHAP-Werte sollten echte Attributionen sein (nicht Heuristiken!)
    assert isinstance(explanation.shap_values, list), "shap_values sollten Liste sein"
    assert len(explanation.shap_values) == 7, "shap_values sollten 7 Einträge haben (1 pro Feature)"
    
    # SHAP Property: sum(shap_values) + base_value ≈ prediction
    shap_sum = sum(explanation.shap_values)
    prediction_from_shap = explanation.base_value + shap_sum
    
    assert prediction_from_shap == pytest.approx(hybrid_score, abs=0.1), \
        f"SHAP Property verletzt: base_value + sum(shap_values) sollte ≈ prediction sein. " \
        f"base_value={explanation.base_value}, sum(shap_values)={shap_sum}, " \
        f"prediction_from_shap={prediction_from_shap}, hybrid_score={hybrid_score}"


def test_shap_explainer_service_uses_background_data():
    """
    SHAP Explainer Service sollte Background-Daten für KernelExplainer verwenden.
    
    Background-Daten sind wichtig für echte SHAP-Berechnung.
    """
    from contexts.ragintegration.infrastructure.shap_real_attribution import (
        SHAPExplainerService,
        FeatureExtractor,
        RankingModelWrapper
    )
    
    # Setup
    feature_extractor = FeatureExtractor()
    model = RankingModelWrapper()
    
    # Background-Daten (50 Samples, 7 Features)
    background_data = np.random.rand(50, 7)
    
    explainer_service = SHAPExplainerService(
        model=model,
        feature_extractor=feature_extractor,
        background_data=background_data
    )
    
    # Mock Query & Chunk
    query = "test query"
    chunk = {
        'chunk_id': 'test_chunk_1',
        'metadata': {
            'chunk_text': 'Test',
            'page_numbers': [1],
            'heading_hierarchy_depth': 1,
            'confidence_score': 0.9,
            'chunk_length': 10
        }
    }
    
    # Explain
    explanation = explainer_service.explain(
        query=query,
        chunk=chunk,
        vector_score=0.8,
        text_score=0.7,
        hybrid_score=0.77,
        document_type='SOP',
        user_level=3,
        keyword_matches=1
    )
    
    # Assertions
    assert explanation is not None, "Explanation sollte nicht None sein"
    assert explanation.base_value is not None, "base_value sollte gesetzt sein"
    
    # base_value sollte dem Durchschnitt der Background-Predictions entsprechen (approximativ)
    # Dies ist eine SHAP-Eigenschaft


def test_shap_explainer_service_returns_feature_importance_dict():
    """
    SHAP Explainer Service sollte feature_importance als Dict zurückgeben.
    
    Format: {'vector_score': 0.15, 'text_score': 0.10, ...}
    """
    from contexts.ragintegration.infrastructure.shap_real_attribution import (
        SHAPExplainerService,
        FeatureExtractor,
        RankingModelWrapper
    )
    
    # Setup
    feature_extractor = FeatureExtractor()
    model = RankingModelWrapper()
    explainer_service = SHAPExplainerService(
        model=model,
        feature_extractor=feature_extractor
    )
    
    # Mock Query & Chunk
    query = "test query"
    chunk = {
        'chunk_id': 'test_chunk_1',
        'metadata': {
            'chunk_text': 'Test',
            'page_numbers': [1],
            'heading_hierarchy_depth': 1,
            'confidence_score': 0.9,
            'chunk_length': 10
        }
    }
    
    # Explain
    explanation = explainer_service.explain(
        query=query,
        chunk=chunk,
        vector_score=0.8,
        text_score=0.7,
        hybrid_score=0.77,
        document_type='SOP',
        user_level=3,
        keyword_matches=1
    )
    
    # Assertions
    assert isinstance(explanation.feature_importance, dict), "feature_importance sollte Dict sein"
    assert 'vector_score' in explanation.feature_importance
    assert 'text_score' in explanation.feature_importance
    assert 'user_level' in explanation.feature_importance
    assert 'keyword_matches' in explanation.feature_importance
    assert 'chunk_length' in explanation.feature_importance
    assert 'heading_hierarchy_depth' in explanation.feature_importance
    assert 'confidence_score' in explanation.feature_importance


# ========================================
# Test 4: Integration Test
# ========================================

def test_shap_integration_with_use_case():
    """
    Integration Test: SHAP-Service sollte in AskQuestionUseCase integriert werden können.
    
    OPTIONAL: Dieser Test prüft die Integration in den bestehenden Use Case.
    Kann zunächst übersprungen werden, bis Service vollständig implementiert ist.
    """
    pytest.skip("Integration Test - wird später implementiert")


# ========================================
# Test 5: Performance Tests
# ========================================

def test_shap_explainer_service_completes_within_time_limit():
    """
    SHAP Explainer Service sollte innerhalb von 2 Sekunden pro Erklärung sein.
    
    OPTIONAL: Performance-Test für später.
    """
    pytest.skip("Performance Test - wird später implementiert")


def test_shap_explainer_service_supports_caching():
    """
    SHAP Explainer Service sollte Caching unterstützen für häufige Queries.
    
    OPTIONAL: Caching-Feature für später.
    """
    pytest.skip("Caching Test - wird später implementiert")

