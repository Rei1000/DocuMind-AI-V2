"""
Infrastructure Layer: OpenAI Embedding Adapter

Implementiert den EmbeddingService mit OpenAI text-embedding-3-small.
"""

from typing import List, Optional
import openai
from openai import OpenAI

from contexts.ragintegration.domain.value_objects import EmbeddingVector
from contexts.ragintegration.domain.repositories import EmbeddingService


class OpenAIEmbeddingAdapter(EmbeddingService):
    """OpenAI Implementation des EmbeddingService."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """Initialisiert den OpenAI Client."""
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.dimension = 1536  # text-embedding-3-small hat 1536 Dimensionen
    
    def generate_embedding(self, text: str) -> EmbeddingVector:
        """Generiert ein Embedding für einen Text."""
        try:
            # Bereite Text vor
            cleaned_text = self._preprocess_text(text)
            
            # Für lokale Entwicklung: Mock Embedding falls API nicht verfügbar
            try:
                # OpenAI API Call
                response = self.client.embeddings.create(
                    model=self.model,
                    input=cleaned_text
                )
                
                # Extrahiere Embedding
                embedding_data = response.data[0].embedding
                
                return EmbeddingVector(
                    vector=embedding_data,
                    model=self.model,
                    dimensions=len(embedding_data)
                )
                
            except Exception as api_error:
                # Fallback: Mock Embedding für lokale Entwicklung
                print(f"⚠️ OpenAI API nicht verfügbar: {api_error}")
                print("🔄 Verwende Mock Embedding für lokale Entwicklung...")
                
                # Erstelle Mock Embedding basierend auf Text-Hash
                import hashlib
                text_hash = hashlib.md5(cleaned_text.encode()).hexdigest()
                
                # Konvertiere Hash zu 1536-dimensionalem Vektor
                mock_vector = []
                for i in range(0, len(text_hash), 2):
                    hex_pair = text_hash[i:i+2]
                    value = int(hex_pair, 16) / 255.0  # Normalisiere zu 0-1
                    mock_vector.append(value)
                
                # Fülle auf 1536 Dimensionen auf
                while len(mock_vector) < 1536:
                    mock_vector.append(0.0)
                
                return EmbeddingVector(
                    vector=mock_vector[:1536],
                    model=self.model,
                    dimensions=1536
                )
            
        except Exception as e:
            raise RuntimeError(f"Fehler beim Generieren des Embeddings: {str(e)}")
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[EmbeddingVector]:
        """Generiert Embeddings für mehrere Texte in einem Batch."""
        try:
            # Bereite Texte vor
            cleaned_texts = [self._preprocess_text(text) for text in texts]
            
            # Für lokale Entwicklung: Mock Embeddings falls API nicht verfügbar
            try:
                # OpenAI API Call für Batch
                response = self.client.embeddings.create(
                    model=self.model,
                    input=cleaned_texts
                )
                
                # Konvertiere zu EmbeddingVector Objekten
                embeddings = []
                for embedding_data in response.data:
                    embeddings.append(EmbeddingVector(
                        vector=embedding_data.embedding,
                        model=self.model,
                        dimensions=len(embedding_data.embedding)
                    ))
                
                return embeddings
                
            except Exception as api_error:
                # Fallback: Mock Embeddings für lokale Entwicklung
                print(f"⚠️ OpenAI API nicht verfügbar: {api_error}")
                print("🔄 Verwende Mock Embeddings für lokale Entwicklung...")
                
                embeddings = []
                for text in cleaned_texts:
                    embedding = self.generate_embedding(text)  # Verwendet Mock-Fallback
                    embeddings.append(embedding)
                
                return embeddings
            
        except Exception as e:
            raise RuntimeError(f"Fehler beim Batch-Generieren der Embeddings: {str(e)}")
    
    def get_dimensions(self) -> int:
        """Gibt die Anzahl der Embedding-Dimensionen zurück."""
        return self.dimension
    
    def _preprocess_text(self, text: str) -> str:
        """Bereitet Text für Embedding vor."""
        if not text:
            return ""
        
        # Entferne überflüssige Whitespaces
        cleaned = " ".join(text.split())
        
        # Begrenze Länge (OpenAI Limit: 8192 Tokens)
        # Grobe Schätzung: 1 Token ≈ 4 Zeichen
        max_chars = 30000  # Sicherheitspuffer
        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars]
        
        return cleaned
    
    def calculate_similarity(self, embedding1: EmbeddingVector, embedding2: EmbeddingVector) -> float:
        """Berechnet die Cosinus-Ähnlichkeit zwischen zwei Embeddings."""
        try:
            import numpy as np
            
            # Konvertiere zu numpy arrays
            vec1 = np.array(embedding1.vector)
            vec2 = np.array(embedding2.vector)
            
            # Cosinus-Ähnlichkeit
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            raise RuntimeError(f"Fehler bei der Ähnlichkeitsberechnung: {str(e)}")
    
    def find_most_similar(
        self, 
        query_embedding: EmbeddingVector, 
        candidate_embeddings: List[EmbeddingVector],
        top_k: int = 5
    ) -> List[tuple[EmbeddingVector, float]]:
        """Findet die ähnlichsten Embeddings zu einem Query."""
        try:
            similarities = []
            
            for candidate in candidate_embeddings:
                similarity = self.calculate_similarity(query_embedding, candidate)
                similarities.append((candidate, similarity))
            
            # Sortiere nach Ähnlichkeit (absteigend)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            raise RuntimeError(f"Fehler bei der Ähnlichkeitssuche: {str(e)}")
    
    def validate_embedding(self, embedding: EmbeddingVector) -> bool:
        """Validiert ein Embedding."""
        try:
            # Prüfe Dimension
            if len(embedding.vector) != self.dimension:
                return False
            
            # Prüfe auf NaN oder Inf Werte
            import math
            for value in embedding.vector:
                if math.isnan(value) or math.isinf(value):
                    return False
            
            # Prüfe ob alle Werte numerisch sind
            for value in embedding.vector:
                if not isinstance(value, (int, float)):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def get_model_info(self) -> dict:
        """Gibt Informationen über das verwendete Modell zurück."""
        return {
            'model': self.model,
            'dimension': self.dimension,
            'provider': 'OpenAI',
            'max_tokens': 8192,
            'cost_per_1k_tokens': 0.00002  # text-embedding-3-small (günstiger)
        }
