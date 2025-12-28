"""
E2E Integration Tests für Prompt-Flow (CR-P0, CR-P1, CR-P2.1)

Testet den vollständigen Flow:
- Question → Prompt-Erkennung → Prompt-Generierung → AI-Response → Prompt-Speicherung → Metadaten
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from contexts.ragintegration.domain.entities import ChatMessage, ChatSession
from contexts.ragintegration.application.use_cases import AskQuestionUseCase
from contexts.ragintegration.infrastructure.ai_service import RAGAIService
from contexts.ragintegration.infrastructure.prompt_structure_detector import detect_prompt_structure_type


class TestE2EPromptFlowIntegration:
    """E2E Integration Tests für Prompt-Flow"""
    
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
    async def test_complete_prompt_flow_with_chunks(self):
        """IT-E2E-001: Vollständiger Prompt-Flow mit Chunks"""
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
        
        # Mock Chunks mit Metadaten
        mock_chunks = [
            {
                "chunk_id": "doc1_p1_c0",
                "text": "Test content",
                "metadata": {
                    "document_type": "FLOWCHART",
                    "document_type_name": "Flussdiagramm",
                    "page_numbers": [1],
                    "heading_hierarchy": ["1. Test"]
                },
                "relevance_score": 0.9
            }
        ]
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = mock_chunks
        
        # Mock AI Service Response mit Prompt
        test_prompt = "ANWEISUNGEN (Flussdiagramm):\n1. Test"
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "model_used": "gpt-4o-mini",
            "tokens_used": 100,
            "prompt_text": test_prompt
        })
        
        # Mock Message Repository
        saved_message = None
        def save_message(msg):
            nonlocal saved_message
            saved_message = ChatMessage(
                id=1,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                source_references=msg.source_references,
                ai_model_used=msg.ai_model_used,
                created_at=msg.created_at,
                metadata=msg.metadata
            )
            return saved_message
        
        mock_repos["message_repository"].save.side_effect = save_message
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Act
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            model_id="gpt-4o-mini"
        )
        
        # Assert: Vollständiger Flow
        assert result is not None
        assert result.metadata is not None
        assert "prompt_text" in result.metadata
        assert result.metadata["prompt_text"] == test_prompt
        assert "prompt_type" in result.metadata
        assert "document_type_effective" in result.metadata or result.metadata.get("document_type_effective") == "FLOWCHART"
        assert result.ai_model_used == "gpt-4o-mini"
    
    @pytest.mark.asyncio
    async def test_prompt_flow_without_chunks_fallback(self):
        """IT-E2E-002: Prompt-Flow ohne Chunks (Fallback)"""
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
        
        # Mock: Keine Chunks
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = []
        
        # Mock AI Service Response mit Generic Prompt
        generic_prompt = "ANWEISUNGEN:\n1. Generischer Prompt"
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "model_used": "gpt-4o-mini",
            "tokens_used": 100,
            "prompt_text": generic_prompt
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
        assert result.metadata["prompt_text"] == generic_prompt
        assert result.metadata.get("prompt_type") == "generic" or "ANWEISUNGEN" in result.metadata["prompt_text"]
    
    @pytest.mark.asyncio
    async def test_prompt_flow_with_query_expansion(self):
        """IT-E2E-003: Prompt-Flow mit Query-Expansion"""
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
        
        # Mock: Query-Expansion Chunk (Dummy-Chunk mit query_expansion Flag)
        mock_chunks = [
            {
                "chunk_id": "query_expansion_dummy",
                "text": "Query Expansion",
                "metadata": {"query_expansion": True},
                "relevance_score": 1.0
            }
        ]
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = mock_chunks
        
        # Mock AI Service Response
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Query Varianten",
            "model_used": "gpt-4o-mini",
            "tokens_used": 50,
            "prompt_text": "Test Frage"  # Query-Expansion verwendet Frage direkt als Prompt
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

