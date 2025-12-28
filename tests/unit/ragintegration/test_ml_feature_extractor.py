"""
Unit Tests für ML Feature Extractor (Learning-to-Rank).

TDD Phase 1: RED - Tests für Feature-Engineering-Pipeline.

Diese Tests definieren Anforderungen für LTR Feature-Extraction:
1. Extrahiert alle relevanten Features für ML-Ranking
2. Normalisiert Features korrekt
3. Gibt konsistente Feature-Matrix zurück
4. Unterstützt Batch-Verarbeitung
"""

import pytest
import numpy as np
from typing import Dict, List, Any


# ========================================
# Test 1: ML Feature Extractor Grundfunktionalität
# ========================================

def test_ml_feature_extractor_extracts_all_features():
    """
    ML Feature Extractor sollte alle 11 Features extrahieren.
    
    Features:
    1. vector_score
    2. text_score
    3. bm25_score
    4. jaccard_score
    5. keyword_matches
    6. chunk_length
    7. document_type_encoded
    8. heading_hierarchy_depth
    9. confidence_score
    10. user_level
    11. hybrid_score
    
    Requirements:
    - Extrahiert 11 Features
    - Normalisiert auf [0, 1] wo nötig
    - Gibt numpy array zurück
    """
    from contexts.ragintegration.infrastructure.ml.features.feature_extractor import MLFeatureExtractor
    
    extractor = MLFeatureExtractor()
    
    # Mock Chunk-Daten
    chunk = {
        'chunk_id': 'test_chunk_1',
        'metadata': {
            'chunk_text': 'Dies ist ein Test-Chunk mit etwas Inhalt für die Analyse.',
            'page_numbers': [1],
            'heading_hierarchy_depth': 2,
            'confidence_score': 0.95,
            'chunk_length': 60,
            'document_type': 'Arbeitsanweisung'
        }
    }
    
    # Scores
    query = "Test Query Freilaufwelle montieren"
    vector_score = 0.85
    text_score = 0.72
    bm25_score = 0.68
    jaccard_score = 0.55
    keyword_matches = 3
    user_level = 4
    hybrid_score = 0.806
    
    # Extrahiere Features
    features = extractor.extract(
        query=query,
        chunk=chunk,
        vector_score=vector_score,
        text_score=text_score,
        bm25_score=bm25_score,
        jaccard_score=jaccard_score,
        keyword_matches=keyword_matches,
        user_level=user_level,
        hybrid_score=hybrid_score
    )
    
    # Assertions
    assert isinstance(features, np.ndarray), "Features sollten numpy array sein"
    assert features.shape == (11,), f"Features sollten 11 Dimensionen haben, aber haben {features.shape}"
    assert np.all((features >= 0) & (features <= 1)), "Alle Features sollten normalisiert sein [0, 1]"
    
    # Prüfe spezifische Werte
    assert features[0] == pytest.approx(0.85, abs=0.01), "vector_score sollte korrekt sein"
    assert features[1] == pytest.approx(0.72, abs=0.01), "text_score sollte korrekt sein"
    assert features[2] == pytest.approx(0.68, abs=0.01), "bm25_score sollte korrekt sein"
    assert features[3] == pytest.approx(0.55, abs=0.01), "jaccard_score sollte korrekt sein"


def test_ml_feature_extractor_returns_feature_names():
    """
    ML Feature Extractor sollte Feature-Namen zurückgeben.
    
    Wichtig für SHAP-Visualisierung und Model-Interpretation.
    """
    from contexts.ragintegration.infrastructure.ml.features.feature_extractor import MLFeatureExtractor
    
    extractor = MLFeatureExtractor()
    feature_names = extractor.feature_names
    
    assert isinstance(feature_names, list), "Feature-Namen sollten Liste sein"
    assert len(feature_names) == 11, f"Feature-Namen sollten 11 Einträge haben, aber haben {len(feature_names)}"
    
    # Prüfe erwartete Feature-Namen
    expected_features = [
        'vector_score',
        'text_score',
        'bm25_score',
        'jaccard_score',
        'keyword_matches',
        'chunk_length',
        'document_type_encoded',
        'heading_hierarchy_depth',
        'confidence_score',
        'user_level',
        'hybrid_score'
    ]
    
    for expected in expected_features:
        assert expected in feature_names, f"Feature '{expected}' sollte vorhanden sein"


# ========================================
# Test 2: Document Type Encoding
# ========================================

def test_ml_feature_extractor_encodes_document_types():
    """
    ML Feature Extractor sollte Document Types encodieren.
    
    Requirements:
    - Label Encoding (Arbeitsanweisung=0, SOP=1, etc.)
    - Normalisiert auf [0, 1]
    - Konsistent über mehrere Aufrufe
    """
    from contexts.ragintegration.infrastructure.ml.features.feature_extractor import MLFeatureExtractor
    
    extractor = MLFeatureExtractor()
    
    # Mock Chunks mit verschiedenen Document Types
    chunk1 = {
        'chunk_id': 'chunk_1',
        'metadata': {
            'chunk_text': 'Test',
            'document_type': 'Arbeitsanweisung',
            'page_numbers': [1],
            'heading_hierarchy_depth': 1,
            'confidence_score': 0.9,
            'chunk_length': 10
        }
    }
    
    chunk2 = {
        'chunk_id': 'chunk_2',
        'metadata': {
            'chunk_text': 'Test',
            'document_type': 'SOP',
            'page_numbers': [1],
            'heading_hierarchy_depth': 1,
            'confidence_score': 0.9,
            'chunk_length': 10
        }
    }
    
    # Extrahiere Features
    features1 = extractor.extract(
        query='Test',
        chunk=chunk1,
        vector_score=0.8,
        text_score=0.7,
        bm25_score=0.6,
        jaccard_score=0.5,
        keyword_matches=1,
        user_level=3,
        hybrid_score=0.77
    )
    
    features2 = extractor.extract(
        query='Test',
        chunk=chunk2,
        vector_score=0.8,
        text_score=0.7,
        bm25_score=0.6,
        jaccard_score=0.5,
        keyword_matches=1,
        user_level=3,
        hybrid_score=0.77
    )
    
    # Document Type Feature (Index 6)
    doc_type_feature1 = features1[6]
    doc_type_feature2 = features2[6]
    
    # Assertions
    assert doc_type_feature1 != doc_type_feature2, "Verschiedene Document Types sollten unterschiedliche Encodings haben"
    assert 0 <= doc_type_feature1 <= 1, "Encoded Document Type sollte normalisiert sein"
    assert 0 <= doc_type_feature2 <= 1, "Encoded Document Type sollte normalisiert sein"


# ========================================
# Test 3: Batch-Verarbeitung
# ========================================

def test_ml_feature_extractor_supports_batch_processing():
    """
    ML Feature Extractor sollte Batch-Verarbeitung unterstützen.
    
    Wichtig für Training-Pipeline.
    """
    from contexts.ragintegration.infrastructure.ml.features.feature_extractor import MLFeatureExtractor
    
    extractor = MLFeatureExtractor()
    
    # Mock Batch von Chunks
    chunks_data = [
        {
            'query': 'Query 1',
            'chunk': {
                'chunk_id': 'chunk_1',
                'metadata': {
                    'chunk_text': 'Text 1',
                    'document_type': 'Arbeitsanweisung',
                    'page_numbers': [1],
                    'heading_hierarchy_depth': 1,
                    'confidence_score': 0.9,
                    'chunk_length': 100
                }
            },
            'vector_score': 0.8,
            'text_score': 0.7,
            'bm25_score': 0.65,
            'jaccard_score': 0.55,
            'keyword_matches': 2,
            'user_level': 3,
            'hybrid_score': 0.77
        },
        {
            'query': 'Query 2',
            'chunk': {
                'chunk_id': 'chunk_2',
                'metadata': {
                    'chunk_text': 'Text 2',
                    'document_type': 'SOP',
                    'page_numbers': [2],
                    'heading_hierarchy_depth': 2,
                    'confidence_score': 0.85,
                    'chunk_length': 200
                }
            },
            'vector_score': 0.75,
            'text_score': 0.65,
            'bm25_score': 0.60,
            'jaccard_score': 0.50,
            'keyword_matches': 1,
            'user_level': 4,
            'hybrid_score': 0.72
        }
    ]
    
    # Batch-Extraktion
    features_batch = extractor.extract_batch(chunks_data)
    
    # Assertions
    assert isinstance(features_batch, np.ndarray), "Batch sollte numpy array sein"
    assert features_batch.shape == (2, 11), f"Batch sollte (2, 11) sein, aber ist {features_batch.shape}"
    assert np.all((features_batch >= 0) & (features_batch <= 1)), "Alle Features sollten normalisiert sein"


# ========================================
# Test 4: Feature Consistency
# ========================================

def test_ml_feature_extractor_produces_consistent_features():
    """
    ML Feature Extractor sollte konsistente Features produzieren.
    
    Gleiche Input-Daten sollten immer gleiche Features ergeben.
    """
    from contexts.ragintegration.infrastructure.ml.features.feature_extractor import MLFeatureExtractor
    
    extractor = MLFeatureExtractor()
    
    chunk = {
        'chunk_id': 'test_chunk',
        'metadata': {
            'chunk_text': 'Test',
            'document_type': 'Arbeitsanweisung',
            'page_numbers': [1],
            'heading_hierarchy_depth': 2,
            'confidence_score': 0.9,
            'chunk_length': 100
        }
    }
    
    # Extrahiere Features zweimal
    features1 = extractor.extract(
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
    
    features2 = extractor.extract(
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
    assert np.array_equal(features1, features2), "Features sollten konsistent sein"


# ========================================
# Test 5: Feature Normalization
# ========================================

def test_ml_feature_extractor_normalizes_features_correctly():
    """
    ML Feature Extractor sollte Features korrekt normalisieren.
    
    Requirements:
    - keyword_matches: normalisiert auf [0, 1] (max 20 assumed)
    - chunk_length: normalisiert auf [0, 1] (max 3000 assumed)
    - heading_hierarchy_depth: normalisiert auf [0, 1] (max 5 assumed)
    - user_level: normalisiert auf [0, 1] (5/5 = 1.0)
    """
    from contexts.ragintegration.infrastructure.ml.features.feature_extractor import MLFeatureExtractor
    
    extractor = MLFeatureExtractor()
    
    # Extreme Werte testen
    chunk = {
        'chunk_id': 'test_chunk',
        'metadata': {
            'chunk_text': 'X' * 5000,  # Sehr lang
            'document_type': 'Arbeitsanweisung',
            'page_numbers': [1],
            'heading_hierarchy_depth': 10,  # Sehr tief
            'confidence_score': 1.0,
            'chunk_length': 5000
        }
    }
    
    features = extractor.extract(
        query='Test',
        chunk=chunk,
        vector_score=1.0,
        text_score=1.0,
        bm25_score=1.0,
        jaccard_score=1.0,
        keyword_matches=50,  # Viele Matches
        user_level=5,  # Max Level
        hybrid_score=1.0
    )
    
    # Assertions - Alle Features sollten in [0, 1] sein (auch bei extremen Werten)
    assert np.all((features >= 0) & (features <= 1)), \
        f"Alle Features sollten in [0, 1] sein, aber: {features}"


# ========================================
# Test 6: Missing Data Handling
# ========================================

def test_ml_feature_extractor_handles_missing_data():
    """
    ML Feature Extractor sollte fehlende Daten gracefully behandeln.
    
    Requirements:
    - Fehlende Metadaten werden mit Default-Werten ersetzt
    - Kein Error bei fehlenden Feldern
    - Default-Werte sind sinnvoll (meist 0.0)
    """
    from contexts.ragintegration.infrastructure.ml.features.feature_extractor import MLFeatureExtractor
    
    extractor = MLFeatureExtractor()
    
    # Chunk mit minimalen Daten
    minimal_chunk = {
        'chunk_id': 'minimal_chunk',
        'metadata': {
            'chunk_text': 'Test'
            # Keine anderen Felder!
        }
    }
    
    # Extrahiere Features
    features = extractor.extract(
        query='Test',
        chunk=minimal_chunk,
        vector_score=0.8,
        text_score=0.7,
        bm25_score=0.65,
        jaccard_score=0.55,
        keyword_matches=1,
        user_level=3,
        hybrid_score=0.77
    )
    
    # Assertions
    assert isinstance(features, np.ndarray), "Features sollten trotz fehlender Daten generiert werden"
    assert features.shape == (11,), "Features sollten 11 Dimensionen haben"
    assert np.all((features >= 0) & (features <= 1)), "Alle Features sollten normalisiert sein"


# ========================================
# Test 7: Feature Descriptions
# ========================================

def test_ml_feature_extractor_provides_feature_descriptions():
    """
    ML Feature Extractor sollte Feature-Beschreibungen liefern.
    
    Wichtig für Model-Interpretation und Debugging.
    """
    from contexts.ragintegration.infrastructure.ml.features.feature_extractor import MLFeatureExtractor
    
    extractor = MLFeatureExtractor()
    descriptions = extractor.get_feature_descriptions()
    
    assert isinstance(descriptions, dict), "Beschreibungen sollten Dict sein"
    assert len(descriptions) == 11, "Beschreibungen sollten 11 Einträge haben"
    
    # Prüfe dass alle Features beschrieben sind
    for feature_name in extractor.feature_names:
        assert feature_name in descriptions, f"Feature '{feature_name}' sollte Beschreibung haben"
        assert isinstance(descriptions[feature_name], str), "Beschreibung sollte String sein"
        assert len(descriptions[feature_name]) > 0, "Beschreibung sollte nicht leer sein"

