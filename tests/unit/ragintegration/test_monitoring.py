"""
TDD Tests für RAG Monitoring Service

Testet Metriken-Sammlung für:
- RAG-Qualität
- Token-Verbrauch
- Chunking-Performance
"""
import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta
from contexts.ragintegration.infrastructure.monitoring import RAGMonitoringService, RAGMetrics
from contexts.ragintegration.domain.entities import ChatMessage, ChatSession


class TestRAGMonitoringService:
    """TDD Tests für RAG Monitoring Service."""
    
    def test_collect_metrics_basic(self):
        """Test: Basis-Metriken werden gesammelt."""
        # Mock Repositories
        mock_chat_message_repo = Mock()
        mock_chat_session_repo = Mock()
        mock_indexed_doc_repo = Mock()
        mock_document_chunk_repo = Mock()
        
        # Mock: Sessions
        mock_session = ChatSession(
            id=1,
            user_id=1,
            session_name="Test Session",
            last_message_at=datetime.now(),
            is_active=True,
            created_at=datetime.now()
        )
        mock_chat_session_repo.get_all.return_value = [mock_session]
        
        # Mock: Messages
        user_message = ChatMessage(
            id=1,
            session_id=1,
            role="user",
            content="Test Frage",
            source_references=[],
            ai_model_used=None,
            created_at=datetime.now()
        )
        assistant_message = ChatMessage(
            id=2,
            session_id=1,
            role="assistant",
            content="Test Antwort",
            source_references=[],
            ai_model_used="gpt-4o-mini",
            created_at=datetime.now(),
            metadata={
                "tokens_used": 100,
                "processing_time_ms": 500
            }
        )
        mock_chat_message_repo.get_by_session_id.return_value = [user_message, assistant_message]
        
        # Mock: Indexed Documents
        mock_indexed_doc_repo.get_all.return_value = []
        mock_document_chunk_repo.get_by_indexed_document_id.return_value = []
        
        service = RAGMonitoringService(
            chat_message_repository=mock_chat_message_repo,
            chat_session_repository=mock_chat_session_repo,
            indexed_document_repository=mock_indexed_doc_repo,
            document_chunk_repository=mock_document_chunk_repo
        )
        
        metrics = service.collect_metrics()
        
        # Prüfe Basis-Metriken
        assert metrics.total_queries == 1
        assert metrics.successful_queries == 1
        assert metrics.failed_queries == 0
        assert metrics.average_tokens_used == 100.0
        assert metrics.average_processing_time_ms == 500.0
    
    def test_get_token_optimization_metrics(self):
        """Test: Token-Optimierungs-Metriken werden berechnet."""
        # Mock Repositories
        mock_chat_message_repo = Mock()
        mock_chat_session_repo = Mock()
        mock_indexed_doc_repo = Mock()
        mock_document_chunk_repo = Mock()
        
        # Mock: Keine Sessions/Messages (vereinfachter Test)
        mock_chat_session_repo.get_all.return_value = []
        mock_chat_message_repo.get_by_session_id.return_value = []
        
        # Mock: Chunks mit strukturierten Texten
        from contexts.ragintegration.domain.entities import DocumentChunk
        from contexts.ragintegration.domain.value_objects import ChunkMetadata
        
        mock_chunk = DocumentChunk(
            id=1,
            indexed_document_id=1,
            chunk_id="doc_1_section_1",
            chunk_text="Dies ist ein strukturierter Text-Chunk. " * 100,  # ~4000 Zeichen
            metadata=ChunkMetadata(
                page_numbers=[1],
                heading_hierarchy=["Einleitung"],
                chunk_type="section",
                token_count=1000
            ),
            qdrant_point_id="uuid-123",
            created_at=datetime.now()
        )
        
        mock_indexed_doc_repo.get_all.return_value = [Mock(id=1)]
        mock_document_chunk_repo.get_by_indexed_document_id.return_value = [mock_chunk]
        
        service = RAGMonitoringService(
            chat_message_repository=mock_chat_message_repo,
            chat_session_repository=mock_chat_session_repo,
            indexed_document_repository=mock_indexed_doc_repo,
            document_chunk_repository=mock_document_chunk_repo
        )
        
        metrics = service.get_token_optimization_metrics()
        
        # Prüfe dass Metriken berechnet wurden
        assert "current_average_tokens" in metrics
        assert "estimated_tokens_before_optimization" in metrics
        assert "estimated_tokens_after_optimization" in metrics
        assert "token_reduction_percent" in metrics
        assert metrics["token_reduction_percent"] > 0  # Sollte Reduktion zeigen
    
    def test_get_quality_metrics(self):
        """Test: Qualitäts-Metriken werden berechnet."""
        # Mock Repositories
        mock_chat_message_repo = Mock()
        mock_chat_session_repo = Mock()
        mock_indexed_doc_repo = Mock()
        mock_document_chunk_repo = Mock()
        
        # Mock: Sessions und Messages
        mock_session = ChatSession(
            id=1,
            user_id=1,
            session_name="Test Session",
            last_message_at=datetime.now(),
            is_active=True,
            created_at=datetime.now()
        )
        mock_chat_session_repo.get_all.return_value = [mock_session]
        
        user_message = ChatMessage(
            id=1,
            session_id=1,
            role="user",
            content="Test Frage",
            source_references=[],
            ai_model_used=None,
            created_at=datetime.now()
        )
        assistant_message = ChatMessage(
            id=2,
            session_id=1,
            role="assistant",
            content="Test Antwort",
            source_references=[],
            ai_model_used="gpt-4o-mini",
            created_at=datetime.now()
        )
        mock_chat_message_repo.get_by_session_id.return_value = [user_message, assistant_message]
        
        # Mock: Indexed Documents
        mock_indexed_doc_repo.get_all.return_value = []
        mock_document_chunk_repo.get_by_indexed_document_id.return_value = []
        
        service = RAGMonitoringService(
            chat_message_repository=mock_chat_message_repo,
            chat_session_repository=mock_chat_session_repo,
            indexed_document_repository=mock_indexed_doc_repo,
            document_chunk_repository=mock_document_chunk_repo
        )
        
        metrics = service.get_quality_metrics()
        
        # Prüfe dass Qualitäts-Metriken berechnet wurden
        assert "quality_score" in metrics
        assert "total_feedback" in metrics
        assert "success_rate" in metrics
        assert metrics["success_rate"] >= 0
        assert metrics["success_rate"] <= 100

