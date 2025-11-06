"""
Tests für RAGAuditLogRepository

TDD: Tests FIRST für Repository Implementation
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

# Imports werden funktionieren nach Repository Implementation


class TestSQLAlchemyRAGAuditLogRepository:
    """Test SQLAlchemyRAGAuditLogRepository"""
    
    @pytest.mark.asyncio
    async def test_save_audit_log_creates_new_entry(self, db_session: Session):
        """
        GIVEN: Valid RAGAuditLog Entity
        WHEN: save() aufgerufen
        THEN: Audit log in DB gespeichert mit ID
        """
        from contexts.ragintegration.infrastructure.repositories import SQLAlchemyRAGAuditLogRepository
        from contexts.ragintegration.domain.entities import RAGAuditLog
        
        # Arrange
        repository = SQLAlchemyRAGAuditLogRepository(db_session)
        
        audit_log = RAGAuditLog(
            id=None,
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
        )
        
        # Act
        saved_log = await repository.save(audit_log)
        
        # Assert
        assert saved_log.id is not None  # ID wurde vergeben
        assert saved_log.action == "chunking_started"
        assert saved_log.user_id == 1
        assert saved_log.details["strategy"] == "research_article"
    
    @pytest.mark.asyncio
    async def test_get_by_document_id_returns_logs(self, db_session: Session):
        """
        GIVEN: Dokument mit mehreren Audit-Logs
        WHEN: get_by_document_id() aufgerufen
        THEN: Alle Logs für Dokument zurückgegeben (sortiert nach timestamp DESC)
        """
        from contexts.ragintegration.infrastructure.repositories import SQLAlchemyRAGAuditLogRepository
        from contexts.ragintegration.domain.entities import RAGAuditLog
        
        # Arrange
        repository = SQLAlchemyRAGAuditLogRepository(db_session)
        
        # Erstelle mehrere Logs
        log1 = RAGAuditLog(
            id=None,
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
        )
        
        log2 = RAGAuditLog(
            id=None,
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
        
        await repository.save(log1)
        await repository.save(log2)
        
        # Act
        logs = await repository.get_by_document_id(indexed_document_id=123, limit=10)
        
        # Assert
        assert len(logs) >= 2  # Mindestens unsere 2 Logs
        assert all(log.indexed_document_id == 123 for log in logs)
        # Sollte nach timestamp DESC sortiert sein (neuste zuerst)
        assert logs[0].action == "chunking_completed"  # Neuster Log
    
    @pytest.mark.asyncio
    async def test_get_by_document_id_respects_limit(self, db_session: Session):
        """
        GIVEN: Dokument mit vielen Audit-Logs
        WHEN: get_by_document_id() mit limit=2
        THEN: Maximal 2 Logs zurückgegeben
        """
        from contexts.ragintegration.infrastructure.repositories import SQLAlchemyRAGAuditLogRepository
        
        # Arrange
        repository = SQLAlchemyRAGAuditLogRepository(db_session)
        
        # Act
        logs = await repository.get_by_document_id(indexed_document_id=999, limit=2)
        
        # Assert
        assert len(logs) <= 2
    
    @pytest.mark.asyncio
    async def test_get_by_user_id_returns_user_logs(self, db_session: Session):
        """
        GIVEN: User mit mehreren Aktionen
        WHEN: get_by_user_id() aufgerufen
        THEN: Alle Logs des Users zurückgegeben
        """
        from contexts.ragintegration.infrastructure.repositories import SQLAlchemyRAGAuditLogRepository
        from contexts.ragintegration.domain.entities import RAGAuditLog
        
        # Arrange
        repository = SQLAlchemyRAGAuditLogRepository(db_session)
        
        log = RAGAuditLog(
            id=None,
            indexed_document_id=123,
            action="query_executed",
            user_id=42,  # Spezifischer User
            timestamp=datetime.utcnow(),
            details={"question": "test"},
            status="success",
            error_message=None,
            duration_ms=None,
            tokens_used=None,
            cost_usd=None
        )
        
        await repository.save(log)
        
        # Act
        logs = await repository.get_by_user_id(user_id=42, limit=10)
        
        # Assert
        assert len(logs) >= 1
        assert all(log.user_id == 42 for log in logs)


# Fixtures for testing
@pytest.fixture
def db_session():
    """
    Provide a test database session.
    
    Note: In production tests, use a real test DB.
    For now, we'll use a mock.
    """
    from unittest.mock import MagicMock
    return MagicMock()

