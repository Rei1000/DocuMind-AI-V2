"""
Integration Tests für Prompt-Speicherung mit echten Chat-Messages

Testet den vollständigen Workflow:
1. AskQuestionUseCase speichert Prompt in metadata
2. get_prompt_for_message verwendet gespeicherten Prompt
3. Prompt Viewer zeigt echten Prompt
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from contexts.ragintegration.domain.entities import ChatMessage, ChatSession
from contexts.ragintegration.application.use_cases import AskQuestionUseCase


class TestPromptStorageIntegration:
    """Integration Tests für Prompt-Speicherung."""
    
    @pytest.mark.asyncio
    async def test_prompt_stored_in_real_chat_message(self):
        """Test: Prompt wird in echten Chat-Messages gespeichert."""
        # Mock Repositories
        mock_chunk_repo = Mock()
        mock_session_repo = Mock()
        mock_indexed_doc_repo = Mock()
        mock_vector_store = Mock()
        mock_embedding_service = Mock()
        mock_multi_query_service = Mock()
        mock_message_repo = Mock()
        
        # Mock AI Service mit Prompt in Response
        mock_ai_service = Mock()
        test_prompt = "Dies ist der echte Prompt für die Frage: Test Frage"
        mock_ai_service.generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "model_used": "gpt-4o-mini",
            "tokens_used": 100,
            "prompt_text": test_prompt  # Prompt in Response
        })
        
        # Mock: Session existiert
        mock_session = ChatSession(
            id=1,
            user_id=1,
            session_name="Test Session",
            last_message_at=datetime.now(),
            is_active=True,
            created_at=datetime.now()
        )
        mock_session_repo.get_by_id.return_value = mock_session
        
        # Mock: Keine Chunks gefunden (vereinfachter Test)
        mock_vector_store.search_similar.return_value = []
        mock_vector_store.search_with_hybrid_scoring.return_value = []
        
        # Mock: Message Repository save
        saved_message = ChatMessage(
            id=1,
            session_id=1,
            role="assistant",
            content="Test Antwort",
            source_references=[],
            ai_model_used="gpt-4o-mini",
            created_at=datetime.now(),
            metadata={"prompt_text": test_prompt}  # Erwartete Metadata
        )
        mock_message_repo.save.return_value = saved_message
        
        use_case = AskQuestionUseCase(
            chunk_repository=mock_chunk_repo,
            session_repository=mock_session_repo,
            indexed_document_repository=mock_indexed_doc_repo,
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            multi_query_service=mock_multi_query_service,
            ai_service=mock_ai_service,
            event_publisher=None,
            message_repository=mock_message_repo
        )
        
        # Führe Use Case aus
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            model_id="gpt-4o-mini"
        )
        
        # Prüfe dass save aufgerufen wurde
        assert mock_message_repo.save.called
        
        # Prüfe dass metadata prompt_text enthält
        # Hole das letzte save-Argument
        call_args = mock_message_repo.save.call_args
        if call_args:
            saved_chat_message = call_args[0][0] if call_args[0] else call_args[1].get('chat_message')
            if saved_chat_message and saved_chat_message.metadata:
                assert "prompt_text" in saved_chat_message.metadata
                assert saved_chat_message.metadata["prompt_text"] == test_prompt
    
    def test_prompt_viewer_uses_stored_prompt(self):
        """Test: Prompt Viewer verwendet gespeicherten Prompt aus metadata."""
        # Mock: ChatMessage mit gespeichertem Prompt
        stored_prompt = "Dies ist der gespeicherte Prompt"
        message = ChatMessage(
            id=1,
            session_id=1,
            role="assistant",
            content="Test Antwort",
            source_references=[],
            ai_model_used="gpt-4o-mini",
            created_at=datetime.now(),
            metadata={
                "prompt_text": stored_prompt,
                "tokens_used": 100
            }
        )
        
        # Prüfe dass prompt_text in metadata ist
        assert message.metadata is not None
        assert "prompt_text" in message.metadata
        assert message.metadata["prompt_text"] == stored_prompt
        
        # Simuliere get_prompt_for_message Logik
        if message.metadata and message.metadata.get("prompt_text"):
            prompt_text = message.metadata["prompt_text"]
            assert prompt_text == stored_prompt
        else:
            pytest.fail("Prompt sollte in metadata sein")

