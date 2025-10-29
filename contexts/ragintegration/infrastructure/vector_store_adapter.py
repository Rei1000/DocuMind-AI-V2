"""
Infrastructure Layer: Qdrant Vector Store Adapter

Implementiert den VectorStoreRepository mit Qdrant (Persistent Mode).
"""

from typing import List, Dict, Any, Optional
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http.exceptions import UnexpectedResponse

from contexts.ragintegration.domain.value_objects import EmbeddingVector, SourceReference
from contexts.ragintegration.domain.repositories import VectorStoreRepository


class QdrantVectorStoreAdapter(VectorStoreRepository):
    """Qdrant Implementation des VectorStoreRepository."""
    
    def __init__(self, collection_name: str = "rag_documents"):
        """Initialisiert den Qdrant Client für persistente Speicherung."""
        # Verwende lokalen Qdrant-Server für persistente Speicherung
        self.client = QdrantClient(host="localhost", port=6333)
        self.collection_name = collection_name
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Stellt sicher, dass die Collection existiert."""
        try:
            # Prüfe ob Collection existiert
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Erstelle Collection mit 1536 Dimensionen (OpenAI text-embedding-3-small)
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            raise RuntimeError(f"Fehler beim Erstellen der Qdrant Collection: {str(e)}")
    
    def collection_exists(self, collection_name: str) -> bool:
        """Prüft ob Collection existiert."""
        try:
            collections = self.client.get_collections()
            return collection_name in [col.name for col in collections.collections]
        except Exception:
            return False
    
    def create_collection(self, collection_name: str, vector_size: int = 1536) -> bool:
        """Erstellt eine neue Collection."""
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            return True
        except Exception:
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Löscht eine Collection."""
        try:
            self.client.delete_collection(collection_name)
            return True
        except Exception:
            return False
    
    def index_chunk(self, collection_name: str, chunk_id: str, 
                   embedding: EmbeddingVector, metadata: Dict[str, Any]) -> bool:
        """Indexiere einzelnen Chunk."""
        try:
            # Konvertiere chunk_id zu UUID falls nötig
            import uuid
            if not self._is_valid_uuid(chunk_id):
                # Erstelle deterministische UUID aus chunk_id
                uuid_obj = uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id)
                point_id = str(uuid_obj)
            else:
                point_id = chunk_id
            
            point = PointStruct(
                id=point_id,
                vector=embedding.vector,
                payload=metadata
            )
            
            self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            return True
            
        except Exception as e:
            print(f"DEBUG: Fehler beim Indexieren von Chunk {chunk_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _is_valid_uuid(self, uuid_string: str) -> bool:
        """Prüfe ob String eine gültige UUID ist."""
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False
    
    def index_chunks_batch(self, collection_name: str, 
                          chunks_data: List[Dict[str, Any]]) -> int:
        """Indexiere mehrere Chunks."""
        try:
            points = []
            for chunk_data in chunks_data:
                # Konvertiere chunk_id zu UUID falls nötig
                chunk_id = chunk_data['chunk_id']
                if not self._is_valid_uuid(chunk_id):
                    # Erstelle deterministische UUID aus chunk_id
                    uuid_obj = uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id)
                    point_id = str(uuid_obj)
                else:
                    point_id = chunk_id
                
                point = PointStruct(
                    id=point_id,
                    vector=chunk_data['embedding'].vector,
                    payload=chunk_data['metadata']
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            return len(points)
            
        except Exception as e:
            print(f"DEBUG: Fehler beim Batch-Indexieren: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def search_similar(self, collection_name: str, query_embedding: EmbeddingVector,
                      filters: Dict[str, Any], top_k: int, min_score: float) -> List[Dict[str, Any]]:
        """Suche ähnliche Chunks."""
        try:
            # Baue Filter für Qdrant
            qdrant_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=value))
                        )
                    else:
                        conditions.append(
                            FieldCondition(key=key, match=MatchValue(value=value))
                        )
                
                if conditions:
                    qdrant_filter = Filter(must=conditions)
            
            # Suche ähnliche Vektoren
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding.vector,
                limit=top_k,
                score_threshold=min_score,
                query_filter=qdrant_filter
            )
            
            # Konvertiere zu unserem Format
            results = []
            for point in search_result:
                results.append({
                    'chunk_id': point.id,
                    'score': point.score,
                    'metadata': point.payload
                })
            
            return results
            
        except Exception:
            return []
    
    def delete_chunk(self, collection_name: str, chunk_id: str) -> bool:
        """Lösche einzelnen Chunk."""
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=[chunk_id]
            )
            return True
            
        except Exception:
            return False
    
    def delete_chunks_by_document_id(self, collection_name: str, document_id: int) -> int:
        """Lösche alle Chunks eines Dokuments."""
        try:
            # Suche alle Chunks des Dokuments
            search_result = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id", 
                            match=MatchValue(value=document_id)
                        )
                    ]
                ),
                limit=10000  # Große Zahl für alle Chunks
            )
            
            chunk_ids = [point.id for point in search_result[0]]
            
            if chunk_ids:
                self.client.delete(
                    collection_name=collection_name,
                    points_selector=chunk_ids
                )
            
            return len(chunk_ids)
            
        except Exception:
            return 0
    
    def search_with_hybrid_scoring(self, collection_name: str, query_embedding: EmbeddingVector,
                                   query_text: str, top_k: int, score_threshold: float,
                                   filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Hybrid Search mit Vektor- und Text-Scoring."""
        try:
            # 1. Vektor-Suche
            vector_results = self.search_similar(
                collection_name=collection_name,
                query_embedding=query_embedding,
                filters=filters or {},
                top_k=top_k * 2,  # Mehr Ergebnisse für Hybrid Scoring
                min_score=score_threshold * 0.5
            )
            
            # 2. Text-Scoring hinzufügen
            hybrid_results = []
            for result in vector_results:
                chunk_text = result['metadata'].get('chunk_text', '')
                text_score = self._calculate_text_relevance(query_text, chunk_text)
                
                # Kombiniere Vektor-Score mit Text-Score
                vector_score = result['score']
                hybrid_score = (vector_score * 0.7) + (text_score * 0.3)
                
                if hybrid_score >= score_threshold:
                    result['hybrid_score'] = hybrid_score
                    hybrid_results.append(result)
            
            # 3. Sortiere nach Hybrid-Score
            hybrid_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
            
            # 4. Begrenze auf top_k
            return hybrid_results[:top_k]
            
        except Exception as e:
            print(f"DEBUG: Fehler bei Hybrid Search: {e}")
            # Fallback: Normale Vektor-Suche
            return self.search_similar(
                collection_name=collection_name,
                query_embedding=query_embedding,
                filters=filters or {},
                top_k=top_k,
                min_score=score_threshold
            )
    
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

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Hole Collection-Informationen."""
        try:
            collection_info = self.client.get_collection(collection_name)
            return {
                'name': collection_name,
                'vector_size': collection_info.config.params.vectors.size,
                'distance': collection_info.config.params.vectors.distance,
                'points_count': collection_info.points_count
            }
        except Exception:
            return {'name': collection_name, 'vector_size': 0, 'distance': 'cosine', 'points_count': 0}
