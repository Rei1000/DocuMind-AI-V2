"""
LTR Service - High-Level API für Learning-to-Rank.

Infrastructure Layer: Vereinfachte API für LTR-Integration in Use Cases.

Wrapper um Training Pipeline + Inference Service für einfache Integration.
"""

from typing import Dict, Any, Optional
import os
import numpy as np


class LTRService:
    """
    LTR Service - High-Level API.
    
    Vereinfacht die Nutzung von LTR-Modellen in Use Cases:
    - Auto-Loading von Modellen
    - Feature-Extraction + Prediction in einem Schritt
    - Score-Kombination
    - Model-Info
    """
    
    def __init__(
        self,
        model_dir: str = 'data/ml_models',
        model_name: str = 'ltr_ranker_v1.pkl',
        enable_ml: bool = True
    ):
        """
        Initialisiere LTR Service.
        
        Args:
            model_dir: Verzeichnis für ML-Modelle
            model_name: Name der Model-Datei
            enable_ml: Aktiviere ML-Ranking (False = nur Hybrid)
        """
        self.model_dir = model_dir
        self.model_name = model_name
        self.enable_ml = enable_ml
        
        # Model-Pfad
        self.model_path = os.path.join(model_dir, model_name)
        
        # Inference Service
        from .inference_service import LTRInferenceService
        
        if self.enable_ml and os.path.exists(self.model_path):
            self.inference_service = LTRInferenceService(model_path=self.model_path)
            print(f"✅ LTR Service initialisiert mit Model: {self.model_path}")
        else:
            self.inference_service = LTRInferenceService(model_path=None)
            if self.enable_ml:
                print(f"⚠️ LTR Model nicht gefunden: {self.model_path}")
                print("   Fallback: Verwende nur Hybrid-Score")
            else:
                print("ℹ️ LTR deaktiviert (enable_ml=False)")
    
    def is_enabled(self) -> bool:
        """Prüfe ob ML-Ranking aktiviert und ready ist."""
        return self.enable_ml and self.inference_service.is_ready()
    
    def predict_ml_score(
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
        if not self.is_enabled():
            # Fallback zu hybrid_score
            return hybrid_score
        
        # Predict mit Inference Service
        return self.inference_service.predict_for_chunk(
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
    
    def get_final_score(
        self,
        hybrid_score: float,
        ml_score: float
    ) -> float:
        """
        Kombiniere Hybrid-Score und ML-Score zu Final-Score.
        
        Args:
            hybrid_score: Hybrid-Score (0-1)
            ml_score: ML-Score
            
        Returns:
            Final Score (0-1)
        """
        if not self.is_enabled():
            # Fallback zu hybrid_score
            return hybrid_score
        
        return self.inference_service.combine_scores(hybrid_score, ml_score)
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Hole Service-Informationen.
        
        Returns:
            Dict mit Service-Info
        """
        return {
            'enabled': self.enable_ml,
            'ready': self.is_enabled(),
            'model_path': self.model_path,
            'model_exists': os.path.exists(self.model_path) if self.model_path else False,
            'model_info': self.inference_service.get_model_info() if self.inference_service else {}
        }

