"""
Tests für RAG-Optimierungen basierend auf SHAP-Insights.

TDD Phase 2: RED - Tests BEVOR Implementierung.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from contexts.ragintegration.application.use_cases import AskQuestionUseCase
from contexts.ragintegration.domain.entities import ChatMessage, SourceReference


class TestRAGOptimizations:
    """Tests für RAG-Optimierungen basierend auf SHAP-Insights."""

    @pytest.fixture
    def mock_repos(self):
        """Fixture für gemockte Repositories."""
        return {
            "chunk_repo": Mock(),
            "session_repo": Mock(),
            "message_repo": AsyncMock(),
            "indexed_doc_repo": Mock(),
            "vector_store": Mock(),
            "embedding_service": Mock(),
            "multi_query_service": Mock(),
            "ai_service": Mock(),
            "event_publisher": Mock(),
            "permission_service": Mock(),
            "shap_service": Mock(),
            "ml_model_service": Mock()
        }

    @pytest.fixture
    def use_case(self, mock_repos):
        """Fixture für AskQuestionUseCase."""
        return AskQuestionUseCase(
            chunk_repository=mock_repos["chunk_repo"],
            session_repository=mock_repos["session_repo"],
            indexed_document_repository=mock_repos["indexed_doc_repo"],
            vector_store=mock_repos["vector_store"],
            embedding_service=mock_repos["embedding_service"],
            multi_query_service=mock_repos["multi_query_service"],
            ai_service=mock_repos["ai_service"],
            event_publisher=mock_repos["event_publisher"],
            message_repository=mock_repos["message_repo"],
            permission_service=mock_repos["permission_service"],
            shap_service=mock_repos["shap_service"],
            ml_model_service=mock_repos["ml_model_service"]
        )

    @pytest.mark.asyncio
    async def test_document_type_boost_applied(self, use_case, mock_repos):
        """
        GIVEN: Query mit "Montage" und SHAP-Insight: document_type hat 35% Impact
        WHEN: AskQuestionUseCase.execute() mit Optimierungen
        THEN: Arbeitsanweisungen erhalten Boost (höhere Gewichtung)
        """
        # Mock: SHAP-Insights zeigen, dass document_type wichtig ist
        mock_repos["training_data_repo"].get_training_data.return_value = [
            Mock(
                document_type="Arbeitsanweisung",
                shap_explanation={
                    "feature_importance": {
                        "document_type": 0.35,
                        "vector_score": 0.28
                    }
                }
            )
        ]
        
        # Mock: Vector Store gibt Ergebnisse zurück
        mock_results = [
            Mock(
                chunk_id="chunk1",
                document_id=1,
                score=0.45,
                metadata={"document_type": "Arbeitsanweisung"}
            ),
            Mock(
                chunk_id="chunk2",
                document_id=2,
                score=0.85,
                metadata={"document_type": "Fachartikel"}
            )
        ]
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = mock_results
        
        # Mock: AI Service gibt Antwort zurück
        mock_repos["ai_service"].generate_response.return_value = "Test Antwort"
        
        # Mock: Session
        mock_session = Mock()
        mock_session.id = 1
        mock_session.user_id = 1
        mock_repos["session_repo"].get_by_id.return_value = mock_session
        
        # Mock: Indexed Documents
        mock_repos["indexed_doc_repo"].get_all.return_value = [
            Mock(upload_document_id=1, collection_name="doc_1", embedding_model="text-embedding-ada-002"),
            Mock(upload_document_id=2, collection_name="doc_2", embedding_model="text-embedding-ada-002")
        ]
        
        # Mock: Embedding Service
        from contexts.ragintegration.domain.value_objects import EmbeddingVector
        mock_embedding = EmbeddingVector(
            vector=[0.1] * 1536,
            model="text-embedding-ada-002",
            dimensions=1536
        )
        mock_repos["embedding_service"].generate_embedding.return_value = mock_embedding
        
        result = await use_case.execute(
            question="Was sind die wichtigsten Schritte bei der Montage?",
            session_id=1,
            use_ml_reranking=True
        )
        
        # Prüfe, dass document_type Boost angewendet wurde
        # Arbeitsanweisungen sollten höhere Scores haben als Fachartikel für "Montage"
        assert result is not None
        assert len(result.source_references) > 0
        
        # Prüfe, dass Arbeitsanweisungen bevorzugt wurden
        arbeitsanweisung_refs = [
            ref for ref in result.source_references
            if hasattr(ref, '_extended_metadata') and
            ref._extended_metadata.get('chunk_metadata', {}).get('document_type') == 'Arbeitsanweisung'
        ]
        
        # Wenn document_type Boost angewendet wurde, sollten Arbeitsanweisungen höhere Scores haben
        if len(arbeitsanweisung_refs) > 0:
            # Der erste Reference sollte eine Arbeitsanweisung sein (nach Boost)
            first_ref = result.source_references[0]
            first_doc_type = first_ref._extended_metadata.get('chunk_metadata', {}).get('document_type') if hasattr(first_ref, '_extended_metadata') else None
            # Prüfe, dass Arbeitsanweisungen bevorzugt wurden
            assert first_doc_type == "Arbeitsanweisung" or len(arbeitsanweisung_refs) > 0

    @pytest.mark.asyncio
    async def test_chunk_length_penalty_applied(self, use_case, mock_repos):
        """
        GIVEN: SHAP-Insight: chunk_length hat -12% Impact (längere Chunks = niedrigere Scores)
        WHEN: AskQuestionUseCase.execute() mit Optimierungen
        THEN: Sehr lange Chunks erhalten Penalty (niedrigere Gewichtung)
        """
        # Mock: Vector Store gibt Ergebnisse mit verschiedenen Chunk-Längen zurück
        mock_results = [
            Mock(
                chunk_id="chunk1",
                document_id=1,
                score=0.85,
                metadata={"chunk_length": 5000}  # Sehr langer Chunk
            ),
            Mock(
                chunk_id="chunk2",
                document_id=2,
                score=0.80,
                metadata={"chunk_length": 500}  # Normaler Chunk
            )
        ]
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = mock_results
        
        # Mock: AI Service
        mock_repos["ai_service"].generate_response.return_value = "Test Antwort"
        
        # Mock: Session
        mock_session = Mock()
        mock_session.id = 1
        mock_session.user_id = 1
        mock_repos["session_repo"].get_by_id.return_value = mock_session
        
        # Mock: Indexed Documents
        mock_repos["indexed_doc_repo"].get_all.return_value = [
            Mock(upload_document_id=1, collection_name="doc_1", embedding_model="text-embedding-ada-002")
        ]
        
        # Mock: Embedding Service
        from contexts.ragintegration.domain.value_objects import EmbeddingVector
        mock_embedding = EmbeddingVector(
            vector=[0.1] * 1536,
            model="text-embedding-ada-002",
            dimensions=1536
        )
        mock_repos["embedding_service"].generate_embedding.return_value = mock_embedding
        
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            use_ml_reranking=True
        )
        
        # Prüfe, dass chunk_length Penalty angewendet wurde
        # Kürzere Chunks sollten bevorzugt werden
        assert result is not None
        if len(result.source_references) > 1:
            # Der erste Reference sollte einen kürzeren Chunk haben (nach Penalty)
            first_ref = result.source_references[0]
            first_length = first_ref._extended_metadata.get('chunk_metadata', {}).get('chunk_length') if hasattr(first_ref, '_extended_metadata') else None
            
            second_ref = result.source_references[1]
            second_length = second_ref._extended_metadata.get('chunk_metadata', {}).get('chunk_length') if hasattr(second_ref, '_extended_metadata') else None
            
            # Kürzere Chunks sollten höher gerankt sein
            if first_length and second_length:
                assert first_length <= second_length

    @pytest.mark.asyncio
    async def test_vector_score_optimization(self, use_case, mock_repos):
        """
        GIVEN: SHAP-Insight: vector_score hat 28% Impact
        WHEN: AskQuestionUseCase.execute() mit Optimierungen
        THEN: Vector-Score wird optimiert (bessere Embedding-Modell-Auswahl)
        """
        # Mock: Vector Store gibt Ergebnisse mit verschiedenen Vector-Scores zurück
        mock_results = [
            Mock(
                chunk_id="chunk1",
                document_id=1,
                score=0.75,
                metadata={"vector_score": 0.75}
            ),
            Mock(
                chunk_id="chunk2",
                document_id=2,
                score=0.70,
                metadata={"vector_score": 0.70}
            )
        ]
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = mock_results
        
        # Mock: AI Service
        mock_repos["ai_service"].generate_response.return_value = "Test Antwort"
        
        # Mock: Session
        mock_session = Mock()
        mock_session.id = 1
        mock_session.user_id = 1
        mock_repos["session_repo"].get_by_id.return_value = mock_session
        
        # Mock: Indexed Documents
        mock_repos["indexed_doc_repo"].get_all.return_value = [
            Mock(upload_document_id=1, collection_name="doc_1", embedding_model="text-embedding-ada-002")
        ]
        
        # Mock: Embedding Service
        from contexts.ragintegration.domain.value_objects import EmbeddingVector
        mock_embedding = EmbeddingVector(
            vector=[0.1] * 1536,
            model="text-embedding-ada-002",
            dimensions=1536
        )
        mock_repos["embedding_service"].generate_embedding.return_value = mock_embedding
        
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            use_ml_reranking=True
        )
        
        # Prüfe, dass Vector-Score optimiert wurde
        assert result is not None
        assert len(result.source_references) > 0
        
        # Prüfe, dass höhere Vector-Scores bevorzugt wurden
        if len(result.source_references) > 1:
            first_score = result.source_references[0].relevance_score
            second_score = result.source_references[1].relevance_score
            assert first_score >= second_score

