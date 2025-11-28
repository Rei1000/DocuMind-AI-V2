"""
Search Quality Metrics Service für RAG System.

Infrastructure Layer: Berechnet Metriken für Suchergebnis-Qualität.

Features:
- Precision@k, Recall@k, NDCG@k, MRR
- Basierend auf User-Feedback und Ground Truth
- Vergleich von Hybrid vs ML Ranking
- Trend-Analyse über Zeit
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import os

# sklearn für Metriken
try:
    from sklearn.metrics import ndcg_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("WARNING: sklearn not available. NDCG calculation will be simplified.")

# NEU v2.10.2: Konfigurierbarer Feedback-Abdeckung Threshold
FEEDBACK_COVERAGE_THRESHOLD = float(
    os.getenv('RAG_FEEDBACK_COVERAGE_THRESHOLD', '0.3')
)


@dataclass
class SearchQualityMetrics:
    """
    Search Quality Metrics für eine Query.
    
    Repräsentiert verschiedene Metriken zur Bewertung der Suchergebnis-Qualität.
    """
    query: str
    timestamp: datetime
    
    # Precision & Recall
    precision_at_1: float
    precision_at_3: float
    precision_at_5: float
    precision_at_10: float
    
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    recall_at_10: float
    
    # Ranking Metriken
    ndcg_at_1: float
    ndcg_at_3: float
    ndcg_at_5: float
    ndcg_at_10: float
    
    mrr: float  # Mean Reciprocal Rank
    
    # Zusätzliche Metriken
    average_relevance_score: float
    num_relevant_results: int
    num_total_results: int
    
    # Ranking-Vergleich (Hybrid vs ML)
    hybrid_ndcg_at_10: Optional[float] = None
    ml_ndcg_at_10: Optional[float] = None
    
    # Metadaten
    session_id: Optional[int] = None
    user_id: Optional[int] = None
    document_type: Optional[str] = None
    
    # NEU v2.10.1: Filter-Informationen (für bessere Metriken-Interpretation)
    filters_applied: Optional[Dict[str, Any]] = None
    score_threshold: Optional[float] = None
    top_k_limit: Optional[int] = None
    feedback_coverage: Optional[float] = None  # Anteil der Chunks mit Feedback (0-1)
    
    # NEU v2.10.3: AI-Modell-Einstellungen (für Antwort-Qualitäts-Analyse)
    temperature: Optional[float] = None  # AI Temperature (0.0-2.0)
    max_tokens: Optional[int] = None  # Max Tokens für Antwort
    top_p: Optional[float] = None  # Top P (Nucleus Sampling, 0.0-1.0)


class SearchQualityMetricsService:
    """
    Search Quality Metrics Service.
    
    Berechnet Metriken für Suchergebnis-Qualität basierend auf:
    - User-Feedback (positive/negative/neutral)
    - Ground Truth (falls vorhanden)
    - Ranking-Positionen
    """
    
    def __init__(self):
        """Initialisiere Search Quality Metrics Service."""
        pass
    
    def _percentile_normalize_score(
        self,
        score: float,
        all_scores: List[float],
        min_percentile: float = 0.0,
        max_percentile: float = 1.0
    ) -> float:
        """
        NEU v2.10.2: Normalisiere Score basierend auf Percentile (robuster als Min/Max).
        
        Args:
            score: Der zu normalisierende Score
            all_scores: Liste aller Scores für Percentile-Berechnung
            min_percentile: Minimaler Percentile-Wert (default: 0.0)
            max_percentile: Maximaler Percentile-Wert (default: 1.0)
            
        Returns:
            Normalisierter Score (0-1)
        """
        if not all_scores or score is None:
            return 0.5
        
        # Filtere None und negative Werte
        valid_scores = [max(0.0, float(s)) for s in all_scores if s is not None]
        if not valid_scores:
            return 0.5
        
        # Berechne Percentile des Scores
        score_float = max(0.0, float(score))
        sorted_scores = sorted(valid_scores)
        
        # Zähle wie viele Scores kleiner oder gleich sind
        count_below = sum(1 for s in sorted_scores if s <= score_float)
        percentile = count_below / len(sorted_scores) if sorted_scores else 0.5
        
        # Normalisiere auf min_percentile bis max_percentile Bereich
        normalized = min_percentile + (percentile * (max_percentile - min_percentile))
        
        # Clamp auf 0-1
        return max(0.0, min(1.0, normalized))
        return max(0.0, min(1.0, normalized))
    
    def calculate_metrics(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        relevance_scores: Optional[List[float]] = None,
        feedback_ratings: Optional[List[str]] = None,
        hybrid_scores: Optional[List[float]] = None,
        ml_scores: Optional[List[float]] = None,
        timestamp: Optional[datetime] = None,
        filters_applied: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None,
        top_k_limit: Optional[int] = None,
        temperature: Optional[float] = None,  # NEU v2.10.3: AI Temperature
        max_tokens: Optional[int] = None,  # NEU v2.10.3: Max Tokens
        top_p: Optional[float] = None,  # NEU v2.10.3: Top P
        text_scores: Optional[List[float]] = None,  # NEU v2.10.5: Text-Scores für semantische Relevanz
        vector_scores: Optional[List[float]] = None,  # NEU v2.10.5: Vector-Scores für semantische Relevanz
        chunk_repository=None  # NEU v2.10.5: Optional Repository für Chunk-Text aus DB
    ) -> SearchQualityMetrics:
        """
        Berechne Search Quality Metrics für eine Query.
        
        Args:
            query: Die ursprüngliche Query
            search_results: Liste von Suchergebnissen (Chunks) mit Scores
            relevance_scores: Optional - Ground Truth Relevance Scores (0-1)
            feedback_ratings: Optional - User-Feedback Ratings ("positive", "negative", "neutral")
            hybrid_scores: Optional - Hybrid-Scores für Vergleich
            ml_scores: Optional - ML-Scores für Vergleich
            timestamp: Optional - Zeitstempel (default: jetzt)
            
        Returns:
            SearchQualityMetrics Objekt
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # NEU v2.10.2: Edge Case Handling - Keine Ergebnisse
        if not search_results or len(search_results) == 0:
            return SearchQualityMetrics(
                query=query,
                timestamp=timestamp,
                precision_at_1=0.0,
                precision_at_3=0.0,
                precision_at_5=0.0,
                precision_at_10=0.0,
                recall_at_1=0.0,
                recall_at_3=0.0,
                recall_at_5=0.0,
                recall_at_10=0.0,
                ndcg_at_1=0.0,
                ndcg_at_3=0.0,
                ndcg_at_5=0.0,
                ndcg_at_10=0.0,
                mrr=0.0,
                average_relevance_score=0.0,
                num_relevant_results=0,
                num_total_results=0,
                has_feedback=False,
                num_feedback_items=0,
                feedback_coverage=0.0,
                    filters_applied=filters_applied,
                    score_threshold=score_threshold,
                    top_k_limit=top_k_limit,
                    temperature=temperature,  # NEU v2.10.3: AI Temperature
                    max_tokens=max_tokens,  # NEU v2.10.3: Max Tokens
                    top_p=top_p  # NEU v2.10.3: Top P
                )
        
        # NEU v2.10.1: Berechne Feedback-Abdeckung
        num_feedback = sum(1 for f in (feedback_ratings or []) if f is not None)
        feedback_coverage = num_feedback / len(search_results) if search_results else 0.0
        
        # Berechne Relevance Scores aus Feedback, Scores oder Ground Truth
        if relevance_scores is None:
            # NEU v2.10.0: Wenn kein Feedback vorhanden, verwende Scores als Proxy
            has_feedback = feedback_ratings and any(f for f in feedback_ratings if f is not None)
            
            if has_feedback:
                # NEU v2.10.2: Wenn zu wenig Feedback (< Threshold), kombiniere mit Scores
                if feedback_coverage < FEEDBACK_COVERAGE_THRESHOLD:
                    # Zu wenig Feedback: Kombiniere Feedback + Scores für bessere Metriken
                    relevance_scores = self._calculate_relevance_from_feedback(
                        feedback_ratings or [],
                        len(search_results)
                    )
                    # Ergänze fehlende Feedback mit Scores
                    if hybrid_scores and len(hybrid_scores) == len(relevance_scores):
                        # NEU v2.10.2: Percentile-basierte Normalisierung (robuster als Min/Max)
                        valid_scores = [max(0.0, float(s)) for s in hybrid_scores if s is not None]
                        
                        if valid_scores:
                            for i, score in enumerate(hybrid_scores):
                                if relevance_scores[i] == 0.5:  # Neutral (kein Feedback)
                                    if score is None or score < 0:
                                        # Negativer oder fehlender Score: Verwende Position als Proxy
                                        position_score = max(0.0, 1.0 - (i / len(hybrid_scores)) * 0.3)
                                        relevance_scores[i] = position_score
                                    else:
                                        # Percentile-basierte Normalisierung (robust gegen Ausreißer)
                                        normalized_score = self._percentile_normalize_score(
                                            score, valid_scores, min_percentile=0.0, max_percentile=1.0
                                        )
                                        relevance_scores[i] = normalized_score
                        else:
                            # Keine gültigen Scores: Verwende Position als Proxy
                            for i in range(len(relevance_scores)):
                                if relevance_scores[i] == 0.5:
                                    position_score = max(0.0, 1.0 - (i / len(relevance_scores)) * 0.3)
                                    relevance_scores[i] = position_score
                else:
                    # Genug Feedback: Verwende nur Feedback
                    relevance_scores = self._calculate_relevance_from_feedback(
                        feedback_ratings or [],
                        len(search_results)
                    )
            else:
                # NEU: Verwende Hybrid-Scores als Proxy für Relevance
                # NEU v2.10.5: Kombiniere Hybrid-Score mit Text-Score für bessere semantische Relevanz
                # Annahme: Höhere Scores = höhere Relevanz, aber Text-Score zeigt Keyword-Matching
                if hybrid_scores and len(hybrid_scores) == len(search_results):
                    # NEU v2.10.5: Kombiniere Hybrid-Score mit Text-Score für semantische Relevanz
                    # Text-Score zeigt Keyword-Matching (wichtig für Query-Relevanz)
                    relevance_scores = []
                    
                    # Extrahiere Text-Scores aus search_results falls nicht übergeben
                    extracted_text_scores = []
                    if text_scores and len(text_scores) == len(search_results):
                        extracted_text_scores = text_scores
                    else:
                        # Versuche Text-Scores aus search_results zu extrahieren
                        for result in search_results:
                            text_score = result.get('_extended_metadata', {}).get('text_score') or result.get('text_score')
                            extracted_text_scores.append(text_score if text_score is not None else 0.0)
                    
                    # NEU v2.10.5: Kombiniere Hybrid-Score mit Text-Score UND Query-Term-Matching
                    # Prüfe ob Query-Terms tatsächlich im Chunk vorkommen (wichtig für Relevanz)
                    combined_scores = []
                    query_terms = set(query.lower().split()) if query else set()
                    
                    for i, hybrid_score in enumerate(hybrid_scores):
                        if hybrid_score is None or hybrid_score < 0:
                            combined_scores.append(0.0)
                        else:
                            text_score = extracted_text_scores[i] if i < len(extracted_text_scores) else 0.0
                            
                            # NEU v2.10.5: Prüfe Query-Term-Matching im Chunk-Text
                            # WICHTIG: Nur reale Werte verwenden - KEINE Fallbacks!
                            # Lade BEIDE wenn möglich für Vergleich
                            extended_metadata = search_results[i].get('_extended_metadata', {})
                            chunk_text_db_loaded = ''
                            chunk_text_source = 'none'
                            
                            # WICHTIG: Prüfe chunk_text direkt in extended_metadata (kann auch leerer String sein, aber Key existiert)
                            chunk_text_metadata = None
                            if extended_metadata and isinstance(extended_metadata, dict):
                                # Prüfe direkt ob 'chunk_text' Key existiert (auch wenn leer)
                                if 'chunk_text' in extended_metadata:
                                    chunk_text_metadata = extended_metadata.get('chunk_text')
                                    # Nur verwenden wenn nicht None und nicht leerer String
                                    if chunk_text_metadata and isinstance(chunk_text_metadata, str) and chunk_text_metadata.strip():
                                        pass  # chunk_text_metadata ist gültig
                                    else:
                                        chunk_text_metadata = None
                            
                            # Fallback: Prüfe auch direkt in search_results
                            if not chunk_text_metadata:
                                chunk_text_metadata = search_results[i].get('chunk_text')
                                if chunk_text_metadata and isinstance(chunk_text_metadata, str) and chunk_text_metadata.strip():
                                    pass  # chunk_text_metadata ist gültig
                                else:
                                    chunk_text_metadata = None
                            
                            # NEU v2.10.5: Versuche IMMER auch aus DB zu laden (für Vergleich)
                            chunk_id = search_results[i].get('chunk_id', '')
                            if chunk_repository and chunk_id:
                                try:
                                    chunk_entity = chunk_repository.get_by_chunk_id(chunk_id)
                                    if chunk_entity and chunk_entity.chunk_text:
                                        chunk_text_db_loaded = chunk_entity.chunk_text
                                except Exception as e:
                                    print(f"DEBUG: Fehler beim Holen von Chunk-Text aus DB für {chunk_id}: {e}")
                            
                            # Option 1: Aus Metadaten (wenn verfügbar) - Priorität
                            if chunk_text_metadata:
                                chunk_text = chunk_text_metadata
                                chunk_text_source = 'metadata'
                            # Option 2: Aus Datenbank (nur wenn Metadaten NICHT verfügbar)
                            elif chunk_text_db_loaded:
                                chunk_text = chunk_text_db_loaded
                                chunk_text_source = 'database'
                            # KEIN Fallback! Wenn keine realen Werte verfügbar, bleibt chunk_text leer
                            else:
                                chunk_text = ''
                                chunk_text_source = 'none'
                                # DEBUG: Log wenn chunk_text nicht gefunden wurde
                                if extended_metadata:
                                    print(f"DEBUG: chunk_text nicht gefunden für {chunk_id}. Keys in _extended_metadata: {list(extended_metadata.keys())}")
                                    if 'chunk_text' in extended_metadata:
                                        print(f"DEBUG: chunk_text Key existiert, aber Wert ist: '{extended_metadata['chunk_text']}' (Type: {type(extended_metadata['chunk_text'])})")
                            
                            chunk_text_lower = chunk_text.lower() if chunk_text else ''
                            
                            # Zähle wie viele Query-Terms im Chunk vorkommen
                            query_term_matches = 0
                            if query_terms and chunk_text_lower:
                                for term in query_terms:
                                    if term in chunk_text_lower:
                                        query_term_matches += 1
                            
                            # Query-Term-Match-Bonus: Wenn alle wichtigen Terms matchen, erhöhe Score
                            query_match_ratio = query_term_matches / len(query_terms) if query_terms else 0.0
                            
                            # DEBUG: Speichere Debug-Info in search_results für Analyse
                            if '_extended_metadata' not in search_results[i]:
                                search_results[i]['_extended_metadata'] = {}
                            search_results[i]['_extended_metadata']['chunk_text_source'] = chunk_text_source
                            search_results[i]['_extended_metadata']['chunk_text_length'] = len(chunk_text) if chunk_text else 0
                            search_results[i]['_extended_metadata']['query_term_matches'] = query_term_matches
                            search_results[i]['_extended_metadata']['query_match_ratio'] = query_match_ratio
                            
                            # NEU v2.10.5: Speichere BEIDE Texte für Vergleich (wenn verfügbar)
                            # WICHTIG: Nur reale Werte speichern - KEINE Fallbacks!
                            # Metadaten-Text (nur wenn wirklich vorhanden)
                            if chunk_text_metadata:
                                search_results[i]['_extended_metadata']['chunk_text_metadata'] = chunk_text_metadata
                                # Auch als chunk_text für Kompatibilität
                                search_results[i]['_extended_metadata']['chunk_text'] = chunk_text_metadata
                            
                            # DB-Text (immer speichern wenn geladen, auch wenn nicht verwendet)
                            if chunk_text_db_loaded:
                                search_results[i]['_extended_metadata']['chunk_text_db'] = chunk_text_db_loaded
                            
                            # Wenn beide verfügbar und unterschiedlich, markiere das
                            if chunk_text_metadata and chunk_text_db_loaded:
                                if chunk_text_metadata != chunk_text_db_loaded:
                                    search_results[i]['_extended_metadata']['chunk_text_differs'] = True
                                else:
                                    search_results[i]['_extended_metadata']['chunk_text_differs'] = False
                            
                            # Warnung wenn keine realen Werte verfügbar
                            if chunk_text_source == 'none':
                                search_results[i]['_extended_metadata']['chunk_text_warning'] = 'Keine Chunk-Text-Daten verfügbar (weder Metadaten noch DB)'
                            
                            # NEU v2.10.5: Kombiniere mit stärkerer Gewichtung für Text-Score wenn Query-Terms matchen
                            # Wenn Query-Terms matchen, ist Text-Score wichtiger
                            if query_match_ratio > 0.5:  # Mehr als 50% der Query-Terms matchen
                                # Stärkere Gewichtung für Text-Score (50% Hybrid, 50% Text)
                                combined_score = (hybrid_score * 0.5) + (text_score * 0.5)
                                # Bonus für vollständiges Query-Term-Matching
                                combined_score = min(1.0, combined_score + (query_match_ratio * 0.1))
                            else:
                                # Standard-Gewichtung (60% Hybrid, 40% Text)
                                combined_score = (hybrid_score * 0.6) + (text_score * 0.4)
                                # Penalty wenn keine Query-Terms matchen
                                combined_score = max(0.0, combined_score - (0.2 * (1.0 - query_match_ratio)))
                            
                            combined_scores.append(combined_score)
                    
                    # NEU v2.10.5: Verwende Hybrid-Normalisierung (Percentile + absoluter Schwellenwert)
                    valid_scores = [max(0.0, float(s)) for s in combined_scores if s is not None]
                    
                    if valid_scores:
                        # Berechne absoluten Schwellenwert (Median der Scores)
                        median_score = sorted(valid_scores)[len(valid_scores) // 2] if valid_scores else 0.5
                        threshold = max(0.4, median_score * 0.8)  # Mindestens 0.4, oder 80% des Medians
                        
                        for i, combined_score in enumerate(combined_scores):
                            if combined_score is None or combined_score < 0:
                                # Negativer oder fehlender Score: Verwende Position als Proxy
                                position_score = max(0.0, 1.0 - (i / len(combined_scores)) * 0.3)
                                relevance_scores.append(position_score)
                            else:
                                # Percentile-basierte Normalisierung (robust gegen Ausreißer)
                                normalized_score = self._percentile_normalize_score(
                                    combined_score, valid_scores, min_percentile=0.0, max_percentile=1.0
                                )
                                
                                # NEU v2.10.5: Berücksichtige absoluten Schwellenwert
                                # Wenn Score unter Schwellenwert, reduziere normalisierten Score
                                if combined_score < threshold:
                                    # Reduziere normalisierten Score wenn unter Schwellenwert
                                    normalized_score = normalized_score * (combined_score / threshold) if threshold > 0 else normalized_score * 0.5
                                
                                relevance_scores.append(normalized_score)
                    else:
                        # Keine gültigen Scores: Verwende Position als Proxy
                        relevance_scores = [
                            max(0.0, 1.0 - (i / len(search_results)) * 0.3)
                            for i in range(len(search_results))
                        ]
                else:
                    # Fallback: Verwende Scores aus search_results
                    relevance_scores = []
                    for result in search_results:
                        score = result.get('relevance_score', 0.5)
                        # NEU v2.10.2: Clamp auf 0-1 Bereich
                        relevance_scores.append(max(0.0, min(1.0, float(score) if score is not None else 0.5)))
        
        # Precision & Recall
        precision_at_1 = self._precision_at_k(relevance_scores, 1)
        precision_at_3 = self._precision_at_k(relevance_scores, 3)
        precision_at_5 = self._precision_at_k(relevance_scores, 5)
        precision_at_10 = self._precision_at_k(relevance_scores, 10)
        
        recall_at_1 = self._recall_at_k(relevance_scores, 1)
        recall_at_3 = self._recall_at_k(relevance_scores, 3)
        recall_at_5 = self._recall_at_k(relevance_scores, 5)
        recall_at_10 = self._recall_at_k(relevance_scores, 10)
        
        # NDCG
        ndcg_at_1 = self._ndcg_at_k(relevance_scores, 1)
        ndcg_at_3 = self._ndcg_at_k(relevance_scores, 3)
        ndcg_at_5 = self._ndcg_at_k(relevance_scores, 5)
        ndcg_at_10 = self._ndcg_at_k(relevance_scores, 10)
        
        # MRR
        mrr = self._mean_reciprocal_rank(relevance_scores)
        
        # Zusätzliche Metriken
        average_relevance = np.mean(relevance_scores) if relevance_scores else 0.0
        num_relevant = sum(1 for r in relevance_scores if r > 0.5) if relevance_scores else 0
        num_total = len(search_results)
        
        # NEU v2.10.4: Speichere normalisierte Relevance Scores in search_results für Frontend
        # WICHTIG: Frontend verwendet diese Scores für is_relevant-Bewertung
        if relevance_scores and len(relevance_scores) == len(search_results):
            for i, result in enumerate(search_results):
                if '_extended_metadata' not in result:
                    result['_extended_metadata'] = {}
                result['_extended_metadata']['normalized_relevance_score'] = relevance_scores[i]
        
        # Ranking-Vergleich (Hybrid vs ML)
        hybrid_ndcg_at_10 = None
        ml_ndcg_at_10 = None
        
        if hybrid_scores and len(hybrid_scores) == len(relevance_scores):
            # Sortiere nach Hybrid-Score
            hybrid_ranked = sorted(
                zip(relevance_scores, hybrid_scores),
                key=lambda x: x[1],
                reverse=True
            )
            hybrid_relevance = [r[0] for r in hybrid_ranked]
            hybrid_ndcg_at_10 = self._ndcg_at_k(hybrid_relevance, 10)
        
        if ml_scores and len(ml_scores) == len(relevance_scores):
            # Sortiere nach ML-Score
            ml_ranked = sorted(
                zip(relevance_scores, ml_scores),
                key=lambda x: x[1],
                reverse=True
            )
            ml_relevance = [r[0] for r in ml_ranked]
            ml_ndcg_at_10 = self._ndcg_at_k(ml_relevance, 10)
        
        return SearchQualityMetrics(
            query=query,
            timestamp=timestamp,
            precision_at_1=precision_at_1,
            precision_at_3=precision_at_3,
            precision_at_5=precision_at_5,
            precision_at_10=precision_at_10,
            recall_at_1=recall_at_1,
            recall_at_3=recall_at_3,
            recall_at_5=recall_at_5,
            recall_at_10=recall_at_10,
            ndcg_at_1=ndcg_at_1,
            ndcg_at_3=ndcg_at_3,
            ndcg_at_5=ndcg_at_5,
            ndcg_at_10=ndcg_at_10,
            mrr=mrr,
            average_relevance_score=average_relevance,
            num_relevant_results=num_relevant,
            num_total_results=num_total,
            hybrid_ndcg_at_10=hybrid_ndcg_at_10,
            ml_ndcg_at_10=ml_ndcg_at_10,
            user_id=None,  # Wird später gesetzt
            document_type=None,  # Wird später gesetzt
            filters_applied=filters_applied,
            score_threshold=score_threshold,
            top_k_limit=top_k_limit,
            feedback_coverage=feedback_coverage,
            temperature=temperature,  # NEU v2.10.3: AI Temperature
            max_tokens=max_tokens,  # NEU v2.10.3: Max Tokens
            top_p=top_p  # NEU v2.10.3: Top P
        )
    
    def _calculate_relevance_from_feedback(
        self,
        feedback_ratings: List[str],
        num_results: int
    ) -> List[float]:
        """
        Berechne Relevance Scores aus User-Feedback.
        
        Args:
            feedback_ratings: Liste von Feedback-Ratings ("positive", "negative", "neutral")
            num_results: Anzahl der Suchergebnisse
            
        Returns:
            Liste von Relevance Scores (0-1)
        """
        # Mapping: positive → 1.0, neutral → 0.5, negative → 0.0
        relevance_mapping = {
            'positive': 1.0,
            'neutral': 0.5,
            'negative': 0.0
        }
        
        relevance_scores = []
        for i in range(num_results):
            if i < len(feedback_ratings):
                rating = feedback_ratings[i].lower()
                relevance_scores.append(relevance_mapping.get(rating, 0.5))
            else:
                # Kein Feedback → 0.5 (neutral)
                relevance_scores.append(0.5)
        
        return relevance_scores
    
    def _precision_at_k(self, relevance_scores: List[float], k: int) -> float:
        """
        Berechne Precision@k.
        
        Args:
            relevance_scores: Liste von Relevance Scores (sortiert nach Ranking)
            k: Anzahl der Top-Ergebnisse
            
        Returns:
            Precision@k (0-1)
        """
        if not relevance_scores or k == 0:
            return 0.0
        
        top_k = relevance_scores[:k]
        relevant_count = sum(1 for r in top_k if r > 0.5)
        
        return relevant_count / min(k, len(relevance_scores))
    
    def _recall_at_k(
        self,
        relevance_scores: List[float],
        k: int,
        total_relevant: Optional[int] = None
    ) -> float:
        """
        Berechne Recall@k.
        
        Args:
            relevance_scores: Liste von Relevance Scores (sortiert nach Ranking)
            k: Anzahl der Top-Ergebnisse
            total_relevant: Optional - Gesamtanzahl relevanter Dokumente (default: alle > 0.5)
            
        Returns:
            Recall@k (0-1)
        """
        if not relevance_scores or k == 0:
            return 0.0
        
        if total_relevant is None:
            total_relevant = sum(1 for r in relevance_scores if r > 0.5)
        
        if total_relevant == 0:
            return 0.0
        
        top_k = relevance_scores[:k]
        relevant_in_top_k = sum(1 for r in top_k if r > 0.5)
        
        return relevant_in_top_k / total_relevant
    
    def _ndcg_at_k(self, relevance_scores: List[float], k: int) -> float:
        """
        Berechne NDCG@k (Normalized Discounted Cumulative Gain).
        
        Args:
            relevance_scores: Liste von Relevance Scores (sortiert nach Ranking)
            k: Anzahl der Top-Ergebnisse
            
        Returns:
            NDCG@k (0-1)
        """
        if not relevance_scores or k == 0:
            return 0.0
        
        top_k = relevance_scores[:k]
        
        # DCG (Discounted Cumulative Gain)
        dcg = 0.0
        for i, rel in enumerate(top_k):
            dcg += rel / np.log2(i + 2)  # i+2 weil log2(1) = 0
        
        # IDCG (Ideal DCG) - sortiere nach Relevance
        ideal_scores = sorted(relevance_scores, reverse=True)[:k]
        idcg = 0.0
        for i, rel in enumerate(ideal_scores):
            idcg += rel / np.log2(i + 2)
        
        # NDCG
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    def _mean_reciprocal_rank(self, relevance_scores: List[float]) -> float:
        """
        Berechne MRR (Mean Reciprocal Rank).
        
        Args:
            relevance_scores: Liste von Relevance Scores (sortiert nach Ranking)
            
        Returns:
            MRR (0-1)
        """
        if not relevance_scores:
            return 0.0
        
        # Finde Position des ersten relevanten Ergebnisses (relevance > 0.5)
        for i, rel in enumerate(relevance_scores):
            if rel > 0.5:
                return 1.0 / (i + 1)
        
        # Kein relevantes Ergebnis gefunden
        return 0.0
    
    def aggregate_metrics(
        self,
        metrics_list: List[SearchQualityMetrics]
    ) -> Dict[str, Any]:
        """
        Aggregiere Metriken über mehrere Queries.
        
        Args:
            metrics_list: Liste von SearchQualityMetrics
            
        Returns:
            Dict mit aggregierten Metriken
        """
        if not metrics_list:
            return {
                'num_queries': 0,
                'average_precision_at_10': 0.0,
                'average_recall_at_10': 0.0,
                'average_ndcg_at_10': 0.0,
                'average_mrr': 0.0
            }
        
        return {
            'num_queries': len(metrics_list),
            'average_precision_at_1': np.mean([m.precision_at_1 for m in metrics_list]),
            'average_precision_at_3': np.mean([m.precision_at_3 for m in metrics_list]),
            'average_precision_at_5': np.mean([m.precision_at_5 for m in metrics_list]),
            'average_precision_at_10': np.mean([m.precision_at_10 for m in metrics_list]),
            'average_recall_at_1': np.mean([m.recall_at_1 for m in metrics_list]),
            'average_recall_at_3': np.mean([m.recall_at_3 for m in metrics_list]),
            'average_recall_at_5': np.mean([m.recall_at_5 for m in metrics_list]),
            'average_recall_at_10': np.mean([m.recall_at_10 for m in metrics_list]),
            'average_ndcg_at_1': np.mean([m.ndcg_at_1 for m in metrics_list]),
            'average_ndcg_at_3': np.mean([m.ndcg_at_3 for m in metrics_list]),
            'average_ndcg_at_5': np.mean([m.ndcg_at_5 for m in metrics_list]),
            'average_ndcg_at_10': np.mean([m.ndcg_at_10 for m in metrics_list]),
            'average_mrr': np.mean([m.mrr for m in metrics_list]),
            'average_relevance_score': np.mean([m.average_relevance_score for m in metrics_list]),
            'average_num_relevant': np.mean([m.num_relevant_results for m in metrics_list]),
            'average_num_total': np.mean([m.num_total_results for m in metrics_list]),
            'hybrid_vs_ml_comparison': self._compare_hybrid_vs_ml(metrics_list)
        }
    
    def _compare_hybrid_vs_ml(
        self,
        metrics_list: List[SearchQualityMetrics]
    ) -> Dict[str, Any]:
        """
        Vergleiche Hybrid vs ML Ranking.
        
        Args:
            metrics_list: Liste von SearchQualityMetrics
            
        Returns:
            Dict mit Vergleichs-Metriken
        """
        hybrid_ndcgs = [m.hybrid_ndcg_at_10 for m in metrics_list if m.hybrid_ndcg_at_10 is not None]
        ml_ndcgs = [m.ml_ndcg_at_10 for m in metrics_list if m.ml_ndcg_at_10 is not None]
        
        if not hybrid_ndcgs or not ml_ndcgs:
            return {
                'hybrid_avg_ndcg_at_10': None,
                'ml_avg_ndcg_at_10': None,
                'improvement': None
            }
        
        hybrid_avg = np.mean(hybrid_ndcgs)
        ml_avg = np.mean(ml_ndcgs)
        improvement = ((ml_avg - hybrid_avg) / hybrid_avg * 100) if hybrid_avg > 0 else 0.0
        
        return {
            'hybrid_avg_ndcg_at_10': float(hybrid_avg),
            'ml_avg_ndcg_at_10': float(ml_avg),
            'improvement_percent': float(improvement),
            'ml_better_count': sum(1 for h, m in zip(hybrid_ndcgs, ml_ndcgs) if m > h),
            'hybrid_better_count': sum(1 for h, m in zip(hybrid_ndcgs, ml_ndcgs) if h > m),
            'equal_count': sum(1 for h, m in zip(hybrid_ndcgs, ml_ndcgs) if abs(m - h) < 0.001)
        }

