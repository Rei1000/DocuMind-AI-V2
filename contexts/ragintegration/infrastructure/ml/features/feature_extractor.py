"""
ML Feature Extractor für Learning-to-Rank.

Infrastructure Layer: Extrahiert 11 Features für ML-Ranking-Modelle.

TDD Phase 2: GREEN - Minimale Implementierung für Tests.

Features (11):
1. vector_score - Vektor-Ähnlichkeits-Score (0-1)
2. text_score - Text-Matching-Score (0-1)
3. bm25_score - BM25-Score (0-1)
4. jaccard_score - Jaccard-Ähnlichkeit (0-1)
5. keyword_matches - Anzahl Keyword-Matches (normalisiert)
6. chunk_length - Chunk-Länge (normalisiert)
7. document_type_encoded - Document Type (Label-Encoded, normalisiert)
8. heading_hierarchy_depth - Heading-Hierarchie-Tiefe (normalisiert)
9. confidence_score - Confidence-Score (0-1)
10. user_level - User-Level (normalisiert)
11. hybrid_score - Hybrid-Score (0-1)
"""

from typing import Dict, Any, List
import numpy as np


class MLFeatureExtractor:
    """
    ML Feature Extractor für Learning-to-Rank.
    
    Extrahiert 11 Features aus Chunk-Daten für ML-Ranking-Modelle.
    Alle Features werden auf [0, 1] normalisiert.
    """
    
    def __init__(self):
        """Initialisiere ML Feature Extractor."""
        # Feature-Namen (Reihenfolge ist wichtig!)
        self._feature_names = [
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
        
        # Document Type Label Encoding
        # WICHTIG: Konsistent über alle Extraktions-Calls
        self._document_types = [
            'Arbeitsanweisung',
            'SOP',
            'Flussdiagramm',
            'Formular',
            'Checkliste',
            'Richtlinie',
            'Sonstiges'
        ]
        
        # Feature-Beschreibungen
        self._descriptions = {
            'vector_score': 'Vektor-Ähnlichkeits-Score (Embedding-basiert)',
            'text_score': 'Text-Matching-Score (Hybrid aus BM25/Jaccard)',
            'bm25_score': 'BM25 Keyword-Relevanz-Score',
            'jaccard_score': 'Jaccard-Ähnlichkeit (Token-Overlap)',
            'keyword_matches': 'Anzahl Keyword-Matches (normalisiert auf max 20)',
            'chunk_length': 'Chunk-Länge in Zeichen (normalisiert auf max 3000)',
            'document_type_encoded': 'Document Type (Label-Encoded, 0-1)',
            'heading_hierarchy_depth': 'Tiefe der Heading-Hierarchie (normalisiert auf max 5)',
            'confidence_score': 'Confidence-Score der AI-Extraktion (0-1)',
            'user_level': 'User-Level (1-5, normalisiert auf 0-1)',
            'hybrid_score': 'Kombinierter Vector/Text Score (0.7 * vector + 0.3 * text)'
        }
    
    @property
    def feature_names(self) -> List[str]:
        """Gibt Feature-Namen zurück (für Model-Training und SHAP)."""
        return self._feature_names
    
    def get_feature_descriptions(self) -> Dict[str, str]:
        """Gibt Feature-Beschreibungen zurück (für Interpretation)."""
        return self._descriptions
    
    def extract(
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
    ) -> np.ndarray:
        """
        Extrahiere Features aus Chunk-Daten.
        
        Args:
            query: Query-String
            chunk: Chunk-Dict mit metadata
            vector_score: Vektor-Score (0-1)
            text_score: Text-Score (0-1)
            bm25_score: BM25-Score (0-1)
            jaccard_score: Jaccard-Score (0-1)
            keyword_matches: Anzahl Keyword-Matches
            user_level: User-Level (1-5)
            hybrid_score: Hybrid-Score (0-1)
            
        Returns:
            numpy array (11,) mit normalisierten Features [0, 1]
        """
        metadata = chunk.get('metadata', {})
        
        # Feature 0: vector_score (bereits normalisiert)
        f_vector = float(vector_score)
        
        # Feature 1: text_score (bereits normalisiert)
        f_text = float(text_score)
        
        # Feature 2: bm25_score (bereits normalisiert)
        f_bm25 = float(bm25_score)
        
        # Feature 3: jaccard_score (bereits normalisiert)
        f_jaccard = float(jaccard_score)
        
        # Feature 4: keyword_matches (normalisiert auf 0-1, max 20 assumed)
        f_keyword = min(float(keyword_matches) / 20.0, 1.0)
        
        # Feature 5: chunk_length (normalisiert auf 0-1, max 3000 assumed)
        chunk_length = metadata.get('chunk_length', len(metadata.get('chunk_text', '')))
        f_chunk_length = min(float(chunk_length) / 3000.0, 1.0)
        
        # Feature 6: document_type_encoded (Label-Encoding, normalisiert auf 0-1)
        document_type = metadata.get('document_type', 'Sonstiges')
        if document_type in self._document_types:
            doc_type_idx = self._document_types.index(document_type)
        else:
            doc_type_idx = len(self._document_types) - 1  # 'Sonstiges' als Default
        f_doc_type = float(doc_type_idx) / max(len(self._document_types) - 1, 1)
        
        # Feature 7: heading_hierarchy_depth (normalisiert auf 0-1, max 5 assumed)
        heading_depth = metadata.get('heading_hierarchy_depth', 0)
        f_heading_depth = min(float(heading_depth) / 5.0, 1.0)
        
        # Feature 8: confidence_score (bereits normalisiert)
        f_confidence = float(metadata.get('confidence_score', 0.5))
        
        # Feature 9: user_level (normalisiert auf 0-1)
        f_user_level = float(user_level) / 5.0
        
        # Feature 10: hybrid_score (bereits normalisiert)
        f_hybrid = float(hybrid_score)
        
        # Als numpy array zurückgeben
        features = np.array([
            f_vector,
            f_text,
            f_bm25,
            f_jaccard,
            f_keyword,
            f_chunk_length,
            f_doc_type,
            f_heading_depth,
            f_confidence,
            f_user_level,
            f_hybrid
        ], dtype=np.float64)
        
        return features
    
    def extract_batch(self, chunks_data: List[Dict[str, Any]]) -> np.ndarray:
        """
        Extrahiere Features für Batch von Chunks.
        
        Args:
            chunks_data: Liste von Dicts mit keys: query, chunk, vector_score, etc.
                        
        Returns:
            numpy array (n_samples, 11) mit normalisierten Features
        """
        features_list = []
        
        for data in chunks_data:
            features = self.extract(
                query=data['query'],
                chunk=data['chunk'],
                vector_score=data['vector_score'],
                text_score=data['text_score'],
                bm25_score=data.get('bm25_score', 0.0),
                jaccard_score=data.get('jaccard_score', 0.0),
                keyword_matches=data['keyword_matches'],
                user_level=data['user_level'],
                hybrid_score=data['hybrid_score']
            )
            features_list.append(features)
        
        # Stack to 2D array
        return np.array(features_list, dtype=np.float64)

