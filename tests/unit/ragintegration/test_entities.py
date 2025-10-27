"""
Unit Tests für RAG Integration Entities.

TDD Approach: Diese Tests werden ZUERST geschrieben, dann die Entities implementiert.
"""

import pytest
from datetime import datetime
from contexts.ragintegration.domain.entities import (
    IndexedDocument,
    DocumentChunk,
    ChatSession,
    ChatMessage
)
from contexts.ragintegration.domain.value_objects import (
    ChunkMetadata,
    SourceReference
)


class TestIndexedDocument:
    """Tests für IndexedDocument Entity."""
    
    def test_create_valid_indexed_document(self):
        """Test: Erstelle gültiges IndexedDocument."""
        doc = IndexedDocument(
            id=1,
            upload_document_id=42,
            collection_name="qms_documents_sop",
            total_chunks=15,
            indexed_at=datetime.utcnow(),
            last_updated_at=datetime.utcnow()
        )
        
        assert doc.id == 1
        assert doc.upload_document_id == 42
        assert doc.collection_name == "qms_documents_sop"
        assert doc.total_chunks == 15
        assert isinstance(doc.indexed_at, datetime)
    
    def test_indexed_document_requires_positive_upload_id(self):
        """Test: upload_document_id muss positiv sein."""
        with pytest.raises(ValueError, match="upload_document_id must be positive"):
            IndexedDocument(
                id=1,
                upload_document_id=-1,
                collection_name="qms_documents_sop",
                total_chunks=15,
                indexed_at=datetime.utcnow(),
                last_updated_at=datetime.utcnow()
            )
    
    def test_indexed_document_requires_positive_total_chunks(self):
        """Test: total_chunks muss positiv sein."""
        with pytest.raises(ValueError, match="total_chunks must be positive"):
            IndexedDocument(
                id=1,
                upload_document_id=42,
                collection_name="qms_documents_sop",
                total_chunks=0,
                indexed_at=datetime.utcnow(),
                last_updated_at=datetime.utcnow()
            )
    
    def test_indexed_document_collection_name_not_empty(self):
        """Test: collection_name darf nicht leer sein."""
        with pytest.raises(ValueError, match="collection_name cannot be empty"):
            IndexedDocument(
                id=1,
                upload_document_id=42,
                collection_name="",
                total_chunks=15,
                indexed_at=datetime.utcnow(),
                last_updated_at=datetime.utcnow()
            )


class TestDocumentChunk:
    """Tests für DocumentChunk Entity."""
    
    def test_create_valid_document_chunk(self):
        """Test: Erstelle gültigen DocumentChunk."""
        metadata = ChunkMetadata(
            page_numbers=[1, 2],
            heading_hierarchy=["1. Arbeitsanweisung", "1.1 Vorbereitung"],
            document_type_id=1,
            confidence=0.95,
            chunk_type="text",
            token_count=150
        )
        
        chunk = DocumentChunk(
            id=1,
            indexed_document_id=1,
            chunk_id="doc_42_chunk_0",
            chunk_text="Dies ist ein Test-Chunk mit wichtigem Inhalt.",
            metadata=metadata,
            qdrant_point_id="uuid-12345",
            created_at=datetime.utcnow()
        )
        
        assert chunk.id == 1
        assert chunk.indexed_document_id == 1
        assert chunk.chunk_id == "doc_42_chunk_0"
        assert len(chunk.chunk_text) > 0
        assert chunk.metadata.page_numbers == [1, 2]
        assert chunk.metadata.confidence == 0.95
    
    def test_document_chunk_requires_positive_indexed_document_id(self):
        """Test: indexed_document_id muss positiv sein."""
        metadata = ChunkMetadata(
            page_numbers=[1],
            heading_hierarchy=[],
            document_type_id=1,
            confidence=0.95,
            chunk_type="text",
            token_count=100
        )
        
        with pytest.raises(ValueError, match="indexed_document_id must be positive"):
            DocumentChunk(
                id=1,
                indexed_document_id=-1,
                chunk_id="doc_42_chunk_0",
                chunk_text="Test",
                metadata=metadata,
                qdrant_point_id="uuid-12345",
                created_at=datetime.utcnow()
            )
    
    def test_document_chunk_text_not_empty(self):
        """Test: chunk_text darf nicht leer sein."""
        metadata = ChunkMetadata(
            page_numbers=[1],
            heading_hierarchy=[],
            document_type_id=1,
            confidence=0.95,
            chunk_type="text",
            token_count=100
        )
        
        with pytest.raises(ValueError, match="chunk_text cannot be empty"):
            DocumentChunk(
                id=1,
                indexed_document_id=1,
                chunk_id="doc_42_chunk_0",
                chunk_text="",
                metadata=metadata,
                qdrant_point_id="uuid-12345",
                created_at=datetime.utcnow()
            )
    
    def test_document_chunk_get_page_count(self):
        """Test: Returniere Anzahl Seiten aus Metadata."""
        metadata = ChunkMetadata(
            page_numbers=[1, 2, 3],
            heading_hierarchy=[],
            document_type_id=1,
            confidence=0.95,
            chunk_type="text",
            token_count=100
        )
        
        chunk = DocumentChunk(
            id=1,
            indexed_document_id=1,
            chunk_id="doc_42_chunk_0",
            chunk_text="Test",
            metadata=metadata,
            qdrant_point_id="uuid-12345",
            created_at=datetime.utcnow()
        )
        
        assert chunk.get_page_count() == 3
    
    def test_document_chunk_is_multi_page(self):
        """Test: Prüfe ob Chunk über mehrere Seiten geht."""
        metadata_single = ChunkMetadata(
            page_numbers=[1],
            heading_hierarchy=[],
            document_type_id=1,
            confidence=0.95,
            chunk_type="text",
            token_count=100
        )
        
        metadata_multi = ChunkMetadata(
            page_numbers=[1, 2],
            heading_hierarchy=[],
            document_type_id=1,
            confidence=0.95,
            chunk_type="text",
            token_count=100
        )
        
        chunk_single = DocumentChunk(
            id=1,
            indexed_document_id=1,
            chunk_id="doc_42_chunk_0",
            chunk_text="Test",
            metadata=metadata_single,
            qdrant_point_id="uuid-12345",
            created_at=datetime.utcnow()
        )
        
        chunk_multi = DocumentChunk(
            id=2,
            indexed_document_id=1,
            chunk_id="doc_42_chunk_1",
            chunk_text="Test",
            metadata=metadata_multi,
            qdrant_point_id="uuid-67890",
            created_at=datetime.utcnow()
        )
        
        assert chunk_single.is_multi_page() is False
        assert chunk_multi.is_multi_page() is True


class TestChatSession:
    """Tests für ChatSession Entity."""
    
    def test_create_valid_chat_session(self):
        """Test: Erstelle gültige ChatSession."""
        session = ChatSession(
            id=1,
            user_id=42,
            session_name="Fragen zu SOPs",
            created_at=datetime.utcnow(),
            last_message_at=datetime.utcnow(),
            is_active=True
        )
        
        assert session.id == 1
        assert session.user_id == 42
        assert session.session_name == "Fragen zu SOPs"
        assert session.is_active is True
    
    def test_chat_session_requires_positive_user_id(self):
        """Test: user_id muss positiv sein."""
        with pytest.raises(ValueError, match="user_id must be positive"):
            ChatSession(
                id=1,
                user_id=-1,
                session_name="Test",
                created_at=datetime.utcnow(),
                last_message_at=datetime.utcnow(),
                is_active=True
            )
    
    def test_chat_session_name_not_empty(self):
        """Test: session_name darf nicht leer sein."""
        with pytest.raises(ValueError, match="session_name cannot be empty"):
            ChatSession(
                id=1,
                user_id=42,
                session_name="",
                created_at=datetime.utcnow(),
                last_message_at=datetime.utcnow(),
                is_active=True
            )
    
    def test_chat_session_deactivate(self):
        """Test: Deaktiviere Session (Business Logic)."""
        session = ChatSession(
            id=1,
            user_id=42,
            session_name="Test",
            created_at=datetime.utcnow(),
            last_message_at=datetime.utcnow(),
            is_active=True
        )
        
        session.deactivate()
        assert session.is_active is False
    
    def test_chat_session_activate(self):
        """Test: Aktiviere Session (Business Logic)."""
        session = ChatSession(
            id=1,
            user_id=42,
            session_name="Test",
            created_at=datetime.utcnow(),
            last_message_at=datetime.utcnow(),
            is_active=False
        )
        
        session.activate()
        assert session.is_active is True


class TestChatMessage:
    """Tests für ChatMessage Entity."""
    
    def test_create_valid_user_message(self):
        """Test: Erstelle gültige User-Nachricht."""
        message = ChatMessage(
            id=1,
            session_id=1,
            role="user",
            content="Welche Sicherheitshinweise gibt es?",
            source_chunk_ids=[],
            confidence_scores={},
            created_at=datetime.utcnow()
        )
        
        assert message.id == 1
        assert message.session_id == 1
        assert message.role == "user"
        assert len(message.content) > 0
        assert message.is_user_message() is True
        assert message.is_assistant_message() is False
    
    def test_create_valid_assistant_message_with_sources(self):
        """Test: Erstelle gültige Assistant-Nachricht mit Quellen."""
        source_refs = [
            SourceReference(
                document_id=42,
                document_title="SOP-001",
                page_number=3,
                chunk_id="doc_42_chunk_5",
                preview_image_path="uploads/2025/01/preview.jpg",
                relevance_score=0.95,
                text_excerpt="Wichtige Sicherheitshinweise..."
            )
        ]
        
        message = ChatMessage(
            id=2,
            session_id=1,
            role="assistant",
            content="Es gibt folgende Sicherheitshinweise...",
            source_chunk_ids=["doc_42_chunk_5"],
            confidence_scores={"doc_42_chunk_5": 0.95},
            created_at=datetime.utcnow(),
            source_references=source_refs
        )
        
        assert message.role == "assistant"
        assert message.is_assistant_message() is True
        assert message.has_sources() is True
        assert len(message.get_source_references()) == 1
        assert message.get_confidence_for_chunk("doc_42_chunk_5") == 0.95
    
    def test_chat_message_requires_positive_session_id(self):
        """Test: session_id muss positiv sein."""
        with pytest.raises(ValueError, match="session_id must be positive"):
            ChatMessage(
                id=1,
                session_id=-1,
                role="user",
                content="Test",
                source_chunk_ids=[],
                confidence_scores={},
                created_at=datetime.utcnow()
            )
    
    def test_chat_message_role_must_be_valid(self):
        """Test: role muss 'user' oder 'assistant' sein."""
        with pytest.raises(ValueError, match="role must be 'user' or 'assistant'"):
            ChatMessage(
                id=1,
                session_id=1,
                role="invalid",
                content="Test",
                source_chunk_ids=[],
                confidence_scores={},
                created_at=datetime.utcnow()
            )
    
    def test_chat_message_content_not_empty(self):
        """Test: content darf nicht leer sein."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            ChatMessage(
                id=1,
                session_id=1,
                role="user",
                content="",
                source_chunk_ids=[],
                confidence_scores={},
                created_at=datetime.utcnow()
            )

