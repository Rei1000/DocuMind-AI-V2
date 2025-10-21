"""
Unit Tests: AI Playground → Prompt Template Integration

Tests für die korrekte Übertragung von AI Playground Einstellungen zu Prompt Templates.
Folgt TDD-Prinzip: Tests ZUERST, dann Implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from contexts.prompttemplates.application.use_cases import CreateFromPlaygroundUseCase
from contexts.prompttemplates.domain.entities import PromptTemplate, PromptTemplateType, PromptStatus
from contexts.prompttemplates.domain.repositories import PromptTemplateRepository


class TestAIPlaygroundIntegration:
    """Test-Klasse für AI Playground → Prompt Template Integration"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock PromptTemplateRepository"""
        return Mock(spec=PromptTemplateRepository)
    
    @pytest.fixture
    def use_case(self, mock_repository):
        """CreateFromPlaygroundUseCase mit gemockten Repository"""
        return CreateFromPlaygroundUseCase(repository=mock_repository)
    
    @pytest.fixture
    def ai_playground_data(self):
        """Beispiel AI Playground Daten"""
        return {
            "name": "Test Prompt from Playground",
            "description": "Test description",
            "system_prompt": "You are a helpful assistant.",
            "user_prompt": "Analyze this document: {document}",
            "ai_model": "gemini-2.5-flash",
            "temperature": 0.0,
            "max_tokens": 5600,
            "top_p": 0.01,
            "detail_level": "high",
            "document_type_id": 3,
            "tags": ["test", "playground"]
        }

    # ===== RED PHASE: Tests schreiben (sollen fehlschlagen) =====
    
    @pytest.mark.asyncio
    async def test_create_from_playground_preserves_ai_settings(self, use_case, mock_repository, ai_playground_data):
        """Test: AI Playground Einstellungen werden korrekt übertragen"""
        # Arrange
        mock_repository.save = AsyncMock(return_value=Mock(id=1))
        
        # Act
        result = await use_case.execute(
            name=ai_playground_data["name"],
            description=ai_playground_data["description"],
            system_prompt=ai_playground_data["system_prompt"],
            user_prompt=ai_playground_data["user_prompt"],
            ai_model=ai_playground_data["ai_model"],
            temperature=ai_playground_data["temperature"],
            max_tokens=ai_playground_data["max_tokens"],
            top_p=ai_playground_data["top_p"],
            detail_level=ai_playground_data["detail_level"],
            document_type_id=ai_playground_data["document_type_id"],
            tags=ai_playground_data["tags"]
        )
        
        # Assert: Repository.save wurde mit korrekten AI-Einstellungen aufgerufen
        mock_repository.save.assert_called_once()
        saved_template = mock_repository.save.call_args[0][0]
        
        # AI-Einstellungen müssen exakt übernommen werden
        assert saved_template.ai_model == "gemini-2.5-flash"
        assert saved_template.temperature == 0.0
        assert saved_template.max_tokens == 5600
        assert saved_template.top_p == 0.01
        assert saved_template.detail_level == "high"
    
    @pytest.mark.asyncio
    async def test_create_from_playground_with_different_models(self, use_case, mock_repository):
        """Test: Verschiedene AI-Modelle mit unterschiedlichen Einstellungen"""
        # Arrange: GPT-5 Mini Einstellungen
        gpt5_data = {
            "name": "GPT-5 Test",
            "ai_model": "gpt-5-mini",
            "temperature": 0.7,
            "max_tokens": 15000,
            "top_p": 1.0,
            "detail_level": "high"
        }
        
        mock_repository.save = AsyncMock(return_value=Mock(id=2))
        
        # Act
        result = await use_case.execute(
            name=gpt5_data["name"],
            description="Test",
            system_prompt="Test system",
            user_prompt="Test user",
            ai_model=gpt5_data["ai_model"],
            temperature=gpt5_data["temperature"],
            max_tokens=gpt5_data["max_tokens"],
            top_p=gpt5_data["top_p"],
            detail_level=gpt5_data["detail_level"],
            document_type_id=3,
            tags=[]
        )
        
        # Assert: GPT-5 Einstellungen korrekt übertragen
        saved_template = mock_repository.save.call_args[0][0]
        assert saved_template.ai_model == "gpt-5-mini"
        assert saved_template.temperature == 0.7
        assert saved_template.max_tokens == 15000
        assert saved_template.top_p == 1.0
    
    @pytest.mark.asyncio
    async def test_create_from_playground_validates_ai_settings(self, use_case, mock_repository):
        """Test: AI-Einstellungen werden validiert"""
        # Arrange: Ungültige Einstellungen
        invalid_data = {
            "temperature": 3.0,  # > 2.0 (ungültig)
            "max_tokens": -100,   # < 0 (ungültig)
            "top_p": 1.5         # > 1.0 (ungültig)
        }
        
        # Act & Assert: Sollte ValueError werfen
        with pytest.raises(ValueError):
            await use_case.execute(
                name="Test",
                description="Test",
                system_prompt="Test",
                user_prompt="Test",
                ai_model="gemini-2.5-flash",
                temperature=invalid_data["temperature"],
                max_tokens=invalid_data["max_tokens"],
                top_p=invalid_data["top_p"],
                detail_level="high",
                document_type_id=3,
                tags=[]
            )
    
    @pytest.mark.asyncio
    async def test_create_from_playground_sets_correct_defaults(self, use_case, mock_repository):
        """Test: Korrekte Default-Werte werden gesetzt"""
        # Arrange
        mock_repository.save = AsyncMock(return_value=Mock(id=3))
        
        # Act: Minimal-Daten (nur required fields)
        result = await use_case.execute(
            name="Minimal Test",
            description="Test",
            system_prompt="Test",
            user_prompt="Test",
            ai_model="gemini-2.5-flash",
            document_type_id=3
        )
        
        # Assert: Default-Werte werden korrekt gesetzt
        saved_template = mock_repository.save.call_args[0][0]
        assert saved_template.temperature == 0.0  # Default aus AI Playground
        assert saved_template.max_tokens == 5600  # Default für Gemini
        assert saved_template.top_p == 0.01       # Default für Gemini
        assert saved_template.detail_level == "high"  # Default
        assert saved_template.status == PromptStatus.DRAFT  # Default Status
        assert saved_template.template_type == PromptTemplateType.DOCUMENT_PROCESSING  # Default Type
