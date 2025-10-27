"""
Unit Tests für RAG Integration Repository Interfaces.

TDD Approach: Diese Tests werden ZUERST geschrieben, dann die Repository Interfaces implementiert.
"""

import pytest
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from contexts.ragintegration.domain.entities import (
    IndexedDocument,
    DocumentChunk,
    ChatSession,
    ChatMessage
)
from contexts.ragintegration.domain.value_objects import (
    EmbeddingVector,
    ChunkMetadata,
    SourceReference
)
from contexts.ragintegration.domain.repositories import (
    IndexedDocumentRepository,
    DocumentChunkRepository,
    ChatSessionRepository,
    VectorStoreRepository,
    EmbeddingService
)


class TestIndexedDocumentRepository:
    """Tests für IndexedDocumentRepository Interface."""
    
    def test_repository_is_abstract(self):
        """Test: Repository ist abstrakte Klasse."""
        assert issubclass(IndexedDocumentRepository, ABC)
    
    def test_repository_has_required_methods(self):
        """Test: Repository hat alle erforderlichen Methoden."""
        required_methods = [
            'get_by_id',
            'get_by_upload_document_id',
            'get_all',
            'save',
            'delete',
            'exists_by_upload_document_id'
        ]
        
        for method_name in required_methods:
            assert hasattr(IndexedDocumentRepository, method_name)
            method = getattr(IndexedDocumentRepository, method_name)
            assert callable(method)
    
    def test_get_by_id_signature(self):
        """Test: get_by_id Methoden-Signatur."""
        # Prüfe dass Methode abstrakt ist
        method = IndexedDocumentRepository.get_by_id
        assert hasattr(method, '__isabstractmethod__')
    
    def test_save_signature(self):
        """Test: save Methoden-Signatur."""
        method = IndexedDocumentRepository.save
        assert hasattr(method, '__isabstractmethod__')


class TestDocumentChunkRepository:
    """Tests für DocumentChunkRepository Interface."""
    
    def test_repository_is_abstract(self):
        """Test: Repository ist abstrakte Klasse."""
        assert issubclass(DocumentChunkRepository, ABC)
    
    def test_repository_has_required_methods(self):
        """Test: Repository hat alle erforderlichen Methoden."""
        required_methods = [
            'get_by_id',
            'get_by_chunk_id',
            'get_by_indexed_document_id',
            'get_all',
            'save',
            'save_batch',
            'delete',
            'delete_by_indexed_document_id',
            'exists_by_chunk_id'
        ]
        
        for method_name in required_methods:
            assert hasattr(DocumentChunkRepository, method_name)
            method = getattr(DocumentChunkRepository, method_name)
            assert callable(method)
    
    def test_get_by_chunk_id_signature(self):
        """Test: get_by_chunk_id Methoden-Signatur."""
        method = DocumentChunkRepository.get_by_chunk_id
        assert hasattr(method, '__isabstractmethod__')
    
    def test_save_batch_signature(self):
        """Test: save_batch Methoden-Signatur."""
        method = DocumentChunkRepository.save_batch
        assert hasattr(method, '__isabstractmethod__')


class TestChatSessionRepository:
    """Tests für ChatSessionRepository Interface."""
    
    def test_repository_is_abstract(self):
        """Test: Repository ist abstrakte Klasse."""
        assert issubclass(ChatSessionRepository, ABC)
    
    def test_repository_has_required_methods(self):
        """Test: Repository hat alle erforderlichen Methoden."""
        required_methods = [
            'get_by_id',
            'get_by_user_id',
            'get_active_by_user_id',
            'get_all',
            'save',
            'delete',
            'get_messages_by_session_id',
            'save_message',
            'delete_message',
            'get_message_count_by_session_id'
        ]
        
        for method_name in required_methods:
            assert hasattr(ChatSessionRepository, method_name)
            method = getattr(ChatSessionRepository, method_name)
            assert callable(method)
    
    def test_get_by_user_id_signature(self):
        """Test: get_by_user_id Methoden-Signatur."""
        method = ChatSessionRepository.get_by_user_id
        assert hasattr(method, '__isabstractmethod__')
    
    def test_save_message_signature(self):
        """Test: save_message Methoden-Signatur."""
        method = ChatSessionRepository.save_message
        assert hasattr(method, '__isabstractmethod__')


class TestVectorStoreRepository:
    """Tests für VectorStoreRepository Interface."""
    
    def test_repository_is_abstract(self):
        """Test: Repository ist abstrakte Klasse."""
        assert issubclass(VectorStoreRepository, ABC)
    
    def test_repository_has_required_methods(self):
        """Test: Repository hat alle erforderlichen Methoden."""
        required_methods = [
            'create_collection',
            'delete_collection',
            'collection_exists',
            'index_chunk',
            'index_chunks_batch',
            'search_similar',
            'delete_chunk',
            'delete_chunks_by_document_id',
            'get_collection_info'
        ]
        
        for method_name in required_methods:
            assert hasattr(VectorStoreRepository, method_name)
            method = getattr(VectorStoreRepository, method_name)
            assert callable(method)
    
    def test_index_chunk_signature(self):
        """Test: index_chunk Methoden-Signatur."""
        method = VectorStoreRepository.index_chunk
        assert hasattr(method, '__isabstractmethod__')
    
    def test_search_similar_signature(self):
        """Test: search_similar Methoden-Signatur."""
        method = VectorStoreRepository.search_similar
        assert hasattr(method, '__isabstractmethod__')


class TestEmbeddingService:
    """Tests für EmbeddingService Interface."""
    
    def test_service_is_abstract(self):
        """Test: Service ist abstrakte Klasse."""
        assert issubclass(EmbeddingService, ABC)
    
    def test_service_has_required_methods(self):
        """Test: Service hat alle erforderlichen Methoden."""
        required_methods = [
            'generate_embedding',
            'generate_embeddings_batch',
            'get_model_info',
            'get_dimensions'
        ]
        
        for method_name in required_methods:
            assert hasattr(EmbeddingService, method_name)
            method = getattr(EmbeddingService, method_name)
            assert callable(method)
    
    def test_generate_embedding_signature(self):
        """Test: generate_embedding Methoden-Signatur."""
        method = EmbeddingService.generate_embedding
        assert hasattr(method, '__isabstractmethod__')
    
    def test_generate_embeddings_batch_signature(self):
        """Test: generate_embeddings_batch Methoden-Signatur."""
        method = EmbeddingService.generate_embeddings_batch
        assert hasattr(method, '__isabstractmethod__')
