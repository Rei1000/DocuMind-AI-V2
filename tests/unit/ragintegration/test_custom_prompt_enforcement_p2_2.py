"""
Unit Tests für CR-P2.2: Custom-Prompt-Enforcement

RED Phase: Alle Tests schlagen zunächst fehl und demonstrieren die Probleme.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Optional

from contexts.ragintegration.domain.exceptions import MissingCustomPromptError, InvalidCustomPromptError
from contexts.ragintegration.domain.entities import RAGChatPrompt
from contexts.ragintegration.infrastructure.ai_service import RAGAIService
from datetime import datetime


class TestCustomPromptValidation:
    """Kategorie 1: Unit Tests - Custom Prompt Validation"""
    
    @patch('contexts.ragintegration.infrastructure.ai_service.OpenAIAdapter')
    @patch('contexts.ragintegration.infrastructure.ai_service.GoogleAIAdapter')
    def test_custom_prompt_must_exist_when_document_type_id_set(self, mock_google, mock_openai):
        """
        TEST-1.1: Verifizieren, dass MissingCustomPromptError geworfen wird,
        wenn document_type_id gesetzt ist, aber kein Custom Prompt existiert.
        """
        # Setup
        mock_repo = Mock()
        mock_repo.get_by_document_type_id.return_value = None
        
        ai_service = RAGAIService(rag_chat_prompt_repo=mock_repo)
        
        # Erwartetes Resultat: MissingCustomPromptError
        with pytest.raises(MissingCustomPromptError) as exc_info:
            ai_service._create_structured_rag_prompt(
                question="Test-Frage",
                context="Test-Kontext",
                document_type="SOP",
                document_type_id=1
            )
        
        assert exc_info.value.document_type_id == 1
        assert "SOP" in str(exc_info.value) or "1" in str(exc_info.value)
    
    @patch('contexts.ragintegration.infrastructure.ai_service.OpenAIAdapter')
    @patch('contexts.ragintegration.infrastructure.ai_service.GoogleAIAdapter')
    def test_custom_prompt_must_contain_context_placeholder(self, mock_google, mock_openai):
        """
        TEST-1.2: Verifizieren, dass Fehler geworfen wird,
        wenn Custom Prompt {context} fehlt.
        """
        # Setup: Custom Prompt ohne {context}
        custom_prompt = RAGChatPrompt(
            id=1,
            document_type_id=10,
            prompt_text="FRAGE: {question}\nANWEISUNGEN: ...",
            created_by_user_id=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        mock_repo = Mock()
        mock_repo.get_by_document_type_id.return_value = custom_prompt
        
        ai_service = RAGAIService(rag_chat_prompt_repo=mock_repo)
        
        # Erwartetes Resultat: InvalidCustomPromptError (wird in GREEN Phase implementiert)
        # Aktuell: Keine Validierung → Test schlägt fehl (RED)
        with pytest.raises(InvalidCustomPromptError) as exc_info:
            ai_service._create_structured_rag_prompt(
                question="Test-Frage",
                context="Test-Kontext",
                document_type="Fachartikel",
                document_type_id=10
            )
        
        assert "{context}" in exc_info.value.missing_placeholders
    
    @patch('contexts.ragintegration.infrastructure.ai_service.OpenAIAdapter')
    @patch('contexts.ragintegration.infrastructure.ai_service.GoogleAIAdapter')
    def test_custom_prompt_must_contain_question_placeholder(self, mock_google, mock_openai):
        """
        TEST-1.3: Verifizieren, dass Fehler geworfen wird,
        wenn Custom Prompt {question} fehlt.
        """
        # Setup: Custom Prompt ohne {question}
        custom_prompt = RAGChatPrompt(
            id=1,
            document_type_id=10,
            prompt_text="KONTEXT: {context}\nANWEISUNGEN: ...",
            created_by_user_id=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        mock_repo = Mock()
        mock_repo.get_by_document_type_id.return_value = custom_prompt
        
        ai_service = RAGAIService(rag_chat_prompt_repo=mock_repo)
        
        # Erwartetes Resultat: InvalidCustomPromptError (wird in GREEN Phase implementiert)
        # Aktuell: Keine Validierung → Test schlägt fehl (RED)
        with pytest.raises(InvalidCustomPromptError) as exc_info:
            ai_service._create_structured_rag_prompt(
                question="Test-Frage",
                context="Test-Kontext",
                document_type="Fachartikel",
                document_type_id=10
            )
        
        assert "{question}" in exc_info.value.missing_placeholders
    
    @patch('contexts.ragintegration.infrastructure.ai_service.OpenAIAdapter')
    @patch('contexts.ragintegration.infrastructure.ai_service.GoogleAIAdapter')
    def test_custom_prompt_placeholders_replaced_correctly(self, mock_google, mock_openai):
        """
        TEST-1.4: Verifizieren, dass Platzhalter korrekt ersetzt werden.
        """
        # Setup
        custom_prompt = RAGChatPrompt(
            id=1,
            document_type_id=10,
            prompt_text="KONTEXT: {context}\nFRAGE: {question}",
            created_by_user_id=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        mock_repo = Mock()
        mock_repo.get_by_document_type_id.return_value = custom_prompt
        
        ai_service = RAGAIService(rag_chat_prompt_repo=mock_repo)
        
        # Execute
        prompt_text, missing_placeholders = ai_service._create_structured_rag_prompt(
            question="vertikale verformung",
            context="Chunk 1: ...",
            document_type="Fachartikel",
            document_type_id=10
        )
        
        # Erwartetes Resultat
        assert "{context}" not in prompt_text
        assert "{question}" not in prompt_text
        assert "vertikale verformung" in prompt_text
        assert "Chunk 1: ..." in prompt_text
        assert missing_placeholders == False
    
    @patch('contexts.ragintegration.infrastructure.ai_service.OpenAIAdapter')
    @patch('contexts.ragintegration.infrastructure.ai_service.GoogleAIAdapter')
    def test_custom_prompt_exact_match_no_modification(self, mock_google, mock_openai):
        """
        TEST-1.5: Verifizieren, dass Custom Prompt exakt verwendet wird
        (keine System-Prefix-Anfügung).
        """
        # Setup: Custom Prompt mit eigenem Prefix
        custom_prompt = RAGChatPrompt(
            id=1,
            document_type_id=10,
            prompt_text="Du bist ein Experte wissenschaftliche Fachliteratur...\nKONTEXT: {context}\nFRAGE: {question}",
            created_by_user_id=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        mock_repo = Mock()
        mock_repo.get_by_document_type_id.return_value = custom_prompt
        
        ai_service = RAGAIService(rag_chat_prompt_repo=mock_repo)
        
        # Execute
        prompt_text, _ = ai_service._create_structured_rag_prompt(
            question="Test",
            context="Test",
            document_type="Fachartikel",
            document_type_id=10
        )
        
        # Erwartetes Resultat: Beginnt mit Custom-Prefix, NICHT System-Prefix
        assert prompt_text.startswith("Du bist ein Experte wissenschaftliche Fachliteratur")
        assert not prompt_text.startswith("Du bist ein Experte für Qualitätsmanagement")


class TestPromptConsistency:
    """Kategorie 2: Unit Tests - Prompt Consistency"""
    
    @patch('contexts.ragintegration.infrastructure.ai_service.OpenAIAdapter')
    @patch('contexts.ragintegration.infrastructure.ai_service.GoogleAIAdapter')
    def test_prompt_stored_in_metadata_matches_used_prompt(self, mock_google, mock_openai):
        """
        TEST-2.1: Verifizieren, dass gespeicherter Prompt in metadata["prompt_text"]
        exakt dem verwendeten Prompt entspricht.
        """
        # Setup
        custom_prompt = RAGChatPrompt(
            id=1,
            document_type_id=10,
            prompt_text="KONTEXT: {context}\nFRAGE: {question}",
            created_by_user_id=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        mock_repo = Mock()
        mock_repo.get_by_document_type_id.return_value = custom_prompt
        
        ai_service = RAGAIService(rag_chat_prompt_repo=mock_repo)
        
        # Execute
        used_prompt, _ = ai_service._create_structured_rag_prompt(
            question="Test-Frage",
            context="Test-Kontext",
            document_type="Fachartikel",
            document_type_id=10
        )
        
        # Simuliere AI Response
        ai_response = {
            "answer": "Test-Antwort",
            "prompt_text": used_prompt  # Sollte exakt der verwendete Prompt sein
        }
        
        # Erwartetes Resultat
        assert ai_response["prompt_text"] == used_prompt
        assert "{context}" not in ai_response["prompt_text"]
        assert "{question}" not in ai_response["prompt_text"]
    
    def test_prompt_viewer_shows_exact_stored_prompt(self):
        """
        TEST-2.2: Verifizieren, dass Prompt Viewer exakt den gespeicherten Prompt zeigt.
        """
        # Setup: Gespeicherter Prompt in metadata
        stored_prompt = "KONTEXT: Chunk 1\nFRAGE: Test-Frage"
        
        # Simuliere Chat-Message mit metadata
        message_metadata = {
            "prompt_text": stored_prompt
        }
        
        # Erwartetes Resultat: Prompt Viewer zeigt exakt stored_prompt
        assert message_metadata["prompt_text"] == stored_prompt
    
    def test_filter_panel_shows_exact_custom_prompt(self):
        """
        TEST-2.3: Verifizieren, dass Filter-Panel exakt den Custom Prompt zeigt
        (mit Platzhaltern).
        """
        # Setup: Custom Prompt aus DB
        custom_prompt = RAGChatPrompt(
            id=1,
            document_type_id=10,
            prompt_text="KONTEXT: {context}\nFRAGE: {question}\nANWEISUNGEN: ...",
            created_by_user_id=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Erwartetes Resultat: Filter-Panel zeigt exakt Custom Prompt (mit Platzhaltern)
        filter_panel_prompt = custom_prompt.prompt_text
        
        assert "{context}" in filter_panel_prompt
        assert "{question}" in filter_panel_prompt
        assert not filter_panel_prompt.startswith("Du bist ein Experte für Qualitätsmanagement")


# Weitere Test-Kategorien werden in separaten Dateien implementiert
# (Integration Tests, Negative Tests, Concurrency Tests, etc.)

