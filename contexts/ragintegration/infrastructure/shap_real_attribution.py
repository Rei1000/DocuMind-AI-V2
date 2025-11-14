"""
ECHTE SHAP-Attribution für RAG Integration.

Infrastructure Layer: Implementiert ECHTE SHAP-basierte Erklärungen mit SHAP-Library.

TDD Phase 2: GREEN - Minimale Implementierung für Tests.

Komponenten:
1. FeatureExtractor - Konsistente Feature-Extraktion
2. RankingModelWrapper - sklearn-kompatibles Ranking Model
3. SHAPExplainerService - Echte SHAP-Berechnung mit KernelExplainer
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np

# SHAP-Library (wird über requirements.txt installiert)
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("WARNING: SHAP library not available. Install with: pip install shap")


@dataclass
class SHAPExplanation:
    """
    SHAP Explanation Dataclass.
    
    Repräsentiert eine ECHTE SHAP-Erklärung für ein RAG-Such-Ergebnis.
    """
    feature_importance: Dict[str, float]  # {'vector_score': 0.15, ...}
    base_value: float  # Durchschnittlicher Score (SHAP base value)
    shap_values: List[float]  # ECHTE SHAP-Werte pro Feature
    expected_value: float  # Erwarteter Score (= base_value für KernelExplainer)
    prediction: float  # Tatsächlicher Score (hybrid_score)
    query: str  # Ursprüngliche Query
    chunk_id: str  # Chunk-ID
    timestamp: datetime  # Zeitstempel
    features: Dict[str, float]  # Normalisierte Feature-Werte


class FeatureExtractor:
    """
    Feature Extractor für konsistente Feature-Extraktion.
    
    Extrahiert 7 Features aus Chunk-Daten und normalisiert sie auf [0, 1].
    Wichtig für SHAP-Konsistenz: Gleiche Features für Training & Inference.
    """
    
    def __init__(self):
        """Initialisiere Feature Extractor."""
        self._feature_names = [
            'vector_score',
            'text_score',
            'user_level',
            'keyword_matches',
            'chunk_length',
            'heading_hierarchy_depth',
            'confidence_score'
        ]
    
    @property
    def feature_names(self) -> List[str]:
        """Gibt Feature-Namen zurück (für SHAP-Visualisierung)."""
        return self._feature_names
    
    def extract(
        self,
        query: str,
        chunk: Dict[str, Any],
        vector_score: float,
        text_score: float,
        user_level: int,
        keyword_matches: int
    ) -> np.ndarray:
        """
        Extrahiere Features aus Chunk-Daten.
        
        Args:
            query: Query-String
            chunk: Chunk-Dict mit metadata
            vector_score: Vektor-Ähnlichkeits-Score (0-1)
            text_score: Text-Matching-Score (0-1)
            user_level: User-Level (1-5)
            keyword_matches: Anzahl Keyword-Matches
            
        Returns:
            numpy array (7,) mit normalisierten Features [0, 1]
        """
        metadata = chunk.get('metadata', {})
        
        # Feature 0: vector_score (bereits normalisiert)
        f_vector = float(vector_score)
        
        # Feature 1: text_score (bereits normalisiert)
        f_text = float(text_score)
        
        # Feature 2: user_level (normalisiert auf 0-1)
        f_user_level = float(user_level) / 5.0
        
        # Feature 3: keyword_matches (normalisiert auf 0-1, max 10 assumed)
        f_keyword = min(float(keyword_matches) / 10.0, 1.0)
        
        # Feature 4: chunk_length (normalisiert auf 0-1, max 2000 assumed)
        chunk_length = metadata.get('chunk_length', 0)
        f_chunk_length = min(float(chunk_length) / 2000.0, 1.0)
        
        # Feature 5: heading_hierarchy_depth (normalisiert auf 0-1, max 5 assumed)
        heading_depth = metadata.get('heading_hierarchy_depth', 0)
        f_heading_depth = min(float(heading_depth) / 5.0, 1.0)
        
        # Feature 6: confidence_score (bereits normalisiert)
        f_confidence = float(metadata.get('confidence_score', 0.0))
        
        # Als numpy array zurückgeben
        features = np.array([
            f_vector,
            f_text,
            f_user_level,
            f_keyword,
            f_chunk_length,
            f_heading_depth,
            f_confidence
        ], dtype=np.float64)
        
        return features
    
    def extract_batch(self, chunks_data: List[Dict[str, Any]]) -> np.ndarray:
        """
        Extrahiere Features für Batch von Chunks.
        
        Args:
            chunks_data: Liste von Dicts mit keys: query, chunk, vector_score, 
                        text_score, user_level, keyword_matches
                        
        Returns:
            numpy array (n_samples, 7) mit normalisierten Features
        """
        features_list = []
        
        for data in chunks_data:
            features = self.extract(
                query=data['query'],
                chunk=data['chunk'],
                vector_score=data['vector_score'],
                text_score=data['text_score'],
                user_level=data['user_level'],
                keyword_matches=data['keyword_matches']
            )
            features_list.append(features)
        
        # Stack to 2D array
        return np.array(features_list, dtype=np.float64)


class RankingModelWrapper:
    """
    Ranking Model Wrapper - sklearn-kompatibles Interface.
    
    Umhüllt das bestehende Hybrid-Scoring als ML-Modell für SHAP.
    Implementiert predict(X) Methode für sklearn-Kompatibilität.
    """
    
    def __init__(self):
        """Initialisiere Ranking Model Wrapper."""
        # Gewichte für Hybrid-Scoring
        self.vector_weight = 0.7
        self.text_weight = 0.3
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict Ranking-Scores für Feature-Matrix X.
        
        Args:
            X: Feature-Matrix (n_samples, 7) mit normalisierten Features
               Spalten: [vector_score, text_score, user_level, keyword_matches, 
                        chunk_length, heading_hierarchy_depth, confidence_score]
                        
        Returns:
            numpy array (n_samples,) mit Ranking-Scores [0, 1]
        """
        # Extrahiere Features
        vector_scores = X[:, 0]
        text_scores = X[:, 1]
        # user_level = X[:, 2]  # Nicht verwendet in Basic Hybrid Scoring
        # keyword_matches = X[:, 3]  # Könnte für Boost verwendet werden
        # chunk_length = X[:, 4]  # Könnte für Penalty verwendet werden
        # heading_depth = X[:, 5]  # Nicht verwendet
        # confidence = X[:, 6]  # Nicht verwendet
        
        # Basic Hybrid Scoring: (vector * 0.7) + (text * 0.3)
        hybrid_scores = (vector_scores * self.vector_weight) + (text_scores * self.text_weight)
        
        # Optional: Document Type Boost (später)
        # Optional: Chunk Length Penalty (später)
        
        # Stelle sicher, dass Scores in [0, 1] sind
        hybrid_scores = np.clip(hybrid_scores, 0.0, 1.0)
        
        return hybrid_scores


class SHAPExplainerService:
    """
    SHAP Explainer Service - ECHTE SHAP-Berechnung.
    
    Verwendet SHAP-Library (KernelExplainer) für echte SHAP-Attribution.
    Ersetzt die heuristische SHAP-Approximation durch mathematisch korrekte Werte.
    """
    
    def __init__(
        self,
        model: RankingModelWrapper,
        feature_extractor: FeatureExtractor,
        background_data: Optional[np.ndarray] = None,
        n_background_samples: int = 50,
        enable_cache: bool = True,
        db_session=None  # NEU v2.7.0: Optional DB Session für SQLite Cache
    ):
        """
        Initialisiere SHAP Explainer Service.
        
        Args:
            model: RankingModelWrapper (sklearn-kompatibel)
            feature_extractor: FeatureExtractor für konsistente Features
            background_data: Background-Daten für KernelExplainer (n_samples, 7)
                           Falls None, wird zufällig generiert
            n_background_samples: Anzahl Background-Samples (falls background_data None)
            enable_cache: Aktiviere Caching für SHAP-Berechnungen (Performance-Optimierung)
        """
        if not SHAP_AVAILABLE:
            raise ImportError("SHAP library not available. Install with: pip install shap")
        
        self.model = model
        self.feature_extractor = feature_extractor
        self.enable_cache = enable_cache
        self._db_session = db_session  # Speichere für Cache-Initialisierung
        
        # Cache für Performance-Optimierung
        if self.enable_cache:
            # NEU v2.7.0: SQLite-basiert oder In-Memory
            import os
            persist_to_db = os.getenv('PERSIST_TO_DB', 'true').lower() == 'true'
            
            # db_session wird als optionaler Parameter übergeben (für SQLite)
            # Falls nicht vorhanden, verwende In-Memory Cache
            if persist_to_db and hasattr(self, '_db_session') and self._db_session:
                from .shap_cache_repository_sqlite import SHAPCacheRepositorySQLite
                self.cache = SHAPCacheRepositorySQLite(
                    db_session=self._db_session,
                    max_size=100,
                    ttl_seconds=3600
                )
            else:
                from .shap_cache_service import get_shap_cache
                self.cache = get_shap_cache()
        else:
            self.cache = None
        
        # Background-Daten für KernelExplainer
        if background_data is not None:
            self.background_data = background_data
        else:
            # Generiere zufällige Background-Daten (falls nicht bereitgestellt)
            # In Production sollten echte historische Daten verwendet werden
            self.background_data = self._generate_background_data(n_background_samples)
        
        # Erstelle KernelExplainer
        self.explainer = shap.KernelExplainer(
            model=self.model.predict,
            data=self.background_data
        )
    
    def _generate_background_data(self, n_samples: int) -> np.ndarray:
        """
        Generiere zufällige Background-Daten.
        
        In Production sollten echte historische Search-Daten verwendet werden.
        
        Args:
            n_samples: Anzahl Samples
            
        Returns:
            numpy array (n_samples, 7) mit normalisierten Random Features
        """
        # Zufällige Features [0, 1]
        return np.random.rand(n_samples, 7)
    
    def explain(
        self,
        query: str,
        chunk: Dict[str, Any],
        vector_score: float,
        text_score: float,
        hybrid_score: float,
        document_type: str,
        user_level: int,
        keyword_matches: int
    ) -> SHAPExplanation:
        """
        Erstelle ECHTE SHAP-Erklärung für Such-Ergebnis.
        
        Args:
            query: Query-String
            chunk: Chunk-Dict
            vector_score: Vektor-Score (0-1)
            text_score: Text-Score (0-1)
            hybrid_score: Hybrid-Score (0-1)
            document_type: Dokumenttyp
            user_level: User-Level (1-5)
            keyword_matches: Anzahl Keyword-Matches
            
        Returns:
            SHAPExplanation mit echten SHAP-Werten
        """
        # 1. Extrahiere Features
        features = self.feature_extractor.extract(
            query=query,
            chunk=chunk,
            vector_score=vector_score,
            text_score=text_score,
            user_level=user_level,
            keyword_matches=keyword_matches
        )
        
        # 1.5 Performance-Optimierung: Cache-Check
        if self.enable_cache and self.cache:
            # Erstelle Features-Dict für Cache-Key
            features_dict = {
                'vector_score': float(features[0]),
                'text_score': float(features[1]),
                'user_level': float(features[2]),
                'keyword_matches': float(features[3]),
                'chunk_length': float(features[4]),
                'heading_hierarchy_depth': float(features[5]),
                'confidence_score': float(features[6])
            }
            
            # Prüfe Cache
            cached_explanation = self.cache.get(query, features_dict)
            if cached_explanation is not None:
                # Cache Hit! 🎯
                return cached_explanation
        
        # 2. Berechne ECHTE SHAP-Werte mit KernelExplainer (nur bei Cache Miss)
        shap_values_obj = self.explainer.shap_values(features.reshape(1, -1))
        
        # shap_values_obj ist (1, 7) Array → flatten to (7,)
        if isinstance(shap_values_obj, np.ndarray):
            if shap_values_obj.ndim == 2:
                shap_values_array = shap_values_obj[0]
            else:
                shap_values_array = shap_values_obj
        else:
            shap_values_array = np.array(shap_values_obj)
        
        # 3. Erstelle Feature Importance Dict
        feature_importance = {}
        for i, feature_name in enumerate(self.feature_extractor.feature_names):
            feature_importance[feature_name] = float(shap_values_array[i])
        
        # 4. Base Value (Expected Value für KernelExplainer)
        base_value = float(self.explainer.expected_value)
        
        # 5. Normalisierte Feature-Werte
        normalized_features = {
            'vector_score': float(features[0]),
            'text_score': float(features[1]),
            'user_level': float(features[2]),
            'keyword_matches': float(features[3]),
            'chunk_length': float(features[4]),
            'heading_hierarchy_depth': float(features[5]),
            'confidence_score': float(features[6])
        }
        
        # 6. Erstelle SHAPExplanation
        explanation = SHAPExplanation(
            feature_importance=feature_importance,
            base_value=base_value,
            shap_values=shap_values_array.tolist(),
            expected_value=base_value,  # Für KernelExplainer: expected_value = base_value
            prediction=hybrid_score,
            query=query,
            chunk_id=str(chunk.get('chunk_id', 'unknown')),
            timestamp=datetime.now(),
            features=normalized_features
        )
        
        # 7. Performance-Optimierung: Speichere im Cache
        if self.enable_cache and self.cache:
            self.cache.put(query, features_dict, explanation)
        
        return explanation
    
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
        Alias-Methode für Kompatibilität mit AskQuestionUseCase.
        
        Diese Methode hat die gleiche Signatur wie die heuristische SHAP-Service-Methode
        und ruft intern explain() auf.
        
        Args:
            query: Query-String
            chunk: Chunk-Dict (muss 'chunk_id' enthalten)
            vector_score: Vektor-Score (0-1)
            text_score: Text-Score (0-1)
            hybrid_score: Hybrid-Score (0-1)
            document_type: Dokumenttyp
            user_level: User-Level (1-5)
            keyword_matches: Anzahl Keyword-Matches
            chunk_length: Chunk-Länge in Zeichen
            heading_hierarchy_depth: Heading-Hierarchie-Tiefe
            confidence_score: Confidence-Score (0-1)
            
        Returns:
            SHAPExplanation mit echten SHAP-Werten
        """
        # Erweitere Chunk mit zusätzlichen Metadaten
        chunk_with_metadata = chunk.copy() if isinstance(chunk, dict) else {'chunk_id': chunk}
        
        # Stelle sicher, dass metadata existiert
        if 'metadata' not in chunk_with_metadata:
            chunk_with_metadata['metadata'] = {}
        
        # Füge zusätzliche Metadaten hinzu
        chunk_with_metadata['metadata'].update({
            'chunk_length': chunk_length,
            'heading_hierarchy_depth': heading_hierarchy_depth,
            'confidence_score': confidence_score
        })
        
        # Rufe explain() auf
        return self.explain(
            query=query,
            chunk=chunk_with_metadata,
            vector_score=vector_score,
            text_score=text_score,
            hybrid_score=hybrid_score,
            document_type=document_type,
            user_level=user_level,
            keyword_matches=keyword_matches
        )

