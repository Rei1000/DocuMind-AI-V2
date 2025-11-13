"""
Monitoring Router für RAG-System

Stellt Endpoints bereit für:
- RAG-Metriken abrufen
- Token-Optimierungs-Metriken
- Qualitäts-Metriken
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from contexts.ragintegration.infrastructure.monitoring import RAGMonitoringService
from contexts.ragintegration.infrastructure.adapters import RAGInfrastructureAdapter
from backend.app.database import get_db_session
from contexts.accesscontrol.interface.guard_router import get_current_user
from contexts.accesscontrol.domain.entities import User

router = APIRouter(prefix="/api/rag/monitoring", tags=["RAG Monitoring"])


def get_monitoring_service(
    db_session: Session = Depends(get_db_session)
) -> RAGMonitoringService:
    """Erstelle Monitoring Service."""
    from contexts.ragintegration.infrastructure.adapters import get_rag_adapter
    rag_adapter = get_rag_adapter(db_session)
    
    return RAGMonitoringService(
        chat_message_repository=rag_adapter.chat_message_repo,
        chat_session_repository=rag_adapter.chat_session_repo,
        indexed_document_repository=rag_adapter.indexed_document_repo,
        document_chunk_repository=rag_adapter.document_chunk_repo
    )


@router.get("/metrics")
async def get_rag_metrics(
    start_date: Optional[str] = Query(None, description="Start-Datum (ISO Format)"),
    end_date: Optional[str] = Query(None, description="End-Datum (ISO Format)"),
    current_user: User = Depends(get_current_user),
    monitoring_service: RAGMonitoringService = Depends(get_monitoring_service)
):
    """
    Hole RAG-Metriken für den angegebenen Zeitraum.
    
    **RBAC:**
    - Level 1+: Alle User können Metriken sehen
    """
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        metrics = monitoring_service.collect_metrics(start, end)
        
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "total_queries": metrics.total_queries,
            "successful_queries": metrics.successful_queries,
            "failed_queries": metrics.failed_queries,
            "average_tokens_used": metrics.average_tokens_used,
            "average_processing_time_ms": metrics.average_processing_time_ms,
            "total_feedback_positive": metrics.total_feedback_positive,
            "total_feedback_negative": metrics.total_feedback_negative,
            "total_feedback_neutral": metrics.total_feedback_neutral,
            "average_relevance_score": metrics.average_relevance_score,
            "chunks_indexed": metrics.chunks_indexed,
            "documents_indexed": metrics.documents_indexed,
            "metadata": metrics.metadata
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Sammeln der Metriken: {str(e)}"
        )


@router.get("/token-optimization")
async def get_token_optimization_metrics(
    start_date: Optional[str] = Query(None, description="Start-Datum (ISO Format)"),
    end_date: Optional[str] = Query(None, description="End-Datum (ISO Format)"),
    current_user: User = Depends(get_current_user),
    monitoring_service: RAGMonitoringService = Depends(get_monitoring_service)
):
    """
    Hole Token-Optimierungs-Metriken (vorher/nachher Vergleich).
    
    **RBAC:**
    - Level 1+: Alle User können Metriken sehen
    """
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        metrics = monitoring_service.get_token_optimization_metrics(start, end)
        
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Sammeln der Token-Optimierungs-Metriken: {str(e)}"
        )


@router.get("/quality")
async def get_quality_metrics(
    start_date: Optional[str] = Query(None, description="Start-Datum (ISO Format)"),
    end_date: Optional[str] = Query(None, description="End-Datum (ISO Format)"),
    current_user: User = Depends(get_current_user),
    monitoring_service: RAGMonitoringService = Depends(get_monitoring_service)
):
    """
    Hole Qualitäts-Metriken (Feedback, Relevance Scores).
    
    **RBAC:**
    - Level 1+: Alle User können Metriken sehen
    """
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        metrics = monitoring_service.get_quality_metrics(start, end)
        
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Sammeln der Qualitäts-Metriken: {str(e)}"
        )

