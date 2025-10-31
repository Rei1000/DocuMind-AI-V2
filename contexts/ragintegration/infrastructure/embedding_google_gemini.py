"""
Infrastructure Layer: Google Gemini Embedding Adapter

Implementiert den EmbeddingService mit Google Gemini text-embedding-004.
768 Dimensionen, sehr gut für multilingual (inkl. Deutsch).

Best Practice: Gut für RAG-Systeme, kostenlos mit Google AI API Key.
"""

from typing import List, Optional
import warnings
warnings.filterwarnings("ignore")

from contexts.ragintegration.domain.value_objects import EmbeddingVector
from contexts.ragintegration.domain.repositories import EmbeddingService


class GoogleGeminiEmbeddingAdapter(EmbeddingService):
    """
    Google Gemini Implementation des EmbeddingService.
    
    Verwendet Google Gemini text-embedding-004 (768 Dimensionen).
    Sehr gut für RAG-Systeme, besonders für multilingual.
    
    Best Practice:
    - Kostenlos mit Google AI API Key
    - 768 Dimensionen (balanciert zwischen Qualität und Speed)
    - Sehr gut für deutsche Dokumente
    """
    
    def __init__(self, api_key: str, model: str = "text-embedding-004"):
        """
        Initialisiert den Google Gemini Embedding Adapter.
        
        Args:
            api_key: Google AI API Key
            model: Modell-Name (default: text-embedding-004)
        """
        self.api_key = api_key
        self.model = model
        self.dimension = 768  # text-embedding-004 hat 768 Dimensionen
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.genai = genai
            print(f"✅ Google Gemini Embedding Service initialisiert")
            print(f"   Modell: {model}")
            print(f"   Dimensionen: {self.dimension}")
        except ImportError:
            raise ImportError(
                "google-generativeai ist nicht installiert. "
                "Installiere mit: pip install google-generativeai"
            )
        except Exception as e:
            raise RuntimeError(
                f"Fehler beim Initialisieren des Google Gemini Embedding Service: {str(e)}"
            )
    
    def generate_embedding(self, text: str) -> EmbeddingVector:
        """Generiert ein Embedding für einen Text."""
        try:
            # Bereite Text vor
            cleaned_text = self._preprocess_text(text)
            
            if not cleaned_text:
                # Fallback für leeren Text
                cleaned_text = " "
            
            # Generiere Embedding via Google Gemini
            result = self.genai.embed_content(
                model=f"models/{self.model}",
                content=cleaned_text
            )
            
            if not result or 'embedding' not in result:
                raise ValueError("Google Gemini API hat kein Embedding zurückgegeben")
            
            embedding_list = result['embedding']
            
            # Validiere Dimension
            if len(embedding_list) != self.dimension:
                raise ValueError(
                    f"Unerwartete Embedding-Dimension: {len(embedding_list)} "
                    f"(erwartet: {self.dimension})"
                )
            
            return EmbeddingVector(
                vector=embedding_list,
                model=self.model,
                dimensions=self.dimension
            )
            
        except Exception as e:
            raise RuntimeError(f"Fehler beim Generieren des Embeddings: {str(e)}")
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[EmbeddingVector]:
        """Generiert Embeddings für mehrere Texte in einem Batch."""
        try:
            # Bereite Texte vor
            cleaned_texts = [self._preprocess_text(text) or " " for text in texts]
            
            # Google Gemini unterstützt Batch-Embeddings
            embeddings = []
            for text in cleaned_texts:
                result = self.genai.embed_content(
                    model=f"models/{self.model}",
                    content=text
                )
                
                if not result or 'embedding' not in result:
                    raise ValueError(f"Google Gemini API hat kein Embedding für Text zurückgegeben")
                
                embedding_list = result['embedding']
                
                embeddings.append(EmbeddingVector(
                    vector=embedding_list,
                    model=self.model,
                    dimensions=self.dimension
                ))
            
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
        
        # Begrenze Länge (Google Gemini hat Limits)
        max_chars = 30000  # Sicherheitsgrenze
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
            'provider': 'google-gemini',
            'type': 'api',
            'cost': 'free_with_api_key',
            'best_for': 'RAG, multilingual, German documents'
        }

