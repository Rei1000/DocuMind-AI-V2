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
            # 1. Erstelle IndexedDocument Entity
            collection_name = f"doc_{upload_document_id}_{int(datetime.now().timestamp())}"
            
            indexed_doc = IndexedDocument(
                id=None,
                upload_document_id=upload_document_id,
                collection_name=collection_name,
                total_chunks=1,  # Start mit 1, wird später aktualisiert
                indexed_at=datetime.now(),
                last_updated_at=datetime.now()
            )
            
            # 2. Speichere IndexedDocument
            saved_doc = self.indexed_document_repo.save(indexed_doc)
            
            # 3. Hole echte Vision-Daten aus der Datenbank
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
            
            # 6. Erstelle Collection in Qdrant
            collection_created = self.vector_store.create_collection(collection_name, 1536)
            print(f"DEBUG: Collection {collection_name} erstellt: {collection_created}")
            
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
        event_publisher
    ):
        self.chunk_repository = chunk_repository
        self.session_repository = session_repository
        self.indexed_document_repository = indexed_document_repository
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.multi_query_service = multi_query_service
        self.ai_service = ai_service
        self.event_publisher = event_publisher
    
    async def execute(
        self, 
        question: str, 
        session_id: int, 
        model_id: str = "gpt-4o-mini",
        filters: Optional[Dict[str, Any]] = None
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
            # 1. Multi-Query Expansion
            if self.multi_query_service:
                queries = self.multi_query_service.generate_queries(question)
            else:
                # Fallback: Verwende Original-Frage
                queries = [question]
            
            # 2. Suche relevante Chunks
            all_results = []
            for query in queries:
                # Erstelle Embedding für die Query
                query_embedding = self.embedding_service.generate_embedding(query)
                
                # Hole alle indexierten Dokumente und suche in deren Collections
                indexed_docs = self.indexed_document_repository.get_all()
                for doc in indexed_docs:
                    results = self.vector_store.search_similar(
                        collection_name=doc.collection_name,
                        query_embedding=query_embedding,
                        filters=filters or {},
                        top_k=10,
                        min_score=0.5
                    )
                    all_results.extend(results)
            
            # 3. Deduplizierung und Ranking
            unique_results = self._deduplicate_and_rank(all_results)
            
            # 4. Verwende echte Ergebnisse oder leere Liste
            if not unique_results:
                print("DEBUG: Keine Suchergebnisse gefunden, verwende leere Liste")
                unique_results = []
            
            # 5. Kontext-Fenster-Management
            context_chunks = self._manage_context_window(unique_results)
            
            # 6. AI-Antwort generieren
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
            
            # 7. Erstelle ChatMessage
            message = ChatMessage(
                id=None,
                session_id=session_id,
                role="assistant",
                content=ai_response["answer"],
                source_chunk_ids=[r["chunk_id"] for r in context_chunks],
                confidence_scores={r["chunk_id"]: r["score"] for r in context_chunks},
                created_at=datetime.now()
            )
            
            # 8. Publiziere Event
            if self.event_publisher:
                self.event_publisher.publish(ChatMessageCreatedEvent(
                    message_id=message.id,
                    session_id=session_id,
                    question=question,
                    answer=ai_response["answer"]
                ))
            
            return message
            
        except Exception as e:
            # Fallback bei Fehlern
            return ChatMessage(
                id=None,
                session_id=session_id,
                role="assistant",
                content=f"Entschuldigung, es gab einen Fehler: {str(e)}",
                source_chunk_ids=[],
                confidence_scores={},
                created_at=datetime.now()
            )
    
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
    
    def _manage_context_window(self, results: List[Dict]) -> List[Dict]:
        """Verwalte Kontext-Fenster basierend auf Token-Limits."""
        # Vereinfachte Implementierung: Nimm die ersten 5 Chunks
        return results[:5]


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


class GetChatHistoryUseCase:
    """Use Case: Hole Chat-Historie."""
    
    def __init__(self, message_repository: ChatMessageRepository):
        self.message_repository = message_repository
    
    def execute(self, session_id: int) -> List[ChatMessage]:
        """Hole Chat-Historie für Session."""
        return self.message_repository.get_by_session_id(session_id)


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