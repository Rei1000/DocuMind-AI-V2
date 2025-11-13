"""
Interface Layer: FastAPI Router für RAG Integration

Implementiert alle API-Endpoints für das RAG System.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import time
from fastapi import APIRouter, HTTPException, Depends, status, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from contexts.ragintegration.interface.schemas import (
    # Request Schemas
    IndexDocumentRequest, AskQuestionRequest, CreateSessionRequest,
    SearchDocumentsRequest, ReindexDocumentRequest,
    # Response Schemas
    IndexDocumentResponse, IndexedDocumentResponse, AskQuestionResponse, ChatHistoryResponse,
    ChatMessageResponse,  # WICHTIG: Für Chat-Historie
    SearchDocumentsResponse, ReindexDocumentResponse, ChatSessionResponse,
    SystemInfoResponse, HealthCheckResponse, UsageStatisticsResponse,
    DocumentIndexStatusResponse,  # NEU: Für Indexierungs-Status-Prüfung
    ChunksListResponse, ChunkPreviewResponse, ChunkMetadataResponse,  # PHASE 2.1: Chunk-Vorschau
    EditChunkRequest, SplitChunkRequest, MergeChunksRequest,  # PHASE 2.2: Chunk-Editor
    ChunkingStrategiesResponse, ChunkingStrategyOption,  # PHASE 2.3: Chunking-Strategie Selector
    PromptViewerResponse,  # PHASE 3.1: RAG Chat Prompt Viewer
    SubmitFeedbackRequest, FeedbackResponse, FeedbackStatisticsResponse,  # PHASE 4.1: RAG Feedback System
    RAGAnalyticsResponse,  # PHASE 4.2: RAG Analytics Dashboard
    SaveRAGChatPromptRequest, RAGChatPromptResponse,  # PHASE 1: RAG Chat Prompt Management
    # Error Schemas
    ErrorResponse, ValidationErrorResponse,
    # Filter Schemas
    DocumentFilter, ChunkFilter, SessionFilter, PaginationParams,
    # Enums
    DocumentStatus
)
from contexts.ragintegration.application.use_cases import (
    IndexApprovedDocumentUseCase, AskQuestionUseCase,
    CreateChatSessionUseCase, UpdateChatSessionUseCase, GetChatHistoryUseCase,
    GetDocumentTypeCountsUseCase, ReindexDocumentUseCase,
    EditChunkUseCase, DeleteChunkUseCase, SplitChunkUseCase, MergeChunksUseCase,  # PHASE 2.2: Chunk-Editor
    GetRAGChatPromptUseCase, SaveRAGChatPromptUseCase, DeleteRAGChatPromptUseCase  # PHASE 1: RAG Chat Prompt Management
)
from contexts.ragintegration.infrastructure.adapters import RAGInfrastructureAdapter
from contexts.ragintegration.infrastructure.ai_service import RAGAIService
from contexts.ragintegration.domain.entities import IndexedDocument, ChatSession, ChatMessage
from contexts.accesscontrol.domain.entities import User
from contexts.accesscontrol.interface.guard_router import get_current_user
from backend.app.database import get_db
from contexts.ragintegration.domain.value_objects import SourceReference

# Dependency für Database Session
def get_db_session():
    """Database Session Dependency."""
    return next(get_db())

# Dependency für RAG Infrastructure Adapter
def get_rag_adapter() -> RAGInfrastructureAdapter:
    """RAG Adapter Dependency."""
    import os
    from backend.app.database import get_db
    
    # Hole OpenAI API Key aus Environment
    # WICHTIG: Prüfe zuerst GPT-5 Mini Key (hat Zugriff auf Embeddings!)
    # Der RAGInfrastructureAdapter verwendet create_embedding_service mit auto-Auswahl,
    # aber wir sollten hier schon den richtigen Key übergeben für Konsistenz
    openai_api_key = os.getenv("OPENAI_GPT5_MINI_API_KEY") or os.getenv("OPENAI_API_KEY", "test-key")
    
    # Hole Database Session
    db_session = next(get_db())
    
    # Erstelle RAG Adapter
    # Note: create_embedding_service prüft selbst nochmal OPENAI_GPT5_MINI_API_KEY,
    # aber hier schon den besten Key übergeben für Konsistenz
    return RAGInfrastructureAdapter(
        db_session=db_session,
        openai_api_key=openai_api_key,
        collection_name="rag_documents"
    )

# Dependency für AI Service (wird später injiziert)
def get_ai_service():
    """Placeholder für AI Service Dependency."""
    # TODO: Implementiere echten AI Service
    pass

# Router erstellen
router = APIRouter(prefix="/api/rag", tags=["RAG Integration"])


@router.post("/documents/index", response_model=IndexDocumentResponse)
async def index_document(
    request: IndexDocumentRequest,
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter),
    ai_service = Depends(get_ai_service)
):
    """Indexiert ein freigegebenes Dokument für das RAG System."""
    try:
        start_time = time.time()
        
        # PHASE 2.3: Erstelle Embedding-Service basierend auf ausgewählter Strategie
        embedding_service = rag_adapter.embedding_service  # Default
        if request.chunking_strategy:
            from contexts.ragintegration.infrastructure.embedding_factory import create_embedding_service
            import os
            
            # Parse Strategie-ID
            if request.chunking_strategy == "openai_1536":
                # OpenAI mit 1536 Dimensionen
                openai_key = os.getenv("OPENAI_GPT5_MINI_API_KEY") or os.getenv("OPENAI_API_KEY")
                if openai_key:
                    embedding_service = create_embedding_service(
                        provider="openai",
                        openai_api_key=openai_key
                    )
                    print(f"✅ Verwende OpenAI Embedding Service (1536 dim) für Dokument {request.upload_document_id}")
                else:
                    print(f"⚠️ OpenAI Key nicht verfügbar, verwende Standard-Embedding-Service")
            elif request.chunking_strategy == "gemini_768":
                # Gemini mit 768 Dimensionen
                google_key = os.getenv("GOOGLE_AI_API_KEY")
                if google_key:
                    embedding_service = create_embedding_service(
                        provider="google",
                        google_api_key=google_key
                    )
                    print(f"✅ Verwende Google Gemini Embedding Service (768 dim) für Dokument {request.upload_document_id}")
                else:
                    print(f"⚠️ Google AI Key nicht verfügbar, verwende Standard-Embedding-Service")
            elif request.chunking_strategy == "local_384":
                # Local SentenceTransformer mit 384 Dimensionen
                embedding_service = create_embedding_service(
                    provider="sentence-transformers"
                )
                print(f"✅ Verwende Local SentenceTransformer Embedding Service (384 dim) für Dokument {request.upload_document_id}")
            else:
                print(f"⚠️ Unbekannte Strategie '{request.chunking_strategy}', verwende Standard-Embedding-Service")
        
        # Erstelle Use Case mit ausgewähltem Embedding-Service
        use_case = IndexApprovedDocumentUseCase(
            indexed_document_repo=rag_adapter.indexed_document_repo,
            chunk_repo=rag_adapter.document_chunk_repo,
            vision_extractor=rag_adapter.vision_extractor,
            chunking_service=rag_adapter.chunking_service,
            embedding_service=embedding_service,  # PHASE 2.3: Verwende ausgewählten Service
            vector_store=rag_adapter.vector_store,
            event_publisher=None  # TODO: Implementiere Event Publisher
        )
        
        # Hole den echten Dokumenttyp und Duplikat-Status aus der Datenbank
        from backend.app.database import get_db
        from sqlalchemy import text
        
        db_session = next(get_db())
        doc_info_result = db_session.execute(text('''
            SELECT dt.name, ud.is_duplicate, ud.duplicate_of_document_id
            FROM upload_documents ud 
            JOIN document_types dt ON ud.document_type_id = dt.id 
            WHERE ud.id = :doc_id
        '''), {"doc_id": request.upload_document_id})
        
        doc_info_row = doc_info_result.fetchone()
        if not doc_info_row:
            return IndexDocumentResponse(
                success=False,
                document=None,
                chunks_created=0,
                processing_time_ms=0,
                message="Dokument nicht gefunden"
            )
        
        document_type = doc_info_row[0] if doc_info_row[0] else "SOP"
        is_duplicate = doc_info_row[1] if doc_info_row[1] is not None else False
        duplicate_of_id = doc_info_row[2]
        
        print(f"DEBUG: Document type: {document_type}, is_duplicate: {is_duplicate}")
        
        # NEU: Prüfe ob Dokument ein Duplikat ist - Duplikate dürfen NICHT indexiert werden
        if is_duplicate:
            original_message = f" (zeigt auf Dokument #{duplicate_of_id})" if duplicate_of_id else ""
            return IndexDocumentResponse(
                success=False,
                document=None,
                chunks_created=0,
                processing_time_ms=0,
                message=f"Duplikate können nicht indexiert werden. Dieses Dokument ist eine Kopie{original_message}. Bitte indexieren Sie das Original-Dokument."
            )
        
        # Führe Indexierung durch
        print(f"DEBUG: Starting index for document {request.upload_document_id}")
        result = use_case.execute(
            upload_document_id=request.upload_document_id,
            document_type=document_type
        )
        print(f"DEBUG: Use case result: {result}")
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Prüfe ob Indexierung erfolgreich war
        if result["success"]:
            total_chunks = result.get('total_chunks', 0)
            # Hole zusätzliche Info: Anzahl verarbeiteter Seiten
            try:
                pages_row = db_session.execute(text('''
                    SELECT COUNT(DISTINCT page_number) as pages_count
                    FROM rag_document_chunks
                    WHERE rag_indexed_document_id = :indexed_doc_id
                '''), {"indexed_doc_id": result.get("indexed_document_id", 0)}).fetchone()
                pages_count = pages_row[0] if pages_row else 0
                message = f"Dokument erfolgreich indexiert. {total_chunks} Chunks aus {pages_count} Seiten erstellt."
            except Exception:
                message = f"Dokument erfolgreich indexiert. {total_chunks} Chunks erstellt."
        else:
            message = f"Indexierung fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}"
        
        return IndexDocumentResponse(
            success=result["success"],
            document=IndexedDocumentResponse(
                id=result.get("indexed_document_id", 0),
                upload_document_id=request.upload_document_id,
                document_title="Test Document",
                document_type="SOP",
                status="indexed" if result["success"] else "failed",
                indexed_at=datetime.now(),
                total_chunks=result.get("total_chunks", 0),
                last_updated=datetime.now()
            ),
            chunks_created=result.get("total_chunks", 0),
            processing_time_ms=processing_time,
            message=message
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"DEBUG: Router error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler bei der Indexierung: {str(e)}"
        )


@router.post("/test-ai", response_model=AskQuestionResponse)
async def test_ai_service(
    request: AskQuestionRequest,
    current_user: User = Depends(get_current_user),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """Test AI Service direkt ohne komplexe RAG-Logik."""
    try:
        start_time = time.time()
        
        # Erstelle AI Service
        from ..infrastructure.ai_service import RAGAIService
        ai_service = RAGAIService()
        
        # Erstelle Mock-Chunks für Test
        from ..domain.entities import DocumentChunk
        from ..domain.value_objects import ChunkMetadata
        from datetime import datetime
        
        mock_chunks = [
            DocumentChunk(
                id=1,
                indexed_document_id=1,
                chunk_id="test_chunk_1",
                chunk_text="Arbeitsanweisung für die Behandlung von Reparaturen. Diese Anweisung beschreibt die wichtigsten Schritte für die Durchführung von Reparaturen an medizinischen Geräten.",
                metadata=ChunkMetadata(
                    page_numbers=[1],
                    heading_hierarchy=["Arbeitsanweisung"],
                    chunk_type='text',
                    token_count=25
                ),
                qdrant_point_id="test_qdrant_1",
                created_at=datetime.utcnow()
            ),
            DocumentChunk(
                id=2,
                indexed_document_id=1,
                chunk_id="test_chunk_2",
                chunk_text="Sicherheitshinweise: Vor jeder Reparatur müssen alle Sicherheitsvorkehrungen beachtet werden. Tragen Sie Schutzausrüstung und prüfen Sie die Geräte auf Defekte.",
                metadata=ChunkMetadata(
                    page_numbers=[1],
                    heading_hierarchy=["Sicherheitshinweise"],
                    chunk_type='text',
                    token_count=22
                ),
                qdrant_point_id="test_qdrant_2",
                created_at=datetime.utcnow()
            )
        ]
        
        # Generiere AI Response
        model_id = request.model if hasattr(request, 'model') else "gpt-4o-mini"
        ai_response = await ai_service.generate_response_async(
            question=request.question,
            context_chunks=mock_chunks,
            model_id=model_id
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return AskQuestionResponse(
            answer=ai_response["answer"],
            source_references=[],
            structured_data=None,
            suggested_questions=["Was sind die wichtigsten Schritte?", "Welche Sicherheitshinweise gibt es?"],
            search_results=[],
            model_used=model_id,
            processing_time_ms=processing_time,
            tokens_used=ai_response.get("tokens_used", 0)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim AI-Test: {str(e)}"
        )

@router.post("/chat/ask", response_model=AskQuestionResponse)
async def ask_question(
    request: AskQuestionRequest,
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter),
    ai_service = Depends(get_ai_service)
):
    """Stellt eine Frage im RAG Chat.
    
    WICHTIG: Prüft ob Session existiert bevor Frage gestellt wird.
    """
    try:
        start_time = time.time()
        
        # Prüfe ob Session existiert (falls session_id angegeben)
        if request.session_id:
            session = rag_adapter.chat_session_repo.find_by_id(request.session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session {request.session_id} nicht gefunden"
                )
        
        # Erstelle Use Case mit echtem AI Service
        from ..infrastructure.ai_service import RAGAIService
        from contexts.documentupload.infrastructure.permission_service import SQLAlchemyWorkflowPermissionService
        # PHASE 1: AI Service mit RAG Chat Prompt Repository initialisieren
        ai_service = RAGAIService(rag_chat_prompt_repo=rag_adapter.rag_chat_prompt_repo)
        
        # RBAC Phase 2: Permission Service für Interest Group Filtering
        permission_service = SQLAlchemyWorkflowPermissionService(db_session)
        
        use_case = AskQuestionUseCase(
            chunk_repository=rag_adapter.document_chunk_repo,
            session_repository=rag_adapter.chat_session_repo,
            indexed_document_repository=rag_adapter.indexed_document_repo,
            vector_store=rag_adapter.vector_store,
            embedding_service=rag_adapter.embedding_service,
            multi_query_service=rag_adapter.multi_query_service,  # NEU: Aktiviert für Query Expansion
            ai_service=ai_service,  # Echter AI Service
            event_publisher=None,  # TODO: Implementiere EventPublisher
            message_repository=rag_adapter.chat_message_repo,
            permission_service=permission_service  # RBAC: Für Interest Group Filtering
        )
        
        # Führe Frage durch
        # Frontend sendet jetzt score_threshold im Bereich 0.0-0.02 (0-2%)
        # Dieser Wert passt direkt zu OpenAI Embeddings (Scores liegen bei 0.02-0.03)
        score_threshold = request.score_threshold if hasattr(request, 'score_threshold') else 0.01
        top_k = request.top_k if hasattr(request, 'top_k') else 10  # PHASE 0.1: top_k vom Frontend
        print(f"DEBUG ask_question: score_threshold={score_threshold}, top_k={top_k} (vom Frontend)")
        
        result = await use_case.execute(
            question=request.question,
            session_id=request.session_id,
            model_id=request.model if hasattr(request, 'model') else "gpt-4o-mini",
            filters=request.filters if hasattr(request, 'filters') else None,
            use_hybrid_search=request.use_hybrid_search if hasattr(request, 'use_hybrid_search') else True,
            use_multi_query=getattr(request, 'use_multi_query', False),  # NEU: MultiQuery-Option (User kann aktivieren)
            score_threshold=score_threshold,  # Direkter Wert vom Frontend (0.0-0.02)
            top_k=top_k  # PHASE 0.1: top_k vom Frontend
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Aktualisiere Metadaten mit processing_time_ms
        if result.metadata:
            result.metadata["processing_time_ms"] = processing_time
            # Speichere aktualisierte Metadaten
            result = rag_adapter.chat_message_repo.save(result)
        
        # Konvertiere SourceReference zu SourceReferenceResponse
        from ..interface.schemas import SourceReferenceResponse
        source_refs = []
        for ref in result.source_references:
            # WICHTIG: chunk_id ist ein String (z.B. "doc_14_page_1_text"), nicht eine Integer-ID
            # Verwende chunk_id direkt, keine Konvertierung zu int
            
            # NEU: Hole erweiterte Metadaten (falls vorhanden)
            extended_metadata = getattr(ref, '_extended_metadata', {})
            
            source_refs.append(SourceReferenceResponse(
                document_id=ref.document_id,
                document_title=ref.document_title,
                page_number=ref.page_number,
                chunk_id=ref.chunk_id,  # Verwende chunk_id direkt (String)
                preview_image_path=ref.preview_image_path,
                relevance_score=ref.relevance_score,
                text_excerpt=ref.text_excerpt or "",
                # NEU: Erweiterte Metadaten
                vector_score=extended_metadata.get('vector_score'),
                text_score=extended_metadata.get('text_score'),
                hybrid_score=extended_metadata.get('hybrid_score', ref.relevance_score),
                rank_position=extended_metadata.get('rank_position'),
                total_candidates=extended_metadata.get('total_candidates'),
                passed_rbac_filter=extended_metadata.get('passed_rbac_filter'),
                passed_score_threshold=extended_metadata.get('passed_score_threshold'),
                chunk_metadata=extended_metadata.get('chunk_metadata'),
                query_text=extended_metadata.get('query_text')  # NEU: Query-Text für Text-Highlighting (Phase 3)
            ))
        
        print(f"DEBUG Router: {len(source_refs)} Source References für Response vorbereitet")
        
        # Hole tokens_used aus Metadaten (falls vorhanden)
        tokens_used = result.metadata.get("tokens_used", 0) if result.metadata else 0
        
        return AskQuestionResponse(
            answer=result.content,
            source_references=source_refs,
            structured_data=None,
            suggested_questions=["Was sind die wichtigsten Schritte?", "Welche Sicherheitshinweise gibt es?"],
            search_results=[],
            model_used=request.model if hasattr(request, 'model') else "gpt-4o-mini",
            processing_time_ms=processing_time,
            tokens_used=tokens_used,
            message_id=result.id  # NEU: Message-ID für Prompt Viewer
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler bei der Frage: {str(e)}"
        )


@router.post("/chat/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: CreateSessionRequest,
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """Erstellt eine neue Chat-Session."""
    try:
        # Erstelle Use Case
        use_case = CreateChatSessionUseCase(
            session_repository=rag_adapter.chat_session_repo
        )
        
        # Führe Session-Erstellung durch
        session = use_case.execute(
            user_id=request.user_id,
            session_name=request.session_name
        )
        
        return ChatSessionResponse(
            id=session.id,
            session_name=session.session_name,
            created_at=session.created_at,
            last_activity=session.last_message_at,
            message_count=0  # TODO: Implementiere message_count
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler bei der Session-Erstellung: {str(e)}"
        )


@router.put("/chat/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    session_id: int,
    request: CreateSessionRequest,  # Wiederverwendung für session_name
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """Aktualisiert den Namen einer Chat-Session."""
    try:
        # Erstelle Use Case
        use_case = UpdateChatSessionUseCase(
            session_repository=rag_adapter.chat_session_repo
        )
        
        # Führe Session-Update durch
        session = use_case.execute(
            session_id=session_id,
            new_session_name=request.session_name
        )
        
        return ChatSessionResponse(
            id=session.id,
            session_name=session.session_name,
            created_at=session.created_at,
            last_activity=session.last_message_at,
            message_count=0  # TODO: Implementiere message_count
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler bei der Session-Aktualisierung: {str(e)}"
        )


@router.get("/chat/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(
    user_id: int = Query(..., description="User ID"),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """Ruft alle Chat-Sessions eines Users ab."""
    try:
        # Hole Sessions aus Repository
        sessions = rag_adapter.chat_session_repo.get_by_user_id(user_id)
        
        return [
            ChatSessionResponse(
                id=session.id,
                session_name=session.session_name,
                created_at=session.created_at,
                last_activity=session.last_message_at,
                message_count=0  # TODO: Implementiere message_count
            )
            for session in sessions
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Sessions: {str(e)}"
        )


@router.get("/documents/types/counts", response_model=Dict[int, int])
async def get_document_type_counts(
    document_type_ids: Optional[str] = Query(None, description="Komma-separierte Liste von Document Type IDs (optional, leer = alle)"),
    current_user: dict = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """Ruft die Anzahl indexierter Dokumente pro Document Type ab (RBAC-gefiltert)."""
    try:
        # Parse document_type_ids String zu List[int]
        parsed_ids = None
        if document_type_ids:
            try:
                parsed_ids = [int(id.strip()) for id in document_type_ids.split(',') if id.strip()]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="document_type_ids muss komma-separierte Liste von Integers sein"
                )
        
        # RBAC Multi-Level: Hole User-Level und Interest Groups
        from contexts.documentupload.infrastructure.permission_service import SQLAlchemyWorkflowPermissionService
        permission_service = SQLAlchemyWorkflowPermissionService(db_session)
        
        user_id = current_user.get('id') or current_user.get('user_id')
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID nicht gefunden in Token"
            )
        
        user_level = permission_service.get_user_level(user_id)
        
        # Interest Group Filtering: Level 1-3 filtern nach IGs, Level 4-5 sehen alles
        interest_group_ids = None
        if user_level < 4:
            interest_group_ids = permission_service.get_user_interest_groups(user_id)
        
        # Erstelle Use Case
        use_case = GetDocumentTypeCountsUseCase(
            indexed_document_repository=rag_adapter.indexed_document_repo
        )
        
        # Führe Abruf durch (mit RBAC-Filter)
        counts = use_case.execute(
            document_type_ids=parsed_ids,
            interest_group_ids=interest_group_ids
        )
        
        return counts
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Document Type Counts: {str(e)}"
        )


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: int = Path(..., description="Session ID"),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """Löscht eine Chat-Session."""
    try:
        # Lösche Session aus Repository
        success = rag_adapter.chat_session_repo.delete(session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session nicht gefunden"
            )
        
        return {"status": "success", "message": "Session gelöscht"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Löschen der Session: {str(e)}"
        )


@router.get("/chat/sessions/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: int = Path(..., description="Session ID"),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """Ruft die Chat-Historie einer Session ab."""
    try:
        # Erstelle Use Case
        use_case = GetChatHistoryUseCase(
            message_repository=rag_adapter.chat_message_repo
        )
        
        # Führe Abruf durch
        messages = use_case.execute(session_id=session_id)
        
        # Konvertiere Messages zu Response-Schemas (mit ai_model_used und source_references)
        from ..interface.schemas import SourceReferenceResponse
        message_responses = []
        for msg in messages:
            # Konvertiere source_references zu SourceReferenceResponse
            source_refs = []
            if msg.source_references:
                for ref in msg.source_references:
                    # WICHTIG: chunk_id ist ein String (z.B. "doc_14_page_1_text"), nicht eine Integer-ID
                    # Verwende chunk_id direkt, keine Konvertierung zu int
                    
                    # NEU: Hole erweiterte Metadaten (falls vorhanden)
                    extended_metadata = getattr(ref, '_extended_metadata', {})
                    
                    # NEU: Hole Query-Text aus Message-Metadaten (falls nicht in extended_metadata)
                    query_text = extended_metadata.get('query_text')
                    if not query_text and msg.metadata:
                        query_text = msg.metadata.get('query_text')
                    
                    source_refs.append(SourceReferenceResponse(
                        document_id=ref.document_id,
                        document_title=ref.document_title,
                        page_number=ref.page_number,
                        chunk_id=ref.chunk_id,  # Verwende chunk_id direkt (String)
                        preview_image_path=ref.preview_image_path,
                        relevance_score=ref.relevance_score,
                        text_excerpt=ref.text_excerpt or "",
                        # NEU: Erweiterte Metadaten
                        vector_score=extended_metadata.get('vector_score'),
                        text_score=extended_metadata.get('text_score'),
                        hybrid_score=extended_metadata.get('hybrid_score', ref.relevance_score),
                        rank_position=extended_metadata.get('rank_position'),
                        total_candidates=extended_metadata.get('total_candidates'),
                        passed_rbac_filter=extended_metadata.get('passed_rbac_filter'),
                        passed_score_threshold=extended_metadata.get('passed_score_threshold'),
                        chunk_metadata=extended_metadata.get('chunk_metadata'),
                        query_text=query_text  # NEU: Query-Text für Text-Highlighting (Phase 3)
                    ))
            
            message_responses.append(ChatMessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                source_references=source_refs if source_refs else None,  # WICHTIG: source_references konvertieren!
                structured_data=None,
                ai_model_used=msg.ai_model_used,  # WICHTIG: ai_model_used aus Entity übernehmen
                metadata=msg.metadata if msg.metadata else None,  # Metadaten für Transparency Layer
                created_at=msg.created_at
            ))
        
        # Hole Session-Info
        session_response = ChatSessionResponse(
            id=session_id,
            session_name=f"Session {session_id}",
            created_at=datetime.now(),
            last_activity=None,
            message_count=len(messages)
        )
        
        return ChatHistoryResponse(
            session=session_response,
            messages=message_responses,
            total_messages=len(messages)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Historie: {str(e)}"
        )


@router.post("/search", response_model=SearchDocumentsResponse)
async def search_documents(
    request: SearchDocumentsRequest,
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """Sucht in indexierten Dokumenten."""
    try:
        start_time = time.time()
        
        # Baue Filter
        filters = {}
        if request.document_type:
            filters['document_type'] = request.document_type
        if request.page_numbers:
            filters['page_numbers'] = request.page_numbers
        
        # Führe Suche durch
        if request.use_hybrid_search:
            search_results = rag_adapter.hybrid_search_service.search_with_reranking(
                query=request.query,
                top_k=request.top_k,
                score_threshold=request.score_threshold,
                filters=filters if filters else None
            )
        else:
            search_results = rag_adapter.hybrid_search_service.search(
                query=request.query,
                top_k=request.top_k,
                score_threshold=request.score_threshold,
                filters=filters if filters else None,
                use_hybrid=False
            )
        
        search_time = int((time.time() - start_time) * 1000)
        
        return SearchDocumentsResponse(
            results=search_results,
            total_results=len(search_results),
            query=request.query,
            filters_applied=filters,
            search_time_ms=search_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler bei der Suche: {str(e)}"
        )


@router.post("/documents/{document_id}/reindex", response_model=ReindexDocumentResponse)
async def reindex_document(
    document_id: int = Path(..., description="Document ID"),
    request: ReindexDocumentRequest = None,
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter),
    ai_service = Depends(get_ai_service)
):
    """Re-indexiert ein Dokument."""
    try:
        start_time = time.time()
        
        # Erstelle Use Case
        use_case = ReindexDocumentUseCase(
            indexed_document_repo=rag_adapter.indexed_document_repo
        )
        
        # Führe Re-Indexierung durch
        result = use_case.execute(indexed_document_id=document_id)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return ReindexDocumentResponse(
            success=True,
            document=result['document'],
            old_chunks_deleted=result['old_chunks_deleted'],
            new_chunks_created=result['new_chunks_created'],
            processing_time_ms=processing_time,
            message=f"Dokument erfolgreich re-indexiert. {result['old_chunks_deleted']} alte Chunks gelöscht, {result['new_chunks_created']} neue Chunks erstellt."
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler bei der Re-Indexierung: {str(e)}"
        )


@router.get("/system/info", response_model=SystemInfoResponse)
async def get_system_info(
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """Ruft System-Informationen ab."""
    try:
        system_info = rag_adapter.get_system_info()
        
        return SystemInfoResponse(
            vector_store=system_info['vector_store'],
            embedding_service=system_info['embedding_service'],
            repositories=system_info['repositories'],
            services=system_info['services'],
            total_documents=system_info.get('total_documents', 0),
            total_chunks=system_info.get('total_chunks', 0)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der System-Info: {str(e)}"
        )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """Führt einen Health Check durch."""
    try:
        health_status = rag_adapter.health_check()
        
        return HealthCheckResponse(
            overall_status=health_status['overall_status'],
            services=health_status['services'],
            errors=health_status['errors'],
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        return HealthCheckResponse(
            overall_status='unhealthy',
            services={},
            errors=[f"Health Check Fehler: {str(e)}"],
            timestamp=datetime.utcnow()
        )


# Zusätzliche Utility Endpoints
@router.get("/documents", response_model=List[IndexDocumentResponse])
async def list_indexed_documents(
    status_filter: Optional[str] = Query(None, description="Filter nach Status"),
    document_type: Optional[str] = Query(None, description="Filter nach Dokumenttyp"),
    pagination: PaginationParams = Depends(),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """Listet alle indexierten Dokumente auf."""
    try:
        if status_filter:
            documents = rag_adapter.indexed_document_repo.find_by_status(status_filter)
        elif document_type:
            documents = rag_adapter.indexed_document_repo.find_by_document_type(document_type)
        else:
            documents = rag_adapter.indexed_document_repo.find_all()
        
        # Pagination
        start_idx = (pagination.page - 1) * pagination.size
        end_idx = start_idx + pagination.size
        paginated_documents = documents[start_idx:end_idx]
        
        return [
            IndexDocumentResponse(
                success=True,
                document=IndexedDocumentResponse(
                    id=doc.id,
                    upload_document_id=doc.upload_document_id,
                    document_title="Test Document",
                    document_type="SOP",
                    status="indexed",
                    indexed_at=doc.indexed_at,
                    total_chunks=doc.total_chunks,
                    last_updated=doc.last_updated_at
                ),
                chunks_created=doc.total_chunks,
                processing_time_ms=0,
                message="Dokument erfolgreich indexiert"
            )
            for doc in paginated_documents
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Dokumente: {str(e)}"
        )


@router.get("/documents/{upload_document_id}/index-status", response_model=DocumentIndexStatusResponse)
async def get_document_index_status(
    upload_document_id: int = Path(..., description="Upload Document ID"),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """Prüft ob ein Dokument bereits in RAG indexiert ist."""
    try:
        indexed_doc = rag_adapter.indexed_document_repo.get_by_upload_document_id(upload_document_id)
        
        if indexed_doc:
            return DocumentIndexStatusResponse(
                is_indexed=True,
                indexed_document_id=indexed_doc.id,
                indexed_at=indexed_doc.indexed_at,
                total_chunks=indexed_doc.total_chunks
            )
        else:
            return DocumentIndexStatusResponse(
                is_indexed=False,
                indexed_document_id=None,
                indexed_at=None,
                total_chunks=None
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Prüfen des Indexierungs-Status: {str(e)}"
        )


@router.get("/statistics", response_model=UsageStatisticsResponse)
async def get_usage_statistics(
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """Ruft Nutzungsstatistiken ab."""
    try:
        stats = rag_adapter.get_usage_statistics()
        
        return UsageStatisticsResponse(
            documents=stats['documents'],
            chunks=stats['chunks'],
            vector_store=stats['vector_store'],
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Statistiken: {str(e)}"
        )


# ============================================================================
# CHUNK PREVIEW ENDPOINT (PHASE 2.1)
# ============================================================================

@router.get(
    "/chunks/{upload_document_id}",
    response_model=ChunksListResponse,
    summary="Get Chunks for Document",
    description="Hole alle Chunks für ein Dokument (Read-Only Vorschau)."
)
async def get_chunks_for_document(
    upload_document_id: int = Path(..., description="Upload Document ID"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """
    Hole alle Chunks für ein Dokument.
    
    **Returns:**
    - Liste aller Chunks mit Metadaten
    - Read-Only Vorschau (keine Edit-Funktionen)
    
    **RBAC:**
    - Level 1+: Alle User können Chunks sehen
    """
    try:
        # 1. Prüfe ob Dokument indexiert ist
        indexed_doc = rag_adapter.indexed_document_repo.get_by_upload_document_id(upload_document_id)
        
        if not indexed_doc:
            # Dokument nicht indexiert → keine Chunks
            return ChunksListResponse(
                document_id=upload_document_id,
                indexed_document_id=None,
                total_chunks=0,
                chunks=[]
            )
        
        # 2. Hole alle Chunks für dieses Dokument
        chunks = rag_adapter.document_chunk_repo.get_by_indexed_document_id(indexed_doc.id)
        
        # 3. Konvertiere zu Response Schema
        chunk_responses = []
        for chunk in chunks:
            chunk_responses.append(ChunkPreviewResponse(
                id=chunk.id,
                chunk_id=chunk.chunk_id,
                chunk_text=chunk.chunk_text,  # Vollständiger Chunk-Text (keine Kürzung - Frontend übernimmt Truncation)
                metadata=ChunkMetadataResponse(
                    page_numbers=chunk.metadata.page_numbers,
                    heading_hierarchy=chunk.metadata.heading_hierarchy,
                    chunk_type=chunk.metadata.chunk_type,
                    token_count=chunk.metadata.token_count,
                    sentence_count=chunk.metadata.sentence_count,
                    has_overlap=chunk.metadata.has_overlap,
                    overlap_sentence_count=chunk.metadata.overlap_sentence_count
                ),
                indexed_document_id=chunk.indexed_document_id,
                created_at=chunk.created_at
            ))
        
        return ChunksListResponse(
            document_id=upload_document_id,
            indexed_document_id=indexed_doc.id,
            total_chunks=len(chunk_responses),
            chunks=chunk_responses
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Chunks: {str(e)}"
        )


# ============================================================================
# CHUNK EDITOR ENDPOINTS (PHASE 2.2)
# ============================================================================

@router.put(
    "/chunks/{chunk_id}",
    response_model=ChunkPreviewResponse,
    summary="Edit Chunk",
    description="Bearbeite Chunk-Text (nur für Level 4+)."
)
async def edit_chunk(
    chunk_id: int = Path(..., description="Chunk ID"),
    request: EditChunkRequest = ...,
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """
    Bearbeite Chunk-Text.
    
    **RBAC:**
    - Level 4+: Nur QM-Mitarbeiter können Chunks bearbeiten
    """
    # RBAC Check
    user_level = current_user.get('level') if isinstance(current_user, dict) else getattr(current_user, 'level', 0)
    if user_level < 4:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur QM-Mitarbeiter (Level 4+) können Chunks bearbeiten"
        )
    
    try:
        use_case = EditChunkUseCase(rag_adapter.document_chunk_repo)
        updated_chunk = await use_case.execute(chunk_id, request.new_text)
        
        # Convert to Response
        return ChunkPreviewResponse(
            id=updated_chunk.id,
            chunk_id=updated_chunk.chunk_id,
            chunk_text=updated_chunk.chunk_text,
            metadata=ChunkMetadataResponse(
                page_numbers=updated_chunk.metadata.page_numbers,
                heading_hierarchy=updated_chunk.metadata.heading_hierarchy,
                chunk_type=updated_chunk.metadata.chunk_type,
                token_count=updated_chunk.metadata.token_count,
                sentence_count=updated_chunk.metadata.sentence_count,
                has_overlap=updated_chunk.metadata.has_overlap,
                overlap_sentence_count=updated_chunk.metadata.overlap_sentence_count
            ),
            indexed_document_id=updated_chunk.indexed_document_id,
            created_at=updated_chunk.created_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Bearbeiten des Chunks: {str(e)}"
        )


@router.delete(
    "/chunks/{chunk_id}",
    response_model=dict,
    summary="Delete Chunk",
    description="Lösche Chunk aus DB und Vector Store (nur für Level 4+)."
)
async def delete_chunk(
    chunk_id: int = Path(..., description="Chunk ID"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """
    Lösche Chunk.
    
    **RBAC:**
    - Level 4+: Nur QM-Mitarbeiter können Chunks löschen
    """
    # RBAC Check
    user_level = current_user.get('level') if isinstance(current_user, dict) else getattr(current_user, 'level', 0)
    if user_level < 4:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur QM-Mitarbeiter (Level 4+) können Chunks löschen"
        )
    
    try:
        use_case = DeleteChunkUseCase(
            chunk_repo=rag_adapter.document_chunk_repo,
            vector_store=rag_adapter.vector_store
        )
        success = await use_case.execute(chunk_id)
        
        return {"success": success, "message": f"Chunk {chunk_id} erfolgreich gelöscht"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Löschen des Chunks: {str(e)}"
        )


@router.post(
    "/chunks/{chunk_id}/split",
    response_model=dict,
    summary="Split Chunk",
    description="Splitte Chunk in zwei Teile (nur für Level 4+)."
)
async def split_chunk(
    chunk_id: int = Path(..., description="Chunk ID"),
    request: SplitChunkRequest = ...,
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """
    Splitte Chunk an gegebener Position.
    
    **RBAC:**
    - Level 4+: Nur QM-Mitarbeiter können Chunks splitten
    """
    # RBAC Check
    # WICHTIG: get_current_user gibt Dict mit 'user_level' zurück, nicht 'level'
    user_level = current_user.get('user_level') if isinstance(current_user, dict) else getattr(current_user, 'user_level', None) or getattr(current_user, 'level', None)
    if user_level is None:
        user_level = 1  # Default für unbekannte User
    if user_level < 4:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur QM-Mitarbeiter (Level 4+) können Chunks splitten"
        )
    
    try:
        use_case = SplitChunkUseCase(
            chunk_repo=rag_adapter.document_chunk_repo,
            vector_store=rag_adapter.vector_store,
            embedding_service=rag_adapter.embedding_service,
            indexed_document_repo=rag_adapter.indexed_document_repo
        )
        new_chunks = await use_case.execute(
            chunk_id, 
            request.split_position,
            overlap_sentences=request.overlap_sentences
        )
        
        return {
            "success": True,
            "message": f"Chunk erfolgreich gesplittet in {len(new_chunks)} Chunks",
            "new_chunks": [
                {
                    "id": c.id,
                    "chunk_id": c.chunk_id,
                    "chunk_text": c.chunk_text  # Vollständiger Chunk-Text
                }
                for c in new_chunks
            ]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Splitten des Chunks: {str(e)}"
        )


@router.post(
    "/chunks/merge",
    response_model=dict,
    summary="Merge Chunks",
    description="Führe mehrere Chunks zusammen (nur für Level 4+)."
)
async def merge_chunks(
    request: MergeChunksRequest = ...,
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """
    Führe Chunks zusammen.
    
    **RBAC:**
    - Level 4+: Nur QM-Mitarbeiter können Chunks zusammenführen
    """
    # RBAC Check
    user_level = current_user.get('level') if isinstance(current_user, dict) else getattr(current_user, 'level', 0)
    if user_level < 4:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur QM-Mitarbeiter (Level 4+) können Chunks zusammenführen"
        )
    
    try:
        use_case = MergeChunksUseCase(
            chunk_repo=rag_adapter.document_chunk_repo,
            vector_store=rag_adapter.vector_store,
            embedding_service=rag_adapter.embedding_service
        )
        merged_chunk = await use_case.execute(request.chunk_ids)
        
        return {
            "success": True,
            "message": f"{len(request.chunk_ids)} Chunks erfolgreich zusammengeführt",
            "merged_chunk": {
                "id": merged_chunk.id,
                "chunk_id": merged_chunk.chunk_id,
                "chunk_text": merged_chunk.chunk_text[:200] + "..." if len(merged_chunk.chunk_text) > 200 else merged_chunk.chunk_text
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Zusammenführen der Chunks: {str(e)}"
        )


# ============================================================================
# CHUNKING STRATEGY SELECTOR ENDPOINT (PHASE 2.3)
# ============================================================================

@router.get(
    "/chunking-strategies",
    response_model=ChunkingStrategiesResponse,
    summary="Get Available Chunking Strategies",
    description="Hole alle verfügbaren Chunking-Strategien mit Embedding-Provider-Info."
)
async def get_chunking_strategies(
    document_type: Optional[str] = Query(None, description="Optional: Dokumenttyp für Empfehlung"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session)
):
    """
    Hole alle verfügbaren Chunking-Strategien.
    
    **Dreistufige Embedding-Strategie:**
    1. OpenAI (1536 dim) - Beste Qualität
    2. Gemini (768 dim) - Gute Qualität, kostenlos
    3. SentenceTransformer (384 dim) - Lokal, kostenlos
    
    **Returns:**
    - Liste aller verfügbaren Strategien
    - Standard-Strategie
    - Empfehlung für Dokumenttyp (falls angegeben)
    """
    try:
        import os
        
        # Verfügbare Strategien basierend auf verfügbaren API Keys
        strategies = []
        
        # 1. OpenAI Strategy (1536 Dimensionen) - Beste Qualität
        has_openai_key = bool(os.getenv("OPENAI_GPT5_MINI_API_KEY") or os.getenv("OPENAI_API_KEY"))
        if has_openai_key:
            strategies.append(ChunkingStrategyOption(
                id="openai_1536",
                name="OpenAI (Premium)",
                description="Beste Qualität mit OpenAI Embeddings (1536 Dimensionen). Ideal für komplexe Dokumente und höchste Genauigkeit.",
                embedding_provider="openai",
                embedding_dimensions=1536,
                recommended_for=["SOP", "ARBEITSANWEISUNG", "PROZESS", "QUALITÄTSMANAGEMENT"],
                is_default=True
            ))
        
        # 2. Gemini Strategy (768 Dimensionen) - Gute Qualität, kostenlos
        has_gemini_key = bool(os.getenv("GOOGLE_AI_API_KEY"))
        if has_gemini_key:
            strategies.append(ChunkingStrategyOption(
                id="gemini_768",
                name="Google Gemini (Standard)",
                description="Gute Qualität mit Google Gemini Embeddings (768 Dimensionen). Kostenlos und schnell.",
                embedding_provider="gemini",
                embedding_dimensions=768,
                recommended_for=["FORMULAR", "FLUSSDIAGRAMM", "COMPLIANCE"],
                is_default=not has_openai_key  # Default wenn OpenAI nicht verfügbar
            ))
        
        # 3. SentenceTransformer Strategy (384 Dimensionen) - Lokal, kostenlos
        strategies.append(ChunkingStrategyOption(
            id="local_384",
            name="Local SentenceTransformer (Economy)",
            description="Lokale Embeddings mit SentenceTransformer (384 Dimensionen). Keine API-Kosten, offline verfügbar.",
            embedding_provider="local",
            embedding_dimensions=384,
            recommended_for=["EINFACHE_DOKUMENTE", "TEXT"],
            is_default=not has_openai_key and not has_gemini_key  # Default wenn keine APIs verfügbar
        ))
        
        # Bestimme Standard-Strategie
        default_strategy = next((s.id for s in strategies if s.is_default), strategies[0].id if strategies else "local_384")
        
        # Empfehlung für Dokumenttyp
        document_type_suggestion = None
        if document_type:
            # Finde beste Strategie für Dokumenttyp
            doc_type_upper = document_type.upper()
            for strategy in strategies:
                if doc_type_upper in [r.upper() for r in strategy.recommended_for]:
                    document_type_suggestion = strategy.id
                    break
            
            # Fallback: Verwende Standard
            if not document_type_suggestion:
                document_type_suggestion = default_strategy
        
        return ChunkingStrategiesResponse(
            strategies=strategies,
            default_strategy=default_strategy,
            document_type_suggestion=document_type_suggestion
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Chunking-Strategien: {str(e)}"
        )


# ============================================================================
# RAG CHAT PROMPT VIEWER ENDPOINT (PHASE 3.1)
# ============================================================================

@router.get(
    "/chat/messages/{message_id}/prompt",
    response_model=PromptViewerResponse,
    summary="Get Prompt for Chat Message",
    description="Hole den verwendeten Prompt für eine Chat-Message (Read-Only)."
)
async def get_prompt_for_message(
    message_id: int = Path(..., description="Chat Message ID"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """
    Hole den verwendeten Prompt für eine Chat-Message.
    
    Rekonstruiert den Prompt basierend auf:
    - User-Frage
    - Verwendete Chunks (aus Source References)
    - Dokumenttyp (aus Chunk-Metadaten)
    - AI-Modell
    
    **RBAC:**
    - Level 1+: Alle User können Prompts sehen (Transparenz)
    """
    try:
        # 1. Lade Chat-Message
        message = rag_adapter.chat_message_repo.get_by_id(message_id)
        
        # PHASE 3: Prüfe ob Prompt bereits in metadata gespeichert ist
        if message.metadata and message.metadata.get("prompt_text"):
            print(f"DEBUG get_prompt_for_message: Verwende gespeicherten Prompt aus metadata")
            # Hole User-Frage (vorherige User-Message)
            all_messages = rag_adapter.chat_message_repo.get_by_session_id(message.session_id)
            sorted_messages = sorted(all_messages, key=lambda m: m.id)
            current_index = None
            for i, msg in enumerate(sorted_messages):
                if msg.id == message_id:
                    current_index = i
                    break
            user_question = None
            if current_index is not None:
                for i in range(current_index - 1, -1, -1):
                    if sorted_messages[i].role == "user":
                        user_question = sorted_messages[i].content
                        break
            
            # Hole context_chunks aus Source References (für Anzeige)
            context_chunks = []
            if message.source_references:
                for source_ref in message.source_references:
                    chunk = rag_adapter.document_chunk_repo.get_by_chunk_id(source_ref.chunk_id)
                    if chunk:
                        context_chunks.append({
                            "chunk_id": chunk.chunk_id,
                            "chunk_text": chunk.chunk_text,
                            "metadata": {
                                "page_numbers": chunk.metadata.page_numbers,
                                "heading_hierarchy": chunk.metadata.heading_hierarchy,
                                "chunk_type": chunk.metadata.chunk_type
                            }
                        })
            
            # Hole document_type aus Chunk-Metadaten
            document_type = None
            if context_chunks:
                first_chunk = context_chunks[0]
                metadata = first_chunk.get("metadata", {})
                document_type = metadata.get("document_type") or metadata.get("document_type_name")
            
            return PromptViewerResponse(
                message_id=message_id,
                question=user_question or "Unbekannt",
                prompt_text=message.metadata["prompt_text"],  # Verwende gespeicherten Prompt
                context_chunks=context_chunks,
                document_type=document_type,
                model_used=message.ai_model_used or "unknown",
                tokens_used=message.metadata.get("tokens_used")
            )
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat Message {message_id} nicht gefunden"
            )
        
        # PHASE 3: Prüfe ob Prompt bereits in metadata gespeichert ist (Priorität!)
        if message.metadata and message.metadata.get("prompt_text"):
            print(f"DEBUG get_prompt_for_message: Verwende gespeicherten Prompt aus metadata")
            # Hole User-Frage (vorherige User-Message)
            all_messages = rag_adapter.chat_message_repo.get_by_session_id(message.session_id)
            sorted_messages = sorted(all_messages, key=lambda m: m.id)
            current_index = None
            for i, msg in enumerate(sorted_messages):
                if msg.id == message_id:
                    current_index = i
                    break
            user_question = None
            if current_index is not None:
                for i in range(current_index - 1, -1, -1):
                    if sorted_messages[i].role == "user":
                        user_question = sorted_messages[i].content
                        break
            
            # Hole context_chunks aus Source References (für Anzeige)
            context_chunks = []
            if message.source_references:
                for source_ref in message.source_references:
                    chunk = rag_adapter.document_chunk_repo.get_by_chunk_id(source_ref.chunk_id)
                    if chunk:
                        context_chunks.append({
                            "chunk_id": chunk.chunk_id,
                            "chunk_text": chunk.chunk_text,
                            "metadata": {
                                "page_numbers": chunk.metadata.page_numbers,
                                "heading_hierarchy": chunk.metadata.heading_hierarchy,
                                "chunk_type": chunk.metadata.chunk_type
                            }
                        })
            
            # Hole document_type aus Chunk-Metadaten
            document_type = None
            if context_chunks:
                first_chunk = context_chunks[0]
                chunk_metadata = first_chunk.get("metadata", {})
                document_type = chunk_metadata.get("document_type") or chunk_metadata.get("document_type_name")
            
            return PromptViewerResponse(
                message_id=message_id,
                question=user_question or "Unbekannt",
                prompt_text=message.metadata["prompt_text"],  # Verwende gespeicherten Prompt
                context_chunks=context_chunks,
                document_type=document_type,
                model_used=message.ai_model_used or "unknown",
                tokens_used=message.metadata.get("tokens_used")
            )
        
        # 2. Prüfe ob Message vom aktuellen User ist (RBAC)
        session = rag_adapter.chat_session_repo.get_by_id(message.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {message.session_id} nicht gefunden"
            )
        
        user_level = current_user.get('level') if isinstance(current_user, dict) else getattr(current_user, 'level', 0)
        user_id = current_user.get('id') if isinstance(current_user, dict) else getattr(current_user, 'id', None)
        
        # Sicherstellen dass user_level ein int ist (Fallback zu 1 wenn None)
        if user_level is None:
            user_level = 1
        
        # Level 4+ können alle Prompts sehen, Level 1-3 nur eigene
        if user_level < 4 and session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur QM-Mitarbeiter (Level 4+) können Prompts anderer User sehen"
            )
        
        # 3. Rekonstruiere Prompt
        # Nur für Assistant-Messages (User-Messages haben keinen Prompt)
        if message.role != "assistant":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt kann nur für Assistant-Messages abgerufen werden"
            )
        
        # 4. Hole vorherige User-Message (die Frage)
        # Finde die letzte User-Message vor dieser Assistant-Message
        all_messages = rag_adapter.chat_message_repo.get_by_session_id(message.session_id)
        # Sortiere Messages nach ID (chronologisch)
        sorted_messages = sorted(all_messages, key=lambda m: m.id)
        
        # Finde Index der aktuellen Assistant-Message
        current_index = None
        for i, msg in enumerate(sorted_messages):
            if msg.id == message_id:
                current_index = i
                break
        
        if current_index is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assistant-Message nicht in Session gefunden"
            )
        
        # Suche rückwärts nach User-Message vor dieser Assistant-Message
        user_question = None
        for i in range(current_index - 1, -1, -1):
            if sorted_messages[i].role == "user":
                user_question = sorted_messages[i].content
                break
        
        if not user_question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Keine User-Frage für diese Assistant-Message gefunden"
            )
        
        # 5. Rekonstruiere Chunks aus Source References
        context_chunks = []
        document_type = None
        
        print(f"DEBUG get_prompt_for_message: Message {message_id} hat {len(message.source_references) if message.source_references else 0} Source References")
        
        if message.source_references:
            for i, source_ref in enumerate(message.source_references, 1):
                # Hole Chunk aus DB
                # WICHTIG: source_ref.chunk_id ist ein String (z.B. "doc_14_page_1_text"), nicht eine Integer-ID
                # Verwende get_by_chunk_id statt get_by_id
                print(f"DEBUG get_prompt_for_message: Suche Chunk {i} mit chunk_id='{source_ref.chunk_id}'")
                chunk = rag_adapter.document_chunk_repo.get_by_chunk_id(source_ref.chunk_id)
                if chunk:
                    print(f"DEBUG get_prompt_for_message: Chunk {i} gefunden: {chunk.chunk_id}, page={chunk.metadata.page_numbers}")
                    chunk_dict = {
                        "chunk_id": chunk.chunk_id,
                        "chunk_text": chunk.chunk_text,
                        "metadata": {
                            "page_numbers": chunk.metadata.page_numbers,
                            "heading_hierarchy": chunk.metadata.heading_hierarchy,
                            "chunk_type": chunk.metadata.chunk_type,
                            "document_type": None  # Wird aus Metadaten extrahiert
                        }
                    }
                    context_chunks.append(chunk_dict)
                    print(f"DEBUG get_prompt_for_message: Chunk {i} zu context_chunks hinzugefügt (Total: {len(context_chunks)})")
                    
                    # Extrahiere document_type aus Metadaten (falls noch nicht gesetzt)
                    if not document_type:
                        # Versuche document_type aus IndexedDocument zu holen
                        indexed_doc = rag_adapter.indexed_document_repo.get_by_id(chunk.indexed_document_id)
                        if indexed_doc:
                            # Hole document_type aus upload_document
                            from backend.app.database import get_db
                            from sqlalchemy import text
                            db = next(get_db())
                            result = db.execute(text('''
                                SELECT dt.name
                                FROM upload_documents ud
                                JOIN document_types dt ON ud.document_type_id = dt.id
                                WHERE ud.id = :upload_doc_id
                            '''), {"upload_doc_id": indexed_doc.upload_document_id})
                            row = result.fetchone()
                            if row:
                                document_type = row[0]
                else:
                    print(f"DEBUG get_prompt_for_message: ⚠️ Chunk {i} NICHT gefunden für chunk_id='{source_ref.chunk_id}'")
        
        # 6. Rekonstruiere Prompt mit AI Service
        from contexts.ragintegration.infrastructure.ai_service import RAGAIService
        # WICHTIG: Verwende rag_chat_prompt_repo für Custom Prompts
        ai_service = RAGAIService(rag_chat_prompt_repo=rag_adapter.rag_chat_prompt_repo)
        
        # Hole document_type_id aus Metadaten (falls vorhanden)
        document_type_id = None
        if context_chunks:
            first_chunk = context_chunks[0]
            chunk_metadata = first_chunk.get("metadata", {})
            document_type_id = chunk_metadata.get("document_type_id")
            if not document_type_id:
                # Versuche document_type_id aus IndexedDocument zu holen
                chunk = rag_adapter.document_chunk_repo.get_by_chunk_id(context_chunks[0].get("chunk_id"))
                if chunk:
                    indexed_doc = rag_adapter.indexed_document_repo.get_by_id(chunk.indexed_document_id)
                    if indexed_doc:
                        # Hole document_type_id aus upload_document
                        from backend.app.database import get_db
                        from sqlalchemy import text
                        db = next(get_db())
                        result = db.execute(text('''
                            SELECT ud.document_type_id
                            FROM upload_documents ud
                            WHERE ud.id = :upload_doc_id
                        '''), {"upload_doc_id": indexed_doc.upload_document_id})
                        row = result.fetchone()
                        if row:
                            document_type_id = row[0]
        
        # Baue Kontext-String
        print(f"DEBUG get_prompt_for_message: Total context_chunks: {len(context_chunks)}")
        context_text = ai_service._build_structured_context_from_chunks(context_chunks) if context_chunks else ""
        print(f"DEBUG get_prompt_for_message: context_text Länge: {len(context_text)} Zeichen")
        print(f"DEBUG get_prompt_for_message: document_type={document_type}, document_type_id={document_type_id}")
        
        # Erstelle Prompt
        prompt_text = ai_service._create_structured_rag_prompt(
            question=user_question,
            context=context_text,
            document_type=document_type,
            document_type_id=document_type_id  # WICHTIG: Für Custom Prompt Lookup
        )
        print(f"DEBUG get_prompt_for_message: Prompt erstellt, Länge: {len(prompt_text)} Zeichen")
        
        return PromptViewerResponse(
            message_id=message_id,
            question=user_question,
            prompt_text=prompt_text,
            context_chunks=context_chunks,
            document_type=document_type,
            model_used=message.ai_model_used or "unknown",
            tokens_used=None  # TODO: Speichere tokens_used in ChatMessage
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen des Prompts: {str(e)}"
        )


# ============================================================================
# RAG FEEDBACK ENDPOINTS (PHASE 4.1)
# ============================================================================

@router.post(
    "/chat/feedback",
    response_model=FeedbackResponse,
    summary="Submit Feedback for Chat Message",
    description="Gebe Feedback zu einer RAG Chat-Antwort ab."
)
async def submit_feedback(
    request: SubmitFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """
    Speichere User Feedback für eine RAG Chat-Antwort.
    
    **RBAC:**
    - Level 1+: Alle User können Feedback geben
    - Ein User kann nur einmal pro Message Feedback geben
    """
    try:
        from contexts.ragintegration.infrastructure.repositories import SQLAlchemyRAGFeedbackRepository
        from contexts.ragintegration.application.use_cases import SubmitFeedbackUseCase
        from contexts.documentupload.interface.workflow_router import get_event_publisher
        
        # Setup Repository
        feedback_repo = SQLAlchemyRAGFeedbackRepository(db_session)
        
        # Get User ID
        user_id = current_user.get('id') if isinstance(current_user, dict) else getattr(current_user, 'id', None)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID nicht gefunden"
            )
        
        # Get Event Publisher (Singleton)
        event_publisher = get_event_publisher()
        
        # Execute Use Case
        use_case = SubmitFeedbackUseCase(
            feedback_repo=feedback_repo,
            event_publisher=event_publisher
        )
        
        saved_feedback = await use_case.execute(
            chat_message_id=request.chat_message_id,
            user_id=user_id,
            rating=request.rating,
            comment=request.comment
        )
        
        return FeedbackResponse(
            id=saved_feedback.id,
            chat_message_id=saved_feedback.chat_message_id,
            user_id=saved_feedback.user_id,
            rating=saved_feedback.rating,
            comment=saved_feedback.comment,
            submitted_at=saved_feedback.submitted_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Speichern des Feedbacks: {str(e)}"
        )


@router.get(
    "/chat/feedback/statistics",
    response_model=FeedbackStatisticsResponse,
    summary="Get Feedback Statistics",
    description="Hole Feedback-Statistiken für Analytics."
)
async def get_feedback_statistics(
    chat_message_id: Optional[int] = Query(None, description="Optional: Filter nach Chat Message"),
    user_id: Optional[int] = Query(None, description="Optional: Filter nach User"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session)
):
    """
    Hole Feedback-Statistiken.
    
    **RBAC:**
    - Level 1+: Alle User können eigene Statistiken sehen
    - Level 4+: QM-Mitarbeiter können alle Statistiken sehen
    """
    try:
        from contexts.ragintegration.infrastructure.repositories import SQLAlchemyRAGFeedbackRepository
        from contexts.ragintegration.application.use_cases import GetFeedbackStatisticsUseCase
        
        # RBAC: Level 1-3 können nur eigene Statistiken sehen
        user_level = current_user.get('level') if isinstance(current_user, dict) else getattr(current_user, 'level', 0)
        current_user_id = current_user.get('id') if isinstance(current_user, dict) else getattr(current_user, 'id', None)
        
        if user_level < 4 and user_id and user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur QM-Mitarbeiter (Level 4+) können Statistiken anderer User sehen"
            )
        
        # Setup Repository & Use Case
        feedback_repo = SQLAlchemyRAGFeedbackRepository(db_session)
        use_case = GetFeedbackStatisticsUseCase(feedback_repo)
        
        stats = await use_case.execute(
            chat_message_id=chat_message_id,
            user_id=user_id
        )
        
        return FeedbackStatisticsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Statistiken: {str(e)}"
        )


@router.get(
    "/chat/messages/{message_id}/feedback",
    response_model=Optional[FeedbackResponse],
    summary="Get Feedback for Chat Message",
    description="Hole Feedback für eine Chat-Message (falls vorhanden)."
)
async def get_feedback_for_message(
    message_id: int = Path(..., description="Chat Message ID"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session)
):
    """
    Hole Feedback für eine Chat-Message.
    
    **RBAC:**
    - Level 1+: Alle User können eigenes Feedback sehen
    - Level 4+: QM-Mitarbeiter können alle Feedbacks sehen
    """
    try:
        from contexts.ragintegration.infrastructure.repositories import SQLAlchemyRAGFeedbackRepository
        
        # Setup Repository
        feedback_repo = SQLAlchemyRAGFeedbackRepository(db_session)
        
        # Get User ID
        user_id = current_user.get('id') if isinstance(current_user, dict) else getattr(current_user, 'id', None)
        user_level = current_user.get('level') if isinstance(current_user, dict) else getattr(current_user, 'level', 0)
        
        # Sicherstellen dass user_level ein int ist (Fallback zu 1 wenn None)
        if user_level is None:
            user_level = 1
        
        # Hole Feedback (nur für aktuellen User, außer Level 4+)
        feedback = await feedback_repo.get_by_message_id(
            chat_message_id=message_id,
            user_id=user_id if user_level < 4 else None
        )
        
        if not feedback:
            return None
        
        return FeedbackResponse(
            id=feedback.id,
            chat_message_id=feedback.chat_message_id,
            user_id=feedback.user_id,
            rating=feedback.rating,
            comment=feedback.comment,
            submitted_at=feedback.submitted_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen des Feedbacks: {str(e)}"
        )


# ============================================================================
# RAG ANALYTICS ENDPOINTS (PHASE 4.2)
# ============================================================================

@router.get(
    "/analytics",
    response_model=RAGAnalyticsResponse,
    summary="Get RAG Analytics",
    description="Hole umfassende RAG Analytics für Dashboard."
)
async def get_rag_analytics(
    start_date: Optional[str] = Query(None, description="Optional: Start-Datum (ISO format)"),
    end_date: Optional[str] = Query(None, description="Optional: End-Datum (ISO format)"),
    user_id: Optional[int] = Query(None, description="Optional: Filter nach User ID"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session)
):
    """
    Hole umfassende RAG Analytics.
    
    **RBAC:**
    - Level 1+: Alle User können eigene Analytics sehen
    - Level 4+: QM-Mitarbeiter können alle Analytics sehen
    """
    try:
        from contexts.ragintegration.infrastructure.repositories import (
            SQLAlchemyRAGFeedbackRepository,
            SQLAlchemyRAGAuditLogRepository
        )
        from contexts.ragintegration.application.use_cases import GetRAGAnalyticsUseCase
        from contexts.ragintegration.infrastructure.repositories import (
            SQLAlchemyChatMessageRepository,
            SQLAlchemyIndexedDocumentRepository
        )
        from datetime import datetime
        
        # RBAC: Level 1-3 können nur eigene Analytics sehen
        user_level = current_user.get('level') if isinstance(current_user, dict) else getattr(current_user, 'level', 0)
        current_user_id = current_user.get('id') if isinstance(current_user, dict) else getattr(current_user, 'id', None)
        
        # Sicherstellen dass user_level ein int ist (Fallback zu 1 wenn None)
        if user_level is None:
            user_level = 1
        
        if user_level < 4 and user_id and user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur QM-Mitarbeiter (Level 4+) können Analytics anderer User sehen"
            )
        
        # Parse Dates und normalisiere auf timezone-naive (DB verwendet timezone-naive)
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            start_dt = start_dt.replace(tzinfo=None) if start_dt.tzinfo else start_dt
        else:
            start_dt = None
            
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            end_dt = end_dt.replace(tzinfo=None) if end_dt.tzinfo else end_dt
        else:
            end_dt = None
        
        # Setup Repositories
        feedback_repo = SQLAlchemyRAGFeedbackRepository(db_session)
        audit_repo = SQLAlchemyRAGAuditLogRepository(db_session)
        chat_message_repo = SQLAlchemyChatMessageRepository(db_session)
        indexed_document_repo = SQLAlchemyIndexedDocumentRepository(db_session)
        
        # NEU: Training Data Repository für SHAP-Statistiken (Phase 3)
        from contexts.ragintegration.infrastructure.repositories import SQLAlchemyTrainingDataRepository
        training_data_repo = SQLAlchemyTrainingDataRepository(db_session)
        
        # Execute Use Case
        use_case = GetRAGAnalyticsUseCase(
            feedback_repo=feedback_repo,
            audit_repo=audit_repo,
            chat_message_repo=chat_message_repo,
            indexed_document_repo=indexed_document_repo,
            training_data_repo=training_data_repo  # NEU: Training Data Repository
        )
        
        analytics = await use_case.execute(
            start_date=start_dt,
            end_date=end_dt,
            user_id=user_id if user_level >= 4 else current_user_id
        )
        
        return RAGAnalyticsResponse(**analytics)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ungültiges Datum: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Analytics: {str(e)}"
        )


# ============================================================================
# RAG CHAT PROMPT ENDPOINTS (PHASE 1)
# ============================================================================

@router.get(
    "/chat/prompts/{document_type_id}",
    response_model=RAGChatPromptResponse,
    summary="Get RAG Chat Prompt",
    description="Hole RAG Chat Prompt für einen Dokumenttyp (Custom oder Standard)."
)
async def get_rag_chat_prompt(
    document_type_id: int = Path(..., description="Document Type ID"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter),
    ai_service = Depends(get_ai_service)
):
    """Hole RAG Chat Prompt für einen Dokumenttyp.
    
    Priorität:
    1. Custom Prompt (aus rag_chat_prompts)
    2. Standard Prompt (aus prompt_templates + AI Service)
    3. Generischer Prompt (Fallback)
    """
    try:
        # Hole Document Type Name für Standard-Prompt
        from backend.app.models import DocumentTypeModel
        doc_type_model = db_session.query(DocumentTypeModel).filter(
            DocumentTypeModel.id == document_type_id
        ).first()
        
        if not doc_type_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document Type {document_type_id} nicht gefunden"
            )
        
        document_type_name = doc_type_model.name
        
        # Erstelle Use Case
        from ..infrastructure.repositories import SQLAlchemyRAGChatPromptRepository
        from ..infrastructure.ai_service import RAGAIService
        
        rag_chat_prompt_repo = SQLAlchemyRAGChatPromptRepository(db_session)
        ai_service_instance = RAGAIService()
        
        use_case = GetRAGChatPromptUseCase(
            rag_chat_prompt_repo=rag_chat_prompt_repo,
            ai_service=ai_service_instance
        )
        
        # Hole Prompt
        prompt_text = use_case.execute(document_type_id, document_type_name)
        
        # Wenn Custom Prompt vorhanden, hole vollständige Entity
        custom_prompt = rag_chat_prompt_repo.get_by_document_type_id(document_type_id)
        
        # WICHTIG: Erstelle vollständigen Prompt (wie er tatsächlich verwendet wird)
        # mit Platzhaltern für {context} und {question}
        system_prompt_prefix = """Du bist ein Experte für Qualitätsmanagement und medizinische Dokumentation. Beantworte die folgende Frage basierend auf den bereitgestellten strukturierten Dokument-Auszügen.

KONTEXT (aus indexierten Dokumenten mit Metadaten):
{context}

FRAGE: {question}

"""
        system_prompt_suffix = """

ANTWORT (strukturiert mit Metadaten-Referenzen direkt im Text):"""
        
        if custom_prompt:
            # Custom Prompt vorhanden - prüfe ob bereits vollständiger Prompt (mit {context} und {question})
            # oder nur Basis-Teil
            if "{context}" in custom_prompt.prompt_text and "{question}" in custom_prompt.prompt_text:
                # Vollständiger Prompt (User hat System-Teil bereits bearbeitet)
                full_prompt_text = custom_prompt.prompt_text
            else:
                # Nur Basis-Teil - füge System-Teil hinzu (für Rückwärtskompatibilität)
                full_prompt_text = system_prompt_prefix + custom_prompt.prompt_text + system_prompt_suffix
            
            return RAGChatPromptResponse(
                id=custom_prompt.id,
                document_type_id=custom_prompt.document_type_id,
                prompt_text=full_prompt_text,  # Vollständiger Prompt
                multi_query_prompt_text=custom_prompt.multi_query_prompt_text,
                is_custom=True,
                created_by_user_id=custom_prompt.created_by_user_id,
                created_at=custom_prompt.created_at,
                updated_at=custom_prompt.updated_at
            )
        else:
            # Standard Prompt (aus AI Service)
            if prompt_text:
                # Erstelle vollständigen Prompt mit System-Teil
                full_prompt_text = system_prompt_prefix + prompt_text + system_prompt_suffix
                return RAGChatPromptResponse(
                    id=0,
                    document_type_id=document_type_id,
                    prompt_text=full_prompt_text,  # Vollständiger Prompt mit System-Teil
                    multi_query_prompt_text=None,
                    is_custom=False,
                    created_by_user_id=0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            else:
                # Fallback: Generischer Prompt
                generic_prompt = ai_service_instance._get_generic_prompt_instructions()
                full_prompt_text = system_prompt_prefix + generic_prompt + system_prompt_suffix
                return RAGChatPromptResponse(
                    id=0,
                    document_type_id=document_type_id,
                    prompt_text=full_prompt_text,  # Vollständiger Prompt mit System-Teil
                    multi_query_prompt_text=None,
                    is_custom=False,
                    created_by_user_id=0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen des Prompts: {str(e)}"
        )


@router.post(
    "/chat/prompts/{document_type_id}",
    response_model=RAGChatPromptResponse,
    summary="Save RAG Chat Prompt",
    description="Speichere RAG Chat Prompt für einen Dokumenttyp (Level 4+)."
)
async def save_rag_chat_prompt(
    document_type_id: int = Path(..., description="Document Type ID"),
    request: SaveRAGChatPromptRequest = ...,
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """Speichere RAG Chat Prompt (Level 4+).
    
    Speichert einen globalen, dokumenttyp-spezifischen RAG Chat Prompt.
    """
    try:
        # RBAC: Prüfe User Level
        user_id = current_user.get('id', 1) if isinstance(current_user, dict) else getattr(current_user, 'id', 1)
        user_level = current_user.get('user_level', 1) if isinstance(current_user, dict) else getattr(current_user, 'user_level', 1)
        
        if user_level < 4:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Level 4+ (QM/QM Admin) können RAG Chat Prompts anpassen"
            )
        
        # Erstelle Use Case
        from ..infrastructure.repositories import SQLAlchemyRAGChatPromptRepository
        
        rag_chat_prompt_repo = SQLAlchemyRAGChatPromptRepository(db_session)
        
        # WICHTIG: Speichere den vollständigen Prompt (inkl. System-Prompt-Teil, wenn vorhanden)
        # Der User kann den vollständigen Prompt bearbeiten, inkl. System-Prompt-Teil
        use_case = SaveRAGChatPromptUseCase(rag_chat_prompt_repo=rag_chat_prompt_repo)
        
        # Speichere den vollständigen Prompt (wie der User ihn eingegeben hat)
        saved_prompt = use_case.execute(
            document_type_id=document_type_id,
            prompt_text=request.prompt_text.strip(),  # Vollständiger Prompt (inkl. System-Teil, falls vorhanden)
            multi_query_prompt_text=request.multi_query_prompt_text,
            user_id=user_id,
            user_level=user_level
        )
        
        return RAGChatPromptResponse(
            id=saved_prompt.id,
            document_type_id=saved_prompt.document_type_id,
            prompt_text=saved_prompt.prompt_text,  # Vollständiger Prompt (wie gespeichert)
            multi_query_prompt_text=saved_prompt.multi_query_prompt_text,
            is_custom=True,
            created_by_user_id=saved_prompt.created_by_user_id,
            created_at=saved_prompt.created_at,
            updated_at=saved_prompt.updated_at
        )
    
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Speichern des Prompts: {str(e)}"
        )


@router.delete(
    "/chat/prompts/{document_type_id}",
    response_model=Dict[str, Any],
    summary="Delete RAG Chat Prompt",
    description="Lösche RAG Chat Prompt (zurücksetzen auf Standard, Level 4+)."
)
async def delete_rag_chat_prompt(
    document_type_id: int = Path(..., description="Document Type ID"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """Lösche RAG Chat Prompt (zurücksetzen auf Standard, Level 4+).
    
    Löscht einen Custom Prompt, sodass wieder der Standard-Prompt verwendet wird.
    """
    try:
        # RBAC: Prüfe User Level
        user_id = current_user.get('id', 1) if isinstance(current_user, dict) else getattr(current_user, 'id', 1)
        user_level = current_user.get('user_level', 1) if isinstance(current_user, dict) else getattr(current_user, 'user_level', 1)
        
        if user_level < 4:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Level 4+ (QM/QM Admin) können RAG Chat Prompts löschen"
            )
        
        # Erstelle Use Case
        from ..infrastructure.repositories import SQLAlchemyRAGChatPromptRepository
        
        rag_chat_prompt_repo = SQLAlchemyRAGChatPromptRepository(db_session)
        
        use_case = DeleteRAGChatPromptUseCase(rag_chat_prompt_repo=rag_chat_prompt_repo)
        
        # Lösche Prompt
        deleted = use_case.execute(
            document_type_id=document_type_id,
            user_id=user_id,
            user_level=user_level
        )
        
        if deleted:
            return {
                "success": True,
                "message": f"RAG Chat Prompt für Document Type {document_type_id} wurde gelöscht (zurückgesetzt auf Standard)"
            }
        else:
            return {
                "success": False,
                "message": f"Kein Custom Prompt für Document Type {document_type_id} gefunden"
            }
    
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Löschen des Prompts: {str(e)}"
        )


# Exception Handler (muss in der Haupt-App registriert werden)
def rag_exception_handler(request, exc):
    """Exception Handler für RAG-spezifische Fehler."""
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.detail,
                message=f"RAG API Error: {exc.detail}",
                timestamp=datetime.utcnow()
            ).dict()
        )
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            message="An unexpected error occurred in the RAG system",
            timestamp=datetime.utcnow()
        ).dict()
    )
