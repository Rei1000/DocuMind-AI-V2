"""
Tests für RAG Feedback Domain Entity

TDD: Tests FIRST für die RAGFeedback Entity
"""
import pytest
from datetime import datetime

from contexts.ragintegration.domain.entities import RAGFeedback


class TestRAGFeedback:
    """Test RAGFeedback Entity"""

    def test_create_feedback_with_required_fields(self):
        """
        GIVEN: Valid feedback data
        WHEN: RAGFeedback erstellt
        THEN: Entity ist valide
        """
        feedback = RAGFeedback(
            id=None,
            chat_message_id=123,
            user_id=1,
            rating="positive",
            comment="Sehr hilfreich!",
            submitted_at=datetime.utcnow()
        )

        assert feedback.chat_message_id == 123
        assert feedback.user_id == 1
        assert feedback.rating == "positive"
        assert feedback.comment == "Sehr hilfreich!"

    def test_feedback_requires_valid_rating(self):
        """
        GIVEN: Feedback mit ungültigem rating
        WHEN: RAGFeedback erstellt
        THEN: ValueError raised
        """
        with pytest.raises(ValueError, match="Invalid rating"):
            RAGFeedback(
                id=None,
                chat_message_id=123,
                user_id=1,
                rating="invalid_rating",
                comment=None,
                submitted_at=datetime.utcnow()
            )

    def test_feedback_allows_empty_comment(self):
        """
        GIVEN: Feedback ohne Kommentar
        WHEN: RAGFeedback erstellt
        THEN: Entity ist valide
        """
        feedback = RAGFeedback(
            id=None,
            chat_message_id=123,
            user_id=1,
            rating="negative",
            comment=None,
            submitted_at=datetime.utcnow()
        )

        assert feedback.rating == "negative"
        assert feedback.comment is None

    def test_feedback_validates_user_id(self):
        """
        GIVEN: Feedback mit ungültiger user_id
        WHEN: RAGFeedback erstellt
        THEN: ValueError raised
        """
        with pytest.raises(ValueError, match="user_id must be positive"):
            RAGFeedback(
                id=None,
                chat_message_id=123,
                user_id=0,
                rating="positive",
                comment=None,
                submitted_at=datetime.utcnow()
            )

    def test_feedback_validates_chat_message_id(self):
        """
        GIVEN: Feedback mit ungültiger chat_message_id
        WHEN: RAGFeedback erstellt
        THEN: ValueError raised
        """
        with pytest.raises(ValueError, match="chat_message_id must be positive"):
            RAGFeedback(
                id=None,
                chat_message_id=0,
                user_id=1,
                rating="positive",
                comment=None,
                submitted_at=datetime.utcnow()
            )

    def test_feedback_valid_ratings_list(self):
        """
        GIVEN: Liste aller validen Ratings
        WHEN: RAGFeedback mit jedem Rating erstellt
        THEN: Alle sind valide
        """
        for rating in RAGFeedback.VALID_RATINGS:
            feedback = RAGFeedback(
                id=None,
                chat_message_id=123,
                user_id=1,
                rating=rating,
                comment=None,
                submitted_at=datetime.utcnow()
            )
            assert feedback.rating == rating  # No ValueError raised

    def test_feedback_comment_max_length(self):
        """
        GIVEN: Feedback mit zu langem Kommentar
        WHEN: RAGFeedback erstellt
        THEN: ValueError raised
        """
        long_comment = "x" * 2001  # Max 2000 Zeichen

        with pytest.raises(ValueError, match="comment must not exceed 2000 characters"):
            RAGFeedback(
                id=None,
                chat_message_id=123,
                user_id=1,
                rating="positive",
                comment=long_comment,
                submitted_at=datetime.utcnow()
            )

    def test_feedback_comment_within_max_length(self):
        """
        GIVEN: Feedback mit Kommentar innerhalb der Max-Länge
        WHEN: RAGFeedback erstellt
        THEN: Entity ist valide
        """
        comment = "x" * 2000  # Exakt 2000 Zeichen

        feedback = RAGFeedback(
            id=None,
            chat_message_id=123,
            user_id=1,
            rating="positive",
            comment=comment,
            submitted_at=datetime.utcnow()
        )

        assert feedback.comment == comment

