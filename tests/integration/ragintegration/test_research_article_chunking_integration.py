"""
Integration Tests für Fachartikel Chunking mit echten Daten

Testet den vollständigen Workflow:
1. Vision AI JSON (wie vom Upload)
2. Chunking mit _chunk_research_article
3. Strukturierte Texte (nicht JSON)
4. Figures und Tables in Chunks
"""
import pytest
from contexts.ragintegration.infrastructure.services import DocumentTypeSpecificChunkingService
from contexts.ragintegration.infrastructure.vision_extractor_adapter import VisionDataExtractorAdapter


class TestResearchArticleChunkingIntegration:
    """Integration Tests für Fachartikel Chunking mit echten Daten."""
    
    def test_fachartikel_chunking_with_real_structure(self):
        """Test: Fachartikel mit echter JSON-Struktur wird korrekt gechunkt."""
        service = DocumentTypeSpecificChunkingService()
        
        # Echte Vision AI JSON-Struktur (wie vom Upload)
        vision_data = {
            "document_metadata": {
                "title": "Methode zur effizienten Modellierung von Verbunddeckensystemen im Brandfall",
                "authors": [
                    {"name": "A. Müller", "affiliation": "TU München"},
                    {"name": "N. Lange", "affiliation": "TU München"}
                ],
                "journal": "BAUINGENIEUR",
                "volume": "95",
                "issue": "2",
                "year": "2020",
                "pages": "48-55",
                "keywords": ["Stahlverbundbau", "Brandfall", "Membranwirkung"]
            },
            "abstract": {
                "german": "Dieser Artikel beschreibt eine Methode zur Modellierung von Verbunddeckensystemen im Brandfall unter Berücksichtigung der Membranwirkung.",
                "english": "This article describes a method for modeling composite slab systems in fire considering membrane action."
            },
            "sections": [
                {
                    "section_number": 1,
                    "title": "Einleitung",
                    "content_summary": "Die Einleitung beschreibt die Bedeutung der Membranwirkung im Brandfall.",
                    "figures": [
                        {
                            "id": "fig1",
                            "caption": "Temperaturverlauf im Brandfall",
                            "description": "Zeigt die Temperaturverteilung über die Zeit für verschiedene Materialien",
                            "source": "Seite 3"
                        }
                    ],
                    "tables": [
                        {
                            "id": "tab1",
                            "caption": "Materialeigenschaften",
                            "content_description": "Tabelle zeigt Materialeigenschaften bei verschiedenen Temperaturen",
                            "table_data": [
                                {
                                    "headers": ["Material", "Festigkeit [MPa]", "Temperatur [°C]"],
                                    "rows": [
                                        ["Stahl", "500", "20"],
                                        ["Stahl", "400", "400"],
                                        ["Beton", "30", "20"]
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "section_number": 2,
                    "title": "Methoden",
                    "content_summary": "Beschreibung der verwendeten Berechnungsmethoden.",
                    "methods": [
                        {
                            "name": "Geometrisch nicht-lineare Berechnung",
                            "description": "Berücksichtigt große Verformungen",
                            "software_used": "ANSYS",
                            "standards": [
                                {"standard": "Eurocode 1", "title": "Teil 1-2", "section": "4.2"}
                            ]
                        }
                    ]
                }
            ],
            "key_findings": [
                "Membranwirkung erhöht Tragfähigkeit um 30%",
                "Temperaturverteilung ist nicht-linear"
            ]
        }
        
        # Test: Chunking
        chunks = service._chunk_research_article(vision_data, document_id=1, page_number=1)
        
        # Prüfe dass Chunks erstellt wurden
        assert len(chunks) > 0
        
        # Prüfe dass strukturierte Texte verwendet werden (nicht JSON)
        for chunk in chunks:
            assert not chunk.chunk_text.startswith('```json')
            assert not chunk.chunk_text.strip().startswith('{')
            assert isinstance(chunk.chunk_text, str)
            assert len(chunk.chunk_text) > 0
        
        # Prüfe dass Metadata Chunk existiert
        metadata_chunks = [c for c in chunks if c.metadata.chunk_type == "metadata"]
        assert len(metadata_chunks) > 0
        metadata_chunk = metadata_chunks[0]
        assert "Methode zur effizienten Modellierung" in metadata_chunk.chunk_text
        assert "A. Müller" in metadata_chunk.chunk_text or "Müller" in metadata_chunk.chunk_text
        assert "BAUINGENIEUR" in metadata_chunk.chunk_text
        
        # Prüfe dass Section Chunks existieren
        section_chunks = [c for c in chunks if c.metadata.chunk_type == "section"]
        assert len(section_chunks) >= 2
        
        # Prüfe dass Figures in Section Chunks eingefügt sind
        einleitung_chunk = None
        for chunk in section_chunks:
            if "Einleitung" in chunk.chunk_text:
                einleitung_chunk = chunk
                break
        assert einleitung_chunk is not None
        assert "Abbildung" in einleitung_chunk.chunk_text or "fig1" in einleitung_chunk.chunk_text
        assert "Temperaturverlauf" in einleitung_chunk.chunk_text or "Temperatur" in einleitung_chunk.chunk_text
        
        # Prüfe dass Tables in Section Chunks eingefügt sind
        assert "Tabelle" in einleitung_chunk.chunk_text or "tab1" in einleitung_chunk.chunk_text
        assert "Materialeigenschaften" in einleitung_chunk.chunk_text or "Material" in einleitung_chunk.chunk_text
    
    def test_fachartikel_chunking_with_merged_json(self):
        """Test: Fachartikel mit zusammengeführtem JSON (mehrere Seiten) wird korrekt gechunkt."""
        extractor = VisionDataExtractorAdapter()
        
        # Simuliere Vision-Daten von mehreren Seiten (wie vom Upload)
        vision_data_list = [
            {
                "page_number": 1,
                "json_response": {
                    "document_metadata": {
                        "title": "Test Artikel",
                        "authors": [{"name": "Test Author"}]
                    },
                    "abstract": {
                        "german": "Deutscher Abstract"
                    }
                }
            },
            {
                "page_number": 2,
                "json_response": {
                    "sections": [
                        {
                            "section_number": 1,
                            "title": "Einleitung",
                            "content_summary": "Dies ist die Einleitung"
                        }
                    ]
                }
            }
        ]
        
        # Test: extract_chunks_from_vision_data sollte zusammenführen
        chunks = extractor.extract_chunks_from_vision_data(
            vision_data_list,
            document_id=1,
            document_type="Fachartikel"
        )
        
        # Prüfe dass Chunks erstellt wurden
        assert len(chunks) > 0
        
        # Prüfe dass strukturierte Texte verwendet werden
        for chunk in chunks:
            assert not chunk.chunk_text.startswith('```json')
            assert not chunk.chunk_text.strip().startswith('{')
    
    def test_fachartikel_chunking_fallback_detection(self):
        """Test: Fallback-Logik erkennt Fachartikel-Struktur auch ohne Prompt."""
        service = DocumentTypeSpecificChunkingService()
        
        # Vision-Daten mit Fachartikel-Struktur (ohne dass Prompt erkannt wird)
        vision_data = {
            "document_metadata": {
                "title": "Test Artikel"
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
        # (simuliert dass Prompt nicht erkannt wurde)
        with pytest.MonkeyPatch().context() as m:
            m.setattr(service, 'get_chunking_strategy_for_document_type', 
                     lambda doc_type: service._chunk_generic_document)
            
            # create_chunks_from_vision_data sollte Fallback-Logik verwenden
            chunks = service.create_chunks_from_vision_data(
                vision_data,
                document_id=1,
                document_type="Fachartikel",
                page_number=1
            )
            
            # Prüfe dass Chunks erstellt wurden
            assert len(chunks) > 0
            
            # Prüfe dass strukturierte Texte verwendet werden (nicht JSON)
            for chunk in chunks:
                assert not chunk.chunk_text.startswith('```json')
                assert not chunk.chunk_text.strip().startswith('{')

