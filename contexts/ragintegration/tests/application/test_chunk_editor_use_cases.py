"""
Tests für Chunk-Editor Use Cases

TDD: Tests FIRST für Chunk-Editor Funktionalität (Edit, Delete, Split, Merge)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

# Diese Tests werden RED sein bis wir die Use Cases implementieren


class TestEditChunkUseCase:
    """Test EditChunkUseCase"""
    
    @pytest.mark.asyncio
    async def test_edit_chunk_text_updates_chunk(self):
        """
        GIVEN: Chunk existiert
        WHEN: EditChunkUseCase.execute() mit neuem Text
        THEN: Chunk-Text wird aktualisiert
        """
        # Dieser Test wird RED sein bis Use Case implementiert
        from contexts.ragintegration.application.use_cases import EditChunkUseCase
        
        # Mock Repository
        mock_repo = AsyncMock()
        mock_chunk = MagicMock(
            id=1,
            chunk_id="doc_123_chunk_1",
            chunk_text="Alter Text",
            indexed_document_id=123
        )
        mock_repo.get_by_id = AsyncMock(return_value=mock_chunk)
        mock_repo.save = AsyncMock(return_value=mock_chunk)
        
        # Execute Use Case
        use_case = EditChunkUseCase(mock_repo)
        result = await use_case.execute(
            chunk_id=1,
            new_text="Neuer Text"
        )
        
        # Verify
        assert result.chunk_text == "Neuer Text"
        mock_repo.save.assert_called_once()


class TestDeleteChunkUseCase:
    """Test DeleteChunkUseCase"""
    
    @pytest.mark.asyncio
    async def test_delete_chunk_removes_from_db_and_vector_store(self):
        """
        GIVEN: Chunk existiert
        WHEN: DeleteChunkUseCase.execute()
        THEN: Chunk wird aus DB und Vector Store gelöscht
        """
        from contexts.ragintegration.application.use_cases import DeleteChunkUseCase
        
        # Mock Dependencies
        mock_chunk_repo = AsyncMock()
        mock_vector_store = AsyncMock()
        mock_chunk = MagicMock(
            id=1,
            chunk_id="doc_123_chunk_1",
            qdrant_point_id="point_123"
        )
        mock_chunk_repo.get_by_id = AsyncMock(return_value=mock_chunk)
        mock_chunk_repo.delete = AsyncMock(return_value=True)
        mock_vector_store.delete_point = AsyncMock(return_value=True)
        
        # Execute Use Case
        use_case = DeleteChunkUseCase(mock_chunk_repo, mock_vector_store)
        result = await use_case.execute(chunk_id=1)
        
        # Verify
        assert result is True
        mock_chunk_repo.delete.assert_called_once_with(1)
        mock_vector_store.delete_point.assert_called_once_with("point_123")


class TestSplitChunkUseCase:
    """Test SplitChunkUseCase"""
    
    @pytest.mark.asyncio
    async def test_split_chunk_creates_two_new_chunks(self):
        """
        GIVEN: Chunk mit langem Text
        WHEN: SplitChunkUseCase.execute() mit Split-Position
        THEN: Zwei neue Chunks werden erstellt, Original wird gelöscht
        """
        from contexts.ragintegration.application.use_cases import SplitChunkUseCase
        
        # Mock Dependencies
        mock_chunk_repo = AsyncMock()
        mock_vector_store = AsyncMock()
        mock_embedding_service = AsyncMock()
        
        original_chunk = MagicMock(
            id=1,
            chunk_id="doc_123_chunk_1",
            chunk_text="Erster Teil. Zweiter Teil.",
            indexed_document_id=123,
            qdrant_point_id="point_123"
        )
        
        mock_chunk_repo.get_by_id = AsyncMock(return_value=original_chunk)
        mock_chunk_repo.save = AsyncMock(side_effect=lambda c: c)  # Return chunk as-is
        mock_embedding_service.create_embedding = AsyncMock(return_value=[0.1] * 1536)
        mock_vector_store.add_point = AsyncMock(return_value="new_point_id")
        
        # Execute Use Case
        use_case = SplitChunkUseCase(
            chunk_repo=mock_chunk_repo,
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service
        )
        
        result = await use_case.execute(
            chunk_id=1,
            split_position=15  # Split nach "Erster Teil."
        )
        
        # Verify
        assert len(result) == 2  # Zwei neue Chunks
        assert result[0].chunk_text == "Erster Teil."
        assert result[1].chunk_text == "Zweiter Teil."
        mock_chunk_repo.delete.assert_called_once_with(1)  # Original gelöscht


class TestMergeChunksUseCase:
    """Test MergeChunksUseCase"""
    
    @pytest.mark.asyncio
    async def test_merge_chunks_creates_single_chunk(self):
        """
        GIVEN: Zwei benachbarte Chunks
        WHEN: MergeChunksUseCase.execute()
        THEN: Ein neuer Chunk wird erstellt, Originale werden gelöscht
        """
        from contexts.ragintegration.application.use_cases import MergeChunksUseCase
        
        # Mock Dependencies
        mock_chunk_repo = AsyncMock()
        mock_vector_store = AsyncMock()
        mock_embedding_service = AsyncMock()
        
        chunk1 = MagicMock(
            id=1,
            chunk_id="doc_123_chunk_1",
            chunk_text="Erster Teil.",
            indexed_document_id=123,
            qdrant_point_id="point_1"
        )
        chunk2 = MagicMock(
            id=2,
            chunk_id="doc_123_chunk_2",
            chunk_text="Zweiter Teil.",
            indexed_document_id=123,
            qdrant_point_id="point_2"
        )
        
        mock_chunk_repo.get_by_id = AsyncMock(side_effect=[chunk1, chunk2])
        mock_chunk_repo.save = AsyncMock(side_effect=lambda c: c)
        mock_embedding_service.create_embedding = AsyncMock(return_value=[0.1] * 1536)
        mock_vector_store.add_point = AsyncMock(return_value="merged_point_id")
        mock_vector_store.delete_point = AsyncMock(return_value=True)
        
        # Execute Use Case
        use_case = MergeChunksUseCase(
            chunk_repo=mock_chunk_repo,
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service
        )
        
        result = await use_case.execute(chunk_ids=[1, 2])
        
        # Verify
        assert result.chunk_text == "Erster Teil. Zweiter Teil."
        assert mock_chunk_repo.delete.call_count == 2  # Beide Originale gelöscht
        assert mock_vector_store.delete_point.call_count == 2  # Beide Points gelöscht

