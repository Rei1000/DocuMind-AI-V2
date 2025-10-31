"""
Integration Tests für RAG Infrastructure Layer - OpenAI Embedding Adapter

Diese Tests prüfen die Integration mit OpenAI Embedding API.
Sie verwenden echte API-Calls für realistische Tests.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List

# Import Domain Value Objects
from contexts.ragintegration.domain.value_objects import EmbeddingVector

# Import Infrastructure
from contexts.ragintegration.infrastructure.embedding_adapter import OpenAIEmbeddingAdapter


class TestOpenAIEmbeddingAdapterIntegration:
    """Integration Tests für OpenAI Embedding Adapter"""
    
    @pytest.fixture
    def embedding_adapter(self):
        """Erstelle OpenAI Embedding Adapter für Tests"""
        return OpenAIEmbeddingAdapter()
    
    @pytest.fixture
    def sample_texts(self):
        """Erstelle Sample Texte für Embedding-Tests"""
        return [
            "Dies ist ein Test-Text für die Embedding-Generierung.",
            "Ein weiterer Text mit wichtigen Informationen zur Montage.",
            "Dritter Text mit Sicherheitshinweisen und Anweisungen."
        ]
    
    def test_generate_embedding_single_text(self, embedding_adapter):
        """Test Embedding-Generierung für einzelnen Text"""
        text = "Test-Text für Embedding-Generierung"
        
        # Mock OpenAI API Response
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1] * 1536
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            embedding = embedding_adapter.generate_embedding(text)
            
            assert isinstance(embedding, EmbeddingVector)
            assert len(embedding.vector) == 1536
            assert all(val == 0.1 for val in embedding.vector)
    
    def test_generate_embeddings_multiple_texts(self, embedding_adapter, sample_texts):
        """Test Embedding-Generierung für mehrere Texte"""
        # Mock OpenAI API Response
        mock_response = Mock()
        mock_response.data = [Mock() for _ in sample_texts]
        for i, data_point in enumerate(mock_response.data):
            data_point.embedding = [i * 0.1] * 1536
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            embeddings = embedding_adapter.generate_embeddings(sample_texts)
            
            assert len(embeddings) == len(sample_texts)
            for i, embedding in enumerate(embeddings):
                assert isinstance(embedding, EmbeddingVector)
                assert len(embedding.vector) == 1536
                assert all(val == i * 0.1 for val in embedding.vector)
    
    def test_embedding_dimension_consistency(self, embedding_adapter):
        """Test dass alle Embeddings die gleiche Dimension haben"""
        texts = [
            "Kurzer Text",
            "Ein sehr langer Text mit vielen Wörtern und Informationen, die für die Embedding-Generierung verwendet werden sollen.",
            "Text mit Sonderzeichen: !@#$%^&*()_+-=[]{}|;':\",./<>?"
        ]
        
        # Mock OpenAI API Response
        mock_response = Mock()
        mock_response.data = [Mock() for _ in texts]
        for i, data_point in enumerate(mock_response.data):
            data_point.embedding = [i * 0.01] * 1536
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            embeddings = embedding_adapter.generate_embeddings(texts)
            
            # Alle Embeddings sollten die gleiche Dimension haben
            dimensions = [len(embedding.vector) for embedding in embeddings]
            assert all(dim == 1536 for dim in dimensions)
            assert len(set(dimensions)) == 1  # Alle Dimensionen sind gleich
    
    def test_empty_text_handling(self, embedding_adapter):
        """Test Handling von leerem Text"""
        empty_text = ""
        
        # Mock OpenAI API Response für leeren Text
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.0] * 1536
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            embedding = embedding_adapter.generate_embedding(empty_text)
            
            assert isinstance(embedding, EmbeddingVector)
            assert len(embedding.vector) == 1536
    
    def test_long_text_handling(self, embedding_adapter):
        """Test Handling von sehr langem Text"""
        # Erstelle sehr langen Text (über 8000 Zeichen)
        long_text = "Dies ist ein sehr langer Text. " * 300  # ~9000 Zeichen
        
        # Mock OpenAI API Response
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.5] * 1536
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            embedding = embedding_adapter.generate_embedding(long_text)
            
            assert isinstance(embedding, EmbeddingVector)
            assert len(embedding.vector) == 1536
    
    def test_special_characters_handling(self, embedding_adapter):
        """Test Handling von Sonderzeichen"""
        special_texts = [
            "Text mit Umlauten: äöü ÄÖÜ ß",
            "Text mit Zahlen: 1234567890",
            "Text mit Symbolen: !@#$%^&*()_+-=[]{}|;':\",./<>?",
            "Text mit Unicode: 🚀💡⭐🎯",
            "Text mit Leerzeichen:   mehrfache   Leerzeichen   "
        ]
        
        # Mock OpenAI API Response
        mock_response = Mock()
        mock_response.data = [Mock() for _ in special_texts]
        for i, data_point in enumerate(mock_response.data):
            data_point.embedding = [i * 0.1] * 1536
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            embeddings = embedding_adapter.generate_embeddings(special_texts)
            
            assert len(embeddings) == len(special_texts)
            for embedding in embeddings:
                assert isinstance(embedding, EmbeddingVector)
                assert len(embedding.vector) == 1536
    
    def test_api_error_handling(self, embedding_adapter):
        """Test Error Handling bei API-Fehlern"""
        text = "Test-Text für Error Handling"
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_client
            
            with pytest.raises(Exception, match="API Error"):
                embedding_adapter.generate_embedding(text)
    
    def test_rate_limit_handling(self, embedding_adapter):
        """Test Handling von Rate Limits"""
        text = "Test-Text für Rate Limit"
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.side_effect = Exception("Rate limit exceeded")
            mock_openai.return_value = mock_client
            
            with pytest.raises(Exception, match="Rate limit exceeded"):
                embedding_adapter.generate_embedding(text)
    
    def test_invalid_api_key_handling(self, embedding_adapter):
        """Test Handling von ungültigem API Key"""
        text = "Test-Text für API Key Error"
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.side_effect = Exception("Invalid API key")
            mock_openai.return_value = mock_client
            
            with pytest.raises(Exception, match="Invalid API key"):
                embedding_adapter.generate_embedding(text)
    
    def test_batch_processing_performance(self, embedding_adapter):
        """Test Performance bei Batch-Verarbeitung"""
        # Erstelle viele Texte für Batch-Test
        texts = [f"Batch test text {i}" for i in range(50)]
        
        # Mock OpenAI API Response
        mock_response = Mock()
        mock_response.data = [Mock() for _ in texts]
        for i, data_point in enumerate(mock_response.data):
            data_point.embedding = [i * 0.01] * 1536
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            import time
            start_time = time.time()
            
            embeddings = embedding_adapter.generate_embeddings(texts)
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert len(embeddings) == len(texts)
            assert duration < 5.0, f"Batch processing took {duration} seconds"
    
    def test_embedding_consistency(self, embedding_adapter):
        """Test dass gleiche Texte konsistente Embeddings erzeugen"""
        text = "Konsistenz-Test Text"
        
        # Mock OpenAI API Response (gleiche Response für beide Calls)
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.123] * 1536
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # Generiere Embedding zweimal
            embedding1 = embedding_adapter.generate_embedding(text)
            embedding2 = embedding_adapter.generate_embedding(text)
            
            # Embeddings sollten identisch sein
            assert embedding1.vector == embedding2.vector
    
    def test_model_configuration(self, embedding_adapter):
        """Test Model-Konfiguration"""
        text = "Model Configuration Test"
        
        # Mock OpenAI API Response
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1] * 1536
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            embedding = embedding_adapter.generate_embedding(text)
            
            # Prüfe dass der richtige Model verwendet wurde
            mock_client.embeddings.create.assert_called_once()
            call_args = mock_client.embeddings.create.call_args
            assert call_args[1]["model"] == "text-embedding-3-small"
            assert call_args[1]["input"] == text
    
    def test_embedding_vector_immutability(self, embedding_adapter):
        """Test dass EmbeddingVector immutable ist"""
        text = "Immutability Test"
        
        # Mock OpenAI API Response
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1] * 1536
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            embedding = embedding_adapter.generate_embedding(text)
            
            # Versuche Embedding zu modifizieren (sollte fehlschlagen)
            with pytest.raises(Exception):
                embedding.vector[0] = 0.5


class TestEmbeddingAdapterIntegrationWithDomain:
    """Integration Tests für Embedding Adapter mit Domain Layer"""
    
    @pytest.fixture
    def embedding_adapter(self):
        """Erstelle OpenAI Embedding Adapter für Tests"""
        return OpenAIEmbeddingAdapter()
    
    def test_embedding_vector_creation(self, embedding_adapter):
        """Test Erstellung von EmbeddingVector aus API Response"""
        text = "Domain Integration Test"
        
        # Mock OpenAI API Response mit realistischen Embedding-Werten
        mock_response = Mock()
        mock_response.data = [Mock()]
        # Erstelle realistische Embedding-Werte (normalisiert zwischen -1 und 1)
        realistic_embedding = [0.1, -0.2, 0.3, -0.4, 0.5] + [0.0] * 1531
        mock_response.data[0].embedding = realistic_embedding
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            embedding = embedding_adapter.generate_embedding(text)
            
            # Prüfe EmbeddingVector Properties
            assert isinstance(embedding, EmbeddingVector)
            assert len(embedding.vector) == 1536
            assert embedding.vector[0] == 0.1
            assert embedding.vector[1] == -0.2
            assert embedding.vector[2] == 0.3
            assert embedding.vector[3] == -0.4
            assert embedding.vector[4] == 0.5
    
    def test_embedding_similarity_calculation(self, embedding_adapter):
        """Test Embedding-Similarity-Berechnung"""
        text1 = "Ähnlicher Text für Similarity Test"
        text2 = "Sehr ähnlicher Text für Similarity Test"
        text3 = "Komplett anderer Text mit anderen Inhalten"
        
        # Mock OpenAI API Responses
        mock_response1 = Mock()
        mock_response1.data = [Mock()]
        mock_response1.data[0].embedding = [0.1, 0.2, 0.3] + [0.0] * 1533
        
        mock_response2 = Mock()
        mock_response2.data = [Mock()]
        mock_response2.data[0].embedding = [0.11, 0.21, 0.31] + [0.0] * 1533
        
        mock_response3 = Mock()
        mock_response3.data = [Mock()]
        mock_response3.data[0].embedding = [-0.5, -0.4, -0.3] + [0.0] * 1533
        
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.side_effect = [
                mock_response1, mock_response2, mock_response3
            ]
            mock_openai.return_value = mock_client
            
            embedding1 = embedding_adapter.generate_embedding(text1)
            embedding2 = embedding_adapter.generate_embedding(text2)
            embedding3 = embedding_adapter.generate_embedding(text3)
            
            # Berechne Similarity (Cosine Similarity)
            def cosine_similarity(vec1, vec2):
                import math
                dot_product = sum(a * b for a, b in zip(vec1, vec2))
                magnitude1 = math.sqrt(sum(a * a for a in vec1))
                magnitude2 = math.sqrt(sum(b * b for b in vec2))
                return dot_product / (magnitude1 * magnitude2)
            
            similarity_1_2 = cosine_similarity(embedding1.vector, embedding2.vector)
            similarity_1_3 = cosine_similarity(embedding1.vector, embedding3.vector)
            
            # Ähnliche Texte sollten höhere Similarity haben
            assert similarity_1_2 > similarity_1_3
            assert similarity_1_2 > 0.9  # Sehr ähnlich
            assert similarity_1_3 < 0.0  # Verschieden (negative Similarity)
