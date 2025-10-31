"""
Integration Tests: Document Type Counts

TDD: RED → GREEN → REFACTOR
Testet dass Document Type Counts korrekt zurückgegeben werden.
"""

import pytest
from sqlalchemy.orm import Session
from contexts.ragintegration.infrastructure.repositories import (
    SQLAlchemyIndexedDocumentRepository
)
from backend.app.database import SessionLocal


class TestDocumentTypeCounts:
    """Integration Tests für Document Type Counts."""

    @pytest.fixture
    def db_session(self):
        """Erstelle DB Session für Tests."""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    @pytest.fixture
    def indexed_doc_repo(self, db_session: Session):
        """Erstelle IndexedDocumentRepository."""
        return SQLAlchemyIndexedDocumentRepository(db_session)

    def test_count_by_document_type_exists(self, indexed_doc_repo: SQLAlchemyIndexedDocumentRepository):
        """Test: count_by_document_type Methode existiert."""
        # RED: Diese Methode existiert noch nicht
        assert hasattr(indexed_doc_repo, 'count_by_document_type')
        
        # Test dass es funktioniert
        count = indexed_doc_repo.count_by_document_type(document_type_id=1)
        assert isinstance(count, int)
        assert count >= 0

    def test_count_by_document_type_returns_correct_count(self, indexed_doc_repo: SQLAlchemyIndexedDocumentRepository):
        """Test: count_by_document_type gibt korrekte Anzahl zurück."""
        # Dieser Test erfordert Test-Daten
        # Für jetzt testen wir nur dass die Methode existiert und funktioniert
        count = indexed_doc_repo.count_by_document_type(document_type_id=999)  # Nicht-existierender Type
        assert count == 0



