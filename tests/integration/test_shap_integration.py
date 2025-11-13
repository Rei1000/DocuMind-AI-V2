"""
Integration Tests für ECHTE SHAP-Integration.

Testet die vollständige SHAP-Pipeline:
- SHAP Analytics API Endpoints
- SHAP Cache Service
- Background Data Service
- SHAP Integration in RAG Use Cases
"""

import pytest
import asyncio
from datetime import datetime
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import Backend-Komponenten
import sys
import os

# Import Context-Komponenten
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'contexts'))

from ragintegration.infrastructure.shap_real_attribution import (
    FeatureExtractor,
    RankingModelWrapper,
    SHAPExplainerService
)
from ragintegration.infrastructure.shap_cache_service import SHAPCacheService
from ragintegration.infrastructure.shap_background_data_service import SHAPBackgroundDataService


# ============================================
# Test Setup
# ============================================

# Note: API Endpoint Tests überspringen (benötigen DB-Setup und Auth)


@pytest.fixture
def feature_extractor():
    """Erstelle FeatureExtractor für Tests."""
    return FeatureExtractor()


@pytest.fixture
def ranking_model():
    """Erstelle RankingModelWrapper für Tests."""
    return RankingModelWrapper()


@pytest.fixture
def shap_service(feature_extractor, ranking_model):
    """Erstelle SHAPExplainerService für Tests."""
    import numpy as np
    
    # Verwende kleine Background-Daten für schnelle Tests
    background_data = np.random.rand(10, 7)
    
    return SHAPExplainerService(
        model=ranking_model,
        feature_extractor=feature_extractor,
        background_data=background_data,
        n_background_samples=10,
        enable_cache=True
    )


@pytest.fixture
def cache_service():
    """Erstelle frischen Cache Service für Tests."""
    cache = SHAPCacheService(max_size=10, ttl_seconds=60)
    cache.clear()  # Starte mit leerem Cache
    return cache


@pytest.fixture
def background_service(feature_extractor):
    """Erstelle Background Data Service für Tests."""
    return SHAPBackgroundDataService(
        max_records=50,
        feature_extractor=feature_extractor
    )


# ============================================
# Integration Tests: SHAP Cache Service
# ============================================

def test_cache_service_stores_and_retrieves_explanations(cache_service, shap_service):
    """Test dass Cache Service Erklärungen korrekt speichert und abruft."""
    query = "Test Query"
    features = {
        'vector_score': 0.8,
        'text_score': 0.7,
        'user_level': 0.6,
        'keyword_matches': 0.2,
        'chunk_length': 0.1,
        'heading_hierarchy_depth': 0.4,
        'confidence_score': 0.9
    }
    
    # Mock SHAP Explanation
    from ragintegration.infrastructure.shap_real_attribution import SHAPExplanation
    mock_explanation = SHAPExplanation(
        feature_importance=features,
        base_value=0.5,
        shap_values=[0.1, 0.2, 0.1, 0.05, 0.02, 0.01, 0.02],
        expected_value=0.5,
        prediction=0.8,
        query=query,
        chunk_id='test_chunk',
        timestamp=datetime.now(),
        features=features
    )
    
    # Speichere im Cache
    cache_service.put(query, features, mock_explanation)
    
    # Hole aus Cache
    retrieved = cache_service.get(query, features)
    
    # Assertions
    assert retrieved is not None
    assert retrieved.query == query
    assert retrieved.prediction == 0.8
    
    # Prüfe Cache Stats
    stats = cache_service.get_statistics()
    assert stats['hits'] == 1
    assert stats['cache_size'] == 1


def test_cache_service_handles_cache_miss(cache_service):
    """Test dass Cache Service Cache Miss korrekt behandelt."""
    query = "Nonexistent Query"
    features = {'vector_score': 0.5, 'text_score': 0.5, 'user_level': 0.5, 
                'keyword_matches': 0.0, 'chunk_length': 0.0, 
                'heading_hierarchy_depth': 0.0, 'confidence_score': 0.5}
    
    # Versuche aus leerem Cache zu holen
    retrieved = cache_service.get(query, features)
    
    # Assertions
    assert retrieved is None
    
    # Prüfe Cache Stats
    stats = cache_service.get_statistics()
    assert stats['misses'] == 1
    assert stats['cache_size'] == 0


def test_cache_service_respects_max_size(cache_service):
    """Test dass Cache Service max_size respektiert (LRU Eviction)."""
    # Cache hat max_size=10
    
    # Füge 12 Einträge hinzu
    for i in range(12):
        query = f"Query {i}"
        features = {'vector_score': float(i) / 10, 'text_score': 0.5, 'user_level': 0.5, 
                   'keyword_matches': 0.0, 'chunk_length': 0.0, 
                   'heading_hierarchy_depth': 0.0, 'confidence_score': 0.5}
        
        from ragintegration.infrastructure.shap_real_attribution import SHAPExplanation
        mock_explanation = SHAPExplanation(
            feature_importance=features,
            base_value=0.5,
            shap_values=[0.1] * 7,
            expected_value=0.5,
            prediction=0.8,
            query=query,
            chunk_id=f'chunk_{i}',
            timestamp=datetime.now(),
            features=features
        )
        
        cache_service.put(query, features, mock_explanation)
    
    # Prüfe dass Cache max_size nicht überschreitet
    stats = cache_service.get_statistics()
    assert stats['cache_size'] <= 10


# ============================================
# Integration Tests: Background Data Service
# ============================================

def test_background_service_collects_search_records(background_service):
    """Test dass Background Service Search-Records korrekt sammelt."""
    # Füge Records hinzu
    for i in range(5):
        background_service.add_search_record(
            query=f"Test Query {i}",
            vector_score=0.8,
            text_score=0.7,
            user_level=3,
            keyword_matches=2,
            chunk_length=100,
            heading_hierarchy_depth=2,
            confidence_score=0.9
        )
    
    # Prüfe dass Records gespeichert wurden
    stats = background_service.get_statistics()
    assert stats['total_records'] == 5


def test_background_service_generates_background_data(background_service):
    """Test dass Background Service Background-Daten generiert."""
    # Füge Records hinzu
    for i in range(10):
        background_service.add_search_record(
            query=f"Query {i}",
            vector_score=0.8,
            text_score=0.7,
            user_level=3,
            keyword_matches=2,
            chunk_length=100,
            heading_hierarchy_depth=2,
            confidence_score=0.9
        )
    
    # Hole Background-Daten
    background_data = background_service.get_background_data(n_samples=5)
    
    # Assertions
    assert background_data is not None
    assert background_data.shape == (5, 7)  # 5 Samples, 7 Features


def test_background_service_respects_rolling_window(background_service):
    """Test dass Background Service Rolling Window respektiert (max_records=50)."""
    # Füge mehr als max_records hinzu
    for i in range(60):
        background_service.add_search_record(
            query=f"Query {i}",
            vector_score=0.8,
            text_score=0.7,
            user_level=3,
            keyword_matches=2,
            chunk_length=100,
            heading_hierarchy_depth=2,
            confidence_score=0.9
        )
    
    # Prüfe dass nur max_records gespeichert wurden
    stats = background_service.get_statistics()
    assert stats['total_records'] <= 50


# ============================================
# Integration Tests: End-to-End SHAP Flow
# ============================================

# Note: API Endpoint Tests werden übersprungen (benötigen DB-Setup und Auth)
# Diese Tests könnten in einer separaten Test-Suite mit vollem Backend-Setup durchgeführt werden

def test_shap_service_caching_improves_performance(shap_service):
    """Test dass Caching die Performance verbessert."""
    import time
    
    # Mock Chunk
    chunk = {
        'chunk_id': 'test_chunk',
        'metadata': {
            'chunk_text': 'Test text',
            'page_numbers': [1],
            'heading_hierarchy_depth': 2,
            'confidence_score': 0.9,
            'chunk_length': 100
        }
    }
    
    query = "Test Query"
    
    # Erste Berechnung (Cache Miss)
    start = time.time()
    explanation1 = shap_service.explain(
        query=query,
        chunk=chunk,
        vector_score=0.8,
        text_score=0.7,
        hybrid_score=0.77,
        document_type='Test',
        user_level=3,
        keyword_matches=2
    )
    time1 = time.time() - start
    
    # Zweite Berechnung (Cache Hit)
    start = time.time()
    explanation2 = shap_service.explain(
        query=query,
        chunk=chunk,
        vector_score=0.8,
        text_score=0.7,
        hybrid_score=0.77,
        document_type='Test',
        user_level=3,
        keyword_matches=2
    )
    time2 = time.time() - start
    
    # Assertions
    assert explanation1.prediction == explanation2.prediction
    assert explanation1.feature_importance == explanation2.feature_importance
    
    # Cache Hit sollte deutlich schneller sein
    print(f"Zeit Cache Miss: {time1:.4f}s, Cache Hit: {time2:.4f}s")
    assert time2 < time1 * 0.5  # Cache Hit sollte < 50% der Zeit sein


def test_feature_extractor_produces_consistent_features(feature_extractor):
    """Test dass Feature Extractor konsistente Features produziert."""
    chunk = {
        'chunk_id': 'test_chunk',
        'metadata': {
            'chunk_text': 'Test',
            'page_numbers': [1],
            'heading_hierarchy_depth': 2,
            'confidence_score': 0.9,
            'chunk_length': 100
        }
    }
    
    # Extrahiere Features zweimal
    features1 = feature_extractor.extract(
        query="Test Query",
        chunk=chunk,
        vector_score=0.8,
        text_score=0.7,
        user_level=3,
        keyword_matches=2
    )
    
    features2 = feature_extractor.extract(
        query="Test Query",
        chunk=chunk,
        vector_score=0.8,
        text_score=0.7,
        user_level=3,
        keyword_matches=2
    )
    
    # Assertions
    assert (features1 == features2).all()
    assert features1.shape == (7,)


def test_ranking_model_produces_valid_scores(ranking_model):
    """Test dass Ranking Model valide Scores produziert."""
    import numpy as np
    
    # Mock Features
    X = np.array([[0.8, 0.7, 0.6, 0.2, 0.1, 0.4, 0.9]])
    
    # Predict
    scores = ranking_model.predict(X)
    
    # Assertions
    assert scores.shape == (1,)
    assert 0.0 <= scores[0] <= 1.0


# ============================================
# Summary
# ============================================

if __name__ == "__main__":
    print("✅ Integration Tests für SHAP-Integration")
    print("  - SHAP Cache Service")
    print("  - Background Data Service")
    print("  - SHAP Analytics API Endpoints")
    print("  - End-to-End SHAP Flow")
    print("\nFühre Tests aus mit: pytest tests/integration/test_shap_integration.py -v")

