"""
Tests für Chunk-Vorschau Endpoint

TDD: Tests FIRST für Chunk-Vorschau API
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

# Diese Tests werden RED sein bis wir den Endpoint implementieren


class TestChunkPreviewEndpoint:
    """Test Chunk-Vorschau API Endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_chunks_for_document_returns_list(self):
        """
        GIVEN: Dokument mit indexierten Chunks
        WHEN: GET /api/rag/chunks/{document_id}
        THEN: Liste aller Chunks zurückgegeben
        """
        # Dieser Test wird RED sein bis Endpoint implementiert
        from contexts.ragintegration.interface.router import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Mock Repository
        with patch('contexts.ragintegration.infrastructure.repositories.SQLAlchemyDocumentChunkRepository') as mock_repo:
            mock_repo.get_by_document_id = AsyncMock(return_value=[
                MagicMock(
                    id=1,
                    chunk_id="doc_123_chunk_1",
                    chunk_text="Test Chunk 1",
                    metadata=MagicMock(page_numbers=[1])
                ),
                MagicMock(
                    id=2,
                    chunk_id="doc_123_chunk_2",
                    chunk_text="Test Chunk 2",
                    metadata=MagicMock(page_numbers=[2])
                )
            ])
            
            response = client.get("/api/rag/chunks/123")
            
            assert response.status_code == 200
            data = response.json()
            assert "chunks" in data
            assert len(data["chunks"]) == 2
            assert data["chunks"][0]["chunk_id"] == "doc_123_chunk_1"
    
    @pytest.mark.asyncio
    async def test_get_chunks_for_nonexistent_document_returns_404(self):
        """
        GIVEN: Dokument existiert nicht
        WHEN: GET /api/rag/chunks/{document_id}
        THEN: 404 Not Found
        """
        from contexts.ragintegration.interface.router import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Mock Repository - keine Chunks gefunden
        with patch('contexts.ragintegration.infrastructure.repositories.SQLAlchemyDocumentChunkRepository') as mock_repo:
            mock_repo.get_by_document_id = AsyncMock(return_value=[])
            
            response = client.get("/api/rag/chunks/999")
            
            # Sollte 404 oder leere Liste zurückgeben (je nach Design)
            assert response.status_code in [200, 404]
            if response.status_code == 200:
                data = response.json()
                assert len(data.get("chunks", [])) == 0
    
    @pytest.mark.asyncio
    async def test_get_chunks_includes_metadata(self):
        """
        GIVEN: Chunk mit vollständigen Metadaten
        WHEN: GET /api/rag/chunks/{document_id}
        THEN: Response enthält Metadaten (page_numbers, heading_hierarchy, etc.)
        """
        from contexts.ragintegration.interface.router import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        # Mock Repository mit Metadaten
        with patch('contexts.ragintegration.infrastructure.repositories.SQLAlchemyDocumentChunkRepository') as mock_repo:
            mock_chunk = MagicMock()
            mock_chunk.id = 1
            mock_chunk.chunk_id = "doc_123_chunk_1"
            mock_chunk.chunk_text = "Test Chunk"
            mock_chunk.metadata.page_numbers = [1, 2]
            mock_chunk.metadata.heading_hierarchy = ["Title", "Section"]
            mock_chunk.metadata.chunk_type = "section"
            mock_chunk.metadata.token_count = 150
            
            mock_repo.get_by_document_id = AsyncMock(return_value=[mock_chunk])
            
            response = client.get("/api/rag/chunks/123")
            
            assert response.status_code == 200
            data = response.json()
            chunk = data["chunks"][0]
            assert "metadata" in chunk
            assert chunk["metadata"]["page_numbers"] == [1, 2]
            assert chunk["metadata"]["heading_hierarchy"] == ["Title", "Section"]

