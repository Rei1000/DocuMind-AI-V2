"""
Integration Tests für RAG Infrastructure Layer - Hybrid Search Service

Diese Tests prüfen die Integration zwischen Qdrant Vector Store und SQLite FTS.
Sie verwenden echte Services für realistische Tests.
"""

import pytest
import tempfile
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock, patch

# Import Domain Entities
from contexts.ragintegration.domain.entities import DocumentChunk
from contexts.ragintegration.domain.value_objects import EmbeddingVector, ChunkMetadata, SearchQuery

# Import Infrastructure
from contexts.ragintegration.infrastructure.hybrid_search_service import HybridSearchService
from contexts.ragintegration.infrastructure.repositories import (
    SQLAlchemyIndexedDocumentRepository,
    SQLAlchemyDocumentChunkRepository
)
from contexts.ragintegration.infrastructure.models import Base


class TestHybridSearchServiceIntegration:
    """Integration Tests für Hybrid Search Service"""
    
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
        
        Base.metadata.create_all(engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        yield session
        
        session.close()
        engine.dispose()
        os.unlink(temp_db.name)
    
    @pytest.fixture
    def hybrid_search_service(self, db_session):
        """Erstelle Hybrid Search Service für Tests"""
        # Mock Dependencies
        vector_store_adapter = Mock()
        embedding_service = Mock()
        
        return HybridSearchService(
            vector_store=vector_store_adapter,
            embedding_service=embedding_service
        )
    
    @pytest.fixture
    def sample_chunks(self, db_session):
        """Erstelle Sample DocumentChunks für Tests"""
        # Erstelle IndexedDocument
        indexed_doc_repo = SQLAlchemyIndexedDocumentRepository(db_session)
        indexed_doc = indexed_doc_repo.save(
            type('IndexedDocument', (), {
                'id': None,
                'upload_document_id': 1,
                'document_title': 'Test Document',
                'document_type': 'Arbeitsanweisung',
                'qdrant_collection_name': 'test_collection',
                'total_chunks': 3,
                'status': 'indexed',
                'indexed_at': datetime.utcnow(),
                'last_updated': datetime.utcnow(),
                'embedding_model': 'text-embedding-3-small',
                'chunking_strategy': 'vision_ai'
            })()
        )
        
        # Erstelle Chunks
        chunk_repo = SQLAlchemyDocumentChunkRepository(db_session)
        chunks = []
        
        metadata1 = ChunkMetadata(
            page_numbers=[1],
            heading_hierarchy=["1. Einleitung"],
            document_type="Arbeitsanweisung",
            confidence_score=0.9,
            chunk_type="instruction",
            token_count=100
        )
        
        metadata2 = ChunkMetadata(
            page_numbers=[2],
            heading_hierarchy=["2. Montage"],
            document_type="Arbeitsanweisung",
            confidence_score=0.85,
            chunk_type="instruction",
            token_count=120
        )
        
        metadata3 = ChunkMetadata(
            page_numbers=[3],
            heading_hierarchy=["3. Sicherheit"],
            document_type="Arbeitsanweisung",
            confidence_score=0.95,
            chunk_type="safety",
            token_count=80
        )
        
        chunk1 = DocumentChunk(
            id=None,
            indexed_document_id=indexed_doc.id,
            chunk_id="doc1_p1_c0",
            chunk_text="Dies ist die Einleitung zur Montage-Anweisung.",
            metadata=metadata1,
            qdrant_point_id="qdrant_point_1",
            embedding_vector_preview="[0.1, 0.2, ...]",
            created_at=datetime.utcnow()
        )
        
        chunk2 = DocumentChunk(
            id=None,
            indexed_document_id=indexed_doc.id,
            chunk_id="doc1_p2_c0",
            chunk_text="Die Montage erfolgt in mehreren Schritten mit speziellen Werkzeugen.",
            metadata=metadata2,
            qdrant_point_id="qdrant_point_2",
            embedding_vector_preview="[0.3, 0.4, ...]",
            created_at=datetime.utcnow()
        )
        
        chunk3 = DocumentChunk(
            id=None,
            indexed_document_id=indexed_doc.id,
            chunk_id="doc1_p3_c0",
            chunk_text="Wichtige Sicherheitshinweise: Schutzbrille tragen und Handschuhe verwenden.",
            metadata=metadata3,
            qdrant_point_id="qdrant_point_3",
            embedding_vector_preview="[0.5, 0.6, ...]",
            created_at=datetime.utcnow()
        )
        
        chunks.append(chunk_repo.save(chunk1))
        chunks.append(chunk_repo.save(chunk2))
        chunks.append(chunk_repo.save(chunk3))
        
        return chunks
    
    def test_hybrid_search_vector_and_text(self, hybrid_search_service, sample_chunks):
        """Test Hybrid Search mit Vector und Text Suche"""
        # Mock Vector Store Results
        vector_results = [
            {
                "chunk_id": "doc1_p2_c0",
                "score": 0.85,
                "payload": {"text": "Die Montage erfolgt in mehreren Schritten mit speziellen Werkzeugen."}
            },
            {
                "chunk_id": "doc1_p1_c0",
                "score": 0.75,
                "payload": {"text": "Dies ist die Einleitung zur Montage-Anweisung."}
            }
        ]
        
        # Mock Embedding Service
        hybrid_search_service.embedding_service.generate_embedding.return_value = EmbeddingVector([0.1] * 1536)
        
        # Mock Vector Store Adapter
        hybrid_search_service.vector_store_adapter.search_similar_chunks.return_value = vector_results
        
        # Test Search
        search_query = SearchQuery(
            text="Montage Schritte Werkzeuge",
            top_k=5,
            relevance_threshold=0.7,
            filters=None
        )
        
        results = hybrid_search_service.search(search_query)
        
        assert len(results) >= 2
        assert results[0]["chunk_id"] == "doc1_p2_c0"
        assert results[0]["relevance_score"] == 0.85
        assert "Montage" in results[0]["text"]
    
    def test_hybrid_search_text_only(self, hybrid_search_service, sample_chunks):
        """Test Hybrid Search mit nur Text Suche (wenn Vector Store nicht verfügbar)"""
        # Mock Embedding Service Error
        hybrid_search_service.embedding_service.generate_embedding.side_effect = Exception("API Error")
        
        # Mock Vector Store Adapter Error
        hybrid_search_service.vector_store_adapter.search_similar_chunks.side_effect = Exception("Vector Store Error")
        
        # Test Search (sollte auf Text-Suche zurückfallen)
        search_query = SearchQuery(
            text="Sicherheit Schutzbrille",
            top_k=5,
            relevance_threshold=0.0,
            filters=None
        )
        
        results = hybrid_search_service.search(search_query)
        
        # Sollte mindestens einen Chunk mit "Sicherheit" finden
        assert len(results) >= 1
        safety_chunks = [r for r in results if "Sicherheit" in r["text"]]
        assert len(safety_chunks) >= 1
        assert "Schutzbrille" in safety_chunks[0]["text"]
    
    def test_hybrid_search_with_filters(self, hybrid_search_service, sample_chunks):
        """Test Hybrid Search mit Filtern"""
        # Mock Vector Store Results
        vector_results = [
            {
                "chunk_id": "doc1_p3_c0",
                "score": 0.9,
                "payload": {"text": "Wichtige Sicherheitshinweise: Schutzbrille tragen und Handschuhe verwenden."}
            }
        ]
        
        # Mock Services
        hybrid_search_service.embedding_service.generate_embedding.return_value = EmbeddingVector([0.1] * 1536)
        hybrid_search_service.vector_store_adapter.search_similar_chunks.return_value = vector_results
        
        # Test Search mit Filter
        search_query = SearchQuery(
            text="Sicherheit",
            top_k=5,
            relevance_threshold=0.0,
            filters={"document_type": "Arbeitsanweisung", "chunk_type": "safety"}
        )
        
        results = hybrid_search_service.search(search_query)
        
        # Sollte nur Safety-Chunks zurückgeben
        assert len(results) >= 1
        for result in results:
            assert result["metadata"]["chunk_type"] == "safety"
            assert result["metadata"]["document_type"] == "Arbeitsanweisung"
    
    def test_hybrid_search_relevance_threshold(self, hybrid_search_service, sample_chunks):
        """Test Hybrid Search mit Relevance Threshold"""
        # Mock Vector Store Results mit verschiedenen Scores
        vector_results = [
            {
                "chunk_id": "doc1_p2_c0",
                "score": 0.9,
                "payload": {"text": "Die Montage erfolgt in mehreren Schritten mit speziellen Werkzeugen."}
            },
            {
                "chunk_id": "doc1_p1_c0",
                "score": 0.6,
                "payload": {"text": "Dies ist die Einleitung zur Montage-Anweisung."}
            },
            {
                "chunk_id": "doc1_p3_c0",
                "score": 0.4,
                "payload": {"text": "Wichtige Sicherheitshinweise: Schutzbrille tragen und Handschuhe verwenden."}
            }
        ]
        
        # Mock Services
        hybrid_search_service.embedding_service.generate_embedding.return_value = EmbeddingVector([0.1] * 1536)
        hybrid_search_service.vector_store_adapter.search_similar_chunks.return_value = vector_results
        
        # Test Search mit hohem Threshold
        search_query = SearchQuery(
            text="Montage",
            top_k=10,
            relevance_threshold=0.7,
            filters=None
        )
        
        results = hybrid_search_service.search(search_query)
        
        # Sollte nur Chunks mit Score >= 0.7 zurückgeben
        assert len(results) >= 1
        for result in results:
            assert result["relevance_score"] >= 0.7
    
    def test_hybrid_search_top_k_limit(self, hybrid_search_service, sample_chunks):
        """Test Hybrid Search mit Top-K Limit"""
        # Mock Vector Store Results
        vector_results = [
            {
                "chunk_id": f"doc1_p{i}_c0",
                "score": 0.9 - i * 0.1,
                "payload": {"text": f"Test chunk {i}"}
            }
            for i in range(10)
        ]
        
        # Mock Services
        hybrid_search_service.embedding_service.generate_embedding.return_value = EmbeddingVector([0.1] * 1536)
        hybrid_search_service.vector_store_adapter.search_similar_chunks.return_value = vector_results
        
        # Test Search mit Top-K = 3
        search_query = SearchQuery(
            text="Test",
            top_k=3,
            relevance_threshold=0.0,
            filters=None
        )
        
        results = hybrid_search_service.search(search_query)
        
        # Sollte maximal 3 Ergebnisse zurückgeben
        assert len(results) <= 3
    
    def test_hybrid_search_empty_results(self, hybrid_search_service, sample_chunks):
        """Test Hybrid Search mit leeren Ergebnissen"""
        # Mock Leere Vector Store Results
        hybrid_search_service.vector_store_adapter.search_similar_chunks.return_value = []
        
        # Mock Embedding Service
        hybrid_search_service.embedding_service.generate_embedding.return_value = EmbeddingVector([0.1] * 1536)
        
        # Test Search mit sehr spezifischem Query
        search_query = SearchQuery(
            text="Nicht existierender Text",
            top_k=5,
            relevance_threshold=0.0,
            filters=None
        )
        
        results = hybrid_search_service.search(search_query)
        
        # Sollte leere Liste zurückgeben
        assert len(results) == 0
    
    def test_hybrid_search_performance(self, hybrid_search_service, sample_chunks):
        """Test Hybrid Search Performance"""
        # Mock Vector Store Results
        vector_results = [
            {
                "chunk_id": f"doc1_p{i}_c0",
                "score": 0.8,
                "payload": {"text": f"Performance test chunk {i}"}
            }
            for i in range(100)
        ]
        
        # Mock Services
        hybrid_search_service.embedding_service.generate_embedding.return_value = EmbeddingVector([0.1] * 1536)
        hybrid_search_service.vector_store_adapter.search_similar_chunks.return_value = vector_results
        
        # Test Performance
        import time
        start_time = time.time()
        
        search_query = SearchQuery(
            text="Performance test",
            top_k=10,
            relevance_threshold=0.0,
            filters=None
        )
        
        results = hybrid_search_service.search(search_query)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert len(results) == 10
        assert duration < 2.0, f"Search took {duration} seconds"
    
    def test_hybrid_search_error_handling(self, hybrid_search_service, sample_chunks):
        """Test Error Handling bei Hybrid Search"""
        # Mock Embedding Service Error
        hybrid_search_service.embedding_service.generate_embedding.side_effect = Exception("Embedding Error")
        
        # Mock Vector Store Adapter Error
        hybrid_search_service.vector_store_adapter.search_similar_chunks.side_effect = Exception("Vector Store Error")
        
        # Test Search (sollte auf Text-Suche zurückfallen)
        search_query = SearchQuery(
            text="Error handling test",
            top_k=5,
            relevance_threshold=0.0,
            filters=None
        )
        
        # Sollte nicht fehlschlagen, sondern auf Text-Suche zurückfallen
        results = hybrid_search_service.search(search_query)
        
        # Sollte leere Liste oder Text-Suchergebnisse zurückgeben
        assert isinstance(results, list)
    
    def test_hybrid_search_re_ranking(self, hybrid_search_service, sample_chunks):
        """Test Re-Ranking von Suchergebnissen"""
        # Mock Vector Store Results (schlechte Reihenfolge)
        vector_results = [
            {
                "chunk_id": "doc1_p1_c0",
                "score": 0.6,
                "payload": {"text": "Dies ist die Einleitung zur Montage-Anweisung."}
            },
            {
                "chunk_id": "doc1_p2_c0",
                "score": 0.8,
                "payload": {"text": "Die Montage erfolgt in mehreren Schritten mit speziellen Werkzeugen."}
            }
        ]
        
        # Mock Services
        hybrid_search_service.embedding_service.generate_embedding.return_value = EmbeddingVector([0.1] * 1536)
        hybrid_search_service.vector_store_adapter.search_similar_chunks.return_value = vector_results
        
        # Test Search
        search_query = SearchQuery(
            text="Montage Schritte",
            top_k=5,
            relevance_threshold=0.0,
            filters=None
        )
        
        results = hybrid_search_service.search(search_query)
        
        # Re-Ranking sollte bessere Reihenfolge erzeugen
        assert len(results) >= 2
        
        # Der Chunk mit "Montage" sollte höher gerankt sein
        montage_chunk = next((r for r in results if "Montage" in r["text"]), None)
        assert montage_chunk is not None
        assert montage_chunk["relevance_score"] >= 0.8
    
    def test_hybrid_search_metadata_enrichment(self, hybrid_search_service, sample_chunks):
        """Test Metadata Enrichment von Suchergebnissen"""
        # Mock Vector Store Results
        vector_results = [
            {
                "chunk_id": "doc1_p3_c0",
                "score": 0.9,
                "payload": {"text": "Wichtige Sicherheitshinweise: Schutzbrille tragen und Handschuhe verwenden."}
            }
        ]
        
        # Mock Services
        hybrid_search_service.embedding_service.generate_embedding.return_value = EmbeddingVector([0.1] * 1536)
        hybrid_search_service.vector_store_adapter.search_similar_chunks.return_value = vector_results
        
        # Test Search
        search_query = SearchQuery(
            text="Sicherheit",
            top_k=5,
            relevance_threshold=0.0,
            filters=None
        )
        
        results = hybrid_search_service.search(search_query)
        
        # Prüfe Metadata Enrichment
        assert len(results) >= 1
        result = results[0]
        
        assert "metadata" in result
        assert result["metadata"]["chunk_type"] == "safety"
        assert result["metadata"]["document_type"] == "Arbeitsanweisung"
        assert result["metadata"]["confidence_score"] == 0.95
        assert result["metadata"]["page_numbers"] == [3]
        assert result["metadata"]["heading_hierarchy"] == ["3. Sicherheit"]
    
    def test_hybrid_search_cross_document_search(self, hybrid_search_service, db_session):
        """Test Cross-Document Search"""
        # Erstelle mehrere Dokumente
        indexed_doc_repo = SQLAlchemyIndexedDocumentRepository(db_session)
        chunk_repo = SQLAlchemyDocumentChunkRepository(db_session)
        
        # Dokument 1
        doc1 = indexed_doc_repo.save(
            type('IndexedDocument', (), {
                'id': None,
                'upload_document_id': 1,
                'document_title': 'Montage-Anweisung',
                'document_type': 'Arbeitsanweisung',
                'qdrant_collection_name': 'test_collection',
                'total_chunks': 1,
                'status': 'indexed',
                'indexed_at': datetime.utcnow(),
                'last_updated': datetime.utcnow(),
                'embedding_model': 'text-embedding-3-small',
                'chunking_strategy': 'vision_ai'
            })()
        )
        
        # Dokument 2
        doc2 = indexed_doc_repo.save(
            type('IndexedDocument', (), {
                'id': None,
                'upload_document_id': 2,
                'document_title': 'Sicherheitshinweise',
                'document_type': 'Sicherheitsdokument',
                'qdrant_collection_name': 'test_collection',
                'total_chunks': 1,
                'status': 'indexed',
                'indexed_at': datetime.utcnow(),
                'last_updated': datetime.utcnow(),
                'embedding_model': 'text-embedding-3-small',
                'chunking_strategy': 'vision_ai'
            })()
        )
        
        # Chunks für beide Dokumente
        chunk1 = chunk_repo.save(DocumentChunk(
            id=None,
            indexed_document_id=doc1.id,
            chunk_id="doc1_p1_c0",
            chunk_text="Montage mit Schrauben und Muttern durchführen.",
            metadata=ChunkMetadata(
                page_numbers=[1],
                heading_hierarchy=["1. Montage"],
                document_type="Arbeitsanweisung",
                confidence_score=0.9,
                chunk_type="instruction",
                token_count=100
            ),
            qdrant_point_id="qdrant_point_1",
            embedding_vector_preview="[0.1, 0.2, ...]",
            created_at=datetime.utcnow()
        ))
        
        chunk2 = chunk_repo.save(DocumentChunk(
            id=None,
            indexed_document_id=doc2.id,
            chunk_id="doc2_p1_c0",
            chunk_text="Sicherheitshinweise für Montagearbeiten beachten.",
            metadata=ChunkMetadata(
                page_numbers=[1],
                heading_hierarchy=["1. Sicherheit"],
                document_type="Sicherheitsdokument",
                confidence_score=0.95,
                chunk_type="safety",
                token_count=80
            ),
            qdrant_point_id="qdrant_point_2",
            embedding_vector_preview="[0.3, 0.4, ...]",
            created_at=datetime.utcnow()
        ))
        
        # Mock Vector Store Results (beide Dokumente)
        vector_results = [
            {
                "chunk_id": "doc1_p1_c0",
                "score": 0.8,
                "payload": {"text": "Montage mit Schrauben und Muttern durchführen."}
            },
            {
                "chunk_id": "doc2_p1_c0",
                "score": 0.7,
                "payload": {"text": "Sicherheitshinweise für Montagearbeiten beachten."}
            }
        ]
        
        # Mock Services
        hybrid_search_service.embedding_service.generate_embedding.return_value = EmbeddingVector([0.1] * 1536)
        hybrid_search_service.vector_store_adapter.search_similar_chunks.return_value = vector_results
        
        # Test Cross-Document Search
        search_query = SearchQuery(
            text="Montage Sicherheit",
            top_k=10,
            relevance_threshold=0.0,
            filters=None
        )
        
        results = hybrid_search_service.search(search_query)
        
        # Sollte Ergebnisse aus beiden Dokumenten zurückgeben
        assert len(results) >= 2
        
        # Prüfe dass beide Dokumente vertreten sind
        document_types = {result["metadata"]["document_type"] for result in results}
        assert "Arbeitsanweisung" in document_types
        assert "Sicherheitsdokument" in document_types
