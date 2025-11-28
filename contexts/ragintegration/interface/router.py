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
    SubmitChunkFeedbackRequest, ChunkFeedbackResponse,  # v2.9.0: Chunk-Level Feedback
    RAGAnalyticsResponse,  # PHASE 4.2: RAG Analytics Dashboard
    SaveRAGChatPromptRequest, RAGChatPromptResponse,  # PHASE 1: RAG Chat Prompt Management
    SearchQualityAnalyticsResponse,  # PHASE 5: Search Quality Analytics
    TrendAnalysisResponse, BeforeAfterComparisonResponse, AlertResponse,  # v2.9.0: Trend Analysis
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
from contexts.ragintegration.domain.exceptions import MissingCustomPromptError, InvalidCustomPromptError
from contexts.accesscontrol.domain.entities import User
from contexts.accesscontrol.interface.guard_router import get_current_user
from backend.app.database import get_db
from contexts.ragintegration.domain.value_objects import SourceReference, PromptState

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
        
        # PHASE 2.8: Einheitliches Embedding-Modell (text-embedding-3-small)
        from contexts.ragintegration.infrastructure.embedding_factory import create_embedding_service, DEFAULT_EMBEDDING_MODEL
        import os
        
        # WICHTIG: Verwende immer text-embedding-3-small als Standard
        embedding_service = rag_adapter.embedding_service  # Default (sollte bereits text-embedding-3-small sein)
        
        # Falls chunking_strategy gesetzt ist, respektiere es (für Migration)
        if request.chunking_strategy:
            if request.chunking_strategy == "openai_1536":
                # OpenAI mit 1536 Dimensionen (text-embedding-3-small)
                openai_key = os.getenv("OPENAI_GPT5_MINI_API_KEY") or os.getenv("OPENAI_API_KEY")
                if openai_key:
                    embedding_service = create_embedding_service(
                        provider="openai",
                        model_name=DEFAULT_EMBEDDING_MODEL,  # text-embedding-3-small
                        openai_api_key=openai_key
                    )
                    print(f"✅ Verwende OpenAI Embedding Service ({DEFAULT_EMBEDDING_MODEL}, 1536 dim) für Dokument {request.upload_document_id}")
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="OpenAI API Key nicht verfügbar. Bitte setze OPENAI_GPT5_MINI_API_KEY oder OPENAI_API_KEY in .env"
                    )
            elif request.chunking_strategy == "gemini_768":
                # Gemini mit 768 Dimensionen (Fallback)
                google_key = os.getenv("GOOGLE_AI_API_KEY")
                if google_key:
                    embedding_service = create_embedding_service(
                        provider="google",
                        google_api_key=google_key
                    )
                    print(f"✅ Verwende Google Gemini Embedding Service (text-embedding-004, 768 dim) für Dokument {request.upload_document_id}")
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Google AI API Key nicht verfügbar. Bitte setze GOOGLE_AI_API_KEY in .env"
                    )
            elif request.chunking_strategy == "local_384":
                # Local SentenceTransformer mit 384 Dimensionen (nur für Entwicklung)
                embedding_service = create_embedding_service(
                    provider="sentence-transformers"
                )
                print(f"⚠️ Verwende Local SentenceTransformer Embedding Service (384 dim) für Dokument {request.upload_document_id} - NUR FÜR ENTWICKLUNG!")
            else:
                print(f"⚠️ Unbekannte Strategie '{request.chunking_strategy}', verwende Standard-Embedding-Service ({DEFAULT_EMBEDDING_MODEL})")
        else:
            # Keine Strategie angegeben - verwende Standard (text-embedding-3-small)
            print(f"✅ Verwende Standard-Embedding-Service ({DEFAULT_EMBEDDING_MODEL}, 1536 dim) für Dokument {request.upload_document_id}")
        
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
        
        # PHASE 1: ECHTE SHAP Service Integration mit Background Data Service
        try:
            from contexts.ragintegration.infrastructure.shap_real_attribution import (
                SHAPExplainerService,
                FeatureExtractor,
                RankingModelWrapper
            )
            from contexts.ragintegration.infrastructure.shap_background_data_service import SHAPBackgroundDataService
            
            # Erstelle Komponenten für echte SHAP-Integration
            feature_extractor = FeatureExtractor()
            ranking_model = RankingModelWrapper()
            
            # Background Data Service (sammelt historische Search-Daten)
            # NEU v2.7.0: SQLite-basiert oder In-Memory
            import os
            persist_to_db = os.getenv('PERSIST_TO_DB', 'true').lower() == 'true'
            
            if persist_to_db:
                # SQLite-basiertes Repository
                from contexts.ragintegration.infrastructure.shap_background_data_repository_sqlite import (
                    SHAPBackgroundDataRepositorySQLite
                )
                background_data_repo = SHAPBackgroundDataRepositorySQLite(
                    db_session=db_session,
                    max_records=1000,
                    feature_extractor=feature_extractor
                )
                # Verwende Repository direkt (hat get_background_data() Methode)
                background_data = background_data_repo.get_background_data(n_samples=50)
                # Speichere Repository für spätere Verwendung
                background_data_service = background_data_repo
            else:
                # In-Memory Service (Fallback)
                background_data_service = SHAPBackgroundDataService(
                    max_records=1000,  # Letzte 1000 Searches
                    feature_extractor=feature_extractor
                )
                background_data = background_data_service.get_background_data(n_samples=50)
            
            # Echte SHAP mit KernelExplainer und echten Background-Daten
            shap_service = SHAPExplainerService(
                model=ranking_model,
                feature_extractor=feature_extractor,
                background_data=background_data,  # Echte historische Daten
                n_background_samples=50,
                db_session=db_session if persist_to_db else None  # NEU v2.7.0: SQLite Cache Support
            )
            
            # Speichere Background Data Service/Repository für spätere Verwendung
            shap_service._background_data_service = background_data_service
            
            print(f"✅ Echte SHAP-Integration aktiviert (KernelExplainer mit {len(background_data)} Background-Samples)")
        except ImportError as e:
            # Fallback zu heuristischem SHAP (falls SHAP-Library nicht verfügbar)
            print(f"⚠️ Konnte echten SHAP-Service nicht laden: {e}")
            print("   Fallback zu heuristischem SHAP-Service")
            from contexts.ragintegration.infrastructure.shap_service import SHAPExplanationService
            shap_service = SHAPExplanationService()
        
        # PHASE 4: ML Model Service (deprecated - verwende ltr_service)
        from contexts.ragintegration.infrastructure.ml_model_service import MLModelService
        from contexts.ragintegration.infrastructure.repositories import SQLAlchemyTrainingDataRepository
        training_data_repo = SQLAlchemyTrainingDataRepository(db_session)
        ml_model_service = MLModelService(training_data_repo=training_data_repo)
        
        # NEU v2.7.0: LTR Service (Learning-to-Rank mit echtem ML-Modell)
        try:
            from contexts.ragintegration.infrastructure.ml.ltr_service import LTRService
            ltr_service = LTRService(
                model_dir='data/ml_models',
                model_name='ltr_ranker_v1.pkl',
                enable_ml=True  # Aktiviere ML-Ranking
            )
            if ltr_service.is_enabled():
                print(f"✅ LTR Service aktiviert (Model: {ltr_service.model_path})")
            else:
                print(f"⚠️ LTR Service nicht ready (Model nicht gefunden)")
        except Exception as e:
            print(f"⚠️ Konnte LTR Service nicht laden: {e}")
            ltr_service = None
        
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
            permission_service=permission_service,  # RBAC: Für Interest Group Filtering
            shap_service=shap_service,  # SHAP: Für Feature-Importance-Erklärungen (Phase 1)
            ml_model_service=ml_model_service,  # ML: Für Learning-to-Rank Re-Ranking (deprecated)
            ltr_service=ltr_service,  # LTR: Learning-to-Rank Service (NEU v2.7.0)
            search_quality_metrics_repo=rag_adapter.search_quality_metrics_repo,  # NEU v2.9.0: Search Quality Metrics Repository
            training_data_repo=training_data_repo  # NEU v2.10.0: Training Data Repository für automatisches Speichern
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
            top_k=top_k,  # PHASE 0.1: top_k vom Frontend
            use_ml_reranking=getattr(request, 'use_ml_reranking', False),  # NEU: ML Re-Ranking (deprecated)
            use_ml_ranking=getattr(request, 'use_ml_ranking', False),  # NEU: LTR ML-Ranking (v2.7.0)
            temperature=getattr(request, 'temperature', None),  # NEU v2.10.3: AI Temperature
            max_tokens=getattr(request, 'max_tokens', None),  # NEU v2.10.3: Max Tokens
            top_p=getattr(request, 'top_p', None)  # NEU v2.10.3: Top P
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
            
            # NEU: ML Score (Phase 4) und Final Score (v2.7.0)
            ml_score = extended_metadata.get('ml_score')
            final_score = extended_metadata.get('final_score')
            
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
                ml_score=ml_score,  # NEU: ML Score aus LTR (v2.7.0)
                final_score=final_score,  # NEU: Final-Score (Hybrid + ML, v2.7.0)
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
        
        # NEU v2.7.0: Hole Analytics-Block aus Metadaten
        analytics = result.metadata.get("analytics") if result.metadata else None
        
        return AskQuestionResponse(
            answer=result.content,
            source_references=source_refs,
            structured_data=None,
            suggested_questions=["Was sind die wichtigsten Schritte?", "Welche Sicherheitshinweise gibt es?"],
            search_results=[],
            model_used=request.model if hasattr(request, 'model') else "gpt-4o-mini",
            processing_time_ms=processing_time,
            tokens_used=tokens_used,
            message_id=result.id,  # NEU: Message-ID für Prompt Viewer
            analytics=analytics  # NEU v2.7.0: Analytics-Block
        )
        
    except MissingCustomPromptError as e:
        # STRICTE REGEL (CR-P2.2): Custom Prompt fehlt für gewählten Dokumenttyp.
        # Wenn document_type_id gesetzt ist, MUSS ein Custom Prompt existieren.
        # Keine Fallbacks, kein generischer Prompt.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except InvalidCustomPromptError as e:
        # STRICTE REGEL (CR-P2.2): Custom Prompt ist ungültig (fehlende Platzhalter).
        # Custom Prompts MÜSSEN die Platzhalter {context} und {question} enthalten.
        # Keine automatische Reparatur, keine Fallbacks.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
                    
                    # NEU: ML Score und Final Score (v2.7.0)
                    ml_score = extended_metadata.get('ml_score')
                    final_score = extended_metadata.get('final_score')
                    
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
                        ml_score=ml_score,  # NEU: ML Score aus LTR (v2.7.0)
                        final_score=final_score,  # NEU: Final-Score (Hybrid + ML, v2.7.0)
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
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat Message {message_id} nicht gefunden"
            )
        
        # Prüfe ob Prompt in metadata gespeichert ist (KEINE Rekonstruktion!)
        prompt_text = None
        prompt_state = PromptState.INVALID.value
        if message.metadata and message.metadata.get("prompt_text"):
            prompt_text = message.metadata["prompt_text"]
            prompt_state = PromptState.VALID.value
            print(f"DEBUG get_prompt_for_message: Verwende gespeicherten Prompt aus metadata")
        else:
            # Kein gespeicherter Prompt - INVALID state
            print(f"WARNING get_prompt_for_message: Prompt fehlt in metadata für Message {message_id} - INVALID state")
            prompt_state = PromptState.INVALID.value
        
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
        
        # 3. Nur für Assistant-Messages (User-Messages haben keinen Prompt)
        if message.role != "assistant":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt kann nur für Assistant-Messages abgerufen werden"
            )
        
        # 4. Hole vorherige User-Message (die Frage) und Context-Chunks für Anzeige
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
        document_type = None
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
                    # Extrahiere document_type aus ersten Chunk
                    if not document_type:
                        indexed_doc = rag_adapter.indexed_document_repo.get_by_id(chunk.indexed_document_id)
                        if indexed_doc:
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
        
        # Hole erweiterte Metadaten aus message.metadata
        prompt_type = message.metadata.get("prompt_type") if message.metadata else None
        document_type_selected = message.metadata.get("document_type_selected") if message.metadata else None
        document_type_effective = message.metadata.get("document_type_effective") if message.metadata else None
        
        # Return Response mit prompt_state
        return PromptViewerResponse(
            message_id=message_id,
            question=user_question or "Unbekannt",
            prompt_text=prompt_text,  # Kann None sein wenn INVALID
            prompt_state=prompt_state,
            context_chunks=context_chunks,
            document_type=document_type,
            model_used=message.ai_model_used or "unknown",
            tokens_used=message.metadata.get("tokens_used") if message.metadata else None,
            prompt_type=prompt_type,
            document_type_selected=document_type_selected,
            document_type_effective=document_type_effective
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
        
        # NEU v2.7.0: Training Data Repository (SQLite oder File-basiert)
        import os
        persist_to_db = os.getenv('PERSIST_TO_DB', 'true').lower() == 'true'
        
        training_data_repo = None
        if persist_to_db:
            # SQLite-basiertes Repository
            from ..infrastructure.ml.training_data_repository_sqlite import TrainingDataRepositorySQLite
            training_data_repo = TrainingDataRepositorySQLite(db_session)
        else:
            # File-basiertes Repository (Fallback)
            from ..infrastructure.ml.training_data_repository import FileBasedTrainingDataRepository
            training_data_repo = FileBasedTrainingDataRepository()
        
        # Get Chat Message Repository für Training-Daten
        from ..infrastructure.repositories import SQLAlchemyChatMessageRepository
        message_repo = SQLAlchemyChatMessageRepository(db_session)
        
        # Execute Use Case
        use_case = SubmitFeedbackUseCase(
            feedback_repo=feedback_repo,
            message_repo=message_repo,
            event_publisher=event_publisher,
            training_data_repo=training_data_repo
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


# ============================================================================
# CHUNK FEEDBACK ENDPOINTS (v2.9.0: Chunk-Level Feedback)
# ============================================================================

@router.post(
    "/chat/chunks/feedback",
    response_model=ChunkFeedbackResponse,
    summary="Submit Chunk-Level Feedback",
    description="Gebe Feedback zu einem einzelnen Chunk in einer RAG Chat-Antwort ab."
)
async def submit_chunk_feedback(
    request: SubmitChunkFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """
    Speichere Chunk-Level Feedback für einen einzelnen Chunk.
    
    **RBAC:**
    - Level 1+: Alle User können Chunk-Level Feedback geben
    - Ein User kann mehrere Feedbacks für denselben Chunk geben (z.B. in verschiedenen Messages)
    """
    try:
        from contexts.ragintegration.infrastructure.repositories import SQLAlchemyChunkFeedbackRepository
        from contexts.ragintegration.application.use_cases import SubmitChunkFeedbackUseCase
        from contexts.documentupload.interface.workflow_router import get_event_publisher
        from contexts.ragintegration.interface.schemas import ChunkFeedbackResponse
        
        # Setup Repository
        chunk_feedback_repo = SQLAlchemyChunkFeedbackRepository(db_session)
        
        # Get User ID
        user_id = current_user.get('id') if isinstance(current_user, dict) else getattr(current_user, 'id', None)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID nicht gefunden"
            )
        
        # Get Event Publisher (Singleton)
        event_publisher = get_event_publisher()
        
        # Get Chat Message Repository für Validierung
        from ..infrastructure.repositories import SQLAlchemyChatMessageRepository
        message_repo = SQLAlchemyChatMessageRepository(db_session)
        
        # Execute Use Case
        use_case = SubmitChunkFeedbackUseCase(
            chunk_feedback_repo=chunk_feedback_repo,
            message_repo=message_repo,
            event_publisher=event_publisher,
            training_data_repo=None  # TODO: Integriere Training-Data-Repository
        )
        
        saved_feedback = await use_case.execute(
            chunk_id=request.chunk_id,
            chat_message_id=request.chat_message_id,
            document_id=request.document_id,
            user_id=user_id,
            rating=request.rating,
            comment=request.comment
        )
        
        return ChunkFeedbackResponse(
            id=saved_feedback.id,
            chunk_id=saved_feedback.chunk_id,
            chat_message_id=saved_feedback.chat_message_id,
            document_id=saved_feedback.document_id,
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
            detail=f"Fehler beim Speichern des Chunk-Feedbacks: {str(e)}"
        )


@router.get(
    "/chat/chunks/{chunk_id}/feedback",
    response_model=List[ChunkFeedbackResponse],
    summary="Get Chunk Feedback",
    description="Hole alle Feedbacks für einen Chunk."
)
async def get_chunk_feedback(
    chunk_id: str = Path(..., description="Chunk-ID"),
    chat_message_id: Optional[int] = Query(None, description="Optional: Filter nach Chat Message"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session)
):
    """
    Hole alle Feedbacks für einen Chunk.
    
    **RBAC:**
    - Level 1+: Alle User können Chunk-Feedbacks sehen
    """
    try:
        from contexts.ragintegration.infrastructure.repositories import SQLAlchemyChunkFeedbackRepository
        from contexts.ragintegration.interface.schemas import ChunkFeedbackResponse
        
        chunk_feedback_repo = SQLAlchemyChunkFeedbackRepository(db_session)
        
        # Get User ID (optional für Filter)
        user_id = current_user.get('id') if isinstance(current_user, dict) else getattr(current_user, 'id', None)
        
        feedbacks = await chunk_feedback_repo.get_by_chunk_id(
            chunk_id=chunk_id,
            chat_message_id=chat_message_id,
            user_id=user_id
        )
        
        return [ChunkFeedbackResponse(
            id=f.id,
            chunk_id=f.chunk_id,
            chat_message_id=f.chat_message_id,
            document_id=f.document_id,
            user_id=f.user_id,
            rating=f.rating,
            comment=f.comment,
            submitted_at=f.submitted_at
        ) for f in feedbacks]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Laden der Chunk-Feedbacks: {str(e)}"
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


@router.get(
    "/analytics/search-quality-overview",
    response_model=SearchQualityAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    tags=["RAG Analytics"],
    summary="Hole Search Quality Analytics Overview",
    description="""
    Hole detaillierte Search Quality Analytics Overview:
    - Dokument-Typ-Verteilung in Suchergebnissen
    - Score-Verteilung
    - Top Queries mit gefundenen/fehlenden Dokument-Typen
    - SHAP-basierte Insights
    
    **RBAC:**
    - Level 1+: Alle User können eigene Analytics sehen
    - Level 4+: QM-Mitarbeiter können alle Analytics sehen
    
    **WICHTIG:** Dieser Endpoint wurde umbenannt von `/analytics/search-quality` zu `/analytics/search-quality-overview`
    um Konflikte mit dem neuen `/analytics/search-quality` Endpoint zu vermeiden.
    """
)
async def get_search_quality_analytics(
    start_date: Optional[str] = Query(None, description="Optional: Start-Datum (ISO format)"),
    end_date: Optional[str] = Query(None, description="Optional: End-Datum (ISO format)"),
    top_k: int = Query(5, ge=1, le=20, description="Top-K für 'found_in_top_k' Berechnung"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session)
):
    """
    Hole Search Quality Analytics.
    
    **RBAC:**
    - Level 1+: Alle User können eigene Analytics sehen
    - Level 4+: QM-Mitarbeiter können alle Analytics sehen
    """
    try:
        from contexts.ragintegration.infrastructure.repositories import (
            SQLAlchemyChatMessageRepository,
            SQLAlchemyIndexedDocumentRepository
        )
        from contexts.ragintegration.application.use_cases import GetSearchQualityAnalyticsUseCase
        from contexts.ragintegration.infrastructure.repositories import (
            SQLAlchemyTrainingDataRepository
        )
        from datetime import datetime
        
        # RBAC: Level 1-3 können nur eigene Analytics sehen
        user_level = current_user.get('level') if isinstance(current_user, dict) else getattr(current_user, 'level', 0)
        current_user_id = current_user.get('id') if isinstance(current_user, dict) else getattr(current_user, 'id', None)
        
        # Sicherstellen dass user_level ein int ist (Fallback zu 1 wenn None)
        if user_level is None:
            user_level = 1
        
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
        
        # Initialisiere Repositories
        chat_message_repo = SQLAlchemyChatMessageRepository(db_session)
        indexed_document_repo = SQLAlchemyIndexedDocumentRepository(db_session)
        training_data_repo = SQLAlchemyTrainingDataRepository(db_session)
        
        # Initialisiere Use Case
        use_case = GetSearchQualityAnalyticsUseCase(
            chat_message_repo=chat_message_repo,
            training_data_repo=training_data_repo,
            indexed_document_repo=indexed_document_repo
        )
        
        # Führe Use Case aus
        analytics = await use_case.execute(
            start_date=start_dt,
            end_date=end_dt,
            top_k=top_k
        )
        
        return SearchQualityAnalyticsResponse(**analytics)
        
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
            detail=f"Fehler beim Abrufen der Search Quality Analytics: {str(e)}"
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


# ============================================
# SHAP Analytics Endpoints (Phase 2)
# ============================================

@router.get(
    "/analytics/shap",
    response_model=Any,  # SHAPAnalyticsResponse aus schemas
    summary="Get SHAP Analytics",
    description="Hole SHAP Analytics-Daten für ein Such-Ergebnis (Feature Importance, Waterfall Data)."
)
async def get_shap_analytics(
    query: str = Query(..., description="Die Suche-Query"),
    chunk_id: Optional[str] = Query(None, description="Spezifischer Chunk für Waterfall (optional)"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """
    Hole SHAP Analytics-Daten für Frontend-Visualisierungen.
    
    Liefert:
    - Feature Importance (für Bar Chart)
    - Waterfall Data (für Waterfall Chart, falls chunk_id angegeben)
    - Background Data Statistics
    - Model Info
    """
    try:
        from ..infrastructure.shap_real_attribution import (
            SHAPExplainerService,
            FeatureExtractor,
            RankingModelWrapper
        )
        from ..infrastructure.shap_background_data_service import SHAPBackgroundDataService
        from ..interface.schemas import (
            SHAPFeatureImportanceResponse,
            SHAPWaterfallDataResponse,
            SHAPAnalyticsResponse
        )
        
        # Feature-Beschreibungen
        feature_descriptions = {
            'vector_score': 'Vektor-Ähnlichkeits-Score (Embedding-basiert)',
            'text_score': 'Text-Matching-Score (BM25/Jaccard)',
            'user_level': 'User-Level (1-5, normalisiert)',
            'keyword_matches': 'Anzahl Keyword-Matches',
            'chunk_length': 'Chunk-Länge in Zeichen',
            'heading_hierarchy_depth': 'Tiefe der Heading-Hierarchie',
            'confidence_score': 'Confidence-Score der Extraktion'
        }
        
        # Erstelle SHAP-Service
        feature_extractor = FeatureExtractor()
        ranking_model = RankingModelWrapper()
        
        # NEU v2.7.0: SQLite-basiert oder In-Memory
        import os
        persist_to_db = os.getenv('PERSIST_TO_DB', 'true').lower() == 'true'
        
        if persist_to_db:
            # SQLite-basiertes Repository
            from ..infrastructure.shap_background_data_repository_sqlite import (
                SHAPBackgroundDataRepositorySQLite
            )
            background_data_service = SHAPBackgroundDataRepositorySQLite(
                db_session=db_session,
                max_records=1000,
                feature_extractor=feature_extractor
            )
            background_data = background_data_service.get_background_data(n_samples=50)
        else:
            # In-Memory Service (Fallback)
            background_data_service = SHAPBackgroundDataService(
                max_records=1000,
                feature_extractor=feature_extractor
            )
            background_data = background_data_service.get_background_data(n_samples=50)
        
        shap_service = SHAPExplainerService(
            model=ranking_model,
            feature_extractor=feature_extractor,
            background_data=background_data,
            n_background_samples=50,
            db_session=db_session if persist_to_db else None  # NEU v2.7.0: SQLite Cache Support
        )
        
        # Hole Background Data Stats
        background_stats = background_data_service.get_statistics()
        
        # Feature Importance (durchschnittlich über alle Features)
        # Für echte Daten müsste man mehrere Samples analysieren
        # Hier verwenden wir ein Beispiel-Sample
        
        # Mock Chunk für Feature Importance Berechnung
        mock_chunk = {
            'chunk_id': 'mock_chunk',
            'metadata': {
                'chunk_text': query,
                'page_numbers': [1],
                'heading_hierarchy_depth': 2,
                'confidence_score': 0.9,
                'chunk_length': len(query)
            }
        }
        
        # Berechne SHAP für Mock-Sample
        shap_explanation = shap_service.explain(
            query=query,
            chunk=mock_chunk,
            vector_score=0.8,  # Mock-Werte
            text_score=0.7,
            hybrid_score=0.77,
            document_type='Arbeitsanweisung',
            user_level=3,
            keyword_matches=2
        )
        
        # Erstelle Feature Importance Response
        feature_importance_list = []
        total_abs_importance = sum(abs(v) for v in shap_explanation.feature_importance.values())
        
        for feature_name, importance in sorted(
            shap_explanation.feature_importance.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        ):
            normalized = abs(importance) / total_abs_importance if total_abs_importance > 0 else 0
            feature_importance_list.append(
                SHAPFeatureImportanceResponse(
                    feature_name=feature_name,
                    importance=importance,
                    normalized_importance=normalized,
                    description=feature_descriptions.get(feature_name, 'Unbekanntes Feature')
                )
            )
        
        # Waterfall Data
        waterfall_features = []
        for feature_name in feature_extractor.feature_names:
            waterfall_features.append({
                'name': feature_name,
                'value': shap_explanation.features.get(feature_name, 0.0),
                'shap_value': shap_explanation.feature_importance.get(feature_name, 0.0)
            })
        
        waterfall_data = SHAPWaterfallDataResponse(
            base_value=shap_explanation.base_value,
            expected_value=shap_explanation.expected_value,
            prediction=shap_explanation.prediction,
            features=waterfall_features
        )
        
        # Model Info
        model_info = {
            'model_type': 'RankingModelWrapper',
            'explainer_type': 'KernelExplainer (SHAP)',
            'n_features': len(feature_extractor.feature_names),
            'feature_names': feature_extractor.feature_names
        }
        
        # Erstelle Response
        response = SHAPAnalyticsResponse(
            feature_importance=feature_importance_list,
            waterfall_data=waterfall_data,
            background_data_stats=background_stats,
            model_info=model_info
        )
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der SHAP Analytics: {str(e)}"
        )


@router.get(
    "/analytics/shap/background-stats",
    response_model=Any,  # BackgroundDataStatsResponse
    summary="Get Background Data Statistics",
    description="Hole Statistiken über gesammelte Background-Daten."
)
async def get_background_data_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Hole Statistiken über gesammelte Background-Daten.
    
    Zeigt wie viele historische Search-Daten gesammelt wurden und wann.
    """
    try:
        from ..infrastructure.shap_real_attribution import FeatureExtractor
        from ..interface.schemas import BackgroundDataStatsResponse
        
        # NEU v2.7.0: SQLite-basiert oder In-Memory
        import os
        persist_to_db = os.getenv('PERSIST_TO_DB', 'true').lower() == 'true'
        
        feature_extractor = FeatureExtractor()
        
        if persist_to_db:
            # SQLite-basiertes Repository
            from ..infrastructure.shap_background_data_repository_sqlite import (
                SHAPBackgroundDataRepositorySQLite
            )
            background_data_service = SHAPBackgroundDataRepositorySQLite(
                db_session=db_session,
                max_records=1000,
                feature_extractor=feature_extractor
            )
        else:
            # In-Memory Service (Fallback)
            from ..infrastructure.shap_background_data_service import SHAPBackgroundDataService
            background_data_service = SHAPBackgroundDataService(
                max_records=1000,
                feature_extractor=feature_extractor
            )
        
        # Hole Statistiken
        stats = background_data_service.get_statistics()
        
        # Konvertiere zu Response
        response = BackgroundDataStatsResponse(
            total_records=stats['total_records'],
            background_data_shape=list(stats['background_data_shape']) if stats['background_data_shape'] else None,
            last_update=stats['last_update'],
            oldest_record=stats['oldest_record'],
            newest_record=stats['newest_record']
        )
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Background Data Stats: {str(e)}"
        )


@router.get(
    "/analytics/shap/cache-stats",
    response_model=Dict[str, Any],
    summary="Get SHAP Cache Statistics",
    description="Hole Cache-Statistiken für SHAP-Berechnungen (Performance-Monitoring)."
)
async def get_shap_cache_stats(
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session)
):
    """
    Hole SHAP Cache-Statistiken.
    
    Zeigt Cache Hit Rate, Cache-Größe, etc. für Performance-Monitoring.
    """
    try:
        # NEU v2.7.0: SQLite-basiert oder In-Memory
        import os
        persist_to_db = os.getenv('PERSIST_TO_DB', 'true').lower() == 'true'
        
        if persist_to_db:
            # SQLite-basiertes Repository
            from ..infrastructure.shap_cache_repository_sqlite import SHAPCacheRepositorySQLite
            cache = SHAPCacheRepositorySQLite(
                db_session=db_session,
                max_size=100,
                ttl_seconds=3600
            )
        else:
            # In-Memory Cache (Fallback)
            from ..infrastructure.shap_cache_service import get_shap_cache
            cache = get_shap_cache()
        
        # Hole Statistiken
        stats = cache.get_statistics()
        
        # Berechne Performance-Verbesserung
        # Annahme: SHAP-Berechnung dauert ~2s, Cache-Hit ~0ms
        estimated_time_saved = stats['hits'] * 2.0  # Sekunden
        
        return {
            'cache_stats': stats,
            'performance_metrics': {
                'estimated_time_saved_seconds': round(estimated_time_saved, 2),
                'estimated_time_saved_minutes': round(estimated_time_saved / 60, 2),
                'average_response_time_ms': 2000 if stats['hit_rate_percent'] == 0 else int(2000 * (1 - stats['hit_rate_percent'] / 100))
            },
            'recommendations': [
                f"Cache Hit Rate: {stats['hit_rate_percent']}% - {'✅ Gut' if stats['hit_rate_percent'] > 50 else '⚠️ Niedrig'}",
                f"Cache-Größe: {stats['cache_size']}/{stats['max_size']} - {'✅ Optimal' if stats['cache_size'] < stats['max_size'] * 0.9 else '⚠️ Fast voll'}",
                f"Geschätzte Zeit gespart: {round(estimated_time_saved / 60, 1)} Minuten"
            ]
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Cache Stats: {str(e)}"
        )


# ============================================
# SHAP HISTORIE ENDPOINT (v2.10.0)
# ============================================

@router.get(
    "/analytics/shap/history",
    response_model=Any,  # SHAPHistoryResponse
    summary="Get SHAP History",
    description="Hole SHAP-Historie aus Training Data (NEU v2.10.0)."
)
async def get_shap_history(
    query: Optional[str] = Query(None, description="Filter nach Query (optional)"),
    chunk_id: Optional[str] = Query(None, description="Filter nach Chunk ID (optional)"),
    start_date: Optional[str] = Query(None, description="Start-Datum (ISO-Format, optional)"),
    end_date: Optional[str] = Query(None, description="End-Datum (ISO-Format, optional)"),
    user_id: Optional[int] = Query(None, description="Filter nach User ID (optional)"),
    limit: int = Query(50, description="Maximale Anzahl Einträge"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session)
):
    """
    Hole SHAP-Historie aus Training Data.
    
    Lädt gespeicherte SHAP-Erklärungen aus der rag_training_data Tabelle.
    """
    try:
        from ..infrastructure.repositories import SQLAlchemyTrainingDataRepository
        from ..interface.schemas import SHAPHistoryEntryResponse, SHAPHistoryResponse
        from datetime import datetime
        
        training_data_repo = SQLAlchemyTrainingDataRepository(db_session)
        
        # Hole Training Data mit SHAP
        training_data = training_data_repo.get_training_data(
            with_shap=True,
            user_id=user_id,
            limit=limit * 2  # Hole mehr für Filterung
        )
        
        # Filtere nach Query
        if query:
            training_data = [td for td in training_data if query.lower() in td.query.lower()]
        
        # Filtere nach Chunk ID
        if chunk_id:
            training_data = [td for td in training_data if td.chunk_id == chunk_id]
        
        # Filtere nach Datum
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            training_data = [td for td in training_data if td.created_at >= start_dt]
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            training_data = [td for td in training_data if td.created_at <= end_dt]
        
        # Limitiere auf limit
        training_data = training_data[:limit]
        
        # Konvertiere zu Response
        entries = []
        for td in training_data:
            # Parse SHAP-Erklärung (JSON String)
            shap_explanation = None
            if td.shap_explanation:
                import json
                try:
                    shap_explanation = json.loads(td.shap_explanation) if isinstance(td.shap_explanation, str) else td.shap_explanation
                except:
                    shap_explanation = None
            
            entries.append(SHAPHistoryEntryResponse(
                id=td.id,
                query=td.query,
                chunk_id=td.chunk_id,
                document_id=td.document_id,
                created_at=td.created_at,
                shap_explanation=shap_explanation,
                user_feedback=td.user_feedback,
                feedback_comment=td.feedback_comment,
                hybrid_score=float(td.hybrid_score) if isinstance(td.hybrid_score, str) else td.hybrid_score
            ))
        
        return SHAPHistoryResponse(
            entries=entries,
            total=len(entries),
            has_more=len(training_data) >= limit
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der SHAP-Historie: {str(e)}"
        )


# ============================================
# SEARCH QUALITY METRICS ENDPOINTS (v2.9.0)
# ============================================

@router.get(
    "/analytics/search-quality",
    response_model=Any,  # SearchQualityMetricsResponse oder AggregatedSearchQualityMetricsResponse
    summary="Get Search Quality Metrics",
    description="Hole Search Quality Metrics für eine Query oder aggregiert über mehrere Queries."
)
async def get_search_quality_metrics(
    query: Optional[str] = Query(None, description="Spezifische Query (optional, für einzelne Metriken)"),
    session_id: Optional[int] = Query(None, description="Session-ID (optional, für Filterung)"),
    aggregate: bool = Query(False, description="Aggregiere Metriken über mehrere Queries"),
    min_date: Optional[str] = Query(None, description="Minimales Datum für Aggregation (ISO-Format)"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """
    Hole Search Quality Metrics für Frontend-Visualisierungen.
    
    Liefert:
    - Precision@k, Recall@k, NDCG@k, MRR
    - Vergleich Hybrid vs ML Ranking
    - Aggregierte Metriken über mehrere Queries (falls aggregate=True)
    """
    try:
        from ..infrastructure.search_quality_metrics import (
            SearchQualityMetricsService,
            SearchQualityMetrics
        )
        from ..interface.schemas import (
            SearchQualityMetricsResponse,
            AggregatedSearchQualityMetricsResponse
        )
        from sqlalchemy import text
        
        metrics_service = SearchQualityMetricsService()
        
        if aggregate:
            # Aggregierte Metriken über mehrere Queries
            # Hole alle Chat-Messages mit Feedback
            query_sql = text("""
                SELECT 
                    rcm.content as query,
                    rcm.session_id,
                    rcm.user_id,
                    rcm.created_at,
                    rcm.source_chunks,
                    rcm._extended_metadata,
                    rf.rating as feedback_rating
                FROM rag_chat_messages rcm
                LEFT JOIN rag_feedback rf ON rcm.id = rf.chat_message_id
                WHERE rcm.role = 'assistant'
                AND rcm.source_chunks IS NOT NULL
            """)
            
            if min_date:
                query_sql = text("""
                    SELECT 
                        rcm.content as query,
                        rcm.session_id,
                        rcm.user_id,
                        rcm.created_at,
                        rcm.source_chunks,
                        rcm._extended_metadata,
                        rf.rating as feedback_rating
                    FROM rag_chat_messages rcm
                    LEFT JOIN rag_feedback rf ON rcm.id = rf.chat_message_id
                    WHERE rcm.role = 'assistant'
                    AND rcm.source_chunks IS NOT NULL
                    AND rcm.created_at >= :min_date
                """)
                result = db_session.execute(query_sql, {"min_date": min_date})
            else:
                result = db_session.execute(query_sql)
            
            messages = result.fetchall()
            
            if not messages:
                # Keine Daten → leere aggregierte Metriken
                return AggregatedSearchQualityMetricsResponse(
                    num_queries=0,
                    average_precision_at_1=0.0,
                    average_precision_at_3=0.0,
                    average_precision_at_5=0.0,
                    average_precision_at_10=0.0,
                    average_recall_at_1=0.0,
                    average_recall_at_3=0.0,
                    average_recall_at_5=0.0,
                    average_recall_at_10=0.0,
                    average_ndcg_at_1=0.0,
                    average_ndcg_at_3=0.0,
                    average_ndcg_at_5=0.0,
                    average_ndcg_at_10=0.0,
                    average_mrr=0.0,
                    average_relevance_score=0.0,
                    average_num_relevant=0.0,
                    average_num_total=0.0,
                    hybrid_vs_ml_comparison={}
                )
            
            # Berechne Metriken für jede Query
            metrics_list = []
            for msg in messages:
                query_text, session_id_val, user_id_val, created_at, source_chunks_json, extended_metadata_json, feedback_rating = msg
                
                # Parse source_chunks und extended_metadata
                import json
                try:
                    source_chunks = json.loads(source_chunks_json) if source_chunks_json else []
                    extended_metadata = json.loads(extended_metadata_json) if extended_metadata_json else {}
                except:
                    continue
                
                if not source_chunks:
                    continue
                
                # NEU: Hole Chunk-Level Feedback aus der Datenbank
                from backend.app.models import ChunkFeedbackModel
                chunk_feedback_map = {}  # chunk_id -> rating
                try:
                    # Hole alle Chunk-Feedbacks für diese Message
                    # Wir brauchen die message_id, aber haben nur session_id und created_at
                    # Hole die message_id aus der Assistant-Message
                    assistant_msg_query = text("""
                        SELECT id FROM rag_chat_messages
                        WHERE session_id = :session_id
                        AND role = 'assistant'
                        AND created_at = :created_at
                        LIMIT 1
                    """)
                    msg_result = db_session.execute(assistant_msg_query, {
                        "session_id": session_id_val,
                        "created_at": created_at
                    })
                    msg_row = msg_result.fetchone()
                    if msg_row:
                        message_id = msg_row[0]
                        # Hole alle Chunk-Feedbacks für diese Message
                        chunk_feedbacks = db_session.query(ChunkFeedbackModel).filter(
                            ChunkFeedbackModel.chat_message_id == message_id
                        ).all()
                        for cf in chunk_feedbacks:
                            chunk_feedback_map[cf.chunk_id] = cf.rating
                except Exception as e:
                    print(f"DEBUG: Fehler beim Laden von Chunk-Feedback: {e}")
                
                # Extrahiere Query aus extended_metadata (analytics.query) falls vorhanden
                # Fallback: Verwende query_text (kann Assistant-Content sein)
                actual_query = query_text
                if extended_metadata and 'analytics' in extended_metadata:
                    analytics_query = extended_metadata.get('analytics', {}).get('query')
                    if analytics_query:
                        actual_query = analytics_query
                
                # Extrahiere Scores und Feedback
                search_results = []
                relevance_scores = []
                feedback_ratings = []
                hybrid_scores = []
                ml_scores = []
                
                for i, chunk_data in enumerate(source_chunks):
                    # Chunk-Daten
                    chunk_id = chunk_data.get('chunk_id', '')
                    
                    # WICHTIG: Scores aus chunk_data._extended_metadata (jeder Chunk hat eigene Scores!)
                    chunk_extended_metadata = chunk_data.get('_extended_metadata', {})
                    hybrid_score = chunk_extended_metadata.get('hybrid_score', chunk_data.get('hybrid_score', 0.5))
                    ml_score = chunk_extended_metadata.get('ml_score', chunk_data.get('ml_score'))
                    vector_score = chunk_extended_metadata.get('vector_score', chunk_data.get('vector_score'))
                    text_score = chunk_extended_metadata.get('text_score', chunk_data.get('text_score'))
                    
                    # NEU: Feedback für diesen Chunk (Chunk-Level hat Priorität über Message-Level)
                    chunk_feedback = chunk_feedback_map.get(chunk_id)
                    if chunk_feedback:
                        # Chunk-Level Feedback hat Priorität
                        feedback_ratings.append(chunk_feedback)
                        chunk_extended_metadata['feedback_rating'] = chunk_feedback  # NEU v2.10.2: Speichere in extended_metadata
                    elif feedback_rating:
                        # Fallback: Message-Level Feedback
                        feedback_ratings.append(feedback_rating)
                        chunk_extended_metadata['feedback_rating'] = feedback_rating  # NEU v2.10.2: Speichere in extended_metadata
                    else:
                        feedback_ratings.append(None)
                        chunk_extended_metadata['feedback_rating'] = None  # NEU v2.10.2: Explizit None setzen
                    
                    search_results.append({
                        'chunk_id': chunk_id,
                        'relevance_score': 0.5,  # Placeholder, wird aus Feedback berechnet
                        '_extended_metadata': chunk_extended_metadata,  # NEU v2.10.2: Extended Metadata mit Feedback mitgeben
                        'text_score': text_score,  # NEU v2.10.5: Text-Score für semantische Relevanz
                        'vector_score': vector_score  # NEU v2.10.5: Vector-Score für semantische Relevanz
                    })
                    hybrid_scores.append(hybrid_score)
                    if ml_score is not None:
                        ml_scores.append(ml_score)
                
                # NEU v2.10.0: Metriken werden auch ohne Feedback berechnet (basierend auf Scores)
                has_feedback = any(f for f in feedback_ratings if f is not None)
                
                # NEU v2.10.1: Extrahiere Filter-Informationen aus message_metadata
                # NEU v2.10.3: Extrahiere auch AI-Modell-Einstellungen
                filters_applied = {}
                score_threshold = None
                top_k_limit = None
                temperature = None
                max_tokens = None
                top_p = None
                try:
                    if extended_metadata and isinstance(extended_metadata, dict):
                        # Prüfe ob Filter in extended_metadata gespeichert sind
                        if 'filters' in extended_metadata:
                            filters_applied = extended_metadata.get('filters', {})
                        if 'score_threshold' in extended_metadata:
                            score_threshold = extended_metadata.get('score_threshold')
                        if 'top_k' in extended_metadata:
                            top_k_limit = extended_metadata.get('top_k')
                    # Fallback: Prüfe message_metadata direkt
                    if message_metadata:
                        if 'query_params' in message_metadata:
                            query_params = message_metadata.get('query_params', {})
                            if 'filters' in query_params:
                                filters_applied = query_params.get('filters', {})
                            if 'score_threshold' in query_params:
                                score_threshold = query_params.get('score_threshold')
                            if 'top_k' in query_params:
                                top_k_limit = query_params.get('top_k')
                            # NEU v2.10.3: AI-Modell-Einstellungen
                            if 'temperature' in query_params:
                                temperature = query_params.get('temperature')
                            if 'max_tokens' in query_params:
                                max_tokens = query_params.get('max_tokens')
                            if 'top_p' in query_params:
                                top_p = query_params.get('top_p')
                except Exception as e:
                    print(f"DEBUG: Fehler beim Extrahieren von Filter-Informationen: {e}")
                
                # NEU v2.10.5: Extrahiere Text-Scores und Vector-Scores für semantische Relevanz
                text_scores = []
                vector_scores = []
                for result in search_results:
                    text_score = result.get('text_score') or result.get('_extended_metadata', {}).get('text_score')
                    vector_score = result.get('vector_score') or result.get('_extended_metadata', {}).get('vector_score')
                    text_scores.append(text_score if text_score is not None else 0.0)
                    vector_scores.append(vector_score if vector_score is not None else 0.0)
                
                # Berechne Metriken (auch ohne Feedback - verwendet Scores als Proxy)
                metrics = metrics_service.calculate_metrics(
                    query=actual_query or "Unknown",  # NEU: Verwende actual_query (aus analytics.query)
                    search_results=search_results,
                    relevance_scores=None,  # Wird aus Feedback oder Scores berechnet
                    feedback_ratings=feedback_ratings if has_feedback else None,
                    hybrid_scores=hybrid_scores if hybrid_scores else None,
                    ml_scores=ml_scores if ml_scores else None,
                    timestamp=created_at,
                    filters_applied=filters_applied if filters_applied else None,
                    score_threshold=score_threshold,
                    top_k_limit=top_k_limit,
                    temperature=temperature,  # NEU v2.10.3: AI Temperature
                    max_tokens=max_tokens,  # NEU v2.10.3: Max Tokens
                    top_p=top_p,  # NEU v2.10.3: Top P
                    text_scores=text_scores if text_scores else None,  # NEU v2.10.5: Text-Scores für semantische Relevanz
                    vector_scores=vector_scores if vector_scores else None,  # NEU v2.10.5: Vector-Scores für semantische Relevanz
                    chunk_repository=rag_adapter.document_chunk_repo  # NEU v2.10.5: Repository für DB-Fallback
                )
                
                # NEU v2.10.4: Integriere normalisierte Scores in source_chunks für Frontend
                # Die normalisierten Scores wurden in search_results._extended_metadata gespeichert
                if search_results and len(search_results) == len(source_chunks):
                    for i, search_result in enumerate(search_results):
                        normalized_score = search_result.get('_extended_metadata', {}).get('normalized_relevance_score')
                        if normalized_score is not None and i < len(source_chunks):
                            chunk_extended_metadata = source_chunks[i].get('_extended_metadata', {})
                            if not chunk_extended_metadata:
                                source_chunks[i]['_extended_metadata'] = chunk_extended_metadata
                            chunk_extended_metadata['normalized_relevance_score'] = normalized_score
                
                metrics.session_id = session_id_val
                metrics.user_id = user_id_val
                metrics_list.append(metrics)
            
            # Aggregiere Metriken
            aggregated = metrics_service.aggregate_metrics(metrics_list)
            
            return AggregatedSearchQualityMetricsResponse(**aggregated)
        
        else:
            # Einzelne Query-Metriken
            if not query:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Query-Parameter erforderlich für einzelne Metriken"
                )
            
            # Hole Chat-Message für diese Query
            # WICHTIG: Query ist in message_metadata.analytics.query gespeichert
            # Oder in der User-Message (content) - suche beide
            query_sql = text("""
                SELECT 
                    rcm.content,
                    rcm.session_id,
                    rcs.user_id,
                    rcm.created_at,
                    rcm.source_chunks,
                    rcm.message_metadata,
                    rf.rating as feedback_rating
                FROM rag_chat_messages rcm
                LEFT JOIN rag_chat_sessions rcs ON rcm.session_id = rcs.id
                LEFT JOIN rag_feedback rf ON rcm.id = rf.chat_message_id
                WHERE rcm.role = 'assistant'
                AND rcm.source_chunks IS NOT NULL
                AND (
                    -- Suche in message_metadata.analytics.query (JSON)
                    (rcm.message_metadata IS NOT NULL 
                     AND json_extract(rcm.message_metadata, '$.analytics.query') = :query_exact)
                    OR
                    -- Fallback: Suche in User-Message der gleichen Session
                    EXISTS (
                        SELECT 1 
                        FROM rag_chat_messages rcm_user
                        WHERE rcm_user.session_id = rcm.session_id
                        AND rcm_user.role = 'user'
                        AND rcm_user.content = :query_exact
                        AND rcm_user.created_at < rcm.created_at
                        AND rcm.created_at <= datetime(rcm_user.created_at, '+5 minutes')
                    )
                )
                ORDER BY rcm.created_at DESC
                LIMIT 1
            """)
            
            result = db_session.execute(query_sql, {"query_exact": query})
            msg = result.fetchone()
            
            if not msg:
                # DEBUG: Versuche auch mit LIKE-Suche (für ähnliche Queries)
                print(f"DEBUG: Exakte Query-Suche fehlgeschlagen für '{query}', versuche LIKE-Suche")
                query_sql_like = text("""
                    SELECT 
                        rcm.content,
                        rcm.session_id,
                        rcs.user_id,
                        rcm.created_at,
                        rcm.source_chunks,
                        rcm.message_metadata,
                        rf.rating as feedback_rating
                    FROM rag_chat_messages rcm
                    LEFT JOIN rag_chat_sessions rcs ON rcm.session_id = rcs.id
                    LEFT JOIN rag_feedback rf ON rcm.id = rf.chat_message_id
                    WHERE rcm.role = 'assistant'
                    AND rcm.source_chunks IS NOT NULL
                    AND (
                        -- Suche in message_metadata.analytics.query (JSON) mit LIKE
                        (rcm.message_metadata IS NOT NULL 
                         AND json_extract(rcm.message_metadata, '$.analytics.query') LIKE :query_pattern)
                        OR
                        -- Fallback: Suche in User-Message der gleichen Session mit LIKE
                        EXISTS (
                            SELECT 1 
                            FROM rag_chat_messages rcm_user
                            WHERE rcm_user.session_id = rcm.session_id
                            AND rcm_user.role = 'user'
                            AND rcm_user.content LIKE :query_pattern
                            AND rcm_user.created_at < rcm.created_at
                            AND rcm.created_at <= datetime(rcm_user.created_at, '+5 minutes')
                        )
                    )
                    ORDER BY rcm.created_at DESC
                    LIMIT 1
                """)
                result_like = db_session.execute(query_sql_like, {"query_pattern": f"%{query}%"})
                msg = result_like.fetchone()
                
                if not msg:
                    print(f"DEBUG: Auch LIKE-Suche fehlgeschlagen für '{query}'")
                    # NEU: Versuche auch nach Messages mit Feedback zu suchen und Query zu extrahieren
                    print(f"DEBUG: Versuche Suche nach Messages mit Feedback")
                    query_sql_feedback = text("""
                        SELECT 
                            rcm.content,
                            rcm.session_id,
                            rcs.user_id,
                            rcm.created_at,
                            rcm.source_chunks,
                            rcm.message_metadata,
                            rf.rating as feedback_rating,
                            rcm.id as message_id
                        FROM rag_chat_messages rcm
                        LEFT JOIN rag_chat_sessions rcs ON rcm.session_id = rcs.id
                        INNER JOIN rag_feedback rf ON rcm.id = rf.chat_message_id
                        WHERE rcm.role = 'assistant'
                        AND rcm.source_chunks IS NOT NULL
                        AND rcm.message_metadata IS NOT NULL
                        ORDER BY rcm.created_at DESC
                        LIMIT 10
                    """)
                    result_feedback = db_session.execute(query_sql_feedback)
                    messages_with_feedback = result_feedback.fetchall()
                    
                    # Prüfe jede Message, ob die Query übereinstimmt
                    for msg_candidate in messages_with_feedback:
                        try:
                            import json
                            message_metadata_candidate = json.loads(msg_candidate[5]) if msg_candidate[5] else {}
                            stored_query = message_metadata_candidate.get('analytics', {}).get('query', '')
                            print(f"DEBUG: Prüfe Message {msg_candidate[7]}: stored_query='{stored_query}', search_query='{query}'")
                            if stored_query:
                                # Prüfe exakte Übereinstimmung oder Teilstring
                                if stored_query.lower() == query.lower() or query.lower() in stored_query.lower() or stored_query.lower() in query.lower():
                                    print(f"DEBUG: Message gefunden durch Feedback-Suche: Query '{stored_query}' passt zu '{query}'")
                                    msg = msg_candidate
                                    break
                        except Exception as e:
                            print(f"DEBUG: Fehler beim Prüfen der Message: {e}")
                            continue
                    
                    if not msg:
                        # WICHTIG: Kein Fallback zu aggregierten Metriken - wirf expliziten Fehler
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Keine Chat-Message für Query '{query}' gefunden. "
                                   f"Bitte stelle sicher, dass: "
                                   f"1) Die Query in message_metadata.analytics.query gespeichert ist, "
                                   f"2) Feedback für diese Message vorhanden ist, "
                                   f"3) Die Query exakt übereinstimmt (Groß-/Kleinschreibung, Leerzeichen)."
                        )
                else:
                    print(f"DEBUG: Message mit LIKE-Suche gefunden für '{query}'")
            
            # Extrahiere Message-Daten (mit message_id falls vorhanden)
            if len(msg) == 8:
                content, session_id_val, user_id_val, created_at, source_chunks_json, message_metadata_json, feedback_rating, message_id = msg
            else:
                content, session_id_val, user_id_val, created_at, source_chunks_json, message_metadata_json, feedback_rating = msg
                message_id = None
            
            # Parse source_chunks und message_metadata
            import json
            try:
                source_chunks = json.loads(source_chunks_json) if source_chunks_json else []
                message_metadata = json.loads(message_metadata_json) if message_metadata_json else {}
                # Hole extended_metadata aus message_metadata.analytics.scores (für Scores)
                # extended_metadata enthält hybrid_score, ml_score, etc.
                extended_metadata = {}
                if message_metadata.get('analytics', {}).get('scores'):
                    # Nimm extended_metadata vom ersten Score (alle haben ähnliche Werte)
                    extended_metadata = message_metadata['analytics']['scores'][0].get('_extended_metadata', {})
            except:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Fehler beim Parsen der Chat-Message-Daten"
                )
            
            if not source_chunks:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Keine Source Chunks für diese Query gefunden"
                )
            
            # Extrahiere Scores und Feedback
            search_results = []
            relevance_scores = []
            feedback_ratings = []
            hybrid_scores = []
            ml_scores = []
            
            # NEU: Hole Chunk-Level Feedback aus der Datenbank
            from backend.app.models import ChunkFeedbackModel
            chunk_feedback_map = {}  # chunk_id -> rating
            try:
                # Hole die message_id aus der Assistant-Message
                assistant_msg_query = text("""
                    SELECT id FROM rag_chat_messages
                    WHERE session_id = :session_id
                    AND role = 'assistant'
                    AND created_at = :created_at
                    LIMIT 1
                """)
                msg_result = db_session.execute(assistant_msg_query, {
                    "session_id": session_id_val,
                    "created_at": created_at_dt if 'created_at_dt' in locals() else created_at
                })
                msg_row = msg_result.fetchone()
                if msg_row:
                    message_id = msg_row[0]
                    # Hole alle Chunk-Feedbacks für diese Message
                    chunk_feedbacks = db_session.query(ChunkFeedbackModel).filter(
                        ChunkFeedbackModel.chat_message_id == message_id
                    ).all()
                    for cf in chunk_feedbacks:
                        chunk_feedback_map[cf.chunk_id] = cf.rating
            except Exception as e:
                print(f"DEBUG: Fehler beim Laden von Chunk-Feedback: {e}")
            
            for chunk_data in source_chunks:
                chunk_id = chunk_data.get('chunk_id', '')
                
                # WICHTIG: Scores aus chunk_data._extended_metadata (jeder Chunk hat eigene Scores!)
                chunk_extended_metadata = chunk_data.get('_extended_metadata', {})
                hybrid_score = chunk_extended_metadata.get('hybrid_score', chunk_data.get('hybrid_score', 0.5))
                ml_score = chunk_extended_metadata.get('ml_score', chunk_data.get('ml_score'))
                vector_score = chunk_extended_metadata.get('vector_score', chunk_data.get('vector_score'))
                text_score = chunk_extended_metadata.get('text_score', chunk_data.get('text_score'))
                
                # NEU v2.10.5: Speichere chunk_text in extended_metadata für Query-Term-Matching
                # WICHTIG: Nur reale Werte verwenden - KEINE Fallbacks!
                # chunk_text aus chunk_data oder _extended_metadata (nur wenn wirklich vorhanden)
                # WICHTIG: chunk_text kann in chunk_data direkt sein ODER in chunk_extended_metadata
                chunk_text = (
                    chunk_data.get('chunk_text', '') or 
                    chunk_extended_metadata.get('chunk_text', '') or
                    chunk_data.get('_extended_metadata', {}).get('chunk_text', '')  # Fallback: Prüfe auch verschachteltes _extended_metadata
                )
                if chunk_text:
                    chunk_extended_metadata['chunk_text'] = chunk_text
                    chunk_extended_metadata['chunk_text_source'] = 'metadata'
                # KEIN Fallback zu text_excerpt - nur reale Werte!
                
                # NEU: Feedback für diesen Chunk (Chunk-Level hat Priorität über Message-Level)
                chunk_feedback = chunk_feedback_map.get(chunk_id)
                if chunk_feedback:
                    # Chunk-Level Feedback hat Priorität
                    feedback_ratings.append(chunk_feedback)
                    chunk_extended_metadata['feedback_rating'] = chunk_feedback  # NEU v2.10.2: Speichere in extended_metadata
                elif feedback_rating:
                    # Fallback: Message-Level Feedback
                    feedback_ratings.append(feedback_rating)
                    chunk_extended_metadata['feedback_rating'] = feedback_rating  # NEU v2.10.2: Speichere in extended_metadata
                else:
                    feedback_ratings.append(None)
                    chunk_extended_metadata['feedback_rating'] = None  # NEU v2.10.2: Explizit None setzen
                
                search_results.append({
                    'chunk_id': chunk_id,
                    'relevance_score': 0.5,  # Placeholder, wird aus Feedback berechnet
                    '_extended_metadata': chunk_extended_metadata,  # NEU v2.10.2: Extended Metadata mit Feedback mitgeben
                    'text_score': chunk_extended_metadata.get('text_score'),  # NEU v2.10.5: Text-Score für semantische Relevanz
                    'vector_score': chunk_extended_metadata.get('vector_score')  # NEU v2.10.5: Vector-Score für semantische Relevanz
                })
                hybrid_scores.append(hybrid_score)
                if ml_score is not None:
                    ml_scores.append(ml_score)
            
            # WICHTIG: Wenn Feedback vorhanden ist, verwende es für Relevance Scores
            # Setze relevance_scores auf None, damit _calculate_relevance_from_feedback aufgerufen wird
            has_feedback = any(f for f in feedback_ratings if f is not None)
            num_feedback_items = sum(1 for f in feedback_ratings if f is not None)
            
            # Konvertiere created_at zu datetime falls es ein String ist
            from datetime import datetime
            if isinstance(created_at, str):
                try:
                    created_at_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_at_dt = created_at_dt.replace(tzinfo=None) if created_at_dt.tzinfo else created_at_dt
                except:
                    created_at_dt = datetime.now()
            else:
                created_at_dt = created_at
            
            # NEU v2.10.1: Extrahiere Filter-Informationen aus message_metadata
            # NEU v2.10.3: Extrahiere auch AI-Modell-Einstellungen
            filters_applied = {}
            score_threshold = None
            top_k_limit = None
            temperature = None
            max_tokens = None
            top_p = None
            try:
                if message_metadata and 'query_params' in message_metadata:
                    query_params = message_metadata.get('query_params', {})
                    if 'filters' in query_params:
                        filters_applied = query_params.get('filters', {})
                    if 'score_threshold' in query_params:
                        score_threshold = query_params.get('score_threshold')
                    if 'top_k' in query_params:
                        top_k_limit = query_params.get('top_k')
                    # NEU v2.10.3: AI-Modell-Einstellungen
                    if 'temperature' in query_params:
                        temperature = query_params.get('temperature')
                    if 'max_tokens' in query_params:
                        max_tokens = query_params.get('max_tokens')
                    if 'top_p' in query_params:
                        top_p = query_params.get('top_p')
            except Exception as e:
                print(f"DEBUG: Fehler beim Extrahieren von Filter-Informationen: {e}")
            
            # NEU v2.10.5: Extrahiere Text-Scores und Vector-Scores für semantische Relevanz
            text_scores = []
            vector_scores = []
            for result in search_results:
                text_score = result.get('text_score') or result.get('_extended_metadata', {}).get('text_score')
                vector_score = result.get('vector_score') or result.get('_extended_metadata', {}).get('vector_score')
                text_scores.append(text_score if text_score is not None else 0.0)
                vector_scores.append(vector_score if vector_score is not None else 0.0)
            
            # Berechne Metriken
            metrics = metrics_service.calculate_metrics(
                query=query,
                search_results=search_results,
                relevance_scores=None if has_feedback else None,  # Wird aus Feedback berechnet
                feedback_ratings=feedback_ratings if has_feedback else None,
                hybrid_scores=hybrid_scores if hybrid_scores else None,
                ml_scores=ml_scores if ml_scores else None,
                timestamp=created_at_dt,
                filters_applied=filters_applied if filters_applied else None,
                score_threshold=score_threshold,
                top_k_limit=top_k_limit,
                temperature=temperature,  # NEU v2.10.3: AI Temperature
                max_tokens=max_tokens,  # NEU v2.10.3: Max Tokens
                top_p=top_p,  # NEU v2.10.3: Top P
                text_scores=text_scores if text_scores else None,  # NEU v2.10.5: Text-Scores für semantische Relevanz
                vector_scores=vector_scores if vector_scores else None,  # NEU v2.10.5: Vector-Scores für semantische Relevanz
                chunk_repository=rag_adapter.chunk_repository  # NEU v2.10.5: Repository für Chunk-Text aus DB
            )
            
            # NEU v2.10.4: Erstelle Mapping von chunk_id zu normalisiertem Relevance Score
            # Die normalisierten Scores wurden in search_results._extended_metadata gespeichert
            # WICHTIG: search_results wird per Referenz übergeben, daher sollten die Änderungen sichtbar sein
            normalized_scores_map: Dict[str, float] = {}
            if search_results:
                for search_result in search_results:
                    chunk_id = search_result.get('chunk_id', '')
                    # Prüfe ob _extended_metadata vorhanden ist
                    extended_metadata = search_result.get('_extended_metadata', {})
                    normalized_score = extended_metadata.get('normalized_relevance_score')
                    
                    if normalized_score is not None and chunk_id:
                        normalized_scores_map[chunk_id] = normalized_score
                    elif chunk_id:
                        # Fallback: Berechne normalisierten Score aus hybrid_score falls vorhanden
                        hybrid_score = extended_metadata.get('hybrid_score')
                        if hybrid_score is not None:
                            # Verwende hybrid_score als Proxy (wird später normalisiert)
                            normalized_scores_map[chunk_id] = max(0.0, min(1.0, float(hybrid_score)))
            
            # DEBUG: Nur loggen wenn Map leer ist (Problem-Indikator)
            if not normalized_scores_map and search_results:
                print(f"DEBUG v2.10.4: WARNUNG - Keine normalisierten Scores gefunden!")
                print(f"DEBUG v2.10.4: search_results[0] Keys: {search_results[0].keys() if search_results else 'N/A'}")
                if search_results and '_extended_metadata' in search_results[0]:
                    print(f"DEBUG v2.10.4: _extended_metadata Keys: {search_results[0]['_extended_metadata'].keys()}")
            
            metrics.session_id = session_id_val
            metrics.user_id = user_id_val
            
            # WICHTIG: Speichere Metriken in Datenbank (wenn Feedback vorhanden)
            if has_feedback and rag_adapter.search_quality_metrics_repo:
                try:
                    saved_metrics = rag_adapter.search_quality_metrics_repo.save(metrics)
                    print(f"DEBUG: Search Quality Metrics gespeichert (mit Feedback): ID={saved_metrics if hasattr(saved_metrics, 'id') else 'N/A'}")
                except Exception as save_error:
                    print(f"DEBUG: Fehler beim Speichern von Search Quality Metrics (überspringe): {save_error}")
            
            # Konvertiere zu Response
            return SearchQualityMetricsResponse(
                query=metrics.query,
                timestamp=metrics.timestamp.isoformat(),
                precision_at_1=metrics.precision_at_1,
                precision_at_3=metrics.precision_at_3,
                precision_at_5=metrics.precision_at_5,
                precision_at_10=metrics.precision_at_10,
                recall_at_1=metrics.recall_at_1,
                recall_at_3=metrics.recall_at_3,
                recall_at_5=metrics.recall_at_5,
                recall_at_10=metrics.recall_at_10,
                ndcg_at_1=metrics.ndcg_at_1,
                ndcg_at_3=metrics.ndcg_at_3,
                ndcg_at_5=metrics.ndcg_at_5,
                ndcg_at_10=metrics.ndcg_at_10,
                mrr=metrics.mrr,
                average_relevance_score=metrics.average_relevance_score,
                num_relevant_results=metrics.num_relevant_results,
                num_total_results=metrics.num_total_results,
                has_feedback=has_feedback,
                num_feedback_items=num_feedback_items,
                hybrid_ndcg_at_10=metrics.hybrid_ndcg_at_10,
                ml_ndcg_at_10=metrics.ml_ndcg_at_10,
                session_id=metrics.session_id,
                user_id=metrics.user_id,
                document_type=metrics.document_type,
                filters_applied=metrics.filters_applied,
                score_threshold=metrics.score_threshold,
                top_k_limit=metrics.top_k_limit,
                feedback_coverage=metrics.feedback_coverage,
                temperature=metrics.temperature,  # NEU v2.10.3: AI Temperature
                max_tokens=metrics.max_tokens,  # NEU v2.10.3: Max Tokens
                top_p=metrics.top_p,  # NEU v2.10.3: Top P
                normalized_relevance_scores=normalized_scores_map if normalized_scores_map else None  # NEU v2.10.4: Normalisierte Scores
            )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Search Quality Metrics: {str(e)}"
        )


# ============================================
# TREND ANALYSIS ENDPOINTS (v2.9.0)
# ============================================

@router.get(
    "/analytics/trends",
    response_model=TrendAnalysisResponse,
    summary="Get Trend Analysis",
    description="Hole Trend-Analyse der Search Quality Metrics über Zeit."
)
async def get_trend_analysis(
    start_date: Optional[str] = Query(None, description="Start-Datum (ISO-Format, default: 7 Tage zurück)"),
    end_date: Optional[str] = Query(None, description="End-Datum (ISO-Format, default: heute)"),
    document_type: Optional[str] = Query(None, description="Filter nach Document Type"),
    user_id: Optional[int] = Query(None, description="Filter nach User ID"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """
    Hole Trend-Analyse der Search Quality Metrics.
    
    Liefert:
    - Datenpunkte über Zeit
    - Aggregierte Metriken
    - Trend-Analyse (improving/stable/degrading)
    - Alerts bei Qualitätsverschlechterung
    """
    try:
        from datetime import datetime, timedelta
        from ..infrastructure.search_quality_metrics import SearchQualityMetricsService
        from ..interface.schemas import TrendAnalysisResponse, TrendDataPoint
        
        # Default: Letzte 7 Tage
        if not end_date:
            end_date_dt = datetime.now()
        else:
            end_date_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        if not start_date:
            start_date_dt = end_date_dt - timedelta(days=7)
        else:
            start_date_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        # Hole Metriken aus Repository
        metrics_repo = rag_adapter.search_quality_metrics_repo
        metrics_list = metrics_repo.get_by_date_range(
            start_date=start_date_dt,
            end_date=end_date_dt,
            document_type=document_type,
            user_id=user_id
        )
        
        # Konvertiere zu TrendDataPoints
        data_points = []
        for metrics in metrics_list:
            data_points.append(TrendDataPoint(
                date=metrics.timestamp.isoformat() if isinstance(metrics.timestamp, datetime) else metrics.timestamp,
                query=metrics.query,
                precision_at_10=metrics.precision_at_10,
                recall_at_10=metrics.recall_at_10,
                ndcg_at_10=metrics.ndcg_at_10,
                mrr=metrics.mrr,
                session_id=metrics.session_id,
                user_id=metrics.user_id,
                document_type=metrics.document_type
            ))
        
        # Aggregiere Metriken
        metrics_service = SearchQualityMetricsService()
        aggregated = metrics_service.aggregate_metrics(metrics_list)
        
        # Trend-Analyse: Vergleiche erste und letzte Hälfte
        trends = {}
        if len(data_points) >= 4:
            mid_point = len(data_points) // 2
            first_half = data_points[:mid_point]
            second_half = data_points[mid_point:]
            
            # Berechne Durchschnitte
            first_avg_ndcg = sum(p.ndcg_at_10 for p in first_half) / len(first_half)
            second_avg_ndcg = sum(p.ndcg_at_10 for p in second_half) / len(second_half)
            
            if second_avg_ndcg > first_avg_ndcg + 0.05:
                trends['ndcg_at_10'] = 'improving'
            elif second_avg_ndcg < first_avg_ndcg - 0.05:
                trends['ndcg_at_10'] = 'degrading'
            else:
                trends['ndcg_at_10'] = 'stable'
        else:
            trends['ndcg_at_10'] = 'insufficient_data'
        
        # Alerts generieren
        alerts = []
        if len(data_points) >= 2:
            # Prüfe auf Qualitätsverschlechterung
            recent_avg = sum(p.ndcg_at_10 for p in data_points[-5:]) / min(5, len(data_points))
            older_avg = sum(p.ndcg_at_10 for p in data_points[:5]) / min(5, len(data_points))
            
            if recent_avg < older_avg - 0.1:  # 10% Verschlechterung
                alerts.append({
                    'type': 'quality_degradation',
                    'severity': 'high',
                    'message': f'Qualitätsverschlechterung erkannt: NDCG@10 von {older_avg:.2%} auf {recent_avg:.2%} gesunken',
                    'query': None,
                    'timestamp': datetime.now().isoformat(),
                    'metrics': {'ndcg_at_10': recent_avg},
                    'actionable': True,
                    'undo_available': False
                })
        
        return TrendAnalysisResponse(
            start_date=start_date_dt.isoformat(),
            end_date=end_date_dt.isoformat(),
            data_points=data_points,
            aggregated_metrics=aggregated,
            trends=trends,
            alerts=alerts
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler bei Trend-Analyse: {str(e)}"
        )


@router.get(
    "/analytics/before-after",
    response_model=BeforeAfterComparisonResponse,
    summary="Get Before/After Comparison",
    description="Vergleiche Metriken vorher/nachher für eine Query."
)
async def get_before_after_comparison(
    query: str = Query(..., description="Die Query"),
    before_date: Optional[str] = Query(None, description="Vorher-Datum (ISO-Format, default: 7 Tage vor after_date)"),
    after_date: Optional[str] = Query(None, description="Nachher-Datum (ISO-Format, default: heute)"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """
    Vergleiche Metriken vorher/nachher für eine Query.
    
    Nützlich um zu sehen, wie sich die Qualität nach Änderungen entwickelt hat.
    """
    try:
        from datetime import datetime, timedelta
        from ..interface.schemas import BeforeAfterComparisonResponse, SearchQualityMetricsResponse
        
        # Default: Nachher = heute, Vorher = 7 Tage vorher
        if not after_date:
            after_date_dt = datetime.now()
        else:
            after_date_dt = datetime.fromisoformat(after_date.replace('Z', '+00:00'))
        
        if not before_date:
            before_date_dt = after_date_dt - timedelta(days=7)
        else:
            before_date_dt = datetime.fromisoformat(before_date.replace('Z', '+00:00'))
        
        # Hole Metriken
        metrics_repo = rag_adapter.search_quality_metrics_repo
        
        # Vorher: Hole älteste Metriken für diese Query
        before_metrics_list = metrics_repo.get_by_query(query=query, limit=10)
        before_metrics_list = [m for m in before_metrics_list if m.timestamp <= before_date_dt]
        
        # Nachher: Hole neueste Metriken für diese Query
        after_metrics_list = metrics_repo.get_by_query(query=query, limit=10)
        after_metrics_list = [m for m in after_metrics_list if m.timestamp >= after_date_dt]
        
        if not before_metrics_list or not after_metrics_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Keine Metriken für Query '{query}' im angegebenen Zeitraum gefunden."
            )
        
        # Verwende Durchschnittswerte
        from ..infrastructure.search_quality_metrics import SearchQualityMetricsService
        metrics_service = SearchQualityMetricsService()
        
        before_avg = metrics_service.aggregate_metrics(before_metrics_list[:5])  # Erste 5
        after_avg = metrics_service.aggregate_metrics(after_metrics_list[:5])  # Letzte 5
        
        # Erstelle Response-Objekte
        before_response = SearchQualityMetricsResponse(
            query=query,
            timestamp=before_date_dt.isoformat(),
            precision_at_1=before_avg.get('average_precision_at_1', 0.0),
            precision_at_3=before_avg.get('average_precision_at_3', 0.0),
            precision_at_5=before_avg.get('average_precision_at_5', 0.0),
            precision_at_10=before_avg.get('average_precision_at_10', 0.0),
            recall_at_1=before_avg.get('average_recall_at_1', 0.0),
            recall_at_3=before_avg.get('average_recall_at_3', 0.0),
            recall_at_5=before_avg.get('average_recall_at_5', 0.0),
            recall_at_10=before_avg.get('average_recall_at_10', 0.0),
            ndcg_at_1=before_avg.get('average_ndcg_at_1', 0.0),
            ndcg_at_3=before_avg.get('average_ndcg_at_3', 0.0),
            ndcg_at_5=before_avg.get('average_ndcg_at_5', 0.0),
            ndcg_at_10=before_avg.get('average_ndcg_at_10', 0.0),
            mrr=before_avg.get('average_mrr', 0.0),
            average_relevance_score=before_avg.get('average_relevance_score', 0.0),
            num_relevant_results=int(before_avg.get('average_num_relevant', 0)),
            num_total_results=int(before_avg.get('average_num_total', 0)),
            hybrid_ndcg_at_10=None,
            ml_ndcg_at_10=None
        )
        
        after_response = SearchQualityMetricsResponse(
            query=query,
            timestamp=after_date_dt.isoformat(),
            precision_at_1=after_avg.get('average_precision_at_1', 0.0),
            precision_at_3=after_avg.get('average_precision_at_3', 0.0),
            precision_at_5=after_avg.get('average_precision_at_5', 0.0),
            precision_at_10=after_avg.get('average_precision_at_10', 0.0),
            recall_at_1=after_avg.get('average_recall_at_1', 0.0),
            recall_at_3=after_avg.get('average_recall_at_3', 0.0),
            recall_at_5=after_avg.get('average_recall_at_5', 0.0),
            recall_at_10=after_avg.get('average_recall_at_10', 0.0),
            ndcg_at_1=after_avg.get('average_ndcg_at_1', 0.0),
            ndcg_at_3=after_avg.get('average_ndcg_at_3', 0.0),
            ndcg_at_5=after_avg.get('average_ndcg_at_5', 0.0),
            ndcg_at_10=after_avg.get('average_ndcg_at_10', 0.0),
            mrr=after_avg.get('average_mrr', 0.0),
            average_relevance_score=after_avg.get('average_relevance_score', 0.0),
            num_relevant_results=int(after_avg.get('average_num_relevant', 0)),
            num_total_results=int(after_avg.get('average_num_total', 0)),
            hybrid_ndcg_at_10=None,
            ml_ndcg_at_10=None
        )
        
        # Berechne Verbesserungen
        improvements = {
            'precision_at_10': after_response.precision_at_10 - before_response.precision_at_10,
            'recall_at_10': after_response.recall_at_10 - before_response.recall_at_10,
            'ndcg_at_10': after_response.ndcg_at_10 - before_response.ndcg_at_10,
            'mrr': after_response.mrr - before_response.mrr
        }
        
        # Detaillierte Änderungen
        changes = []
        for metric, delta in improvements.items():
            if abs(delta) > 0.01:  # Nur signifikante Änderungen
                changes.append({
                    'metric': metric,
                    'before': getattr(before_response, metric),
                    'after': getattr(after_response, metric),
                    'delta': delta,
                    'delta_percent': (delta / getattr(before_response, metric) * 100) if getattr(before_response, metric) > 0 else 0.0,
                    'direction': 'improved' if delta > 0 else 'degraded'
                })
        
        return BeforeAfterComparisonResponse(
            query=query,
            before_date=before_date_dt.isoformat(),
            after_date=after_date_dt.isoformat(),
            before_metrics=before_response,
            after_metrics=after_response,
            improvements=improvements,
            changes=changes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler bei Vorher/Nachher Vergleich: {str(e)}"
        )


@router.get(
    "/analytics/alerts",
    response_model=List[AlertResponse],
    summary="Get Quality Alerts",
    description="Hole aktuelle Alerts bei Qualitätsverschlechterung."
)
async def get_quality_alerts(
    severity: Optional[str] = Query(None, description="Filter nach Schweregrad (low, medium, high, critical)"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """
    Hole aktuelle Alerts bei Qualitätsverschlechterung.
    
    Alerts werden automatisch generiert wenn:
    - Qualität um >10% verschlechtert
    - Metriken unter Schwellenwerte fallen
    - Signifikante Verbesserungen erkannt werden
    """
    try:
        from datetime import datetime, timedelta
        from ..interface.schemas import AlertResponse
        
        # Hole Metriken der letzten 7 Tage
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        metrics_repo = rag_adapter.search_quality_metrics_repo
        metrics_list = metrics_repo.get_by_date_range(start_date=start_date, end_date=end_date)
        
        alerts = []
        
        if len(metrics_list) >= 10:
            # Gruppiere nach Query
            from collections import defaultdict
            query_metrics = defaultdict(list)
            for m in metrics_list:
                query_metrics[m.query].append(m)
            
            # Prüfe jede Query auf Verschlechterung
            for query, query_metrics_list in query_metrics.items():
                if len(query_metrics_list) < 3:
                    continue
                
                # Sortiere nach Zeit
                query_metrics_list.sort(key=lambda x: x.timestamp)
                
                # Vergleiche erste und letzte Hälfte
                mid = len(query_metrics_list) // 2
                first_half = query_metrics_list[:mid]
                second_half = query_metrics_list[mid:]
                
                first_avg_ndcg = sum(m.ndcg_at_10 for m in first_half) / len(first_half)
                second_avg_ndcg = sum(m.ndcg_at_10 for m in second_half) / len(second_half)
                
                if second_avg_ndcg < first_avg_ndcg - 0.1:  # 10% Verschlechterung
                    severity_level = 'critical' if (first_avg_ndcg - second_avg_ndcg) > 0.2 else 'high'
                    alerts.append(AlertResponse(
                        id=len(alerts) + 1,
                        type='quality_degradation',
                        severity=severity_level,
                        message=f'Qualitätsverschlechterung für Query "{query[:50]}...": NDCG@10 von {first_avg_ndcg:.2%} auf {second_avg_ndcg:.2%} gesunken',
                        query=query,
                        timestamp=datetime.now().isoformat(),
                        metrics={'ndcg_at_10': second_avg_ndcg, 'previous_ndcg_at_10': first_avg_ndcg},
                        actionable=True,
                        undo_available=False
                    ))
        
        # Filter nach Schweregrad
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return alerts
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Alerts: {str(e)}"
        )


@router.post(
    "/analytics/undo",
    response_model=Dict[str, Any],
    summary="Undo Quality Change",
    description="Mache eine Qualitätsänderung rückgängig (z.B. nach ML-Model-Training)."
)
async def undo_quality_change(
    alert_id: int = Query(..., description="Alert ID"),
    action: str = Query(..., description="Aktion: 'revert_model' oder 'ignore_alert'"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
    rag_adapter: RAGInfrastructureAdapter = Depends(get_rag_adapter)
):
    """
    Mache eine Qualitätsänderung rückgängig.
    
    Unterstützte Aktionen:
    - 'revert_model': Stelle vorheriges ML-Modell wieder her
    - 'ignore_alert': Markiere Alert als ignoriert
    
    Returns:
        Erfolgsstatus und Details der Undo-Aktion
    """
    try:
        from datetime import datetime
        import os
        import shutil
        from pathlib import Path
        
        if action == 'revert_model':
            # Stelle vorheriges ML-Modell wieder her
            model_dir = os.getenv('ML_MODEL_DIR', 'data/ml_models')
            model_name = os.getenv('ML_MODEL_NAME', 'ltr_ranker_v1.pkl')
            model_path = os.path.join(model_dir, model_name)
            
            # Suche nach Backup
            backup_files = list(Path(model_dir).glob(f"{model_name}.backup.*"))
            if not backup_files:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Kein Backup-Modell gefunden. Undo nicht möglich."
                )
            
            # Sortiere nach Timestamp (neuestes zuerst)
            backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            latest_backup = backup_files[0]
            
            # Stelle wieder her
            shutil.copy2(latest_backup, model_path)
            
            return {
                'success': True,
                'action': 'revert_model',
                'message': f'ML-Modell wurde auf Version vom {datetime.fromtimestamp(latest_backup.stat().st_mtime).isoformat()} zurückgesetzt.',
                'backup_file': str(latest_backup),
                'timestamp': datetime.now().isoformat()
            }
        
        elif action == 'ignore_alert':
            # Markiere Alert als ignoriert (wird in zukünftiger Version in DB gespeichert)
            return {
                'success': True,
                'action': 'ignore_alert',
                'message': f'Alert {alert_id} wurde als ignoriert markiert.',
                'timestamp': datetime.now().isoformat()
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unbekannte Aktion: {action}. Unterstützt: 'revert_model', 'ignore_alert'"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Undo: {str(e)}"
        )


# ============================================
# AUTOMATISCHES ML-TRAINING ENDPOINTS (v2.9.0)
# ============================================

@router.post(
    "/ml/train",
    response_model=Dict[str, Any],
    summary="Trigger ML Model Training",
    description="Starte manuelles Training des ML-Ranking-Modells. Prüft ob genug Training-Daten vorhanden sind und trainiert das Modell neu."
)
async def trigger_ml_training(
    min_new_samples: int = Query(100, ge=10, le=10000, description="Minimale Anzahl neuer Samples für Training"),
    min_improvement: float = Query(0.01, ge=0.0, le=1.0, description="Minimale NDCG-Verbesserung für Deployment (0.01 = 1%)"),
    force: bool = Query(False, description="Erzwinge Training auch ohne neue Samples"),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session)
):
    """
    Trigger ML Model Training manuell.
    
    Startet einen Background Job, der:
    1. Prüft ob genug neue Training-Daten vorhanden sind
    2. Trainiert das Modell neu mit Cross-Validation
    3. Vergleicht mit aktuellem Modell
    4. Deployt neues Modell falls besser
    
    Returns:
        Task-ID für Status-Tracking
    """
    try:
        from ..infrastructure.background_jobs.tasks import auto_retrain_ml_model
        
        # Starte Background Job
        task = auto_retrain_ml_model.delay(
            min_new_samples=min_new_samples,
            min_improvement_threshold=min_improvement,
            force_retrain=force
        )
        
        return {
            'success': True,
            'task_id': task.id,
            'status': 'started',
            'message': f'ML-Training gestartet. Task-ID: {task.id}. Prüfe Status mit /ml/training-status/{task.id}',
            'estimated_duration_minutes': 30
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Starten des ML-Trainings: {str(e)}"
        )


@router.get(
    "/ml/training-status/{task_id}",
    response_model=Dict[str, Any],
    summary="Get ML Training Status",
    description="Hole Status eines ML-Training-Jobs."
)
async def get_ml_training_status(
    task_id: str = Path(..., description="Task-ID vom Training-Job"),
    current_user: User = Depends(get_current_user)
):
    """
    Hole Status eines ML-Training-Jobs.
    
    Returns:
        Status-Informationen:
        - state: 'PENDING', 'STARTED', 'PROGRESS', 'SUCCESS', 'FAILURE'
        - current: Fortschritt (0-100)
        - status: Status-Text
        - result: Ergebnis (falls fertig)
    """
    try:
        from ..infrastructure.background_jobs.celery_app import celery_app
        
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'task_id': task_id,
                'state': task.state,
                'current': 0,
                'total': 100,
                'status': 'Wartet auf Start...'
            }
        elif task.state == 'FAILURE':
            response = {
                'task_id': task_id,
                'state': task.state,
                'error': str(task.info),
                'status': 'Fehler beim Training'
            }
        else:
            # STARTED, PROGRESS, SUCCESS
            response = {
                'task_id': task_id,
                'state': task.state,
                'current': task.info.get('current', 0) if isinstance(task.info, dict) else 0,
                'total': task.info.get('total', 100) if isinstance(task.info, dict) else 100,
                'status': task.info.get('status', 'In Bearbeitung...') if isinstance(task.info, dict) else 'In Bearbeitung...'
            }
            
            # Falls SUCCESS: Füge Ergebnis hinzu
            if task.state == 'SUCCESS':
                response['result'] = task.result
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen des Training-Status: {str(e)}"
        )


# ============================================
# ML Model Info & Metrics Endpoints (v2.7.0)
# ============================================

@router.get(
    "/ml/model-info",
    response_model=Dict[str, Any],
    summary="Get ML Model Info",
    description="Hole Informationen über das trainierte LTR-Modell."
)
async def get_ml_model_info(
    current_user: User = Depends(get_current_user)
):
    """
    Hole ML Model-Informationen.
    
    Response:
    - model_type (lightgbm/sklearn)
    - model_version
    - model_path
    - is_ready
    - feature_names (11 Features)
    - training_date (falls vorhanden)
    - n_training_samples (falls vorhanden)
    """
    try:
        from ..infrastructure.ml.ltr_service import LTRService
        
        # Erstelle LTR Service
        ltr_service = LTRService(
            model_dir='data/ml_models',
            model_name='ltr_ranker_v1.pkl'
        )
        
        # Hole Service Info
        info = ltr_service.get_service_info()
        
        # Erweitere mit zusätzlichen Infos
        if ltr_service.is_enabled():
            # Hole Feature-Namen
            info['feature_names'] = ltr_service.inference_service.feature_extractor.feature_names
            
            # Hole Training Data Stats (falls vorhanden)
            try:
                # NEU v2.7.0: SQLite-basiert oder File-basiert
                import os
                persist_to_db = os.getenv('PERSIST_TO_DB', 'true').lower() == 'true'
                
                if persist_to_db:
                    # SQLite-basiertes Repository
                    from ..infrastructure.ml.training_data_repository_sqlite import TrainingDataRepositorySQLite
                    training_repo = TrainingDataRepositorySQLite(db_session)
                else:
                    # File-basiertes Repository (Fallback)
                    from ..infrastructure.ml.training_data_repository import FileBasedTrainingDataRepository
                    training_repo = FileBasedTrainingDataRepository()
                
                training_stats = training_repo.get_statistics()
                info['training_data_stats'] = training_stats
            except Exception:
                info['training_data_stats'] = {}
        
        return info
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Model-Info: {str(e)}"
        )


@router.get(
    "/ml/feature-importance",
    response_model=Dict[str, Any],
    summary="Get Global ML Feature Importance",
    description="Hole globale Feature Importance aus ML-Modell (aggregiert über alle Predictions)."
)
async def get_ml_feature_importance(
    current_user: User = Depends(get_current_user)
):
    """
    Hole globale ML Feature Importance.
    
    Zeigt welche Features am wichtigsten für das ML-Modell sind.
    """
    try:
        from ..infrastructure.ml.ltr_service import LTRService
        
        ltr_service = LTRService()
        
        if not ltr_service.is_enabled():
            return {
                'enabled': False,
                'message': 'ML-Modell nicht verfügbar',
                'feature_importance': {}
            }
        
        # Feature Importance aus sklearn Model
        if hasattr(ltr_service.inference_service.model, 'feature_importances_'):
            # sklearn GradientBoostingRegressor
            importances = ltr_service.inference_service.model.feature_importances_
            feature_names = ltr_service.inference_service.feature_extractor.feature_names
            
            feature_importance = {
                feature_names[i]: float(importances[i])
                for i in range(len(feature_names))
            }
        else:
            # Fallback: Gleichmäßige Verteilung
            feature_names = ltr_service.inference_service.feature_extractor.feature_names
            feature_importance = {name: 1.0 / len(feature_names) for name in feature_names}
        
        # Sortiere nach Wichtigkeit
        sorted_importance = dict(sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        ))
        
        return {
            'enabled': True,
            'feature_importance': sorted_importance,
            'model_type': ltr_service.inference_service.model_type
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen der Feature Importance: {str(e)}"
        )


# ============================================
# Background Jobs Endpoints (Celery + Redis)
# ============================================

@router.get(
    "/shap-tasks/{task_id}",
    response_model=Dict[str, Any],
    summary="Get SHAP Task Status",
    description="Hole Status eines SHAP Background-Tasks (Async SHAP-Berechnung)."
)
async def get_shap_task_status(
    task_id: str = Path(..., description="Celery Task-ID"),
    current_user: User = Depends(get_current_user)
):
    """
    Hole Status eines SHAP Background-Tasks.
    
    Response:
    - task_id: Task-ID
    - status: PENDING | STARTED | PROGRESS | SUCCESS | FAILURE
    - current: Fortschritt (0-100)
    - total: Total (100)
    - result: SHAP-Explanation (nur bei SUCCESS)
    - error: Fehlermeldung (nur bei FAILURE)
    """
    try:
        from celery.result import AsyncResult
        
        # Hole Task-Result
        task_result = AsyncResult(task_id)
        
        # Status-Mapping
        response = {
            'task_id': task_id,
            'status': task_result.state,
            'current': 0,
            'total': 100,
            'result': None,
            'error': None
        }
        
        # Bei SUCCESS: Hole Ergebnis
        if task_result.state == 'SUCCESS':
            response['result'] = task_result.result
            response['current'] = 100
        
        # Bei PROGRESS: Hole Meta-Info
        elif task_result.state == 'PROGRESS' or task_result.state == 'STARTED':
            info = task_result.info
            if info:
                response['current'] = info.get('current', 0)
                response['total'] = info.get('total', 100)
                response['status_text'] = info.get('status', '')
        
        # Bei FAILURE: Hole Fehler
        elif task_result.state == 'FAILURE':
            info = task_result.info
            if info and isinstance(info, dict):
                response['error'] = info.get('error', str(task_result.result))
            else:
                response['error'] = str(task_result.result)
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen des Task-Status: {str(e)}"
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
