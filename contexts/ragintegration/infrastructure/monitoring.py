"""
Monitoring Service für RAG-System

Sammelt Metriken für:
- RAG-Qualität (Feedback, Antwortqualität)
- Token-Verbrauch (vorher/nachher)
- Chunking-Performance
- Embedding-Qualität
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from contexts.ragintegration.domain.repositories import (
    ChatMessageRepository,
    ChatSessionRepository,
    IndexedDocumentRepository,
    DocumentChunkRepository
)


@dataclass
class RAGMetrics:
    """RAG-System Metriken."""
    timestamp: datetime
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    average_tokens_used: float = 0.0
    average_processing_time_ms: float = 0.0
    total_feedback_positive: int = 0
    total_feedback_negative: int = 0
    total_feedback_neutral: int = 0
    average_relevance_score: float = 0.0
    chunks_indexed: int = 0
    documents_indexed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class RAGMonitoringService:
    """
    Monitoring Service für RAG-System.
    
    Sammelt Metriken für Performance-Monitoring und Qualitäts-Tracking.
    """
    
    def __init__(
        self,
        chat_message_repository: ChatMessageRepository,
        chat_session_repository: ChatSessionRepository,
        indexed_document_repository: IndexedDocumentRepository,
        document_chunk_repository: DocumentChunkRepository
    ):
        self.chat_message_repository = chat_message_repository
        self.chat_session_repository = chat_session_repository
        self.indexed_document_repository = indexed_document_repository
        self.document_chunk_repository = document_chunk_repository
    
    def collect_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> RAGMetrics:
        """
        Sammle RAG-Metriken für den angegebenen Zeitraum.
        
        Args:
            start_date: Start-Datum (default: 7 Tage zurück)
            end_date: End-Datum (default: jetzt)
            
        Returns:
            RAGMetrics mit allen gesammelten Metriken
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()
        
        # Hole alle Chat-Messages im Zeitraum
        # Hole alle Sessions
        all_sessions = self.chat_session_repository.get_all()
        
        all_messages = []
        for session in all_sessions:
            messages = self.chat_message_repository.get_by_session_id(session.id)
            all_messages.extend(messages)
        
        # Filtere nach Zeitraum
        filtered_messages = [
            msg for msg in all_messages
            if start_date <= msg.created_at <= end_date
        ]
        
        # Assistant-Messages (mit AI-Antworten)
        assistant_messages = [msg for msg in filtered_messages if msg.role == "assistant"]
        
        # Sammle Metriken
        total_queries = len([msg for msg in filtered_messages if msg.role == "user"])
        successful_queries = len([msg for msg in assistant_messages if msg.content and len(msg.content) > 0])
        failed_queries = total_queries - successful_queries
        
        # Token-Verbrauch
        tokens_used_list = [
            msg.metadata.get("tokens_used", 0) 
            for msg in assistant_messages 
            if msg.metadata and msg.metadata.get("tokens_used")
        ]
        average_tokens_used = sum(tokens_used_list) / len(tokens_used_list) if tokens_used_list else 0.0
        
        # Processing Time
        processing_times = [
            msg.metadata.get("processing_time_ms", 0)
            for msg in assistant_messages
            if msg.metadata and msg.metadata.get("processing_time_ms")
        ]
        average_processing_time_ms = sum(processing_times) / len(processing_times) if processing_times else 0.0
        
        # Feedback (aus RAGFeedback Repository - würde hier importiert werden)
        # TODO: Integriere RAGFeedbackRepository wenn verfügbar
        total_feedback_positive = 0
        total_feedback_negative = 0
        total_feedback_neutral = 0
        
        # Relevance Scores
        relevance_scores = []
        for msg in assistant_messages:
            if msg.source_references:
                scores = [ref.relevance_score for ref in msg.source_references]
                if scores:
                    relevance_scores.extend(scores)
        average_relevance_score = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
        
        # Indexing Metriken
        indexed_docs = self.indexed_document_repository.get_all()
        documents_indexed = len(indexed_docs)
        
        chunks_indexed = 0
        for doc in indexed_docs:
            chunks = self.document_chunk_repository.get_by_indexed_document_id(doc.id)
            chunks_indexed += len(chunks)
        
        return RAGMetrics(
            timestamp=datetime.now(),
            total_queries=total_queries,
            successful_queries=successful_queries,
            failed_queries=failed_queries,
            average_tokens_used=average_tokens_used,
            average_processing_time_ms=average_processing_time_ms,
            total_feedback_positive=total_feedback_positive,
            total_feedback_negative=total_feedback_negative,
            total_feedback_neutral=total_feedback_neutral,
            average_relevance_score=average_relevance_score,
            chunks_indexed=chunks_indexed,
            documents_indexed=documents_indexed,
            metadata={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_messages": len(filtered_messages),
                "assistant_messages": len(assistant_messages)
            }
        )
    
    def get_token_optimization_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Hole Token-Optimierungs-Metriken (vorher/nachher Vergleich).
        
        Returns:
            Dict mit Metriken für Token-Optimierung
        """
        metrics = self.collect_metrics(start_date, end_date)
        
        # Schätze "vorher" Token-Verbrauch (basierend auf Chunk-Größen)
        # Vorher: JSON würde ~27.000 Tokens haben (14.000 Zeichen * 2)
        # Nachher: Strukturierte Texte ~10.000 Tokens (40.000 Zeichen / 4)
        
        # Hole durchschnittliche Chunk-Größe
        all_chunks = []
        indexed_docs = self.indexed_document_repository.get_all()
        for doc in indexed_docs:
            chunks = self.document_chunk_repository.get_by_indexed_document_id(doc.id)
            all_chunks.extend(chunks)
        
        if all_chunks:
            avg_chunk_size = sum(len(chunk.chunk_text) for chunk in all_chunks) / len(all_chunks)
            estimated_tokens_current = avg_chunk_size / 4  # ~4 Zeichen pro Token
            estimated_tokens_before = avg_chunk_size * 2  # JSON würde ~2x mehr Tokens haben
            
            token_reduction_percent = ((estimated_tokens_before - estimated_tokens_current) / estimated_tokens_before) * 100
        else:
            estimated_tokens_current = 0
            estimated_tokens_before = 0
            token_reduction_percent = 0
        
        return {
            "current_average_tokens": metrics.average_tokens_used,
            "estimated_tokens_before_optimization": estimated_tokens_before,
            "estimated_tokens_after_optimization": estimated_tokens_current,
            "token_reduction_percent": token_reduction_percent,
            "chunks_analyzed": len(all_chunks),
            "average_chunk_size_chars": avg_chunk_size if all_chunks else 0
        }
    
    def get_quality_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Hole Qualitäts-Metriken (Feedback, Relevance Scores).
        
        Returns:
            Dict mit Qualitäts-Metriken
        """
        metrics = self.collect_metrics(start_date, end_date)
        
        total_feedback = (
            metrics.total_feedback_positive + 
            metrics.total_feedback_negative + 
            metrics.total_feedback_neutral
        )
        
        quality_score = 0.0
        if total_feedback > 0:
            # Berechne Quality Score: (positive * 1.0 + neutral * 0.5 + negative * 0.0) / total
            quality_score = (
                (metrics.total_feedback_positive * 1.0) +
                (metrics.total_feedback_neutral * 0.5) +
                (metrics.total_feedback_negative * 0.0)
            ) / total_feedback
        
        return {
            "quality_score": quality_score,
            "total_feedback": total_feedback,
            "positive_feedback": metrics.total_feedback_positive,
            "negative_feedback": metrics.total_feedback_negative,
            "neutral_feedback": metrics.total_feedback_neutral,
            "average_relevance_score": metrics.average_relevance_score,
            "success_rate": (metrics.successful_queries / metrics.total_queries * 100) if metrics.total_queries > 0 else 0.0
        }

