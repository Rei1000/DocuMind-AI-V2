"""
Unit Tests für RAG Integration Domain Events.

TDD Approach: Diese Tests werden ZUERST geschrieben, dann die Events implementiert.
"""

import pytest
from datetime import datetime
from contexts.ragintegration.domain.events import (
    DocumentIndexedEvent,
    ChatMessageCreatedEvent,
    ChunkCreatedEvent
)


class TestDocumentIndexedEvent:
    """Tests für DocumentIndexedEvent."""
    
    def test_create_valid_document_indexed_event(self):
        """Test: Erstelle gültiges DocumentIndexedEvent."""
        event = DocumentIndexedEvent(
            indexed_document_id=1,
            upload_document_id=42,
            total_chunks=15,
            timestamp=datetime.utcnow()
        )
        
        assert event.indexed_document_id == 1
        assert event.upload_document_id == 42
        assert event.total_chunks == 15
        assert isinstance(event.timestamp, datetime)
    
    def test_document_indexed_event_requires_positive_indexed_document_id(self):
        """Test: indexed_document_id muss positiv sein."""
        with pytest.raises(ValueError, match="indexed_document_id must be positive"):
            DocumentIndexedEvent(
                indexed_document_id=-1,
                upload_document_id=42,
                total_chunks=15,
                timestamp=datetime.utcnow()
            )
    
    def test_document_indexed_event_requires_positive_upload_document_id(self):
        """Test: upload_document_id muss positiv sein."""
        with pytest.raises(ValueError, match="upload_document_id must be positive"):
            DocumentIndexedEvent(
                indexed_document_id=1,
                upload_document_id=-1,
                total_chunks=15,
                timestamp=datetime.utcnow()
            )
    
    def test_document_indexed_event_requires_positive_total_chunks(self):
        """Test: total_chunks muss positiv sein."""
        with pytest.raises(ValueError, match="total_chunks must be positive"):
            DocumentIndexedEvent(
                indexed_document_id=1,
                upload_document_id=42,
                total_chunks=0,
                timestamp=datetime.utcnow()
            )
    
    def test_document_indexed_event_get_event_type(self):
        """Test: Returniere Event-Typ."""
        event = DocumentIndexedEvent(
            indexed_document_id=1,
            upload_document_id=42,
            total_chunks=15,
            timestamp=datetime.utcnow()
        )
        
        assert event.get_event_type() == "DocumentIndexed"


class TestChatMessageCreatedEvent:
    """Tests für ChatMessageCreatedEvent."""
    
    def test_create_valid_chat_message_created_event(self):
        """Test: Erstelle gültiges ChatMessageCreatedEvent."""
        event = ChatMessageCreatedEvent(
            message_id=1,
            session_id=2,
            user_id=42,
            role="assistant",
            content="Das ist eine Antwort.",
            timestamp=datetime.utcnow()
        )
        
        assert event.message_id == 1
        assert event.session_id == 2
        assert event.user_id == 42
        assert event.role == "assistant"
        assert event.content == "Das ist eine Antwort."
        assert isinstance(event.timestamp, datetime)
    
    def test_chat_message_created_event_requires_positive_message_id(self):
        """Test: message_id muss positiv sein."""
        with pytest.raises(ValueError, match="message_id must be positive"):
            ChatMessageCreatedEvent(
                message_id=-1,
                session_id=2,
                user_id=42,
                role="assistant",
                content="Test",
                timestamp=datetime.utcnow()
            )
    
    def test_chat_message_created_event_requires_positive_session_id(self):
        """Test: session_id muss positiv sein."""
        with pytest.raises(ValueError, match="session_id must be positive"):
            ChatMessageCreatedEvent(
                message_id=1,
                session_id=-1,
                user_id=42,
                role="assistant",
                content="Test",
                timestamp=datetime.utcnow()
            )
    
    def test_chat_message_created_event_requires_positive_user_id(self):
        """Test: user_id muss positiv sein."""
        with pytest.raises(ValueError, match="user_id must be positive"):
            ChatMessageCreatedEvent(
                message_id=1,
                session_id=2,
                user_id=-1,
                role="assistant",
                content="Test",
                timestamp=datetime.utcnow()
            )
    
    def test_chat_message_created_event_role_must_be_valid(self):
        """Test: role muss 'user' oder 'assistant' sein."""
        with pytest.raises(ValueError, match="role must be one of"):
            ChatMessageCreatedEvent(
                message_id=1,
                session_id=2,
                user_id=42,
                role="invalid",
                content="Test",
                timestamp=datetime.utcnow()
            )
    
    def test_chat_message_created_event_content_not_empty(self):
        """Test: content darf nicht leer sein."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            ChatMessageCreatedEvent(
                message_id=1,
                session_id=2,
                user_id=42,
                role="assistant",
                content="",
                timestamp=datetime.utcnow()
            )
    
    def test_chat_message_created_event_get_event_type(self):
        """Test: Returniere Event-Typ."""
        event = ChatMessageCreatedEvent(
            message_id=1,
            session_id=2,
            user_id=42,
            role="assistant",
            content="Test",
            timestamp=datetime.utcnow()
        )
        
        assert event.get_event_type() == "ChatMessageCreated"


class TestChunkCreatedEvent:
    """Tests für ChunkCreatedEvent."""
    
    def test_create_valid_chunk_created_event(self):
        """Test: Erstelle gültiges ChunkCreatedEvent."""
        event = ChunkCreatedEvent(
            chunk_id="doc_42_chunk_5",
            indexed_document_id=1,
            page_number=3,
            paragraph_index=2,
            timestamp=datetime.utcnow()
        )
        
        assert event.chunk_id == "doc_42_chunk_5"
        assert event.indexed_document_id == 1
        assert event.page_number == 3
        assert event.paragraph_index == 2
        assert isinstance(event.timestamp, datetime)
    
    def test_chunk_created_event_chunk_id_not_empty(self):
        """Test: chunk_id darf nicht leer sein."""
        with pytest.raises(ValueError, match="chunk_id cannot be empty"):
            ChunkCreatedEvent(
                chunk_id="",
                indexed_document_id=1,
                page_number=3,
                paragraph_index=2,
                timestamp=datetime.utcnow()
            )
    
    def test_chunk_created_event_requires_positive_indexed_document_id(self):
        """Test: indexed_document_id muss positiv sein."""
        with pytest.raises(ValueError, match="indexed_document_id must be positive"):
            ChunkCreatedEvent(
                chunk_id="doc_42_chunk_5",
                indexed_document_id=-1,
                page_number=3,
                paragraph_index=2,
                timestamp=datetime.utcnow()
            )
    
    def test_chunk_created_event_requires_positive_page_number(self):
        """Test: page_number muss positiv sein."""
        with pytest.raises(ValueError, match="page_number must be positive"):
            ChunkCreatedEvent(
                chunk_id="doc_42_chunk_5",
                indexed_document_id=1,
                page_number=0,
                paragraph_index=2,
                timestamp=datetime.utcnow()
            )
    
    def test_chunk_created_event_requires_non_negative_paragraph_index(self):
        """Test: paragraph_index muss nicht-negativ sein."""
        with pytest.raises(ValueError, match="paragraph_index must be non-negative"):
            ChunkCreatedEvent(
                chunk_id="doc_42_chunk_5",
                indexed_document_id=1,
                page_number=3,
                paragraph_index=-1,
                timestamp=datetime.utcnow()
            )
    
    def test_chunk_created_event_get_event_type(self):
        """Test: Returniere Event-Typ."""
        event = ChunkCreatedEvent(
            chunk_id="doc_42_chunk_5",
            indexed_document_id=1,
            page_number=3,
            paragraph_index=2,
            timestamp=datetime.utcnow()
        )
        
        assert event.get_event_type() == "ChunkCreated"
