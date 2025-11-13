"""
Tests für AI Processing Error Handling

TDD: Tests FIRST für besseres Error-Handling bei Gemini und anderen AI-Modellen
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from contexts.documentupload.infrastructure.ai_processing_service import (
    AIPlaygroundProcessingService,
    AIProcessingError
)


class TestAIProcessingErrorHandling:
    """Test AI Processing Error Scenarios"""
    
    @pytest.mark.asyncio
    async def test_gemini_safety_filter_error_returns_clear_message(self):
        """
        GIVEN: Gemini blockiert wegen Safety Filter
        WHEN: process_page() aufgerufen
        THEN: Klare Fehlermeldung mit Hinweis auf Safety Settings
        """
        # Arrange
        ai_playground_service = AsyncMock()
        
        # Simuliere Gemini Safety Filter Response
        test_result = MagicMock()
        test_result.response = ""  # Empty wegen Safety Filter
        test_result.error_message = "Content blocked by safety filters"
        test_result.model_name = "gemini-2.5-flash"
        test_result.tokens_sent = 0
        test_result.tokens_received = 0
        test_result.total_tokens = 0
        test_result.response_time = 0.5
        
        ai_playground_service.test_model.return_value = test_result
        
        ai_processing_service = AIPlaygroundProcessingService(ai_playground_service)
        
        # Act & Assert
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', MagicMock()):
                with pytest.raises(AIProcessingError) as exc_info:
                    await ai_processing_service.process_page(
                        page_image_path="test.png",
                        prompt_text="Test prompt",
                        ai_model_id="gemini-2.5-flash",
                        temperature=0.7,
                        max_tokens=1000,
                        top_p=1.0,
                        detail_level="high"
                    )
        
        # Verify error message is clear and helpful
        error_message = str(exc_info.value)
        assert "safety filter" in error_message.lower() or "blocked" in error_message.lower() or "empty response" in error_message.lower()
    
    @pytest.mark.asyncio
    async def test_empty_response_without_error_message(self):
        """
        GIVEN: AI gibt leere Response ohne Error-Message
        WHEN: process_page() aufgerufen
        THEN: Allgemeine Fehlermeldung für leere Response
        """
        # Arrange
        ai_playground_service = AsyncMock()
        
        test_result = MagicMock()
        test_result.response = ""
        test_result.error_message = None  # Kein spezifischer Error
        test_result.model_name = "gpt-5-mini"
        test_result.tokens_sent = 100
        test_result.tokens_received = 0
        test_result.total_tokens = 100
        test_result.response_time = 1.2
        
        ai_playground_service.test_model.return_value = test_result
        
        ai_processing_service = AIPlaygroundProcessingService(ai_playground_service)
        
        # Act & Assert
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', MagicMock()):
                with pytest.raises(AIProcessingError) as exc_info:
                    await ai_processing_service.process_page(
                        page_image_path="test.png",
                        prompt_text="Test prompt",
                        ai_model_id="gpt-5-mini",
                        temperature=0.7,
                        max_tokens=1000,
                        top_p=1.0,
                        detail_level="high"
                    )
        
        error_message = str(exc_info.value)
        assert "empty response" in error_message.lower()
    
    @pytest.mark.asyncio
    async def test_network_error_is_caught(self):
        """
        GIVEN: Netzwerkfehler bei AI-Call
        WHEN: process_page() aufgerufen
        THEN: AIProcessingError mit Netzwerk-Hinweis
        """
        # Arrange
        ai_playground_service = AsyncMock()
        ai_playground_service.test_model.side_effect = Exception("Connection timeout")
        
        ai_processing_service = AIPlaygroundProcessingService(ai_playground_service)
        
        # Act & Assert
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', MagicMock()):
                with pytest.raises(AIProcessingError) as exc_info:
                    await ai_processing_service.process_page(
                        page_image_path="test.png",
                        prompt_text="Test prompt",
                        ai_model_id="gpt-4o-mini",
                        temperature=0.7,
                        max_tokens=1000,
                        top_p=1.0,
                        detail_level="high"
                    )
        
        error_message = str(exc_info.value)
        assert "failed to process page" in error_message.lower()
        assert "connection timeout" in error_message.lower()
    
    @pytest.mark.asyncio
    async def test_successful_processing_returns_valid_result(self):
        """
        GIVEN: AI gibt valide Response
        WHEN: process_page() aufgerufen
        THEN: Erfolgreiche Verarbeitung ohne Error
        """
        # Arrange
        ai_playground_service = AsyncMock()
        
        test_result = MagicMock()
        test_result.response = '{"title": "Test Document", "content": "Valid JSON"}'
        test_result.error_message = None
        test_result.model_name = "gpt-4o-mini"
        test_result.tokens_sent = 150
        test_result.tokens_received = 50
        test_result.total_tokens = 200
        test_result.response_time = 2.5
        
        ai_playground_service.test_model.return_value = test_result
        
        ai_processing_service = AIPlaygroundProcessingService(ai_playground_service)
        
        # Act
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', MagicMock()):
                result = await ai_processing_service.process_page(
                    page_image_path="test.png",
                    prompt_text="Test prompt",
                    ai_model_id="gpt-4o-mini",
                    temperature=0.7,
                    max_tokens=1000,
                    top_p=1.0,
                    detail_level="high"
                )
        
        # Assert
        assert result["json_response"] == '{"title": "Test Document", "content": "Valid JSON"}'
        assert result["model_name"] == "gpt-4o-mini"
        assert result["tokens_sent"] == 150
        assert result["tokens_received"] == 50
        assert result["total_tokens"] == 200
        assert result["response_time_ms"] > 0

