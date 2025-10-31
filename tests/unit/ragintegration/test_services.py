"""
Unit Tests für RAG Integration Application Services.

TDD Approach: Diese Tests werden ZUERST geschrieben, dann die Services implementiert.
"""

import pytest
from unittest.mock import Mock
from typing import List, Dict, Any

from contexts.ragintegration.application.services import (
    HeadingAwareChunkingService,
    MultiQueryService,
    StructuredDataExtractorService
)
from contexts.ragintegration.domain.entities import DocumentChunk
from contexts.ragintegration.domain.value_objects import ChunkMetadata


class TestHeadingAwareChunkingService:
    """Tests für HeadingAwareChunkingService."""
    
    def test_create_chunks_from_vision_ai_data(self):
        """Test: Erstelle Chunks aus Vision AI JSON-Daten."""
        # Arrange
        mock_vision_extractor = Mock()
        mock_ai_service = Mock()
        
        # Mock Vision AI JSON Response
        vision_ai_data = {
            "text": "1. Arbeitsanweisung\n\n1.1 Vorbereitung\nBereite alle Werkzeuge vor.\n\n1.2 Durchführung\nFühre die Arbeit durch.\n\n2. Sicherheitshinweise\n\nBeachte alle Sicherheitsregeln.",
            "structure": {
                "headings": [
                    {"level": 1, "text": "Arbeitsanweisung", "start": 0, "end": 100},
                    {"level": 2, "text": "Vorbereitung", "start": 100, "end": 200},
                    {"level": 2, "text": "Durchführung", "start": 200, "end": 300},
                    {"level": 1, "text": "Sicherheitshinweise", "start": 300, "end": 400}
                ]
            }
        }
        
        mock_vision_extractor.extract_structured_data.return_value = vision_ai_data
        
        service = HeadingAwareChunkingService(
            vision_extractor=mock_vision_extractor,
            ai_service=mock_ai_service
        )
        
        # Mock Document Pages
        mock_pages = [
            Mock(
                id=1,
                page_number=1,
                ai_processing_result=Mock(json_response=str(vision_ai_data))
            )
        ]
        
        # Act
        chunks = service.create_chunks(
            document_id=42,
            pages=mock_pages,
            document_type_id=1
        )
        
        # Assert
        assert len(chunks) > 0
        
        # Verify chunk structure
        for chunk in chunks:
            assert isinstance(chunk, DocumentChunk)
            assert chunk.chunk_text is not None
            assert chunk.metadata is not None
            assert chunk.metadata.document_type_id == 1
        
        mock_vision_extractor.extract_structured_data.assert_called_once()
    
    def test_create_chunks_with_page_boundaries(self):
        """Test: Chunking mit Seitenübergängen."""
        # Arrange
        mock_vision_extractor = Mock()
        mock_ai_service = Mock()
        
        # Mock Multi-Page Data
        page1_data = {
            "text": "1. Arbeitsanweisung\n\n1.1 Vorbereitung\nBereite alle Werkzeuge vor.",
            "structure": {"headings": [{"level": 1, "text": "Arbeitsanweisung", "start": 0, "end": 50}]}
        }
        
        page2_data = {
            "text": "1.2 Durchführung\nFühre die Arbeit durch.\n\n2. Sicherheitshinweise",
            "structure": {"headings": [{"level": 2, "text": "Durchführung", "start": 0, "end": 30}]}
        }
        
        mock_vision_extractor.extract_structured_data.side_effect = [page1_data, page2_data]
        
        service = HeadingAwareChunkingService(
            vision_extractor=mock_vision_extractor,
            ai_service=mock_ai_service
        )
        
        # Mock Multi-Page Document
        mock_pages = [
            Mock(
                id=1,
                page_number=1,
                ai_processing_result=Mock(json_response=str(page1_data))
            ),
            Mock(
                id=2,
                page_number=2,
                ai_processing_result=Mock(json_response=str(page2_data))
            )
        ]
        
        # Act
        chunks = service.create_chunks(
            document_id=42,
            pages=mock_pages,
            document_type_id=1
        )
        
        # Assert
        assert len(chunks) > 0
        
        # Check for multi-page chunks
        multi_page_chunks = [chunk for chunk in chunks if chunk.metadata.is_multi_page()]
        assert len(multi_page_chunks) > 0  # Should have chunks spanning pages
    
    def test_create_chunks_fallback_to_plain_text(self):
        """Test: Fallback zu Plain Text wenn keine Vision AI Daten."""
        # Arrange
        mock_vision_extractor = Mock()
        mock_ai_service = Mock()
        
        # Mock Fallback: No Vision AI Data
        mock_vision_extractor.extract_structured_data.return_value = None
        
        service = HeadingAwareChunkingService(
            vision_extractor=mock_vision_extractor,
            ai_service=mock_ai_service
        )
        
        # Mock Pages without AI Processing
        mock_pages = [
            Mock(
                id=1,
                page_number=1,
                ai_processing_result=None
            )
        ]
        
        # Act
        chunks = service.create_chunks(
            document_id=42,
            pages=mock_pages,
            document_type_id=1
        )
        
        # Assert
        assert len(chunks) > 0
        
        # Should still create chunks from plain text
        for chunk in chunks:
            assert chunk.chunk_text is not None
            assert chunk.metadata.chunk_type == "text"


class TestMultiQueryService:
    """Tests für MultiQueryService."""
    
    def test_generate_queries_success(self):
        """Test: Erfolgreiche Generierung von Query-Varianten."""
        # Arrange
        mock_ai_service = Mock()
        
        mock_ai_service.generate_response.return_value = """1. Welche Sicherheitshinweise gibt es?
2. Welche Sicherheitsregeln sind zu beachten?
3. Was sind die wichtigsten Sicherheitsmaßnahmen?"""
        
        service = MultiQueryService(ai_service=mock_ai_service)
        
        # Act
        queries = service.generate_queries("Welche Sicherheitshinweise gibt es?")
        
        # Assert
        assert len(queries) >= 3
        assert "Sicherheitshinweise" in queries[0]
        assert "Sicherheitsregeln" in queries[1]
        assert "Sicherheitsmaßnahmen" in queries[2]
        
        mock_ai_service.generate_response.assert_called_once()
    
    def test_generate_queries_empty_input(self):
        """Test: Fehler bei leerer Eingabe."""
        # Arrange
        mock_ai_service = Mock()
        
        service = MultiQueryService(ai_service=mock_ai_service)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Query cannot be empty"):
            service.generate_queries("")
    
    def test_generate_queries_ai_service_error(self):
        """Test: Fehler bei AI Service."""
        # Arrange
        mock_ai_service = Mock()
        mock_ai_service.generate_response.side_effect = Exception("AI Service Error")
        
        service = MultiQueryService(ai_service=mock_ai_service)
        
        # Act & Assert
        with pytest.raises(Exception, match="AI Service Error"):
            service.generate_queries("Test query")


class TestStructuredDataExtractorService:
    """Tests für StructuredDataExtractorService."""
    
    def test_extract_material_list_success(self):
        """Test: Erfolgreiche Extraktion von Materiallisten."""
        # Arrange
        mock_ai_service = Mock()
        
        mock_ai_response = """{
            "material_list": [
                {"artikel_nr": "ABC123", "bezeichnung": "Schraube M6", "menge": "4 Stück"},
                {"artikel_nr": "DEF456", "bezeichnung": "Mutter M6", "menge": "4 Stück"}
            ]
        }"""
        
        mock_ai_service.generate_response.return_value = mock_ai_response
        
        service = StructuredDataExtractorService(ai_service=mock_ai_service)
        
        # Act
        result = service.extract_material_list("Bereite alle Materialien vor: Schraube M6, Mutter M6")
        
        # Assert
        assert result is not None
        assert "material_list" in result
        assert len(result["material_list"]) == 2
        assert result["material_list"][0]["artikel_nr"] == "ABC123"
        assert result["material_list"][0]["bezeichnung"] == "Schraube M6"
        
        mock_ai_service.generate_response.assert_called_once()
    
    def test_extract_safety_instructions_success(self):
        """Test: Erfolgreiche Extraktion von Sicherheitshinweisen."""
        # Arrange
        mock_ai_service = Mock()
        
        mock_ai_response = """{
            "safety_instructions": [
                {"kategorie": "Schutzausrüstung", "beschreibung": "Sicherheitsschuhe tragen", "priorität": "Hoch"},
                {"kategorie": "Werkzeuge", "beschreibung": "Werkzeuge vor Gebrauch prüfen", "priorität": "Mittel"}
            ]
        }"""
        
        mock_ai_service.generate_response.return_value = mock_ai_response
        
        service = StructuredDataExtractorService(ai_service=mock_ai_service)
        
        # Act
        result = service.extract_safety_instructions("Beachte alle Sicherheitsregeln: Sicherheitsschuhe tragen, Werkzeuge prüfen")
        
        # Assert
        assert result is not None
        assert "safety_instructions" in result
        assert len(result["safety_instructions"]) == 2
        assert result["safety_instructions"][0]["priorität"] == "Hoch"
        
        mock_ai_service.generate_response.assert_called_once()
    
    def test_extract_work_steps_success(self):
        """Test: Erfolgreiche Extraktion von Arbeitsschritten."""
        # Arrange
        mock_ai_service = Mock()
        
        mock_ai_response = """{
            "work_steps": [
                {"nummer": 1, "beschreibung": "Werkzeuge bereitstellen", "dauer": "5 Min", "werkzeuge": ["Schraubendreher", "Schrauben"]},
                {"nummer": 2, "beschreibung": "Teile zusammenfügen", "dauer": "15 Min", "werkzeuge": ["Schraubendreher"]}
            ]
        }"""
        
        mock_ai_service.generate_response.return_value = mock_ai_response
        
        service = StructuredDataExtractorService(ai_service=mock_ai_service)
        
        # Act
        result = service.extract_work_steps("1. Werkzeuge bereitstellen\n2. Teile zusammenfügen")
        
        # Assert
        assert result is not None
        assert "work_steps" in result
        assert len(result["work_steps"]) == 2
        assert result["work_steps"][0]["nummer"] == 1
        assert result["work_steps"][0]["dauer"] == "5 Min"
        
        mock_ai_service.generate_response.assert_called_once()
    
    def test_extract_structured_data_invalid_json(self):
        """Test: Fehler bei ungültigem JSON."""
        # Arrange
        mock_ai_service = Mock()
        mock_ai_service.generate_response.return_value = "Invalid JSON response"
        
        service = StructuredDataExtractorService(ai_service=mock_ai_service)
        
        # Act & Assert
        with pytest.raises(ValueError, match="No JSON found"):
            service.extract_material_list("Test content")
    
    def test_extract_structured_data_empty_input(self):
        """Test: Fehler bei leerer Eingabe."""
        # Arrange
        mock_ai_service = Mock()
        
        service = StructuredDataExtractorService(ai_service=mock_ai_service)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Content cannot be empty"):
            service.extract_material_list("")
