"""
TDD Tests für RAG Chat Prompt Use Cases (PHASE 1).

Tests für Use Case Business Logic.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from contexts.ragintegration.domain.entities import RAGChatPrompt
from contexts.ragintegration.application.use_cases import (
    GetRAGChatPromptUseCase,
    SaveRAGChatPromptUseCase,
    DeleteRAGChatPromptUseCase
)


class TestGetRAGChatPromptUseCase:
    """Tests für GetRAGChatPromptUseCase."""
    
    def test_get_rag_chat_prompt_returns_custom_if_exists(self):
        """Test: Custom Prompt wird zurückgegeben wenn vorhanden."""
        # Arrange
        mock_repo = Mock()
        custom_prompt = RAGChatPrompt(
            id=1,
            document_type_id=10,
            prompt_text="Custom Prompt für Fachartikel",
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            multi_query_prompt_text=None
        )
        mock_repo.get_by_document_type_id.return_value = custom_prompt
        
        use_case = GetRAGChatPromptUseCase(rag_chat_prompt_repo=mock_repo)
        
        # Act
        result = use_case.execute(10)
        
        # Assert
        assert result == "Custom Prompt für Fachartikel"
        mock_repo.get_by_document_type_id.assert_called_once_with(10)
    
    def test_get_rag_chat_prompt_returns_standard_if_no_custom(self):
        """Test: Standard Prompt wird zurückgegeben wenn kein Custom Prompt vorhanden."""
        # Arrange
        mock_repo = Mock()
        mock_repo.get_by_document_type_id.return_value = None
        
        mock_ai_service = Mock()
        mock_ai_service._get_document_type_prompt_instructions.return_value = "Standard Prompt"
        
        use_case = GetRAGChatPromptUseCase(
            rag_chat_prompt_repo=mock_repo,
            ai_service=mock_ai_service
        )
        
        # Act
        result = use_case.execute(10, document_type_name="Fachartikel")
        
        # Assert
        assert result == "Standard Prompt"
        mock_ai_service._get_document_type_prompt_instructions.assert_called_once_with("Fachartikel")
    
    def test_get_rag_chat_prompt_returns_none_if_no_prompt_available(self):
        """Test: None wird zurückgegeben wenn weder Custom noch Standard Prompt vorhanden."""
        # Arrange
        mock_repo = Mock()
        mock_repo.get_by_document_type_id.return_value = None
        
        use_case = GetRAGChatPromptUseCase(rag_chat_prompt_repo=mock_repo)
        
        # Act
        result = use_case.execute(10)
        
        # Assert
        assert result is None


class TestSaveRAGChatPromptUseCase:
    """Tests für SaveRAGChatPromptUseCase."""
    
    def test_save_rag_chat_prompt_creates_new_prompt(self):
        """Test: Neues Prompt wird erstellt."""
        # Arrange
        mock_repo = Mock()
        mock_repo.get_by_document_type_id.return_value = None
        
        saved_prompt = RAGChatPrompt(
            id=1,
            document_type_id=10,
            prompt_text="Custom Prompt",
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            multi_query_prompt_text=None
        )
        mock_repo.save.return_value = saved_prompt
        
        use_case = SaveRAGChatPromptUseCase(rag_chat_prompt_repo=mock_repo)
        
        # Act
        result = use_case.execute(
            document_type_id=10,
            prompt_text="Custom Prompt",
            user_id=1,
            user_level=4
        )
        
        # Assert
        assert result.id == 1
        mock_repo.save.assert_called_once()
    
    def test_save_rag_chat_prompt_updates_existing_prompt(self):
        """Test: Existierendes Prompt wird aktualisiert."""
        # Arrange
        mock_repo = Mock()
        existing_prompt = RAGChatPrompt(
            id=1,
            document_type_id=10,
            prompt_text="Old Prompt",
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            multi_query_prompt_text=None
        )
        mock_repo.get_by_document_type_id.return_value = existing_prompt
        mock_repo.save.return_value = existing_prompt
        
        use_case = SaveRAGChatPromptUseCase(rag_chat_prompt_repo=mock_repo)
        
        # Act
        result = use_case.execute(
            document_type_id=10,
            prompt_text="Updated Prompt",
            user_id=1,
            user_level=4
        )
        
        # Assert
        assert result.prompt_text == "Updated Prompt"
        mock_repo.save.assert_called_once()
    
    def test_save_rag_chat_prompt_requires_level_4(self):
        """Test: Nur Level 4+ können Prompts speichern."""
        # Arrange
        mock_repo = Mock()
        use_case = SaveRAGChatPromptUseCase(rag_chat_prompt_repo=mock_repo)
        
        # Act & Assert
        with pytest.raises(PermissionError, match="Nur Level 4\+"):
            use_case.execute(
                document_type_id=10,
                prompt_text="Custom Prompt",
                user_id=1,
                user_level=3  # Level 3 ist nicht erlaubt
            )
    
    def test_save_rag_chat_prompt_validates_empty_prompt_text(self):
        """Test: Validierung schlägt fehl wenn prompt_text leer ist."""
        # Arrange
        mock_repo = Mock()
        use_case = SaveRAGChatPromptUseCase(rag_chat_prompt_repo=mock_repo)
        
        # Act & Assert
        with pytest.raises(ValueError, match="prompt_text darf nicht leer sein"):
            use_case.execute(
                document_type_id=10,
                prompt_text="",  # Leer
                user_id=1,
                user_level=4
            )
    
    def test_save_rag_chat_prompt_validates_invalid_document_type_id(self):
        """Test: Validierung schlägt fehl wenn document_type_id ungültig ist."""
        # Arrange
        mock_repo = Mock()
        use_case = SaveRAGChatPromptUseCase(rag_chat_prompt_repo=mock_repo)
        
        # Act & Assert
        with pytest.raises(ValueError, match="document_type_id muss positiv sein"):
            use_case.execute(
                document_type_id=0,  # Ungültig
                prompt_text="Custom Prompt",
                user_id=1,
                user_level=4
            )
    
    def test_save_rag_chat_prompt_with_multi_query(self):
        """Test: Speichere Prompt mit Multi-Query Prompt."""
        # Arrange
        mock_repo = Mock()
        mock_repo.get_by_document_type_id.return_value = None
        
        saved_prompt = RAGChatPrompt(
            id=1,
            document_type_id=10,
            prompt_text="Custom Prompt",
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            multi_query_prompt_text="Multi-Query Prompt"
        )
        mock_repo.save.return_value = saved_prompt
        
        use_case = SaveRAGChatPromptUseCase(rag_chat_prompt_repo=mock_repo)
        
        # Act
        result = use_case.execute(
            document_type_id=10,
            prompt_text="Custom Prompt",
            multi_query_prompt_text="Multi-Query Prompt",
            user_id=1,
            user_level=4
        )
        
        # Assert
        assert result.multi_query_prompt_text == "Multi-Query Prompt"


class TestDeleteRAGChatPromptUseCase:
    """Tests für DeleteRAGChatPromptUseCase."""
    
    def test_delete_rag_chat_prompt_returns_true_when_deleted(self):
        """Test: True wird zurückgegeben wenn Prompt gelöscht wurde."""
        # Arrange
        mock_repo = Mock()
        mock_repo.delete.return_value = True
        
        use_case = DeleteRAGChatPromptUseCase(rag_chat_prompt_repo=mock_repo)
        
        # Act
        result = use_case.execute(
            document_type_id=10,
            user_id=1,
            user_level=4
        )
        
        # Assert
        assert result is True
        mock_repo.delete.assert_called_once_with(10)
    
    def test_delete_rag_chat_prompt_returns_false_when_not_found(self):
        """Test: False wird zurückgegeben wenn Prompt nicht gefunden wurde."""
        # Arrange
        mock_repo = Mock()
        mock_repo.delete.return_value = False
        
        use_case = DeleteRAGChatPromptUseCase(rag_chat_prompt_repo=mock_repo)
        
        # Act
        result = use_case.execute(
            document_type_id=10,
            user_id=1,
            user_level=4
        )
        
        # Assert
        assert result is False
    
    def test_delete_rag_chat_prompt_requires_level_4(self):
        """Test: Nur Level 4+ können Prompts löschen."""
        # Arrange
        mock_repo = Mock()
        use_case = DeleteRAGChatPromptUseCase(rag_chat_prompt_repo=mock_repo)
        
        # Act & Assert
        with pytest.raises(PermissionError, match="Nur Level 4\+"):
            use_case.execute(
                document_type_id=10,
                user_id=1,
                user_level=3  # Level 3 ist nicht erlaubt
            )

