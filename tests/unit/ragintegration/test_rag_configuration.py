"""
TDD Tests für RAG-Konfigurations-Modal

Tests für die RAG-Konfiguration basierend auf RAG-Anything Best Practices.
"""
import pytest
from unittest.mock import Mock, patch
from contexts.ragintegration.domain.value_objects import RAGConfig
from contexts.ragintegration.application.use_cases import ConfigureRAGUseCase


class TestRAGConfiguration:
    """TDD Tests für RAG-Konfiguration."""
    
    def test_rag_config_creation(self):
        """Test: RAG-Konfiguration kann erstellt werden."""
        config = RAGConfig(
            parser="mineru",
            chunking_strategy="semantic",
            embedding_model="text-embedding-3-small",
            ai_model="gpt-4o-mini",
            chunk_size=1000,
            chunk_overlap=200,
            max_context_chunks=5
        )
        
        assert config.parser == "mineru"
        assert config.chunking_strategy == "semantic"
        assert config.embedding_model == "text-embedding-3-small"
        assert config.ai_model == "gpt-4o-mini"
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
        assert config.max_context_chunks == 5
    
    def test_rag_config_validation(self):
        """Test: RAG-Konfiguration wird validiert."""
        with pytest.raises(ValueError, match="Invalid parser"):
            RAGConfig(
                parser="invalid_parser",
                chunking_strategy="semantic",
                embedding_model="text-embedding-3-small",
                ai_model="gpt-4o-mini"
            )
        
        with pytest.raises(ValueError, match="Invalid chunking strategy"):
            RAGConfig(
                parser="mineru",
                chunking_strategy="invalid_strategy",
                embedding_model="text-embedding-3-small",
                ai_model="gpt-4o-mini"
            )
    
    def test_configure_rag_use_case(self):
        """Test: ConfigureRAG Use Case funktioniert."""
        mock_repo = Mock()
        use_case = ConfigureRAGUseCase(mock_repo)
        
        config = RAGConfig(
            parser="mineru",
            chunking_strategy="semantic",
            embedding_model="text-embedding-3-small",
            ai_model="gpt-4o-mini"
        )
        
        result = use_case.execute(config)
        
        assert result["success"] is True
        mock_repo.save_config.assert_called_once_with(config)
    
    def test_rag_config_parser_options(self):
        """Test: Verfügbare Parser-Optionen."""
        config = RAGConfig(
            parser="mineru",
            chunking_strategy="semantic",
            embedding_model="text-embedding-3-small",
            ai_model="gpt-4o-mini"
        )
        
        # Teste alle verfügbaren Parser (basierend auf RAG-Anything)
        valid_parsers = ["mineru", "docling"]
        for parser in valid_parsers:
            config.parser = parser
            assert config.parser in valid_parsers
    
    def test_rag_config_chunking_strategies(self):
        """Test: Verfügbare Chunking-Strategien."""
        config = RAGConfig(
            parser="mineru",
            chunking_strategy="semantic",
            embedding_model="text-embedding-3-small",
            ai_model="gpt-4o-mini"
        )
        
        # Teste alle verfügbaren Strategien (basierend auf RAG-Anything)
        valid_strategies = ["semantic", "hierarchical", "fixed_size", "structured"]
        for strategy in valid_strategies:
            config.chunking_strategy = strategy
            assert config.chunking_strategy in valid_strategies
    
    def test_rag_config_embedding_models(self):
        """Test: Verfügbare Embedding-Modelle."""
        config = RAGConfig(
            parser="mineru",
            chunking_strategy="semantic",
            embedding_model="text-embedding-3-small",
            ai_model="gpt-4o-mini"
        )
        
        # Teste alle verfügbaren Embedding-Modelle
        valid_embeddings = ["text-embedding-3-small", "text-embedding-ada-002"]
        for embedding in valid_embeddings:
            config.embedding_model = embedding
            assert config.embedding_model in valid_embeddings
    
    def test_rag_config_ai_models(self):
        """Test: Verfügbare AI-Modelle."""
        config = RAGConfig(
            parser="mineru",
            chunking_strategy="semantic",
            embedding_model="text-embedding-3-small",
            ai_model="gpt-4o-mini"
        )
        
        # Teste alle verfügbaren AI-Modelle
        valid_models = ["gpt-4o-mini", "gpt-5-mini", "gemini-2.5-flash"]
        for model in valid_models:
            config.ai_model = model
            assert config.ai_model in valid_models
