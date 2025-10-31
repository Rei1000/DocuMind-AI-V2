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
    GetDocumentTypeCountsUseCase, ReindexDocumentUseCase
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
    openai_api_key = os.getenv("OPENAI_API_KEY", "test-key")
    
    # Hole Database Session
    db_session = next(get_db())
    
    # Erstelle RAG Adapter
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
        
        # Erstelle Use Case
        use_case = IndexApprovedDocumentUseCase(
            indexed_document_repo=rag_adapter.indexed_document_repo,
            chunk_repo=rag_adapter.document_chunk_repo,
            vision_extractor=rag_adapter.vision_extractor,
            chunking_service=rag_adapter.chunking_service,
            embedding_service=rag_adapter.embedding_service,
            vector_store=rag_adapter.vector_store,
            event_publisher=None  # TODO: Implementiere Event Publisher
        )
        
        # Hole den echten Dokumenttyp aus der Datenbank
        from backend.app.database import get_db
        from sqlalchemy import text
        
        db_session = next(get_db())
        doc_type_result = db_session.execute(text('''
            SELECT dt.name 
            FROM upload_documents ud 
            JOIN document_types dt ON ud.document_type_id = dt.id 
            WHERE ud.id = :doc_id
        '''), {"doc_id": request.upload_document_id})
        
        doc_type_row = doc_type_result.fetchone()
        document_type = doc_type_row[0] if doc_type_row else "SOP"
        print(f"DEBUG: Document type: {document_type}")
        
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
            message = f"Dokument erfolgreich indexiert. {result.get('total_chunks', 0)} Chunks erstellt."
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
        ai_service = RAGAIService()
        
        use_case = AskQuestionUseCase(
            chunk_repository=rag_adapter.document_chunk_repo,
            session_repository=rag_adapter.chat_session_repo,
            indexed_document_repository=rag_adapter.indexed_document_repo,
            vector_store=rag_adapter.vector_store,
            embedding_service=rag_adapter.embedding_service,
            multi_query_service=None,  # TODO: Implementiere MultiQueryService
            ai_service=ai_service,  # Echter AI Service
            event_publisher=None,  # TODO: Implementiere EventPublisher
            message_repository=rag_adapter.chat_message_repo
        )
        
        # Führe Frage durch
        result = await use_case.execute(
            question=request.question,
            session_id=request.session_id,
            model_id=request.model if hasattr(request, 'model') else "gpt-4o-mini",
            filters=request.filters if hasattr(request, 'filters') else None,
            use_hybrid_search=request.use_hybrid_search if hasattr(request, 'use_hybrid_search') else True
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return AskQuestionResponse(
            answer=result.content,
            source_references=[ref.__dict__ for ref in result.source_references],
            structured_data=None,
            suggested_questions=["Was sind die wichtigsten Schritte?", "Welche Sicherheitshinweise gibt es?"],
            search_results=[],
            model_used=request.model if hasattr(request, 'model') else "gpt-4o-mini",
            processing_time_ms=processing_time,
            tokens_used=50
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
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """Ruft die Anzahl indexierter Dokumente pro Document Type ab."""
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
        
        # Erstelle Use Case
        use_case = GetDocumentTypeCountsUseCase(
            indexed_document_repository=rag_adapter.indexed_document_repo
        )
        
        # Führe Abruf durch
        counts = use_case.execute(document_type_ids=parsed_ids)
        
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
        
        # Konvertiere Messages zu Response-Schemas (mit ai_model_used)
        message_responses = [
            ChatMessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                source_references=None,  # Wird aus source_references konvertiert falls nötig
                structured_data=None,
                ai_model_used=msg.ai_model_used,  # WICHTIG: ai_model_used aus Entity übernehmen
                created_at=msg.created_at
            )
            for msg in messages
        ]
        
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
