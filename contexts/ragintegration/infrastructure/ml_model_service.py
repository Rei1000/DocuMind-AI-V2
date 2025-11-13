"""
ML Model Service für RAG Integration.

TDD Phase 4: GREEN - Minimaler Code für Tests.

Service für Training und Prediction mit Learning-to-Rank Model.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from contexts.ragintegration.infrastructure.ml_models import LearningToRankModel
from contexts.ragintegration.domain.entities import TrainingData
from contexts.ragintegration.domain.repositories import TrainingDataRepository


class MLModelService:
    """
    Service für ML Model Training und Prediction.
    
    Koordiniert:
    - Training Data Repository
    - Learning-to-Rank Model
    - Model Evaluation
    """
    
    def __init__(self, training_data_repo: TrainingDataRepository):
        """
        Initialisiere ML Model Service.
        
        Args:
            training_data_repo: TrainingDataRepository Instance
        """
        self.training_data_repo = training_data_repo
        self.model = LearningToRankModel()
    
    def train_model(
        self,
        with_feedback: Optional[bool] = None,
        with_shap: Optional[bool] = None,
        user_id: Optional[int] = None,
        document_type: Optional[str] = None,
        limit: int = 10000
    ) -> Dict[str, Any]:
        """
        Trainiere Model mit Training Data.
        
        Args:
            with_feedback: Filtert nach Daten mit/ohne User-Feedback
            with_shap: Filtert nach Daten mit/ohne SHAP-Erklärung
            user_id: Filtert nach User-ID
            document_type: Filtert nach Dokumenttyp
            limit: Maximale Anzahl Einträge
        
        Returns:
            Dict mit Training-Ergebnis (success, metrics, training_samples)
        """
        # Hole Training Data (synchron, da Repository synchron ist)
        training_data = self.training_data_repo.get_training_data(
            with_feedback=with_feedback,
            with_shap=with_shap,
            user_id=user_id,
            document_type=document_type,
            limit=limit
        )
        
        # Trainiere Model
        self.model.train(training_data)
        
        # Evaluiere Model (mit denselben Daten für jetzt)
        metrics = self.model.evaluate(training_data)
        
        return {
            "success": True,
            "metrics": metrics,
            "training_samples": len(training_data)
        }
    
    def predict_score(self, features: Dict[str, Any]) -> float:
        """
        Vorhersage Score für Features.
        
        Args:
            features: Dict mit Feature-Werten
        
        Returns:
            Predicted Score (0.0-1.0)
        """
        return self.model.predict(features)
    
    def get_model_performance(self) -> Dict[str, Any]:
        """
        Hole Model Performance Metriken.
        
        Returns:
            Dict mit Metriken (accuracy, precision, recall, f1_score, training_samples)
        """
        # Hole Training Data für Evaluation (synchron, da Repository synchron ist)
        training_data = self.training_data_repo.get_training_data(
            limit=1000  # Für Evaluation: kleinere Stichprobe
        )
        
        # Evaluiere Model
        metrics = self.model.evaluate(training_data)
        
        # Hole Statistiken (synchron)
        stats = self.training_data_repo.get_statistics()
        
        return {
            "accuracy": metrics["accuracy"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1_score": metrics["f1_score"],
            "training_samples": stats["total_count"]
        }

