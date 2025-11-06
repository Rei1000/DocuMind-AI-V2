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
            
            # 3. Hole echte Vision-Daten aus der Datenbank (BEVOR IndexedDocument erstellt wird)
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
            
            # 4. Speichere IndexedDocument ZUERST (um eine echte ID zu bekommen)
            saved_doc = self.indexed_document_repo.save(indexed_doc)
            
            # 5. Extrahiere Chunks mit strukturierter Chunking-Strategie (NACH IndexedDocument erstellt)
            # Jetzt können wir die echte indexed_document_id verwenden
            chunks = self.vision_extractor.extract_chunks_from_vision_data(
                vision_data, 
                saved_doc.id,  # Echte IndexedDocument ID
                document_type
            )
            
            print(f"DEBUG: Vision data count: {len(vision_data)}")
            print(f"DEBUG: Vision data content: {vision_data}")
            print(f"DEBUG: Chunks created: {len(chunks)}")
            for i, chunk in enumerate(chunks):
                print(f"DEBUG: Chunk {i}: {chunk.chunk_text[:100]}...")
            
            # Prüfe ob Chunks erstellt wurden - wenn nicht, Fehler werfen und IndexedDocument löschen
            if not chunks or len(chunks) == 0:
                # Lösche IndexedDocument wieder, da keine Chunks erstellt wurden
                try:
                    self.indexed_document_repo.delete(saved_doc.id)
                    if 'collection_name' in locals():
                        try:
                            self.vector_store.delete_collection(collection_name)
                        except:
                            pass
                except:
                    pass
                raise ValueError("Keine Chunks konnten aus dem Dokument extrahiert werden. Bitte stellen Sie sicher, dass das Dokument erfolgreich mit AI verarbeitet wurde.")
            
            # 6. Speichere Chunks (Chunks haben bereits die korrekte indexed_document_id)
            saved_chunks = self.chunk_repo.save_batch(chunks)
            
            # 7. Erstelle Collection in Qdrant mit dynamischer Dimension
            # Hole Dimension vom Embedding Service (unterschiedlich je nach Provider)
            embedding_dimension = self.embedding_service.get_dimensions()
            collection_created = self.vector_store.create_collection(collection_name, embedding_dimension)
            print(f"DEBUG: Collection {collection_name} erstellt mit {embedding_dimension} Dimensionen: {collection_created}")
            
            # 8. Hole document_title aus UploadDocument
            from backend.app.database import get_db
            from sqlalchemy import text
            
            db_session = next(get_db())
            doc_info_result = db_session.execute(text('''
                SELECT ud.original_filename, dt.name as document_type_name
                FROM upload_documents ud
                JOIN document_types dt ON ud.document_type_id = dt.id
                WHERE ud.id = :doc_id
            '''), {"doc_id": upload_document_id})
            
            doc_info_row = doc_info_result.fetchone()
            document_title = doc_info_row[0] if doc_info_row else f"Dokument {upload_document_id}"
            document_type_name = doc_info_row[1] if doc_info_row else document_type
            
            print(f"DEBUG: Document title: {document_title}, document_type: {document_type_name}")
            
            # 9. Erstelle Embeddings und speichere in Qdrant
            chunks_data = []
            for chunk in saved_chunks:
                # Erstelle Embedding für Chunk
                embedding = self.embedding_service.generate_embedding(chunk.chunk_text)
                
                # Bereite Metadaten vor (WICHTIG: document_id, document_type, document_title hinzufügen!)
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
                    "document_id": upload_document_id,  # WICHTIG: Für Source References
                    "upload_document_id": upload_document_id,  # Alias für Kompatibilität
                    "document_type": document_type_name,  # WICHTIG: Für dokumenttyp-spezifische Prompts
                    "document_type_name": document_type_name,  # Alias für Kompatibilität
                    "document_title": document_title,  # WICHTIG: Für Source References
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
            
            # 10. Aktualisiere IndexedDocument
            saved_doc.total_chunks = len(saved_chunks)
            updated_doc = self.indexed_document_repo.save(saved_doc)
            
            # 11. Publiziere Events (optional)
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
            
            # WICHTIG: Wenn IndexedDocument bereits erstellt wurde, aber Indexierung fehlgeschlagen ist, lösche es
            try:
                if 'saved_doc' in locals() and saved_doc and saved_doc.id:
                    print(f"DEBUG: Lösche IndexedDocument {saved_doc.id} wegen Fehler bei Indexierung")
                    self.indexed_document_repo.delete(saved_doc.id)
                    # Lösche auch Collection falls erstellt
                    if 'collection_name' in locals():
                        try:
                            self.vector_store.delete_collection(collection_name)
                        except:
                            pass
            except Exception as cleanup_error:
                print(f"DEBUG: Fehler beim Cleanup: {cleanup_error}")
            
            return {
                "success": False,
                "error": str(e)
            }


class RemoveDocumentFromRAGUseCase:
    """
    Use Case: Dokument aus RAG entfernen.
    
    NEU Phase 5: RAG Cleanup für Document Lifecycle Management.
    
    Verantwortlichkeiten:
    - Entferne alle Chunks aus Vector Store (Qdrant)
    - Lösche alle Chunks aus Chunk Repository
    - Lösche IndexedDocument aus Repository
    - Idempotent: Kein Fehler wenn Dokument nicht indexiert ist
    
    Args:
        indexed_document_repository: IndexedDocumentRepository Interface
        document_chunk_repository: DocumentChunkRepository Interface
        vector_store: VectorStoreRepository Interface
    """
    
    def __init__(
        self,
        indexed_document_repository,
        document_chunk_repository,
        vector_store
    ):
        self.indexed_document_repository = indexed_document_repository
        self.document_chunk_repository = document_chunk_repository
        self.vector_store = vector_store
    
    def execute(self, upload_document_id: int) -> Dict[str, Any]:
        """
        Entferne Dokument aus RAG.
        
        Args:
            upload_document_id: Upload Document ID
            
        Returns:
            Dict mit success, removed_chunks, message
            
        Raises:
            Keine Exceptions (idempotent - gibt Success zurück auch wenn nicht indexiert)
        """
        # 1. Prüfe ob Dokument indexiert ist
        indexed_doc = self.indexed_document_repository.get_by_upload_document_id(
            upload_document_id
        )
        
        if not indexed_doc:
            # Dokument ist nicht indexiert - idempotent return
            return {
                "success": True,
                "removed_chunks": 0,
                "message": "Document not indexed in RAG"
            }
        
        # 2. Entferne Chunks aus Vector Store (Qdrant)
        removed_from_vector_store = self.vector_store.delete_chunks_by_document_id(
            collection_name=indexed_doc.collection_name,
            document_id=upload_document_id
        )
        
        # 3. Lösche Chunks aus Chunk Repository
        removed_chunks_from_db = self.document_chunk_repository.delete_by_indexed_document_id(
            indexed_document_id=indexed_doc.id
        )
        
        # 4. Lösche IndexedDocument
        self.indexed_document_repository.delete(indexed_document_id=indexed_doc.id)
        
        return {
            "success": True,
            "removed_chunks": removed_from_vector_store,
            "message": f"Document removed from RAG. {removed_from_vector_store} chunks removed."
        }


class AskQuestionUseCase:
    """
    Use Case: Stelle eine Frage an das RAG-System.
    
    Orchestriert die vollständige RAG-Pipeline:
    1. Erweitere Frage mit Multi-Query
    2. Suche relevante Chunks
    3. Filtere nach Interest Groups (RBAC Phase 2)
    4. Verwalte Kontext-Fenster
    5. Generiere AI-Antwort
    6. Speichere Chat-Message
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
        message_repository: ChatMessageRepository,
        permission_service=None  # Optional: Für RBAC Interest Group Filtering
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
        self.permission_service = permission_service  # RBAC: Permission Service für Interest Group Filtering
    
    async def execute(
        self, 
        question: str, 
        session_id: int, 
        model_id: str = "gpt-4o-mini",
        filters: Optional[Dict[str, Any]] = None,
        use_hybrid_search: bool = True,
        use_multi_query: bool = False,  # NEU: MultiQuery-Option (User kann aktivieren)
        score_threshold: float = 0.01  # Default für OpenAI Embeddings (niedrigere Scores)
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
            # NEU: Nur verwenden wenn use_multi_query=True (User-Option)
            if use_multi_query and self.multi_query_service:
                print(f"DEBUG: MultiQueryService aktiviert (User-Option) - generiere Varianten für: '{normalized_question}'")
                queries = self.multi_query_service.generate_queries(normalized_question)
                print(f"DEBUG: MultiQueryService generierte {len(queries)} Varianten:")
                for i, q in enumerate(queries, 1):
                    print(f"  {i}. {q}")
                # Stelle sicher, dass die normalisierte Frage auch dabei ist
                if normalized_question not in queries:
                    queries.insert(0, normalized_question)
            else:
                # Fallback: Verwende normalisierte Frage
                if not use_multi_query:
                    print(f"DEBUG: MultiQueryService deaktiviert (User-Option) - verwende nur Original-Query")
                elif not self.multi_query_service:
                    print(f"DEBUG: MultiQueryService nicht verfügbar - verwende nur Original-Query")
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
                        # WICHTIG: score_threshold wird vom Frontend übergeben (normalisiert für Embedding-Provider)
                        # Für OpenAI Embeddings sollten niedrige Werte verwendet werden (0.01-0.03)
                        # Für andere Provider (Google, Sentence Transformers) können höhere Werte (0.3-0.7) verwendet werden
                        results = self.vector_store.search_with_hybrid_scoring(
                            collection_name=doc.collection_name,
                            query_embedding=query_embedding,
                            query_text=final_query,  # WICHTIG: query_text für Text-Scoring (inkl. Schnellsuche)
                            top_k=10,
                            score_threshold=score_threshold,  # Verwende übergebenen Threshold
                            filters=qdrant_filters if qdrant_filters else None
                        )
                    else:
                        # Reine Vektor-Suche
                        # WICHTIG: score_threshold wird vom Frontend übergeben (normalisiert für Embedding-Provider)
                        results = self.vector_store.search_similar(
                            collection_name=doc.collection_name,
                            query_embedding=query_embedding,
                            filters=qdrant_filters or {},
                            top_k=10,
                            min_score=score_threshold  # Verwende übergebenen Threshold
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
            
            # 3.5 RBAC Phase 2: Interest Group Filtering
            if self.permission_service:
                try:
                    # Hole User-ID aus Session
                    session = self.session_repository.get_by_id(session_id)
                    if session:
                        user_id = session.user_id
                        
                        # Hole User-Level und Interest Groups
                        user_level = self.permission_service.get_user_level(user_id)
                        user_interest_groups = self.permission_service.get_user_interest_groups(user_id)
                        
                        print(f"DEBUG: RBAC Filter - User ID: {user_id}, Level: {user_level}, Interest Groups: {user_interest_groups}")
                        
                        # Filtere Ergebnisse nach Interest Groups (nur wenn Level < 4)
                        if user_level < 4 and user_interest_groups:
                            # Level 1-3: Nur eigene Interest Groups
                            filtered_results = self._filter_results_by_interest_group(
                                unique_results, 
                                user_interest_groups
                            )
                            print(f"DEBUG: RBAC Filter angewendet - {len(unique_results)} → {len(filtered_results)} Ergebnisse")
                            unique_results = filtered_results
                        else:
                            # Level 4-5: Alle Dokumente (keine Filterung)
                            print(f"DEBUG: RBAC Filter übersprungen - Level {user_level} sieht alle Dokumente")
                    else:
                        print(f"DEBUG: Session {session_id} nicht gefunden, überspringe RBAC Filter")
                except Exception as e:
                    print(f"DEBUG: Fehler bei RBAC Filter, verwende alle Ergebnisse: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 7. Kontext-Fenster-Management
            context_chunks = self._manage_context_window(unique_results)
            
            # 7.5. Erstelle source_references aus context_chunks
            from contexts.ragintegration.domain.value_objects import SourceReference
            source_references = []
            print(f"DEBUG: Erstelle source_references aus {len(context_chunks)} context_chunks")
            for i, chunk in enumerate(context_chunks):
                metadata = chunk.get('metadata', {})
                document_id = metadata.get('document_id') or metadata.get('upload_document_id')
                
                # WICHTIG: Fallback wenn document_id fehlt - hole es über indexed_document_id
                if not document_id:
                    indexed_document_id = metadata.get('indexed_document_id')
                    if indexed_document_id:
                        try:
                            # Hole IndexedDocument über indexed_document_id
                            indexed_doc = self.indexed_document_repository.get_by_id(indexed_document_id)
                            if indexed_doc:
                                document_id = indexed_doc.upload_document_id
                                print(f"DEBUG: Chunk {i+1}: document_id fehlt, geholt über indexed_doc_id={indexed_document_id} → document_id={document_id}")
                        except Exception as e:
                            print(f"DEBUG: Chunk {i+1}: Konnte document_id nicht über indexed_doc holen: {e}")
                
                print(f"DEBUG: Chunk {i+1}: document_id={document_id}, metadata_keys={list(metadata.keys()) if metadata else 'keine'}")
                if document_id:
                    page_numbers = metadata.get('page_numbers', [])
                    page_number = page_numbers[0] if page_numbers else 1
                    chunk_id = chunk.get('chunk_id', metadata.get('chunk_id', ''))
                    relevance_score = chunk.get('hybrid_score', chunk.get('score', 0.0))
                    # Normalisiere Score auf 0-1
                    relevance_score = max(0.0, min(1.0, float(relevance_score)))
                    
                    # Hole document_title aus IndexedDocument
                    document_title = metadata.get('document_title', 'Unbekanntes Dokument')
                    if document_title == 'Unbekanntes Dokument':
                        # Versuche aus indexed_document_repository zu holen
                        try:
                            indexed_doc = self.indexed_document_repository.get_by_upload_document_id(document_id)
                            if indexed_doc:
                                document_title = indexed_doc.document_title
                        except Exception as e:
                            print(f"DEBUG: Konnte document_title nicht holen: {e}")
                    
                    source_ref = SourceReference(
                        document_id=int(document_id),
                        document_title=document_title,
                        page_number=int(page_number),
                        chunk_id=str(chunk_id),
                        preview_image_path=metadata.get('preview_image_path'),
                        relevance_score=relevance_score,
                        text_excerpt=metadata.get('chunk_text', '')[:200]  # Erste 200 Zeichen
                    )
                    source_references.append(source_ref)
                else:
                    print(f"DEBUG: Chunk {i+1}: Keine document_id gefunden, überspringe Chunk")
            
            print(f"DEBUG: {len(source_references)} Source References erstellt")
            
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
            # Bestimme document_type aus Chunks für dokumenttyp-spezifischen Prompt
            document_type_for_prompt = None
            if context_chunks:
                first_chunk = context_chunks[0]
                metadata = first_chunk.get('metadata', {})
                document_type_for_prompt = metadata.get('document_type') or metadata.get('document_type_name')
                if document_type_for_prompt:
                    print(f"DEBUG: Document type für AI-Prompt: {document_type_for_prompt}")
            
            if self.ai_service:
                ai_response = await self.ai_service.generate_response_async(
                    question=question,
                    context_chunks=context_chunks,
                    model_id=model_id,
                    document_type=document_type_for_prompt  # Dokumenttyp für spezifischen Prompt
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
                source_references=source_references,  # WICHTIG: Verwende die erstellten source_references!
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
    
    def _filter_results_by_interest_group(
        self, 
        results: List[Dict], 
        user_interest_group_ids: List[int]
    ) -> List[Dict]:
        """
        Filtert Suchergebnisse nach User-Interest-Groups (RBAC Phase 2).
        
        Nur Dokumente, die mindestens einer User-Interest-Group zugeordnet sind,
        werden in den Ergebnissen belassen.
        
        Args:
            results: Liste von Suchergebnissen (Chunks mit Metadaten)
            user_interest_group_ids: Liste der Interest Group IDs des Users
            
        Returns:
            Gefilterte Liste von Suchergebnissen
        """
        if not user_interest_group_ids:
            # Leere Liste = keine Filterung (sollte nicht passieren bei Level < 4)
            return results
        
        filtered_results = []
        document_interest_groups_cache = {}  # Cache für Document → Interest Groups
        
        for result in results:
            metadata = result.get('metadata', {})
            document_id = metadata.get('document_id') or metadata.get('upload_document_id')
            
            if not document_id:
                # Ohne document_id können wir nicht filtern → ausschließen
                print(f"DEBUG: Chunk ohne document_id gefunden, ausschließen")
                continue
            
            document_id = int(document_id)
            
            # Hole Interest Groups des Dokuments (mit Cache)
            if document_id not in document_interest_groups_cache:
                document_interest_groups = self._get_document_interest_groups(document_id)
                document_interest_groups_cache[document_id] = document_interest_groups
            else:
                document_interest_groups = document_interest_groups_cache[document_id]
            
            # Prüfe ob Dokument zu User-Interest-Groups gehört
            if document_interest_groups:
                # Dokument hat Interest Groups: Prüfe Überschneidung
                if any(ig_id in user_interest_group_ids for ig_id in document_interest_groups):
                    filtered_results.append(result)
                    print(f"DEBUG: Dokument {document_id} gehört zu User-IGs, behalten")
                else:
                    print(f"DEBUG: Dokument {document_id} gehört nicht zu User-IGs, entfernt")
            else:
                # Dokument hat keine Interest Groups → ausschließen (Level 1-3 sehen nur ihre IG)
                print(f"DEBUG: Dokument {document_id} hat keine Interest Groups, entfernt")
        
        return filtered_results
    
    def _get_document_interest_groups(self, upload_document_id: int) -> List[int]:
        """
        Hole Interest Group IDs eines Dokuments aus der Datenbank.
        
        Args:
            upload_document_id: Upload Document ID
            
        Returns:
            Liste der Interest Group IDs
        """
        try:
            from backend.app.models import UploadDocumentInterestGroup
            from backend.app.database import SessionLocal
            
            db_session = SessionLocal()
            try:
                interest_groups = db_session.query(
                    UploadDocumentInterestGroup.interest_group_id
                ).filter(
                    UploadDocumentInterestGroup.upload_document_id == upload_document_id
                ).all()
                
                interest_group_ids = [row[0] for row in interest_groups]
                print(f"DEBUG: Dokument {upload_document_id} hat {len(interest_group_ids)} Interest Groups: {interest_group_ids}")
                return interest_group_ids
            finally:
                db_session.close()
        except Exception as e:
            print(f"DEBUG: Fehler beim Holen der Interest Groups für Dokument {upload_document_id}: {e}")
            return []  # Bei Fehler: Keine Interest Groups → Dokument wird entfernt
    
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
    """Use Case: Hole Document Type Counts (RBAC-gefiltert)."""
    
    def __init__(self, indexed_document_repository: IndexedDocumentRepository):
        self.indexed_document_repository = indexed_document_repository
    
    def execute(
        self, 
        document_type_ids: Optional[List[int]] = None,
        interest_group_ids: Optional[List[int]] = None
    ) -> Dict[int, int]:
        """Hole Counts für Document Types.
        
        Args:
            document_type_ids: Liste von Document Type IDs (None = alle)
            interest_group_ids: Optional - Filter nach Interest Groups (RBAC Multi-Level)
                              None/Leere Liste = alle Dokumente (Level 4-5)
                              Liste mit IDs = nur Dokumente in diesen IGs (Level 1-3)
        
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
            
            # Erstelle Dict mit Counts (RBAC-gefiltert)
            counts = {}
            for doc_type_id in document_type_ids:
                counts[doc_type_id] = self.indexed_document_repository.count_by_document_type(
                    document_type_id=doc_type_id,
                    interest_group_ids=interest_group_ids
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


# ============================================================================
# AUDIT-TRAIL USE CASES (PHASE 1.2)
# ============================================================================

class LogRAGActionUseCase:
    """
    Use Case: RAG-Aktion im Audit-Trail loggen.
    
    Protokolliert alle RAG-Operationen für Compliance und Transparenz.
    Wird verwendet von Event Handlers und Use Cases.
    
    Attributes:
        audit_repo: Repository für RAGAuditLog Entities
    """
    
    def __init__(self, audit_repo):
        """
        Initialisiere Use Case.
        
        Args:
            audit_repo: RAGAuditLogRepository Instance
        """
        self.audit_repo = audit_repo
    
    async def execute(
        self,
        action: str,
        user_id: int,
        details: Dict[str, Any],
        indexed_document_id: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        cost_usd: Optional[float] = None
    ):
        """
        Logge RAG-Aktion.
        
        Args:
            action: Action-Type (z.B. "chunking_started")
            user_id: User der die Aktion ausführte
            details: JSON-Details mit allen Parametern
            indexed_document_id: Optional Document ID (NULL bei Chat-Queries)
            status: Status der Aktion ("success", "failed", "in_progress")
            error_message: Optional Fehler-Message
            duration_ms: Optional Dauer in Millisekunden
            tokens_used: Optional Anzahl verwendeter Tokens
            cost_usd: Optional Kosten in USD
        
        Returns:
            Gespeicherter RAGAuditLog
        """
        from contexts.ragintegration.domain.entities import RAGAuditLog
        
        # Erstelle Entity
        audit_log = RAGAuditLog(
            id=None,
            indexed_document_id=indexed_document_id,
            action=action,
            user_id=user_id,
            timestamp=datetime.utcnow(),
            details=details,
            status=status,
            error_message=error_message,
            duration_ms=duration_ms,
            tokens_used=tokens_used,
            cost_usd=cost_usd
        )
        
        # Speichere in Repository
        return await self.audit_repo.save(audit_log)


class GetAuditTrailUseCase:
    """
    Use Case: Audit-Trail für Dokument oder User abrufen.
    
    Ermöglicht Abruf der vollständigen Historie aller RAG-Operationen
    für Compliance-Audits und Transparenz.
    
    Attributes:
        audit_repo: Repository für RAGAuditLog Entities
    """
    
    def __init__(self, audit_repo):
        """
        Initialisiere Use Case.
        
        Args:
            audit_repo: RAGAuditLogRepository Instance
        """
        self.audit_repo = audit_repo
    
    async def execute(
        self,
        indexed_document_id: Optional[int] = None,
        user_id: Optional[int] = None,
        action_filter: Optional[List[str]] = None,
        limit: int = 100
    ):
        """
        Hole Audit-Trail mit Filtern.
        
        Args:
            indexed_document_id: Optional Document ID Filter
            user_id: Optional User ID Filter
            action_filter: Optional Liste von Action-Types zum Filtern
            limit: Maximale Anzahl Einträge
        
        Returns:
            Liste von RAGAuditLog Entities (sortiert nach timestamp DESC)
        """
        # Wenn Document ID gegeben, hole Einträge für Dokument
        if indexed_document_id:
            return await self.audit_repo.get_by_document_id(
                indexed_document_id=indexed_document_id,
                limit=limit
            )
        
        # Wenn User ID gegeben, hole Einträge für User
        if user_id:
            return await self.audit_repo.get_by_user_id(
                user_id=user_id,
                limit=limit
            )
        
        # TODO: Implementiere action_filter wenn benötigt
        # Für jetzt: Gebe leere Liste zurück wenn keine Filter
        return []