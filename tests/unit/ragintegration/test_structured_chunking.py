"""
TDD Tests für Strukturierte Chunking-Strategie

Tests für Vision-JSON-Daten Chunking basierend auf RAG-Anything Best Practices.
"""
import pytest
from unittest.mock import Mock, patch
from contexts.ragintegration.domain.entities import DocumentChunk
from contexts.ragintegration.domain.value_objects import ChunkMetadata, SourceReference
from contexts.ragintegration.infrastructure.services import StructuredChunkingService


class TestStructuredChunking:
    """TDD Tests für strukturierte Chunking-Strategie."""
    
    def test_vision_json_chunking(self):
        """Test: Vision-JSON-Daten werden korrekt gechunkt."""
        service = StructuredChunkingService()
        
        # Mock Vision-JSON-Daten (wie sie vom Upload kommen)
        vision_data = {
            "pages": [
                {
                    "page_number": 1,
                    "content": {
                        "text": "Arbeitsanweisung WA-001: Freilaufwelle\nArtikelnummer: 123.456.789\nSicherheitshinweise: Vor Reparatur Strom abschalten.",
                        "tables": [
                            {
                                "data": [
                                    ["Teil", "Artikelnummer", "Beschreibung"],
                                    ["Freilaufwelle", "123.456.789", "Hauptkomponente"],
                                    ["Lager", "987.654.321", "Lagerung"]
                                ]
                            }
                        ],
                        "images": [
                            {
                                "description": "Freilaufwelle Montage",
                                "ocr_text": "Freilaufwelle 123.456.789"
                            }
                        ]
                    }
                }
            ]
        }
        
        chunks = service.create_chunks_from_vision_data(vision_data, document_id=1)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        
        # Teste spezifische Chunks
        text_chunks = [c for c in chunks if c.metadata.chunk_type == "text"]
        table_chunks = [c for c in chunks if c.metadata.chunk_type == "table"]
        image_chunks = [c for c in chunks if c.metadata.chunk_type == "image"]
        
        assert len(text_chunks) > 0
        assert len(table_chunks) > 0
        assert len(image_chunks) > 0
    
    def test_article_number_extraction(self):
        """Test: Artikelnummern werden korrekt extrahiert."""
        service = StructuredChunkingService()
        
        vision_data = {
            "pages": [
                {
                    "page_number": 1,
                    "content": {
                        "text": "Die Freilaufwelle hat die Artikelnummer 123.456.789 und wird in der Arbeitsanweisung WA-001 beschrieben.",
                        "tables": [],
                        "images": []
                    }
                }
            ]
        }
        
        chunks = service.create_chunks_from_vision_data(vision_data, document_id=1)
        
        # Finde Chunk mit Artikelnummer
        article_chunk = None
        for chunk in chunks:
            if "123.456.789" in chunk.chunk_text:
                article_chunk = chunk
                break
        
        assert article_chunk is not None
        assert "Freilaufwelle" in article_chunk.chunk_text
        assert "123.456.789" in article_chunk.chunk_text
        assert article_chunk.metadata.page_numbers == [1]
    
    def test_hierarchical_chunking(self):
        """Test: Hierarchische Chunking mit Überschriften."""
        service = StructuredChunkingService()
        
        vision_data = {
            "pages": [
                {
                    "page_number": 1,
                    "content": {
                        "text": "1. Einleitung\nDies ist die Einleitung.\n\n2. Hauptteil\nHier steht der Hauptinhalt.\n\n3. Schluss\nDas ist das Ende.",
                        "tables": [],
                        "images": []
                    }
                }
            ]
        }
        
        chunks = service.create_chunks_from_vision_data(vision_data, document_id=1)
        
        # Teste hierarchische Struktur
        intro_chunk = None
        main_chunk = None
        end_chunk = None
        
        for chunk in chunks:
            if "Einleitung" in chunk.chunk_text:
                intro_chunk = chunk
            elif "Hauptteil" in chunk.chunk_text:
                main_chunk = chunk
            elif "Schluss" in chunk.chunk_text:
                end_chunk = chunk
        
        assert intro_chunk is not None
        assert main_chunk is not None
        assert end_chunk is not None
        
        # Teste Überschriften-Hierarchie
        assert "1. Einleitung" in intro_chunk.metadata.heading_hierarchy
        assert "2. Hauptteil" in main_chunk.metadata.heading_hierarchy
        assert "3. Schluss" in end_chunk.metadata.heading_hierarchy
    
    def test_table_chunking(self):
        """Test: Tabellen werden korrekt gechunkt."""
        service = StructuredChunkingService()
        
        vision_data = {
            "pages": [
                {
                    "page_number": 1,
                    "content": {
                        "text": "",
                        "tables": [
                            {
                                "data": [
                                    ["Teil", "Artikelnummer", "Beschreibung"],
                                    ["Freilaufwelle", "123.456.789", "Hauptkomponente"],
                                    ["Lager", "987.654.321", "Lagerung"]
                                ]
                            }
                        ],
                        "images": []
                    }
                }
            ]
        }
        
        chunks = service.create_chunks_from_vision_data(vision_data, document_id=1)
        
        table_chunks = [c for c in chunks if c.metadata.chunk_type == "table"]
        assert len(table_chunks) > 0
        
        table_chunk = table_chunks[0]
        assert "Freilaufwelle" in table_chunk.chunk_text
        assert "123.456.789" in table_chunk.chunk_text
        assert "Lager" in table_chunk.chunk_text
        assert "987.654.321" in table_chunk.chunk_text
    
    def test_image_chunking(self):
        """Test: Bilder werden korrekt gechunkt."""
        service = StructuredChunkingService()
        
        vision_data = {
            "pages": [
                {
                    "page_number": 1,
                    "content": {
                        "text": "",
                        "tables": [],
                        "images": [
                            {
                                "description": "Freilaufwelle Montage",
                                "ocr_text": "Freilaufwelle 123.456.789"
                            }
                        ]
                    }
                }
            ]
        }
        
        chunks = service.create_chunks_from_vision_data(vision_data, document_id=1)
        
        image_chunks = [c for c in chunks if c.metadata.chunk_type == "image"]
        assert len(image_chunks) > 0
        
        image_chunk = image_chunks[0]
        assert "Freilaufwelle" in image_chunk.chunk_text
        assert "123.456.789" in image_chunk.chunk_text
        assert "Montage" in image_chunk.chunk_text
    
    def test_chunk_structure(self):
        """Test: Chunk-Struktur ist korrekt."""
        service = StructuredChunkingService()
        
        vision_data = {
            "pages": [
                {
                    "page_number": 1,
                    "content": {
                        "text": "Test Inhalt",
                        "tables": [],
                        "images": []
                    }
                }
            ]
        }
        
        chunks = service.create_chunks_from_vision_data(vision_data, document_id=1)
        
        for chunk in chunks:
            assert chunk.indexed_document_id == 1
            assert chunk.chunk_id is not None
            assert chunk.chunk_text is not None
            assert chunk.metadata is not None
            assert chunk.qdrant_point_id is not None
            assert chunk.created_at is not None
    
    def test_chunk_metadata(self):
        """Test: Chunk-Metadaten werden korrekt gesetzt."""
        service = StructuredChunkingService()
        
        vision_data = {
            "pages": [
                {
                    "page_number": 1,
                    "content": {
                        "text": "Test Inhalt",
                        "tables": [],
                        "images": []
                    }
                }
            ]
        }
        
        chunks = service.create_chunks_from_vision_data(vision_data, document_id=1)
        
        for chunk in chunks:
            assert chunk.metadata.page_numbers == [1]
            assert chunk.metadata.chunk_type in ["text", "table", "image"]
            assert chunk.metadata.token_count is not None
            assert chunk.metadata.token_count > 0
