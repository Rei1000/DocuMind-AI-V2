"""
TDD Tests für RAGChatPromptRepository (PHASE 1).

Tests für Repository Implementation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from contexts.ragintegration.domain.entities import RAGChatPrompt
from contexts.ragintegration.infrastructure.repositories import SQLAlchemyRAGChatPromptRepository


class TestSQLAlchemyRAGChatPromptRepository:
    """Tests für SQLAlchemyRAGChatPromptRepository."""
    
    def test_get_by_document_type_id_returns_prompt_when_exists(self):
        """Test: Hole Prompt wenn vorhanden."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_model = Mock()
        mock_model.id = 1
        mock_model.document_type_id = 10
        mock_model.prompt_text = "Custom Prompt"
        mock_model.multi_query_prompt_text = None
        mock_model.created_by_user_id = 1
        mock_model.created_at = datetime.utcnow()
        mock_model.updated_at = datetime.utcnow()
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_model
        mock_db.query.return_value = mock_query
        
        repo = SQLAlchemyRAGChatPromptRepository(mock_db)
        
        # Act
        result = repo.get_by_document_type_id(10)
        
        # Assert
        assert result is not None
        assert result.document_type_id == 10
        assert result.prompt_text == "Custom Prompt"
        mock_db.query.assert_called_once()
    
    def test_get_by_document_type_id_returns_none_when_not_exists(self):
        """Test: Hole None wenn Prompt nicht vorhanden."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        repo = SQLAlchemyRAGChatPromptRepository(mock_db)
        
        # Act
        result = repo.get_by_document_type_id(10)
        
        # Assert
        assert result is None
    
    def test_save_creates_new_prompt(self):
        """Test: Speichere neues Prompt."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_model = Mock()
        mock_model.id = 1
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.commit = Mock()
        
        # Mock query für get_by_document_type_id (wird nicht aufgerufen bei neuem Prompt)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # Mock Model-Konstruktor
        with pytest.mock.patch('backend.app.models.RAGChatPromptModel') as MockModel:
            MockModel.return_value = mock_model
            
            repo = SQLAlchemyRAGChatPromptRepository(mock_db)
            prompt = RAGChatPrompt(
                id=None,
                document_type_id=10,
                prompt_text="Custom Prompt",
                created_by_user_id=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                multi_query_prompt_text=None
            )
            
            # Act
            result = repo.save(prompt)
            
            # Assert
            assert result.id == 1
            mock_db.add.assert_called_once()
            mock_db.flush.assert_called_once()
            mock_db.commit.assert_called_once()
    
    def test_save_updates_existing_prompt(self):
        """Test: Update existierendes Prompt."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_model = Mock()
        mock_model.id = 1
        mock_model.prompt_text = "Old Prompt"
        mock_model.multi_query_prompt_text = None
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_model
        mock_db.query.return_value = mock_query
        mock_db.commit = Mock()
        
        repo = SQLAlchemyRAGChatPromptRepository(mock_db)
        prompt = RAGChatPrompt(
            id=1,
            document_type_id=10,
            prompt_text="Updated Prompt",
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            multi_query_prompt_text=None
        )
        
        # Act
        result = repo.save(prompt)
        
        # Assert
        assert result.id == 1
        assert mock_model.prompt_text == "Updated Prompt"
        mock_db.commit.assert_called_once()
    
    def test_save_handles_integrity_error(self):
        """Test: Handle IntegrityError beim Speichern."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_db.add = Mock()
        mock_db.flush = Mock(side_effect=IntegrityError("UNIQUE constraint", None, None))
        mock_db.rollback = Mock()
        
        # Mock Model-Konstruktor
        with pytest.mock.patch('backend.app.models.RAGChatPromptModel') as MockModel:
            MockModel.return_value = Mock()
            
            repo = SQLAlchemyRAGChatPromptRepository(mock_db)
            prompt = RAGChatPrompt(
                id=None,
                document_type_id=10,
                prompt_text="Custom Prompt",
                created_by_user_id=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                multi_query_prompt_text=None
            )
            
            # Act & Assert
            with pytest.raises(ValueError, match="Fehler beim Speichern des Prompts"):
                repo.save(prompt)
            
            mock_db.rollback.assert_called_once()
    
    def test_delete_returns_true_when_prompt_exists(self):
        """Test: Lösche Prompt wenn vorhanden."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_model = Mock()
        mock_model.id = 1
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_model
        mock_db.query.return_value = mock_query
        mock_db.delete = Mock()
        mock_db.commit = Mock()
        
        repo = SQLAlchemyRAGChatPromptRepository(mock_db)
        
        # Act
        result = repo.delete(10)
        
        # Assert
        assert result is True
        mock_db.delete.assert_called_once_with(mock_model)
        mock_db.commit.assert_called_once()
    
    def test_delete_returns_false_when_prompt_not_exists(self):
        """Test: Lösche gibt False zurück wenn Prompt nicht vorhanden."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        repo = SQLAlchemyRAGChatPromptRepository(mock_db)
        
        # Act
        result = repo.delete(10)
        
        # Assert
        assert result is False
    
    def test_get_all_returns_all_prompts(self):
        """Test: Hole alle Prompts."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_model1 = Mock()
        mock_model1.id = 1
        mock_model1.document_type_id = 10
        mock_model1.prompt_text = "Prompt 1"
        mock_model1.multi_query_prompt_text = None
        mock_model1.created_by_user_id = 1
        mock_model1.created_at = datetime.utcnow()
        mock_model1.updated_at = datetime.utcnow()
        
        mock_model2 = Mock()
        mock_model2.id = 2
        mock_model2.document_type_id = 20
        mock_model2.prompt_text = "Prompt 2"
        mock_model2.multi_query_prompt_text = None
        mock_model2.created_by_user_id = 1
        mock_model2.created_at = datetime.utcnow()
        mock_model2.updated_at = datetime.utcnow()
        
        mock_query = Mock()
        mock_query.all.return_value = [mock_model1, mock_model2]
        mock_db.query.return_value = mock_query
        
        repo = SQLAlchemyRAGChatPromptRepository(mock_db)
        
        # Act
        result = repo.get_all()
        
        # Assert
        assert len(result) == 2
        assert result[0].document_type_id == 10
        assert result[1].document_type_id == 20

