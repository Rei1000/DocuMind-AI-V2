"""
Performance Tests für Chunking-Strategien

Testet Performance-Metriken:
1. Chunking-Geschwindigkeit
2. Token-Verbrauch (vorher/nachher)
3. Chunk-Größe (strukturierte Texte vs. JSON)
"""
import pytest
import time
from contexts.ragintegration.infrastructure.services import DocumentTypeSpecificChunkingService


class TestChunkingPerformance:
    """Performance Tests für Chunking-Strategien."""
    
    def test_chunking_performance_fachartikel(self):
        """Test: Performance-Metriken für Fachartikel Chunking."""
        service = DocumentTypeSpecificChunkingService()
        
        # Große Vision-Daten (simuliert echtes Dokument)
        vision_data = {
            "document_metadata": {
                "title": "Test Artikel",
                "authors": [{"name": "Test Author"}],
                "journal": "Test Journal",
                "year": "2020"
            },
            "abstract": {
                "german": "Dies ist ein langer Abstract. " * 50  # ~2000 Zeichen
            },
            "sections": [
                {
                    "section_number": i,
                    "title": f"Abschnitt {i}",
                    "content_summary": f"Dies ist der Inhalt von Abschnitt {i}. " * 100,  # ~2000 Zeichen pro Section
                    "figures": [
                        {
                            "id": f"fig{i}",
                            "caption": f"Abbildung {i}",
                            "description": f"Beschreibung von Abbildung {i}",
                            "source": f"Seite {i}"
                        }
                    ] if i % 2 == 0 else [],
                    "tables": [
                        {
                            "id": f"tab{i}",
                            "caption": f"Tabelle {i}",
                            "content_description": f"Beschreibung von Tabelle {i}",
                            "table_data": [
                                {
                                    "headers": ["Spalte 1", "Spalte 2"],
                                    "rows": [["Wert 1", "Wert 2"]] * 10
                                }
                            ]
                        }
                    ] if i % 3 == 0 else []
                }
                for i in range(1, 11)  # 10 Sections
            ]
        }
        
        # Messung: Chunking-Zeit
        start_time = time.time()
        chunks = service._chunk_research_article(vision_data, document_id=1, page_number=1)
        end_time = time.time()
        chunking_time = end_time - start_time
        
        # Prüfe dass Chunking schnell genug ist (< 1 Sekunde für 10 Sections)
        assert chunking_time < 1.0, f"Chunking dauerte {chunking_time:.2f}s (erwartet < 1.0s)"
        
        # Prüfe dass Chunks erstellt wurden
        assert len(chunks) > 0
        
        # Messung: Token-Verbrauch (Schätzung basierend auf Zeichen)
        total_chars = sum(len(chunk.chunk_text) for chunk in chunks)
        estimated_tokens = total_chars / 4  # ~4 Zeichen pro Token
        
        # Prüfe dass Token-Verbrauch reduziert wurde (strukturierte Texte statt JSON)
        # JSON würde ~27.000 Tokens haben (14.000 Zeichen * 2 für JSON-Struktur)
        # Strukturierte Texte sollten deutlich weniger sein (~10.000 Tokens = ~63% Reduktion)
        assert estimated_tokens < 15000, f"Token-Verbrauch zu hoch: {estimated_tokens:.0f} Tokens (erwartet < 15000, JSON würde ~27000 haben)"
        
        # Prüfe dass Chunk-Größen angemessen sind (nicht zu groß)
        max_chunk_size = max(len(chunk.chunk_text) for chunk in chunks)
        assert max_chunk_size < 10000, f"Chunk zu groß: {max_chunk_size} Zeichen (erwartet < 10000)"
        
        # Prüfe dass keine JSON-Struktur gespeichert wurde
        for chunk in chunks:
            assert not chunk.chunk_text.startswith('```json')
            assert not chunk.chunk_text.strip().startswith('{')
    
    def test_chunking_token_optimization(self):
        """Test: Token-Optimierung durch strukturierte Texte."""
        service = DocumentTypeSpecificChunkingService()
        
        # Vision-Daten mit großem JSON (wie vorher)
        vision_data = {
            "document_metadata": {
                "title": "Test Artikel",
                "authors": [{"name": "Test Author"}]
            },
            "sections": [
                {
                    "section_number": 1,
                    "title": "Einleitung",
                    "content_summary": "Dies ist die Einleitung. " * 200  # ~4000 Zeichen
                }
            ]
        }
        
        chunks = service._chunk_research_article(vision_data, document_id=1, page_number=1)
        
        # Prüfe dass strukturierte Texte verwendet werden (nicht JSON)
        total_chars = sum(len(chunk.chunk_text) for chunk in chunks)
        
        # JSON würde ~8000 Zeichen haben (mit Struktur und Overhead)
        # Strukturierte Texte sollten ähnlich oder weniger sein (~5000 Zeichen)
        # WICHTIG: Hauptvorteil ist dass es strukturierte Texte sind, nicht JSON
        assert total_chars < 6000, f"Chunk-Größe zu groß: {total_chars} Zeichen (erwartet < 6000)"
        
        # Prüfe dass keine JSON-Struktur gespeichert wurde
        for chunk in chunks:
            assert not chunk.chunk_text.startswith('```json')
            assert not chunk.chunk_text.strip().startswith('{')

