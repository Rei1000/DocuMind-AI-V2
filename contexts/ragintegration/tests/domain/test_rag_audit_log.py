"""
Tests für RAGAuditLog Entity

TDD: Tests FIRST für vollständige Audit-Trail Funktionalität
"""
import pytest
from datetime import datetime
from typing import Dict, Any

# Import wird nach Entity-Erstellung funktionieren
# from contexts.ragintegration.domain.entities import RAGAuditLog


class TestRAGAuditLog:
    """Test RAGAuditLog Entity"""
    
    def test_create_audit_log_with_required_fields(self):
        """
        GIVEN: Valid audit log data
        WHEN: RAGAuditLog erstellt
        THEN: Entity ist valide
        """
        # Dieser Test wird RED sein bis wir die Entity erstellen
        from contexts.ragintegration.domain.entities import RAGAuditLog
        
        audit_log = RAGAuditLog(
            id=None,
            indexed_document_id=123,
            action="chunking_started",
            user_id=1,
            timestamp=datetime.utcnow(),
            details={"strategy": "research_article", "document_id": 456},
            status="success",
            error_message=None,
            duration_ms=1500,
            tokens_used=250,
            cost_usd=0.05
        )
        
        assert audit_log.action == "chunking_started"
        assert audit_log.user_id == 1
        assert audit_log.indexed_document_id == 123
        assert audit_log.status == "success"
        assert audit_log.details["strategy"] == "research_article"
    
    def test_audit_log_requires_valid_action(self):
        """
        GIVEN: Audit log mit ungültigem action
        WHEN: RAGAuditLog erstellt
        THEN: ValueError raised
        """
        from contexts.ragintegration.domain.entities import RAGAuditLog
        
        with pytest.raises(ValueError, match="Invalid action"):
            RAGAuditLog(
                id=None,
                indexed_document_id=123,
                action="invalid_action",  # Ungültiger Action-Type
                user_id=1,
                timestamp=datetime.utcnow(),
                details={},
                status="success",
                error_message=None,
                duration_ms=None,
                tokens_used=None,
                cost_usd=None
            )
    
    def test_audit_log_allows_null_indexed_document_id(self):
        """
        GIVEN: Audit log ohne indexed_document_id (z.B. bei Chat-Query)
        WHEN: RAGAuditLog erstellt
        THEN: Entity ist valide
        """
        from contexts.ragintegration.domain.entities import RAGAuditLog
        
        audit_log = RAGAuditLog(
            id=None,
            indexed_document_id=None,  # NULL bei Chat-Queries
            action="query_executed",
            user_id=1,
            timestamp=datetime.utcnow(),
            details={"question": "What is chunking?", "session_id": 789},
            status="success",
            error_message=None,
            duration_ms=350,
            tokens_used=180,
            cost_usd=0.02
        )
        
        assert audit_log.indexed_document_id is None
        assert audit_log.action == "query_executed"
        assert audit_log.details["question"] == "What is chunking?"
    
    def test_audit_log_with_error_status(self):
        """
        GIVEN: Audit log mit Fehler-Status
        WHEN: RAGAuditLog erstellt
        THEN: Entity enthält error_message
        """
        from contexts.ragintegration.domain.entities import RAGAuditLog
        
        error_msg = "Qdrant connection timeout"
        
        audit_log = RAGAuditLog(
            id=None,
            indexed_document_id=123,
            action="embedding_started",
            user_id=1,
            timestamp=datetime.utcnow(),
            details={"chunk_count": 50},
            status="failed",
            error_message=error_msg,
            duration_ms=None,
            tokens_used=None,
            cost_usd=None
        )
        
        assert audit_log.status == "failed"
        assert audit_log.error_message == error_msg
    
    def test_audit_log_valid_actions_list(self):
        """
        GIVEN: Liste aller validen Actions
        WHEN: RAGAuditLog mit jedem Action erstellt
        THEN: Alle sind valide
        """
        from contexts.ragintegration.domain.entities import RAGAuditLog
        
        valid_actions = [
            "chunking_started",
            "chunking_completed",
            "chunking_failed",
            "chunk_created",
            "chunk_edited",
            "chunk_deleted",
            "embedding_started",
            "embedding_completed",
            "embedding_failed",
            "indexing_started",
            "indexing_completed",
            "indexing_failed",
            "query_executed",
            "feedback_submitted"
        ]
        
        for action in valid_actions:
            audit_log = RAGAuditLog(
                id=None,
                indexed_document_id=123,
                action=action,
                user_id=1,
                timestamp=datetime.utcnow(),
                details={},
                status="success",
                error_message=None,
                duration_ms=None,
                tokens_used=None,
                cost_usd=None
            )
            
            assert audit_log.action == action
    
    def test_audit_log_details_json_serializable(self):
        """
        GIVEN: Audit log mit komplexen Details
        WHEN: Details als JSON serialisiert
        THEN: Serialisierung funktioniert
        """
        from contexts.ragintegration.domain.entities import RAGAuditLog
        import json
        
        complex_details = {
            "chunks": [
                {"id": "chunk_1", "tokens": 150},
                {"id": "chunk_2", "tokens": 200}
            ],
            "strategy": "research_article",
            "model": "gpt-4o-mini",
            "metadata": {
                "document_type": "Fachartikel",
                "page_count": 15
            }
        }
        
        audit_log = RAGAuditLog(
            id=None,
            indexed_document_id=123,
            action="chunking_completed",
            user_id=1,
            timestamp=datetime.utcnow(),
            details=complex_details,
            status="success",
            error_message=None,
            duration_ms=2500,
            tokens_used=350,
            cost_usd=0.08
        )
        
        # Prüfe ob Details JSON-serialisierbar sind
        serialized = json.dumps(audit_log.details)
        deserialized = json.loads(serialized)
        
        assert deserialized["strategy"] == "research_article"
        assert len(deserialized["chunks"]) == 2

