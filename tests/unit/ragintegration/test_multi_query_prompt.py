"""
TDD Tests für Multi-Query Prompt Management (PHASE 2).

Tests für Custom Multi-Query Prompts in MultiQueryServiceImpl.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from contexts.ragintegration.domain.entities import RAGChatPrompt
from contexts.ragintegration.infrastructure.services import MultiQueryServiceImpl


class TestMultiQueryServiceImpl:
    """Tests für MultiQueryServiceImpl mit Custom Multi-Query Prompts."""
    
    def test_generate_queries_uses_custom_multi_query_prompt_when_available(self):
        """Test: Custom Multi-Query Prompt wird verwendet wenn vorhanden."""
        # Arrange
        mock_ai_service = Mock()
        mock_ai_service.generate_response_async = AsyncMock(return_value={
            "answer": "1. Variante 1\n2. Variante 2\n3. Variante 3",
            "model_used": "gpt-4o-mini"
        })
        
        mock_repo = Mock()
        custom_prompt = RAGChatPrompt(
            id=1,
            document_type_id=10,
            prompt_text="RAG Chat Prompt",
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            multi_query_prompt_text="Erstelle 3 Varianten für: {question}\nFormat: Eine pro Zeile."
        )
        mock_repo.get_by_document_type_id.return_value = custom_prompt
        
        service = MultiQueryServiceImpl(
            ai_service=mock_ai_service,
            rag_chat_prompt_repo=mock_repo
        )
        
        # Act
        import asyncio
        result = asyncio.run(service.generate_queries("Test Frage", document_type_id=10))
        
        # Assert
        assert len(result) > 0
        mock_repo.get_by_document_type_id.assert_called_once_with(10)
        # Prüfe dass Custom Prompt verwendet wurde (enthält "Erstelle 3 Varianten")
        mock_ai_service.generate_response_async.assert_called_once()
        call_args = mock_ai_service.generate_response_async.call_args
        assert "Erstelle 3 Varianten" in call_args.kwargs['question']
        assert "Test Frage" in call_args.kwargs['question']
    
    def test_generate_queries_uses_standard_prompt_when_no_custom(self):
        """Test: Standard-Prompt wird verwendet wenn kein Custom Prompt vorhanden."""
        # Arrange
        mock_ai_service = Mock()
        mock_ai_service.generate_response_async = AsyncMock(return_value={
            "answer": "1. Variante 1\n2. Variante 2",
            "model_used": "gpt-4o-mini"
        })
        
        mock_repo = Mock()
        mock_repo.get_by_document_type_id.return_value = None  # Kein Custom Prompt
        
        service = MultiQueryServiceImpl(
            ai_service=mock_ai_service,
            rag_chat_prompt_repo=mock_repo
        )
        
        # Act
        import asyncio
        result = asyncio.run(service.generate_queries("Test Frage", document_type_id=10))
        
        # Assert
        assert len(result) > 0
        mock_repo.get_by_document_type_id.assert_called_once_with(10)
        # Prüfe dass Standard-Prompt verwendet wurde (enthält "Erstelle 3-5 verschiedene Suchvarianten")
        mock_ai_service.generate_response_async.assert_called_once()
        call_args = mock_ai_service.generate_response_async.call_args
        assert "Erstelle 3-5 verschiedene Suchvarianten" in call_args.kwargs['question']
    
    def test_generate_queries_uses_standard_prompt_when_custom_has_no_multi_query_text(self):
        """Test: Standard-Prompt wird verwendet wenn Custom Prompt kein multi_query_prompt_text hat."""
        # Arrange
        mock_ai_service = Mock()
        mock_ai_service.generate_response_async = AsyncMock(return_value={
            "answer": "1. Variante 1",
            "model_used": "gpt-4o-mini"
        })
        
        mock_repo = Mock()
        custom_prompt = RAGChatPrompt(
            id=1,
            document_type_id=10,
            prompt_text="RAG Chat Prompt",
            created_by_user_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            multi_query_prompt_text=None  # Kein Multi-Query Prompt
        )
        mock_repo.get_by_document_type_id.return_value = custom_prompt
        
        service = MultiQueryServiceImpl(
            ai_service=mock_ai_service,
            rag_chat_prompt_repo=mock_repo
        )
        
        # Act
        import asyncio
        result = asyncio.run(service.generate_queries("Test Frage", document_type_id=10))
        
        # Assert
        assert len(result) > 0
        # Prüfe dass Standard-Prompt verwendet wurde
        call_args = mock_ai_service.generate_response_async.call_args
        assert "Erstelle 3-5 verschiedene Suchvarianten" in call_args.kwargs['question']
    
    def test_generate_queries_works_without_document_type_id(self):
        """Test: generate_queries funktioniert auch ohne document_type_id (Standard-Prompt)."""
        # Arrange
        mock_ai_service = Mock()
        mock_ai_service.generate_response_async = AsyncMock(return_value={
            "answer": "1. Variante 1",
            "model_used": "gpt-4o-mini"
        })
        
        service = MultiQueryServiceImpl(ai_service=mock_ai_service)
        
        # Act
        import asyncio
        result = asyncio.run(service.generate_queries("Test Frage"))
        
        # Assert
        assert len(result) > 0
        # Prüfe dass Standard-Prompt verwendet wurde
        call_args = mock_ai_service.generate_response_async.call_args
        assert "Erstelle 3-5 verschiedene Suchvarianten" in call_args.kwargs['question']
    
    def test_generate_queries_works_without_repo(self):
        """Test: generate_queries funktioniert auch ohne rag_chat_prompt_repo (Standard-Prompt)."""
        # Arrange
        mock_ai_service = Mock()
        mock_ai_service.generate_response_async = AsyncMock(return_value={
            "answer": "1. Variante 1",
            "model_used": "gpt-4o-mini"
        })
        
        service = MultiQueryServiceImpl(ai_service=mock_ai_service, rag_chat_prompt_repo=None)
        
        # Act
        import asyncio
        result = asyncio.run(service.generate_queries("Test Frage", document_type_id=10))
        
        # Assert
        assert len(result) > 0
        # Prüfe dass Standard-Prompt verwendet wurde
        call_args = mock_ai_service.generate_response_async.call_args
        assert "Erstelle 3-5 verschiedene Suchvarianten" in call_args.kwargs['question']

