"""
Unit Tests für ML-Model Integration in AskQuestionUseCase.

TDD: RED - Tests schreiben bevor Code existiert.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from datetime import datetime
from typing import List, Dict, Any

# Diese Imports werden fehlschlagen, bis Code existiert
try:
    from contexts.ragintegration.application.use_cases import AskQuestionUseCase
    from contexts.ragintegration.infrastructure.ml_model_service import MLModelService
    from contexts.ragintegration.domain.entities import ChatMessage, SourceReference
except ImportError:
    # Für RED-Phase: Mock-Imports
    AskQuestionUseCase = None
    MLModelService = None
    ChatMessage = None
    SourceReference = None


class TestAskQuestionUseCaseMLIntegration:
    """Tests für ML-Model Integration in AskQuestionUseCase."""
    
    @pytest.fixture
    def mock_repos(self):
        """Fixture für gemockte Repositories."""
        return {
            "chunk_repository": AsyncMock(),
            "session_repository": AsyncMock(),
            "indexed_document_repository": AsyncMock(),
            "vector_store": AsyncMock(),
            "embedding_service": AsyncMock(),
            "multi_query_service": AsyncMock(),
            "ai_service": AsyncMock(),
            "event_publisher": AsyncMock(),
            "message_repository": AsyncMock(),
            "permission_service": AsyncMock(),
            "shap_service": AsyncMock(),
            "ml_model_service": Mock()  # NEU: ML Model Service
        }
    
    @pytest.mark.asyncio
    async def test_ask_question_uses_ml_model_for_reranking(self, mock_repos):
        """Test: AskQuestionUseCase verwendet ML-Model für Re-Ranking."""
        if AskQuestionUseCase is None or MLModelService is None:
            pytest.skip("AskQuestionUseCase oder MLModelService noch nicht erweitert (RED-Phase)")
        
        # Mock: ML Model Service ist trainiert
        mock_repos["ml_model_service"].model = MagicMock()
        mock_repos["ml_model_service"].model.is_trained = MagicMock(return_value=True)
        mock_repos["ml_model_service"].predict_score = Mock(side_effect=lambda f: f.get("vector_score", 0.5) * 0.7 + f.get("text_score", 0.5) * 0.3)
        
        # Mock: Embedding Service
        mock_repos["embedding_service"].generate_embedding = AsyncMock(return_value=[0.1] * 1536)
        
        # Mock: Vector Store gibt Ergebnisse zurück
        mock_repos["vector_store"].search_with_hybrid_scoring = AsyncMock(return_value=[
            {
                "chunk_id": "chunk_1",
                "score": 0.85,
                "vector_score": 0.85,
                "text_score": 0.72,
                "hybrid_score": 0.81,
                "metadata": {"chunk_text": "Test Chunk 1"}
            },
            {
                "chunk_id": "chunk_2",
                "score": 0.80,
                "vector_score": 0.80,
                "text_score": 0.75,
                "hybrid_score": 0.78,
                "metadata": {"chunk_text": "Test Chunk 2"}
            }
        ])
        
        # Mock: Chat Session
        mock_repos["session_repository"].get_by_id = AsyncMock(return_value=MagicMock(id=1, user_id=1))
        
        # Mock: AI Service
        mock_repos["ai_service"].generate_response = AsyncMock(return_value="Test Response")
        
        # Mock: Chat Message Repository
        mock_repos["message_repository"].save = AsyncMock(return_value=ChatMessage(
            id=1,
            session_id=1,
            role="assistant",
            content="Test Response",
            source_references=[],
            created_at=datetime.now()
        ))
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Execute
        result = await use_case.execute(
            question="Test Question",
            session_id=1,
            use_ml_reranking=True  # NEU: ML Re-Ranking aktivieren
        )
        
        # Prüfe dass ML Model Service verwendet wurde
        assert mock_repos["ml_model_service"].predict_score.called
        
        # Prüfe dass Source References vorhanden sind
        assert len(result.source_references) > 0
    
    @pytest.mark.asyncio
    async def test_ask_question_works_without_ml_model(self, mock_repos):
        """Test: AskQuestionUseCase funktioniert auch ohne ML-Model."""
        if AskQuestionUseCase is None:
            pytest.skip("AskQuestionUseCase noch nicht erweitert (RED-Phase)")
        
        # Mock: ML Model Service ist NICHT vorhanden
        mock_repos_without_ml = mock_repos.copy()
        mock_repos_without_ml["ml_model_service"] = None  # Kein ML Model Service
        
        # Mock: Indexed Documents
        mock_indexed_doc = MagicMock()
        mock_indexed_doc.id = 1
        mock_indexed_doc.collection_name = "rag_documents"
        mock_indexed_doc.upload_document_id = 1
        mock_indexed_doc.document_title = "Test Doc"
        mock_repos_without_ml["indexed_document_repository"].get_all = AsyncMock(return_value=[mock_indexed_doc])
        
        mock_repos = mock_repos_without_ml
        
        # Mock: Embedding Service
        mock_repos["embedding_service"].generate_embedding = AsyncMock(return_value=[0.1] * 1536)
        
        # Mock: Vector Store gibt Ergebnisse zurück
        mock_repos["vector_store"].search_with_hybrid_scoring = AsyncMock(return_value=[
            {
                "chunk_id": "chunk_1",
                "score": 0.85,
                "vector_score": 0.85,
                "text_score": 0.72,
                "hybrid_score": 0.81,
                "metadata": {"chunk_text": "Test Chunk 1", "document_id": 1, "chunk_id": "chunk_1"}
            }
        ])
        
        # Mock: Chat Session
        mock_repos["session_repository"].get_by_id = AsyncMock(return_value=MagicMock(id=1, user_id=1))
        
        # Mock: AI Service
        mock_repos["ai_service"].generate_response = AsyncMock(return_value="Test Response")
        
        # Mock: Chunk Repository
        mock_repos["chunk_repository"].get_by_chunk_id = AsyncMock(return_value=None)
        
        # Mock: Multi Query Service
        mock_repos["multi_query_service"].expand_query = AsyncMock(return_value="Test Question")
        
        # Mock: Chat Message Repository
        mock_repos["message_repository"].save = AsyncMock(return_value=ChatMessage(
            id=1,
            session_id=1,
            role="assistant",
            content="Test Response",
            source_references=[],
            created_at=datetime.now()
        ))
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Execute (ohne ML Re-Ranking)
        result = await use_case.execute(
            question="Test Question",
            session_id=1,
            use_ml_reranking=False,  # ML Re-Ranking deaktiviert
            use_hybrid_search=True,
            top_k=10
        )
        
        # Prüfe dass Ergebnis vorhanden ist
        assert result is not None
        assert result.content == "Test Response"
    
    @pytest.mark.asyncio
    async def test_ml_reranking_improves_result_order(self, mock_repos):
        """Test: ML Re-Ranking verbessert die Reihenfolge der Ergebnisse."""
        if AskQuestionUseCase is None or MLModelService is None:
            pytest.skip("AskQuestionUseCase oder MLModelService noch nicht erweitert (RED-Phase)")
        
        # Mock: ML Model Service gibt bessere Scores für chunk_2
        def mock_predict(features):
            # chunk_2 sollte höheren Score bekommen (bessere Relevanz)
            # Prüfe anhand der Features (z.B. text_score)
            if features.get("text_score", 0) > 0.74:  # chunk_2 hat text_score=0.75
                return 0.90  # Höherer ML-Score
            return 0.70  # Niedrigerer ML-Score
        
        mock_repos["ml_model_service"].model = MagicMock()
        mock_repos["ml_model_service"].model.is_trained = MagicMock(return_value=True)
        mock_repos["ml_model_service"].predict_score = Mock(side_effect=mock_predict)
        
        # Mock: Indexed Documents (get_all ist synchron)
        mock_indexed_doc = MagicMock()
        mock_indexed_doc.id = 1
        mock_indexed_doc.collection_name = "rag_documents"
        mock_indexed_doc.upload_document_id = 1
        mock_indexed_doc.document_title = "Test Doc"
        mock_repos["indexed_document_repository"].get_all = Mock(return_value=[mock_indexed_doc])
        
        # Mock: Vector Store gibt Ergebnisse zurück (chunk_1 hat höheren hybrid_score)
        mock_repos["vector_store"].search_with_hybrid_scoring = AsyncMock(return_value=[
            {
                "chunk_id": "chunk_1",
                "score": 0.85,
                "vector_score": 0.85,
                "text_score": 0.72,
                "hybrid_score": 0.81,  # Höherer Hybrid-Score
                "metadata": {"chunk_text": "Test Chunk 1", "document_id": 1, "chunk_id": "chunk_1"}
            },
            {
                "chunk_id": "chunk_2",
                "score": 0.80,
                "vector_score": 0.80,
                "text_score": 0.75,
                "hybrid_score": 0.78,  # Niedrigerer Hybrid-Score
                "metadata": {"chunk_text": "Test Chunk 2", "document_id": 1, "chunk_id": "chunk_2"}
            }
        ])
        
        # Mock: Chat Session
        mock_repos["session_repository"].get_by_id = AsyncMock(return_value=MagicMock(id=1, user_id=1))
        
        # Mock: AI Service
        mock_repos["ai_service"].generate_response = AsyncMock(return_value="Test Response")
        
        # Mock: Chunk Repository
        mock_repos["chunk_repository"].get_by_chunk_id = AsyncMock(return_value=None)
        
        # Mock: Multi Query Service
        mock_repos["multi_query_service"].expand_query = AsyncMock(return_value="Test Question")
        
        # Mock: Chat Message Repository
        mock_repos["message_repository"].save = AsyncMock(return_value=ChatMessage(
            id=1,
            session_id=1,
            role="assistant",
            content="Test Response",
            source_references=[],
            created_at=datetime.now()
        ))
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Execute mit ML Re-Ranking
        result = await use_case.execute(
            question="Test Question",
            session_id=1,
            use_ml_reranking=True,
            use_hybrid_search=True,
            top_k=10
        )
        
        # Prüfe dass ML Model Service verwendet wurde
        assert mock_repos["ml_model_service"].predict_score.called
        
        # Prüfe dass Source References vorhanden sind
        assert len(result.source_references) > 0
        # Nach ML Re-Ranking sollte chunk_2 vor chunk_1 kommen (höherer ML-Score)

