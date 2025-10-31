"""
Unit Tests für RAG Integration Application Layer Use Cases.

TDD Approach: Diese Tests werden ZUERST geschrieben, dann die Use Cases implementiert.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from typing import List, Optional

from contexts.ragintegration.application.use_cases import (
    IndexApprovedDocumentUseCase,
    AskQuestionUseCase,
    CreateChatSessionUseCase,
    GetChatHistoryUseCase,
    ReindexDocumentUseCase
)
from contexts.ragintegration.domain.entities import (
    IndexedDocument,
    DocumentChunk,
    ChatSession,
    ChatMessage
)
from contexts.ragintegration.domain.value_objects import (
    ChunkMetadata,
    SourceReference,
    SearchQuery
)
from contexts.ragintegration.domain.events import (
    DocumentIndexedEvent,
    ChatMessageCreatedEvent
)


class TestIndexApprovedDocumentUseCase:
    """Tests für IndexApprovedDocumentUseCase."""
    
    def test_index_approved_document_success(self):
        """Test: Erfolgreiche Indexierung eines Approved Dokuments."""
        # Arrange
        mock_document_repo = Mock()
        mock_chunk_repo = Mock()
        mock_vector_store = Mock()
        mock_embedding_service = Mock()
        mock_chunking_service = Mock()
        mock_event_publisher = Mock()
        
        # Mock Document Data
        mock_document = Mock()
        mock_document.id = 42
        mock_document.status = "Approved"
        mock_document.document_type_id = 1
        
        mock_pages = [
            Mock(id=1, page_number=1, ai_processing_result=Mock(json_response='{"text": "Test content"}')),
            Mock(id=2, page_number=2, ai_processing_result=Mock(json_response='{"text": "More content"}'))
        ]
        
        mock_chunks = [
            DocumentChunk(
                id=None,
                indexed_document_id=1,
                chunk_id="doc_42_chunk_0",
                chunk_text="Test content",
                metadata=ChunkMetadata(
                    page_numbers=[1],
                    heading_hierarchy=[],
                    document_type_id=1,
                    confidence=0.95,
                    chunk_type="text",
                    token_count=50
                ),
                qdrant_point_id="point_1",
                created_at=datetime.utcnow()
            )
        ]
        
        mock_embedding = Mock()
        mock_embedding.vector = tuple([0.1] * 1536)
        
        # Setup Mocks
        mock_document_repo.get_by_id.return_value = mock_document
        mock_chunking_service.create_chunks.return_value = mock_chunks
        mock_embedding_service.generate_embeddings_batch.return_value = [mock_embedding]
        mock_vector_store.index_chunks_batch.return_value = 1
        mock_vector_store.collection_exists.return_value = True
        mock_document_repo.save.return_value = IndexedDocument(
            id=1,
            upload_document_id=42,
            collection_name="qms_documents_sop",
            total_chunks=1,
            indexed_at=datetime.utcnow(),
            last_updated_at=datetime.utcnow()
        )
        
        use_case = IndexApprovedDocumentUseCase(
            document_repository=mock_document_repo,
            chunk_repository=mock_chunk_repo,
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            chunking_service=mock_chunking_service,
            event_publisher=mock_event_publisher
        )
        
        # Act
        result = use_case.execute(document_id=42, user_id=1)
        
        # Assert
        assert result is not None
        assert result.upload_document_id == 42
        assert result.total_chunks == 1
        
        # Verify interactions
        mock_chunking_service.create_chunks.assert_called_once()
        mock_embedding_service.generate_embeddings_batch.assert_called_once()
        mock_vector_store.index_chunks_batch.assert_called_once()
        mock_event_publisher.publish.assert_called_once()
    
    def test_index_document_not_approved(self):
        """Test: Fehler bei nicht-approved Dokument."""
        # Arrange
        mock_document_repo = Mock()
        mock_chunk_repo = Mock()
        mock_vector_store = Mock()
        mock_embedding_service = Mock()
        mock_chunking_service = Mock()
        mock_event_publisher = Mock()
        
        mock_document = Mock()
        mock_document.status = "Draft"  # Nicht approved
        
        mock_document_repo.get_by_id.return_value = mock_document
        
        use_case = IndexApprovedDocumentUseCase(
            document_repository=mock_document_repo,
            chunk_repository=mock_chunk_repo,
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            chunking_service=mock_chunking_service,
            event_publisher=mock_event_publisher
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Document must be approved"):
            use_case.execute(document_id=42, user_id=1)
    
    def test_index_document_not_found(self):
        """Test: Fehler bei nicht gefundenem Dokument."""
        # Arrange
        mock_document_repo = Mock()
        mock_chunk_repo = Mock()
        mock_vector_store = Mock()
        mock_embedding_service = Mock()
        mock_chunking_service = Mock()
        mock_event_publisher = Mock()
        
        mock_document_repo.get_by_id.return_value = None
        
        use_case = IndexApprovedDocumentUseCase(
            document_repository=mock_document_repo,
            chunk_repository=mock_chunk_repo,
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            chunking_service=mock_chunking_service,
            event_publisher=mock_event_publisher
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Document not found"):
            use_case.execute(document_id=42, user_id=1)


class TestAskQuestionUseCase:
    """Tests für AskQuestionUseCase."""
    
    def test_ask_question_success(self):
        """Test: Erfolgreiche Frage-Antwort."""
        # Arrange
        mock_chunk_repo = Mock()
        mock_session_repo = Mock()
        mock_vector_store = Mock()
        mock_embedding_service = Mock()
        mock_multi_query_service = Mock()
        mock_ai_service = Mock()
        mock_event_publisher = Mock()
        
        # Mock Search Results
        mock_search_results = [
            {
                "chunk_id": "doc_42_chunk_0",
                "score": 0.95,
                "payload": {
                    "document_id": 42,
                    "page_number": 1,
                    "chunk_text": "Test answer content"
                }
            }
        ]
        
        mock_embedding = Mock()
        mock_embedding.vector = tuple([0.1] * 1536)
        
        mock_chunk = DocumentChunk(
            id=1,
            indexed_document_id=1,
            chunk_id="doc_42_chunk_0",
            chunk_text="Test answer content",
            metadata=ChunkMetadata(
                page_numbers=[1],
                heading_hierarchy=[],
                document_type_id=1,
                confidence=0.95,
                chunk_type="text",
                token_count=50
            ),
            qdrant_point_id="point_1",
            created_at=datetime.utcnow()
        )
        
        mock_ai_response = "Das ist die Antwort auf Ihre Frage."
        
        # Setup Mocks
        mock_multi_query_service.generate_queries.return_value = ["Test question"]
        mock_embedding_service.generate_embedding.return_value = mock_embedding
        mock_vector_store.search_similar.return_value = mock_search_results
        mock_chunk_repo.get_by_chunk_id.return_value = mock_chunk
        mock_ai_service.generate_response.return_value = mock_ai_response
        mock_session_repo.save_message.return_value = ChatMessage(
            id=1,
            session_id=1,
            role="assistant",
            content=mock_ai_response,
            source_chunk_ids=["doc_42_chunk_0"],
            confidence_scores={"doc_42_chunk_0": 0.95},
            created_at=datetime.utcnow()
        )
        
        use_case = AskQuestionUseCase(
            chunk_repository=mock_chunk_repo,
            session_repository=mock_session_repo,
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            multi_query_service=mock_multi_query_service,
            ai_service=mock_ai_service,
            event_publisher=mock_event_publisher
        )
        
        # Act
        result = use_case.execute(
            question="Test question",
            session_id=1,
            user_id=1,
            model_id="gpt-4o-mini",
            filters={}
        )
        
        # Assert
        assert result is not None
        assert result.content == mock_ai_response
        assert len(result.source_chunk_ids) == 1
        
        # Verify interactions
        mock_multi_query_service.generate_queries.assert_called_once()
        mock_embedding_service.generate_embedding.assert_called_once()
        mock_vector_store.search_similar.assert_called_once()
        mock_ai_service.generate_response.assert_called_once()
        mock_event_publisher.publish.assert_called_once()
    
    def test_ask_question_no_results(self):
        """Test: Keine Suchergebnisse gefunden."""
        # Arrange
        mock_chunk_repo = Mock()
        mock_session_repo = Mock()
        mock_vector_store = Mock()
        mock_embedding_service = Mock()
        mock_multi_query_service = Mock()
        mock_ai_service = Mock()
        mock_event_publisher = Mock()
        
        mock_embedding = Mock()
        mock_embedding.vector = tuple([0.1] * 1536)
        
        # Setup Mocks
        mock_multi_query_service.generate_queries.return_value = ["Test question"]
        mock_embedding_service.generate_embedding.return_value = mock_embedding
        mock_vector_store.search_similar.return_value = []  # Keine Ergebnisse
        
        use_case = AskQuestionUseCase(
            chunk_repository=mock_chunk_repo,
            session_repository=mock_session_repo,
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            multi_query_service=mock_multi_query_service,
            ai_service=mock_ai_service,
            event_publisher=mock_event_publisher
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="No relevant documents found"):
            use_case.execute(
                question="Test question",
                session_id=1,
                user_id=1,
                model_id="gpt-4o-mini",
                filters={}
            )


class TestCreateChatSessionUseCase:
    """Tests für CreateChatSessionUseCase."""
    
    def test_create_chat_session_success(self):
        """Test: Erfolgreiche Erstellung einer Chat-Session."""
        # Arrange
        mock_session_repo = Mock()
        
        mock_session = ChatSession(
            id=1,
            user_id=42,
            session_name="Neue Session",
            created_at=datetime.utcnow(),
            last_message_at=datetime.utcnow(),
            is_active=True
        )
        
        mock_session_repo.save.return_value = mock_session
        
        use_case = CreateChatSessionUseCase(session_repository=mock_session_repo)
        
        # Act
        result = use_case.execute(user_id=42, session_name="Neue Session")
        
        # Assert
        assert result is not None
        assert result.user_id == 42
        assert result.session_name == "Neue Session"
        assert result.is_active is True
        
        mock_session_repo.save.assert_called_once()
    
    def test_create_chat_session_empty_name(self):
        """Test: Fehler bei leerem Session-Namen."""
        # Arrange
        mock_session_repo = Mock()
        
        use_case = CreateChatSessionUseCase(session_repository=mock_session_repo)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Session name cannot be empty"):
            use_case.execute(user_id=42, session_name="")


class TestGetChatHistoryUseCase:
    """Tests für GetChatHistoryUseCase."""
    
    def test_get_chat_history_success(self):
        """Test: Erfolgreiche Abfrage der Chat-Historie."""
        # Arrange
        mock_session_repo = Mock()
        
        mock_messages = [
            ChatMessage(
                id=1,
                session_id=1,
                role="user",
                content="Test question",
                source_chunk_ids=[],
                confidence_scores={},
                created_at=datetime.utcnow()
            ),
            ChatMessage(
                id=2,
                session_id=1,
                role="assistant",
                content="Test answer",
                source_chunk_ids=["chunk_1"],
                confidence_scores={"chunk_1": 0.95},
                created_at=datetime.utcnow()
            )
        ]
        
        mock_session_repo.get_messages_by_session_id.return_value = mock_messages
        
        use_case = GetChatHistoryUseCase(session_repository=mock_session_repo)
        
        # Act
        result = use_case.execute(session_id=1, user_id=42)
        
        # Assert
        assert len(result) == 2
        assert result[0].role == "user"
        assert result[1].role == "assistant"
        
        mock_session_repo.get_messages_by_session_id.assert_called_once_with(1)
    
    def test_get_chat_history_empty(self):
        """Test: Leere Chat-Historie."""
        # Arrange
        mock_session_repo = Mock()
        mock_session_repo.get_messages_by_session_id.return_value = []
        
        use_case = GetChatHistoryUseCase(session_repository=mock_session_repo)
        
        # Act
        result = use_case.execute(session_id=1, user_id=42)
        
        # Assert
        assert len(result) == 0


class TestReindexDocumentUseCase:
    """Tests für ReindexDocumentUseCase."""
    
    def test_reindex_document_success(self):
        """Test: Erfolgreiche Neu-Indexierung."""
        # Arrange
        mock_document_repo = Mock()
        mock_chunk_repo = Mock()
        mock_vector_store = Mock()
        mock_embedding_service = Mock()
        mock_chunking_service = Mock()
        mock_event_publisher = Mock()
        
        mock_indexed_doc = IndexedDocument(
            id=1,
            upload_document_id=42,
            collection_name="qms_documents_sop",
            total_chunks=5,
            indexed_at=datetime.utcnow(),
            last_updated_at=datetime.utcnow()
        )
        
        mock_chunks = [
            DocumentChunk(
                id=i,
                indexed_document_id=1,
                chunk_id=f"doc_42_chunk_{i}",
                chunk_text=f"Content {i}",
                metadata=ChunkMetadata(
                    page_numbers=[1],
                    heading_hierarchy=[],
                    document_type_id=1,
                    confidence=0.95,
                    chunk_type="text",
                    token_count=50
                ),
                qdrant_point_id=f"point_{i}",
                created_at=datetime.utcnow()
            )
            for i in range(5)
        ]
        
        # Setup Mocks
        mock_document_repo.get_by_upload_document_id.return_value = mock_indexed_doc
        mock_chunk_repo.get_by_indexed_document_id.return_value = mock_chunks
        mock_vector_store.delete_chunks_by_document_id.return_value = 5
        mock_chunking_service.create_chunks.return_value = mock_chunks
        mock_embedding_service.generate_embeddings_batch.return_value = [Mock()] * 5
        mock_vector_store.index_chunks_batch.return_value = 5
        mock_document_repo.save.return_value = mock_indexed_doc
        
        use_case = ReindexDocumentUseCase(
            document_repository=mock_document_repo,
            chunk_repository=mock_chunk_repo,
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            chunking_service=mock_chunking_service,
            event_publisher=mock_event_publisher
        )
        
        # Act
        result = use_case.execute(document_id=42)
        
        # Assert
        assert result is not None
        assert result.upload_document_id == 42
        
        # Verify cleanup and reindexing
        mock_vector_store.delete_chunks_by_document_id.assert_called_once()
        mock_chunking_service.create_chunks.assert_called_once()
        mock_vector_store.index_chunks_batch.assert_called_once()
        mock_event_publisher.publish.assert_called_once()
    
    def test_reindex_document_not_found(self):
        """Test: Fehler bei nicht gefundenem indexierten Dokument."""
        # Arrange
        mock_document_repo = Mock()
        mock_chunk_repo = Mock()
        mock_vector_store = Mock()
        mock_embedding_service = Mock()
        mock_chunking_service = Mock()
        mock_event_publisher = Mock()
        
        mock_document_repo.get_by_upload_document_id.return_value = None
        
        use_case = ReindexDocumentUseCase(
            document_repository=mock_document_repo,
            chunk_repository=mock_chunk_repo,
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            chunking_service=mock_chunking_service,
            event_publisher=mock_event_publisher
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Indexed document not found"):
            use_case.execute(document_id=42)
