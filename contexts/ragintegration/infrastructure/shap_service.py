"""
SHAP Explanation Service für RAG Integration.

Infrastructure Layer: Implementiert SHAP-basierte Erklärungen für RAG-Suche.

TDD Phase 1: GREEN - Minimaler Code für Tests.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class SHAPExplanation:
    """SHAP Explanation Dataclass.
    
    Repräsentiert eine SHAP-Erklärung für einen RAG-Such-Ergebnis.
    """
    feature_importance: Dict[str, float]
    base_value: float
    shap_values: List[float]
    expected_value: float
    prediction: float
    query: str
    chunk_id: str
    timestamp: datetime
    features: Dict[str, float]
    feature_names: Optional[List[str]] = None  # NEU: Feature-Namen für Frontend
    
    def __post_init__(self):
        """Setze feature_names automatisch aus feature_importance.keys() wenn nicht gesetzt."""
        if self.feature_names is None:
            self.feature_names = list(self.feature_importance.keys())


class SHAPExplanationService:
    """
    Service für SHAP-basierte Erklärungen von RAG-Suche.
    
    Erstellt SHAP-Erklärungen für jeden gefundenen Chunk, um zu verstehen,
    welche Features (vector_score, text_score, keyword_matches, etc.) am
    meisten zur Relevanz beitragen.
    """
    
    def __init__(self):
        """Initialisiere SHAP Explanation Service."""
        pass
    
    def explain_search_result(
        self,
        query: str,
        chunk: Dict[str, Any],
        vector_score: float,
        text_score: float,
        hybrid_score: float,
        document_type: str,
        user_level: int,
        keyword_matches: int,
        chunk_length: int,
        heading_hierarchy_depth: int,
        confidence_score: float
    ) -> SHAPExplanation:
        """
        Erstelle SHAP-Erklärung für ein Such-Ergebnis.
        
        Args:
            query: Die ursprüngliche Query
            chunk: Chunk-Daten (muss 'chunk_id' enthalten)
            vector_score: Vektor-Ähnlichkeits-Score (0-1)
            text_score: Text-Matching-Score (0-1)
            hybrid_score: Kombinierter Score (0-1)
            document_type: Dokumenttyp
            user_level: User-Level (1-5)
            keyword_matches: Anzahl der Keyword-Matches
            chunk_length: Chunk-Länge in Zeichen
            heading_hierarchy_depth: Tiefe der Heading-Hierarchie
            confidence_score: Confidence-Score (0-1)
            
        Returns:
            SHAPExplanation mit Feature-Importance
        """
        chunk_id = chunk.get('chunk_id', 'unknown')
        
        # Normalisiere Features für SHAP
        normalized_features = {
            'vector_score': vector_score,
            'text_score': text_score,
            'user_level': user_level / 5.0,  # Normalisiere auf 0-1 (5/5 = 1.0)
            'keyword_matches': keyword_matches / 10.0,  # Normalisiere auf 0-1 (2/10 = 0.2)
            'chunk_length': min(chunk_length / 2000.0, 1.0),  # Normalisiere auf 0-1 (max 2000 Zeichen)
            'heading_hierarchy_depth': min(heading_hierarchy_depth / 5.0, 1.0),  # Normalisiere auf 0-1 (max 5 Ebenen)
            'confidence_score': confidence_score
        }
        
        # Berechne Feature-Importance (vereinfachte SHAP-Approximation)
        # In einer echten Implementierung würde hier SHAP verwendet werden
        # Für GREEN-Phase: Einfache Heuristik basierend auf Feature-Werten
        
        feature_importance = {}
        shap_values = []
        
        # Vector Score Importance (höherer Score = höhere Importance)
        vector_importance = vector_score * 0.4  # 40% Gewichtung
        feature_importance['vector_score'] = vector_importance
        shap_values.append(vector_importance)
        
        # Text Score Importance (höherer Score = höhere Importance)
        text_importance = text_score * 0.3  # 30% Gewichtung
        feature_importance['text_score'] = text_importance
        shap_values.append(text_importance)
        
        # Keyword Matches Importance (mehr Matches = höhere Importance)
        keyword_importance = normalized_features['keyword_matches'] * 0.2  # 20% Gewichtung
        feature_importance['keyword_matches'] = keyword_importance
        shap_values.append(keyword_importance)
        
        # User Level Importance (höheres Level = höhere Importance)
        user_level_importance = normalized_features['user_level'] * 0.05  # 5% Gewichtung
        feature_importance['user_level'] = user_level_importance
        shap_values.append(user_level_importance)
        
        # Chunk Length Importance (mittlere Länge = höhere Importance)
        chunk_length_importance = normalized_features['chunk_length'] * 0.03  # 3% Gewichtung
        feature_importance['chunk_length'] = chunk_length_importance
        shap_values.append(chunk_length_importance)
        
        # Heading Hierarchy Depth Importance
        heading_importance = normalized_features['heading_hierarchy_depth'] * 0.01  # 1% Gewichtung
        feature_importance['heading_hierarchy_depth'] = heading_importance
        shap_values.append(heading_importance)
        
        # Confidence Score Importance
        confidence_importance = normalized_features['confidence_score'] * 0.01  # 1% Gewichtung
        feature_importance['confidence_score'] = confidence_importance
        shap_values.append(confidence_importance)
        
        # Base Value: Durchschnittlicher Score (vereinfacht)
        base_value = 0.5
        
        # Expected Value: Erwarteter Score (vereinfacht)
        expected_value = base_value
        
        return SHAPExplanation(
            feature_importance=feature_importance,
            base_value=base_value,
            shap_values=shap_values,
            expected_value=expected_value,
            prediction=hybrid_score,  # Prediction entspricht hybrid_score
            query=query,
            chunk_id=str(chunk_id),
            timestamp=datetime.now(),
            features=normalized_features,
            feature_names=list(feature_importance.keys())  # NEU: Feature-Namen aus Keys extrahieren
        )

