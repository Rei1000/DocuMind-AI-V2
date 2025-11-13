"""
Tests für RAG Feedback Repository (Infrastructure Layer)

TDD: Tests FIRST für SQLAlchemyRAGFeedbackRepository
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from contexts.ragintegration.infrastructure.repositories import SQLAlchemyRAGFeedbackRepository
from contexts.ragintegration.domain.entities import RAGFeedback


class TestSQLAlchemyRAGFeedbackRepository:
    """Test SQLAlchemyRAGFeedbackRepository"""

    @pytest.fixture
    def db_session(self):
        """Erstelle in-memory SQLite DB für Tests."""
        engine = create_engine("sqlite:///:memory:")
        from backend.app.models import Base, RAGFeedbackModel
        from contexts.ragintegration.infrastructure.models import ChatMessageModel, ChatSessionModel
        # Erstelle alle benötigten Tabellen
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def feedback_repo(self, db_session):
        """Erstelle Repository Instance."""
        return SQLAlchemyRAGFeedbackRepository(db_session)

    @pytest.mark.asyncio
    async def test_save_feedback_creates_database_entry(self, feedback_repo):
        """
        GIVEN: RAGFeedback Entity
        WHEN: save() aufgerufen
        THEN: Feedback in DB gespeichert
        """
        feedback = RAGFeedback(
            id=None,
            chat_message_id=123,
            user_id=1,
            rating="positive",
            comment="Sehr hilfreich!",
            submitted_at=datetime.utcnow()
        )

        saved = await feedback_repo.save(feedback)

        assert saved.id is not None
        assert saved.rating == "positive"
        assert saved.comment == "Sehr hilfreich!"

    @pytest.mark.asyncio
    async def test_get_by_id_returns_feedback(self, feedback_repo):
        """
        GIVEN: Gespeichertes Feedback
        WHEN: get_by_id() aufgerufen
        THEN: Feedback zurückgegeben
        """
        feedback = RAGFeedback(
            id=None,
            chat_message_id=456,
            user_id=2,
            rating="negative",
            comment=None,
            submitted_at=datetime.utcnow()
        )
        saved = await feedback_repo.save(feedback)

        retrieved = await feedback_repo.get_by_id(saved.id)

        assert retrieved is not None
        assert retrieved.id == saved.id
        assert retrieved.rating == "negative"

    @pytest.mark.asyncio
    async def test_get_by_message_id_returns_feedback(self, feedback_repo):
        """
        GIVEN: Gespeichertes Feedback für Message
        WHEN: get_by_message_id() aufgerufen
        THEN: Feedback zurückgegeben
        """
        feedback = RAGFeedback(
            id=None,
            chat_message_id=789,
            user_id=3,
            rating="neutral",
            comment="OK",
            submitted_at=datetime.utcnow()
        )
        await feedback_repo.save(feedback)

        retrieved = await feedback_repo.get_by_message_id(789, user_id=3)

        assert retrieved is not None
        assert retrieved.chat_message_id == 789
        assert retrieved.user_id == 3

    @pytest.mark.asyncio
    async def test_get_by_user_id_returns_all_user_feedbacks(self, feedback_repo):
        """
        GIVEN: Mehrere Feedbacks von einem User
        WHEN: get_by_user_id() aufgerufen
        THEN: Alle Feedbacks zurückgegeben
        """
        # Erstelle mehrere Feedbacks
        for i in range(3):
            feedback = RAGFeedback(
                id=None,
                chat_message_id=100 + i,
                user_id=1,
                rating="positive",
                comment=f"Feedback {i}",
                submitted_at=datetime.utcnow()
            )
            await feedback_repo.save(feedback)

        retrieved = await feedback_repo.get_by_user_id(user_id=1)

        assert len(retrieved) == 3
        assert all(f.user_id == 1 for f in retrieved)

    @pytest.mark.asyncio
    async def test_get_statistics_returns_correct_counts(self, feedback_repo):
        """
        GIVEN: Mehrere Feedbacks mit verschiedenen Ratings
        WHEN: get_statistics() aufgerufen
        THEN: Korrekte Statistiken zurückgegeben
        """
        # Erstelle Feedbacks
        ratings = ["positive", "positive", "negative", "neutral"]
        for i, rating in enumerate(ratings):
            feedback = RAGFeedback(
                id=None,
                chat_message_id=200 + i,
                user_id=1,
                rating=rating,
                comment=None,
                submitted_at=datetime.utcnow()
            )
            await feedback_repo.save(feedback)

        stats = await feedback_repo.get_statistics()

        assert stats["total"] == 4
        assert stats["positive"] == 2
        assert stats["negative"] == 1
        assert stats["neutral"] == 1

