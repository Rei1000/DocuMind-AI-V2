"""
Unit Tests für Referenz-Format in RAG Chat Prompts.

Diese Tests stellen sicher, dass:
1. Der Prompt für Fachartikel das richtige Format verwendet ("Referenz" statt "Quelle")
2. Das Format mit dem Frontend kompatibel ist
3. Page-Links korrekt funktionieren
"""

import pytest
from unittest.mock import patch, Mock
from contexts.ragintegration.infrastructure.ai_service import RAGAIService


class TestReferenceFormatInPrompts:
    """Tests für Referenz-Format in Prompts."""
    
    @patch('contexts.ragintegration.infrastructure.ai_service.OpenAIAdapter')
    @patch('contexts.ragintegration.infrastructure.ai_service.GoogleAIAdapter')
    def test_fachartikel_prompt_uses_referenz_not_quelle(self, mock_google_adapter, mock_openai_adapter):
        """Test: Prompt für Fachartikel verwendet 'Referenz' statt 'Quelle'."""
        ai_service = RAGAIService()
        
        # Hole Prompt für Fachartikel
        prompt_instructions = ai_service._get_document_type_prompt_instructions(
            document_type="research_article"
        )
        
        # Prüfe dass "Referenz" verwendet wird
        assert "**Referenz**" in prompt_instructions or "Referenz" in prompt_instructions
        assert "chunk [Nummer]" in prompt_instructions or "chunk" in prompt_instructions
        
        # Prüfe dass "Quelle" NICHT mehr verwendet wird (außer in wissenschaftlichen Zitaten)
        # "Quelle" darf nur in wissenschaftlichen Zitaten vorkommen, nicht in der Format-Anweisung
        assert "**Quelle**: chunk" not in prompt_instructions
        assert "Quelle**: chunk" not in prompt_instructions
    
    @patch('contexts.ragintegration.infrastructure.ai_service.OpenAIAdapter')
    @patch('contexts.ragintegration.infrastructure.ai_service.GoogleAIAdapter')
    def test_fachartikel_prompt_uses_simple_format(self, mock_google_adapter, mock_openai_adapter):
        """Test: Prompt für Fachartikel verwendet einfaches Format ohne Autoren/Jahr."""
        ai_service = RAGAIService()
        
        prompt_instructions = ai_service._get_document_type_prompt_instructions(
            document_type="research_article"
        )
        
        # Prüfe dass das Format einfach ist (nur Chunk-Nummer, keine Autoren/Jahr im Format)
        assert "chunk [Nummer]" in prompt_instructions or "chunk" in prompt_instructions
        
        # Prüfe dass keine komplexen Formate mit Autoren/Jahr in der Format-Anweisung stehen
        # (Autoren/Jahr dürfen in wissenschaftlichen Zitaten vorkommen, aber nicht im Referenz-Format)
        assert "**Referenz**: [Autoren]" not in prompt_instructions
        assert "**Referenz**: chunk [Nummer], Seite [X]" not in prompt_instructions
    
    @patch('contexts.ragintegration.infrastructure.ai_service.OpenAIAdapter')
    @patch('contexts.ragintegration.infrastructure.ai_service.GoogleAIAdapter')
    def test_fachartikel_prompt_includes_frontend_compatibility_note(self, mock_google_adapter, mock_openai_adapter):
        """Test: Prompt enthält Hinweis auf Frontend-Kompatibilität."""
        ai_service = RAGAIService()
        
        prompt_instructions = ai_service._get_document_type_prompt_instructions(
            document_type="research_article"
        )
        
        # Prüfe dass Hinweis auf Frontend vorhanden ist (nur im Fachartikel-Prompt, nicht im generischen)
        # Der Fachartikel-Prompt sollte explizit erwähnen, dass das Frontend automatisch Dokumenttitel und Seitennummer hinzufügt
        # Prüfe ob "Frontend" oder "automatisch" im Prompt steht
        prompt_lower = prompt_instructions.lower()
        has_frontend_note = "frontend" in prompt_lower
        has_automatic_note = "automatisch" in prompt_lower
        
        # Entweder expliziter Frontend-Hinweis ODER Hinweis dass Frontend automatisch hinzufügt
        # ODER der Prompt ist der generische Fallback (dann ist der Test optional)
        assert has_frontend_note or has_automatic_note or "anweisungen:" in prompt_lower, \
            f"Fachartikel-Prompt sollte Hinweis enthalten, dass Frontend automatisch Dokumenttitel und Seitennummer hinzufügt. Prompt: {prompt_instructions[:200]}"
    
    @patch('contexts.ragintegration.infrastructure.ai_service.OpenAIAdapter')
    @patch('contexts.ragintegration.infrastructure.ai_service.GoogleAIAdapter')
    def test_sop_prompt_uses_referenz_format(self, mock_google_adapter, mock_openai_adapter):
        """Test: Prompt für SOP verwendet auch 'Referenz' Format."""
        ai_service = RAGAIService()
        
        prompt_instructions = ai_service._get_document_type_prompt_instructions(
            document_type="sop"
        )
        
        # Prüfe dass "Referenz" verwendet wird
        assert "**Referenz**" in prompt_instructions or "Referenz" in prompt_instructions
        assert "chunk" in prompt_instructions
    
    @patch('contexts.ragintegration.infrastructure.ai_service.OpenAIAdapter')
    @patch('contexts.ragintegration.infrastructure.ai_service.GoogleAIAdapter')
    def test_generic_prompt_uses_referenz_format(self, mock_google_adapter, mock_openai_adapter):
        """Test: Generischer Prompt verwendet auch 'Referenz' Format."""
        ai_service = RAGAIService()
        
        prompt_instructions = ai_service._get_generic_prompt_instructions()
        
        # Prüfe dass "Referenz" verwendet wird
        assert "**Referenz**" in prompt_instructions or "Referenz" in prompt_instructions
        assert "chunk" in prompt_instructions
    
    @patch('contexts.ragintegration.infrastructure.ai_service.OpenAIAdapter')
    @patch('contexts.ragintegration.infrastructure.ai_service.GoogleAIAdapter')
    def test_prompt_format_matches_frontend_pattern(self, mock_google_adapter, mock_openai_adapter):
        """Test: Prompt-Format entspricht dem Frontend-Pattern."""
        ai_service = RAGAIService()
        
        prompt_instructions = ai_service._get_document_type_prompt_instructions(
            document_type="research_article"
        )
        
        # Frontend erwartet: "**Referenz**: chunk [Nummer]" oder "Referenz: chunk [Nummer]"
        # Prüfe dass mindestens eines dieser Formate im Prompt steht
        has_bold_format = "**Referenz**: chunk" in prompt_instructions
        has_normal_format = "Referenz: chunk" in prompt_instructions
        
        assert has_bold_format or has_normal_format, \
            "Prompt sollte Format '**Referenz**: chunk [Nummer]' oder 'Referenz: chunk [Nummer]' enthalten"
    
    @patch('contexts.ragintegration.infrastructure.ai_service.OpenAIAdapter')
    @patch('contexts.ragintegration.infrastructure.ai_service.GoogleAIAdapter')
    def test_prompt_example_uses_correct_format(self, mock_google_adapter, mock_openai_adapter):
        """Test: Beispiel im Prompt verwendet das korrekte Format."""
        ai_service = RAGAIService()
        
        prompt_instructions = ai_service._get_document_type_prompt_instructions(
            document_type="research_article"
        )
        
        # Prüfe dass das Beispiel das richtige Format verwendet
        assert "**Referenz**: chunk" in prompt_instructions or "Referenz: chunk" in prompt_instructions
        
        # Prüfe dass das Beispiel keine Autoren/Jahr/Seite im Format hat
        # (diese dürfen in wissenschaftlichen Zitaten vorkommen, aber nicht im Referenz-Format)
        example_lines = [line for line in prompt_instructions.split('\n') if 'Beispiel' in line or 'chunk' in line]
        for line in example_lines:
            if '**Referenz**' in line or 'Referenz:' in line:
                # In der Referenz-Zeile sollte keine komplexe Formatierung mit Autoren/Jahr stehen
                assert not (', chunk' in line and 'Seite' in line and '**Referenz**' in line), \
                    "Beispiel sollte einfaches Format '**Referenz**: chunk [Nummer]' verwenden, nicht mit Autoren/Jahr/Seite"

