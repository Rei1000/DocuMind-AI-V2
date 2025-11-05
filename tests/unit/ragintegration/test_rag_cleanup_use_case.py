"""
Unit Tests für RemoveDocumentFromRAGUseCase.

Test-Driven Development: RED Phase für RAG Cleanup Use Case.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime

from contexts.ragintegration.application.use_cases import RemoveDocumentFromRAGUseCase
from contexts.ragintegration.domain.entities import IndexedDocument
from contexts.ragintegration.domain.repositories import (
    IndexedDocumentRepository,
    DocumentChunkRepository,
    VectorStoreRepository
)


class TestRemoveDocumentFromRAGUseCase:
    """Tests für RemoveDocumentFromRAGUseCase."""
    
    @pytest.fixture
    def mock_indexed_doc_repo(self):
        """Mock IndexedDocumentRepository."""
        return Mock(spec=IndexedDocumentRepository)
    
    @pytest.fixture
    def mock_chunk_repo(self):
        """Mock DocumentChunkRepository."""
        return Mock(spec=DocumentChunkRepository)
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock VectorStoreRepository."""
        return Mock(spec=VectorStoreRepository)
    
    @pytest.fixture
    def use_case(self, mock_indexed_doc_repo, mock_chunk_repo, mock_vector_store):
        """RemoveDocumentFromRAGUseCase mit Mocks."""
        return RemoveDocumentFromRAGUseCase(
            indexed_document_repository=mock_indexed_doc_repo,
            document_chunk_repository=mock_chunk_repo,
            vector_store=mock_vector_store
        )
    
    def test_remove_document_deletes_from_vector_store(self, use_case, mock_indexed_doc_repo, mock_chunk_repo, mock_vector_store):
        """Remove löscht Chunks aus Vector Store"""
        # Arrange
        upload_document_id = 1
        indexed_doc = IndexedDocument(
            id=1,
            upload_document_id=upload_document_id,
            collection_name="rag_documents",
            indexed_at=datetime.utcnow(),
            total_chunks=5,
            last_updated_at=datetime.utcnow()
        )
        mock_indexed_doc_repo.get_by_upload_document_id = Mock(return_value=indexed_doc)
        mock_vector_store.delete_chunks_by_document_id = Mock(return_value=5)
        mock_chunk_repo.delete_by_indexed_document_id = Mock(return_value=5)
        mock_indexed_doc_repo.delete = Mock(return_value=True)
        
        # Act
        result = use_case.execute(upload_document_id=upload_document_id)
        
        # Assert
        assert result["success"] is True
        assert result["removed_chunks"] == 5
        mock_vector_store.delete_chunks_by_document_id.assert_called_once_with(
            collection_name="rag_documents",
            document_id=upload_document_id
        )
    
    def test_remove_document_deletes_chunks_from_repository(self, use_case, mock_indexed_doc_repo, mock_chunk_repo, mock_vector_store):
        """Remove löscht Chunks aus Chunk Repository"""
        # Arrange
        upload_document_id = 1
        indexed_doc = IndexedDocument(
            id=1,
            upload_document_id=upload_document_id,
            collection_name="rag_documents",
            indexed_at=datetime.utcnow(),
            total_chunks=5,
            last_updated_at=datetime.utcnow()
        )
        mock_indexed_doc_repo.get_by_upload_document_id = Mock(return_value=indexed_doc)
        mock_vector_store.delete_chunks_by_document_id = Mock(return_value=5)
        mock_chunk_repo.delete_by_indexed_document_id = Mock(return_value=5)
        mock_indexed_doc_repo.delete = Mock(return_value=True)
        
        # Act
        result = use_case.execute(upload_document_id=upload_document_id)
        
        # Assert
        assert result["removed_chunks"] == 5
        mock_chunk_repo.delete_by_indexed_document_id.assert_called_once_with(indexed_document_id=1)
    
    def test_remove_document_deletes_indexed_document(self, use_case, mock_indexed_doc_repo, mock_chunk_repo, mock_vector_store):
        """Remove löscht IndexedDocument aus Repository"""
        # Arrange
        upload_document_id = 1
        indexed_doc = IndexedDocument(
            id=1,
            upload_document_id=upload_document_id,
            collection_name="rag_documents",
            indexed_at=datetime.utcnow(),
            total_chunks=5,
            last_updated_at=datetime.utcnow()
        )
        mock_indexed_doc_repo.get_by_upload_document_id = Mock(return_value=indexed_doc)
        mock_vector_store.delete_chunks_by_document_id = Mock(return_value=5)
        mock_chunk_repo.delete_by_indexed_document_id = Mock(return_value=5)
        mock_indexed_doc_repo.delete = Mock(return_value=True)
        
        # Act
        result = use_case.execute(upload_document_id=upload_document_id)
        
        # Assert
        assert result["success"] is True
        mock_indexed_doc_repo.delete.assert_called_once_with(indexed_document_id=1)
    
    def test_remove_document_not_indexed_returns_success(self, use_case, mock_indexed_doc_repo, mock_chunk_repo, mock_vector_store):
        """Remove gibt Success zurück wenn Dokument nicht indexiert ist (idempotent)"""
        # Arrange
        upload_document_id = 999
        mock_indexed_doc_repo.get_by_upload_document_id = Mock(return_value=None)
        
        # Act
        result = use_case.execute(upload_document_id=upload_document_id)
        
        # Assert
        assert result["success"] is True
        assert result["removed_chunks"] == 0
        assert result["message"] == "Document not indexed in RAG"
        # Vector Store und Chunk Repo sollten nicht aufgerufen werden
        mock_vector_store.delete_chunks_by_document_id.assert_not_called()
        mock_chunk_repo.delete_by_indexed_document_id.assert_not_called()
        mock_indexed_doc_repo.delete.assert_not_called()
    
    def test_remove_document_zero_chunks_handles_correctly(self, use_case, mock_indexed_doc_repo, mock_chunk_repo, mock_vector_store):
        """Remove behandelt Dokumente ohne Chunks korrekt"""
        # Arrange
        upload_document_id = 1
        indexed_doc = IndexedDocument(
            id=1,
            upload_document_id=upload_document_id,
            collection_name="rag_documents",
            indexed_at=datetime.utcnow(),
            total_chunks=0,  # Keine Chunks
            last_updated_at=datetime.utcnow()
        )
        mock_indexed_doc_repo.get_by_upload_document_id = Mock(return_value=indexed_doc)
        mock_vector_store.delete_chunks_by_document_id = Mock(return_value=0)
        mock_chunk_repo.delete_by_indexed_document_id = Mock(return_value=0)
        mock_indexed_doc_repo.delete = Mock(return_value=True)
        
        # Act
        result = use_case.execute(upload_document_id=upload_document_id)
        
        # Assert
        assert result["success"] is True
        assert result["removed_chunks"] == 0

