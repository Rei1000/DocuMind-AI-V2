"""
Integration Tests für RAG Infrastructure Layer - Vision Data Extractor Adapter

Diese Tests prüfen die Integration mit Vision AI Services für strukturierte Datenextraktion.
Sie verwenden echte AI-Services für realistische Tests.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any

# Import Domain Entities
from contexts.ragintegration.domain.entities import DocumentChunk
from contexts.ragintegration.domain.value_objects import ChunkMetadata

# Import Infrastructure
from contexts.ragintegration.infrastructure.vision_extractor_adapter import VisionDataExtractorAdapter


class TestVisionDataExtractorAdapterIntegration:
    """Integration Tests für Vision Data Extractor Adapter"""
    
    @pytest.fixture
    def vision_extractor(self):
        """Erstelle Vision Data Extractor Adapter für Tests"""
        return VisionDataExtractorAdapter()
    
    @pytest.fixture
    def sample_vision_data(self):
        """Erstelle Sample Vision AI Data für Tests"""
        return {
            "sections": [
                {
                    "heading": "1. Einleitung",
                    "content": "Dies ist die Einleitung zur Montage-Anweisung.",
                    "start_page": 1,
                    "end_page": 1,
                    "confidence": 0.95
                },
                {
                    "heading": "2. Montage-Schritte",
                    "content": "Die Montage erfolgt in folgenden Schritten:",
                    "start_page": 2,
                    "end_page": 3,
                    "confidence": 0.9
                },
                {
                    "heading": "2.1 Werkzeuge",
                    "content": "Benötigte Werkzeuge: Schraubendreher, Zange, Hammer",
                    "start_page": 2,
                    "end_page": 2,
                    "confidence": 0.85
                },
                {
                    "heading": "2.2 Sicherheit",
                    "content": "Wichtige Sicherheitshinweise: Schutzbrille tragen",
                    "start_page": 3,
                    "end_page": 3,
                    "confidence": 0.98
                }
            ],
            "tables": [
                {
                    "title": "Werkzeug-Liste",
                    "data": [
                        ["Werkzeug", "Anzahl", "Verwendung"],
                        ["Schraubendreher", "2", "Schrauben anziehen"],
                        ["Zange", "1", "Teile halten"],
                        ["Hammer", "1", "Nieten einschlagen"]
                    ],
                    "page": 2,
                    "confidence": 0.92
                }
            ],
            "lists": [
                {
                    "title": "Sicherheitshinweise",
                    "items": [
                        "Schutzbrille tragen",
                        "Handschuhe verwenden",
                        "Arbeitsplatz sauber halten"
                    ],
                    "page": 3,
                    "confidence": 0.96
                }
            ],
            "metadata": {
                "document_type": "Arbeitsanweisung",
                "total_pages": 3,
                "processing_confidence": 0.94,
                "extraction_method": "vision_ai"
            }
        }
    
    def test_extract_structured_data_from_vision_ai(self, vision_extractor, sample_vision_data):
        """Test Extraktion von strukturierten Daten aus Vision AI Response"""
        # Mock AI Service Response
        mock_ai_response = {
            "content": f"Strukturierte Daten: {sample_vision_data}",
            "model": "gpt-4o-mini",
            "tokens_used": 150
        }
        
        with patch.object(vision_extractor.ai_service, 'generate_response') as mock_generate:
            mock_generate.return_value = mock_ai_response
            
            result = vision_extractor.extract_structured_data_from_vision_ai(
                document_id=123,
                page_number=1,
                image_path="test/image.jpg"
            )
            
            assert result is not None
            assert "sections" in result
            assert "tables" in result
            assert "lists" in result
            assert "metadata" in result
            
            # Prüfe Sections
            assert len(result["sections"]) == 4
            assert result["sections"][0]["heading"] == "1. Einleitung"
            assert result["sections"][0]["confidence"] == 0.95
            
            # Prüfe Tables
            assert len(result["tables"]) == 1
            assert result["tables"][0]["title"] == "Werkzeug-Liste"
            assert len(result["tables"][0]["data"]) == 4
            
            # Prüfe Lists
            assert len(result["lists"]) == 1
            assert result["lists"][0]["title"] == "Sicherheitshinweise"
            assert len(result["lists"][0]["items"]) == 3
    
    def test_extract_structured_data_with_invalid_json(self, vision_extractor):
        """Test Extraktion mit ungültigem JSON"""
        # Mock AI Service Response mit ungültigem JSON
        mock_ai_response = {
            "content": "Dies ist kein gültiges JSON",
            "model": "gpt-4o-mini",
            "tokens_used": 50
        }
        
        with patch.object(vision_extractor.ai_service, 'generate_response') as mock_generate:
            mock_generate.return_value = mock_ai_response
            
            with pytest.raises(Exception, match="No JSON found"):
                vision_extractor.extract_structured_data_from_vision_ai(
                    document_id=123,
                    page_number=1,
                    image_path="test/image.jpg"
                )
    
    def test_extract_structured_data_with_partial_json(self, vision_extractor):
        """Test Extraktion mit teilweisem JSON"""
        # Mock AI Service Response mit teilweisem JSON
        partial_json = '{"sections": [{"heading": "Test", "content": "Test content"}]}'
        mock_ai_response = {
            "content": f"Hier sind die Daten: {partial_json} und weitere Informationen.",
            "model": "gpt-4o-mini",
            "tokens_used": 100
        }
        
        with patch.object(vision_extractor.ai_service, 'generate_response') as mock_generate:
            mock_generate.return_value = mock_ai_response
            
            result = vision_extractor.extract_structured_data_from_vision_ai(
                document_id=123,
                page_number=1,
                image_path="test/image.jpg"
            )
            
            assert result is not None
            assert "sections" in result
            assert len(result["sections"]) == 1
            assert result["sections"][0]["heading"] == "Test"
    
    def test_extract_structured_data_with_empty_response(self, vision_extractor):
        """Test Extraktion mit leerer AI Response"""
        # Mock AI Service Response mit leerem Content
        mock_ai_response = {
            "content": "",
            "model": "gpt-4o-mini",
            "tokens_used": 0
        }
        
        with patch.object(vision_extractor.ai_service, 'generate_response') as mock_generate:
            mock_generate.return_value = mock_ai_response
            
            with pytest.raises(Exception, match="No JSON found"):
                vision_extractor.extract_structured_data_from_vision_ai(
                    document_id=123,
                    page_number=1,
                    image_path="test/image.jpg"
                )
    
    def test_extract_structured_data_with_api_error(self, vision_extractor):
        """Test Extraktion mit API-Fehler"""
        with patch.object(vision_extractor.ai_service, 'generate_response') as mock_generate:
            mock_generate.side_effect = Exception("API Error")
            
            with pytest.raises(Exception, match="API Error"):
                vision_extractor.extract_structured_data_from_vision_ai(
                    document_id=123,
                    page_number=1,
                    image_path="test/image.jpg"
                )
    
    def test_extract_structured_data_with_missing_fields(self, vision_extractor):
        """Test Extraktion mit fehlenden Feldern"""
        # Mock AI Service Response mit unvollständigen Daten
        incomplete_data = {
            "sections": [
                {
                    "heading": "Test Section",
                    "content": "Test content"
                    # Fehlende Felder: start_page, end_page, confidence
                }
            ]
            # Fehlende Felder: tables, lists, metadata
        }
        
        mock_ai_response = {
            "content": f"Strukturierte Daten: {incomplete_data}",
            "model": "gpt-4o-mini",
            "tokens_used": 80
        }
        
        with patch.object(vision_extractor.ai_service, 'generate_response') as mock_generate:
            mock_generate.return_value = mock_ai_response
            
            result = vision_extractor.extract_structured_data_from_vision_ai(
                document_id=123,
                page_number=1,
                image_path="test/image.jpg"
            )
            
            assert result is not None
            assert "sections" in result
            assert len(result["sections"]) == 1
            
            # Prüfe dass fehlende Felder mit Default-Werten gefüllt werden
            section = result["sections"][0]
            assert section["start_page"] == 1  # Default-Wert
            assert section["end_page"] == 1     # Default-Wert
            assert section["confidence"] == 0.8  # Default-Wert
    
    def test_extract_structured_data_with_complex_tables(self, vision_extractor):
        """Test Extraktion mit komplexen Tabellen"""
        complex_data = {
            "tables": [
                {
                    "title": "Komplexe Tabelle",
                    "data": [
                        ["Spalte 1", "Spalte 2", "Spalte 3", "Spalte 4"],
                        ["Wert 1", "Wert 2", "Wert 3", "Wert 4"],
                        ["Wert 5", "Wert 6", "Wert 7", "Wert 8"],
                        ["Wert 9", "Wert 10", "Wert 11", "Wert 12"]
                    ],
                    "page": 1,
                    "confidence": 0.95
                }
            ],
            "sections": [],
            "lists": [],
            "metadata": {
                "document_type": "Test",
                "total_pages": 1,
                "processing_confidence": 0.95,
                "extraction_method": "vision_ai"
            }
        }
        
        mock_ai_response = {
            "content": f"Strukturierte Daten: {complex_data}",
            "model": "gpt-4o-mini",
            "tokens_used": 120
        }
        
        with patch.object(vision_extractor.ai_service, 'generate_response') as mock_generate:
            mock_generate.return_value = mock_ai_response
            
            result = vision_extractor.extract_structured_data_from_vision_ai(
                document_id=123,
                page_number=1,
                image_path="test/image.jpg"
            )
            
            assert result is not None
            assert "tables" in result
            assert len(result["tables"]) == 1
            
            table = result["tables"][0]
            assert table["title"] == "Komplexe Tabelle"
            assert len(table["data"]) == 4
            assert len(table["data"][0]) == 4  # 4 Spalten
            assert table["confidence"] == 0.95
    
    def test_extract_structured_data_with_nested_lists(self, vision_extractor):
        """Test Extraktion mit verschachtelten Listen"""
        nested_data = {
            "lists": [
                {
                    "title": "Hauptliste",
                    "items": [
                        "Punkt 1",
                        "Punkt 2",
                        "Punkt 3"
                    ],
                    "page": 1,
                    "confidence": 0.9
                },
                {
                    "title": "Unterliste",
                    "items": [
                        "Unterpunkt 1",
                        "Unterpunkt 2"
                    ],
                    "page": 1,
                    "confidence": 0.85
                }
            ],
            "sections": [],
            "tables": [],
            "metadata": {
                "document_type": "Test",
                "total_pages": 1,
                "processing_confidence": 0.9,
                "extraction_method": "vision_ai"
            }
        }
        
        mock_ai_response = {
            "content": f"Strukturierte Daten: {nested_data}",
            "model": "gpt-4o-mini",
            "tokens_used": 100
        }
        
        with patch.object(vision_extractor.ai_service, 'generate_response') as mock_generate:
            mock_generate.return_value = mock_ai_response
            
            result = vision_extractor.extract_structured_data_from_vision_ai(
                document_id=123,
                page_number=1,
                image_path="test/image.jpg"
            )
            
            assert result is not None
            assert "lists" in result
            assert len(result["lists"]) == 2
            
            assert result["lists"][0]["title"] == "Hauptliste"
            assert len(result["lists"][0]["items"]) == 3
            assert result["lists"][1]["title"] == "Unterliste"
            assert len(result["lists"][1]["items"]) == 2
    
    def test_extract_structured_data_performance(self, vision_extractor):
        """Test Performance der Datenextraktion"""
        # Mock AI Service Response
        mock_ai_response = {
            "content": "Strukturierte Daten: {'sections': [], 'tables': [], 'lists': [], 'metadata': {}}",
            "model": "gpt-4o-mini",
            "tokens_used": 50
        }
        
        with patch.object(vision_extractor.ai_service, 'generate_response') as mock_generate:
            mock_generate.return_value = mock_ai_response
            
            import time
            start_time = time.time()
            
            # Führe mehrere Extraktionen durch
            for i in range(10):
                result = vision_extractor.extract_structured_data_from_vision_ai(
                    document_id=i,
                    page_number=1,
                    image_path=f"test/image_{i}.jpg"
                )
                assert result is not None
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Performance sollte unter 5 Sekunden liegen
            assert duration < 5.0, f"Extraction took {duration} seconds"
    
    def test_extract_structured_data_with_different_models(self, vision_extractor):
        """Test Extraktion mit verschiedenen AI-Modellen"""
        models = ["gpt-4o-mini", "gpt-5-mini", "gemini-2.5-flash"]
        
        for model in models:
            mock_ai_response = {
                "content": f"Strukturierte Daten: {{'sections': [], 'tables': [], 'lists': [], 'metadata': {{'model': '{model}'}}}}",
                "model": model,
                "tokens_used": 50
            }
            
            with patch.object(vision_extractor.ai_service, 'generate_response') as mock_generate:
                mock_generate.return_value = mock_ai_response
                
                result = vision_extractor.extract_structured_data_from_vision_ai(
                    document_id=123,
                    page_number=1,
                    image_path="test/image.jpg"
                )
                
                assert result is not None
                assert "metadata" in result
                assert result["metadata"]["model"] == model
    
    def test_extract_structured_data_with_confidence_scores(self, vision_extractor):
        """Test Extraktion mit Confidence Scores"""
        confidence_data = {
            "sections": [
                {
                    "heading": "High Confidence Section",
                    "content": "Clear text content",
                    "start_page": 1,
                    "end_page": 1,
                    "confidence": 0.98
                },
                {
                    "heading": "Low Confidence Section",
                    "content": "Blurry text content",
                    "start_page": 2,
                    "end_page": 2,
                    "confidence": 0.65
                }
            ],
            "tables": [],
            "lists": [],
            "metadata": {
                "document_type": "Test",
                "total_pages": 2,
                "processing_confidence": 0.82,
                "extraction_method": "vision_ai"
            }
        }
        
        mock_ai_response = {
            "content": f"Strukturierte Daten: {confidence_data}",
            "model": "gpt-4o-mini",
            "tokens_used": 100
        }
        
        with patch.object(vision_extractor.ai_service, 'generate_response') as mock_generate:
            mock_generate.return_value = mock_ai_response
            
            result = vision_extractor.extract_structured_data_from_vision_ai(
                document_id=123,
                page_number=1,
                image_path="test/image.jpg"
            )
            
            assert result is not None
            assert "sections" in result
            assert len(result["sections"]) == 2
            
            # Prüfe Confidence Scores
            high_conf_section = result["sections"][0]
            low_conf_section = result["sections"][1]
            
            assert high_conf_section["confidence"] == 0.98
            assert low_conf_section["confidence"] == 0.65
            assert result["metadata"]["processing_confidence"] == 0.82
    
    def test_extract_structured_data_with_page_boundaries(self, vision_extractor):
        """Test Extraktion mit Seiten-Grenzen"""
        page_boundary_data = {
            "sections": [
                {
                    "heading": "Multi-Page Section",
                    "content": "This section spans multiple pages",
                    "start_page": 1,
                    "end_page": 3,
                    "confidence": 0.9
                },
                {
                    "heading": "Single Page Section",
                    "content": "This section is on one page",
                    "start_page": 4,
                    "end_page": 4,
                    "confidence": 0.95
                }
            ],
            "tables": [],
            "lists": [],
            "metadata": {
                "document_type": "Test",
                "total_pages": 4,
                "processing_confidence": 0.92,
                "extraction_method": "vision_ai"
            }
        }
        
        mock_ai_response = {
            "content": f"Strukturierte Daten: {page_boundary_data}",
            "model": "gpt-4o-mini",
            "tokens_used": 100
        }
        
        with patch.object(vision_extractor.ai_service, 'generate_response') as mock_generate:
            mock_generate.return_value = mock_ai_response
            
            result = vision_extractor.extract_structured_data_from_vision_ai(
                document_id=123,
                page_number=1,
                image_path="test/image.jpg"
            )
            
            assert result is not None
            assert "sections" in result
            assert len(result["sections"]) == 2
            
            # Prüfe Seiten-Grenzen
            multi_page_section = result["sections"][0]
            single_page_section = result["sections"][1]
            
            assert multi_page_section["start_page"] == 1
            assert multi_page_section["end_page"] == 3
            assert single_page_section["start_page"] == 4
            assert single_page_section["end_page"] == 4
