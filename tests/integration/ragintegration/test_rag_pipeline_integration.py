"""
Integration Tests für vollständige RAG-Pipeline (CR-P0, CR-P1, CR-P2.1)

Testet die vollständige Pipeline:
- Index → Search → Prompt → Answer
- Mit Interest Group Filtering
- Mit Multi-Query Expansion
- Mit Hybrid Search
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from contexts.ragintegration.domain.entities import ChatMessage, ChatSession, IndexedDocument
from contexts.ragintegration.application.use_cases import AskQuestionUseCase, IndexApprovedDocumentUseCase


class TestRAGPipelineIntegration:
    """Integration Tests für vollständige RAG-Pipeline"""
    
    def _create_mock_repos(self):
        """Helper: Erstelle Mock-Repositories."""
        mock_permission_service = MagicMock()
        mock_permission_service.get_user_level.return_value = 4
        mock_permission_service.get_user_interest_groups.return_value = []
        
        mock_shap_service = MagicMock()
        mock_shap_service._background_data_service = MagicMock()
        mock_shap_service._background_data_service.get_statistics.return_value = {}
        mock_shap_service.cache = MagicMock()
        mock_shap_service.cache.get_statistics.return_value = {}
        
        mock_ltr_service = MagicMock()
        mock_ltr_service.is_enabled.return_value = False
        
        return {
            "chunk_repository": MagicMock(),
            "session_repository": MagicMock(),
            "indexed_document_repository": MagicMock(),
            "message_repository": MagicMock(),
            "vector_store": MagicMock(),
            "embedding_service": MagicMock(),
            "multi_query_service": MagicMock(),
            "ai_service": AsyncMock(),
            "event_publisher": MagicMock(),
            "permission_service": mock_permission_service,
            "shap_service": mock_shap_service,
            "ml_model_service": MagicMock(),
            "ltr_service": mock_ltr_service
        }
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_index_search_prompt_answer(self):
        """IT-PIPELINE-001: Vollständige Pipeline: Index → Search → Prompt → Answer"""
        # Arrange
        mock_repos = self._create_mock_repos()
        
        # Mock: Indexed Document
        mock_indexed_doc = IndexedDocument(
            id=1,
            upload_document_id=1,
            collection_name="rag_documents",
            total_chunks=5,
            indexed_at=datetime.now(),
            last_updated_at=datetime.now()
        )
        mock_repos["indexed_document_repository"].get_by_upload_document_id.return_value = mock_indexed_doc
        
        # Mock Session
        mock_session = ChatSession(
            id=1,
            user_id=1,
            session_name="Test",
            last_message_at=datetime.now(),
            is_active=True,
            created_at=datetime.now()
        )
        mock_repos["session_repository"].get_by_id.return_value = mock_session
        
        # Mock Chunks
        mock_chunks = [
            {
                "chunk_id": "doc1_p1_c0",
                "text": "Test content",
                "metadata": {
                    "document_type": "FLOWCHART",
                    "page_numbers": [1],
                    "heading_hierarchy": ["1. Test"]
                },
                "relevance_score": 0.9
            }
        ]
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = mock_chunks
        
        # Mock AI Service
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "model_used": "gpt-4o-mini",
            "tokens_used": 100,
            "prompt_text": "ANWEISUNGEN (Flussdiagramm):\n1. Test"
        })
        
        # Mock Message Repository
        saved_message = None
        def save_message(msg):
            nonlocal saved_message
            saved_message = msg
            return msg
        
        mock_repos["message_repository"].save.side_effect = save_message
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Act
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            model_id="gpt-4o-mini"
        )
        
        # Assert: Vollständige Pipeline
        assert result is not None
        assert result.metadata is not None
        assert "prompt_text" in result.metadata
        assert result.ai_model_used == "gpt-4o-mini"
        assert len(result.source_references) > 0 or len(mock_chunks) == 0
    
    @pytest.mark.asyncio
    async def test_pipeline_with_interest_group_filtering(self):
        """IT-PIPELINE-002: Pipeline mit Interest Group Filtering"""
        # Arrange
        mock_repos = self._create_mock_repos()
        
        # Mock Permission Service: Level 2 (nur eigene Interest Groups)
        mock_permission_service = MagicMock()
        mock_permission_service.get_user_level.return_value = 2
        mock_permission_service.get_user_interest_groups.return_value = [1, 2]
        mock_repos["permission_service"] = mock_permission_service
        
        # Mock Session
        mock_session = ChatSession(
            id=1,
            user_id=1,
            session_name="Test",
            last_message_at=datetime.now(),
            is_active=True,
            created_at=datetime.now()
        )
        mock_repos["session_repository"].get_by_id.return_value = mock_session
        
        # Mock Chunks mit Interest Groups
        mock_chunks = [
            {
                "chunk_id": "doc1_p1_c0",
                "text": "Test content",
                "metadata": {
                    "document_type": "FLOWCHART",
                    "interest_group_ids": [1]  # User hat Zugriff
                },
                "relevance_score": 0.9
            },
            {
                "chunk_id": "doc2_p1_c0",
                "text": "Test content 2",
                "metadata": {
                    "document_type": "FLOWCHART",
                    "interest_group_ids": [3]  # User hat KEINEN Zugriff
                },
                "relevance_score": 0.8
            }
        ]
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = mock_chunks
        
        # Mock AI Service
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "model_used": "gpt-4o-mini",
            "tokens_used": 100,
            "prompt_text": "ANWEISUNGEN (Flussdiagramm):\n1. Test"
        })
        
        # Mock Message Repository
        saved_message = None
        def save_message(msg):
            nonlocal saved_message
            saved_message = msg
            return msg
        
        mock_repos["message_repository"].save.side_effect = save_message
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Act
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            model_id="gpt-4o-mini"
        )
        
        # Assert
        assert result is not None
        assert result.metadata is not None
        assert "prompt_text" in result.metadata
    
    @pytest.mark.asyncio
    async def test_pipeline_with_multi_query_expansion(self):
        """IT-PIPELINE-003: Pipeline mit Multi-Query Expansion"""
        # Arrange
        mock_repos = self._create_mock_repos()
        
        # Mock Multi-Query Service
        mock_repos["multi_query_service"].generate_queries = Mock(return_value=[
            "Test Frage",
            "Alternative Frage 1",
            "Alternative Frage 2"
        ])
        
        # Mock Session
        mock_session = ChatSession(
            id=1,
            user_id=1,
            session_name="Test",
            last_message_at=datetime.now(),
            is_active=True,
            created_at=datetime.now()
        )
        mock_repos["session_repository"].get_by_id.return_value = mock_session
        
        # Mock Chunks
        mock_chunks = [
            {
                "chunk_id": "doc1_p1_c0",
                "text": "Test content",
                "metadata": {"document_type": "FLOWCHART"},
                "relevance_score": 0.9
            }
        ]
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = mock_chunks
        
        # Mock AI Service
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "model_used": "gpt-4o-mini",
            "tokens_used": 100,
            "prompt_text": "ANWEISUNGEN (Flussdiagramm):\n1. Test"
        })
        
        # Mock Message Repository
        saved_message = None
        def save_message(msg):
            nonlocal saved_message
            saved_message = msg
            return msg
        
        mock_repos["message_repository"].save.side_effect = save_message
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Act
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            model_id="gpt-4o-mini",
            use_multi_query=True
        )
        
        # Assert
        assert result is not None
        assert result.metadata is not None
        assert "prompt_text" in result.metadata
        # Prüfe dass Multi-Query Service aufgerufen wurde
        assert mock_repos["multi_query_service"].generate_queries.called
    
    @pytest.mark.asyncio
    async def test_pipeline_with_hybrid_search(self):
        """IT-PIPELINE-004: Pipeline mit Hybrid Search"""
        # Arrange
        mock_repos = self._create_mock_repos()
        
        # Mock Session
        mock_session = ChatSession(
            id=1,
            user_id=1,
            session_name="Test",
            last_message_at=datetime.now(),
            is_active=True,
            created_at=datetime.now()
        )
        mock_repos["session_repository"].get_by_id.return_value = mock_session
        
        # Mock Chunks mit Hybrid Search
        mock_chunks = [
            {
                "chunk_id": "doc1_p1_c0",
                "text": "Test content",
                "metadata": {"document_type": "FLOWCHART"},
                "relevance_score": 0.9,
                "bm25_score": 0.8,
                "vector_score": 0.7
            }
        ]
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = mock_chunks
        
        # Mock AI Service
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "model_used": "gpt-4o-mini",
            "tokens_used": 100,
            "prompt_text": "ANWEISUNGEN (Flussdiagramm):\n1. Test"
        })
        
        # Mock Message Repository
        saved_message = None
        def save_message(msg):
            nonlocal saved_message
            saved_message = msg
            return msg
        
        mock_repos["message_repository"].save.side_effect = save_message
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Act
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            model_id="gpt-4o-mini",
            use_hybrid_search=True
        )
        
        # Assert
        assert result is not None
        assert result.metadata is not None
        assert "prompt_text" in result.metadata
        # Prüfe dass Hybrid Search verwendet wurde
        assert mock_repos["vector_store"].search_with_hybrid_scoring.called

