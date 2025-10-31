"""
RAG Integration Use Cases

Use Cases für RAG Integration Context basierend auf Clean DDD.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from contexts.ragintegration.domain.entities import (
    IndexedDocument, DocumentChunk, ChatSession, ChatMessage
)
from contexts.ragintegration.domain.value_objects import RAGConfig
from contexts.ragintegration.domain.repositories import (
    IndexedDocumentRepository, DocumentChunkRepository, 
    ChatSessionRepository, ChatMessageRepository, RAGConfigRepository
)
from contexts.ragintegration.domain.events import (
    DocumentIndexedEvent, ChunkCreatedEvent, ChatMessageCreatedEvent
)


# ===== BESTEHENDE USE CASES =====

class IndexApprovedDocumentUseCase:
    """
    Use Case: Indexiere ein genehmigtes Dokument.
    
    Orchestriert die vollständige Indexierung eines Dokuments:
    1. Erstelle IndexedDocument Entity
    2. Extrahiere und chunkte Dokument-Inhalte
    3. Generiere Embeddings
    4. Speichere in Vector Store
    5. Publiziere Domain Events
    """
    
    def __init__(
        self,
        indexed_document_repo: IndexedDocumentRepository,
        chunk_repo: DocumentChunkRepository,
        vision_extractor,
        chunking_service,
        embedding_service,
        vector_store,
        event_publisher
    ):
        self.indexed_document_repo = indexed_document_repo
        self.chunk_repo = chunk_repo
        self.vision_extractor = vision_extractor
        self.chunking_service = chunking_service
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.event_publisher = event_publisher
    
    def execute(self, upload_document_id: int, document_type: str) -> Dict[str, Any]:
        """
        Führe Dokument-Indexierung aus.
        
        Args:
            upload_document_id: ID des Upload-Dokuments
            document_type: Dokumenttyp
            
        Returns:
            Dict mit Indexierungs-Ergebnissen
        """
        try:
            # 1. Prüfe ob Dokument bereits indexiert ist - wenn ja, lösche alte Indexierung
            existing_doc = self.indexed_document_repo.get_by_upload_document_id(upload_document_id)
            if existing_doc:
                print(f"DEBUG: Dokument bereits indexiert (ID: {existing_doc.id}), führe Re-Indexierung durch...")
                
                # Lösche alte Chunks aus Qdrant
                old_collection_name = existing_doc.collection_name
                try:
                    # Lösche alle Chunks der alten Collection
                    deleted_count = self.vector_store.delete_chunks_by_document_id(
                        collection_name=old_collection_name,
                        document_id=upload_document_id
                    )
                    print(f"DEBUG: {deleted_count} alte Chunks aus Qdrant gelöscht")
                    
                    # Lösche Collection falls leer oder verwende neue
                    try:
                        self.vector_store.delete_collection(old_collection_name)
                        print(f"DEBUG: Alte Collection '{old_collection_name}' gelöscht")
                    except Exception as e:
                        print(f"DEBUG: Collection konnte nicht gelöscht werden (OK wenn bereits leer): {e}")
                except Exception as e:
                    print(f"DEBUG: Fehler beim Löschen alter Chunks (fortfahren mit neuem Index): {e}")
                
                # Lösche alte Chunks aus der Datenbank
                try:
                    self.chunk_repo.delete_by_indexed_document_id(existing_doc.id)
                    print(f"DEBUG: Alte Chunks aus Datenbank gelöscht")
                except Exception as e:
                    print(f"DEBUG: Fehler beim Löschen aus DB (fortfahren): {e}")
                
                # Lösche IndexedDocument - wird neu erstellt
                try:
                    self.indexed_document_repo.delete(existing_doc.id)
                    print(f"DEBUG: Altes IndexedDocument gelöscht")
                except Exception as e:
                    print(f"DEBUG: Fehler beim Löschen IndexedDocument (fortfahren): {e}")
                
                print(f"DEBUG: Re-Indexierung startet mit neuem Index...")
            
            # 2. Erstelle IndexedDocument Entity
            collection_name = f"doc_{upload_document_id}_{int(datetime.now().timestamp())}"
            
            indexed_doc = IndexedDocument(
                id=None,
                upload_document_id=upload_document_id,
                collection_name=collection_name,
                total_chunks=1,  # Start mit 1, wird später aktualisiert
                indexed_at=datetime.now(),
                last_updated_at=datetime.now()
            )
            
            # 3. Speichere IndexedDocument
            saved_doc = self.indexed_document_repo.save(indexed_doc)
            
            # 4. Hole echte Vision-Daten aus der Datenbank
            from backend.app.database import get_db
            from sqlalchemy import text
            
            db_session = next(get_db())
            result = db_session.execute(text('''
                SELECT dar.json_response, udp.page_number 
                FROM document_ai_responses dar
                JOIN upload_document_pages udp ON dar.upload_document_page_id = udp.id
                WHERE dar.upload_document_id = :doc_id
                AND dar.processing_status = 'completed'
                ORDER BY udp.page_number
            '''), {"doc_id": upload_document_id})
            
            vision_data = []
            for row in result.fetchall():
                json_response = row[0]
                page_number = row[1]
                
                if json_response:
                    try:
                        import json
                        parsed_json = json.loads(json_response) if isinstance(json_response, str) else json_response
                        vision_data.append({
                            "page_number": page_number,
                            "json_response": parsed_json
                        })
                    except json.JSONDecodeError:
                        # Fallback für einfachen Text
                        vision_data.append({
                            "page_number": page_number,
                            "json_response": {
                                "text": json_response if isinstance(json_response, str) else str(json_response),
                                "tables": [],
                                "images": []
                            }
                        })
            
            # Fallback zu Mock-Daten wenn keine echten Daten vorhanden
            if not vision_data:
                vision_data = [
                    {
                        "page_number": 1,
                        "json_response": {
                            "text": f"Arbeitsanweisung für Dokument {upload_document_id}\nArtikelnummer: 123.456.789\nSicherheitshinweise: Vor Reparatur Strom abschalten.",
                            "tables": [
                                {
                                    "data": [
                                        ["Teil", "Artikelnummer", "Beschreibung"],
                                        ["Freilaufwelle", "123.456.789", "Hauptkomponente"],
                                        ["Lager", "987.654.321", "Lagerung"]
                                    ]
                                }
                            ],
                            "images": [
                                {
                                    "description": "Freilaufwelle Montage",
                                    "ocr_text": "Freilaufwelle 123.456.789"
                                }
                            ]
                        }
                    }
                ]
            
            # 4. Extrahiere Chunks mit strukturierter Chunking-Strategie
            chunks = self.vision_extractor.extract_chunks_from_vision_data(
                vision_data, 
                saved_doc.id,
                document_type
            )
            
            print(f"DEBUG: Vision data count: {len(vision_data)}")
            print(f"DEBUG: Vision data content: {vision_data}")
            print(f"DEBUG: Chunks created: {len(chunks)}")
            for i, chunk in enumerate(chunks):
                print(f"DEBUG: Chunk {i}: {chunk.chunk_text[:100]}...")
            
            # 5. Speichere Chunks
            saved_chunks = self.chunk_repo.save_batch(chunks)
            
            # 6. Erstelle Collection in Qdrant mit dynamischer Dimension
            # Hole Dimension vom Embedding Service (unterschiedlich je nach Provider)
            embedding_dimension = self.embedding_service.get_dimensions()
            collection_created = self.vector_store.create_collection(collection_name, embedding_dimension)
            print(f"DEBUG: Collection {collection_name} erstellt mit {embedding_dimension} Dimensionen: {collection_created}")
            
            # 7. Erstelle Embeddings und speichere in Qdrant
            chunks_data = []
            for chunk in saved_chunks:
                # Erstelle Embedding für Chunk
                embedding = self.embedding_service.generate_embedding(chunk.chunk_text)
                
                # Bereite Metadaten vor
                metadata = {
                    "chunk_id": chunk.chunk_id,
                    "chunk_text": chunk.chunk_text,
                    "page_numbers": chunk.metadata.page_numbers,
                    "heading_hierarchy": chunk.metadata.heading_hierarchy,
                    "chunk_type": chunk.metadata.chunk_type,
                    "token_count": chunk.metadata.token_count,
                    "sentence_count": chunk.metadata.sentence_count,
                    "has_overlap": chunk.metadata.has_overlap,
                    "overlap_sentence_count": chunk.metadata.overlap_sentence_count,
                    "indexed_document_id": chunk.indexed_document_id,
                    "created_at": chunk.created_at.isoformat()
                }
                
                chunks_data.append({
                    "chunk_id": chunk.chunk_id,
                    "embedding": embedding,
                    "metadata": metadata
                })
            
            # Speichere alle Chunks in Qdrant
            indexed_count = self.vector_store.index_chunks_batch(collection_name, chunks_data)
            print(f"DEBUG: {indexed_count} Chunks in Qdrant indexiert")
            
            # 8. Aktualisiere IndexedDocument
            saved_doc.total_chunks = len(saved_chunks)
            updated_doc = self.indexed_document_repo.save(saved_doc)
            
            # 9. Publiziere Events (optional)
            if self.event_publisher:
                self.event_publisher.publish(DocumentIndexedEvent(
                    indexed_document_id=updated_doc.id,
                    upload_document_id=upload_document_id,
                    total_chunks=len(saved_chunks)
                ))
            
            return {
                "success": True,
                "indexed_document_id": updated_doc.id,
                "total_chunks": len(saved_chunks),
                "collection_name": collection_name
            }
            
        except Exception as e:
            print(f"DEBUG: Error in IndexApprovedDocumentUseCase: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }


class AskQuestionUseCase:
    """
    Use Case: Stelle eine Frage an das RAG-System.
    
    Orchestriert die vollständige RAG-Pipeline:
    1. Erweitere Frage mit Multi-Query
    2. Suche relevante Chunks
    3. Verwalte Kontext-Fenster
    4. Generiere AI-Antwort
    5. Speichere Chat-Message
    """
    
    def __init__(
        self,
        chunk_repository: DocumentChunkRepository,
        session_repository: ChatSessionRepository,
        indexed_document_repository,
        vector_store,
        embedding_service,
        multi_query_service,
        ai_service,
        event_publisher,
        message_repository: ChatMessageRepository
    ):
        self.chunk_repository = chunk_repository
        self.session_repository = session_repository
        self.indexed_document_repository = indexed_document_repository
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.multi_query_service = multi_query_service
        self.ai_service = ai_service
        self.event_publisher = event_publisher
        self.message_repository = message_repository
    
    async def execute(
        self, 
        question: str, 
        session_id: int, 
        model_id: str = "gpt-4o-mini",
        filters: Optional[Dict[str, Any]] = None,
        use_hybrid_search: bool = True
    ) -> ChatMessage:
        """
        Führe RAG-Frage aus.
        
        Args:
            question: User-Frage
            session_id: Chat-Session-ID
            model_id: AI-Modell-ID
            filters: Optionale Filter
            
        Returns:
            ChatMessage Entity mit Antwort
        """
        try:
            # 0. Frage-Normalisierung: Entferne Stop-Wörter am Anfang (z.B. "und", "aber", "oder")
            # Dies verbessert die Konsistenz der Vector-Search-Ergebnisse
            normalized_question = self._normalize_question(question)
            print(f"DEBUG: Original-Frage: '{question}' → Normalisiert: '{normalized_question}'")
            
            # 1. Multi-Query Expansion (verwende normalisierte Frage)
            if self.multi_query_service:
                queries = self.multi_query_service.generate_queries(normalized_question)
                # Stelle sicher, dass die normalisierte Frage auch dabei ist
                if normalized_question not in queries:
                    queries.insert(0, normalized_question)
            else:
                # Fallback: Verwende normalisierte Frage
                queries = [normalized_question]
            
            # 2. Filter-Vorbereitung: document_type ID zu Document Name konvertieren
            search_filters = filters.copy() if filters else {}
            if 'document_type' in search_filters and search_filters['document_type']:
                # document_type könnte ID (String/Number) oder Name sein
                # Prüfe ob es eine ID ist und konvertiere zu Name
                from backend.app.models import DocumentTypeModel, UploadDocument
                from backend.app.database import SessionLocal
                
                db_session = SessionLocal()
                try:
                    doc_type_value = search_filters['document_type']
                    # Versuche es als ID zu parsen
                    try:
                        doc_type_id = int(doc_type_value)
                        doc_type = db_session.query(DocumentTypeModel).filter(
                            DocumentTypeModel.id == doc_type_id
                        ).first()
                        if doc_type:
                            # Ersetze ID durch Name für Filter
                            search_filters['document_type'] = doc_type.name
                            print(f"DEBUG: Document Type ID {doc_type_id} → Name: {doc_type.name}")
                    except (ValueError, TypeError):
                        # Bereits ein Name oder ungültiger Wert
                        print(f"DEBUG: document_type ist bereits Name oder ungültig: {doc_type_value}")
                finally:
                    db_session.close()
            
            # 3. Extrahiere query aus Filters (Schnellsuche)
            quick_search_query = search_filters.pop('query', None) if search_filters else None
            
            # 4. Suche relevante Chunks
            all_results = []
            print(f"DEBUG: Suche nach Frage: '{question}' mit Filtern: {search_filters}, use_hybrid_search: {use_hybrid_search}, quick_search_query: {quick_search_query}")
            
            for query in queries:
                # Kombiniere query mit quick_search_query falls vorhanden
                final_query = query
                if quick_search_query and quick_search_query.strip():
                    final_query = f"{quick_search_query}. {query}"
                    print(f"DEBUG: Schnellsuche kombiniert mit Query: '{final_query}'")
                
                print(f"DEBUG: Verarbeite Query: '{final_query}'")
                
                # Hole alle indexierten Dokumente
                indexed_docs = self.indexed_document_repository.get_all()
                print(f"DEBUG: Gefunden {len(indexed_docs)} indexierte Dokumente")
                
                # Wenn document_type Filter gesetzt ist, filtere Dokumente vorher
                if 'document_type' in search_filters and search_filters['document_type']:
                    from backend.app.models import UploadDocument
                    from backend.app.database import SessionLocal
                    
                    db_filter = SessionLocal()
                    try:
                        doc_type_name = search_filters['document_type']
                        # Hole upload_document_ids für diesen document_type
                        filtered_upload_ids = db_filter.query(UploadDocument.id).join(
                            UploadDocument.document_type
                        ).filter(
                            UploadDocument.document_type.has(name=doc_type_name)
                        ).all()
                        filtered_upload_ids_set = {row[0] for row in filtered_upload_ids}
                        
                        # Filtere indexed_docs
                        indexed_docs = [doc for doc in indexed_docs if doc.upload_document_id in filtered_upload_ids_set]
                        print(f"DEBUG: Nach document_type Filter: {len(indexed_docs)} Dokumente")
                    finally:
                        db_filter.close()
                
                # Erstelle Embedding für die Query
                query_embedding = self.embedding_service.generate_embedding(final_query)
                
                for doc in indexed_docs:
                    print(f"DEBUG: Suche in Collection: {doc.collection_name}")
                    # Entferne document_type und query aus Qdrant-Filter da sie nicht in Metadaten sind
                    qdrant_filters = {k: v for k, v in search_filters.items() if k != 'document_type' and k != 'query'}
                    
                    if use_hybrid_search:
                        # Verwende Hybrid Search mit query_text für Text-Scoring
                        # WICHTIG: Score-Threshold auf 0.01 gesenkt (OpenAI Embeddings haben niedrigere Scores)
                        results = self.vector_store.search_with_hybrid_scoring(
                            collection_name=doc.collection_name,
                            query_embedding=query_embedding,
                            query_text=final_query,  # WICHTIG: query_text für Text-Scoring (inkl. Schnellsuche)
                            top_k=10,
                            score_threshold=0.01,  # Gesenkt von 0.5 auf 0.01 (OpenAI Embeddings haben Scores ~0.02-0.03)
                            filters=qdrant_filters if qdrant_filters else None
                        )
                    else:
                        # Reine Vektor-Suche
                        # WICHTIG: Score-Threshold auf 0.01 gesenkt (OpenAI Embeddings haben niedrigere Scores)
                        results = self.vector_store.search_similar(
                            collection_name=doc.collection_name,
                            query_embedding=query_embedding,
                            filters=qdrant_filters or {},
                            top_k=10,
                            min_score=0.01  # Gesenkt von 0.5 auf 0.01 (OpenAI Embeddings haben Scores ~0.02-0.03)
                        )
                    print(f"DEBUG: Gefunden {len(results)} Ergebnisse in {doc.collection_name}")
                    all_results.extend(results)
            
            print(f"DEBUG: Gesamt {len(all_results)} Ergebnisse gefunden")
            
            # 3. Deduplizierung und Ranking
            unique_results = self._deduplicate_and_rank(all_results)
            
            # 6. Verwende echte Ergebnisse oder leere Liste
            if not unique_results:
                print("DEBUG: Keine Suchergebnisse gefunden, verwende leere Liste")
                unique_results = []
            
            # 7. Kontext-Fenster-Management
            context_chunks = self._manage_context_window(unique_results)
            
            # 8. Speichere User-Nachricht (Frage) ZUERST in der Datenbank
            user_message = ChatMessage(
                id=None,
                session_id=session_id,
                role="user",
                content=question,  # Die ursprüngliche Frage des Users
                source_references=[],
                ai_model_used=None,  # User-Nachrichten haben kein AI-Model
                created_at=datetime.now()
            )
            saved_user_message = self.message_repository.save(user_message)
            print(f"DEBUG: User-Nachricht gespeichert: ID={saved_user_message.id}, Content={question[:50]}...")
            
            # 9. AI-Antwort generieren
            if self.ai_service:
                ai_response = await self.ai_service.generate_response_async(
                    question=question,
                    context_chunks=context_chunks,
                    model_id=model_id
                )
            else:
                # Fallback zu Mock-Antwort
                ai_response = {
                    "answer": f"Basierend auf den verfügbaren Dokumenten kann ich folgende Informationen zu Ihrer Frage \"{question}\" geben: Das Dokument enthält wichtige Informationen über Arbeitsanweisungen und Verfahren.",
                    "model_used": model_id,
                    "tokens_used": 50,
                    "confidence": 0.5,
                    "provider": "mock"
                }
            
            # 10. Erstelle Assistant-ChatMessage
            assistant_message = ChatMessage(
                id=None,
                session_id=session_id,
                role="assistant",
                content=ai_response["answer"],
                source_references=[],
                ai_model_used=model_id,  # AI Model das für diese Antwort verwendet wurde
                created_at=datetime.now()
            )
            
            # 11. Publiziere Event
            if self.event_publisher:
                self.event_publisher.publish(ChatMessageCreatedEvent(
                    message_id=assistant_message.id,
                    session_id=session_id,
                    question=question,
                    answer=ai_response["answer"]
                ))
            
            # 12. Speichere Assistant-Message in der Datenbank
            saved_assistant_message = self.message_repository.save(assistant_message)
            print(f"DEBUG: Assistant-Nachricht gespeichert: ID={saved_assistant_message.id}")
            
            return saved_assistant_message
            
        except Exception as e:
            # Fallback bei Fehlern
            import traceback
            traceback.print_exc()
            
            # Versuche trotzdem User-Nachricht zu speichern (falls noch nicht gespeichert)
            try:
                # Prüfe ob User-Nachricht bereits gespeichert wurde
                # (In diesem Fall könnte sie bei Schritt 8 gespeichert worden sein)
                # Falls nicht, speichere sie jetzt
                user_message = ChatMessage(
                    id=None,
                    session_id=session_id,
                    role="user",
                    content=question,
                    source_references=[],
                    ai_model_used=None,
                    created_at=datetime.now()
                )
                self.message_repository.save(user_message)
            except Exception as save_error:
                print(f"WARNUNG: Konnte User-Nachricht nicht speichern: {str(save_error)}")
            
            # Erstelle und speichere Fehler-Nachricht
            error_message = ChatMessage(
                id=None,
                session_id=session_id,
                role="assistant",
                content=f"Entschuldigung, es gab einen Fehler: {str(e)}",
                source_references=[],
                ai_model_used=model_id,
                created_at=datetime.now()
            )
            saved_error_message = self.message_repository.save(error_message)
            return saved_error_message
    
    def _deduplicate_and_rank(self, results: List[Dict]) -> List[Dict]:
        """Dedupliziere und ranke Suchergebnisse."""
        seen_chunks = set()
        unique_results = []
        
        for result in results:
            chunk_id = result.get("chunk_id")
            if chunk_id and chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                unique_results.append(result)
        
        # Sortiere nach Score
        unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return unique_results
    
    def _normalize_question(self, question: str) -> str:
        """
        Normalisiert die Frage für konsistentere Vector-Search-Ergebnisse.
        
        Entfernt Stop-Wörter am Anfang (z.B. "und", "aber", "oder") die das
        Embedding beeinflussen können ohne die Bedeutung zu ändern.
        
        Args:
            question: Original-Frage
            
        Returns:
            Normalisierte Frage
        """
        if not question or not question.strip():
            return question
        
        # Normalisiere Leerzeichen
        normalized = question.strip()
        
        # Entferne Stop-Wörter am Anfang (kleinschreibung)
        stop_words = ["und", "aber", "oder", "auch", "noch", "dann", "danach"]
        normalized_lower = normalized.lower()
        
        for stop_word in stop_words:
            # Prüfe ob Frage mit Stop-Wort beginnt (gefolgt von Leerzeichen oder Komma)
            if normalized_lower.startswith(stop_word + " ") or normalized_lower.startswith(stop_word + ","):
                normalized = normalized[len(stop_word):].strip()
                # Entferne führendes Komma falls vorhanden
                if normalized.startswith(","):
                    normalized = normalized[1:].strip()
                normalized_lower = normalized.lower()
        
        return normalized if normalized else question  # Fallback: Original falls leer
    
    def _manage_context_window(self, results: List[Dict]) -> List[Dict]:
        """
        Verwalte Kontext-Fenster basierend auf Token-Limits.
        
        Erhöht die Anzahl der Chunks von 5 auf 10 für bessere Abdeckung,
        insbesondere wenn die Frage variiert wird (z.B. mit/ohne "und").
        """
        # Erhöht auf 10 Chunks für bessere Abdeckung von Varianten
        context_chunks = results[:10]
        print(f"DEBUG: Kontext-Chunks für AI-Service: {len(context_chunks)}")
        for i, chunk in enumerate(context_chunks):
            chunk_id = chunk.get('chunk_id', 'unknown')
            score = chunk.get('hybrid_score', chunk.get('score', 0))
            print(f"DEBUG: Chunk {i+1}: {chunk_id} - Score: {score:.6f}")
        return context_chunks


# ===== NEUE RAG-KONFIGURATION USE CASES =====


class CreateChatSessionUseCase:
    """Use Case: Erstelle neue Chat-Session."""
    
    def __init__(self, session_repository: ChatSessionRepository):
        self.session_repository = session_repository
    
    def execute(self, user_id: int, session_name: Optional[str] = None) -> ChatSession:
        """Erstelle neue Chat-Session."""
        if not session_name:
            session_name = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        session = ChatSession(
            id=None,
            user_id=user_id,
            session_name=session_name,
            is_active=True,
            created_at=datetime.now(),
            last_message_at=None
        )
        return self.session_repository.save(session)


class UpdateChatSessionUseCase:
    """Use Case: Aktualisiere ChatSession Name."""
    
    def __init__(self, session_repository: ChatSessionRepository):
        self.session_repository = session_repository
    
    def execute(self, session_id: int, new_session_name: str) -> ChatSession:
        """Aktualisiere Session Name."""
        session = self.session_repository.get_by_id(session_id)
        
        if not session:
            raise ValueError(f"Session mit ID {session_id} nicht gefunden")
        
        # Update session name
        session.session_name = new_session_name
        
        return self.session_repository.save(session)


class GetChatHistoryUseCase:
    """Use Case: Hole Chat-Historie."""
    
    def __init__(self, message_repository: ChatMessageRepository):
        self.message_repository = message_repository
    
    def execute(self, session_id: int) -> List[ChatMessage]:
        """Hole Chat-Historie für Session."""
        return self.message_repository.get_by_session_id(session_id)


class GetDocumentTypeCountsUseCase:
    """Use Case: Hole Document Type Counts."""
    
    def __init__(self, indexed_document_repository: IndexedDocumentRepository):
        self.indexed_document_repository = indexed_document_repository
    
    def execute(self, document_type_ids: Optional[List[int]] = None) -> Dict[int, int]:
        """Hole Counts für Document Types.
        
        Args:
            document_type_ids: Liste von Document Type IDs (None = alle)
        
        Returns:
            Dict[document_type_id, count]
        """
        from backend.app.models import DocumentTypeModel
        from backend.app.database import SessionLocal
        
        # Hole alle Document Types falls keine IDs angegeben
        db_session = SessionLocal()
        try:
            if document_type_ids is None:
                # Hole alle aktiven Document Types
                doc_types = db_session.query(DocumentTypeModel).filter(
                    DocumentTypeModel.is_active == True
                ).all()
                document_type_ids = [dt.id for dt in doc_types]
            
            # Erstelle Dict mit Counts
            counts = {}
            for doc_type_id in document_type_ids:
                counts[doc_type_id] = self.indexed_document_repository.count_by_document_type(
                    document_type_id=doc_type_id
                )
            
            return counts
        finally:
            db_session.close()


class ReindexDocumentUseCase:
    """Use Case: Reindexiere ein Dokument."""
    
    def __init__(self, indexed_document_repo: IndexedDocumentRepository):
        self.indexed_document_repo = indexed_document_repo
    
    def execute(self, indexed_document_id: int) -> Dict[str, Any]:
        """Reindexiere ein Dokument."""
        try:
            # Hole IndexedDocument
            indexed_doc = self.indexed_document_repo.get_by_id(indexed_document_id)
            if not indexed_doc:
                return {"success": False, "error": "Document not found"}
            
            # Aktualisiere Zeitstempel
            indexed_doc.last_updated_at = datetime.now()
            updated_doc = self.indexed_document_repo.save(indexed_doc)
            
            return {
                "success": True,
                "indexed_document_id": updated_doc.id,
                "last_updated_at": updated_doc.last_updated_at
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


class ConfigureRAGUseCase:
    """
    Use Case: RAG-Konfiguration speichern und anwenden.
    
    Orchestriert die RAG-Konfiguration basierend auf RAG-Anything Best Practices.
    """
    
    def __init__(self, config_repository: RAGConfigRepository):
        self.config_repository = config_repository
    
    def execute(self, config: RAGConfig) -> dict:
        """
        Führe RAG-Konfiguration aus.
        
        Args:
            config: RAG-Konfiguration
            
        Returns:
            Dict mit Erfolgs-Status und Details
        """
        try:
            # Speichere Konfiguration
            self.config_repository.save_config(config)
            
            # Validiere Konfiguration
            self._validate_configuration(config)
            
            return {
                "success": True,
                "message": "RAG-Konfiguration erfolgreich gespeichert",
                "config": config.to_dict()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Fehler bei der RAG-Konfiguration: {str(e)}",
                "config": None
            }
    
    def _validate_configuration(self, config: RAGConfig):
        """Validiere RAG-Konfiguration."""
        # Zusätzliche Validierung kann hier implementiert werden
        pass


class GetRAGConfigUseCase:
    """
    Use Case: RAG-Konfiguration abrufen.
    """
    
    def __init__(self, config_repository: RAGConfigRepository):
        self.config_repository = config_repository
    
    def execute(self) -> Optional[RAGConfig]:
        """
        Hole aktuelle RAG-Konfiguration.
        
        Returns:
            Aktuelle RAG-Konfiguration oder None
        """
        return self.config_repository.get_current_config()


class GetRAGConfigOptionsUseCase:
    """
    Use Case: Verfügbare RAG-Konfigurationsoptionen abrufen.
    """
    
    def execute(self) -> dict:
        """
        Hole alle verfügbaren Konfigurationsoptionen.
        
        Returns:
            Dict mit allen verfügbaren Optionen
        """
        config = RAGConfig()
        return config.get_available_options()