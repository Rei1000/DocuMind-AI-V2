"""
TDD Tests für RAGChatPrompt Entity (PHASE 1).

Tests für Domain Entity Validierung und Business Logic.
"""

import pytest
from datetime import datetime, timedelta
from contexts.ragintegration.domain.entities import RAGChatPrompt


class TestRAGChatPromptEntity:
    """Tests für RAGChatPrompt Entity."""
    
    def test_create_valid_rag_chat_prompt(self):
        """Test: Erstelle gültigen RAG Chat Prompt."""
        # Arrange & Act
        prompt = RAGChatPrompt(
            id=None,
            document_type_id=10,
            prompt_text="Custom Prompt für Fachartikel",
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            multi_query_prompt_text=None
        )
        
        # Assert
        assert prompt.id is None
        assert prompt.document_type_id == 10
        assert prompt.prompt_text == "Custom Prompt für Fachartikel"
        assert prompt.created_by_user_id == 1
        assert prompt.is_custom() is True
        assert prompt.has_multi_query() is False
    
    def test_rag_chat_prompt_with_multi_query(self):
        """Test: RAG Chat Prompt mit Multi-Query Prompt."""
        # Arrange & Act
        prompt = RAGChatPrompt(
            id=1,
            document_type_id=10,
            prompt_text="Custom Prompt",
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            multi_query_prompt_text="Multi-Query Prompt"
        )
        
        # Assert
        assert prompt.has_multi_query() is True
        assert prompt.multi_query_prompt_text == "Multi-Query Prompt"
    
    def test_rag_chat_prompt_validation_document_type_id_zero(self):
        """Test: Validierung schlägt fehl wenn document_type_id <= 0."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="document_type_id must be positive"):
            RAGChatPrompt(
                id=None,
                document_type_id=0,  # Invalid
                prompt_text="Test",
                created_by_user_id=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                multi_query_prompt_text=None
            )
    
    def test_rag_chat_prompt_validation_empty_prompt_text(self):
        """Test: Validierung schlägt fehl wenn prompt_text leer ist."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="prompt_text cannot be empty"):
            RAGChatPrompt(
                id=None,
                document_type_id=10,
                prompt_text="",  # Invalid
                created_by_user_id=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                multi_query_prompt_text=None
            )
    
    def test_rag_chat_prompt_validation_whitespace_prompt_text(self):
        """Test: Validierung schlägt fehl wenn prompt_text nur Whitespace ist."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="prompt_text cannot be empty"):
            RAGChatPrompt(
                id=None,
                document_type_id=10,
                prompt_text="   ",  # Invalid (nur Whitespace)
                created_by_user_id=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                multi_query_prompt_text=None
            )
    
    def test_rag_chat_prompt_validation_created_by_user_id_zero(self):
        """Test: Validierung schlägt fehl wenn created_by_user_id <= 0."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="created_by_user_id must be positive"):
            RAGChatPrompt(
                id=None,
                document_type_id=10,
                prompt_text="Test",
                created_by_user_id=0,  # Invalid
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                multi_query_prompt_text=None
            )
    
    def test_rag_chat_prompt_validation_updated_at_before_created_at(self):
        """Test: Validierung schlägt fehl wenn updated_at vor created_at liegt."""
        # Arrange
        created_at = datetime.utcnow()
        updated_at = created_at - timedelta(days=1)  # Vor created_at
        
        # Act & Assert
        with pytest.raises(ValueError, match="updated_at cannot be before created_at"):
            RAGChatPrompt(
                id=None,
                document_type_id=10,
                prompt_text="Test",
                created_by_user_id=1,
                created_at=created_at,
                updated_at=updated_at,  # Invalid
                multi_query_prompt_text=None
            )
    
    def test_rag_chat_prompt_has_multi_query_with_empty_string(self):
        """Test: has_multi_query() gibt False zurück wenn multi_query_prompt_text leer ist."""
        # Arrange & Act
        prompt = RAGChatPrompt(
            id=1,
            document_type_id=10,
            prompt_text="Custom Prompt",
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            multi_query_prompt_text=""  # Leer
        )
        
        # Assert
        assert prompt.has_multi_query() is False
    
    def test_rag_chat_prompt_has_multi_query_with_whitespace(self):
        """Test: has_multi_query() gibt False zurück wenn multi_query_prompt_text nur Whitespace ist."""
        # Arrange & Act
        prompt = RAGChatPrompt(
            id=1,
            document_type_id=10,
            prompt_text="Custom Prompt",
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            multi_query_prompt_text="   "  # Nur Whitespace
        )
        
        # Assert
        assert prompt.has_multi_query() is False

