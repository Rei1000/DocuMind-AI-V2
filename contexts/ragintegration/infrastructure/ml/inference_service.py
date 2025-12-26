"""
LTR Inference Service für ML Model Serving.

Infrastructure Layer: Serving-Layer für trainierte LTR-Modelle.

TDD Phase 2: GREEN - Minimale Implementierung für Tests.

Features:
- Model Loading (Pickle)
- ML Predictions
- Score Combination (Hybrid + ML)
- Feature Extraction Integration
- Model Info
"""

from typing import Dict, Any, Optional
import numpy as np
import pickle
import os


class LTRInferenceService:
    """
    LTR Inference Service.
    
    Serving-Layer für trainierte Learning-to-Rank-Modelle.
    Lädt Model bei Init, macht Predictions, kombiniert Scores.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        hybrid_weight: float = 0.6,
        ml_weight: float = 0.4
    ):
        """
        Initialisiere Inference Service.
        
        Args:
            model_path: Pfad zum trainierten Model (None = kein Model, Fallback)
            hybrid_weight: Gewicht für Hybrid-Score (default: 0.6)
            ml_weight: Gewicht für ML-Score (default: 0.4)
        """
        self.model_path = model_path
        self.hybrid_weight = hybrid_weight
        self.ml_weight = ml_weight
        self.model = None
        self.model_type = None
        self.model_version = None
        
        # Feature Extractor
        from .features.feature_extractor import MLFeatureExtractor
        self.feature_extractor = MLFeatureExtractor()
        
        # Lade Model falls Pfad angegeben
        if model_path and os.path.exists(model_path):
            try:
                self._load_model(model_path)
                print(f"✅ LTR Model geladen: {model_path} (Type: {self.model_type}, Version: {self.model_version})")
            except Exception as e:
                print(f"⚠️ Konnte Model nicht laden: {e}")
                print("   Fallback: Verwende nur Hybrid-Score")
        else:
            print("⚠️ Kein Model-Pfad angegeben oder File nicht gefunden")
            print("   Fallback: Verwende nur Hybrid-Score")
    
    def _load_model(self, path: str):
        """Lade Model von Disk."""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
            self.model = model_data['model']
            self.model_type = model_data.get('model_type', 'unknown')
            self.model_version = model_data.get('model_version', '1.0.0')
    
    def is_ready(self) -> bool:
        """Prüfe ob Model geladen und ready ist."""
        return self.model is not None
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """
        Predict ML-Scores für Feature-Matrix.
        
        Args:
            features: Feature-Matrix (n_samples, 11)
            
        Returns:
            numpy array (n_samples,) mit ML-Scores
        """
        if not self.is_ready():
            # Fallback: Verwende hybrid_score (Feature 10)
            if features.ndim == 1:
                return features[10]  # hybrid_score
            else:
                return features[:, 10]  # hybrid_score für alle Samples
        
        # Predict mit ML-Model
        predictions = self.model.predict(features)
        
        # Stelle sicher, dass Rückgabe numpy array ist
        if not isinstance(predictions, np.ndarray):
            predictions = np.array(predictions)
        
        return predictions

    def normalize_scores_minmax(self, scores: np.ndarray, default: float = 0.5) -> np.ndarray:
        """
        Normalisiere ML-Scores per Query via Min-Max auf [0, 1].

        Hintergrund:
        - LTR-Modelle (Regression/Ranker) liefern oft unskalierte Scores (z.B. > 1.0).
        - Für UI-Transparenz (Prozentanzeige) und gewichtete Mischung mit Hybrid (0-1)
          brauchen wir eine stabile Skalierung pro Kandidatenmenge.

        Args:
            scores: Array von Roh-Scores (n_candidates,)
            default: Fallback-Wert, wenn keine Normalisierung möglich ist (z.B. konstante Scores)

        Returns:
            Array gleicher Form, Werte in [0, 1]
        """
        arr = np.asarray(scores, dtype=float)
        if arr.size == 0:
            return arr

        finite_mask = np.isfinite(arr)
        if not finite_mask.any():
            return np.full(arr.shape, float(default), dtype=float)

        min_val = float(np.min(arr[finite_mask]))
        max_val = float(np.max(arr[finite_mask]))
        range_val = max_val - min_val

        if range_val < 1e-12:
            out = np.full(arr.shape, float(default), dtype=float)
        else:
            out = (arr - min_val) / range_val
            out = np.clip(out, 0.0, 1.0)

        # Nicht-finite Werte als default setzen
        out[~finite_mask] = float(default)
        return out
    
    def combine_scores(
        self,
        hybrid_score: float,
        ml_score: float
    ) -> float:
        """
        Kombiniere Hybrid-Score und ML-Score zu Final-Score.
        
        Args:
            hybrid_score: Hybrid-Score (0-1)
            ml_score: ML-Score (kann außerhalb [0, 1] sein für Regression-Modelle)
            
        Returns:
            Final Score (0-1)
        """
        # Normalisiere ml_score falls außerhalb [0, 1]
        ml_score_normalized = np.clip(ml_score, 0.0, 1.0)
        
        # Gewichtete Kombination
        final_score = (self.hybrid_weight * hybrid_score) + (self.ml_weight * ml_score_normalized)
        
        # Clip auf [0, 1]
        final_score = np.clip(final_score, 0.0, 1.0)
        
        return float(final_score)
    
    def predict_for_chunk(
        self,
        query: str,
        chunk: Dict[str, Any],
        vector_score: float,
        text_score: float,
        bm25_score: float,
        jaccard_score: float,
        keyword_matches: int,
        user_level: int,
        hybrid_score: float
    ) -> float:
        """
        Predict ML-Score für einen Chunk.
        
        Extrahiert Features und macht Prediction in einem Schritt.
        
        Args:
            query: Query-String
            chunk: Chunk-Dict
            vector_score: Vektor-Score (0-1)
            text_score: Text-Score (0-1)
            bm25_score: BM25-Score (0-1)
            jaccard_score: Jaccard-Score (0-1)
            keyword_matches: Anzahl Keyword-Matches
            user_level: User-Level (1-5)
            hybrid_score: Hybrid-Score (0-1)
            
        Returns:
            ML-Score (float)
        """
        # Extrahiere Features
        features = self.feature_extractor.extract(
            query=query,
            chunk=chunk,
            vector_score=vector_score,
            text_score=text_score,
            bm25_score=bm25_score,
            jaccard_score=jaccard_score,
            keyword_matches=keyword_matches,
            user_level=user_level,
            hybrid_score=hybrid_score
        )
        
        # Predict
        ml_score = self.predict(features.reshape(1, -1))
        
        # Return als float
        return float(ml_score[0]) if isinstance(ml_score, np.ndarray) else float(ml_score)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Hole Model-Informationen.
        
        Returns:
            Dict mit Model-Info
        """
        return {
            'model_type': self.model_type or 'none',
            'model_version': self.model_version or 'none',
            'model_path': self.model_path or 'none',
            'is_ready': self.is_ready(),
            'hybrid_weight': self.hybrid_weight,
            'ml_weight': self.ml_weight,
            'feature_names': self.feature_extractor.feature_names
        }

