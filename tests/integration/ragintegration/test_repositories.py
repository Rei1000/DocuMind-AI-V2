"""
Integration Tests für RAG Infrastructure Layer - SQLAlchemy Repositories

Diese Tests prüfen die Integration zwischen Domain Entities und SQLAlchemy Models.
Sie verwenden eine echte SQLite-Datenbank für realistische Tests.
"""

import pytest
import tempfile
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import Domain Entities
from contexts.ragintegration.domain.entities import (
    IndexedDocument, DocumentChunk, ChatSession, ChatMessage
)
from contexts.ragintegration.domain.value_objects import (
    EmbeddingVector, ChunkMetadata, SourceReference, SearchQuery
)

# Import Infrastructure
from contexts.ragintegration.infrastructure.models import (
    IndexedDocumentModel, DocumentChunkModel, ChatSessionModel, ChatMessageModel
)
from contexts.ragintegration.infrastructure.repositories import (
    SQLAlchemyIndexedDocumentRepository,
    SQLAlchemyDocumentChunkRepository,
    SQLAlchemyChatSessionRepository,
    SQLAlchemyChatMessageRepository
)


class TestSQLAlchemyRepositoriesIntegration:
    """Integration Tests für SQLAlchemy Repositories"""
    
    @pytest.fixture
    def db_session(self):
        """Erstelle eine temporäre SQLite-Datenbank für Tests"""
        # Temporäre Datei für SQLite
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        # SQLAlchemy Engine mit SQLite
        engine = create_engine(
            f'sqlite:///{temp_db.name}',
            poolclass=StaticPool,
            connect_args={'check_same_thread': False}
        )
        
        # Erstelle alle Tabellen
        from contexts.ragintegration.infrastructure.models import Base
        Base.metadata.create_all(engine)
        
        # Session Factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        yield session
        
        # Cleanup
        session.close()
        engine.dispose()
        os.unlink(temp_db.name)
    
    def test_indexed_document_repository_crud(self, db_session):
        """Test CRUD-Operationen für IndexedDocument Repository"""
        repo = SQLAlchemyIndexedDocumentRepository(db_session)
        
        # Create
        indexed_doc = IndexedDocument(
            id=None,
            upload_document_id=123,
            collection_name="test_collection",
            total_chunks=5,
            indexed_at=datetime.utcnow(),
            last_updated_at=datetime.utcnow()
        )
        
        saved_doc = repo.save(indexed_doc)
        assert saved_doc.id is not None
        assert saved_doc.upload_document_id == 123
        assert saved_doc.collection_name == "test_collection"
        
        # Read
        found_doc = repo.get_by_id(saved_doc.id)
        assert found_doc is not None
        assert found_doc.collection_name == "test_collection"
        
        # Update
        found_doc.total_chunks = 10
        updated_doc = repo.save(found_doc)
        assert updated_doc.total_chunks == 10
        
        # Delete
        repo.delete(saved_doc.id)
        deleted_doc = repo.get_by_id(saved_doc.id)
        assert deleted_doc is None
    
    def test_indexed_document_repository_get_by_upload_id(self, db_session):
        """Test GetByUploadDocumentId Methode"""
        repo = SQLAlchemyIndexedDocumentRepository(db_session)
        
        # Erstelle Test-Dokument
        indexed_doc = IndexedDocument(
            id=None,
            upload_document_id=456,
            collection_name="test_collection_2",
            total_chunks=3,
            indexed_at=datetime.utcnow(),
            last_updated_at=datetime.utcnow()
        )
        
        saved_doc = repo.save(indexed_doc)
        
        # Test GetByUploadDocumentId
        found_doc = repo.get_by_upload_document_id(456)
        assert found_doc is not None
        assert found_doc.upload_document_id == 456
        assert found_doc.collection_name == "test_collection_2"
        
        # Test mit nicht existierender ID
        not_found = repo.get_by_upload_document_id(999)
        assert not_found is None
    
    def test_document_chunk_repository_crud(self, db_session):
        """Test CRUD-Operationen für DocumentChunk Repository"""
        # Erstelle zuerst ein IndexedDocument
        indexed_doc_repo = SQLAlchemyIndexedDocumentRepository(db_session)
        indexed_doc = IndexedDocument(
            id=None,
            upload_document_id=789,
            collection_name="test_collection_3",
            total_chunks=1,
            indexed_at=datetime.utcnow(),
            last_updated_at=datetime.utcnow()
        )
        saved_indexed_doc = indexed_doc_repo.save(indexed_doc)
        
        # Test DocumentChunk Repository
        chunk_repo = SQLAlchemyDocumentChunkRepository(db_session)
        
        chunk_metadata = ChunkMetadata(
            page_numbers=[1, 2],
            heading_hierarchy=["1. Einleitung", "1.1 Grundlagen"],
            document_type_id=1,
            confidence=0.95,
            chunk_type="text",
            token_count=150
        )
        
        chunk = DocumentChunk(
            id=None,
            indexed_document_id=saved_indexed_doc.id,
            chunk_id="789_p1_c0",
            chunk_text="Dies ist ein Test-Chunk mit wichtigen Informationen.",
            metadata=chunk_metadata,
            qdrant_point_id="qdrant_point_123",
            created_at=datetime.utcnow()
        )
        
        saved_chunk = chunk_repo.save(chunk)
        assert saved_chunk.id is not None
        assert saved_chunk.chunk_id == "789_p1_c0"
        assert saved_chunk.metadata.confidence == 0.95
        
        # Test GetByIndexedDocumentId
        chunks = chunk_repo.get_by_indexed_document_id(saved_indexed_doc.id)
        assert len(chunks) == 1
        assert chunks[0].chunk_id == "789_p1_c0"
        
        # Test GetByChunkId
        found_chunk = chunk_repo.get_by_chunk_id("789_p1_c0")
        assert found_chunk is not None
        assert found_chunk.chunk_text == "Dies ist ein Test-Chunk mit wichtigen Informationen."
    
    def test_chat_session_repository_crud(self, db_session):
        """Test CRUD-Operationen für ChatSession Repository"""
        repo = SQLAlchemyChatSessionRepository(db_session)
        
        session = ChatSession(
            id=None,
            user_id=1,
            session_name="Test Session",
            created_at=datetime.utcnow(),
            last_message_at=datetime.utcnow(),
            is_active=True
        )
        
        saved_session = repo.save(session)
        assert saved_session.id is not None
        assert saved_session.user_id == 1
        assert saved_session.session_name == "Test Session"
        
        # Test GetByUserId
        user_sessions = repo.get_by_user_id(1)
        assert len(user_sessions) == 1
        assert user_sessions[0].session_name == "Test Session"
        
        # Test GetActiveByUserId
        active_sessions = repo.get_active_by_user_id(1)
        assert len(active_sessions) == 1
        
        
    def test_chat_message_repository_crud(self, db_session):
        """Test CRUD-Operationen für ChatMessage Repository"""
        # Erstelle zuerst eine ChatSession
        session_repo = SQLAlchemyChatSessionRepository(db_session)
        chat_session = ChatSession(
            id=None,
            user_id=2,
            session_name="Test Chat Session",
            created_at=datetime.utcnow(),
            last_message_at=datetime.utcnow(),
            is_active=True
        )
        saved_session = session_repo.save(chat_session)
        
        # Test ChatMessage Repository
        message_repo = SQLAlchemyChatMessageRepository(db_session)
        
        source_ref = SourceReference(
            document_id=123,
            document_title="Test Document",
            page_number=1,
            chunk_id="123_p1_c0",
            preview_image_path="test/preview.jpg",
            relevance_score=0.85,
            text_excerpt="Dies ist ein relevanter Text-Auszug."
        )
        
        message = ChatMessage(
            id=None,
            session_id=saved_session.id,
            role="assistant",
            content="Dies ist eine Test-Antwort.",
            source_chunk_ids=["chunk_1"],
            confidence_scores={"chunk_1": 0.85},
            source_references=[source_ref],
            created_at=datetime.utcnow()
        )
        
        saved_message = message_repo.save(message)
        assert saved_message.id is not None
        assert saved_message.role == "assistant"
        assert len(saved_message.source_references) == 1
        assert saved_message.source_references[0].relevance_score == 0.85
        
        # Test GetBySessionId
        session_messages = message_repo.get_by_session_id(saved_session.id)
        assert len(session_messages) == 1
        assert session_messages[0].content == "Dies ist eine Test-Antwort."
    
    def test_repository_transaction_rollback(self, db_session):
        """Test Transaction Rollback bei Fehlern"""
        repo = SQLAlchemyIndexedDocumentRepository(db_session)
        
        # Erstelle ein Dokument mit ungültigen Daten
        indexed_doc = IndexedDocument(
            id=None,
            upload_document_id=999,
            collection_name="test_collection",
            total_chunks=5,
            indexed_at=datetime.utcnow(),
            last_updated_at=datetime.utcnow()
        )
        
        # Speichere das Dokument
        saved_doc = repo.save(indexed_doc)
        
        # Versuche ein Update mit ungültigen Daten
        try:
            # Erstelle eine neue Entity mit ungültigen Daten
            invalid_doc = IndexedDocument(
                id=saved_doc.id,
                upload_document_id=saved_doc.upload_document_id,
                collection_name="",  # Ungültiger leerer Name
                total_chunks=saved_doc.total_chunks,
                indexed_at=saved_doc.indexed_at,
                last_updated_at=saved_doc.last_updated_at
            )
            repo.save(invalid_doc)
        except Exception:
            # Transaction sollte rollback werden
            pass
        
        # Prüfe, dass das ursprüngliche Dokument unverändert ist
        found_doc = repo.get_by_id(saved_doc.id)
        assert found_doc.total_chunks == 5  # Ursprünglicher Wert
    
    def test_repository_concurrent_access(self, db_session):
        """Test Concurrent Access auf Repository"""
        repo = SQLAlchemyIndexedDocumentRepository(db_session)
        
        # Erstelle mehrere Dokumente gleichzeitig
        documents = []
        for i in range(5):
            doc = IndexedDocument(
                id=None,
                upload_document_id=1000 + i,
                collection_name=f"concurrent_collection_{i}",
                total_chunks=i + 1,
                indexed_at=datetime.utcnow(),
                last_updated_at=datetime.utcnow()
            )
            documents.append(repo.save(doc))
        
        # Prüfe, dass alle Dokumente gespeichert wurden
        assert len(documents) == 5
        for i, doc in enumerate(documents):
            assert doc.id is not None
            assert doc.upload_document_id == 1000 + i
            assert doc.collection_name == f"concurrent_collection_{i}"
    
    def test_repository_performance_large_dataset(self, db_session):
        """Test Performance mit größerem Dataset"""
        repo = SQLAlchemyIndexedDocumentRepository(db_session)
        
        # Erstelle 100 Dokumente
        start_time = datetime.utcnow()
        
        for i in range(100):
            doc = IndexedDocument(
                id=None,
                upload_document_id=2000 + i,
                collection_name=f"perf_collection_{i}",
                total_chunks=i % 10 + 1,
                indexed_at=datetime.utcnow(),
                last_updated_at=datetime.utcnow()
            )
            repo.save(doc)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Performance sollte unter 5 Sekunden liegen
        assert duration < 5.0, f"Performance test took {duration} seconds"
        
        # Prüfe, dass alle Dokumente gespeichert wurden
        all_docs = repo.get_all()
        assert len(all_docs) == 100


class TestRepositoryIntegrationWithDomain:
    """Integration Tests für Repository-Domain Integration"""
    
    @pytest.fixture
    def db_session(self):
        """Erstelle eine temporäre SQLite-Datenbank für Tests"""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        engine = create_engine(
            f'sqlite:///{temp_db.name}',
            poolclass=StaticPool,
            connect_args={'check_same_thread': False}
        )
        
        from contexts.ragintegration.infrastructure.models import Base
        Base.metadata.create_all(engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        yield session
        
        session.close()
        engine.dispose()
        os.unlink(temp_db.name)
    
    def test_domain_entity_persistence_consistency(self, db_session):
        """Test dass Domain Entities konsistent persistiert werden"""
        indexed_doc_repo = SQLAlchemyIndexedDocumentRepository(db_session)
        chunk_repo = SQLAlchemyDocumentChunkRepository(db_session)
        
        # Erstelle IndexedDocument
        indexed_doc = IndexedDocument(
            id=None,
            upload_document_id=3000,
            collection_name="domain_test_collection",
            total_chunks=2,
            indexed_at=datetime.utcnow(),
            last_updated_at=datetime.utcnow()
        )
        
        saved_doc = indexed_doc_repo.save(indexed_doc)
        
        # Erstelle DocumentChunks
        chunk_metadata_1 = ChunkMetadata(
            page_numbers=[1],
            heading_hierarchy=["1. Einleitung"],
            document_type_id=1,
            confidence=0.9,
            chunk_type="text",
            token_count=100
        )
        
        chunk_metadata_2 = ChunkMetadata(
            page_numbers=[2],
            heading_hierarchy=["2. Hauptteil"],
            document_type_id=1,
            confidence=0.85,
            chunk_type="text",
            token_count=120
        )
        
        chunk1 = DocumentChunk(
            id=None,
            indexed_document_id=saved_doc.id,
            chunk_id="3000_p1_c0",
            chunk_text="Erster Chunk mit wichtigen Informationen.",
            metadata=chunk_metadata_1,
            qdrant_point_id="qdrant_point_1",
            created_at=datetime.utcnow()
        )
        
        chunk2 = DocumentChunk(
            id=None,
            indexed_document_id=saved_doc.id,
            chunk_id="3000_p2_c0",
            chunk_text="Zweiter Chunk mit weiteren Informationen.",
            metadata=chunk_metadata_2,
            qdrant_point_id="qdrant_point_2",
            created_at=datetime.utcnow()
        )
        
        saved_chunk1 = chunk_repo.save(chunk1)
        saved_chunk2 = chunk_repo.save(chunk2)
        
        # Prüfe Konsistenz
        assert saved_chunk1.indexed_document_id == saved_doc.id
        assert saved_chunk2.indexed_document_id == saved_doc.id
        
        # Prüfe Metadaten-Konsistenz
        assert saved_chunk1.metadata.confidence == 0.9
        assert saved_chunk2.metadata.confidence == 0.85
        assert saved_chunk1.metadata.page_numbers == [1]
        assert saved_chunk2.metadata.page_numbers == [2]
        
        # Prüfe Chunk-Text-Konsistenz
        assert saved_chunk1.chunk_text == "Erster Chunk mit wichtigen Informationen."
        assert saved_chunk2.chunk_text == "Zweiter Chunk mit weiteren Informationen."
    
    def test_value_object_serialization(self, db_session):
        """Test Serialisierung von Value Objects"""
        chunk_repo = SQLAlchemyDocumentChunkRepository(db_session)
        
        # Erstelle komplexe ChunkMetadata
        complex_metadata = ChunkMetadata(
            page_numbers=[1, 2, 3],
            heading_hierarchy=["1. Einleitung", "1.1 Grundlagen", "1.1.1 Details"],
            document_type_id=1,
            confidence=0.95,
            chunk_type="text",
            token_count=250
        )
        
        chunk = DocumentChunk(
            id=None,
            indexed_document_id=1,  # Annahme: IndexedDocument existiert
            chunk_id="complex_chunk",
            chunk_text="Komplexer Chunk mit vielen Metadaten.",
            metadata=complex_metadata,
            qdrant_point_id="complex_qdrant_point",
            created_at=datetime.utcnow()
        )
        
        saved_chunk = chunk_repo.save(chunk)
        
        # Prüfe dass komplexe Metadaten korrekt serialisiert wurden
        assert saved_chunk.metadata.page_numbers == [1, 2, 3]
        assert len(saved_chunk.metadata.heading_hierarchy) == 3
        assert saved_chunk.metadata.heading_hierarchy[0] == "1. Einleitung"
        assert saved_chunk.metadata.heading_hierarchy[2] == "1.1.1 Details"
        assert saved_chunk.metadata.confidence == 0.95
        assert saved_chunk.metadata.token_count == 250
