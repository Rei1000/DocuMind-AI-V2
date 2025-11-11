"""
TDD Tests für Fachartikel Chunking-Strategie

Tests für _chunk_research_article um sicherzustellen:
1. Die Strategie wird korrekt erkannt und aufgerufen
2. Strukturierte Texte (nicht JSON) werden erstellt
3. Figures und Tables werden in Chunks eingefügt
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from contexts.ragintegration.domain.entities import DocumentChunk
from contexts.ragintegration.domain.value_objects import ChunkMetadata
from contexts.ragintegration.infrastructure.services import DocumentTypeSpecificChunkingService


class TestResearchArticleChunking:
    """TDD Tests für Fachartikel Chunking-Strategie."""
    
    def test_chunking_strategy_recognized_for_fachartikel(self):
        """Test: _chunk_research_article wird für Fachartikel erkannt."""
        service = DocumentTypeSpecificChunkingService()
        
        # Mock: Aktiver Prompt mit sections + document_metadata
        with patch.object(service, '_get_active_standard_prompt') as mock_prompt:
            mock_prompt.return_value = {
                'name': 'Fachartikel Prompt',
                'prompt_text': '{"sections": [...], "document_metadata": {...}}',
                'status': 'active'
            }
            
            strategy = service.get_chunking_strategy_for_document_type("Fachartikel")
            
            # Prüfe dass _chunk_research_article zurückgegeben wird
            assert strategy == service._chunk_research_article
    
    def test_chunking_strategy_fallback_for_fachartikel(self):
        """Test: Fallback erkennt Fachartikel-Struktur in vision_data."""
        service = DocumentTypeSpecificChunkingService()
        
        # Vision-Daten mit Fachartikel-Struktur
        vision_data = {
            "document_metadata": {
                "title": "Test Artikel",
                "authors": [{"name": "Test Author"}]
            },
            "sections": [
                {
                    "section_number": 1,
                    "title": "Einleitung",
                    "content_summary": "Dies ist die Einleitung"
                }
            ]
        }
        
        # Mock: get_chunking_strategy_for_document_type gibt _chunk_generic_document zurück
        with patch.object(service, 'get_chunking_strategy_for_document_type') as mock_strategy:
            mock_strategy.return_value = service._chunk_generic_document
            
            # create_chunks_from_vision_data sollte Fallback-Logik verwenden
            chunks = service.create_chunks_from_vision_data(
                vision_data,
                document_id=1,
                document_type="Fachartikel",
                page_number=1
            )
            
            # Prüfe dass Chunks erstellt wurden (nicht leer)
            assert len(chunks) > 0
            # Prüfe dass es strukturierte Texte sind (nicht JSON)
            for chunk in chunks:
                assert not chunk.chunk_text.startswith('```json')
                assert not chunk.chunk_text.startswith('{')
    
    def test_chunk_research_article_creates_structured_text(self):
        """Test: _chunk_research_article erstellt strukturierte Texte (nicht JSON)."""
        service = DocumentTypeSpecificChunkingService()
        
        vision_data = {
            "document_metadata": {
                "title": "Methode zur effizienten Modellierung",
                "authors": [{"name": "A. Müller"}, {"name": "N. Lange"}],
                "journal": "BAUINGENIEUR",
                "year": "2020",
                "keywords": ["Stahlverbundbau", "Brandfall"]
            },
            "abstract": {
                "german": "Dies ist der deutsche Abstract",
                "english": "This is the English abstract"
            },
            "sections": [
                {
                    "section_number": 1,
                    "title": "Einleitung",
                    "content_summary": "Die Einleitung beschreibt..."
                }
            ]
        }
        
        chunks = service._chunk_research_article(vision_data, document_id=1, page_number=1)
        
        # Prüfe dass Chunks erstellt wurden
        assert len(chunks) > 0
        
        # Prüfe dass chunk_text strukturierte Texte sind (nicht JSON)
        for chunk in chunks:
            # KEIN JSON-Format
            assert not chunk.chunk_text.startswith('```json')
            assert not chunk.chunk_text.strip().startswith('{')
            # Sollte strukturierte Markdown-ähnliche Texte sein
            assert isinstance(chunk.chunk_text, str)
            assert len(chunk.chunk_text) > 0
            
            # Prüfe dass Metadaten korrekt sind
            assert chunk.metadata is not None
            assert chunk.metadata.chunk_type in ["metadata", "section", "findings", "software"]
    
    def test_chunk_research_article_includes_metadata_chunk(self):
        """Test: Metadata Chunk wird erstellt mit strukturierten Texten."""
        service = DocumentTypeSpecificChunkingService()
        
        vision_data = {
            "document_metadata": {
                "title": "Test Artikel",
                "authors": [{"name": "A. Müller"}, {"name": "N. Lange"}],
                "journal": "BAUINGENIEUR",
                "year": "2020"
            },
            "abstract": {
                "german": "Deutscher Abstract"
            }
        }
        
        chunks = service._chunk_research_article(vision_data, document_id=1, page_number=1)
        
        # Finde Metadata Chunk
        metadata_chunk = None
        for chunk in chunks:
            if chunk.metadata.chunk_type == "metadata":
                metadata_chunk = chunk
                break
        
        assert metadata_chunk is not None
        # Prüfe dass strukturierte Texte verwendet werden
        assert "Test Artikel" in metadata_chunk.chunk_text
        assert "A. Müller" in metadata_chunk.chunk_text or "Müller" in metadata_chunk.chunk_text
        assert "BAUINGENIEUR" in metadata_chunk.chunk_text
        assert "2020" in metadata_chunk.chunk_text
        # KEIN JSON
        assert not metadata_chunk.chunk_text.startswith('{')
    
    def test_chunk_research_article_includes_section_chunks(self):
        """Test: Section Chunks werden erstellt mit strukturierten Texten."""
        service = DocumentTypeSpecificChunkingService()
        
        vision_data = {
            "document_metadata": {
                "title": "Test Artikel"
            },
            "sections": [
                {
                    "section_number": 1,
                    "title": "Einleitung",
                    "content_summary": "Dies ist die Einleitung"
                },
                {
                    "section_number": 2,
                    "title": "Methoden",
                    "content_summary": "Dies sind die Methoden"
                }
            ]
        }
        
        chunks = service._chunk_research_article(vision_data, document_id=1, page_number=1)
        
        # Finde Section Chunks
        section_chunks = [c for c in chunks if c.metadata.chunk_type == "section"]
        assert len(section_chunks) >= 2
        
        # Prüfe dass strukturierte Texte verwendet werden
        for chunk in section_chunks:
            assert "Abschnitt" in chunk.chunk_text or "##" in chunk.chunk_text
            # KEIN JSON
            assert not chunk.chunk_text.startswith('{')
    
    def test_chunk_research_article_includes_figures(self):
        """Test: Figures werden in Section Chunks eingefügt."""
        service = DocumentTypeSpecificChunkingService()
        
        vision_data = {
            "document_metadata": {
                "title": "Test Artikel"
            },
            "sections": [
                {
                    "section_number": 1,
                    "title": "Einleitung",
                    "content_summary": "Dies ist die Einleitung",
                    "figures": [
                        {
                            "id": "fig1",
                            "caption": "Temperaturverlauf im Brandfall",
                            "description": "Zeigt die Temperaturverteilung über die Zeit",
                            "source": "Seite 3"
                        }
                    ]
                }
            ]
        }
        
        chunks = service._chunk_research_article(vision_data, document_id=1, page_number=1)
        
        # Finde Section Chunk mit Figure
        section_chunk = None
        for chunk in chunks:
            if chunk.metadata.chunk_type == "section":
                section_chunk = chunk
                break
        
        assert section_chunk is not None
        # Prüfe dass Figure-Beschreibung im chunk_text ist
        assert "Abbildung" in section_chunk.chunk_text or "Figure" in section_chunk.chunk_text or "fig1" in section_chunk.chunk_text
        assert "Temperaturverlauf" in section_chunk.chunk_text or "Temperatur" in section_chunk.chunk_text
    
    def test_chunk_research_article_includes_tables(self):
        """Test: Tables werden in Section Chunks eingefügt."""
        service = DocumentTypeSpecificChunkingService()
        
        vision_data = {
            "document_metadata": {
                "title": "Test Artikel"
            },
            "sections": [
                {
                    "section_number": 1,
                    "title": "Einleitung",
                    "content_summary": "Dies ist die Einleitung",
                    "tables": [
                        {
                            "id": "tab1",
                            "caption": "Materialeigenschaften",
                            "content_description": "Tabelle zeigt Materialeigenschaften",
                            "table_data": [
                                {
                                    "headers": ["Material", "Festigkeit"],
                                    "rows": [
                                        ["Stahl", "500 MPa"],
                                        ["Beton", "30 MPa"]
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        chunks = service._chunk_research_article(vision_data, document_id=1, page_number=1)
        
        # Finde Section Chunk mit Table
        section_chunk = None
        for chunk in chunks:
            if chunk.metadata.chunk_type == "section":
                section_chunk = chunk
                break
        
        assert section_chunk is not None
        # Prüfe dass Table-Beschreibung im chunk_text ist
        assert "Tabelle" in section_chunk.chunk_text or "Table" in section_chunk.chunk_text or "tab1" in section_chunk.chunk_text
        assert "Materialeigenschaften" in section_chunk.chunk_text or "Material" in section_chunk.chunk_text

