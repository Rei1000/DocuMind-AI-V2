"""
Tests für Audit-Trail Use Cases

TDD: Tests FIRST für RAG Audit-Trail Use Cases
"""
import pytest
from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, MagicMock

# Imports werden funktionieren nach Use Case Implementierung
# from contexts.ragintegration.application.use_cases import LogRAGActionUseCase, GetAuditTrailUseCase
# from contexts.ragintegration.domain.entities import RAGAuditLog


class TestLogRAGActionUseCase:
    """Test LogRAGActionUseCase"""
    
    @pytest.mark.asyncio
    async def test_log_chunking_started_creates_audit_entry(self):
        """
        GIVEN: Chunking wird gestartet
        WHEN: LogRAGActionUseCase.execute()
        THEN: RAGAuditLog mit action='chunking_started' erstellt
        """
        from contexts.ragintegration.application.use_cases import LogRAGActionUseCase
        from contexts.ragintegration.domain.entities import RAGAuditLog
        
        # Mock Repository
        mock_repo = AsyncMock()
        mock_repo.save = AsyncMock(return_value=RAGAuditLog(
            id=1,
            indexed_document_id=123,
            action="chunking_started",
            user_id=1,
            timestamp=datetime.utcnow(),
            details={"strategy": "research_article"},
            status="success",
            error_message=None,
            duration_ms=None,
            tokens_used=None,
            cost_usd=None
        ))
        
        # Execute Use Case
        use_case = LogRAGActionUseCase(mock_repo)
        result = await use_case.execute(
            action="chunking_started",
            user_id=1,
            details={"strategy": "research_article"},
            indexed_document_id=123,
            status="success"
        )
        
        # Verify
        assert result.action == "chunking_started"
        assert result.user_id == 1
        assert result.indexed_document_id == 123
        assert result.details["strategy"] == "research_article"
        mock_repo.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_query_without_document_id(self):
        """
        GIVEN: Chat Query ohne indexed_document_id
        WHEN: LogRAGActionUseCase.execute()
        THEN: RAGAuditLog mit indexed_document_id=None erstellt
        """
        from contexts.ragintegration.application.use_cases import LogRAGActionUseCase
        from contexts.ragintegration.domain.entities import RAGAuditLog
        
        # Mock Repository
        mock_repo = AsyncMock()
        mock_repo.save = AsyncMock(return_value=RAGAuditLog(
            id=2,
            indexed_document_id=None,  # NULL bei Chat-Query
            action="query_executed",
            user_id=1,
            timestamp=datetime.utcnow(),
            details={"question": "What is chunking?"},
            status="success",
            error_message=None,
            duration_ms=350,
            tokens_used=180,
            cost_usd=0.02
        ))
        
        # Execute Use Case
        use_case = LogRAGActionUseCase(mock_repo)
        result = await use_case.execute(
            action="query_executed",
            user_id=1,
            details={"question": "What is chunking?"},
            indexed_document_id=None,  # Keine Document ID
            status="success",
            duration_ms=350,
            tokens_used=180,
            cost_usd=0.02
        )
        
        # Verify
        assert result.action == "query_executed"
        assert result.indexed_document_id is None
        assert result.details["question"] == "What is chunking?"
        assert result.duration_ms == 350
        mock_repo.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_failed_action_with_error_message(self):
        """
        GIVEN: Operation schlägt fehl
        WHEN: LogRAGActionUseCase.execute() mit status='failed'
        THEN: RAGAuditLog mit error_message erstellt
        """
        from contexts.ragintegration.application.use_cases import LogRAGActionUseCase
        from contexts.ragintegration.domain.entities import RAGAuditLog
        
        error_msg = "Qdrant connection timeout"
        
        # Mock Repository
        mock_repo = AsyncMock()
        mock_repo.save = AsyncMock(return_value=RAGAuditLog(
            id=3,
            indexed_document_id=123,
            action="indexing_failed",
            user_id=1,
            timestamp=datetime.utcnow(),
            details={"reason": "timeout"},
            status="failed",
            error_message=error_msg,
            duration_ms=None,
            tokens_used=None,
            cost_usd=None
        ))
        
        # Execute Use Case
        use_case = LogRAGActionUseCase(mock_repo)
        result = await use_case.execute(
            action="indexing_failed",
            user_id=1,
            details={"reason": "timeout"},
            indexed_document_id=123,
            status="failed",
            error_message=error_msg
        )
        
        # Verify
        assert result.status == "failed"
        assert result.error_message == error_msg
        mock_repo.save.assert_called_once()


class TestGetAuditTrailUseCase:
    """Test GetAuditTrailUseCase"""
    
    @pytest.mark.asyncio
    async def test_get_audit_trail_for_document(self):
        """
        GIVEN: Dokument mit mehreren Audit-Einträgen
        WHEN: GetAuditTrailUseCase.execute() mit document_id
        THEN: Liste aller Audit-Einträge zurückgegeben
        """
        from contexts.ragintegration.application.use_cases import GetAuditTrailUseCase
        from contexts.ragintegration.domain.entities import RAGAuditLog
        
        # Mock Audit Logs
        mock_logs = [
            RAGAuditLog(
                id=1,
                indexed_document_id=123,
                action="chunking_started",
                user_id=1,
                timestamp=datetime.utcnow(),
                details={},
                status="success",
                error_message=None,
                duration_ms=None,
                tokens_used=None,
                cost_usd=None
            ),
            RAGAuditLog(
                id=2,
                indexed_document_id=123,
                action="chunking_completed",
                user_id=1,
                timestamp=datetime.utcnow(),
                details={},
                status="success",
                error_message=None,
                duration_ms=1500,
                tokens_used=None,
                cost_usd=None
            )
        ]
        
        # Mock Repository
        mock_repo = AsyncMock()
        mock_repo.get_by_document_id = AsyncMock(return_value=mock_logs)
        
        # Execute Use Case
        use_case = GetAuditTrailUseCase(mock_repo)
        result = await use_case.execute(indexed_document_id=123)
        
        # Verify
        assert len(result) == 2
        assert result[0].action == "chunking_started"
        assert result[1].action == "chunking_completed"
        mock_repo.get_by_document_id.assert_called_once_with(indexed_document_id=123, limit=100)
    
    @pytest.mark.asyncio
    async def test_get_audit_trail_with_limit(self):
        """
        GIVEN: Dokument mit vielen Audit-Einträgen
        WHEN: GetAuditTrailUseCase.execute() mit limit=50
        THEN: Maximal 50 Einträge zurückgegeben
        """
        from contexts.ragintegration.application.use_cases import GetAuditTrailUseCase
        
        # Mock Repository
        mock_repo = AsyncMock()
        mock_repo.get_by_document_id = AsyncMock(return_value=[])
        
        # Execute Use Case
        use_case = GetAuditTrailUseCase(mock_repo)
        await use_case.execute(indexed_document_id=123, limit=50)
        
        # Verify limit wurde übergeben
        mock_repo.get_by_document_id.assert_called_once_with(indexed_document_id=123, limit=50)
    
    @pytest.mark.asyncio
    async def test_get_audit_trail_for_user(self):
        """
        GIVEN: User mit mehreren Aktionen
        WHEN: GetAuditTrailUseCase.execute() mit user_id
        THEN: Alle Aktionen des Users zurückgegeben
        """
        from contexts.ragintegration.application.use_cases import GetAuditTrailUseCase
        
        # Mock Repository
        mock_repo = AsyncMock()
        mock_repo.get_by_user_id = AsyncMock(return_value=[])
        
        # Execute Use Case
        use_case = GetAuditTrailUseCase(mock_repo)
        await use_case.execute(user_id=1)
        
        # Verify
        mock_repo.get_by_user_id.assert_called_once_with(user_id=1, limit=100)

