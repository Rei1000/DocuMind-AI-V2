"""
Infrastructure Layer: Hybrid Search Service

Kombiniert Vektor-Suche mit Text-Suche für bessere Ergebnisse.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from contexts.ragintegration.domain.value_objects import EmbeddingVector, SourceReference
from contexts.ragintegration.infrastructure.vector_store_adapter import QdrantVectorStoreAdapter
from contexts.ragintegration.infrastructure.embedding_adapter import OpenAIEmbeddingAdapter


@dataclass
class SearchResult:
    """Ein Suchergebnis mit Score und Metadaten."""
    chunk_id: str
    score: float
    metadata: Dict[str, Any]
    source_reference: Optional[SourceReference] = None


class HybridSearchService:
    """Service für Hybrid Search (Vektor + Text)."""
    
    def __init__(
        self, 
        vector_store: QdrantVectorStoreAdapter,
        embedding_service: OpenAIEmbeddingAdapter
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
        use_hybrid: bool = True
    ) -> List[SearchResult]:
        """Führt Hybrid Search durch."""
        try:
            # 1. Generiere Query Embedding
            query_embedding = self.embedding_service.generate_embedding(query)
            
            if use_hybrid:
                # 2. Hybrid Search
                results = self.vector_store.search_with_hybrid_scoring(
                    query_embedding=query_embedding,
                    query_text=query,
                    top_k=top_k,
                    score_threshold=score_threshold,
                    filters=filters
                )
            else:
                # 3. Reine Vektor-Suche
                results = self.vector_store.search_similar_chunks(
                    query_embedding=query_embedding,
                    top_k=top_k,
                    score_threshold=score_threshold,
                    filters=filters
                )
            
            # 4. Konvertiere zu SearchResult Objekten
            search_results = []
            for result in results:
                search_result = SearchResult(
                    chunk_id=result['chunk_id'],
                    score=result.get('hybrid_score', result['score']),
                    metadata=result['metadata']
                )
                search_results.append(search_result)
            
            return search_results
            
        except Exception as e:
            raise RuntimeError(f"Fehler bei der Hybrid Search: {str(e)}")
    
    def search_with_reranking(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Führt Search mit Re-Ranking durch."""
        try:
            # 1. Erste Suche mit mehr Ergebnissen
            initial_results = self.search(
                query=query,
                top_k=top_k * 3,  # Mehr Ergebnisse für Re-Ranking
                score_threshold=score_threshold * 0.8,
                filters=filters,
                use_hybrid=True
            )
            
            # 2. Re-Ranking basierend auf Text-Relevanz
            reranked_results = self._rerank_results(query, initial_results)
            
            # 3. Begrenze auf gewünschte Anzahl
            return reranked_results[:top_k]
            
        except Exception as e:
            raise RuntimeError(f"Fehler beim Re-Ranking: {str(e)}")
    
    def search_by_document_type(
        self,
        query: str,
        document_type: str,
        top_k: int = 5,
        score_threshold: float = 0.7
    ) -> List[SearchResult]:
        """Sucht nur in bestimmten Dokumenttypen."""
        filters = {'document_type': document_type}
        return self.search(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
            filters=filters
        )
    
    def search_by_page_range(
        self,
        query: str,
        page_numbers: List[int],
        top_k: int = 5,
        score_threshold: float = 0.7
    ) -> List[SearchResult]:
        """Sucht nur in bestimmten Seiten."""
        filters = {'page_numbers': page_numbers}
        return self.search(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
            filters=filters
        )
    
    def search_with_filters(
        self,
        query: str,
        filters: Dict[str, Any],
        top_k: int = 5,
        score_threshold: float = 0.7
    ) -> List[SearchResult]:
        """Sucht mit benutzerdefinierten Filtern."""
        return self.search(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
            filters=filters
        )
    
    def _rerank_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """Re-Rankt Ergebnisse basierend auf Text-Relevanz."""
        try:
            # Berechne Text-Relevanz für jeden Result
            for result in results:
                chunk_text = result.metadata.get('chunk_text', '')
                text_relevance = self._calculate_text_relevance(query, chunk_text)
                
                # Kombiniere Vektor-Score mit Text-Relevanz
                vector_score = result.score
                combined_score = (vector_score * 0.6) + (text_relevance * 0.4)
                
                result.score = combined_score
            
            # Sortiere nach neuem Score
            results.sort(key=lambda x: x.score, reverse=True)
            
            return results
            
        except Exception as e:
            # Bei Fehler: Originale Ergebnisse zurückgeben
            return results
    
    def _calculate_text_relevance(self, query: str, text: str) -> float:
        """Berechnet Text-Relevanz zwischen Query und Text."""
        try:
            # Einfache Implementierung: Wort-Übereinstimmung
            query_words = set(query.lower().split())
            text_words = set(text.lower().split())
            
            if not query_words:
                return 0.0
            
            # Berechne Jaccard-Ähnlichkeit
            intersection = query_words.intersection(text_words)
            union = query_words.union(text_words)
            
            if not union:
                return 0.0
            
            jaccard_similarity = len(intersection) / len(union)
            
            # Berücksichtige auch Teilwort-Matches
            partial_matches = 0
            for query_word in query_words:
                for text_word in text_words:
                    if query_word in text_word or text_word in query_word:
                        partial_matches += 1
            
            partial_score = partial_matches / len(query_words) if query_words else 0
            
            # Kombiniere Jaccard und Partial Matches
            final_score = (jaccard_similarity * 0.7) + (partial_score * 0.3)
            
            return min(final_score, 1.0)  # Begrenze auf 1.0
            
        except Exception:
            return 0.0
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """Gibt Statistiken über die Suche zurück."""
        try:
            collection_info = self.vector_store.get_collection_info()
            
            return {
                'total_chunks': collection_info.get('points_count', 0),
                'vector_dimension': collection_info.get('vector_size', 0),
                'distance_metric': collection_info.get('distance', 'cosine'),
                'embedding_model': self.embedding_service.get_model_info(),
                'search_capabilities': [
                    'vector_search',
                    'hybrid_search',
                    'reranking',
                    'filtering',
                    'document_type_filtering',
                    'page_range_filtering'
                ]
            }
            
        except Exception as e:
            return {'error': f'Fehler beim Abrufen der Statistiken: {str(e)}'}
    
    def validate_search_query(self, query: str) -> Tuple[bool, str]:
        """Validiert eine Suchanfrage."""
        if not query or not query.strip():
            return False, "Suchanfrage darf nicht leer sein"
        
        if len(query.strip()) < 3:
            return False, "Suchanfrage muss mindestens 3 Zeichen lang sein"
        
        if len(query) > 1000:
            return False, "Suchanfrage ist zu lang (max. 1000 Zeichen)"
        
        return True, "Suchanfrage ist gültig"
    
    def suggest_search_improvements(self, query: str) -> List[str]:
        """Schlägt Verbesserungen für die Suchanfrage vor."""
        suggestions = []
        
        # Prüfe Länge
        if len(query) < 10:
            suggestions.append("Verwende spezifischere Begriffe für bessere Ergebnisse")
        
        # Prüfe auf Fragewörter
        question_words = ['was', 'wie', 'wo', 'wann', 'warum', 'wer']
        if not any(word in query.lower() for word in question_words):
            suggestions.append("Formuliere deine Anfrage als Frage für bessere Ergebnisse")
        
        # Prüfe auf zu allgemeine Begriffe
        generic_words = ['dokument', 'text', 'information', 'daten']
        if any(word in query.lower() for word in generic_words):
            suggestions.append("Verwende spezifischere Begriffe statt allgemeiner Wörter")
        
        return suggestions
