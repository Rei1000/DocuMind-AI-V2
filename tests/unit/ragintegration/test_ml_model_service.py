"""
Unit Tests für ML Model Service (Integration mit Training Data Repository).

TDD Phase 4: RED - Tests schreiben bevor Code existiert.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from typing import List, Dict, Any

# Diese Imports werden fehlschlagen, bis Code existiert
try:
    from contexts.ragintegration.infrastructure.ml_model_service import MLModelService
    from contexts.ragintegration.domain.entities import TrainingData
except ImportError:
    # Für RED-Phase: Mock-Imports
    MLModelService = None
    TrainingData = None


class TestMLModelService:
    """Tests für ML Model Service."""
    
    @pytest.fixture
    def mock_training_data_repo(self):
        """Fixture für gemocktes Training Data Repository."""
        return Mock()
    
    def test_service_initialization(self, mock_training_data_repo):
        """Test: ML Model Service kann initialisiert werden."""
        if MLModelService is None:
            pytest.skip("MLModelService noch nicht implementiert (RED-Phase)")
        
        service = MLModelService(training_data_repo=mock_training_data_repo)
        assert service is not None
        assert isinstance(service, MLModelService)
    
    def test_service_train_model(self, mock_training_data_repo):
        """Test: Service kann Model mit Training Data trainieren."""
        if MLModelService is None or TrainingData is None:
            pytest.skip("MLModelService oder TrainingData noch nicht implementiert (RED-Phase)")
        
        # Mock Training Data
        mock_training_data = [
            TrainingData(
                id=1,
                query="Test Query 1",
                chunk_id="chunk_1",
                document_id=1,
                session_id=1,
                user_id=1,
                vector_score=0.85,
                text_score=0.72,
                hybrid_score=0.81,
                document_type="Arbeitsanweisung",
                user_level=5,
                keyword_matches=2,
                chunk_length=150,
                heading_hierarchy_depth=2,
                confidence_score=0.95,
                shap_explanation=None,
                user_feedback="positive",
                feedback_comment=None,
                created_at=datetime.now()
            )
        ]
        
        from unittest.mock import Mock
        mock_training_data_repo.get_training_data = Mock(
            return_value=mock_training_data
        )
        
        service = MLModelService(training_data_repo=mock_training_data_repo)
        
        # Train Model (synchron, da Repository synchron ist)
        result = service.train_model(with_feedback=True)
        
        # Model sollte trainiert sein
        assert result["success"] is True
        assert "metrics" in result
    
    def test_service_predict_score(self, mock_training_data_repo):
        """Test: Service kann Score für Features vorhersagen."""
        if MLModelService is None:
            pytest.skip("MLModelService noch nicht implementiert (RED-Phase)")
        
        service = MLModelService(training_data_repo=mock_training_data_repo)
        
        # Mock: Model ist bereits trainiert
        service.model = MagicMock()
        service.model.is_trained = MagicMock(return_value=True)
        service.model.predict = MagicMock(return_value=0.85)
        
        # Features für Prediction
        features = {
            "vector_score": 0.85,
            "text_score": 0.72,
            "keyword_matches": 2,
            "chunk_length": 150,
            "heading_hierarchy_depth": 2,
            "confidence_score": 0.95,
            "document_type": "Arbeitsanweisung",
            "user_level": 5
        }
        
        # Predict Score (synchron)
        predicted_score = service.predict_score(features)
        
        # Score sollte zwischen 0 und 1 sein
        assert isinstance(predicted_score, (int, float))
        assert 0.0 <= predicted_score <= 1.0
    
    def test_service_get_model_performance(self, mock_training_data_repo):
        """Test: Service kann Model Performance Metriken abrufen."""
        if MLModelService is None:
            pytest.skip("MLModelService noch nicht implementiert (RED-Phase)")
        
        service = MLModelService(training_data_repo=mock_training_data_repo)
        
        # Mock: Model ist bereits trainiert
        service.model = MagicMock()
        service.model.is_trained = MagicMock(return_value=True)
        service.model.evaluate = MagicMock(return_value={
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.88,
            "f1_score": 0.85
        })
        
        # Mock Test Data (synchron)
        mock_training_data_repo.get_training_data = Mock(return_value=[])
        mock_training_data_repo.get_statistics = Mock(return_value={
            "total_count": 100,
            "with_feedback_count": 50,
            "with_shap_count": 80,
            "average_hybrid_score": 0.75
        })
        
        # Get Model Performance (synchron)
        performance = service.get_model_performance()
        
        # Performance sollte Metriken enthalten
        assert "accuracy" in performance
        assert "precision" in performance
        assert "recall" in performance
        assert "f1_score" in performance
        assert "training_samples" in performance

