"""
Infrastructure Layer: Qdrant Vector Store Adapter

Implementiert den VectorStoreRepository mit Qdrant (Persistent Mode).
"""

from typing import List, Dict, Any, Optional
import unicodedata
import uuid
import os
from urllib.parse import urlparse
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http.exceptions import UnexpectedResponse

from contexts.ragintegration.domain.value_objects import EmbeddingVector, SourceReference
from contexts.ragintegration.domain.repositories import VectorStoreRepository


class QdrantVectorStoreAdapter(VectorStoreRepository):
    """Qdrant Implementation des VectorStoreRepository."""
    
    def __init__(self, collection_name: str = "rag_documents"):
        """Initialisiert den Qdrant Client für persistente Speicherung."""
        # Lese QDRANT_URL aus Environment-Variable
        qdrant_url = os.getenv("QDRANT_URL", "localhost:6333")
        
        # Parse URL-Format (http://host:port, https://host:port, host:port)
        if "://" in qdrant_url:
            # HTTP/HTTPS Format
            parsed = urlparse(qdrant_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 6333
        else:
            # Host:Port Format
            if ":" in qdrant_url:
                host, port_str = qdrant_url.split(":", 1)
                port = int(port_str)
            else:
                host = qdrant_url
                port = 6333
        
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Stellt sicher, dass die Collection existiert."""
        try:
            # Prüfe ob Collection existiert
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Erstelle Collection mit Standard-Dimensionen
                # WICHTIG: Dimension muss mit Embedding Service übereinstimmen!
                # Default: 1536 (OpenAI text-embedding-3-small)
                # Kann aber variieren je nach Provider (Sentence Transformers: 384 oder 768)
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # Default, wird aber beim Indexieren durch tatsächliche Dimension überschrieben
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
        print(f"DEBUG search_similar: min_score={min_score}, top_k={top_k}, collection={collection_name}")
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
        print(f"DEBUG search_with_hybrid_scoring: score_threshold={score_threshold}, top_k={top_k}, collection={collection_name}")
        try:
            query_terms_for_recall = [w for w in query_text.lower().split() if len(w) >= 3]
            is_short_query = len(query_terms_for_recall) <= 2
            candidate_multiplier = 10 if is_short_query else 3

            # 1. Vektor-Suche
            # WICHTIG: Verwende niedrigeren Threshold für Vector-Search (0.0 für maximale Abdeckung)
            # Der Hybrid-Score wird später gefiltert
            vector_results = self.search_similar(
                collection_name=collection_name,
                query_embedding=query_embedding,
                filters=filters or {},
                top_k=top_k * candidate_multiplier,  # Mehr Kandidaten, v.a. für kurze Queries
                min_score=0.0  # Kein Threshold für Vector-Search (Hybrid-Score wird später gefiltert)
            )

            # 1.5 Kurzquery-Lexikal-Fallback:
            # Falls Embedding-Raum nicht ideal passt (z.B. Modell-Migration), holen wir
            # zusätzliche Kandidaten über Textterm-Match direkt aus der Collection.
            if is_short_query:
                lexical_results = self._search_lexical_candidates(
                    collection_name=collection_name,
                    query_text=query_text,
                    filters=filters or {},
                    max_candidates=max(top_k * 30, 120)
                )
                if lexical_results:
                    # Merge über chunk_id, bevor Hybrid-Scoring berechnet wird
                    merged_by_chunk = {
                        str(item.get("chunk_id")): item for item in vector_results
                    }
                    for lex_item in lexical_results:
                        chunk_id = str(lex_item.get("chunk_id"))
                        if chunk_id not in merged_by_chunk:
                            merged_by_chunk[chunk_id] = lex_item
                    vector_results = list(merged_by_chunk.values())
            
            # 2. Text-Scoring hinzufügen
            hybrid_results = []
            for result in vector_results:
                chunk_text = result['metadata'].get('chunk_text', '')
                text_score = self._calculate_text_relevance(query_text, chunk_text)
                
                # Kombiniere Vektor-Score mit Text-Score
                vector_score = float(result.get('score', 0.0) or 0.0)
                base_hybrid = (vector_score * 0.7) + (text_score * 0.3)
                if is_short_query:
                    # Bei kurzen Fachbegriffen darf starker Lexikal-Match dominieren.
                    hybrid_score = max(base_hybrid, text_score * 0.7)
                else:
                    hybrid_score = base_hybrid
                
                # DEBUG: Zeige Score-Vergleich für erste Ergebnisse
                if len(hybrid_results) < 3:  # Nur erste 3 für Debug
                    print(f"DEBUG Hybrid Score: vector={vector_score:.4f}, text={text_score:.4f}, hybrid={hybrid_score:.4f}, threshold={score_threshold:.4f}, pass={hybrid_score >= score_threshold}")
                    print(f"DEBUG text_score Details: query='{query_text[:50]}...', chunk_text='{chunk_text[:100]}...', text_score={text_score}")
                
                if hybrid_score >= score_threshold:
                    # NEU: Speichere alle Scores für Transparenz
                    result['hybrid_score'] = hybrid_score
                    result['vector_score'] = vector_score
                    result['text_score'] = text_score
                    hybrid_results.append(result)
            
            # 3. Sortiere nach Hybrid-Score
            if is_short_query:
                hybrid_results.sort(
                    key=lambda x: (
                        x['hybrid_score'],
                        self._short_query_tie_breaker(x.get('metadata', {})),
                        x.get('text_score', 0.0),
                        x.get('vector_score', 0.0)
                    ),
                    reverse=True
                )
            else:
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

    def _search_lexical_candidates(
        self,
        collection_name: str,
        query_text: str,
        filters: Dict[str, Any],
        max_candidates: int = 200
    ) -> List[Dict[str, Any]]:
        """Sammelt textbasierte Kandidaten direkt aus Qdrant-Payloads."""
        try:
            qdrant_filter = self._build_qdrant_filter(filters)
            points, _ = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=qdrant_filter,
                limit=max_candidates,
                with_payload=True,
                with_vectors=False
            )

            query_terms = [
                self._normalize_for_match(w)
                for w in query_text.lower().split()
                if len(w) >= 3
            ]
            query_terms = [t for t in query_terms if t]
            if not query_terms:
                return []

            candidates: List[Dict[str, Any]] = []
            for point in points:
                payload = point.payload or {}
                chunk_text = payload.get("chunk_text", "")
                normalized_text = self._normalize_for_match(chunk_text)
                if not normalized_text:
                    continue

                # Nur Kandidaten mit mindestens einem Query-Term berücksichtigen
                if not any(term in normalized_text for term in query_terms):
                    continue

                candidates.append({
                    "chunk_id": point.id,
                    "score": 0.0,  # Reines Lexikal-Kandidat, Score kommt aus Text-Relevanz
                    "metadata": payload
                })

            return candidates
        except Exception:
            return []

    def _build_qdrant_filter(self, filters: Dict[str, Any]) -> Optional[Filter]:
        """Konvertiert Dict-Filter in Qdrant-Filterobjekt."""
        if not filters:
            return None
        conditions = []
        for key, value in filters.items():
            if isinstance(value, list):
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
            else:
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
        return Filter(must=conditions) if conditions else None

    @staticmethod
    def _short_query_tie_breaker(metadata: Dict[str, Any]) -> float:
        """Sekundär-Ranking für Kurzqueries mit vielen Score-Gleichständen."""
        chunk_type = str(metadata.get("chunk_type", "")).lower()
        chunk_text = str(metadata.get("chunk_text", "")).lower()

        type_priority = {
            "requirement": 1.0,
            "definition": 0.9,
            "test_method": 0.8,
            "section": 0.7,
            "equation": 0.6,
            "figure": 0.2,
        }.get(chunk_type, 0.5)

        numeric_signal = 0.0
        if any(token in chunk_text for token in [" bis ", " range ", "von ", "kg", "max", "min"]):
            numeric_signal += 0.15
        if "trägheitsmoment" in chunk_text or "traegheitsmoment" in chunk_text:
            numeric_signal += 0.1

        return type_priority + numeric_signal
    
    def _calculate_text_relevance(self, query: str, text: str) -> float:
        """
        Berechnet Text-Relevanz zwischen Query und Text.
        
        NEU: Verwendet BM25 statt Jaccard-Ähnlichkeit für bessere Keyword-Suche.
        NEU v2.9.1: Boost für Chunks die mehrere Query-Begriffe enthalten.
        """
        try:
            # NEU: Verwende BM25 für bessere Text-Relevanz
            from contexts.ragintegration.infrastructure.bm25_service import BM25Service
            
            bm25_service = BM25Service()
            score = bm25_service.calculate_score(query, text)
            
            # NEU v2.9.1: Boost für Chunks die mehrere Query-Begriffe enthalten
            # Extrahiere Query-Begriffe (mindestens 3 Zeichen, keine Stop-Wörter)
            query_lower = query.lower()
            stop_words = {'der', 'die', 'das', 'ein', 'eine', 'und', 'oder', 'aber', 'ist', 'sind', 'wird', 'werden', 'hat', 'haben', 'zu', 'zum', 'zur', 'von', 'vom', 'für', 'mit', 'bei', 'in', 'im', 'auf', 'an'}
            query_terms = [w for w in query_lower.split() if len(w) >= 3 and w not in stop_words]
            
            if len(query_terms) >= 2:
                # Prüfe wie viele Query-Begriffe im Text vorkommen
                text_lower = text.lower()
                matched_terms = sum(1 for term in query_terms if term in text_lower)
                
                # Boost wenn mehrere Begriffe matchen (z.B. "entsorgung" UND "loctite")
                if matched_terms >= 2:
                    # Starker Boost für Chunks mit mehreren Query-Begriffen
                    boost = 1.0 + (matched_terms / len(query_terms)) * 0.3  # Bis zu 30% Boost
                    score = min(1.0, score * boost)
                elif matched_terms == 1 and len(query_terms) >= 2:
                    # WICHTIG: Keine Penalty für Chunks mit einem Begriff!
                    # Bei "entsorgung loctite" kann "Entsorgung" im Chunk-Text sein,
                    # während "Loctite" nur im Dokument-Namen steht (nicht im Chunk-Text).
                    # Diese Chunks sind trotzdem relevant und sollten nicht bestraft werden.
                    # Stattdessen: Leichter Boost wenn der Begriff im Text vorkommt
                    # (der andere Begriff ist wahrscheinlich im Dokument-Namen/Metadaten)
                    boost = 1.0 + 0.1  # 10% Boost für Chunks mit einem Query-Begriff
                    score = min(1.0, score * boost)

            # NEU v2.9.5: Exakter Begriffstreffer für kurze Fachqueries priorisieren.
            # Das verbessert Fälle wie "trägheitsmoment", bei denen ein einzelner
            # Terminus stark aussagekräftig ist.
            if len(query_terms) == 1:
                term = query_terms[0]
                normalized_term = self._normalize_for_match(term)
                normalized_text = self._normalize_for_match(text)
                if normalized_term and normalized_term in normalized_text:
                    score = max(score, 0.75)
            
            return score
            
        except Exception as e:
            # Fallback: Einfache Jaccard-Ähnlichkeit bei Fehler
            try:
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

    @staticmethod
    def _normalize_for_match(value: str) -> str:
        """Normalisiert Text robust für exakte Terminus-Matches."""
        lowered = value.lower()
        umlaut_mapped = (
            lowered
            .replace("ä", "ae")
            .replace("ö", "oe")
            .replace("ü", "ue")
            .replace("ß", "ss")
        )
        return "".join(
            ch for ch in unicodedata.normalize("NFKD", umlaut_mapped)
            if not unicodedata.combining(ch)
        )

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
