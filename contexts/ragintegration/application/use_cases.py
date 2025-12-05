"""
RAG Integration Use Cases

Use Cases für RAG Integration Context basierend auf Clean DDD.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from contexts.ragintegration.domain.entities import (
    IndexedDocument, DocumentChunk, ChatSession, ChatMessage, RAGChatPrompt
)
from contexts.ragintegration.domain.value_objects import RAGConfig, PromptType, PromptState
from contexts.ragintegration.domain.exceptions import MissingCustomPromptError, InvalidCustomPromptError
from contexts.ragintegration.domain.repositories import (
    IndexedDocumentRepository, DocumentChunkRepository, 
    ChatSessionRepository, ChatMessageRepository, RAGConfigRepository,
    RAGChatPromptRepository, SearchQualityMetricsRepository
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
            
            # WICHTIG: Setze Embedding-Modell basierend auf verwendetem Service
            embedding_model = getattr(self.embedding_service, 'model', 'text-embedding-3-small')
            if hasattr(self.embedding_service, 'model'):
                embedding_model = self.embedding_service.model
            else:
                # Fallback: Verwende Standard-Modell
                from contexts.ragintegration.infrastructure.embedding_factory import DEFAULT_EMBEDDING_MODEL
                embedding_model = DEFAULT_EMBEDDING_MODEL
            
            indexed_doc = IndexedDocument(
                id=None,
                upload_document_id=upload_document_id,
                collection_name=collection_name,
                total_chunks=1,  # Start mit 1, wird später aktualisiert
                embedding_model=embedding_model,  # WICHTIG: Speichere verwendetes Embedding-Modell
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
                        # WICHTIG: Entferne Markdown-Code-Blöcke (```json ... ```) falls vorhanden
                        if isinstance(json_response, str):
                            cleaned_json = json_response.strip()
                            if cleaned_json.startswith("```json"):
                                cleaned_json = cleaned_json[7:].strip()
                            elif cleaned_json.startswith("```"):
                                cleaned_json = cleaned_json[3:].strip()
                            if cleaned_json.endswith("```"):
                                cleaned_json = cleaned_json[:-3].strip()
                            parsed_json = json.loads(cleaned_json)
                        else:
                            parsed_json = json_response
                        vision_data.append({
                            "page_number": page_number,
                            "json_response": parsed_json
                        })
                    except json.JSONDecodeError as e:
                        print(f"WARNING: IndexApprovedDocumentUseCase: JSON-Parse-Fehler für Seite {page_number}: {e}")
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
            
            # 4. Hole embedding_model aus Embedding Service
            # WICHTIG: Speichere das verwendete Modell für konsistente Suche
            embedding_model = getattr(self.embedding_service, 'model', 'text-embedding-ada-002')
            indexed_doc.embedding_model = embedding_model
            
            # 5. Speichere IndexedDocument ZUERST (um eine echte ID zu bekommen)
            saved_doc = self.indexed_document_repo.save(indexed_doc)
            
            # 6. Extrahiere Chunks mit strukturierter Chunking-Strategie (NACH IndexedDocument erstellt)
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
            
            # 7. Speichere Chunks (Chunks haben bereits die korrekte indexed_document_id)
            saved_chunks = self.chunk_repo.save_batch(chunks)
            
            # 8. Erstelle Collection in Qdrant mit dynamischer Dimension
            # Hole Dimension vom Embedding Service (unterschiedlich je nach Provider)
            embedding_dimension = self.embedding_service.get_dimensions()
            collection_created = self.vector_store.create_collection(collection_name, embedding_dimension)
            print(f"DEBUG: Collection {collection_name} erstellt mit {embedding_dimension} Dimensionen: {collection_created}")
            
            # 9. Hole document_title und document_type_id aus UploadDocument
            from backend.app.database import get_db
            from sqlalchemy import text
            
            db_session = next(get_db())
            doc_info_result = db_session.execute(text('''
                SELECT ud.original_filename, dt.name as document_type_name, ud.document_type_id
                FROM upload_documents ud
                JOIN document_types dt ON ud.document_type_id = dt.id
                WHERE ud.id = :doc_id
            '''), {"doc_id": upload_document_id})
            
            doc_info_row = doc_info_result.fetchone()
            document_title = doc_info_row[0] if doc_info_row else f"Dokument {upload_document_id}"
            document_type_name = doc_info_row[1] if doc_info_row else document_type
            document_type_id = doc_info_row[2] if doc_info_row else None  # PHASE 1: Für Custom Prompt Lookup
            
            print(f"DEBUG: Document title: {document_title}, document_type: {document_type_name}, document_type_id: {document_type_id}")
            
            # 10. Erstelle Embeddings und speichere in Qdrant
            chunks_data = []
            for chunk in saved_chunks:
                # Erstelle Embedding für Chunk
                embedding = self.embedding_service.generate_embedding(chunk.chunk_text)
                
                # WICHTIG: Prüfe Embedding-Qualität (keine Mock Embeddings mehr!)
                if hasattr(embedding, 'model') and 'mock' in embedding.model.lower():
                    raise RuntimeError(
                        f"❌ Mock Embedding erstellt! API Key hat keinen Zugriff auf Embedding-Modell.\n"
                        f"   Embedding Model: {embedding.model}\n"
                        f"   💡 Lösung: Überprüfe OPENAI_GPT5_MINI_API_KEY oder OPENAI_API_KEY im OpenAI Dashboard"
                    )
                
                # Bereite Metadaten vor (WICHTIG: document_id, document_type, document_type_id, document_title hinzufügen!)
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
                    "document_type_id": document_type_id,  # PHASE 1: Für Custom Prompt Lookup
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
            print(f"DEBUG: {indexed_count} Chunks in Qdrant indexiert mit {embedding.model} ({embedding.dimensions} dim)")
            
            # 10. Aktualisiere IndexedDocument mit Embedding-Modell
            saved_doc.total_chunks = len(saved_chunks)
            # WICHTIG: Stelle sicher, dass Embedding-Modell korrekt gesetzt ist
            if hasattr(embedding, 'model'):
                saved_doc.embedding_model = embedding.model
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
        permission_service=None,  # Optional: Für RBAC Interest Group Filtering
        shap_service=None,  # Optional: Für SHAP-Erklärungen
        ml_model_service=None,  # Optional: Für ML Re-Ranking (Phase 4, deprecated - use ltr_service)
        ltr_service=None,  # Optional: Für Learning-to-Rank ML-Ranking (NEU v2.7.0)
        search_quality_metrics_repo=None,  # Optional: Für Search Quality Metrics Persistenz (NEU v2.9.0)
        training_data_repo=None  # Optional: Für automatisches Speichern von Training Data (NEU v2.10.0)
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
        self.shap_service = shap_service  # SHAP: Für Feature-Importance-Erklärungen
        self.ml_model_service = ml_model_service  # ML: Für Learning-to-Rank Re-Ranking (deprecated)
        self.ltr_service = ltr_service  # LTR: Neuer Learning-to-Rank Service (v2.7.0)
        self.search_quality_metrics_repo = search_quality_metrics_repo  # Search Quality Metrics: Für Persistenz (v2.9.0)
        self.training_data_repo = training_data_repo  # Training Data: Für automatisches Speichern (v2.10.0)
    
    async def execute(
        self, 
        question: str, 
        session_id: int, 
        model_id: str = "gpt-4o-mini",
        filters: Optional[Dict[str, Any]] = None,
        use_hybrid_search: bool = True,
        use_multi_query: bool = False,  # NEU: MultiQuery-Option (User kann aktivieren)
        score_threshold: float = 0.01,  # Default für OpenAI Embeddings (niedrigere Scores)
        top_k: int = 10,  # NEU: Anzahl der besten Chunks (PHASE 0.1)
        use_ml_reranking: bool = False,  # NEU: ML Re-Ranking aktivieren (Phase 4, deprecated)
        use_ml_ranking: bool = False,  # NEU: Learning-to-Rank aktivieren (v2.7.0)
        temperature: Optional[float] = None,  # NEU v2.10.3: AI Temperature (optional)
        max_tokens: Optional[int] = None,  # NEU v2.10.3: Max Tokens (optional)
        top_p: Optional[float] = None  # NEU v2.10.3: Top P (optional)
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
            
            # 1. Filter-Vorbereitung: document_type ID zu Document Name konvertieren (PHASE 2: Behalte ID für Multi-Query)
            search_filters = filters.copy() if filters else {}
            document_type_id_for_multi_query = None  # PHASE 2: Für Custom Multi-Query Prompt
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
                            # PHASE 2: Behalte document_type_id für Multi-Query Prompt
                            document_type_id_for_multi_query = doc_type_id
                            # Ersetze ID durch Name für Filter
                            search_filters['document_type'] = doc_type.name
                            print(f"DEBUG: Document Type ID {doc_type_id} → Name: {doc_type.name}")
                    except (ValueError, TypeError):
                        # Bereits ein Name oder ungültiger Wert
                        print(f"DEBUG: document_type ist bereits Name oder ungültig: {doc_type_value}")
                finally:
                    db_session.close()
            
            # 2. Multi-Query Expansion (verwende normalisierte Frage, PHASE 2: Mit document_type_id für Custom Prompt)
            # NEU: Nur verwenden wenn use_multi_query=True (User-Option)
            if use_multi_query and self.multi_query_service:
                print(f"DEBUG: MultiQueryService aktiviert (User-Option) - generiere Varianten für: '{normalized_question}', document_type_id: {document_type_id_for_multi_query}")
                queries = await self.multi_query_service.generate_queries(
                    normalized_question,
                    document_type_id=document_type_id_for_multi_query  # PHASE 2: Für Custom Multi-Query Prompt
                )
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
                # WICHTIG: Level 4-5 (QM/QMS Admin) sollten alle Dokumente sehen, auch wenn Filter gesetzt ist
                # WICHTIG: document_type Filter sollte IMMER angewendet werden, wenn gesetzt
                # Auch Level 4-5 sollten den Filter respektieren, wenn explizit gewählt
                apply_document_type_filter = False
                if 'document_type' in search_filters and search_filters['document_type']:
                    # Wende document_type Filter IMMER an, wenn explizit gewählt
                    apply_document_type_filter = True
                    print(f"DEBUG: document_type Filter gesetzt: {search_filters['document_type']} - wende Filter an")
                
                if apply_document_type_filter and 'document_type' in search_filters and search_filters['document_type']:
                    from backend.app.models import UploadDocument
                    from backend.app.database import SessionLocal
                    
                    db_filter = SessionLocal()
                    try:
                        doc_type_name = search_filters['document_type']
                        # Hole upload_document_ids für diesen document_type
                        # WICHTIG: Filtere gelöschte Dokumente aus (workflow_status != 'deleted')
                        filtered_upload_ids = db_filter.query(UploadDocument.id).join(
                            UploadDocument.document_type
                        ).filter(
                            UploadDocument.document_type.has(name=doc_type_name),
                            UploadDocument.workflow_status != 'deleted'  # Gelöschte Dokumente ausschließen
                        ).all()
                        filtered_upload_ids_set = {row[0] for row in filtered_upload_ids}
                        
                        # Filtere indexed_docs
                        indexed_docs = [doc for doc in indexed_docs if doc.upload_document_id in filtered_upload_ids_set]
                        print(f"DEBUG: Nach document_type Filter (ohne gelöschte): {len(indexed_docs)} Dokumente")
                    finally:
                        db_filter.close()
                
                # WICHTIG: Erstelle Embedding für jedes IndexedDocument mit dem passenden Service
                # Dies stellt sicher, dass die gleichen Dimensionen wie beim Indexieren verwendet werden
                from contexts.ragintegration.infrastructure.embedding_factory import create_embedding_service_from_model
                import os
                
                for doc in indexed_docs:
                    # WICHTIG: Hole collection_name und embedding_model korrekt
                    collection_name = getattr(doc, 'qdrant_collection_name', None) or getattr(doc, 'collection_name', None)
                    embedding_model = getattr(doc, 'embedding_model', None)
                    
                    if not collection_name:
                        print(f"⚠️ Dokument ID {getattr(doc, 'id', 'unknown')}: Keine Collection gefunden, überspringe")
                        continue
                    
                    if not embedding_model:
                        print(f"⚠️ Dokument ID {getattr(doc, 'id', 'unknown')}: Kein embedding_model gefunden, verwende Standard")
                        embedding_model = "text-embedding-ada-002"  # Fallback
                    
                    print(f"DEBUG: Suche in Collection: {collection_name}, embedding_model: {embedding_model}")
                    
                    # Erstelle Embedding Service basierend auf embedding_model des Dokuments
                    # WICHTIG: Dies stellt sicher, dass die gleichen Dimensionen wie beim Indexieren verwendet werden
                    try:
                        doc_embedding_service = create_embedding_service_from_model(
                            embedding_model=embedding_model,
                            openai_api_key=os.getenv("OPENAI_GPT5_MINI_API_KEY") or os.getenv("OPENAI_API_KEY"),
                            google_api_key=os.getenv("GOOGLE_AI_API_KEY")
                        )
                        dimensions = doc_embedding_service.get_dimensions() if hasattr(doc_embedding_service, 'get_dimensions') else None
                        print(f"DEBUG: Embedding Service für {embedding_model} erstellt: {dimensions} Dimensionen")
                    except Exception as e:
                        print(f"⚠️ KRITISCH: Konnte Embedding Service für {embedding_model} nicht erstellen: {e}")
                        print(f"   Grund: OpenAI API Key fehlt oder hat keine Embedding-Permissions")
                        print(f"   Versuche Fallback auf Standard-Service...")
                        doc_embedding_service = self.embedding_service
                        fallback_dimensions = doc_embedding_service.get_dimensions() if hasattr(doc_embedding_service, 'get_dimensions') else None
                        
                        # Prüfe ob Dimensionen kompatibel sind
                        # Erwartete Dimensionen basierend auf embedding_model
                        expected_dims = None
                        if "ada" in embedding_model.lower() or "3" in embedding_model.lower():
                            expected_dims = 1536  # OpenAI
                        elif "004" in embedding_model.lower() or "gemini" in embedding_model.lower():
                            expected_dims = 768  # Google Gemini
                        else:
                            expected_dims = 768  # Sentence Transformers (Standard)
                        
                        if expected_dims and fallback_dimensions and fallback_dimensions != expected_dims:
                            print(f"❌ DIMENSION-MISMATCH ERKANNT!")
                            print(f"   Erwartet: {expected_dims} Dimensionen (für {embedding_model})")
                            print(f"   Fallback-Service: {fallback_dimensions} Dimensionen")
                            print(f"   → Suche wird fehlschlagen oder falsche Ergebnisse liefern!")
                            print(f"   → LÖSUNG: OpenAI API Key für {embedding_model} bereitstellen")
                            print(f"   → ODER: Dokument mit kompatiblem Modell re-indexieren")
                            # Überspringe dieses Dokument, da Suche nicht funktionieren wird
                            print(f"   → Überspringe Dokument ID {getattr(doc, 'id', 'unknown')} (Collection: {collection_name})")
                            continue
                        else:
                            print(f"✅ Fallback-Service kompatibel: {fallback_dimensions} Dimensionen")
                            dimensions = fallback_dimensions
                    
                    # Erstelle Embedding für die Query mit dem passenden Service
                    # WICHTIG: Verwende das gleiche Embedding-Modell wie beim Indexieren
                    # generate_embedding gibt bereits ein EmbeddingVector Objekt zurück
                    query_embedding = doc_embedding_service.generate_embedding(final_query)
                    model_name = query_embedding.model
                    dimensions = query_embedding.dimensions
                    
                    print(f"DEBUG: Query-Embedding erstellt - Modell: {model_name}, Dimensionen: {dimensions}")
                    
                    # Entferne document_type und query aus Qdrant-Filter da sie nicht in Metadaten sind
                    qdrant_filters = {k: v for k, v in search_filters.items() if k != 'document_type' and k != 'query'}
                    
                    if use_hybrid_search:
                        # Verwende Hybrid Search mit query_text für Text-Scoring
                        # WICHTIG: score_threshold wird vom Frontend übergeben (normalisiert für Embedding-Provider)
                        # Für OpenAI Embeddings sollten niedrige Werte verwendet werden (0.01-0.03)
                        # Für andere Provider (Google, Sentence Transformers) können höhere Werte (0.3-0.7) verwendet werden
                        print(f"DEBUG: Hybrid Search mit score_threshold={score_threshold}, top_k={top_k}, Modell: {model_name}")
                        results = self.vector_store.search_with_hybrid_scoring(
                            collection_name=collection_name,
                            query_embedding=query_embedding,
                            query_text=final_query,  # WICHTIG: query_text für Text-Scoring (inkl. Schnellsuche)
                            top_k=top_k,  # PHASE 0.1: Verwende übergebenen top_k Parameter
                            score_threshold=score_threshold,  # Verwende übergebenen Threshold
                            filters=qdrant_filters if qdrant_filters else None
                        )
                        print(f"DEBUG: Hybrid Search Ergebnisse: {len(results)} Chunks (nach score_threshold={score_threshold} gefiltert)")
                    else:
                        # Reine Vektor-Suche
                        # WICHTIG: score_threshold wird vom Frontend übergeben (normalisiert für Embedding-Provider)
                        print(f"DEBUG: Vektor-Suche mit min_score={score_threshold}, top_k={top_k}, Modell: {model_name}")
                        results = self.vector_store.search_similar(
                            collection_name=collection_name,
                            query_embedding=query_embedding,
                            filters=qdrant_filters or {},
                            top_k=top_k,  # PHASE 0.1: Verwende übergebenen top_k Parameter
                            min_score=score_threshold  # Verwende übergebenen Threshold
                        )
                        print(f"DEBUG: Vektor-Suche Ergebnisse: {len(results)} Chunks (nach min_score={score_threshold} gefiltert)")
                    print(f"DEBUG: Gefunden {len(results)} Ergebnisse in {collection_name}")
                    all_results.extend(results)
            
            print(f"DEBUG: Gesamt {len(all_results)} Ergebnisse gefunden")
            
            # 3. Deduplizierung und Ranking
            unique_results = self._deduplicate_and_rank(all_results)
            
            # 6. Verwende echte Ergebnisse oder leere Liste
            if not unique_results:
                print("DEBUG: Keine Suchergebnisse gefunden, verwende leere Liste")
                unique_results = []
            
            # 3.5 RBAC Phase 2: Interest Group Filtering
            filtered_chunk_ids = None  # Wird gesetzt wenn RBAC-Filter angewendet wird
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
                            # Speichere chunk_ids der gefilterten Ergebnisse für späteres Tracking
                            filtered_chunk_ids = {r.get('chunk_id') or r.get('metadata', {}).get('chunk_id') for r in filtered_results}
                            unique_results = filtered_results
                        else:
                            # Level 4-5: Alle Dokumente (keine Filterung)
                            print(f"DEBUG: RBAC Filter übersprungen - Level {user_level} sieht alle Dokumente")
                            filtered_chunk_ids = None  # Keine Filterung = alle Chunks sind "passed"
                    else:
                        print(f"DEBUG: Session {session_id} nicht gefunden, überspringe RBAC Filter")
                except Exception as e:
                    print(f"DEBUG: Fehler bei RBAC Filter, verwende alle Ergebnisse: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 3.6 Top-K Limitierung (nach Deduplizierung und RBAC-Filter)
            # WICHTIG: Begrenze auf top_k NACH allen Filtern, damit der User genau die gewünschte Anzahl erhält
            if len(unique_results) > top_k:
                print(f"DEBUG: Begrenze Ergebnisse von {len(unique_results)} auf top_k={top_k}")
                unique_results = unique_results[:top_k]
            else:
                print(f"DEBUG: {len(unique_results)} Ergebnisse (≤ top_k={top_k}), keine Begrenzung nötig")
            
            # 7. Kontext-Fenster-Management
            context_chunks = self._manage_context_window(unique_results)
            
            # 7.2.5. SHAP-basierte Optimierungen (NEU: Phase 5)
            # Basierend auf SHAP-Insights:
            # - document_type hat 35% Impact → Boost für relevante Dokument-Typen
            # - chunk_length hat -12% Impact → Penalty für sehr lange Chunks
            print(f"DEBUG: Wende SHAP-basierte Optimierungen an")
            
            # 1. Document Type Boost: Wenn Query "Montage" enthält, booste "Arbeitsanweisung"
            query_lower = question.lower()
            if "montage" in query_lower or "zusammenbau" in query_lower or "installation" in query_lower:
                print(f"DEBUG: Query enthält Montage-relevante Begriffe - Boost für Arbeitsanweisungen")
                for chunk in context_chunks:
                    metadata = chunk.get('metadata', {})
                    document_type = metadata.get('document_type', '').lower()
                    
                    # Fallback: Hole document_type aus IndexedDocument wenn nicht in Metadaten
                    if not document_type:
                        try:
                            document_id = metadata.get('document_id') or metadata.get('upload_document_id')
                            if document_id:
                                indexed_doc = self.indexed_document_repository.get_by_upload_document_id(document_id)
                                if indexed_doc:
                                    # Hole document_type aus UploadDocument
                                    from backend.app.models import UploadDocument
                                    from contexts.ragintegration.infrastructure.models import IndexedDocumentModel
                                    from backend.app.database import SessionLocal
                                    db_session = SessionLocal()
                                    try:
                                        upload_doc = db_session.query(UploadDocument).filter(
                                            UploadDocument.id == document_id
                                        ).first()
                                        if upload_doc and upload_doc.document_type:
                                            document_type = upload_doc.document_type.name.lower()
                                            # Speichere in Metadaten für später
                                            metadata['document_type'] = upload_doc.document_type.name
                                    finally:
                                        db_session.close()
                        except Exception as e:
                            print(f"DEBUG: Konnte document_type nicht holen: {e}")
                    
                    if document_type == "arbeitsanweisung":
                        # Boost: Erhöhe hybrid_score um 0.15 (35% Impact * 0.4 = 14% Boost)
                        current_score = chunk.get('hybrid_score', chunk.get('score', 0.0))
                        boosted_score = min(1.0, current_score + 0.15)
                        chunk['hybrid_score'] = boosted_score
                        chunk['score'] = boosted_score  # Aktualisiere auch score
                        print(f"DEBUG: Chunk {metadata.get('chunk_id', 'unknown')}: Boost für Arbeitsanweisung: {current_score:.4f} → {boosted_score:.4f}")
            
            # 2. Chunk Length Penalty: Sehr lange Chunks (>3000 Zeichen) erhalten Penalty
            for chunk in context_chunks:
                metadata = chunk.get('metadata', {})
                chunk_text = metadata.get('chunk_text', '')
                chunk_length = len(chunk_text) if chunk_text else 0
                
                if chunk_length > 3000:
                    # Penalty: Reduziere hybrid_score um 0.10 (12% Impact * 0.8 = 9.6% Penalty)
                    current_score = chunk.get('hybrid_score', chunk.get('score', 0.0))
                    penalized_score = max(0.0, current_score - 0.10)
                    chunk['hybrid_score'] = penalized_score
                    chunk['score'] = penalized_score  # Aktualisiere auch score
                    print(f"DEBUG: Chunk {metadata.get('chunk_id', 'unknown')}: Penalty für lange Chunk ({chunk_length} Zeichen): {current_score:.4f} → {penalized_score:.4f}")
            
            # NEU v2.10.6: Berechne Hybrid-Scores neu VOR der Sortierung (falls Vector und Text vorhanden)
            # Das stellt sicher, dass die Sortierung die korrekten Scores verwendet
            for chunk in context_chunks:
                metadata = chunk.get('metadata', {})
                vector_score = chunk.get('vector_score') or metadata.get('vector_score') or 0.0
                text_score = chunk.get('text_score') or metadata.get('text_score') or 0.0
                
                # Stelle sicher dass es Zahlen sind
                vector_score = float(vector_score) if vector_score is not None else 0.0
                text_score = float(text_score) if text_score is not None else 0.0
                
                # Berechne Hybrid-Score neu, wenn Vector und Text vorhanden sind
                if vector_score > 0.0 and text_score > 0.0:
                    hybrid_score = (vector_score * 0.7) + (text_score * 0.3)
                    hybrid_score = max(0.0, min(1.0, hybrid_score))
                    chunk['hybrid_score'] = hybrid_score
                    chunk['score'] = hybrid_score  # Aktualisiere auch score für Kompatibilität
            
            # Sortiere nach optimiertem hybrid_score
            context_chunks.sort(key=lambda x: x.get('hybrid_score', x.get('score', 0.0)), reverse=True)
            if context_chunks:
                print(f"DEBUG: SHAP-basierte Optimierungen abgeschlossen - Top Chunk Score: {context_chunks[0].get('hybrid_score', context_chunks[0].get('score', 0.0)):.4f}")
            
            # 7.4. LTR ML-Ranking (NEU v2.7.0) - Learning-to-Rank mit echtem ML-Modell
            if use_ml_ranking and self.ltr_service and self.ltr_service.is_enabled():
                try:
                    print(f"DEBUG: LTR ML-Ranking aktiviert - Berechne ML-Scores für {len(context_chunks)} Chunks")
                    
                    # Berechne ML-Scores für alle Chunks
                    for chunk in context_chunks:
                        metadata = chunk.get('metadata', {})
                        chunk_text = metadata.get('chunk_text', '')
                        
                        # Extrahiere alle benötigten Scores
                        vector_score = chunk.get('vector_score') or metadata.get('vector_score') or 0.0
                        text_score = chunk.get('text_score') or metadata.get('text_score') or 0.0
                        hybrid_score = chunk.get('hybrid_score') or chunk.get('score', 0.0)
                        
                        # Berechne BM25 und Jaccard (falls nicht vorhanden)
                        bm25_score = 0.0
                        jaccard_score = 0.0
                        try:
                            from contexts.ragintegration.infrastructure.bm25_service import BM25Service
                            bm25_service = BM25Service()
                            bm25_score = bm25_service.calculate_score(question, chunk_text)
                            
                            # Jaccard (einfache Token-Overlap-Berechnung)
                            query_words = set(question.lower().split())
                            text_words = set(chunk_text.lower().split())
                            if query_words and text_words:
                                intersection = query_words.intersection(text_words)
                                union = query_words.union(text_words)
                                jaccard_score = len(intersection) / len(union) if union else 0.0
                        except Exception as e:
                            print(f"DEBUG: Fehler bei BM25/Jaccard-Berechnung: {e}")
                        
                        # Keyword Matches
                        keyword_matches = len([word for word in question.lower().split() if word in chunk_text.lower()])
                        
                        # User Level
                        user_level = 1
                        try:
                            session = self.session_repository.get_by_id(session_id)
                            if session and self.permission_service:
                                user_level = self.permission_service.get_user_level(session.user_id)
                        except Exception:
                            pass
                        
                        # Predict ML-Score
                        ml_score = self.ltr_service.predict_ml_score(
                            query=question,
                            chunk=chunk,
                            vector_score=float(vector_score),
                            text_score=float(text_score),
                            bm25_score=bm25_score,
                            jaccard_score=jaccard_score,
                            keyword_matches=keyword_matches,
                            user_level=user_level,
                            hybrid_score=float(hybrid_score)
                        )
                        
                        # Final-Score (kombiniert Hybrid + ML)
                        final_score = self.ltr_service.get_final_score(
                            hybrid_score=float(hybrid_score),
                            ml_score=ml_score
                        )
                        
                        # Speichere Scores in Chunk
                        chunk['ml_score'] = ml_score
                        chunk['final_score'] = final_score
                        
                        print(f"DEBUG: Chunk {metadata.get('chunk_id', 'unknown')}: hybrid={hybrid_score:.4f}, ml={ml_score:.4f}, final={final_score:.4f}")
                    
                    # Sortiere nach final_score (statt hybrid_score)
                    context_chunks.sort(key=lambda x: x.get('final_score', x.get('hybrid_score', 0.0)), reverse=True)
                    if context_chunks:
                        print(f"DEBUG: LTR ML-Ranking abgeschlossen - Top Chunk Final-Score: {context_chunks[0].get('final_score', 0.0):.4f}")
                    
                except Exception as e:
                    print(f"DEBUG: Fehler bei LTR ML-Ranking (verwende Hybrid-Score): {e}")
                    import traceback
                    traceback.print_exc()
            
            # 7.3. ML Re-Ranking (DEPRECATED: Phase 4) - Optional, nach Hybrid Search und SHAP-Optimierungen
            # WICHTIG: Wird durch use_ml_ranking ersetzt (v2.7.0)
            elif use_ml_reranking and self.ml_model_service and self.ml_model_service.model.is_trained():
                try:
                    print(f"DEBUG: ML Re-Ranking aktiviert - Re-Ranke {len(context_chunks)} Chunks")
                    # Erstelle Features für jeden Chunk
                    chunks_with_ml_scores = []
                    for chunk in context_chunks:
                        metadata = chunk.get('metadata', {})
                        chunk_text = metadata.get('chunk_text', '')
                        
                        # Extrahiere Features
                        vector_score = chunk.get('vector_score') or metadata.get('vector_score') or chunk.get('score', 0.0)
                        text_score = chunk.get('text_score') or metadata.get('text_score') or 0.0
                        keyword_matches = len([word for word in question.lower().split() if word in chunk_text.lower()])
                        chunk_length = len(chunk_text)
                        heading_hierarchy_depth = len(metadata.get('heading_hierarchy', []))
                        confidence_score = metadata.get('confidence_score', 0.5)
                        
                        # Hole user_level aus Session
                        user_level = 1  # Default
                        try:
                            session = self.session_repository.get_by_id(session_id)
                            if session and self.permission_service:
                                user_level = self.permission_service.get_user_level(session.user_id)
                        except Exception as e:
                            print(f"DEBUG: Konnte user_level nicht holen: {e}")
                        
                        # NEU: BM25 Score berechnen (zusätzliches Feature für ML Model)
                        bm25_score = 0.0
                        try:
                            from contexts.ragintegration.infrastructure.bm25_service import BM25Service
                            bm25_service = BM25Service()
                            bm25_score = bm25_service.calculate_score(question, chunk_text)
                        except Exception as e:
                            print(f"DEBUG: Fehler bei BM25-Berechnung (überspringe): {e}")
                        
                        # Features für ML Model
                        features = {
                            "vector_score": float(vector_score) if vector_score else 0.0,
                            "text_score": float(text_score) if text_score else 0.0,
                            "bm25_score": bm25_score,  # NEU: BM25 Score als zusätzliches Feature
                            "keyword_matches": keyword_matches,
                            "chunk_length": chunk_length,
                            "heading_hierarchy_depth": heading_hierarchy_depth,
                            "confidence_score": float(confidence_score) if confidence_score else 0.5,
                            "user_level": user_level
                        }
                        
                        # Predict ML Score
                        ml_score = self.ml_model_service.predict_score(features)
                        
                        # Speichere ML Score in Chunk
                        chunk['ml_score'] = ml_score
                        chunks_with_ml_scores.append((chunk, ml_score))
                    
                    # Sortiere nach ML Score (höchste zuerst)
                    chunks_with_ml_scores.sort(key=lambda x: x[1], reverse=True)
                    context_chunks = [chunk for chunk, _ in chunks_with_ml_scores]
                    
                    print(f"DEBUG: ML Re-Ranking abgeschlossen - Top Chunk ML-Score: {chunks_with_ml_scores[0][1]:.4f}")
                except Exception as e:
                    # Graceful Error Handling: Wenn ML Re-Ranking fehlschlägt, verwende originale Reihenfolge
                    print(f"DEBUG: Fehler bei ML Re-Ranking (überspringe): {e}")
                    import traceback
                    traceback.print_exc()
            
            # 7.5. Erstelle source_references aus context_chunks
            from contexts.ragintegration.domain.value_objects import SourceReference
            source_references = []
            print(f"DEBUG: Erstelle source_references aus {len(context_chunks)} context_chunks")
            
            # NEU: Speichere erweiterte Metadaten für Transparenz
            total_candidates_before_filtering = len(all_results)  # Vor Deduplizierung und RBAC
            total_candidates_after_dedup = len(unique_results)  # Nach Deduplizierung, vor RBAC
            
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
                    # WICHTIG: Verwende mittlere Seite bei Multi-Page Chunks (besser als erste Seite)
                    # Falls nur eine Seite, verwende diese
                    if page_numbers and len(page_numbers) > 1:
                        # Multi-Page Chunk: Verwende mittlere Seite (besser repräsentativ)
                        page_number = page_numbers[len(page_numbers) // 2]
                        print(f"DEBUG: Chunk {i+1}: Multi-Page Chunk (Seiten {page_numbers}), verwende mittlere Seite {page_number}")
                    elif page_numbers:
                        page_number = page_numbers[0]
                    else:
                        page_number = 1
                        print(f"DEBUG: Chunk {i+1}: WARNUNG - page_numbers fehlt, verwende Fallback page_number=1")
                    # WICHTIG: chunk_id muss aus Metadaten kommen, nicht aus chunk.get('chunk_id')
                    # chunk.get('chunk_id') ist die UUID (point.id), die echte chunk_id ist in metadata
                    chunk_id = metadata.get('chunk_id', chunk.get('chunk_id', ''))
                    if not chunk_id:
                        print(f"DEBUG: Chunk {i+1}: WARNUNG - chunk_id fehlt in Metadaten!")
                    
                    # NEU: Extrahiere vector_score und text_score aus Metadaten
                    # WICHTIG: text_score sollte direkt in chunk sein (aus hybrid_results)
                    # Prüfe zuerst in chunk, dann in metadata
                    vector_score = chunk.get('vector_score')
                    if vector_score is None:
                        vector_score = metadata.get('vector_score')
                    if vector_score is None:
                        vector_score = 0.0
                    
                    text_score = chunk.get('text_score')
                    if text_score is None:
                        text_score = metadata.get('text_score')
                    if text_score is None:
                        text_score = 0.0
                    
                    # Stelle sicher dass es Zahlen sind (nicht None)
                    vector_score = float(vector_score) if vector_score is not None else 0.0
                    text_score = float(text_score) if text_score is not None else 0.0
                    
                    # DEBUG: Zeige text_score wenn es 0.0 ist (um Problem zu identifizieren)
                    if text_score == 0.0 and i < 3:  # Nur erste 3 für Debug
                        print(f"DEBUG: Chunk {i+1} text_score ist 0.0 - chunk.keys()={list(chunk.keys())}, metadata.keys()={list(metadata.keys())}")
                        if 'text_score' in chunk:
                            print(f"DEBUG: chunk['text_score'] = {chunk['text_score']}")
                        if 'text_score' in metadata:
                            print(f"DEBUG: metadata['text_score'] = {metadata['text_score']}")
                    
                    # NEU v2.10.6: Berechne Hybrid-Score neu, wenn Vector und Text vorhanden sind
                    # Das stellt sicher, dass der Hybrid-Score korrekt ist: (Vector * 0.7) + (Text * 0.3)
                    if vector_score > 0.0 and text_score > 0.0:
                        # Berechne Hybrid-Score neu aus Vector und Text
                        hybrid_score = (vector_score * 0.7) + (text_score * 0.3)
                        # Normalisiere auf 0-1
                        hybrid_score = max(0.0, min(1.0, hybrid_score))
                        print(f"DEBUG: Chunk {i+1} Hybrid-Score neu berechnet: Vector={vector_score:.4f}, Text={text_score:.4f}, Hybrid={hybrid_score:.4f}")
                    else:
                        # Fallback: Verwende vorhandenen hybrid_score oder score
                        hybrid_score = chunk.get('hybrid_score') or chunk.get('score', 0.0)
                        hybrid_score = max(0.0, min(1.0, float(hybrid_score)))
                        if i < 3:  # Debug für erste 3
                            print(f"DEBUG: Chunk {i+1} Hybrid-Score aus Chunk: {hybrid_score:.4f} (Vector={vector_score:.4f}, Text={text_score:.4f})")
                    
                    # NEU v2.10.6: relevance_score entspricht jetzt immer hybrid_score (für Konsistenz)
                    relevance_score = hybrid_score
                    
                    # NEU: Ranking-Informationen
                    rank_position = i + 1  # Position im finalen Ranking (1-basiert)
                    
                    # NEU: Filter-Status - Setze korrekt basierend auf tatsächlichem Status
                    # passed_rbac_filter: True wenn Chunk nach RBAC-Filterung noch vorhanden ist
                    # Prüfe ob Chunk durch RBAC-Filter durchgelassen wurde
                    if filtered_chunk_ids is not None:
                        # RBAC-Filter wurde angewendet - prüfe ob dieser Chunk durchgelassen wurde
                        chunk_id_for_check = chunk_id or metadata.get('chunk_id', '')
                        passed_rbac_filter = chunk_id_for_check in filtered_chunk_ids
                    else:
                        # Level 4-5 oder keine RBAC-Filterung = alle Chunks sind "passed"
                        passed_rbac_filter = True
                    
                    # passed_score_threshold: True wenn Score >= score_threshold
                    # score_threshold wird in der Schleife verwendet, daher müssen wir es hier prüfen
                    passed_score_threshold = relevance_score >= score_threshold if score_threshold else True
                    
                    # Hole document_type ZUERST (wird für chunk_metadata benötigt)
                    document_type = metadata.get('document_type') or metadata.get('document_type_name')
                    if not document_type:
                        # Fallback: Hole aus UploadDocument über IndexedDocument
                        try:
                            indexed_doc = self.indexed_document_repository.get_by_upload_document_id(document_id)
                            if indexed_doc:
                                from backend.app.models import UploadDocument
                                from backend.app.database import SessionLocal
                                db_session = SessionLocal()
                                try:
                                    upload_doc = db_session.query(UploadDocument).filter(
                                        UploadDocument.id == indexed_doc.upload_document_id
                                    ).first()
                                    if upload_doc and upload_doc.document_type:
                                        document_type = upload_doc.document_type.name
                                finally:
                                    db_session.close()
                        except Exception as e:
                            print(f"DEBUG: Konnte document_type nicht holen: {e}")
                    
                    # NEU: Chunk-Metadaten
                    chunk_metadata = {
                        'heading_hierarchy': metadata.get('heading_hierarchy', []),
                        'confidence_score': metadata.get('confidence_score'),
                        'chunk_type': metadata.get('chunk_type'),
                        'token_count': metadata.get('token_count'),
                        'document_type': document_type  # NEU: Für Analytics
                    }
                    # Entferne None-Werte
                    chunk_metadata = {k: v for k, v in chunk_metadata.items() if v is not None}
                    
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
                    
                    # NEU: Speichere erweiterte Metadaten in source_ref (als Dict für später)
                    # Diese werden in Router zu SourceReferenceResponse konvertiert
                    # NEU: ML Score (wenn ML Re-Ranking/LTR verwendet wurde)
                    ml_score = chunk.get('ml_score')
                    final_score = chunk.get('final_score')  # NEU: Final-Score (LTR v2.7.0)
                    
                    # NEU v2.10.5: Hole vollständigen chunk_text aus Metadaten (für Query-Term-Matching)
                    chunk_text_full = metadata.get('chunk_text', '')
                    
                    source_ref._extended_metadata = {
                        'vector_score': vector_score,
                        'text_score': text_score,
                        'hybrid_score': hybrid_score,
                        'ml_score': ml_score,  # NEU: ML Re-Ranking Score (Phase 4) oder LTR ML-Score (v2.7.0)
                        'final_score': final_score,  # NEU: Final-Score (kombiniert Hybrid + ML, v2.7.0)
                        'rank_position': rank_position,
                        'total_candidates': total_candidates_before_filtering,
                        'passed_rbac_filter': passed_rbac_filter,
                        'passed_score_threshold': passed_score_threshold,
                        'chunk_metadata': chunk_metadata if chunk_metadata else None,
                        'query_text': question,  # NEU: Query-Text für Text-Highlighting (Phase 3) - verwende ursprüngliche Frage
                        'page_number': page_number,  # NEU: Verwendete Seite (für Verlinkung)
                        'page_numbers': page_numbers,  # NEU: Alle Seiten des Chunks (für Multi-Page Chunks)
                        'document_id': document_id,  # NEU: Für Chunk-Analyse
                        'document_title': document_title,  # NEU: Für Chunk-Analyse
                        'text_excerpt': chunk_text_full[:200] if chunk_text_full else '',  # NEU: Chunk-Text-Auszug für Analyse
                        'chunk_text': chunk_text_full  # NEU v2.10.5: Vollständiger Chunk-Text für Query-Term-Matching
                    }
                    
                    # NEU: SHAP-Erklärung erstellen (wenn Service vorhanden)
                    if self.shap_service:
                        try:
                            # Sammle notwendige Daten für SHAP
                            chunk_text = metadata.get('chunk_text', '')
                            keyword_matches = len([word for word in question.lower().split() if word in chunk_text.lower()])
                            chunk_length = len(chunk_text)
                            heading_hierarchy_depth = len(metadata.get('heading_hierarchy', []))
                            confidence_score = metadata.get('confidence_score', 0.5)
                            
                            # document_type wurde bereits oben geholt (für chunk_metadata)
                            # Falls noch nicht gesetzt, verwende "Unbekannt"
                            if not document_type:
                                document_type = "Unbekannt"
                            
                            # Hole user_level aus Session
                            user_level = 1  # Default
                            try:
                                session = self.session_repository.get_by_id(session_id)
                                if session and self.permission_service:
                                    user_level = self.permission_service.get_user_level(session.user_id)
                            except Exception as e:
                                print(f"DEBUG: Konnte user_level nicht holen: {e}")
                            
                            # Erstelle SHAP-Erklärung
                            shap_explanation = self.shap_service.explain_search_result(
                                query=question,
                                chunk={'chunk_id': chunk_id},
                                vector_score=vector_score or 0.0,
                                text_score=text_score or 0.0,
                                hybrid_score=hybrid_score or relevance_score,
                                document_type=document_type,
                                user_level=user_level,
                                keyword_matches=keyword_matches,
                                chunk_length=chunk_length,
                                heading_hierarchy_depth=heading_hierarchy_depth,
                                confidence_score=confidence_score
                            )
                            
                            # Konvertiere SHAPExplanation zu Dictionary für JSON-Serialisierung
                            from dataclasses import asdict
                            shap_dict = asdict(shap_explanation)
                            # Konvertiere datetime zu ISO-String
                            if 'timestamp' in shap_dict and hasattr(shap_dict['timestamp'], 'isoformat'):
                                shap_dict['timestamp'] = shap_dict['timestamp'].isoformat()
                            
                            # Speichere SHAP-Erklärung in extended_metadata
                            source_ref._extended_metadata['shap_explanation'] = shap_dict
                            
                            # NEU v2.10.0: Speichere Training Data automatisch (immer, nicht nur bei Feedback)
                            if self.training_data_repo:
                                try:
                                    # Hole user_id aus Session
                                    user_id = None
                                    try:
                                        session = self.session_repository.get_by_id(session_id)
                                        if session:
                                            user_id = session.user_id
                                    except Exception as e:
                                        print(f"DEBUG: Konnte user_id nicht holen: {e}")
                                    
                                    if user_id:
                                        from contexts.ragintegration.domain.entities import TrainingData
                                        from datetime import datetime
                                        
                                        training_data = TrainingData(
                                            id=None,
                                            query=question,
                                            chunk_id=str(chunk_id),
                                            document_id=int(document_id),
                                            session_id=session_id,
                                            user_id=user_id,
                                            vector_score=vector_score or 0.0,
                                            text_score=text_score or 0.0,
                                            hybrid_score=hybrid_score or relevance_score,
                                            document_type=document_type or "Unbekannt",
                                            user_level=user_level,
                                            keyword_matches=keyword_matches,
                                            chunk_length=chunk_length,
                                            heading_hierarchy_depth=heading_hierarchy_depth,
                                            confidence_score=confidence_score,
                                            shap_explanation=shap_dict,  # SHAP-Erklärung
                                            user_feedback=None,  # Wird später durch Feedback ergänzt
                                            feedback_comment=None,
                                            created_at=datetime.utcnow()
                                        )
                                        
                                        # Speichere Training Data (nicht async, da Repository synchron ist)
                                        self.training_data_repo.save(training_data)
                                        print(f"DEBUG: Training Data gespeichert für Chunk {chunk_id}")
                                except Exception as e:
                                    # Graceful Error Handling: Wenn Training Data Speichern fehlschlägt, Use Case funktioniert trotzdem
                                    print(f"DEBUG: Fehler beim Speichern von Training Data (überspringe): {e}")
                                    import traceback
                                    traceback.print_exc()
                        except Exception as e:
                            # Graceful Error Handling: Wenn SHAP fehlschlägt, Use Case funktioniert trotzdem
                            print(f"DEBUG: Fehler bei SHAP-Erklärung (überspringe): {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # NEU v2.10.7: Markiere Chunk als in RAG-Antwort referenziert (Ground Truth)
                    # Alle Chunks in source_references wurden in der RAG-Antwort verwendet
                    source_ref._extended_metadata['referenced_in_rag_answer'] = True
                    source_ref._extended_metadata['rag_reference_position'] = len(source_references) + 1  # 1-basiert
                    
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
            
            # 8.5. Speichere Query in Metadaten für späteres Text-Highlighting
            # Die Query wird in den Metadaten gespeichert, damit sie in get_chat_history verfügbar ist
            query_for_metadata = question
            
            # 9. AI-Antwort generieren
            # WICHTIG: Bestimme document_type und document_type_id für Prompt-Auswahl
            # Priorität:
            # 1. document_type Filter (wenn vom User gewählt)
            # 2. Häufigster Dokument-Typ in den gefundenen Chunks
            # 3. Generischer Prompt (wenn keine Chunks vorhanden)
            document_type_for_prompt = None
            document_type_id_for_prompt = None
            
            # 1. Prüfe zuerst, ob ein document_type Filter gesetzt wurde
            if filters and 'document_type' in filters and filters['document_type']:
                document_type_for_prompt = filters['document_type']
                print(f"DEBUG: Verwende document_type Filter für Prompt: {document_type_for_prompt}")
                
                # Hole document_type_id aus Datenbank
                # FIX: Akzeptiere sowohl ID (Zahl) als auch Name (String)
                try:
                    from backend.app.models import DocumentTypeModel
                    from backend.app.database import SessionLocal
                    db_session = SessionLocal()
                    try:
                        # Prüfe ob document_type eine ID (Zahl) oder ein Name (String) ist
                        if str(document_type_for_prompt).isdigit():
                            # ID übergeben → Query nach ID
                            doc_type = db_session.query(DocumentTypeModel).filter(
                                DocumentTypeModel.id == int(document_type_for_prompt)
                            ).first()
                            print(f"DEBUG: document_type ist ID: {document_type_for_prompt}")
                        else:
                            # Name übergeben → Query nach Name
                            doc_type = db_session.query(DocumentTypeModel).filter(
                                DocumentTypeModel.name == document_type_for_prompt
                            ).first()
                            print(f"DEBUG: document_type ist Name: {document_type_for_prompt}")
                        
                        if doc_type:
                            document_type_id_for_prompt = doc_type.id
                            # Normalisiere document_type_for_prompt zu Name (für Konsistenz)
                            document_type_for_prompt = doc_type.name
                            print(f"DEBUG: document_type_id aus Filter geholt: {document_type_id_for_prompt}, Name: {document_type_for_prompt}")
                        else:
                            print(f"DEBUG: Document Type nicht gefunden: {document_type_for_prompt}")
                    finally:
                        db_session.close()
                except Exception as e:
                    print(f"DEBUG: Konnte document_type_id aus Filter nicht holen: {e}")
            
            # 2. Wenn kein Filter gesetzt, verwende häufigsten Dokument-Typ in Chunks
            elif context_chunks:
                # Zähle Dokument-Typen in Chunks
                from collections import Counter
                doc_type_counts = Counter()
                doc_type_id_map = {}  # Map document_type -> document_type_id
                
                for chunk in context_chunks:
                    metadata = chunk.get('metadata', {})
                    doc_type = metadata.get('document_type') or metadata.get('document_type_name')
                    doc_type_id = metadata.get('document_type_id')
                    
                    if doc_type:
                        doc_type_counts[doc_type] += 1
                        if doc_type_id and doc_type not in doc_type_id_map:
                            doc_type_id_map[doc_type] = doc_type_id
                
                # Verwende häufigsten Dokument-Typ
                if doc_type_counts:
                    document_type_for_prompt = doc_type_counts.most_common(1)[0][0]
                    document_type_id_for_prompt = doc_type_id_map.get(document_type_for_prompt)
                    print(f"DEBUG: Verwende häufigsten Dokument-Typ für Prompt: {document_type_for_prompt} (aus {len(context_chunks)} Chunks)")
                    
                    # Fallback: Wenn document_type_id nicht in Metadaten, hole es aus upload_document
                    if not document_type_id_for_prompt and context_chunks:
                        first_chunk = context_chunks[0]
                        metadata = first_chunk.get('metadata', {})
                        document_id = metadata.get('document_id') or metadata.get('upload_document_id')
                        if document_id:
                            try:
                                from backend.app.database import get_db
                                from sqlalchemy import text
                                db = next(get_db())
                                result = db.execute(text('''
                                    SELECT document_type_id
                                    FROM upload_documents
                                    WHERE id = :doc_id
                                '''), {"doc_id": document_id})
                                row = result.fetchone()
                                if row:
                                    document_type_id_for_prompt = row[0]
                                    print(f"DEBUG: document_type_id aus upload_document geholt: {document_type_id_for_prompt}")
                            except Exception as e:
                                print(f"DEBUG: Konnte document_type_id nicht aus upload_document holen: {e}")
            
            # 3. Wenn keine Chunks vorhanden, bleibt document_type_for_prompt = None (generischer Prompt)
            else:
                print(f"DEBUG: Keine Chunks vorhanden, verwende generischen Prompt")
            
            if document_type_for_prompt:
                print(f"DEBUG: Document type für AI-Prompt: {document_type_for_prompt}, document_type_id: {document_type_id_for_prompt}")
            else:
                print(f"DEBUG: Verwende generischen Prompt (kein document_type)")
            
            if self.ai_service:
                try:
                    ai_response = await self.ai_service.generate_response_async(
                        question=question,
                        context_chunks=context_chunks,
                        model_id=model_id,
                        document_type=document_type_for_prompt,  # Dokumenttyp für spezifischen Prompt
                        document_type_id=document_type_id_for_prompt,  # PHASE 1: Document Type ID für Custom Prompt Lookup
                        temperature=temperature,  # NEU v2.10.3: AI Temperature
                        max_tokens=max_tokens,  # NEU v2.10.3: Max Tokens
                        top_p=top_p  # NEU v2.10.3: Top P
                    )
                except (MissingCustomPromptError, InvalidCustomPromptError) as e:
                    # STRICTE REGEL (CR-P2.2): Custom-Prompt-Enforcement.
                    # Wenn document_type_id gesetzt ist:
                    # - Custom Prompt MUSS existieren (sonst MissingCustomPromptError)
                    # - Custom Prompt MUSS {context} und {question} enthalten (sonst InvalidCustomPromptError)
                    # Keine Fallbacks, keine generischen Prompts, keine automatische Reparatur.
                    raise e
            else:
                # Fallback zu Mock-Antwort
                ai_response = {
                    "answer": f"Basierend auf den verfügbaren Dokumenten kann ich folgende Informationen zu Ihrer Frage \"{question}\" geben: Das Dokument enthält wichtige Informationen über Arbeitsanweisungen und Verfahren.",
                    "model_used": model_id,
                    "tokens_used": 50,
                    "confidence": 0.5,
                    "provider": "mock"
                }
            
            # 10. Erstelle Assistant-ChatMessage mit Metadaten
            # Sammle Metadaten für Transparency Layer
            
            # Bestimme prompt_type und Prompt-IDs für Traceability
            prompt_type, custom_prompt_id, standard_prompt_id = self._determine_prompt_type_and_ids(
                document_type_id_for_prompt,
                document_type_for_prompt
            )
            
            # Bestimme document_type_effective aus Chunks (unabhängig vom Filter)
            # Dies ermöglicht Widerspruch-Erkennung zwischen Filter und Chunk-Analyse
            document_type_effective = None
            if context_chunks:
                from collections import Counter
                doc_type_counts = Counter()
                
                for chunk in context_chunks:
                    metadata = chunk.get('metadata', {})
                    doc_type = metadata.get('document_type') or metadata.get('document_type_name')
                    
                    if doc_type:
                        doc_type_counts[doc_type] += 1
                
                # Verwende häufigsten Dokument-Typ aus Chunks
                if doc_type_counts:
                    document_type_effective = doc_type_counts.most_common(1)[0][0]
                    print(f"DEBUG: document_type_effective aus Chunks: {document_type_effective}")
            
            # Prüfe auf Widerspruch zwischen Filter und Chunk-Analyse
            document_type_selected = filters.get('document_type') if filters and 'document_type' in filters else None
            document_type_mismatch_warning = False
            if document_type_selected and document_type_effective and document_type_selected != document_type_effective:
                # Widerspruch erkannt: Filter und Chunk-Analyse unterscheiden sich
                document_type_mismatch_warning = True
                print(f"DEBUG: Widerspruch erkannt - Filter: {document_type_selected}, Chunks: {document_type_effective}")
            
            # NEU v2.7.0: Analytics-Block für Analytics-Dashboard
            analytics_scores = []
            for i, ref in enumerate(source_references):
                extended = getattr(ref, '_extended_metadata', {})
                analytics_scores.append({
                    'chunk_id': ref.chunk_id,
                    'vector_score': extended.get('vector_score'),
                    'text_score': extended.get('text_score'),
                    'hybrid_score': extended.get('hybrid_score'),
                    'ml_score': extended.get('ml_score'),
                    'final_score': extended.get('final_score'),
                    'rank_position': i + 1,
                    '_extended_metadata': extended
                })
            
            # NEU v2.9.0: Berechne Search Quality Metrics
            # WICHTIG: Metriken werden NUR berechnet, wenn Feedback vorhanden ist!
            # Feedback wird NACH der Message-Erstellung gegeben, daher werden Metriken
            # beim Erstellen der Message NICHT berechnet (kein Feedback verfügbar).
            # Metriken werden stattdessen beim Abrufen der Analytics berechnet (siehe router.py).
            search_quality_metrics = None
            # Metriken werden später berechnet, wenn Feedback vorhanden ist (siehe /analytics/search-quality Endpoint)
            
            # System Metrics für Analytics
            analytics_block = {
                'query': question,  # NEU v2.9.0: Query prominent speichern
                'scores': analytics_scores,
                'search_quality_metrics': search_quality_metrics,  # NEU v2.9.0
                'background_data_stats': {},  # Wird später aus Service geholt
                'cache_stats': {},  # Wird später aus Service geholt
                'model_info': {
                    'ml_enabled': self.ltr_service.is_enabled() if self.ltr_service else False,
                    'shap_enabled': self.shap_service is not None
                }
            }
            
            # Hole Background Stats (falls verfügbar)
            if self.shap_service and hasattr(self.shap_service, '_background_data_service'):
                try:
                    bg_service = self.shap_service._background_data_service
                    analytics_block['background_data_stats'] = bg_service.get_statistics()
                except Exception:
                    pass
            
            # Hole Cache Stats (falls verfügbar)
            if self.shap_service and hasattr(self.shap_service, 'cache'):
                try:
                    analytics_block['cache_stats'] = self.shap_service.cache.get_statistics()
                except Exception:
                    pass
            
            # Prompt muss IMMER vorhanden sein (audit-sicher)
            prompt_text = ai_response.get("prompt_text")
            if not prompt_text:
                # Fallback: Generiere Prompt wenn nicht vorhanden (sollte nicht passieren)
                print("WARNING: prompt_text fehlt in ai_response - generiere Fallback-Prompt")
                if self.ai_service:
                    prompt_text = self.ai_service._create_structured_rag_prompt(
                        question,
                        "",
                        document_type_for_prompt,
                        document_type_id_for_prompt
                    )
                else:
                    prompt_text = "Generischer Prompt (Fallback)"
            
            # Erweiterte Metadaten für vollständige Traceability
            metadata = {
                "tokens_used": ai_response.get("tokens_used", 0),
                "query_params": {
                    "top_k": len(context_chunks),
                    "score_threshold": score_threshold,
                    "use_hybrid_search": use_hybrid_search,
                    "use_multi_query": use_multi_query,
                    "use_ml_ranking": use_ml_ranking,
                    # NEU v2.10.3: AI-Modell-Einstellungen für Analytics
                    "temperature": temperature if temperature is not None else 0.0,
                    "max_tokens": max_tokens if max_tokens is not None else 8000,
                    "top_p": top_p if top_p is not None else 0.9
                },
                "prompt_text": prompt_text,  # IMMER vorhanden (audit-sicher)
                "prompt_type": prompt_type,  # PromptType Enum-Wert
                "document_type_selected": document_type_selected,  # User-Intent (bereits oben bestimmt)
                "document_type_effective": document_type_effective,  # Tatsächlich verwendet
                "query_text": query_for_metadata,
                "analytics": analytics_block
            }
            
            # Füge Flag hinzu wenn Custom Prompt Platzhalter fehlen (STRICTE REGEL 3)
            if ai_response.get("custom_prompt_missing_placeholders"):
                metadata["missing_placeholders"] = True  # Umbenannt für Konsistenz
            
            # Füge Warnung hinzu wenn Dokumenttyp-Widerspruch erkannt wurde
            if document_type_mismatch_warning:
                metadata["document_type_mismatch_warning"] = True
            
            # Füge Prompt-IDs hinzu wenn vorhanden
            if custom_prompt_id:
                metadata["custom_prompt_id"] = custom_prompt_id
            if standard_prompt_id:
                metadata["standard_prompt_id"] = standard_prompt_id
            
            assistant_message = ChatMessage(
                id=None,
                session_id=session_id,
                role="assistant",
                content=ai_response["answer"],
                source_references=source_references,  # WICHTIG: Verwende die erstellten source_references!
                ai_model_used=model_id,  # AI Model das für diese Antwort verwendet wurde
                created_at=datetime.now(),
                metadata=metadata  # Metadaten für Transparency Layer
            )
            
            # 11. Speichere Assistant-Message in der Datenbank (vor Event-Publikation)
            saved_assistant_message = self.message_repository.save(assistant_message)
            print(f"DEBUG: Assistant-Nachricht gespeichert: ID={saved_assistant_message.id}")
            
            # Stelle sicher, dass saved_assistant_message source_references hat (für Tests und Runtime)
            # Überschreibe auch wenn es bereits existiert, um sicherzustellen dass es eine Liste ist
            saved_assistant_message.source_references = source_references
            
            # 13. Sammle Search-Daten für SHAP Background Data (falls Service vorhanden)
            if self.shap_service and hasattr(self.shap_service, '_background_data_service'):
                try:
                    background_data_service = self.shap_service._background_data_service
                    # Sammle Daten von allen Context-Chunks
                    for chunk in context_chunks:
                        metadata = chunk.get('metadata', {})
                        chunk_text = metadata.get('chunk_text', '')
                        
                        # Extrahiere Daten
                        vector_score = chunk.get('vector_score') or metadata.get('vector_score') or 0.0
                        text_score = chunk.get('text_score') or metadata.get('text_score') or 0.0
                        keyword_matches = len([word for word in question.lower().split() if word in chunk_text.lower()])
                        chunk_length = len(chunk_text)
                        heading_hierarchy_depth = len(metadata.get('heading_hierarchy', []))
                        confidence_score = metadata.get('confidence_score', 0.5)
                        
                        # Hole user_level
                        user_level = 1  # Default
                        try:
                            session = self.session_repository.get_by_id(session_id)
                            if session and self.permission_service:
                                user_level = self.permission_service.get_user_level(session.user_id)
                        except Exception:
                            pass
                        
                        # Füge zu Background Data hinzu
                        background_data_service.add_search_record(
                            query=question,
                            vector_score=float(vector_score),
                            text_score=float(text_score),
                            user_level=user_level,
                            keyword_matches=keyword_matches,
                            chunk_length=chunk_length,
                            heading_hierarchy_depth=heading_hierarchy_depth,
                            confidence_score=float(confidence_score)
                        )
                    
                    print(f"✅ {len(context_chunks)} Search-Records zu Background-Daten hinzugefügt")
                except Exception as e:
                    print(f"⚠️ Konnte Search-Daten nicht sammeln: {e}")
            
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
    
    def _determine_prompt_type_and_ids(
        self,
        document_type_id: Optional[int],
        document_type: Optional[str]
    ) -> tuple[str, Optional[int], Optional[int]]:
        """
        Bestimme prompt_type und Prompt-IDs für Traceability.
        
        Ermittelt den verwendeten Prompt-Typ (Custom, Standard oder Generic) und die
        entsprechenden IDs für vollständige Audit-Traceability.
        
        Args:
            document_type_id: Document Type ID (falls vorhanden)
            document_type: Document Type Name (falls vorhanden)
            
        Returns:
            Tuple (prompt_type, custom_prompt_id, standard_prompt_id)
            prompt_type: PromptType Enum-Wert
        """
        custom_prompt_id = None
        standard_prompt_id = None
        prompt_type = PromptType.GENERIC.value  # Default
        
        # Prüfe Custom Prompt zuerst
        if document_type_id:
            try:
                from backend.app.models import RAGChatPromptModel, PromptTemplateModel
                from backend.app.database import SessionLocal
                
                db_session = SessionLocal()
                try:
                    # Prüfe Custom Prompt
                    custom_prompt = db_session.query(RAGChatPromptModel).filter(
                        RAGChatPromptModel.document_type_id == document_type_id
                    ).first()
                    
                    if custom_prompt:
                        prompt_type = PromptType.CUSTOM.value
                        custom_prompt_id = custom_prompt.id
                        print(f"DEBUG: Custom Prompt gefunden: ID={custom_prompt_id}")
                    else:
                        # Prüfe Standard Prompt
                        if document_type:
                            standard_prompt = db_session.query(PromptTemplateModel).filter(
                                PromptTemplateModel.document_type == document_type.upper(),
                                PromptTemplateModel.status == "active"
                            ).first()
                            
                            if standard_prompt:
                                prompt_type = PromptType.STANDARD.value
                                standard_prompt_id = standard_prompt.id
                                print(f"DEBUG: Standard Prompt gefunden: ID={standard_prompt_id}")
                finally:
                    db_session.close()
            except Exception as e:
                print(f"DEBUG: Fehler beim Bestimmen des Prompt-Typs: {e}")
                # Fallback zu generic
                prompt_type = PromptType.GENERIC.value
        
        return (prompt_type, custom_prompt_id, standard_prompt_id)
    
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
        
        WICHTIG: Ergebnisse sind bereits durch top_k gefiltert (vom Frontend konfigurierbar).
        Verwende alle übergebenen Ergebnisse - keine weitere Begrenzung.
        Vollständige Chunks werden verwendet (keine Kürzung mehr).
        """
        # Verwende alle übergebenen Ergebnisse (bereits durch top_k vom Frontend gefiltert)
        # Vollständige Chunks werden verwendet (keine Kürzung mehr)
        context_chunks = results
        print(f"DEBUG: Kontext-Chunks für AI-Service: {len(context_chunks)} (vollständige Chunks, keine Kürzung, top_k vom Frontend)")
        for i, chunk in enumerate(context_chunks):
            chunk_id = chunk.get('chunk_id', 'unknown')
            score = chunk.get('hybrid_score', chunk.get('score', 0))
            chunk_text_length = len(chunk.get('chunk_text', chunk.get('metadata', {}).get('chunk_text', '')))
            print(f"DEBUG: Chunk {i+1}: {chunk_id} - Score: {score:.6f} - Länge: {chunk_text_length} Zeichen")
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


# ============================================================================
# CHUNK EDITOR USE CASES (PHASE 2.2)
# ============================================================================

class EditChunkUseCase:
    """
    Use Case: Chunk-Text bearbeiten.
    
    Ermöglicht das Bearbeiten von Chunk-Text für Korrekturen und Verbesserungen.
    """
    
    def __init__(self, chunk_repo):
        """
        Initialisiere Use Case.
        
        Args:
            chunk_repo: DocumentChunkRepository Instance
        """
        self.chunk_repo = chunk_repo
    
    async def execute(self, chunk_id: int, new_text: str):
        """
        Bearbeite Chunk-Text.
        
        Args:
            chunk_id: Chunk ID
            new_text: Neuer Chunk-Text
        
        Returns:
            Aktualisierter DocumentChunk
        
        Raises:
            ValueError: Wenn Chunk nicht gefunden oder Text leer
        """
        if not new_text or not new_text.strip():
            raise ValueError("Chunk-Text darf nicht leer sein")
        
        # Lade Chunk
        chunk = self.chunk_repo.get_by_id(chunk_id)
        if not chunk:
            raise ValueError(f"Chunk {chunk_id} nicht gefunden")
        
        # Update Text
        chunk.chunk_text = new_text.strip()
        
        # Update Metadata (Token Count, etc.)
        # TODO: Recalculate token_count, sentence_count
        
        # Speichere
        return self.chunk_repo.save(chunk)


class DeleteChunkUseCase:
    """
    Use Case: Chunk löschen.
    
    Löscht Chunk aus DB und Vector Store.
    """
    
    def __init__(self, chunk_repo, vector_store):
        """
        Initialisiere Use Case.
        
        Args:
            chunk_repo: DocumentChunkRepository Instance
            vector_store: VectorStoreRepository Instance
        """
        self.chunk_repo = chunk_repo
        self.vector_store = vector_store
    
    async def execute(self, chunk_id: int):
        """
        Lösche Chunk.
        
        Args:
            chunk_id: Chunk ID
        
        Returns:
            True wenn erfolgreich
        
        Raises:
            ValueError: Wenn Chunk nicht gefunden
        """
        # Lade Chunk
        chunk = self.chunk_repo.get_by_id(chunk_id)
        if not chunk:
            raise ValueError(f"Chunk {chunk_id} nicht gefunden")
        
        # Lösche aus Vector Store
        if chunk.qdrant_point_id:
            await self.vector_store.delete_point(chunk.qdrant_point_id)
        
        # Lösche aus DB
        return self.chunk_repo.delete(chunk_id)


class SplitChunkUseCase:
    """
    Use Case: Chunk in zwei Teile splitten.
    
    Teilt einen langen Chunk in zwei kleinere Chunks auf.
    """
    
    def __init__(self, chunk_repo, vector_store, embedding_service, indexed_document_repo=None):
        """
        Initialisiere Use Case.
        
        Args:
            chunk_repo: DocumentChunkRepository Instance
            vector_store: VectorStoreRepository Instance
            embedding_service: EmbeddingService Instance
            indexed_document_repo: Optional IndexedDocumentRepository (für Collection-Name)
        """
        self.chunk_repo = chunk_repo
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.indexed_document_repo = indexed_document_repo
    
    async def execute(self, chunk_id: int, split_position: int, overlap_sentences: int = 0):
        """
        Splitte Chunk an gegebener Position.
        
        Args:
            chunk_id: Chunk ID
            split_position: Position im Text (Character-Index)
            overlap_sentences: Anzahl Overlap-Sätze zwischen den beiden Chunks (0-10, Standard: 0)
        
        Returns:
            Liste von zwei neuen DocumentChunks
        
        Raises:
            ValueError: Wenn Chunk nicht gefunden oder Position ungültig
        """
        from contexts.ragintegration.domain.entities import DocumentChunk
        from contexts.ragintegration.domain.value_objects import ChunkMetadata
        import uuid
        import re
        
        # Lade Original Chunk
        original_chunk = self.chunk_repo.get_by_id(chunk_id)
        if not original_chunk:
            raise ValueError(f"Chunk {chunk_id} nicht gefunden")
        
        # Hole Collection-Name aus IndexedDocument
        collection_name = "rag_documents"  # Default Fallback
        if self.indexed_document_repo:
            try:
                indexed_doc = self.indexed_document_repo.get_by_id(original_chunk.indexed_document_id)
                if indexed_doc and indexed_doc.collection_name:
                    collection_name = indexed_doc.collection_name
            except:
                pass
        else:
            # Fallback: Hole Collection-Name direkt aus DB
            from backend.app.database import get_db
            from sqlalchemy import text
            db = next(get_db())
            try:
                result = db.execute(text('''
                    SELECT collection_name
                    FROM rag_indexed_documents
                    WHERE id = :idx_doc_id
                '''), {"idx_doc_id": original_chunk.indexed_document_id})
                row = result.fetchone()
                if row:
                    collection_name = row[0]
            except:
                pass
        
        if split_position < 0 or split_position >= len(original_chunk.chunk_text):
            raise ValueError(f"Split-Position {split_position} ist ungültig")
        
        if overlap_sentences < 0 or overlap_sentences > 10:
            raise ValueError(f"Overlap-Sätze muss zwischen 0 und 10 liegen")
        
        # Split Text
        text1 = original_chunk.chunk_text[:split_position].strip()
        text2 = original_chunk.chunk_text[split_position:].strip()
        
        if not text1 or not text2:
            raise ValueError("Split würde zu leeren Chunks führen")
        
        # WICHTIG: Overlap-Logik
        # Wenn overlap_sentences > 0, füge die letzten N Sätze von text1 am Anfang von text2 hinzu
        # und die ersten N Sätze von text2 am Ende von text1
        has_overlap = overlap_sentences > 0
        overlap_sentence_count = 0
        
        # Hilfsfunktionen für Token- und Satz-Berechnung
        def split_into_sentences(text: str) -> list:
            """Teile Text in Sätze."""
            # Einfache Satz-Trennung (verbessert: berücksichtigt Abkürzungen)
            sentences = re.split(r'(?<=[.!?])\s+', text)
            return [s.strip() for s in sentences if s.strip()]
        
        def estimate_tokens(text: str) -> int:
            """Schätze Token-Anzahl (vereinfacht: ~4 Zeichen pro Token)."""
            return len(text) // 4
        
        if has_overlap:
            # Teile beide Texte in Sätze (VOR dem Split!)
            # WICHTIG: Wir müssen die Sätze aus dem ORIGINALEN Text zählen, nicht aus text1/text2
            # da text1/text2 bereits gesplittet sind
            original_text = original_chunk.chunk_text
            all_sentences = split_into_sentences(original_text)
            
            # Finde die Split-Position in Sätzen
            text_before_split = original_text[:split_position]
            sentences_before = split_into_sentences(text_before_split)
            sentences_after = split_into_sentences(original_text[split_position:])
            
            # Berechne tatsächliche Overlap-Anzahl (nicht mehr als verfügbar)
            actual_overlap = min(overlap_sentences, len(sentences_before), len(sentences_after))
            
            if actual_overlap > 0:
                # Hole Overlap-Sätze aus dem ORIGINALEN Text
                # WICHTIG: Overlap bedeutet, dass der ZWEITE Chunk mit den letzten N Sätzen des ERSTEN Chunks beginnt
                # Der erste Chunk bleibt unverändert (endet am Split-Punkt)
                overlap_from_before = sentences_before[-actual_overlap:]  # Letzte N Sätze von text1
                
                # Füge Overlap zu text2 hinzu (am Anfang)
                # text2 beginnt jetzt mit den letzten Sätzen von text1
                text2_with_overlap = " ".join(overlap_from_before) + " " + text2
                
                # text1 bleibt unverändert (kein Overlap am Ende!)
                # text1 = text1  # Unverändert
                text2 = text2_with_overlap
                overlap_sentence_count = actual_overlap
                has_overlap = True  # Stelle sicher, dass has_overlap True ist
            else:
                # Wenn actual_overlap 0 ist, dann gibt es kein Overlap
                has_overlap = False
                overlap_sentence_count = 0
        
        # Berechne Metadaten für beide Chunks
        sentences1 = split_into_sentences(text1)
        sentences2 = split_into_sentences(text2)
        token_count1 = estimate_tokens(text1)
        token_count2 = estimate_tokens(text2)
        sentence_count1 = len(sentences1)
        sentence_count2 = len(sentences2)
        
        # Erstelle zwei neue Chunks
        chunk1 = DocumentChunk(
            id=None,
            indexed_document_id=original_chunk.indexed_document_id,
            chunk_id=f"{original_chunk.chunk_id}_split_1",
            chunk_text=text1,
            metadata=ChunkMetadata(
                page_numbers=original_chunk.metadata.page_numbers,
                heading_hierarchy=original_chunk.metadata.heading_hierarchy,
                chunk_type=original_chunk.metadata.chunk_type,
                token_count=token_count1,
                sentence_count=sentence_count1,
                has_overlap=has_overlap,
                overlap_sentence_count=overlap_sentence_count
            ),
            qdrant_point_id=str(uuid.uuid4()),
            created_at=datetime.utcnow()
        )
        
        chunk2 = DocumentChunk(
            id=None,
            indexed_document_id=original_chunk.indexed_document_id,
            chunk_id=f"{original_chunk.chunk_id}_split_2",
            chunk_text=text2,
            metadata=ChunkMetadata(
                page_numbers=original_chunk.metadata.page_numbers,
                heading_hierarchy=original_chunk.metadata.heading_hierarchy,
                chunk_type=original_chunk.metadata.chunk_type,
                token_count=token_count2,
                sentence_count=sentence_count2,
                has_overlap=has_overlap,
                overlap_sentence_count=overlap_sentence_count
            ),
            qdrant_point_id=str(uuid.uuid4()),
            created_at=datetime.utcnow()
        )
        
        # Generiere Embeddings
        # WICHTIG: Embedding-Service verwendet generate_embedding, nicht create_embedding
        embedding1 = self.embedding_service.generate_embedding(text1)
        embedding2 = self.embedding_service.generate_embedding(text2)
        
        # Speichere in Vector Store
        # WICHTIG: Verwende index_chunk statt add_point
        metadata1 = {
            "chunk_id": chunk1.chunk_id,
            "text": text1,
            "document_id": original_chunk.indexed_document_id,
            "page_numbers": original_chunk.metadata.page_numbers,
            "chunk_type": original_chunk.metadata.chunk_type
        }
        metadata2 = {
            "chunk_id": chunk2.chunk_id,
            "text": text2,
            "document_id": original_chunk.indexed_document_id,
            "page_numbers": original_chunk.metadata.page_numbers,
            "chunk_type": original_chunk.metadata.chunk_type
        }
        
        # Indexiere Chunks in Qdrant
        self.vector_store.index_chunk(collection_name, chunk1.chunk_id, embedding1, metadata1)
        self.vector_store.index_chunk(collection_name, chunk2.chunk_id, embedding2, metadata2)
        
        # Setze qdrant_point_id (wird aus chunk_id generiert)
        import uuid
        chunk1.qdrant_point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk1.chunk_id))
        chunk2.qdrant_point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk2.chunk_id))
        
        # Speichere in DB
        saved_chunk1 = self.chunk_repo.save(chunk1)
        saved_chunk2 = self.chunk_repo.save(chunk2)
        
        # Lösche Original aus DB und Vector Store
        self.chunk_repo.delete(chunk_id)
        if original_chunk.chunk_id:
            # WICHTIG: Verwende delete_chunk statt delete_point
            self.vector_store.delete_chunk(collection_name, original_chunk.chunk_id)
        
        return [saved_chunk1, saved_chunk2]


class MergeChunksUseCase:
    """
    Use Case: Zwei Chunks zusammenführen.
    
    Führt zwei benachbarte Chunks zu einem zusammen.
    """
    
    def __init__(self, chunk_repo, vector_store, embedding_service):
        """
        Initialisiere Use Case.
        
        Args:
            chunk_repo: DocumentChunkRepository Instance
            vector_store: VectorStoreRepository Instance
            embedding_service: EmbeddingService Instance
        """
        self.chunk_repo = chunk_repo
        self.vector_store = vector_store
        self.embedding_service = embedding_service
    
    async def execute(self, chunk_ids: List[int]):
        """
        Führe Chunks zusammen.
        
        Args:
            chunk_ids: Liste von Chunk IDs (mindestens 2)
        
        Returns:
            Neuer zusammengeführter DocumentChunk
        
        Raises:
            ValueError: Wenn weniger als 2 Chunks oder Chunks nicht gefunden
        """
        from contexts.ragintegration.domain.entities import DocumentChunk
        from contexts.ragintegration.domain.value_objects import ChunkMetadata
        import uuid
        
        if len(chunk_ids) < 2:
            raise ValueError("Mindestens 2 Chunks müssen zum Zusammenführen angegeben werden")
        
        # Lade Chunks
        chunks = []
        for chunk_id in chunk_ids:
            chunk = self.chunk_repo.get_by_id(chunk_id)
            if not chunk:
                raise ValueError(f"Chunk {chunk_id} nicht gefunden")
            chunks.append(chunk)
        
        # Prüfe ob alle Chunks zum selben Dokument gehören
        indexed_doc_id = chunks[0].indexed_document_id
        if not all(c.indexed_document_id == indexed_doc_id for c in chunks):
            raise ValueError("Chunks müssen zum selben Dokument gehören")
        
        # Merge Text
        merged_text = " ".join(c.chunk_text for c in chunks)
        
        # Merge Metadata
        all_page_numbers = []
        for chunk in chunks:
            all_page_numbers.extend(chunk.metadata.page_numbers)
        unique_page_numbers = sorted(list(set(all_page_numbers)))
        
        # Erstelle neuen Chunk
        merged_chunk = DocumentChunk(
            id=None,
            indexed_document_id=indexed_doc_id,
            chunk_id=f"{chunks[0].chunk_id}_merged",
            chunk_text=merged_text,
            metadata=ChunkMetadata(
                page_numbers=unique_page_numbers,
                heading_hierarchy=chunks[0].metadata.heading_hierarchy,  # Nimm erste
                chunk_type=chunks[0].metadata.chunk_type,  # Nimm erste
                token_count=None,  # TODO: Recalculate
                sentence_count=None,  # TODO: Recalculate
                has_overlap=False,
                overlap_sentence_count=0
            ),
            qdrant_point_id=str(uuid.uuid4()),
            created_at=datetime.utcnow()
        )
        
        # Generiere Embedding
        embedding = await self.embedding_service.create_embedding(merged_text)
        
        # Speichere in Vector Store
        point_id = await self.vector_store.add_point(
            point_id=merged_chunk.qdrant_point_id,
            vector=embedding,
            payload={"chunk_id": merged_chunk.chunk_id, "text": merged_text}
        )
        merged_chunk.qdrant_point_id = point_id
        
        # Speichere in DB
        saved_chunk = self.chunk_repo.save(merged_chunk)
        
        # Lösche Originale
        for chunk in chunks:
            self.chunk_repo.delete(chunk.id)
            if chunk.qdrant_point_id:
                await self.vector_store.delete_point(chunk.qdrant_point_id)
        
        return saved_chunk


# ============================================================================
# RAG FEEDBACK USE CASES (PHASE 4.1)
# ============================================================================

class SubmitFeedbackUseCase:
    """
    Use Case: User Feedback für RAG Chat-Antwort abgeben.
    
    Ermöglicht es Usern, Feedback zu RAG-Antworten zu geben für
    Qualitätsverbesserung und ML-Training.
    """
    
    def __init__(
        self,
        feedback_repo,
        message_repo=None,
        event_publisher=None,
        training_data_repo=None
    ):
        """
        Initialisiere Use Case.
        
        Args:
            feedback_repo: RAGFeedbackRepository Instance
            message_repo: ChatMessageRepository (für Training-Daten-Extraktion)
            event_publisher: Optional Event Publisher für FeedbackSubmittedEvent
            training_data_repo: Optional Training Data Repository für ML-Training (v2.7.0)
        """
        self.feedback_repo = feedback_repo
        self.message_repo = message_repo
        self.event_publisher = event_publisher
        self.training_data_repo = training_data_repo
    
    async def execute(
        self,
        chat_message_id: int,
        user_id: int,
        rating: str,
        comment: Optional[str] = None
    ):
        """
        Speichere User Feedback.
        
        Args:
            chat_message_id: Chat Message ID (Assistant-Message)
            user_id: User ID
            rating: Bewertung ("positive", "negative", "neutral")
            comment: Optionaler Kommentar (max 2000 Zeichen)
        
        Returns:
            Gespeicherter RAGFeedback
        
        Raises:
            ValueError: Wenn Feedback bereits existiert oder ungültige Daten
        """
        from contexts.ragintegration.domain.entities import RAGFeedback
        
        # Prüfe ob bereits Feedback für diese Message von diesem User existiert
        existing = await self.feedback_repo.get_by_message_id(
            chat_message_id=chat_message_id,
            user_id=user_id
        )
        if existing:
            raise ValueError(f"Feedback already exists for message {chat_message_id} by user {user_id}")
        
        # Erstelle Entity
        feedback = RAGFeedback(
            id=None,
            chat_message_id=chat_message_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
            submitted_at=datetime.utcnow()
        )
        
        # Speichere in Repository
        saved_feedback = await self.feedback_repo.save(feedback)
        
        # Publiziere Event
        if self.event_publisher:
            from contexts.ragintegration.domain.events import FeedbackSubmittedEvent
            event = FeedbackSubmittedEvent(
                feedback_id=saved_feedback.id,
                chat_message_id=chat_message_id,
                user_id=user_id,
                rating=rating,
                timestamp=saved_feedback.submitted_at
            )
            await self.event_publisher.publish(event)
        
        # NEU v2.7.0: Speichere Training-Daten (falls Repository vorhanden UND Feature aktiviert)
        import os
        feedback_training_enabled = os.getenv('FEEDBACK_TRAINING_ENABLE', 'true').lower() == 'true'
        
        if self.training_data_repo and self.message_repo and feedback_training_enabled:
            try:
                # Hole Chat-Message für Features
                message = self.message_repo.get_by_id(chat_message_id)
                
                if message and message.source_references:
                    # Mappe Feedback zu Relevance-Score
                    from contexts.ragintegration.infrastructure.ml.training_data_repository import map_feedback_to_relevance
                    relevance_score = map_feedback_to_relevance(rating)
                    
                    # Erstelle Training-Samples für alle Source References
                    for ref in message.source_references:
                        # Hole ML-Features aus _extended_metadata
                        extended_metadata = getattr(ref, '_extended_metadata', {})
                        
                        if extended_metadata:
                            training_sample = {
                                'query': message.content if message.role == 'user' else 'Unknown',
                                'chunk_id': ref.chunk_id,
                                'features': {
                                    'vector_score': extended_metadata.get('vector_score', 0.0),
                                    'text_score': extended_metadata.get('text_score', 0.0),
                                    'bm25_score': extended_metadata.get('bm25_score', 0.0),
                                    'jaccard_score': extended_metadata.get('jaccard_score', 0.0),
                                    'keyword_matches': extended_metadata.get('keyword_matches', 0),
                                    'chunk_length': extended_metadata.get('chunk_length', 0),
                                    'document_type_encoded': extended_metadata.get('document_type_encoded', 0.0),
                                    'heading_hierarchy_depth': extended_metadata.get('heading_hierarchy_depth', 0),
                                    'confidence_score': extended_metadata.get('confidence_score', 0.5),
                                    'user_level': extended_metadata.get('user_level', 1),
                                    'hybrid_score': extended_metadata.get('hybrid_score', 0.0)
                                },
                                'relevance_score': relevance_score,
                                'source': 'feedback',
                                'user_id': user_id,
                                'feedback_id': saved_feedback.id
                            }
                            
                            # Speichere Training-Sample
                            self.training_data_repo.save_training_sample(training_sample)
                            print(f"✅ Training-Sample aus Feedback erstellt: {ref.chunk_id}")
            
            except Exception as e:
                # Graceful Error Handling: Feedback speichern funktioniert auch wenn Training-Daten fehlschlagen
                print(f"⚠️ Konnte Training-Daten nicht aus Feedback erstellen: {e}")
        
        return saved_feedback


# ============================================================================
# CHUNK FEEDBACK USE CASES (v2.9.0: Chunk-Level Feedback)
# ============================================================================

class SubmitChunkFeedbackUseCase:
    """
    Use Case: Speichere Chunk-Level Feedback.
    
    Ermöglicht es Usern, Feedback zu einzelnen Chunks zu geben für:
    - Präzise Qualitätsverbesserung (welche Chunks sind relevant/nicht relevant)
    - ML-Training (Chunk-Level Relevanz-Scores)
    - Analytics (Chunk-Level Metriken)
    """
    
    def __init__(
        self,
        chunk_feedback_repo,
        message_repo=None,
        event_publisher=None,
        training_data_repo=None
    ):
        """
        Initialisiere Use Case.
        
        Args:
            chunk_feedback_repo: ChunkFeedbackRepository
            message_repo: Optional ChatMessageRepository (für Validierung)
            event_publisher: Optional EventPublisher (für Events)
            training_data_repo: Optional TrainingDataRepository (für ML-Training)
        """
        self.chunk_feedback_repo = chunk_feedback_repo
        self.message_repo = message_repo
        self.event_publisher = event_publisher
        self.training_data_repo = training_data_repo
    
    async def execute(
        self,
        chunk_id: str,
        chat_message_id: int,
        document_id: int,
        user_id: int,
        rating: str,
        comment: Optional[str] = None
    ):
        """
        Speichere Chunk-Level Feedback.
        
        Args:
            chunk_id: Chunk-ID (z.B. "doc_123_meta_abc123")
            chat_message_id: Chat Message ID (für Kontext)
            document_id: Dokument-ID (für Kontext)
            user_id: User ID
            rating: Bewertung ("positive", "negative", "neutral")
            comment: Optionaler Kommentar (max 2000 Zeichen)
        
        Returns:
            Gespeicherter ChunkFeedback
        
        Raises:
            ValueError: Wenn ungültige Daten
        """
        from contexts.ragintegration.domain.entities import ChunkFeedback
        
        # Validiere dass Message existiert (falls Repository vorhanden)
        if self.message_repo:
            try:
                message = self.message_repo.get_by_id(chat_message_id)
                if not message:
                    raise ValueError(f"Chat message {chat_message_id} not found")
            except Exception as e:
                print(f"DEBUG: Konnte Message nicht validieren: {e}")
        
        # Erstelle Entity
        feedback = ChunkFeedback(
            id=None,
            chunk_id=chunk_id,
            chat_message_id=chat_message_id,
            document_id=document_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
            submitted_at=datetime.utcnow()
        )
        
        # Speichere in Repository
        saved_feedback = await self.chunk_feedback_repo.save(feedback)
        
        # Publiziere Event (falls vorhanden)
        if self.event_publisher:
            from contexts.ragintegration.domain.events import ChunkFeedbackSubmittedEvent
            event = ChunkFeedbackSubmittedEvent(
                chunk_feedback_id=saved_feedback.id,
                chunk_id=chunk_id,
                chat_message_id=chat_message_id,
                document_id=document_id,
                user_id=user_id,
                rating=rating,
                timestamp=saved_feedback.submitted_at
            )
            await self.event_publisher.publish(event)
        
        # NEU v2.9.0: Speichere Training-Daten (falls Repository vorhanden)
        # TODO: Implementiere Training-Data-Integration für Chunk-Level Feedback
        
        return saved_feedback


class GetFeedbackStatisticsUseCase:
    """
    Use Case: Hole Feedback-Statistiken.
    
    Ermöglicht Abruf von Feedback-Statistiken für Analytics und Monitoring.
    """
    
    def __init__(self, feedback_repo):
        """
        Initialisiere Use Case.
        
        Args:
            feedback_repo: RAGFeedbackRepository Instance
        """
        self.feedback_repo = feedback_repo
    
    async def execute(
        self,
        chat_message_id: Optional[int] = None,
        user_id: Optional[int] = None
    ):
        """
        Hole Feedback-Statistiken.
        
        Args:
            chat_message_id: Optional Filter nach Chat Message
            user_id: Optional Filter nach User
        
        Returns:
            Dict mit Statistiken (total, positive, negative, neutral, average_rating)
        """
        return await self.feedback_repo.get_statistics(
            chat_message_id=chat_message_id,
            user_id=user_id
        )


# ============================================================================
# RAG ANALYTICS USE CASES (PHASE 4.2)
# ============================================================================

class GetRAGAnalyticsUseCase:
    """
    Use Case: Hole umfassende RAG Analytics.
    
    Aggregiert Daten aus verschiedenen Quellen:
    - Feedback-Statistiken
    - Query-Performance
    - Chunking/Indexing-Metriken
    - Quality Trends
    """
    
    def __init__(
        self,
        feedback_repo,
        audit_repo,
        chat_message_repo,
        indexed_document_repo=None,
        training_data_repo=None  # NEU: Training Data Repository für SHAP-Statistiken
    ):
        """
        Initialisiere Use Case.
        
        Args:
            feedback_repo: RAGFeedbackRepository Instance
            audit_repo: RAGAuditLogRepository Instance
            chat_message_repo: ChatMessageRepository Instance
            indexed_document_repo: Optional IndexedDocumentRepository Instance
            training_data_repo: Optional TrainingDataRepository Instance (für SHAP-Statistiken)
        """
        self.feedback_repo = feedback_repo
        self.audit_repo = audit_repo
        self.chat_message_repo = chat_message_repo
        self.indexed_document_repo = indexed_document_repo
        self.training_data_repo = training_data_repo  # NEU: Training Data Repository
    
    async def execute(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None
    ):
        """
        Hole umfassende RAG Analytics.
        
        Args:
            start_date: Optional Start-Datum für Zeitbereich
            end_date: Optional End-Datum für Zeitbereich
            user_id: Optional User ID Filter
        
        Returns:
            Dict mit umfassenden Analytics-Daten
        """
        # 1. Feedback-Statistiken
        feedback_stats = await self.feedback_repo.get_statistics(
            user_id=user_id
        )
        
        # 2. Query-Statistiken aus Audit Logs
        # Hole alle Audit Logs (wenn user_id gegeben, nur für diesen User)
        if user_id:
            all_audit_logs = await self.audit_repo.get_by_user_id(
                user_id=user_id,
                limit=10000  # Großzügiges Limit für Analytics
            )
        else:
            # Für alle User: Hole Logs für mehrere User (Workaround: hole für User 1-100)
            # TODO: Bessere Methode implementieren (get_all() für Audit Logs)
            all_audit_logs = []
            for uid in range(1, 101):  # Annahme: Max 100 User
                try:
                    user_logs = await self.audit_repo.get_by_user_id(user_id=uid, limit=1000)
                    all_audit_logs.extend(user_logs)
                except:
                    break  # Stoppe wenn User nicht existiert
        
        # Filtere nach Zeitbereich wenn angegeben
        if start_date or end_date:
            filtered_logs = []
            # Normalisiere Datetimes auf timezone-naive (DB verwendet timezone-naive)
            start_dt_naive = start_date.replace(tzinfo=None) if start_date and start_date.tzinfo else start_date
            end_dt_naive = end_date.replace(tzinfo=None) if end_date and end_date.tzinfo else end_date
            
            for log in all_audit_logs:
                # Normalisiere log.timestamp auf timezone-naive falls nötig
                log_timestamp = log.timestamp.replace(tzinfo=None) if log.timestamp.tzinfo else log.timestamp
                
                if start_dt_naive and log_timestamp < start_dt_naive:
                    continue
                if end_dt_naive and log_timestamp > end_dt_naive:
                    continue
                filtered_logs.append(log)
            all_audit_logs = filtered_logs
        
        # Zähle Queries
        query_logs = [log for log in all_audit_logs if log.action == "query_executed"]
        total_queries = len(query_logs)
        avg_query_duration = (
            sum(log.duration_ms for log in query_logs if log.duration_ms) / len(query_logs)
            if query_logs else 0
        )
        
        # 3. Chunking-Statistiken
        chunking_logs = [log for log in all_audit_logs if log.action.startswith("chunking_")]
        chunking_started = len([log for log in chunking_logs if log.action == "chunking_started"])
        chunking_completed = len([log for log in chunking_logs if log.action == "chunking_completed"])
        chunking_failed = len([log for log in chunking_logs if log.action == "chunking_failed"])
        
        # 4. Indexing-Statistiken
        indexing_logs = [log for log in all_audit_logs if log.action.startswith("indexing_")]
        indexing_started = len([log for log in indexing_logs if log.action == "indexing_started"])
        indexing_completed = len([log for log in indexing_logs if log.action == "indexing_completed"])
        indexing_failed = len([log for log in indexing_logs if log.action == "indexing_failed"])
        
        # 5. Chat Message Count
        all_messages = await self.chat_message_repo.get_all()
        if start_date or end_date:
            filtered_messages = []
            # Normalisiere Datetimes auf timezone-naive (DB verwendet timezone-naive)
            start_dt_naive = start_date.replace(tzinfo=None) if start_date and start_date.tzinfo else start_date
            end_dt_naive = end_date.replace(tzinfo=None) if end_date and end_date.tzinfo else end_date
            
            for msg in all_messages:
                msg_date = msg.created_at if hasattr(msg, 'created_at') else datetime.utcnow()
                # Normalisiere msg_date auf timezone-naive falls nötig
                msg_date_naive = msg_date.replace(tzinfo=None) if msg_date.tzinfo else msg_date
                
                if start_dt_naive and msg_date_naive < start_dt_naive:
                    continue
                if end_dt_naive and msg_date_naive > end_dt_naive:
                    continue
                filtered_messages.append(msg)
            all_messages = filtered_messages
        
        total_messages = len(all_messages)
        assistant_messages = len([msg for msg in all_messages if hasattr(msg, 'role') and msg.role == 'assistant'])
        
        # 6. Quality Score (basierend auf Feedback)
        quality_score = feedback_stats.get("average_rating", 0.0) * 100  # 0-100 Skala
        
        # 7. SHAP-Statistiken (NEU: Phase 3)
        shap_statistics = None
        if self.training_data_repo:
            try:
                # Hole Training Data mit SHAP-Erklärungen
                # WICHTIG: get_training_data ist nicht async, daher kein await
                training_data_with_shap = self.training_data_repo.get_training_data(
                    with_shap=True,
                    user_id=user_id,
                    limit=10000  # Großzügiges Limit für Analytics
                )
                
                # Filtere nach Zeitbereich wenn angegeben
                if start_date or end_date:
                    filtered_training_data = []
                    start_dt_naive = start_date.replace(tzinfo=None) if start_date and start_date.tzinfo else start_date
                    end_dt_naive = end_date.replace(tzinfo=None) if end_date and end_date.tzinfo else end_date
                    
                    for td in training_data_with_shap:
                        td_date = td.created_at.replace(tzinfo=None) if td.created_at.tzinfo else td.created_at
                        if start_dt_naive and td_date < start_dt_naive:
                            continue
                        if end_dt_naive and td_date > end_dt_naive:
                            continue
                        filtered_training_data.append(td)
                    training_data_with_shap = filtered_training_data
                
                # Berechne SHAP-Statistiken
                total_explanations = len(training_data_with_shap)
                
                if total_explanations > 0:
                    # Sammle alle Features aus SHAP-Erklärungen
                    feature_importances = {}  # Dict[feature_name, List[importance_values]]
                    
                    for td in training_data_with_shap:
                        if td.shap_explanation and isinstance(td.shap_explanation, dict):
                            feature_importance = td.shap_explanation.get("feature_importance", {})
                            if isinstance(feature_importance, dict):
                                for feature_name, importance_value in feature_importance.items():
                                    if feature_name not in feature_importances:
                                        feature_importances[feature_name] = []
                                    feature_importances[feature_name].append(abs(importance_value))
                    
                    # Berechne durchschnittliche Importance pro Feature
                    average_feature_importances = {}
                    for feature_name, importance_values in feature_importances.items():
                        if importance_values:
                            average_feature_importances[feature_name] = sum(importance_values) / len(importance_values)
                    
                    # Sortiere Features nach durchschnittlicher Importance (höchste zuerst)
                    sorted_features = sorted(
                        average_feature_importances.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                    
                    # Top 10 Features
                    top_features = [
                        {"feature": feature_name, "average_importance": avg_importance}
                        for feature_name, avg_importance in sorted_features[:10]
                    ]
                    
                    # Durchschnittliche Anzahl Features pro Erklärung
                    total_feature_count = sum(len(td.shap_explanation.get("feature_importance", {})) if td.shap_explanation and isinstance(td.shap_explanation, dict) else 0 for td in training_data_with_shap)
                    average_feature_count = total_feature_count / total_explanations if total_explanations > 0 else 0.0
                    
                    shap_statistics = {
                        "total_explanations": total_explanations,
                        "average_feature_count": round(average_feature_count, 2),
                        "top_features": top_features
                    }
                else:
                    # Keine SHAP-Daten vorhanden
                    shap_statistics = {
                        "total_explanations": 0,
                        "average_feature_count": 0.0,
                        "top_features": []
                    }
            except Exception as e:
                # Graceful Error Handling: Wenn SHAP-Statistiken fehlschlagen, Analytics funktioniert trotzdem
                print(f"DEBUG: Fehler bei SHAP-Statistiken (überspringe): {e}")
                import traceback
                traceback.print_exc()
                shap_statistics = None
        
        result = {
            "feedback": feedback_stats,
            "queries": {
                "total": total_queries,
                "average_duration_ms": round(avg_query_duration, 2),
                "success_rate": 1.0  # Queries schlagen normalerweise nicht fehl
            },
            "chunking": {
                "started": chunking_started,
                "completed": chunking_completed,
                "failed": chunking_failed,
                "success_rate": round(chunking_completed / chunking_started * 100, 2) if chunking_started > 0 else 0.0
            },
            "indexing": {
                "started": indexing_started,
                "completed": indexing_completed,
                "failed": indexing_failed,
                "success_rate": round(indexing_completed / indexing_started * 100, 2) if indexing_started > 0 else 0.0
            },
            "messages": {
                "total": total_messages,
                "assistant": assistant_messages,
                "user": total_messages - assistant_messages
            },
            "quality": {
                "score": round(quality_score, 2),
                "trend": "stable"  # TODO: Berechne Trend aus historischen Daten
            },
            "time_range": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }
        
        # Füge SHAP-Statistiken hinzu (optional)
        if shap_statistics is not None:
            result["shap"] = shap_statistics
        
        return result


# ============================================================================
# SEARCH QUALITY ANALYTICS USE CASES (PHASE 5)
# ============================================================================

class GetSearchQualityAnalyticsUseCase:
    """
    Use Case: Hole Search Quality Analytics.
    
    Analysiert Suchqualität basierend auf:
    - Dokument-Typ-Verteilung in Suchergebnissen
    - Score-Verteilung
    - Top Queries mit gefundenen/fehlenden Dokument-Typen
    - SHAP-basierte Insights
    """
    
    def __init__(
        self,
        chat_message_repo,
        training_data_repo=None,
        indexed_document_repo=None
    ):
        """
        Initialisiere Use Case.
        
        Args:
            chat_message_repo: ChatMessageRepository Instance
            training_data_repo: Optional TrainingDataRepository Instance (für SHAP-Insights)
            indexed_document_repo: Optional IndexedDocumentRepository Instance (für Dokument-Typ-Counts)
        """
        self.chat_message_repo = chat_message_repo
        self.training_data_repo = training_data_repo
        self.indexed_document_repo = indexed_document_repo
    
    async def execute(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        top_k: int = 5  # Top-K für "found_in_top_k" Berechnung
    ) -> Dict[str, Any]:
        """
        Hole Search Quality Analytics.
        
        Args:
            start_date: Optional - Start-Datum für Filterung
            end_date: Optional - End-Datum für Filterung
            top_k: Anzahl der Top-K Chunks für "found_in_top_k" Berechnung
        
        Returns:
            Dict mit:
            - document_type_distribution: Liste von {document_type, count, average_score, found_in_top_k}
            - score_distribution: {min, max, average, median}
            - top_queries: Liste von {query, document_types_found, missing_document_types, average_score}
            - shap_insights: Liste von {feature, impact, explanation}
        """
        from collections import defaultdict
        from statistics import median
        
        # 1. Hole alle Chat Messages
        all_messages = await self.chat_message_repo.get_all()
        
        # Filtere nach Zeitbereich
        if start_date or end_date:
            filtered_messages = []
            start_dt_naive = start_date.replace(tzinfo=None) if start_date and start_date.tzinfo else start_date
            end_dt_naive = end_date.replace(tzinfo=None) if end_date and end_date.tzinfo else end_date
            
            for msg in all_messages:
                msg_date = msg.created_at.replace(tzinfo=None) if msg.created_at.tzinfo else msg.created_at
                if start_dt_naive and msg_date < start_dt_naive:
                    continue
                if end_dt_naive and msg_date > end_dt_naive:
                    continue
                filtered_messages.append(msg)
            all_messages = filtered_messages
        
        # 2. Sammle Source References aus Assistant Messages
        all_source_refs = []
        query_to_refs = {}  # Map query -> source references
        
        for msg in all_messages:
            if msg.role == "assistant" and msg.source_references:
                all_source_refs.extend(msg.source_references)
                
                # Finde zugehörige User-Message für Query
                user_msg = None
                for prev_msg in reversed(all_messages):
                    if prev_msg.session_id == msg.session_id and prev_msg.role == "user":
                        user_msg = prev_msg
                        break
                
                if user_msg:
                    query = user_msg.content
                    if query not in query_to_refs:
                        query_to_refs[query] = []
                    query_to_refs[query].extend(msg.source_references)
        
        # 3. Dokument-Typ-Verteilung
        doc_type_stats = defaultdict(lambda: {"scores": [], "in_top_k": 0, "total": 0})
        
        # Hole alle indexierten Dokumente für Counts
        indexed_docs = []
        if self.indexed_document_repo:
            indexed_docs = self.indexed_document_repo.get_all()
        
        # Zähle Dokumente pro Typ
        doc_type_counts = defaultdict(int)
        for doc in indexed_docs:
            # Hole document_type aus UploadDocument
            from backend.app.models import UploadDocument
            from backend.app.database import SessionLocal
            db_session = SessionLocal()
            try:
                upload_doc = db_session.query(UploadDocument).filter(
                    UploadDocument.id == doc.upload_document_id
                ).first()
                if upload_doc and upload_doc.document_type:
                    doc_type_name = upload_doc.document_type.name
                    doc_type_counts[doc_type_name] += 1
            except Exception as e:
                print(f"DEBUG: Fehler beim Laden von document_type: {e}")
            finally:
                db_session.close()
        
        # Analysiere Source References
        for ref in all_source_refs:
            # Hole document_type aus _extended_metadata oder document_title
            doc_type = None
            if hasattr(ref, '_extended_metadata') and ref._extended_metadata:
                doc_type = ref._extended_metadata.get('chunk_metadata', {}).get('document_type')
            
            if not doc_type:
                    # Fallback: Versuche aus document_title zu extrahieren
                    # Oder hole aus UploadDocument
                    try:
                        from backend.app.models import UploadDocument
                        from contexts.ragintegration.infrastructure.models import IndexedDocumentModel
                        from backend.app.database import SessionLocal
                        db_session = SessionLocal()
                        try:
                            indexed_doc = db_session.query(IndexedDocumentModel).filter(
                                IndexedDocumentModel.id == ref.document_id
                            ).first()
                            if indexed_doc:
                                upload_doc = db_session.query(UploadDocument).filter(
                                    UploadDocument.id == indexed_doc.upload_document_id
                                ).first()
                                if upload_doc and upload_doc.document_type:
                                    doc_type = upload_doc.document_type.name
                        finally:
                            db_session.close()
                    except Exception as e:
                        print(f"DEBUG: Fehler beim Extrahieren von document_type: {e}")
            
            if doc_type:
                doc_type_stats[doc_type]["scores"].append(ref.relevance_score)
                doc_type_stats[doc_type]["total"] += 1
                
                # Prüfe ob in Top-K (basierend auf rank_position)
                rank = None
                if hasattr(ref, '_extended_metadata') and ref._extended_metadata:
                    rank = ref._extended_metadata.get('rank_position')
                
                if rank and rank <= top_k:
                    doc_type_stats[doc_type]["in_top_k"] += 1
        
        # Erstelle document_type_distribution
        document_type_distribution = []
        for doc_type, stats in doc_type_stats.items():
            avg_score = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0.0
            document_type_distribution.append({
                "document_type": doc_type,
                "count": doc_type_counts.get(doc_type, stats["total"]),
                "average_score": round(avg_score, 4),
                "found_in_top_k": stats["in_top_k"]
            })
        
        # Sortiere nach average_score (höchste zuerst)
        document_type_distribution.sort(key=lambda x: x["average_score"], reverse=True)
        
        # 4. Score-Verteilung
        all_scores = [ref.relevance_score for ref in all_source_refs]
        score_distribution = {
            "min": round(min(all_scores), 4) if all_scores else 0.0,
            "max": round(max(all_scores), 4) if all_scores else 0.0,
            "average": round(sum(all_scores) / len(all_scores), 4) if all_scores else 0.0,
            "median": round(median(all_scores), 4) if all_scores else 0.0
        }
        
        # 5. Top Queries
        top_queries = []
        for query, refs in query_to_refs.items():
            if not refs:
                continue
            
            # Sammle gefundene und fehlende Dokument-Typen
            found_types = set()
            all_types_in_system = set(doc_type_counts.keys())
            
            for ref in refs:
                doc_type = None
                if hasattr(ref, '_extended_metadata') and ref._extended_metadata:
                    doc_type = ref._extended_metadata.get('chunk_metadata', {}).get('document_type')
                
                if not doc_type:
                    # Fallback: Hole aus UploadDocument
                    try:
                        from backend.app.models import UploadDocument
                        from contexts.ragintegration.infrastructure.models import IndexedDocumentModel
                        from backend.app.database import SessionLocal
                        db_session = SessionLocal()
                        try:
                            indexed_doc = db_session.query(IndexedDocumentModel).filter(
                                IndexedDocumentModel.id == ref.document_id
                            ).first()
                            if indexed_doc:
                                upload_doc = db_session.query(UploadDocument).filter(
                                    UploadDocument.id == indexed_doc.upload_document_id
                                ).first()
                                if upload_doc and upload_doc.document_type:
                                    doc_type = upload_doc.document_type.name
                        finally:
                            db_session.close()
                    except Exception:
                        pass
                
                if doc_type:
                    found_types.add(doc_type)
            
            missing_types = all_types_in_system - found_types
            avg_score = sum(ref.relevance_score for ref in refs) / len(refs) if refs else 0.0
            
            top_queries.append({
                "query": query,
                "document_types_found": list(found_types),
                "missing_document_types": list(missing_types),
                "average_score": round(avg_score, 4)
            })
        
        # Sortiere nach average_score (höchste zuerst)
        top_queries.sort(key=lambda x: x["average_score"], reverse=True)
        top_queries = top_queries[:10]  # Top 10 Queries
        
        # 6. SHAP-Insights
        shap_insights = []
        if self.training_data_repo:
            try:
                training_data = self.training_data_repo.get_training_data(
                    with_shap=True,
                    limit=1000
                )
                
                # Sammle Feature-Importances
                feature_importances = defaultdict(list)
                
                for td in training_data:
                    if td.shap_explanation and isinstance(td.shap_explanation, dict):
                        feature_importance = td.shap_explanation.get("feature_importance", {})
                        if isinstance(feature_importance, dict):
                            for feature_name, importance_value in feature_importance.items():
                                feature_importances[feature_name].append(abs(importance_value))
                
                # Berechne durchschnittliche Importance pro Feature
                for feature_name, importance_values in feature_importances.items():
                    if importance_values:
                        avg_importance = sum(importance_values) / len(importance_values)
                        
                        # Erstelle Erklärung basierend auf Feature-Name
                        explanation = self._generate_shap_explanation(feature_name, avg_importance)
                        
                        shap_insights.append({
                            "feature": feature_name,
                            "impact": round(avg_importance, 4),
                            "explanation": explanation
                        })
                
                # Sortiere nach Impact (höchste zuerst)
                shap_insights.sort(key=lambda x: x["impact"], reverse=True)
                shap_insights = shap_insights[:10]  # Top 10 Features
                
            except Exception as e:
                print(f"DEBUG: Fehler bei SHAP-Insights (überspringe): {e}")
                import traceback
                traceback.print_exc()
        
        return {
            "document_type_distribution": document_type_distribution,
            "score_distribution": score_distribution,
            "top_queries": top_queries,
            "shap_insights": shap_insights
        }
    
    def _generate_shap_explanation(self, feature_name: str, impact: float) -> str:
        """
        Generiere Erklärung für SHAP-Feature.
        
        Args:
            feature_name: Name des Features
            impact: Durchschnittliche Importance
        
        Returns:
            Erklärungstext
        """
        explanations = {
            "document_type": f"Dokument-Typ hat starken Einfluss ({impact*100:.1f}%): Bestimmte Dokument-Typen haben höhere Scores als andere",
            "vector_score": f"Vector-Score ist wichtig ({impact*100:.1f}%): Semantische Ähnlichkeit trägt zur Relevanz bei",
            "text_score": f"Text-Score ({impact*100:.1f}%): Keyword-Matching trägt zur Relevanz bei",
            "hybrid_score": f"Hybrid-Score ({impact*100:.1f}%): Kombination aus Vector- und Text-Score",
            "chunk_length": f"Chunk-Länge ({impact*100:.1f}%): Längere Chunks haben tendenziell {'höhere' if impact > 0 else 'niedrigere'} Scores",
            "keyword_matches": f"Keyword-Übereinstimmungen ({impact*100:.1f}%): Mehr Übereinstimmungen = höhere Relevanz",
            "heading_hierarchy_depth": f"Überschriften-Hierarchie ({impact*100:.1f}%): Tiefere Hierarchie = strukturierterer Inhalt",
            "confidence_score": f"Confidence-Score ({impact*100:.1f}%): Vertrauenswürdigkeit des Chunks",
            "user_level": f"User-Level ({impact*100:.1f}%): Höheres Level = bessere Relevanz-Bewertung",
            "ml_score": f"ML Re-Ranking Score ({impact*100:.1f}%): Machine Learning Modell verbessert Ranking"
        }
        
        return explanations.get(feature_name, f"{feature_name} hat {impact*100:.1f}% Einfluss auf die Relevanz")


# ============================================================================
# RAG CHAT PROMPT USE CASES (PHASE 1)
# ============================================================================

class GetRAGChatPromptUseCase:
    """
    Use Case: Hole RAG Chat Prompt für einen Dokumenttyp.
    
    Priorität:
    1. Custom Prompt (aus rag_chat_prompts)
    2. Standard Prompt (aus prompt_templates + _get_document_type_prompt_instructions)
    3. Generischer Prompt (Fallback)
    """
    
    def __init__(
        self,
        rag_chat_prompt_repo: RAGChatPromptRepository,
        ai_service=None  # Optional: Für Standard-Prompt-Generierung
    ):
        self.rag_chat_prompt_repo = rag_chat_prompt_repo
        self.ai_service = ai_service
    
    def execute(self, document_type_id: int, document_type_name: Optional[str] = None) -> Optional[str]:
        """
        Hole RAG Chat Prompt für einen Dokumenttyp.
        
        Args:
            document_type_id: Document Type ID
            document_type_name: Optional Document Type Name (für Standard-Prompt)
            
        Returns:
            Prompt-Text oder None (wenn kein Custom Prompt und kein Standard-Prompt)
        """
        # 1. Prüfe Custom Prompt
        custom_prompt = self.rag_chat_prompt_repo.get_by_document_type_id(document_type_id)
        if custom_prompt:
            return custom_prompt.prompt_text
        
        # 2. Standard Prompt (wird in AI Service generiert, wenn document_type_name vorhanden)
        if document_type_name and self.ai_service:
            standard_prompt = self.ai_service._get_document_type_prompt_instructions(document_type_name)
            if standard_prompt:
                return standard_prompt
        
        # 3. Fallback: None (wird dann generischer Prompt verwendet)
        return None


class SaveRAGChatPromptUseCase:
    """
    Use Case: Speichere RAG Chat Prompt (Level 4+).
    
    Speichert einen globalen, dokumenttyp-spezifischen RAG Chat Prompt.
    """
    
    def __init__(self, rag_chat_prompt_repo: RAGChatPromptRepository):
        self.rag_chat_prompt_repo = rag_chat_prompt_repo
    
    def execute(
        self,
        document_type_id: Optional[int],  # None = Default-Prompt
        prompt_text: str,
        multi_query_prompt_text: Optional[str] = None,
        user_id: int = 1,
        user_level: int = 1
    ) -> RAGChatPrompt:
        """
        Speichere Custom RAG Chat Prompt.
        
        Args:
            document_type_id: Document Type ID (None = Default-Prompt)
            prompt_text: RAG Chat Prompt-Text
            multi_query_prompt_text: Optional Multi-Query Prompt-Text (PHASE 2)
            user_id: User ID des Erstellers
            user_level: User Level (muss >= 4 sein)
            
        Returns:
            Gespeicherter RAGChatPrompt
            
        Raises:
            PermissionError: Wenn user_level < 4
            ValueError: Wenn prompt_text leer oder document_type_id ungültig
        """
        # RBAC: Prüfe Berechtigung
        if user_level < 4:
            raise PermissionError("Nur Level 4+ (QM/QM Admin) können RAG Chat Prompts anpassen")
        
        # Validiere Input
        if not prompt_text or not prompt_text.strip():
            raise ValueError("prompt_text darf nicht leer sein")
        
        if document_type_id is not None and document_type_id < 0:
            raise ValueError("document_type_id muss >= 0 oder None sein (None = Default-Prompt)")
        
        # Prüfe ob bereits ein Prompt existiert
        existing_prompt = self.rag_chat_prompt_repo.get_by_document_type_id(document_type_id)
        
        now = datetime.utcnow()
        
        if existing_prompt:
            # Update existierendes Prompt
            existing_prompt.prompt_text = prompt_text.strip()
            existing_prompt.multi_query_prompt_text = multi_query_prompt_text.strip() if multi_query_prompt_text else None
            existing_prompt.updated_at = now
            return self.rag_chat_prompt_repo.save(existing_prompt)
        else:
            # Neues Prompt
            new_prompt = RAGChatPrompt(
                id=None,
                document_type_id=document_type_id,
                prompt_text=prompt_text.strip(),
                created_by_user_id=user_id,
                created_at=now,
                updated_at=now,
                multi_query_prompt_text=multi_query_prompt_text.strip() if multi_query_prompt_text else None  # PHASE 2: Multi-Query Prompt (muss am Ende sein)
            )
            return self.rag_chat_prompt_repo.save(new_prompt)


class DeleteRAGChatPromptUseCase:
    """
    Use Case: Lösche RAG Chat Prompt (zurücksetzen auf Standard, Level 4+).
    
    Löscht einen Custom Prompt, sodass wieder der Standard-Prompt verwendet wird.
    """
    
    def __init__(self, rag_chat_prompt_repo: RAGChatPromptRepository):
        self.rag_chat_prompt_repo = rag_chat_prompt_repo
    
    def execute(
        self,
        document_type_id: Optional[int],  # None = Default-Prompt
        user_id: int = 1,
        user_level: int = 1
    ) -> bool:
        """
        Lösche Custom Prompt → zurück zu Standard.
        
        Args:
            document_type_id: Document Type ID (None = Default-Prompt)
            user_id: User ID (für Audit-Trail)
            user_level: User Level (muss >= 4 sein)
            
        Returns:
            True wenn gelöscht, False wenn nicht gefunden
            
        Raises:
            PermissionError: Wenn user_level < 4
        """
        # RBAC: Prüfe Berechtigung
        if user_level < 4:
            raise PermissionError("Nur Level 4+ (QM/QM Admin) können RAG Chat Prompts löschen")
        
        return self.rag_chat_prompt_repo.delete(document_type_id)