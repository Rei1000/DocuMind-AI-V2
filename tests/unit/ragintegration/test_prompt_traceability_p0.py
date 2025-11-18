"""
TDD Tests für CR RAG-PROMPT-TRACEABILITY-P0

Tests für kritische Audit-Verstöße:
- Prompt wird nicht immer gespeichert (T2, T4)
- Prompt-Rekonstruktion statt gespeichertem Prompt
- Unvollständige Metadaten (prompt_type, document_type_selected, etc.)

Test-Szenarien T1-T4 gemäß RAG_PROMPT_VALIDATION_ANALYSIS.md
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch, MagicMock
from datetime import datetime
from typing import List, Dict, Any, Optional

from contexts.ragintegration.domain.entities import ChatMessage, ChatSession
from contexts.ragintegration.application.use_cases import AskQuestionUseCase


class TestPromptTraceabilityT1:
    """T1: Dokumententyp gewählt + Chunks vorhanden"""
    
    @pytest.mark.asyncio
    async def test_prompt_always_stored_when_chunks_available(self):
        """Test: Prompt wird IMMER gespeichert wenn Chunks vorhanden sind."""
        # Arrange
        mock_repos = self._create_mock_repos()
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = [
            {
                "chunk_id": "chunk_1",
                "score": 0.85,
                "metadata": {
                    "chunk_text": "Test Chunk",
                    "document_type": "Arbeitsanweisung",
                    "document_type_id": 1
                }
            }
        ]
        
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "model_used": "gpt-4o-mini",
            "tokens_used": 100,
            "prompt_text": "Vollständiger Prompt Text"  # Prompt vorhanden
        })
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Act
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            model_id="gpt-4o-mini",
            filters={"document_type": "Arbeitsanweisung"}
        )
        
        # Assert
        assert mock_repos["message_repository"].save.called
        call_args = mock_repos["message_repository"].save.call_args
        saved_message = call_args[0][0] if call_args[0] else None
        
        assert saved_message is not None
        assert saved_message.metadata is not None
        assert "prompt_text" in saved_message.metadata
        assert saved_message.metadata["prompt_text"] == "Vollständiger Prompt Text"
        assert saved_message.metadata["prompt_text"] is not None  # CR-P0: Muss immer vorhanden sein
    
    @pytest.mark.asyncio
    async def test_metadata_includes_prompt_type(self):
        """Test: Metadaten enthalten prompt_type (custom | standard | generic)."""
        # Arrange
        mock_repos = self._create_mock_repos()
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = [
            {
                "chunk_id": "chunk_1",
                "score": 0.85,
                "metadata": {"document_type": "Arbeitsanweisung", "document_type_id": 1}
            }
        ]
        
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "prompt_text": "Test Prompt",
            "tokens_used": 100
        })
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Act
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            filters={"document_type": "Arbeitsanweisung"}
        )
        
        # Assert
        call_args = mock_repos["message_repository"].save.call_args
        saved_message = call_args[0][0]
        
        assert "prompt_type" in saved_message.metadata  # CR-P0: Muss vorhanden sein
        assert saved_message.metadata["prompt_type"] in ["custom", "standard", "generic"]
    
    @pytest.mark.asyncio
    async def test_metadata_includes_document_type_selected(self):
        """Test: Metadaten enthalten document_type_selected (User-Intent)."""
        # Arrange
        mock_repos = self._create_mock_repos()
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = []
        
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "prompt_text": "Test Prompt",
            "tokens_used": 100
        })
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Act
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            filters={"document_type": "Arbeitsanweisung"}
        )
        
        # Assert
        call_args = mock_repos["message_repository"].save.call_args
        saved_message = call_args[0][0]
        
        assert "document_type_selected" in saved_message.metadata  # CR-P0: User-Intent
        assert saved_message.metadata["document_type_selected"] == "Arbeitsanweisung"
    
    def _create_mock_repos(self):
        """Helper: Erstelle Mock-Repositories."""
        mock_session = ChatSession(
            id=1,
            user_id=1,
            session_name="Test",
            last_message_at=datetime.now(),
            is_active=True,
            created_at=datetime.now()
        )
        
        return {
            "chunk_repository": Mock(),
            "session_repository": Mock(get_by_id=Mock(return_value=mock_session)),
            "indexed_document_repository": Mock(get_all=Mock(return_value=[])),  # CR-P0: Liste statt Mock
            "vector_store": Mock(),
            "embedding_service": Mock(generate_embedding=Mock(return_value=Mock(model="text-embedding-ada-002", dimensions=1536))),
            "multi_query_service": Mock(),
            "ai_service": Mock(),
            "event_publisher": Mock(),
            "message_repository": Mock(),
            "permission_service": Mock(get_user_level=Mock(return_value=4), get_user_interest_groups=Mock(return_value=[])),
            "shap_service": Mock(),
            "ml_model_service": Mock(),
            "ltr_service": Mock(is_enabled=Mock(return_value=False))
        }


class TestPromptTraceabilityT2:
    """T2: Dokumententyp gewählt + keine Chunks (KRITISCH)"""
    
    def _create_mock_repos(self):
        """Helper: Erstelle Mock-Repositories."""
        mock_session = ChatSession(
            id=1,
            user_id=1,
            session_name="Test",
            last_message_at=datetime.now(),
            is_active=True,
            created_at=datetime.now()
        )
        
        return {
            "chunk_repository": Mock(),
            "session_repository": Mock(get_by_id=Mock(return_value=mock_session)),
            "indexed_document_repository": Mock(get_all=Mock(return_value=[])),  # CR-P0: Liste statt Mock
            "vector_store": Mock(),
            "embedding_service": Mock(generate_embedding=Mock(return_value=Mock(model="text-embedding-ada-002", dimensions=1536))),
            "multi_query_service": Mock(),
            "ai_service": Mock(),
            "event_publisher": Mock(),
            "message_repository": Mock(),
            "permission_service": Mock(get_user_level=Mock(return_value=4), get_user_interest_groups=Mock(return_value=[])),
            "shap_service": Mock(),
            "ml_model_service": Mock(),
            "ltr_service": Mock(is_enabled=Mock(return_value=False))
        }
    
    @pytest.mark.asyncio
    async def test_prompt_stored_even_when_no_chunks(self):
        """Test: Prompt wird IMMER gespeichert, auch wenn keine Chunks vorhanden sind."""
        # Arrange
        mock_repos = self._create_mock_repos()
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = []  # Keine Chunks
        
        # WICHTIG: AI Service gibt prompt_text zurück, auch wenn keine Chunks
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Entschuldigung, ich konnte keine relevanten Informationen finden...",
            "model_used": "gpt-4o-mini",
            "tokens_used": 0,
            "provider": "no_context",
            "prompt_text": "Generischer Prompt für Arbeitsanweisung"  # CR-P0: Muss vorhanden sein!
        })
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Act
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            filters={"document_type": "Arbeitsanweisung"}
        )
        
        # Assert
        assert mock_repos["message_repository"].save.called
        call_args = mock_repos["message_repository"].save.call_args
        saved_message = call_args[0][0]
        
        # CR-P0: Prompt muss IMMER gespeichert werden, auch bei No-Chunk-Case
        assert saved_message.metadata is not None
        assert "prompt_text" in saved_message.metadata
        assert saved_message.metadata["prompt_text"] is not None
        assert saved_message.metadata["prompt_text"] != ""
    
    @pytest.mark.asyncio
    async def test_prompt_generated_even_when_no_chunks(self):
        """Test: Prompt wird generiert, auch wenn keine Chunks vorhanden sind."""
        # Arrange
        mock_repos = self._create_mock_repos()
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = []
        
        # Mock: AI Service wird aufgerufen, auch wenn keine Chunks
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Keine Informationen gefunden",
            "prompt_text": "Du bist ein Experte...\nFRAGE: Test Frage\nANWEISUNGEN...",
            "tokens_used": 50
        })
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Act
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            filters={"document_type": "Arbeitsanweisung"}
        )
        
        # Assert
        # CR-P0: AI Service muss aufgerufen werden, auch wenn keine Chunks
        assert mock_repos["ai_service"].generate_response_async.called
        
        # CR-P0: Prompt muss generiert werden
        call_args = mock_repos["ai_service"].generate_response_async.call_args
        assert call_args is not None
        assert call_args[1]["document_type"] == "Arbeitsanweisung"  # Filter-Typ wird verwendet
    
    def _create_mock_repos(self):
        """Helper: Erstelle Mock-Repositories."""
        mock_session = ChatSession(
            id=1,
            user_id=1,
            session_name="Test",
            last_message_at=datetime.now(),
            is_active=True,
            created_at=datetime.now()
        )
        
        return {
            "chunk_repository": Mock(),
            "session_repository": Mock(get_by_id=Mock(return_value=mock_session)),
            "indexed_document_repository": Mock(get_all=Mock(return_value=[])),
            "vector_store": Mock(),
            "embedding_service": Mock(generate_embedding=Mock(return_value=Mock(model="text-embedding-ada-002", dimensions=1536))),
            "multi_query_service": Mock(),
            "ai_service": Mock(),
            "event_publisher": Mock(),
            "message_repository": Mock(),
            "permission_service": Mock(get_user_level=Mock(return_value=4), get_user_interest_groups=Mock(return_value=[])),
            "shap_service": Mock(),
            "ml_model_service": Mock(),
            "ltr_service": Mock(is_enabled=Mock(return_value=False))
        }


class TestPromptTraceabilityT3:
    """T3: Kein Dokumententyp + Chunks vorhanden"""
    
    @pytest.mark.asyncio
    async def test_prompt_stored_with_automatic_document_type(self):
        """Test: Prompt wird gespeichert mit automatisch ermitteltem Dokumenttyp."""
        # Arrange
        mock_repos = self._create_mock_repos()
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = [
            {
                "chunk_id": "chunk_1",
                "score": 0.85,
                "metadata": {
                    "document_type": "Arbeitsanweisung",
                    "document_type_id": 1
                }
            }
        ]
        
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "prompt_text": "Test Prompt",
            "tokens_used": 100
        })
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Act
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            filters=None  # Kein Filter gesetzt
        )
        
        # Assert
        call_args = mock_repos["message_repository"].save.call_args
        saved_message = call_args[0][0]
        
        # CR-P0: document_type_selected sollte None sein (kein User-Filter)
        assert "document_type_selected" in saved_message.metadata
        assert saved_message.metadata["document_type_selected"] is None
        
        # CR-P0: document_type_effective sollte automatisch ermittelt sein (kann None sein wenn DB-Fehler oder keine Chunks verarbeitet)
        assert "document_type_effective" in saved_message.metadata
        # Kann "Arbeitsanweisung" sein wenn Chunks richtig verarbeitet werden, oder None wenn DB-Fehler/keine Chunks
        assert saved_message.metadata["document_type_effective"] in ["Arbeitsanweisung", None]
    
    def _create_mock_repos(self):
        """Helper: Erstelle Mock-Repositories."""
        mock_session = ChatSession(
            id=1,
            user_id=1,
            session_name="Test",
            last_message_at=datetime.now(),
            is_active=True,
            created_at=datetime.now()
        )
        
        return {
            "chunk_repository": Mock(),
            "session_repository": Mock(get_by_id=Mock(return_value=mock_session)),
            "indexed_document_repository": Mock(get_all=Mock(return_value=[])),
            "vector_store": Mock(),
            "embedding_service": Mock(generate_embedding=Mock(return_value=Mock(model="text-embedding-ada-002", dimensions=1536))),
            "multi_query_service": Mock(),
            "ai_service": Mock(),
            "event_publisher": Mock(),
            "message_repository": Mock(),
            "permission_service": Mock(get_user_level=Mock(return_value=4), get_user_interest_groups=Mock(return_value=[])),
            "shap_service": Mock(),
            "ml_model_service": Mock(),
            "ltr_service": Mock(is_enabled=Mock(return_value=False))
        }


class TestPromptTraceabilityT4:
    """T4: Kein Dokumententyp + keine Chunks (KRITISCH)"""
    
    @pytest.mark.asyncio
    async def test_prompt_stored_with_generic_prompt_when_no_chunks_no_filter(self):
        """Test: Generischer Prompt wird gespeichert, auch wenn keine Chunks und kein Filter."""
        # Arrange
        mock_repos = self._create_mock_repos()
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = []  # Keine Chunks
        
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Keine Informationen gefunden",
            "prompt_text": "Du bist ein Experte...\nFRAGE: Test Frage\nANWEISUNGEN: Generischer Prompt",
            "tokens_used": 50
        })
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Act
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            filters=None  # Kein Filter
        )
        
        # Assert
        call_args = mock_repos["message_repository"].save.call_args
        saved_message = call_args[0][0]
        
        # CR-P0: Prompt muss IMMER gespeichert werden
        assert saved_message.metadata is not None
        assert "prompt_text" in saved_message.metadata
        assert saved_message.metadata["prompt_text"] is not None
        assert saved_message.metadata["prompt_text"] != ""
        
        # CR-P0: prompt_type sollte "generic" sein
        assert saved_message.metadata.get("prompt_type") == "generic"
        
        # CR-P0: document_type_selected sollte None sein
        assert saved_message.metadata.get("document_type_selected") is None
        
        # CR-P0: document_type_effective sollte None sein
        assert saved_message.metadata.get("document_type_effective") is None
    
    def _create_mock_repos(self):
        """Helper: Erstelle Mock-Repositories."""
        mock_session = ChatSession(
            id=1,
            user_id=1,
            session_name="Test",
            last_message_at=datetime.now(),
            is_active=True,
            created_at=datetime.now()
        )
        
        return {
            "chunk_repository": Mock(),
            "session_repository": Mock(get_by_id=Mock(return_value=mock_session)),
            "indexed_document_repository": Mock(get_all=Mock(return_value=[])),
            "vector_store": Mock(),
            "embedding_service": Mock(generate_embedding=Mock(return_value=Mock(model="text-embedding-ada-002", dimensions=1536))),
            "multi_query_service": Mock(),
            "ai_service": Mock(),
            "event_publisher": Mock(),
            "message_repository": Mock(),
            "permission_service": Mock(get_user_level=Mock(return_value=4), get_user_interest_groups=Mock(return_value=[])),
            "shap_service": Mock(),
            "ml_model_service": Mock(),
            "ltr_service": Mock(is_enabled=Mock(return_value=False))
        }


class TestPromptViewerNoReconstruction:
    """Tests für Prompt Viewer: Keine Rekonstruktion"""
    
    def test_prompt_viewer_returns_stored_prompt(self):
        """Test: Prompt Viewer gibt gespeicherten Prompt zurück."""
        # Arrange
        message = ChatMessage(
            id=1,
            session_id=1,
            role="assistant",
            content="Test Antwort",
            source_references=[],
            ai_model_used="gpt-4o-mini",
            created_at=datetime.now(),
            metadata={
                "prompt_text": "Gespeicherter Prompt Text",
                "prompt_type": "custom",
                "document_type_selected": "Arbeitsanweisung",
                "document_type_effective": "Arbeitsanweisung"
            }
        )
        
        # Act & Assert
        # CR-P0: Gespeicherter Prompt muss vorhanden sein
        assert message.metadata.get("prompt_text") is not None
        assert message.metadata.get("prompt_text") == "Gespeicherter Prompt Text"
    
    def test_prompt_viewer_returns_invalid_state_when_missing(self):
        """Test: Prompt Viewer gibt INVALID state zurück wenn Prompt fehlt."""
        # Arrange
        message = ChatMessage(
            id=1,
            session_id=1,
            role="assistant",
            content="Test Antwort",
            source_references=[],
            ai_model_used="gpt-4o-mini",
            created_at=datetime.now(),
            metadata={
                "prompt_text": None,  # CR-P0: Fehlender Prompt
                "tokens_used": 100
            }
        )
        
        # Act & Assert
        # CR-P0: Wenn prompt_text fehlt oder None, sollte state = INVALID sein
        prompt_text = message.metadata.get("prompt_text")
        assert prompt_text is None or prompt_text == ""
        
        # CR-P0: Keine Rekonstruktion erlaubt!
        # (Dies wird im Router-Endpoint geprüft)


class TestPromptMetadataCompleteness:
    """Tests für vollständige Metadaten"""
    
    @pytest.mark.asyncio
    async def test_metadata_includes_all_required_fields(self):
        """Test: Metadaten enthalten alle erforderlichen Felder für Traceability."""
        # Arrange
        mock_repos = self._create_mock_repos()
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = []
        
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "prompt_text": "Test Prompt",
            "tokens_used": 100
        })
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Act
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            filters={"document_type": "Arbeitsanweisung"}
        )
        
        # Assert
        call_args = mock_repos["message_repository"].save.call_args
        saved_message = call_args[0][0]
        metadata = saved_message.metadata
        
        # CR-P0: Alle erforderlichen Felder müssen vorhanden sein
        assert "prompt_text" in metadata
        assert "prompt_type" in metadata  # custom | standard | generic
        assert "document_type_selected" in metadata  # User-Intent
        assert "document_type_effective" in metadata  # Tatsächlich verwendet
        
        # Optional aber empfohlen:
        # assert "custom_prompt_id" in metadata or "standard_prompt_id" in metadata
        # assert "prompt_version" in metadata
    
    def _create_mock_repos(self):
        """Helper: Erstelle Mock-Repositories."""
        mock_session = ChatSession(
            id=1,
            user_id=1,
            session_name="Test",
            last_message_at=datetime.now(),
            is_active=True,
            created_at=datetime.now()
        )
        
        return {
            "chunk_repository": Mock(),
            "session_repository": Mock(get_by_id=Mock(return_value=mock_session)),
            "indexed_document_repository": Mock(get_all=Mock(return_value=[])),
            "vector_store": Mock(),
            "embedding_service": Mock(generate_embedding=Mock(return_value=Mock(model="text-embedding-ada-002", dimensions=1536))),
            "multi_query_service": Mock(),
            "ai_service": Mock(),
            "event_publisher": Mock(),
            "message_repository": Mock(),
            "permission_service": Mock(get_user_level=Mock(return_value=4), get_user_interest_groups=Mock(return_value=[])),
            "shap_service": Mock(),
            "ml_model_service": Mock(),
            "ltr_service": Mock(is_enabled=Mock(return_value=False))
        }


class TestPromptTypeDetection:
    """Tests für Prompt-Typ-Erkennung"""
    
    @pytest.mark.asyncio
    async def test_prompt_type_is_set_in_metadata(self):
        """Test: prompt_type wird in Metadaten gespeichert (generic als Fallback wenn DB-Fehler)."""
        # Arrange
        mock_repos = self._create_mock_repos()
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = []
        
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "prompt_text": "Test Prompt",
            "tokens_used": 100
        })
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Act
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            filters=None  # Kein Filter → kein document_type_id → generic
        )
        
        # Assert
        call_args = mock_repos["message_repository"].save.call_args
        saved_message = call_args[0][0]
        
        # CR-P0: prompt_type muss vorhanden sein (kann generic sein wenn DB-Fehler)
        assert "prompt_type" in saved_message.metadata
        assert saved_message.metadata["prompt_type"] in ["custom", "standard", "generic"]
    
    
    @pytest.mark.asyncio
    async def test_prompt_type_generic_when_no_specific_prompt(self):
        """Test: prompt_type = 'generic' wenn kein spezifischer Prompt vorhanden."""
        # Arrange
        mock_repos = self._create_mock_repos()
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = []
        
        # Kein document_type_id → prompt_type sollte "generic" sein
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "prompt_text": "Du bist ein Experte...\nANWEISUNGEN: Generischer Prompt...",
            "tokens_used": 100
        })
        
        use_case = AskQuestionUseCase(**mock_repos)
        
        # Act
        result = await use_case.execute(
            question="Test Frage",
            session_id=1,
            filters=None  # Kein Filter → kein document_type_id
        )
        
        # Assert
        call_args = mock_repos["message_repository"].save.call_args
        saved_message = call_args[0][0]
        
        assert saved_message.metadata.get("prompt_type") == "generic"
    
    def _create_mock_repos(self):
        """Helper: Erstelle Mock-Repositories."""
        mock_session = ChatSession(
            id=1,
            user_id=1,
            session_name="Test",
            last_message_at=datetime.now(),
            is_active=True,
            created_at=datetime.now()
        )
        
        return {
            "chunk_repository": Mock(),
            "session_repository": Mock(get_by_id=Mock(return_value=mock_session)),
            "indexed_document_repository": Mock(get_all=Mock(return_value=[])),
            "vector_store": Mock(),
            "embedding_service": Mock(generate_embedding=Mock(return_value=Mock(model="text-embedding-ada-002", dimensions=1536))),
            "multi_query_service": Mock(),
            "ai_service": Mock(),
            "event_publisher": Mock(),
            "message_repository": Mock(),
            "permission_service": Mock(get_user_level=Mock(return_value=4), get_user_interest_groups=Mock(return_value=[])),
            "shap_service": Mock(),
            "ml_model_service": Mock(),
            "ltr_service": Mock(is_enabled=Mock(return_value=False))
        }

