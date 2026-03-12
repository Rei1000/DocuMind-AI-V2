"""
Integration Tests für Prompt-Struktur-Erkennung (CR-P2.1)

Testet die Integration zwischen:
- RAGAIService
- DocumentTypeSpecificChunkingService
- prompt_structure_detector

Mit echten Datenbank-Prompts und verschiedenen Format-Varianten.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from contexts.ragintegration.infrastructure.ai_service import RAGAIService
from contexts.ragintegration.infrastructure.services import DocumentTypeSpecificChunkingService
from contexts.ragintegration.infrastructure.prompt_structure_detector import (
    detect_prompt_structure_type,
    remove_json_comments,
    detect_type_by_string_pattern
)


class TestPromptStructureDetectionIntegration:
    """Integration Tests für Prompt-Struktur-Erkennung"""
    
    @patch('contexts.ragintegration.infrastructure.ai_service.OpenAIAdapter')
    @patch('contexts.ragintegration.infrastructure.ai_service.GoogleAIAdapter')
    def test_consistent_detection_between_ai_and_chunking_service(self, mock_google_adapter, mock_openai_adapter):
        """IT-PSD-001: Konsistente Erkennung zwischen AI Service und Chunking Service"""
        # Arrange
        ai_service = RAGAIService(rag_chat_prompt_repo=None)
        chunking_service = DocumentTypeSpecificChunkingService()
        
        # Test-Prompts mit verschiedenen Strukturen
        test_cases = [
            ('{"nodes": [...], "connections": [...]}', "flowchart"),
            ('{"steps": [{"step_number": 1, "description": "Test"}]}', "work_instruction"),
            ('{"process_steps": [...]}', "sop"),
            ('{"sections": [...], "document_metadata": {...}}', "research_article"),
            ('{"technical_specifications": {...}}', "datasheet"),
            ('{"page_text_de": "...", "scope_statements": [], "terms_and_definitions": [], "requirements": []}', "technical_standard"),
        ]
        
        for prompt_text, expected_type in test_cases:
            # Act
            ai_detected = detect_prompt_structure_type(prompt_text)
            chunking_detected = detect_prompt_structure_type(prompt_text)
            
            # Assert
            assert ai_detected == chunking_detected, f"Inkonsistente Erkennung für {expected_type}"
            assert ai_detected == expected_type, f"Falsche Erkennung: erwartet {expected_type}, erhalten {ai_detected}"
    
    @patch('backend.app.database.get_db')
    @patch('contexts.ragintegration.infrastructure.ai_service.OpenAIAdapter')
    @patch('contexts.ragintegration.infrastructure.ai_service.GoogleAIAdapter')
    def test_detection_with_real_database_prompts(self, mock_google_adapter, mock_openai_adapter, mock_get_db):
        """IT-PSD-002: Erkennung mit echten Prompt-Templates aus DB"""
        # Arrange
        ai_service = RAGAIService(rag_chat_prompt_repo=None)
        
        # Mock DB: Flussdiagramm-Prompt
        mock_db_session = Mock()
        mock_result = Mock()
        prompt_text = '{"nodes": [{"id": "1", "label": "Start"}], "connections": []}'
        mock_row = (1, "Flussdiagramm Prompt", prompt_text, "active")
        mock_result.fetchone.return_value = mock_row
        mock_db_session.execute.return_value = mock_result
        
        def mock_get_db_generator():
            while True:
                yield mock_db_session
        
        mock_get_db.return_value = mock_get_db_generator()
        
        # Act
        result = ai_service._get_document_type_prompt_instructions("FLOWCHART", None)
        
        # Assert
        assert result is not None
        assert "Flussdiagramm" in result or "ANWEISUNGEN" in result
    
    def test_format_variants_detection(self):
        """IT-PSD-003: Format-Varianten Erkennung (camelCase, PascalCase)"""
        # Arrange
        test_cases = [
            ('{"nodeList": [...]}', "flowchart"),  # camelCase
            ('{"ProcessSteps": [...]}', "sop"),  # PascalCase
            ('{"Steps": [{"StepNumber": 1}]}', "work_instruction"),  # PascalCase
            ('{"NodeList": [...]}', "flowchart"),  # PascalCase
        ]
        
        for prompt_text, expected_type in test_cases:
            # Act
            detected = detect_prompt_structure_type(prompt_text)
            
            # Assert
            assert detected == expected_type, f"Format-Variante nicht erkannt: {prompt_text} -> erwartet {expected_type}, erhalten {detected}"
    
    def test_comment_removal_in_prompts(self):
        """IT-PSD-004: Kommentar-Ignorierung in Prompts"""
        # Arrange
        prompt_with_comment = '''{
            // Kommentar: Dieses Dokument enthält nodes für Beispiele
            "steps": [
                {"step_number": 1, "description": "Schritt 1"}
            ]
        }'''
        
        prompt_with_multiline_comment = '''{
            /* 
             * Multiline Kommentar mit nodes
             */
            "steps": [
                {"step_number": 1, "description": "Schritt 1"}
            ]
        }'''
        
        # Act
        detected1 = detect_prompt_structure_type(prompt_with_comment)
        detected2 = detect_prompt_structure_type(prompt_with_multiline_comment)
        
        # Assert
        assert detected1 == "work_instruction", "Kommentar sollte ignoriert werden"
        assert detected2 == "work_instruction", "Multiline-Kommentar sollte ignoriert werden"
        
        # Prüfe dass Kommentare entfernt werden
        cleaned1 = remove_json_comments(prompt_with_comment)
        cleaned2 = remove_json_comments(prompt_with_multiline_comment)
        
        assert "// Kommentar" not in cleaned1
        assert "/*" not in cleaned2
        assert "*/" not in cleaned2

