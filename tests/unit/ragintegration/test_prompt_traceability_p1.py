"""
CR-P1 Tests: Custom Prompt ohne Platzhalter & Dokumenttyp-Widerspruch

Test-Szenarien für CR-P1:
- Custom Prompt ohne Platzhalter wird unterstützt
- Warnung bei widersprüchlichem Dokumenttyp

TDD Strict: RED Phase - Tests müssen initial fehlschlagen
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from contexts.ragintegration.domain.entities import ChatMessage, ChatSession
from contexts.ragintegration.application.use_cases import AskQuestionUseCase


class TestCustomPromptWithoutPlaceholders:
    """CR-P1: Custom Prompt ohne Platzhalter unterstützen"""
    
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
    
    @pytest.mark.asyncio
    async def test_custom_prompt_used_without_context_placeholder(self):
        """CR-P1: Custom Prompt ohne {context} Platzhalter wird verwendet."""
        # Arrange
        mock_repos = self._create_mock_repos()
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = [
            {
                "chunk_id": "chunk_1",
                "score": 0.85,
                "metadata": {
                    "document_type": "Arbeitsanweisung",
                    "document_type_id": 1,
                    "chunk_text": "Test Chunk"
                }
            }
        ]
        
        # Mock: Custom Prompt OHNE {context} Platzhalter
        custom_prompt_text = "Du bist ein Experte. Beantworte die Frage: {question}"
        # {context} fehlt!
        
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "prompt_text": custom_prompt_text,  # Custom Prompt sollte verwendet werden
            "tokens_used": 100,
            "custom_prompt_missing_placeholders": True  # CR-P1: Warnung sollte vorhanden sein
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
        
        # CR-P1: Custom Prompt sollte verwendet werden (auch ohne {context})
        assert saved_message.metadata.get("prompt_text") is not None
        # CR-P1: Warnung sollte gespeichert sein wenn Platzhalter fehlen
        assert saved_message.metadata.get("custom_prompt_missing_placeholders") is not None
        assert saved_message.metadata.get("custom_prompt_missing_placeholders") == True
    
    @pytest.mark.asyncio
    async def test_custom_prompt_used_without_question_placeholder(self):
        """CR-P1: Custom Prompt ohne {question} Platzhalter wird verwendet."""
        # Arrange
        mock_repos = self._create_mock_repos()
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = [
            {
                "chunk_id": "chunk_1",
                "score": 0.85,
                "metadata": {
                    "document_type": "Arbeitsanweisung",
                    "document_type_id": 1,
                    "chunk_text": "Test Chunk"
                }
            }
        ]
        
        # Mock: Custom Prompt OHNE {question} Platzhalter
        custom_prompt_text = "Du bist ein Experte. Kontext: {context}"
        # {question} fehlt!
        
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "prompt_text": custom_prompt_text,  # Custom Prompt sollte verwendet werden
            "tokens_used": 100,
            "custom_prompt_missing_placeholders": True  # CR-P1: Warnung sollte vorhanden sein
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
        
        # CR-P1: Custom Prompt sollte verwendet werden (auch ohne {question})
        assert saved_message.metadata.get("prompt_text") is not None
        # CR-P1: Warnung sollte gespeichert sein
        assert saved_message.metadata.get("custom_prompt_missing_placeholders") is not None
        assert saved_message.metadata.get("custom_prompt_missing_placeholders") == True
    
    @pytest.mark.asyncio
    async def test_custom_prompt_used_with_all_placeholders(self):
        """CR-P1: Custom Prompt mit allen Platzhaltern wird verwendet (keine Warnung)."""
        # Arrange
        mock_repos = self._create_mock_repos()
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = [
            {
                "chunk_id": "chunk_1",
                "score": 0.85,
                "metadata": {
                    "document_type": "Arbeitsanweisung",
                    "document_type_id": 1,
                    "chunk_text": "Test Chunk"
                }
            }
        ]
        
        # Mock: Custom Prompt MIT allen Platzhaltern
        custom_prompt_text = "Du bist ein Experte. Kontext: {context}\nFrage: {question}"
        
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "prompt_text": custom_prompt_text,
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
        
        # CR-P1: Custom Prompt sollte verwendet werden
        assert saved_message.metadata.get("prompt_text") is not None
        # CR-P1: Keine Warnung wenn alle Platzhalter vorhanden
        assert saved_message.metadata.get("custom_prompt_missing_placeholders") != True
    
    @pytest.mark.asyncio
    async def test_custom_prompt_warning_in_metadata(self):
        """CR-P1: Warnung wird in Metadaten gespeichert wenn Platzhalter fehlen."""
        # Arrange
        mock_repos = self._create_mock_repos()
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = []
        
        # Mock: Custom Prompt OHNE Platzhalter
        custom_prompt_text = "Du bist ein Experte. Beantworte die Frage."
        # Keine Platzhalter!
        
        mock_repos["ai_service"].generate_response_async = AsyncMock(return_value={
            "answer": "Test Antwort",
            "prompt_text": custom_prompt_text,
            "tokens_used": 100,
            "custom_prompt_missing_placeholders": True  # CR-P1: Warnung sollte vorhanden sein
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
        
        # CR-P1: Warnung muss in Metadaten vorhanden sein
        assert "custom_prompt_missing_placeholders" in saved_message.metadata
        assert saved_message.metadata.get("custom_prompt_missing_placeholders") == True


class TestDocumentTypeMismatch:
    """CR-P1: Warnung bei widersprüchlichem Dokumenttyp"""
    
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
    
    @pytest.mark.asyncio
    @patch('backend.app.database.SessionLocal')
    async def test_document_type_mismatch_detected(self, mock_session_local):
        """CR-P1: Widerspruch zwischen Filter und Chunk-Analyse wird erkannt."""
        # Arrange
        mock_repos = self._create_mock_repos()
        # Mock: Mindestens ein IndexedDocument muss vorhanden sein, damit Chunks verarbeitet werden
        mock_indexed_doc = Mock()
        mock_indexed_doc.upload_document_id = 1
        mock_indexed_doc.id = 1
        mock_repos["indexed_document_repository"].get_all.return_value = [mock_indexed_doc]
        
        # Mock DB Session für document_type Filter (damit Filter nicht alle Dokumente herausfiltert)
        mock_db_session = Mock()
        mock_query = Mock()
        mock_doc_type = Mock()
        mock_doc_type.id = 1
        mock_query.join.return_value.filter.return_value.all.return_value = [(1,)]  # upload_document_id = 1
        mock_db_session.query.return_value = mock_query
        mock_session_local.return_value = mock_db_session
        
        # Filter: Arbeitsanweisung
        # Chunks: SOP (Widerspruch!)
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = [
            {
                "chunk_id": "chunk_1",
                "score": 0.85,
                "metadata": {
                    "document_type": "SOP",  # Widerspruch zu Filter!
                    "document_type_id": 2,
                    "chunk_text": "Test Chunk"
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
            filters={"document_type": "Arbeitsanweisung"}  # Filter: Arbeitsanweisung
        )
        
        # Assert
        call_args = mock_repos["message_repository"].save.call_args
        saved_message = call_args[0][0]
        
        # CR-P1: Widerspruch sollte erkannt werden
        assert saved_message.metadata.get("document_type_selected") == "Arbeitsanweisung"
        assert saved_message.metadata.get("document_type_effective") == "SOP"  # Aus Chunks
        # CR-P1: Warnung sollte gespeichert sein
        assert saved_message.metadata.get("document_type_mismatch_warning") is not None
        assert saved_message.metadata.get("document_type_mismatch_warning") == True
    
    @pytest.mark.asyncio
    @patch('backend.app.database.SessionLocal')
    async def test_document_type_mismatch_warning_in_metadata(self, mock_session_local):
        """CR-P1: Warnung wird in Metadaten gespeichert bei Widerspruch."""
        # Arrange
        mock_repos = self._create_mock_repos()
        # Mock: Mindestens ein IndexedDocument muss vorhanden sein
        mock_indexed_doc = Mock()
        mock_indexed_doc.upload_document_id = 1
        mock_indexed_doc.id = 1
        mock_repos["indexed_document_repository"].get_all.return_value = [mock_indexed_doc]
        
        # Mock DB Session für document_type Filter
        mock_db_session = Mock()
        mock_query = Mock()
        mock_query.join.return_value.filter.return_value.all.return_value = [(1,)]
        mock_db_session.query.return_value = mock_query
        mock_session_local.return_value = mock_db_session
        
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = [
            {
                "chunk_id": "chunk_1",
                "score": 0.85,
                "metadata": {
                    "document_type": "Formular",  # Widerspruch!
                    "document_type_id": 3,
                    "chunk_text": "Test Chunk"
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
            filters={"document_type": "Arbeitsanweisung"}  # Filter: Arbeitsanweisung
        )
        
        # Assert
        call_args = mock_repos["message_repository"].save.call_args
        saved_message = call_args[0][0]
        
        # CR-P1: Warnung muss in Metadaten vorhanden sein
        assert "document_type_mismatch_warning" in saved_message.metadata
        assert saved_message.metadata.get("document_type_mismatch_warning") == True
        # CR-P1: Beide Werte müssen vorhanden sein für Vergleich
        assert saved_message.metadata.get("document_type_selected") is not None
        assert saved_message.metadata.get("document_type_effective") is not None
    
    @pytest.mark.asyncio
    @patch('backend.app.database.SessionLocal')
    async def test_no_mismatch_when_types_match(self, mock_session_local):
        """CR-P1: Keine Warnung wenn Filter und Chunk-Analyse übereinstimmen."""
        # Arrange
        mock_repos = self._create_mock_repos()
        # Mock: Mindestens ein IndexedDocument muss vorhanden sein
        mock_indexed_doc = Mock()
        mock_indexed_doc.upload_document_id = 1
        mock_indexed_doc.id = 1
        mock_repos["indexed_document_repository"].get_all.return_value = [mock_indexed_doc]
        
        # Mock DB Session für document_type Filter
        mock_db_session = Mock()
        mock_query = Mock()
        mock_query.join.return_value.filter.return_value.all.return_value = [(1,)]
        mock_db_session.query.return_value = mock_query
        mock_session_local.return_value = mock_db_session
        
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = [
            {
                "chunk_id": "chunk_1",
                "score": 0.85,
                "metadata": {
                    "document_type": "Arbeitsanweisung",  # Übereinstimmung!
                    "document_type_id": 1,
                    "chunk_text": "Test Chunk"
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
            filters={"document_type": "Arbeitsanweisung"}  # Filter: Arbeitsanweisung
        )
        
        # Assert
        call_args = mock_repos["message_repository"].save.call_args
        saved_message = call_args[0][0]
        
        # CR-P1: Keine Warnung wenn Typen übereinstimmen
        assert saved_message.metadata.get("document_type_selected") == "Arbeitsanweisung"
        assert saved_message.metadata.get("document_type_effective") == "Arbeitsanweisung"
        # CR-P1: Keine Warnung wenn keine Widerspruch
        assert saved_message.metadata.get("document_type_mismatch_warning") != True
    
    @pytest.mark.asyncio
    async def test_no_mismatch_when_no_filter(self):
        """CR-P1: Keine Warnung wenn kein Filter gesetzt (kein User-Intent)."""
        # Arrange
        mock_repos = self._create_mock_repos()
        # Mock: Mindestens ein IndexedDocument muss vorhanden sein
        mock_indexed_doc = Mock()
        mock_indexed_doc.upload_document_id = 1
        mock_indexed_doc.id = 1
        mock_repos["indexed_document_repository"].get_all.return_value = [mock_indexed_doc]
        
        mock_repos["vector_store"].search_with_hybrid_scoring.return_value = [
            {
                "chunk_id": "chunk_1",
                "score": 0.85,
                "metadata": {
                    "document_type": "Arbeitsanweisung",
                    "document_type_id": 1,
                    "chunk_text": "Test Chunk"
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
        
        # CR-P1: Keine Warnung wenn kein Filter (kein User-Intent)
        assert saved_message.metadata.get("document_type_selected") is None
        assert saved_message.metadata.get("document_type_effective") == "Arbeitsanweisung"  # Aus Chunks
        # CR-P1: Keine Warnung wenn kein Filter gesetzt
        assert saved_message.metadata.get("document_type_mismatch_warning") != True

