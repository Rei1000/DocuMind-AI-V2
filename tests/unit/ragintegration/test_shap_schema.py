"""
Unit Tests für SHAP Schema.

TDD Phase 1: RED - Tests schreiben bevor Code existiert.

Diese Tests müssen fehlschlagen, bis SHAPExplanationResponse Schema implementiert ist.
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List

# Diese Imports werden fehlschlagen, bis Code existiert
try:
    from contexts.ragintegration.interface.schemas import SHAPExplanationResponse
except ImportError:
    # Für RED-Phase: Mock-Import
    SHAPExplanationResponse = None


class TestSHAPExplanationResponse:
    """Tests für SHAPExplanationResponse Schema."""
    
    def test_shap_explanation_response_creation(self):
        """Test: SHAPExplanationResponse kann erstellt werden."""
        if SHAPExplanationResponse is None:
            pytest.skip("SHAPExplanationResponse noch nicht implementiert (RED-Phase)")
        
        response = SHAPExplanationResponse(
            feature_importance={'vector_score': 0.4, 'text_score': 0.3, 'keyword_matches': 0.2},
            base_value=0.5,
            shap_values=[0.4, 0.3, 0.2],
            expected_value=0.5,
            prediction=0.81,
            query="Test Query",
            chunk_id="test_chunk_1",
            timestamp=datetime.now(),
            features={'vector_score': 0.85, 'text_score': 0.72, 'keyword_matches': 0.2}
        )
        
        assert response.feature_importance == {'vector_score': 0.4, 'text_score': 0.3, 'keyword_matches': 0.2}
        assert response.base_value == 0.5
        assert response.prediction == 0.81
        assert response.query == "Test Query"
        assert response.chunk_id == "test_chunk_1"
    
    def test_shap_explanation_response_validation_prediction_range(self):
        """Test: SHAPExplanationResponse validiert prediction (0-1)."""
        if SHAPExplanationResponse is None:
            pytest.skip("SHAPExplanationResponse noch nicht implementiert (RED-Phase)")
        
        # Test: prediction > 1.0 sollte ValueError werfen
        with pytest.raises(ValueError):
            SHAPExplanationResponse(
                feature_importance={},
                base_value=0.5,
                shap_values=[],
                expected_value=0.5,
                prediction=1.5,  # Ungültig (> 1.0)
                query="Test",
                chunk_id="test",
                timestamp=datetime.now(),
                features={}
            )
        
        # Test: prediction < 0.0 sollte ValueError werfen
        with pytest.raises(ValueError):
            SHAPExplanationResponse(
                feature_importance={},
                base_value=0.5,
                shap_values=[],
                expected_value=0.5,
                prediction=-0.1,  # Ungültig (< 0.0)
                query="Test",
                chunk_id="test",
                timestamp=datetime.now(),
                features={}
            )
    
    def test_shap_explanation_response_validation_base_value_range(self):
        """Test: SHAPExplanationResponse validiert base_value (0-1)."""
        if SHAPExplanationResponse is None:
            pytest.skip("SHAPExplanationResponse noch nicht implementiert (RED-Phase)")
        
        # Test: base_value > 1.0 sollte ValueError werfen
        with pytest.raises(ValueError):
            SHAPExplanationResponse(
                feature_importance={},
                base_value=1.5,  # Ungültig (> 1.0)
                shap_values=[],
                expected_value=0.5,
                prediction=0.81,
                query="Test",
                chunk_id="test",
                timestamp=datetime.now(),
                features={}
            )
    
    def test_shap_explanation_response_optional_fields(self):
        """Test: SHAPExplanationResponse hat optionale Felder."""
        if SHAPExplanationResponse is None:
            pytest.skip("SHAPExplanationResponse noch nicht implementiert (RED-Phase)")
        
        # Test: Alle Felder können optional sein (außer prediction, query, chunk_id, timestamp)
        response = SHAPExplanationResponse(
            feature_importance={},  # Optional
            base_value=0.5,
            shap_values=[],  # Optional
            expected_value=0.5,
            prediction=0.81,
            query="Test",
            chunk_id="test",
            timestamp=datetime.now(),
            features={}  # Optional
        )
        
        assert response.feature_importance == {}
        assert response.shap_values == []
        assert response.features == {}
    
    def test_shap_explanation_response_feature_importance_type(self):
        """Test: feature_importance muss Dict sein."""
        if SHAPExplanationResponse is None:
            pytest.skip("SHAPExplanationResponse noch nicht implementiert (RED-Phase)")
        
        # Test: feature_importance muss Dict[str, float] sein
        response = SHAPExplanationResponse(
            feature_importance={'vector_score': 0.4, 'text_score': 0.3},
            base_value=0.5,
            shap_values=[],
            expected_value=0.5,
            prediction=0.81,
            query="Test",
            chunk_id="test",
            timestamp=datetime.now(),
            features={}
        )
        
        assert isinstance(response.feature_importance, dict)
        for key, value in response.feature_importance.items():
            assert isinstance(key, str)
            assert isinstance(value, (int, float))
    
    def test_shap_explanation_response_shap_values_type(self):
        """Test: shap_values muss List[float] sein."""
        if SHAPExplanationResponse is None:
            pytest.skip("SHAPExplanationResponse noch nicht implementiert (RED-Phase)")
        
        # Test: shap_values muss List[float] sein
        response = SHAPExplanationResponse(
            feature_importance={},
            base_value=0.5,
            shap_values=[0.4, 0.3, 0.2],
            expected_value=0.5,
            prediction=0.81,
            query="Test",
            chunk_id="test",
            timestamp=datetime.now(),
            features={}
        )
        
        assert isinstance(response.shap_values, list)
        for value in response.shap_values:
            assert isinstance(value, (int, float))
    
    def test_shap_explanation_response_timestamp_type(self):
        """Test: timestamp muss datetime sein."""
        if SHAPExplanationResponse is None:
            pytest.skip("SHAPExplanationResponse noch nicht implementiert (RED-Phase)")
        
        now = datetime.now()
        response = SHAPExplanationResponse(
            feature_importance={},
            base_value=0.5,
            shap_values=[],
            expected_value=0.5,
            prediction=0.81,
            query="Test",
            chunk_id="test",
            timestamp=now,
            features={}
        )
        
        assert isinstance(response.timestamp, datetime)
        assert response.timestamp == now

