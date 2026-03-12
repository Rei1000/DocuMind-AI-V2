"""
Infrastructure Layer: Google Gemini Embedding Adapter

Implementiert den EmbeddingService mit Google Gemini Embedding-Modellen.
Standardisiert auf 768 Dimensionen fuer stabile Kompatibilitaet im RAG-Kontext.

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
    
    Verwendet Google Gemini Embedding-Modelle.
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
        # Ziel-Dimension fuer bestehende Collections (historisch 768).
        # Neuere Gemini-Modelle koennen groessere native Dimensionen haben
        # und werden per output_dimensionality auf 768 projiziert.
        self.dimension = 768
        
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
            
            # Generiere Embedding via Google Gemini (mit robustem Modell-Fallback)
            result = self._embed_with_model_fallback(cleaned_text)
            embedding_list = result['embedding']
            
            # Validiere Dimension
            actual_dimension = len(embedding_list)
            if actual_dimension != self.dimension:
                # API-Modelle können sich über Versionen ändern; wir synchronisieren
                # die Dimension zur Laufzeit, statt den Request vollständig scheitern zu lassen.
                print(
                    f"⚠️ Google Embedding-Dimension angepasst: {self.dimension} -> {actual_dimension}"
                )
                self.dimension = actual_dimension
            
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
            
            # Google Gemini unterstützt Batch nicht konsistent über alle Modell-Versionen,
            # deshalb verwenden wir den robusten Einzelaufruf pro Text.
            embeddings = []
            for text in cleaned_texts:
                embeddings.append(self.generate_embedding(text))
            
            return embeddings
            
        except Exception as e:
            raise RuntimeError(f"Fehler beim Batch-Generieren der Embeddings: {str(e)}")

    def _embed_with_model_fallback(self, content: str) -> dict:
        """Versucht Embedding über primäres Modell und kompatible Fallbacks."""
        candidates = [self.model]
        if self.model == "text-embedding-004":
            # Migration: Neues Gemini-Modell statt altem text-embedding-004.
            candidates.append("gemini-embedding-001")
        elif self.model == "embedding-001":
            candidates.append("gemini-embedding-001")

        last_error: Optional[Exception] = None
        for candidate in candidates:
            try:
                request_kwargs = self._build_embed_request_kwargs(candidate, content)
                result = self.genai.embed_content(
                    **request_kwargs
                )
                if not result or 'embedding' not in result:
                    raise ValueError("Google Gemini API hat kein Embedding zurückgegeben")
                if candidate != self.model:
                    print(f"⚠️ Google Embedding Fallback aktiv: {self.model} -> {candidate}")
                    self.model = candidate
                return result
            except Exception as e:
                last_error = e

        raise RuntimeError(
            f"Kein Google Embedding-Modell verfügbar ({', '.join(candidates)}): {last_error}"
        )

    def _build_embed_request_kwargs(self, model: str, content: str) -> dict:
        """Erstellt API-Parameter für kompatible Gemini-Embedding-Requests."""
        kwargs = {
            "model": f"models/{model}",
            "content": content
        }
        if model == "gemini-embedding-001":
            kwargs["output_dimensionality"] = self.dimension
            kwargs["task_type"] = "RETRIEVAL_QUERY"
        return kwargs
    
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

