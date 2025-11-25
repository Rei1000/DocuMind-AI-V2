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
                error_str = str(api_error)
                # KEIN FALLBACK MEHR - Fehler direkt weiterwerfen
                if "does not have access to model" in error_str or "model_not_found" in error_str.lower():
                    error_msg = (
                        f"❌ OpenAI API: Model-Zugriff verweigert für {self.model}\n"
                        f"   Fehler: {error_str}\n"
                        f"   💡 Tipp: Bitte überprüfe deinen OpenAI API Key und dessen Zugriff auf das Modell\n"
                        f"   💡 Lösung: Aktiviere Embedding-Modelle im OpenAI Dashboard oder verwende einen anderen Embedding-Service"
                    )
                    print(error_msg)
                    raise RuntimeError(error_msg) from api_error
                elif "invalid_api_key" in error_str.lower() or "api key" in error_str.lower():
                    error_msg = (
                        f"❌ OpenAI API: Ungültiger API Key\n"
                        f"   Fehler: {error_str}\n"
                        f"   💡 Lösung: Überprüfe OPENAI_API_KEY oder OPENAI_GPT5_MINI_API_KEY in .env"
                    )
                    print(error_msg)
                    raise RuntimeError(error_msg) from api_error
                else:
                    error_msg = (
                        f"❌ OpenAI API Fehler: {error_str}\n"
                        f"   💡 Lösung: Überprüfe API Key, Netzwerk-Verbindung und OpenAI Service Status"
                    )
                    print(error_msg)
                    raise RuntimeError(error_msg) from api_error
            
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
                # KEIN FALLBACK MEHR - Fehler direkt weiterwerfen
                error_msg = (
                    f"❌ OpenAI API Fehler beim Batch-Embedding: {api_error}\n"
                    f"   💡 Lösung: Überprüfe API Key, Netzwerk-Verbindung und OpenAI Service Status"
                )
                print(error_msg)
                raise RuntimeError(error_msg) from api_error
            
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
