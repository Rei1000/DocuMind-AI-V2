"""
Regression Tests: MLFeatureExtractor sollte mit echten DB-Daten robust umgehen.

Warum:
- In training_samples existieren reale Records mit text_score=null.
- Der Training-Workflow darf dadurch nicht crashen.
"""

import numpy as np


def test_ml_feature_extractor_handles_none_values():
    """None-Werte (z.B. text_score=None) dürfen nicht zu TypeError führen."""
    from contexts.ragintegration.infrastructure.ml.features.feature_extractor import MLFeatureExtractor

    extractor = MLFeatureExtractor()
    chunk = {"chunk_id": "c1", "metadata": {"chunk_length": 100, "confidence_score": 0.8, "heading_hierarchy_depth": 1}}

    features = extractor.extract(
        query="q",
        chunk=chunk,
        vector_score=0.5,
        text_score=None,  # kritischer Fall aus data/qms.db
        bm25_score=0.2,
        jaccard_score=0.1,
        keyword_matches=2,
        user_level=3,
        hybrid_score=0.4
    )

    assert isinstance(features, np.ndarray)
    assert features.shape == (11,)
    # text_score sollte auf 0.0 fallen und im zulässigen Bereich liegen
    assert 0.0 <= float(features[1]) <= 1.0


def test_ml_feature_extractor_uses_numeric_document_type_encoded_if_present():
    """Wenn document_type_encoded numerisch vorhanden ist, muss es als Feature genutzt werden."""
    from contexts.ragintegration.infrastructure.ml.features.feature_extractor import MLFeatureExtractor

    extractor = MLFeatureExtractor()
    chunk = {
        "chunk_id": "c2",
        "metadata": {
            "document_type": "Sonstiges",  # darf überschrieben werden
            "document_type_encoded": 0.25,
            "chunk_length": 50,
            "heading_hierarchy_depth": 0,
            "confidence_score": 0.5
        }
    }

    features = extractor.extract(
        query="q",
        chunk=chunk,
        vector_score=0.5,
        text_score=0.5,
        bm25_score=0.2,
        jaccard_score=0.1,
        keyword_matches=1,
        user_level=1,
        hybrid_score=0.5
    )

    assert abs(float(features[6]) - 0.25) < 1e-9


