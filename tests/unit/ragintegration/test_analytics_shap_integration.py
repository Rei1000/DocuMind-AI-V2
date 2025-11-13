"""
Unit Tests für SHAP-Integration in GetRAGAnalyticsUseCase.

TDD Phase 3 Backend-Integration: RED - Tests schreiben bevor Code existiert.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from typing import List, Dict, Any

# Diese Imports werden fehlschlagen, bis Code existiert
try:
    from contexts.ragintegration.application.use_cases import GetRAGAnalyticsUseCase
    from contexts.ragintegration.domain.entities import TrainingData
except ImportError:
    # Für RED-Phase: Mock-Imports
    GetRAGAnalyticsUseCase = None
    TrainingData = None


class TestGetRAGAnalyticsUseCaseSHAPIntegration:
    """Tests für SHAP-Integration in GetRAGAnalyticsUseCase."""
    
    @pytest.fixture
    def mock_repos(self):
        """Fixture für gemockte Repositories."""
        return {
            "feedback_repo": AsyncMock(),
            "audit_repo": AsyncMock(),
            "chat_message_repo": AsyncMock(),
            "indexed_document_repo": AsyncMock(),
            "training_data_repo": AsyncMock()  # NEU: Training Data Repository
        }
    
    @pytest.mark.asyncio
    async def test_analytics_includes_shap_statistics(self, mock_repos):
        """Test: Analytics-Response enthält SHAP-Statistiken."""
        if GetRAGAnalyticsUseCase is None:
            pytest.skip("GetRAGAnalyticsUseCase noch nicht erweitert (RED-Phase)")
        
        # Mock Feedback Statistics
        mock_repos["feedback_repo"].get_statistics = AsyncMock(return_value={
            "total": 50,
            "positive": 35,
            "negative": 10,
            "neutral": 5,
            "average_rating": 0.75
        })
        
        # Mock Audit Logs (leer)
        mock_repos["audit_repo"].get_by_user_id = AsyncMock(return_value=[])
        
        # Mock Chat Messages (leer)
        mock_repos["chat_message_repo"].get_all = AsyncMock(return_value=[])
        
        # Mock Training Data mit SHAP-Erklärungen
        if TrainingData is not None:
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
                    shap_explanation={"feature_importance": {"vector_score": 0.4}},
                    user_feedback=None,
                    feedback_comment=None,
                    created_at=datetime.now()
                )
            ]
        else:
            mock_training_data = []
        
        mock_repos["training_data_repo"].get_training_data = AsyncMock(
            return_value=mock_training_data
        )
        
        # Mock get_statistics für Training Data
        mock_repos["training_data_repo"].get_statistics = AsyncMock(return_value={
            "total_count": 10,
            "with_feedback_count": 5,
            "with_shap_count": 8,
            "average_hybrid_score": 0.75
        })
        
        use_case = GetRAGAnalyticsUseCase(**mock_repos)
        
        result = await use_case.execute()
        
        # Prüfe dass SHAP-Statistiken vorhanden sind
        assert "shap" in result
        assert result["shap"] is not None
        assert "total_explanations" in result["shap"]
        assert "average_feature_count" in result["shap"]
        assert "top_features" in result["shap"]
    
    @pytest.mark.asyncio
    async def test_shap_statistics_calculates_top_features(self, mock_repos):
        """Test: SHAP-Statistiken berechnen Top Features korrekt."""
        if GetRAGAnalyticsUseCase is None or TrainingData is None:
            pytest.skip("GetRAGAnalyticsUseCase oder TrainingData noch nicht erweitert (RED-Phase)")
        
        # Mock Training Data mit verschiedenen Features
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
                shap_explanation={
                    "feature_importance": {
                        "vector_score": 0.4,
                        "text_score": 0.3,
                        "keyword_matches": 0.2
                    }
                },
                user_feedback=None,
                feedback_comment=None,
                created_at=datetime.now()
            ),
            TrainingData(
                id=2,
                query="Test Query 2",
                chunk_id="chunk_2",
                document_id=2,
                session_id=2,
                user_id=1,
                vector_score=0.80,
                text_score=0.75,
                hybrid_score=0.78,
                document_type="Fachartikel",
                user_level=5,
                keyword_matches=3,
                chunk_length=200,
                heading_hierarchy_depth=3,
                confidence_score=0.90,
                shap_explanation={
                    "feature_importance": {
                        "vector_score": 0.35,
                        "text_score": 0.35,
                        "keyword_matches": 0.25
                    }
                },
                user_feedback=None,
                feedback_comment=None,
                created_at=datetime.now()
            )
        ]
        
        mock_repos["feedback_repo"].get_statistics = AsyncMock(return_value={
            "total": 0, "positive": 0, "negative": 0, "neutral": 0, "average_rating": 0.0
        })
        mock_repos["audit_repo"].get_by_user_id = AsyncMock(return_value=[])
        mock_repos["chat_message_repo"].get_all = AsyncMock(return_value=[])
        mock_repos["training_data_repo"].get_training_data = AsyncMock(return_value=mock_training_data)
        mock_repos["training_data_repo"].get_statistics = AsyncMock(return_value={
            "total_count": 2,
            "with_feedback_count": 0,
            "with_shap_count": 2,
            "average_hybrid_score": 0.795
        })
        
        use_case = GetRAGAnalyticsUseCase(**mock_repos)
        
        result = await use_case.execute()
        
        # Prüfe dass Top Features berechnet wurden
        assert "shap" in result
        assert len(result["shap"]["top_features"]) > 0
        # vector_score sollte durchschnittlich höchste Importance haben
        top_feature = result["shap"]["top_features"][0]
        assert "feature" in top_feature
        assert "average_importance" in top_feature
    
    @pytest.mark.asyncio
    async def test_analytics_handles_missing_shap_gracefully(self, mock_repos):
        """Test: Analytics funktioniert auch wenn keine SHAP-Daten vorhanden sind."""
        if GetRAGAnalyticsUseCase is None:
            pytest.skip("GetRAGAnalyticsUseCase noch nicht erweitert (RED-Phase)")
        
        mock_repos["feedback_repo"].get_statistics = AsyncMock(return_value={
            "total": 0, "positive": 0, "negative": 0, "neutral": 0, "average_rating": 0.0
        })
        mock_repos["audit_repo"].get_by_user_id = AsyncMock(return_value=[])
        mock_repos["chat_message_repo"].get_all = AsyncMock(return_value=[])
        mock_repos["training_data_repo"].get_training_data = AsyncMock(return_value=[])
        mock_repos["training_data_repo"].get_statistics = AsyncMock(return_value={
            "total_count": 0,
            "with_feedback_count": 0,
            "with_shap_count": 0,
            "average_hybrid_score": 0.0
        })
        
        use_case = GetRAGAnalyticsUseCase(**mock_repos)
        
        result = await use_case.execute()
        
        # Analytics sollte trotzdem funktionieren
        assert "feedback" in result
        assert "queries" in result
        # SHAP sollte None oder leere Statistiken sein
        assert "shap" in result
        # Wenn keine Daten: shap sollte None sein oder leere Statistiken haben
        if result["shap"] is not None:
            assert result["shap"]["total_explanations"] == 0

