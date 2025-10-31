"""
Infrastructure Layer: Sentence Transformers Embedding Adapter

Implementiert den EmbeddingService mit Sentence Transformers (lokal, kostenlos).
Beste Alternative zu OpenAI Embeddings für RAG-Systeme.

Best Practice: Verwendet multilingual-Modelle für deutsche Dokumente.
"""

from typing import List, Optional
import warnings
warnings.filterwarnings("ignore")

from contexts.ragintegration.domain.value_objects import EmbeddingVector
from contexts.ragintegration.domain.repositories import EmbeddingService


class SentenceTransformersEmbeddingAdapter(EmbeddingService):
    """
    Sentence Transformers Implementation des EmbeddingService.
    
    Verwendet lokale Modelle (kostenlos, keine API-Anrufe).
    Sehr gut für RAG-Systeme, besonders für deutsche Dokumente.
    
    Best Practice Modelle:
    - all-MiniLM-L6-v2: Schnell, 384 Dimensionen, gut für englisch/deutsch
    - multilingual-e5-base: Groß, 768 Dimensionen, sehr gut für multilingual
    - paraphrase-multilingual-mpnet-base-v2: Sehr gut für deutsche Texte
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialisiert den Sentence Transformers Adapter.
        
        Args:
            model_name: Name des Modells von Hugging Face
                Empfohlene Modelle:
                - all-MiniLM-L6-v2 (384 dim, schnell, gut)
                - multilingual-e5-base (768 dim, sehr gut für multilingual)
                - paraphrase-multilingual-mpnet-base-v2 (768 dim, best für DE)
        """
        self.model_name = model_name
        
        try:
            from sentence_transformers import SentenceTransformer
            print(f"📥 Lade Sentence Transformers Modell: {model_name}")
            self.model = SentenceTransformer(model_name)
            
            # Hole Dimensionen vom Modell
            # Test mit einem Sample-Text
            sample_embedding = self.model.encode("test", convert_to_numpy=True)
            self.dimension = len(sample_embedding)
            
            print(f"✅ Sentence Transformers Modell geladen:")
            print(f"   Modell: {model_name}")
            print(f"   Dimensionen: {self.dimension}")
            
        except ImportError:
            raise ImportError(
                "sentence-transformers ist nicht installiert. "
                "Installiere mit: pip install sentence-transformers"
            )
        except Exception as e:
            raise RuntimeError(
                f"Fehler beim Laden des Sentence Transformers Modells: {str(e)}"
            )
    
    def generate_embedding(self, text: str) -> EmbeddingVector:
        """Generiert ein Embedding für einen Text."""
        try:
            # Bereite Text vor
            cleaned_text = self._preprocess_text(text)
            
            if not cleaned_text:
                # Fallback für leeren Text
                cleaned_text = " "
            
            # Generiere Embedding
            embedding_array = self.model.encode(
                cleaned_text,
                convert_to_numpy=True,
                normalize_embeddings=True  # Normalisiere für bessere Cosinus-Ähnlichkeit
            )
            
            # Konvertiere zu Liste
            embedding_list = embedding_array.tolist()
            
            return EmbeddingVector(
                vector=embedding_list,
                model=self.model_name,
                dimensions=self.dimension
            )
            
        except Exception as e:
            raise RuntimeError(f"Fehler beim Generieren des Embeddings: {str(e)}")
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[EmbeddingVector]:
        """Generiert Embeddings für mehrere Texte in einem Batch."""
        try:
            # Bereite Texte vor
            cleaned_texts = [self._preprocess_text(text) or " " for text in texts]
            
            # Batch-Encoding ist effizienter
            embeddings_array = self.model.encode(
                cleaned_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                batch_size=32,  # Optimale Batch-Größe
                show_progress_bar=False
            )
            
            # Konvertiere zu EmbeddingVector Objekten
            embeddings = []
            for embedding_array in embeddings_array:
                embedding_list = embedding_array.tolist()
                embeddings.append(EmbeddingVector(
                    vector=embedding_list,
                    model=self.model_name,
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
        
        # Begrenze Länge (Sentence Transformers haben keine strikten Limits,
        # aber sehr lange Texte werden möglicherweise gekürzt)
        max_chars = 50000  # Sicherheitsgrenze
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
            
            # Cosinus-Ähnlichkeit (für normalisierte Embeddings)
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
            'model': self.model_name,
            'dimension': self.dimension,
            'provider': 'sentence-transformers',
            'type': 'local',
            'cost': 'free',
            'best_for': 'RAG, multilingual, German documents'
        }

