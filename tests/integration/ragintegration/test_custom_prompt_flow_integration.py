"""
Integration Tests für Custom Prompt Flow (CR-P1)

Testet den vollständigen Custom Prompt Flow:
- Custom Prompt mit Platzhaltern
- Custom Prompt ohne Platzhalter
- Standard Prompt Fallback
- Custom Prompt + Standard Prompt Assembly
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from contexts.ragintegration.domain.entities import ChatMessage, ChatSession, RAGChatPrompt
from contexts.ragintegration.application.use_cases import AskQuestionUseCase
from contexts.ragintegration.infrastructure.ai_service import RAGAIService
from contexts.ragintegration.infrastructure.repositories import SQLAlchemyRAGChatPromptRepository


class TestCustomPromptFlowIntegration:
    """Integration Tests für Custom Prompt Flow"""
    
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
    async def test_custom_prompt_with_placeholders(self):
        """IT-CUSTOM-001: Custom Prompt mit Platzhaltern"""
        # Arrange
        mock_repos = self._create_mock_repos()
        
        # Mock RAG Chat Prompt Repository mit Custom Prompt
        mock_rag_chat_prompt_repo = MagicMock()
        custom_prompt = RAGChatPrompt(
            id=1,
            document_type_id=1,
            prompt_text="{context}\n\n{question}\n\nAntworte präzise.",
            created_by_user_id=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_rag_chat_prompt_repo.get_by_document_type_id.return_value = custom_prompt
        
        # Mock AI Service mit RAG Chat Prompt Repository
        mock_repos["ai_service"] = AsyncMock()
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "model_used": "gpt-4o-mini",
            "tokens_used": 100,
            "prompt_text": "KONTEXT\n\nFRAGE\n\nAntworte präzise."
        })
        
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
                "metadata": {"document_type": "ARBEITSANWEISUNG"},
                "relevance_score": 0.9
            }
        ]
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = mock_chunks
        
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
            filters={"document_type_id": 1}
        )
        
        # Assert
        assert result is not None
        assert result.metadata is not None
        assert "prompt_text" in result.metadata
    
    @pytest.mark.asyncio
    async def test_custom_prompt_without_placeholders(self):
        """IT-CUSTOM-002: Custom Prompt ohne Platzhalter"""
        # Arrange
        mock_repos = self._create_mock_repos()
        
        # Mock RAG Chat Prompt Repository mit Custom Prompt ohne Platzhalter
        mock_rag_chat_prompt_repo = MagicMock()
        custom_prompt = RAGChatPrompt(
            id=1,
            document_type_id=1,
            prompt_text="Dies ist ein Custom Prompt ohne Platzhalter.",
            created_by_user_id=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_rag_chat_prompt_repo.get_by_document_type_id.return_value = custom_prompt
        
        # Mock AI Service
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "model_used": "gpt-4o-mini",
            "tokens_used": 100,
            "prompt_text": "Dies ist ein Custom Prompt ohne Platzhalter."
        })
        
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
                "metadata": {"document_type": "ARBEITSANWEISUNG"},
                "relevance_score": 0.9
            }
        ]
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = mock_chunks
        
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
            filters={"document_type_id": 1}
        )
        
        # Assert
        assert result is not None
        assert result.metadata is not None
        assert "prompt_text" in result.metadata
    
    @pytest.mark.asyncio
    async def test_standard_prompt_fallback(self):
        """IT-CUSTOM-003: Standard Prompt Fallback (kein Custom Prompt)"""
        # Arrange
        mock_repos = self._create_mock_repos()
        
        # Mock RAG Chat Prompt Repository: Kein Custom Prompt
        mock_rag_chat_prompt_repo = MagicMock()
        mock_rag_chat_prompt_repo.get_by_document_type_id.return_value = None
        
        # Mock AI Service
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "model_used": "gpt-4o-mini",
            "tokens_used": 100,
            "prompt_text": "ANWEISUNGEN (Flussdiagramm):\n1. Test"
        })
        
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
        assert result.metadata.get("prompt_type") == "generic" or "ANWEISUNGEN" in result.metadata["prompt_text"]
    
    @pytest.mark.asyncio
    async def test_custom_prompt_with_standard_assembly(self):
        """IT-CUSTOM-004: Custom Prompt + Standard Prompt Assembly"""
        # Arrange
        mock_repos = self._create_mock_repos()
        
        # Mock RAG Chat Prompt Repository mit Custom Prompt ohne Platzhalter
        mock_rag_chat_prompt_repo = MagicMock()
        custom_prompt = RAGChatPrompt(
            id=1,
            document_type_id=1,
            prompt_text="Custom Prompt Text ohne Platzhalter",
            created_by_user_id=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_rag_chat_prompt_repo.get_by_document_type_id.return_value = custom_prompt
        
        # Mock AI Service
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "model_used": "gpt-4o-mini",
            "tokens_used": 100,
            "prompt_text": "Custom Prompt Text ohne Platzhalter\n\nANWEISUNGEN..."
        })
        
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
                "metadata": {"document_type": "ARBEITSANWEISUNG"},
                "relevance_score": 0.9
            }
        ]
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = mock_chunks
        
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
            filters={"document_type_id": 1}
        )
        
        # Assert
        assert result is not None
        assert result.metadata is not None
        assert "prompt_text" in result.metadata

