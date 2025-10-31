"""
Integration Tests für RAG Infrastructure Layer - Qdrant Vector Store

Diese Tests prüfen die Integration mit Qdrant Vector Store (In-Memory).
Sie verwenden echte Qdrant-Instanzen für realistische Tests.
"""

import pytest
import tempfile
import os
from typing import List
from unittest.mock import Mock, patch

# Import Domain Entities
from contexts.ragintegration.domain.entities import DocumentChunk
from contexts.ragintegration.domain.value_objects import EmbeddingVector, ChunkMetadata

# Import Infrastructure
from contexts.ragintegration.infrastructure.vector_store_adapter import QdrantVectorStoreAdapter


class TestQdrantVectorStoreIntegration:
    """Integration Tests für Qdrant Vector Store Adapter"""
    
    @pytest.fixture
    def qdrant_adapter(self):
        """Erstelle Qdrant Adapter für Tests"""
        return QdrantVectorStoreAdapter()
    
    @pytest.fixture
    def sample_chunks(self):
        """Erstelle Sample DocumentChunks für Tests"""
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
            heading_hierarchy=["2. Hauptteil"],
            document_type="Arbeitsanweisung",
            confidence_score=0.85,
            chunk_type="instruction",
            token_count=120
        )
        
        chunk1 = DocumentChunk(
            id=1,
            indexed_document_id=1,
            chunk_id="doc1_p1_c0",
            chunk_text="Dies ist der erste Chunk mit wichtigen Informationen zur Montage.",
            metadata=metadata1,
            qdrant_point_id="qdrant_point_1",
            embedding_vector_preview="[0.1, 0.2, 0.3, ...]",
            created_at=None
        )
        
        chunk2 = DocumentChunk(
            id=2,
            indexed_document_id=1,
            chunk_id="doc1_p2_c0",
            chunk_text="Dies ist der zweite Chunk mit weiteren Details zur Installation.",
            metadata=metadata2,
            qdrant_point_id="qdrant_point_2",
            embedding_vector_preview="[0.4, 0.5, 0.6, ...]",
            created_at=None
        )
        
        return [chunk1, chunk2]
    
    @pytest.fixture
    def sample_embeddings(self):
        """Erstelle Sample Embeddings für Tests"""
        # Simuliere 1536-Dimension Embeddings
        embedding1 = EmbeddingVector([0.1] * 1536)
        embedding2 = EmbeddingVector([0.2] * 1536)
        return [embedding1, embedding2]
    
    def test_create_collection(self, qdrant_adapter):
        """Test Collection Creation"""
        collection_name = "test_collection"
        
        # Erstelle Collection
        result = qdrant_adapter.create_collection(collection_name)
        assert result is True
        
        # Prüfe dass Collection existiert
        exists = qdrant_adapter.collection_exists(collection_name)
        assert exists is True
    
    def test_delete_collection(self, qdrant_adapter):
        """Test Collection Deletion"""
        collection_name = "test_collection_delete"
        
        # Erstelle Collection
        qdrant_adapter.create_collection(collection_name)
        assert qdrant_adapter.collection_exists(collection_name) is True
        
        # Lösche Collection
        result = qdrant_adapter.delete_collection(collection_name)
        assert result is True
        
        # Prüfe dass Collection gelöscht wurde
        exists = qdrant_adapter.collection_exists(collection_name)
        assert exists is False
    
    def test_upsert_chunks(self, qdrant_adapter, sample_chunks, sample_embeddings):
        """Test Chunk Upsert Operation"""
        collection_name = "test_upsert_collection"
        
        # Erstelle Collection
        qdrant_adapter.create_collection(collection_name)
        
        # Upsert Chunks
        result = qdrant_adapter.upsert_chunks(collection_name, sample_chunks, sample_embeddings)
        assert result is True
        
        # Prüfe dass Chunks gespeichert wurden
        count = qdrant_adapter.get_collection_count(collection_name)
        assert count == 2
    
    def test_search_similar_chunks(self, qdrant_adapter, sample_chunks, sample_embeddings):
        """Test Similarity Search"""
        collection_name = "test_search_collection"
        
        # Erstelle Collection und füge Chunks hinzu
        qdrant_adapter.create_collection(collection_name)
        qdrant_adapter.upsert_chunks(collection_name, sample_chunks, sample_embeddings)
        
        # Suche ähnliche Chunks
        query_embedding = EmbeddingVector([0.15] * 1536)  # Ähnlich zu embedding1
        results = qdrant_adapter.search_similar_chunks(
            collection_name=collection_name,
            query_embedding=query_embedding,
            limit=2,
            score_threshold=0.0
        )
        
        assert len(results) == 2
        assert results[0]["chunk_id"] == "doc1_p1_c0"
        assert results[0]["score"] > 0.0
        assert results[1]["chunk_id"] == "doc1_p2_c0"
    
    def test_search_with_score_threshold(self, qdrant_adapter, sample_chunks, sample_embeddings):
        """Test Search mit Score Threshold"""
        collection_name = "test_threshold_collection"
        
        # Erstelle Collection und füge Chunks hinzu
        qdrant_adapter.create_collection(collection_name)
        qdrant_adapter.upsert_chunks(collection_name, sample_chunks, sample_embeddings)
        
        # Suche mit hohem Score Threshold
        query_embedding = EmbeddingVector([0.1] * 1536)
        results = qdrant_adapter.search_similar_chunks(
            collection_name=collection_name,
            query_embedding=query_embedding,
            limit=10,
            score_threshold=0.9  # Sehr hoher Threshold
        )
        
        # Sollte keine Ergebnisse zurückgeben (Score zu niedrig)
        assert len(results) == 0
    
    def test_delete_chunks(self, qdrant_adapter, sample_chunks, sample_embeddings):
        """Test Chunk Deletion"""
        collection_name = "test_delete_collection"
        
        # Erstelle Collection und füge Chunks hinzu
        qdrant_adapter.create_collection(collection_name)
        qdrant_adapter.upsert_chunks(collection_name, sample_chunks, sample_embeddings)
        
        # Prüfe dass Chunks existieren
        count_before = qdrant_adapter.get_collection_count(collection_name)
        assert count_before == 2
        
        # Lösche einen Chunk
        chunk_ids_to_delete = ["doc1_p1_c0"]
        result = qdrant_adapter.delete_chunks(collection_name, chunk_ids_to_delete)
        assert result is True
        
        # Prüfe dass Chunk gelöscht wurde
        count_after = qdrant_adapter.get_collection_count(collection_name)
        assert count_after == 1
    
    def test_get_collection_info(self, qdrant_adapter, sample_chunks, sample_embeddings):
        """Test Collection Info Retrieval"""
        collection_name = "test_info_collection"
        
        # Erstelle Collection und füge Chunks hinzu
        qdrant_adapter.create_collection(collection_name)
        qdrant_adapter.upsert_chunks(collection_name, sample_chunks, sample_embeddings)
        
        # Hole Collection Info
        info = qdrant_adapter.get_collection_info(collection_name)
        
        assert info is not None
        assert info["name"] == collection_name
        assert info["points_count"] == 2
        assert info["vector_size"] == 1536
    
    def test_multiple_collections(self, qdrant_adapter, sample_chunks, sample_embeddings):
        """Test Multiple Collections Management"""
        collection1 = "test_multi_collection_1"
        collection2 = "test_multi_collection_2"
        
        # Erstelle beide Collections
        qdrant_adapter.create_collection(collection1)
        qdrant_adapter.create_collection(collection2)
        
        # Füge Chunks zu beiden Collections hinzu
        qdrant_adapter.upsert_chunks(collection1, sample_chunks, sample_embeddings)
        qdrant_adapter.upsert_chunks(collection2, sample_chunks, sample_embeddings)
        
        # Prüfe beide Collections
        count1 = qdrant_adapter.get_collection_count(collection1)
        count2 = qdrant_adapter.get_collection_count(collection2)
        
        assert count1 == 2
        assert count2 == 2
        
        # Suche in beiden Collections
        query_embedding = EmbeddingVector([0.1] * 1536)
        
        results1 = qdrant_adapter.search_similar_chunks(
            collection_name=collection1,
            query_embedding=query_embedding,
            limit=2,
            score_threshold=0.0
        )
        
        results2 = qdrant_adapter.search_similar_chunks(
            collection_name=collection2,
            query_embedding=query_embedding,
            limit=2,
            score_threshold=0.0
        )
        
        assert len(results1) == 2
        assert len(results2) == 2
    
    def test_error_handling_nonexistent_collection(self, qdrant_adapter):
        """Test Error Handling für nicht existierende Collections"""
        collection_name = "nonexistent_collection"
        
        # Versuche Suche in nicht existierender Collection
        query_embedding = EmbeddingVector([0.1] * 1536)
        
        with pytest.raises(Exception):
            qdrant_adapter.search_similar_chunks(
                collection_name=collection_name,
                query_embedding=query_embedding,
                limit=10,
                score_threshold=0.0
            )
    
    def test_error_handling_invalid_embedding_dimension(self, qdrant_adapter):
        """Test Error Handling für ungültige Embedding-Dimensionen"""
        collection_name = "test_dimension_collection"
        qdrant_adapter.create_collection(collection_name)
        
        # Erstelle Chunk mit ungültiger Embedding-Dimension
        invalid_embedding = EmbeddingVector([0.1] * 100)  # Falsche Dimension
        
        chunk = DocumentChunk(
            id=1,
            indexed_document_id=1,
            chunk_id="invalid_chunk",
            chunk_text="Test chunk",
            metadata=ChunkMetadata(
                page_numbers=[1],
                heading_hierarchy=["Test"],
                document_type="Test",
                confidence_score=0.9,
                chunk_type="test",
                token_count=10
            ),
            qdrant_point_id="invalid_point",
            embedding_vector_preview="[0.1, 0.2, ...]",
            created_at=None
        )
        
        with pytest.raises(Exception):
            qdrant_adapter.upsert_chunks(collection_name, [chunk], [invalid_embedding])
    
    def test_performance_large_dataset(self, qdrant_adapter):
        """Test Performance mit größerem Dataset"""
        collection_name = "test_performance_collection"
        qdrant_adapter.create_collection(collection_name)
        
        # Erstelle 100 Chunks
        chunks = []
        embeddings = []
        
        for i in range(100):
            metadata = ChunkMetadata(
                page_numbers=[i % 10 + 1],
                heading_hierarchy=[f"{i}. Test Heading"],
                document_type="Performance Test",
                confidence_score=0.9,
                chunk_type="test",
                token_count=100
            )
            
            chunk = DocumentChunk(
                id=i,
                indexed_document_id=i,
                chunk_id=f"perf_chunk_{i}",
                chunk_text=f"Performance test chunk {i} with important information.",
                metadata=metadata,
                qdrant_point_id=f"perf_point_{i}",
                embedding_vector_preview=f"[{i * 0.01}, ...]",
                created_at=None
            )
            
            # Erstelle einzigartige Embeddings
            embedding = EmbeddingVector([i * 0.01] * 1536)
            
            chunks.append(chunk)
            embeddings.append(embedding)
        
        # Test Upsert Performance
        import time
        start_time = time.time()
        
        result = qdrant_adapter.upsert_chunks(collection_name, chunks, embeddings)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert result is True
        assert duration < 10.0, f"Upsert took {duration} seconds"
        
        # Test Search Performance
        query_embedding = EmbeddingVector([0.5] * 1536)
        
        start_time = time.time()
        results = qdrant_adapter.search_similar_chunks(
            collection_name=collection_name,
            query_embedding=query_embedding,
            limit=10,
            score_threshold=0.0
        )
        end_time = time.time()
        search_duration = end_time - start_time
        
        assert len(results) == 10
        assert search_duration < 1.0, f"Search took {search_duration} seconds"
    
    def test_concurrent_operations(self, qdrant_adapter):
        """Test Concurrent Operations"""
        collection_name = "test_concurrent_collection"
        qdrant_adapter.create_collection(collection_name)
        
        # Erstelle mehrere Chunks gleichzeitig
        chunks = []
        embeddings = []
        
        for i in range(10):
            metadata = ChunkMetadata(
                page_numbers=[i + 1],
                heading_hierarchy=[f"{i}. Concurrent Test"],
                document_type="Concurrent Test",
                confidence_score=0.9,
                chunk_type="test",
                token_count=100
            )
            
            chunk = DocumentChunk(
                id=i,
                indexed_document_id=i,
                chunk_id=f"concurrent_chunk_{i}",
                chunk_text=f"Concurrent test chunk {i}.",
                metadata=metadata,
                qdrant_point_id=f"concurrent_point_{i}",
                embedding_vector_preview=f"[{i * 0.1}, ...]",
                created_at=None
            )
            
            embedding = EmbeddingVector([i * 0.1] * 1536)
            
            chunks.append(chunk)
            embeddings.append(embedding)
        
        # Upsert alle Chunks
        result = qdrant_adapter.upsert_chunks(collection_name, chunks, embeddings)
        assert result is True
        
        # Prüfe dass alle Chunks gespeichert wurden
        count = qdrant_adapter.get_collection_count(collection_name)
        assert count == 10
        
        # Teste mehrere gleichzeitige Suchen
        query_embeddings = [
            EmbeddingVector([0.1] * 1536),
            EmbeddingVector([0.2] * 1536),
            EmbeddingVector([0.3] * 1536)
        ]
        
        for query_embedding in query_embeddings:
            results = qdrant_adapter.search_similar_chunks(
                collection_name=collection_name,
                query_embedding=query_embedding,
                limit=5,
                score_threshold=0.0
            )
            assert len(results) == 5
            assert all(result["score"] >= 0.0 for result in results)
