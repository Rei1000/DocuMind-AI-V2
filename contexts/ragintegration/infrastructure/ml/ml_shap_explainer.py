"""
ML-SHAP Explainer für Learning-to-Rank Modelle.

Infrastructure Layer: SHAP-Erklärungen für LTR-ML-Modelle.

TDD Phase 2: GREEN - Minimale Implementierung für Tests.

Features:
- TreeExplainer für LightGBM/XGBoost
- KernelExplainer für sklearn Fallback
- SHAP für alle 11 ML-Features
- Feature Importance Aggregation
"""

from typing import Dict, Any, List, Optional
import numpy as np

# SHAP Library
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("WARNING: SHAP library not available")


class MLSHAPExplainer:
    """
    SHAP Explainer für ML-Ranking-Modelle.
    
    Verwendet TreeExplainer für tree-based models (LightGBM, XGBoost)
    oder KernelExplainer für andere Modelle (sklearn).
    """
    
    def __init__(
        self,
        model,
        model_type: str,
        background_data: Optional[np.ndarray] = None,
        feature_names: Optional[List[str]] = None
    ):
        """
        Initialisiere ML-SHAP Explainer.
        
        Args:
            model: Trainiertes ML-Model
            model_type: 'lightgbm', 'xgboost', oder 'sklearn'
            background_data: Background-Daten für KernelExplainer (nur für sklearn)
            feature_names: Namen der 11 Features
        """
        if not SHAP_AVAILABLE:
            raise ImportError("SHAP library not available")
        
        self.model = model
        self.model_type = model_type
        self.background_data = background_data
        self.feature_names = feature_names or self._get_default_feature_names()
        
        # Erstelle passenden Explainer
        if model_type in ['lightgbm', 'xgboost']:
            # TreeExplainer für tree-based models
            self.explainer = shap.TreeExplainer(model)
            self.explainer_type = 'tree'
            print(f"✅ TreeExplainer erstellt für {model_type}")
        else:
            # KernelExplainer für andere Modelle
            if background_data is None:
                raise ValueError("background_data required for KernelExplainer (sklearn models)")
            
            self.explainer = shap.KernelExplainer(
                model=model.predict,
                data=background_data
            )
            self.explainer_type = 'kernel'
            print(f"✅ KernelExplainer erstellt für {model_type}")
    
    def _get_default_feature_names(self) -> List[str]:
        """Hole Default Feature-Namen (11 Features)."""
        return [
            'vector_score',
            'text_score',
            'bm25_score',
            'jaccard_score',
            'keyword_matches',
            'chunk_length',
            'document_type_encoded',
            'heading_hierarchy_depth',
            'confidence_score',
            'user_level',
            'hybrid_score'
        ]
    
    def explain(self, features: np.ndarray) -> Dict[str, Any]:
        """
        Erstelle SHAP-Erklärung für Features.
        
        Args:
            features: Feature-Vector (11,) oder Feature-Matrix (1, 11)
            
        Returns:
            Dict mit SHAP-Explanation
        """
        # Ensure 2D array
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        # Berechne SHAP-Werte
        shap_values = self.explainer.shap_values(features)
        
        # TreeExplainer gibt direkt Array zurück
        # KernelExplainer gibt auch Array zurück
        if isinstance(shap_values, list):
            # Multi-output model - nehme erste Ausgabe
            shap_values = shap_values[0]
        
        # Flatten falls 2D
        if isinstance(shap_values, np.ndarray) and shap_values.ndim == 2:
            shap_values = shap_values[0]
        
        # Base Value
        if hasattr(self.explainer, 'expected_value'):
            if isinstance(self.explainer.expected_value, np.ndarray):
                base_value = float(self.explainer.expected_value[0])
            else:
                base_value = float(self.explainer.expected_value)
        else:
            # Fallback: Durchschnitt der Background-Data Predictions
            base_value = 0.5
        
        # Prediction
        prediction = float(self.model.predict(features)[0])
        
        # Feature Importance (absolute SHAP values)
        feature_importance = {}
        for i, feature_name in enumerate(self.feature_names):
            feature_importance[feature_name] = float(abs(shap_values[i]))
        
        # Erstelle Explanation Dict
        explanation = {
            'feature_names': self.feature_names,
            'shap_values': shap_values.tolist() if isinstance(shap_values, np.ndarray) else list(shap_values),
            'base_value': base_value,
            'prediction': prediction,
            'feature_importance': feature_importance
        }
        
        return explanation
    
    def aggregate_feature_importance(
        self,
        explanations: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Aggregiere Feature Importance über mehrere Explanations.
        
        Berechnet durchschnittliche absolute SHAP-Werte pro Feature.
        
        Args:
            explanations: Liste von SHAP-Explanations
            
        Returns:
            Dict mit aggregierter Feature Importance
        """
        if not explanations:
            return {}
        
        # Sammle alle Feature Importances
        importance_by_feature = {name: [] for name in self.feature_names}
        
        for explanation in explanations:
            for feature, importance in explanation['feature_importance'].items():
                if feature in importance_by_feature:
                    importance_by_feature[feature].append(importance)
        
        # Berechne Durchschnitt
        aggregated = {}
        for feature, importances in importance_by_feature.items():
            if importances:
                aggregated[feature] = float(np.mean(importances))
            else:
                aggregated[feature] = 0.0
        
        return aggregated

