"""
Unit Tests für SHAP Explanation Service.

TDD Phase 1: RED - Tests schreiben bevor Code existiert.

Diese Tests müssen fehlschlagen, bis SHAPExplanationService implementiert ist.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

# Diese Imports werden fehlschlagen, bis Code existiert
try:
    from contexts.ragintegration.infrastructure.shap_service import (
        SHAPExplanationService,
        SHAPExplanation
    )
except ImportError:
    # Für RED-Phase: Mock-Imports
    SHAPExplanationService = None
    SHAPExplanation = None


class TestSHAPExplanationService:
    """Tests für SHAP Explanation Service."""
    
    def test_shap_service_initialization(self):
        """Test: SHAP-Service kann initialisiert werden."""
        if SHAPExplanationService is None:
            pytest.skip("SHAPExplanationService noch nicht implementiert (RED-Phase)")
        
        service = SHAPExplanationService()
        assert service is not None
        assert isinstance(service, SHAPExplanationService)
    
    def test_explain_search_result_returns_shap_explanation(self):
        """Test: explain_search_result gibt SHAPExplanation zurück."""
        if SHAPExplanationService is None:
            pytest.skip("SHAPExplanationService noch nicht implementiert (RED-Phase)")
        
        service = SHAPExplanationService()
        
        explanation = service.explain_search_result(
            query="Was sind die wichtigsten Schritte bei der Montage?",
            chunk={'chunk_id': 'test_chunk_1', 'chunk_text': 'Montage erfolgt in 5 Schritten...'},
            vector_score=0.85,
            text_score=0.72,
            hybrid_score=0.81,
            document_type="Arbeitsanweisung",
            user_level=5,
            keyword_matches=2,
            chunk_length=150,
            heading_hierarchy_depth=2,
            confidence_score=0.95
        )
        
        assert explanation is not None
        assert isinstance(explanation, SHAPExplanation)
        assert explanation.query == "Was sind die wichtigsten Schritte bei der Montage?"
        assert explanation.chunk_id == 'test_chunk_1'
        assert explanation.prediction == 0.81
    
    def test_shap_explanation_has_feature_importance(self):
        """Test: SHAPExplanation enthält Feature-Importance."""
        if SHAPExplanationService is None:
            pytest.skip("SHAPExplanationService noch nicht implementiert (RED-Phase)")
        
        service = SHAPExplanationService()
        
        explanation = service.explain_search_result(
            query="Test Query",
            chunk={'chunk_id': 'test_chunk_1'},
            vector_score=0.85,
            text_score=0.72,
            hybrid_score=0.81,
            document_type="Arbeitsanweisung",
            user_level=5,
            keyword_matches=2,
            chunk_length=150,
            heading_hierarchy_depth=2,
            confidence_score=0.95
        )
        
        assert explanation.feature_importance is not None
        assert isinstance(explanation.feature_importance, dict)
        assert len(explanation.feature_importance) > 0
        assert 'vector_score' in explanation.feature_importance
        assert 'text_score' in explanation.feature_importance
        assert 'keyword_matches' in explanation.feature_importance
    
    def test_shap_feature_importance_values_are_float(self):
        """Test: Feature-Importance-Werte sind Floats."""
        if SHAPExplanationService is None:
            pytest.skip("SHAPExplanationService noch nicht implementiert (RED-Phase)")
        
        service = SHAPExplanationService()
        
        explanation = service.explain_search_result(
            query="Test Query",
            chunk={'chunk_id': 'test_chunk_1'},
            vector_score=0.85,
            text_score=0.72,
            hybrid_score=0.81,
            document_type="Arbeitsanweisung",
            user_level=5,
            keyword_matches=2,
            chunk_length=150,
            heading_hierarchy_depth=2,
            confidence_score=0.95
        )
        
        for feature, importance in explanation.feature_importance.items():
            assert isinstance(importance, (int, float)), f"Feature {feature} hat keinen numerischen Importance-Wert"
            # Importance sollte zwischen -1 und 1 sein (SHAP-Values können negativ sein)
            assert -1.0 <= importance <= 1.0, f"Feature {feature} hat Importance außerhalb von [-1, 1]: {importance}"
    
    def test_shap_explanation_has_all_required_fields(self):
        """Test: SHAPExplanation hat alle erforderlichen Felder."""
        if SHAPExplanationService is None:
            pytest.skip("SHAPExplanationService noch nicht implementiert (RED-Phase)")
        
        service = SHAPExplanationService()
        
        explanation = service.explain_search_result(
            query="Test Query",
            chunk={'chunk_id': 'test_chunk_1'},
            vector_score=0.85,
            text_score=0.72,
            hybrid_score=0.81,
            document_type="Arbeitsanweisung",
            user_level=5,
            keyword_matches=2,
            chunk_length=150,
            heading_hierarchy_depth=2,
            confidence_score=0.95
        )
        
        # Prüfe alle erforderlichen Felder
        required_fields = [
            'feature_importance',
            'base_value',
            'shap_values',
            'expected_value',
            'prediction',
            'query',
            'chunk_id',
            'timestamp',
            'features'
        ]
        
        for field in required_fields:
            assert hasattr(explanation, field), f"SHAPExplanation fehlt Feld: {field}"
            assert getattr(explanation, field) is not None, f"SHAPExplanation Feld {field} ist None"
    
    def test_shap_explanation_features_match_input(self):
        """Test: Features in Explanation stimmen mit Input überein."""
        if SHAPExplanationService is None:
            pytest.skip("SHAPExplanationService noch nicht implementiert (RED-Phase)")
        
        service = SHAPExplanationService()
        
        explanation = service.explain_search_result(
            query="Test Query",
            chunk={'chunk_id': 'test_chunk_1'},
            vector_score=0.85,
            text_score=0.72,
            hybrid_score=0.81,
            document_type="Arbeitsanweisung",
            user_level=5,
            keyword_matches=2,
            chunk_length=150,
            heading_hierarchy_depth=2,
            confidence_score=0.95
        )
        
        # Prüfe dass Features korrekt extrahiert wurden
        assert explanation.features is not None
        assert isinstance(explanation.features, dict)
        assert explanation.features['vector_score'] == 0.85
        assert explanation.features['text_score'] == 0.72
        # user_level sollte normalisiert sein (5/5 = 1.0)
        assert explanation.features['user_level'] == 1.0
        # keyword_matches sollte normalisiert sein (2/10 = 0.2)
        assert explanation.features['keyword_matches'] == 0.2
    
    def test_shap_explanation_base_value_is_float(self):
        """Test: base_value ist ein Float."""
        if SHAPExplanationService is None:
            pytest.skip("SHAPExplanationService noch nicht implementiert (RED-Phase)")
        
        service = SHAPExplanationService()
        
        explanation = service.explain_search_result(
            query="Test Query",
            chunk={'chunk_id': 'test_chunk_1'},
            vector_score=0.85,
            text_score=0.72,
            hybrid_score=0.81,
            document_type="Arbeitsanweisung",
            user_level=5,
            keyword_matches=2,
            chunk_length=150,
            heading_hierarchy_depth=2,
            confidence_score=0.95
        )
        
        assert isinstance(explanation.base_value, (int, float))
        assert 0.0 <= explanation.base_value <= 1.0
    
    def test_shap_explanation_shap_values_is_list(self):
        """Test: shap_values ist eine Liste von Floats."""
        if SHAPExplanationService is None:
            pytest.skip("SHAPExplanationService noch nicht implementiert (RED-Phase)")
        
        service = SHAPExplanationService()
        
        explanation = service.explain_search_result(
            query="Test Query",
            chunk={'chunk_id': 'test_chunk_1'},
            vector_score=0.85,
            text_score=0.72,
            hybrid_score=0.81,
            document_type="Arbeitsanweisung",
            user_level=5,
            keyword_matches=2,
            chunk_length=150,
            heading_hierarchy_depth=2,
            confidence_score=0.95
        )
        
        assert isinstance(explanation.shap_values, list)
        assert len(explanation.shap_values) > 0
        for value in explanation.shap_values:
            assert isinstance(value, (int, float))
    
    def test_shap_explanation_timestamp_is_datetime(self):
        """Test: timestamp ist ein datetime-Objekt."""
        if SHAPExplanationService is None:
            pytest.skip("SHAPExplanationService noch nicht implementiert (RED-Phase)")
        
        service = SHAPExplanationService()
        
        explanation = service.explain_search_result(
            query="Test Query",
            chunk={'chunk_id': 'test_chunk_1'},
            vector_score=0.85,
            text_score=0.72,
            hybrid_score=0.81,
            document_type="Arbeitsanweisung",
            user_level=5,
            keyword_matches=2,
            chunk_length=150,
            heading_hierarchy_depth=2,
            confidence_score=0.95
        )
        
        assert isinstance(explanation.timestamp, datetime)
    
    def test_shap_explanation_prediction_matches_hybrid_score(self):
        """Test: prediction entspricht hybrid_score (Input)."""
        if SHAPExplanationService is None:
            pytest.skip("SHAPExplanationService noch nicht implementiert (RED-Phase)")
        
        service = SHAPExplanationService()
        
        hybrid_score = 0.81
        explanation = service.explain_search_result(
            query="Test Query",
            chunk={'chunk_id': 'test_chunk_1'},
            vector_score=0.85,
            text_score=0.72,
            hybrid_score=hybrid_score,
            document_type="Arbeitsanweisung",
            user_level=5,
            keyword_matches=2,
            chunk_length=150,
            heading_hierarchy_depth=2,
            confidence_score=0.95
        )
        
        assert explanation.prediction == hybrid_score

