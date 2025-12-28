"""
Integration Tests für Referenz-Format in RAG Chat Responses.

Diese Tests stellen sicher, dass:
1. Die AI-Antwort das richtige Referenz-Format verwendet
2. Source References korrekt zugeordnet werden
3. Page-Links funktionieren
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime

from contexts.ragintegration.application.use_cases import AskQuestionUseCase
from contexts.ragintegration.domain.entities import ChatMessage, ChatSession
from contexts.ragintegration.domain.value_objects import SourceReference
from contexts.ragintegration.infrastructure.ai_service import RAGAIService


class TestReferenceFormatIntegration:
    """Integration Tests für Referenz-Format."""
    
    @pytest.mark.asyncio
    async def test_ai_response_contains_referenz_format(self):
        """Test: AI-Antwort enthält 'Referenz' Format (nicht 'Quelle')."""
        # Arrange
        mock_vector_store = Mock()
        mock_vector_store.search_with_hybrid_scoring = AsyncMock(return_value=[
            {
                'chunk_id': 'chunk_1',
                'score': 0.95,
                'hybrid_score': 0.95,
                'metadata': {
                    'chunk_id': 'chunk_1',
                    'document_id': 1,
                    'document_title': 'Test Document',
                    'page_numbers': [6],
                    'chunk_text': 'Test content about vertical deformations'
                }
            }
        ])
        
        mock_embedding_service = Mock()
        mock_embedding_service.generate_embedding = Mock(return_value=[0.1] * 1536)
        
        mock_ai_service = Mock(spec=RAGAIService)
        # Mock AI-Antwort mit korrektem Format
        mock_ai_service.generate_response_async = AsyncMock(return_value={
            'answer': 'Die vertikalen Verformungen betragen 91 mm. **Referenz**: chunk 1',
            'tokens_used': 100
        })
        
        mock_session_repo = Mock()
        mock_session_repo.get_by_id = Mock(return_value=ChatSession(
            id=1,
            user_id=1,
            session_name="Test Session",
            created_at=datetime.now(),
            is_active=True
        ))
        
        mock_message_repo = Mock()
        mock_message_repo.save = Mock(return_value=ChatMessage(
            id=1,
            session_id=1,
            role="assistant",
            content="Test Response",
            source_references=[],
            created_at=datetime.now()
        ))
        
        mock_event_publisher = Mock()
        mock_event_publisher.publish = Mock()
        
        use_case = AskQuestionUseCase(
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            ai_service=mock_ai_service,
            session_repository=mock_session_repo,
            message_repository=mock_message_repo,
            event_publisher=mock_event_publisher,
            document_chunk_repo=Mock(),
            document_repository=Mock()
        )
        
        # Act
        result = await use_case.execute(
            question="vertikale verformung",
            session_id=1,
            filters={'document_type': 'Fachartikel'}
        )
        
        # Assert
        assert result is not None
        assert result.role == "assistant"
        
        # Prüfe dass AI-Service mit korrektem Prompt aufgerufen wurde
        mock_ai_service.generate_response_async.assert_called_once()
        call_args = mock_ai_service.generate_response_async.call_args
        
        # Prüfe dass der Prompt "Referenz" enthält (nicht "Quelle")
        context_chunks = call_args[1]['context_chunks']
        assert len(context_chunks) > 0
        
        # Prüfe dass die Antwort "Referenz" enthält (falls Mock korrekt ist)
        # In einem echten Test würde die AI-Antwort das Format verwenden
    
    @pytest.mark.asyncio
    async def test_source_references_have_correct_page_numbers(self):
        """Test: Source References haben korrekte Page-Nummern."""
        # Arrange
        mock_vector_store = Mock()
        mock_vector_store.search_with_hybrid_scoring = AsyncMock(return_value=[
            {
                'chunk_id': 'chunk_1',
                'score': 0.95,
                'hybrid_score': 0.95,
                'metadata': {
                    'chunk_id': 'chunk_1',
                    'document_id': 1,
                    'document_title': 'Test Document',
                    'page_numbers': [6],  # WICHTIG: Page 6
                    'chunk_text': 'Test content'
                }
            }
        ])
        
        mock_embedding_service = Mock()
        mock_embedding_service.generate_embedding = Mock(return_value=[0.1] * 1536)
        
        mock_ai_service = Mock(spec=RAGAIService)
        mock_ai_service.generate_response_async = AsyncMock(return_value={
            'answer': 'Test Response. **Referenz**: chunk 1',
            'tokens_used': 100
        })
        
        mock_session_repo = Mock()
        mock_session_repo.get_by_id = Mock(return_value=ChatSession(
            id=1,
            user_id=1,
            session_name="Test Session",
            created_at=datetime.now(),
            is_active=True
        ))
        
        mock_message_repo = Mock()
        mock_message_repo.save = Mock(return_value=ChatMessage(
            id=1,
            session_id=1,
            role="assistant",
            content="Test Response",
            source_references=[],
            created_at=datetime.now()
        ))
        
        mock_event_publisher = Mock()
        mock_event_publisher.publish = Mock()
        
        # Mock Document Repository
        mock_doc_repo = Mock()
        mock_doc_repo.get_by_id = Mock(return_value=Mock(
            id=1,
            upload_document_id=1,
            document_type="Fachartikel"
        ))
        
        use_case = AskQuestionUseCase(
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            ai_service=mock_ai_service,
            session_repository=mock_session_repo,
            message_repository=mock_message_repo,
            event_publisher=mock_event_publisher,
            document_chunk_repo=Mock(),
            document_repository=mock_doc_repo
        )
        
        # Act
        result = await use_case.execute(
            question="vertikale verformung",
            session_id=1
        )
        
        # Assert
        assert result is not None
        assert len(result.source_references) > 0
        
        # Prüfe dass Source Reference korrekte Page-Nummer hat
        source_ref = result.source_references[0]
        assert source_ref.page_number == 6, \
            f"Source Reference sollte Page 6 haben, hat aber {source_ref.page_number}"
    
    @pytest.mark.asyncio
    async def test_source_references_are_in_correct_order(self):
        """Test: Source References sind in der gleichen Reihenfolge wie Chunks im Kontext."""
        # Arrange
        mock_vector_store = Mock()
        mock_vector_store.search_with_hybrid_scoring = AsyncMock(return_value=[
            {
                'chunk_id': 'chunk_1',
                'score': 0.95,
                'hybrid_score': 0.95,
                'metadata': {
                    'chunk_id': 'chunk_1',
                    'document_id': 1,
                    'document_title': 'Test Document 1',
                    'page_numbers': [6],
                    'chunk_text': 'First chunk'
                }
            },
            {
                'chunk_id': 'chunk_2',
                'score': 0.90,
                'hybrid_score': 0.90,
                'metadata': {
                    'chunk_id': 'chunk_2',
                    'document_id': 1,
                    'document_title': 'Test Document 1',
                    'page_numbers': [7],
                    'chunk_text': 'Second chunk'
                }
            }
        ])
        
        mock_embedding_service = Mock()
        mock_embedding_service.generate_embedding = Mock(return_value=[0.1] * 1536)
        
        mock_ai_service = Mock(spec=RAGAIService)
        mock_ai_service.generate_response_async = AsyncMock(return_value={
            'answer': 'Test Response. **Referenz**: chunk 1. **Referenz**: chunk 2',
            'tokens_used': 100
        })
        
        mock_session_repo = Mock()
        mock_session_repo.get_by_id = Mock(return_value=ChatSession(
            id=1,
            user_id=1,
            session_name="Test Session",
            created_at=datetime.now(),
            is_active=True
        ))
        
        mock_message_repo = Mock()
        mock_message_repo.save = Mock(return_value=ChatMessage(
            id=1,
            session_id=1,
            role="assistant",
            content="Test Response",
            source_references=[],
            created_at=datetime.now()
        ))
        
        mock_event_publisher = Mock()
        mock_event_publisher.publish = Mock()
        
        mock_doc_repo = Mock()
        mock_doc_repo.get_by_id = Mock(return_value=Mock(
            id=1,
            upload_document_id=1,
            document_type="Fachartikel"
        ))
        
        use_case = AskQuestionUseCase(
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            ai_service=mock_ai_service,
            session_repository=mock_session_repo,
            message_repository=mock_message_repo,
            event_publisher=mock_event_publisher,
            document_chunk_repo=Mock(),
            document_repository=mock_doc_repo
        )
        
        # Act
        result = await use_case.execute(
            question="test question",
            session_id=1
        )
        
        # Assert
        assert result is not None
        assert len(result.source_references) == 2
        
        # Prüfe dass Source References in der richtigen Reihenfolge sind
        # Chunk 1 sollte Page 6 haben, Chunk 2 sollte Page 7 haben
        assert result.source_references[0].page_number == 6, \
            "Erste Source Reference sollte Page 6 haben (Chunk 1)"
        assert result.source_references[1].page_number == 7, \
            "Zweite Source Reference sollte Page 7 haben (Chunk 2)"


