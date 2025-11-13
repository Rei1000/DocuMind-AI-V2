"""
Tests für RAG Feedback Use Cases

TDD: Tests FIRST für SubmitFeedbackUseCase und GetFeedbackStatisticsUseCase
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from contexts.ragintegration.application.use_cases import (
    SubmitFeedbackUseCase,
    GetFeedbackStatisticsUseCase
)
from contexts.ragintegration.domain.entities import RAGFeedback


class TestSubmitFeedbackUseCase:
    """Test SubmitFeedbackUseCase"""

    @pytest.mark.asyncio
    async def test_submit_positive_feedback_creates_feedback(self):
        """
        GIVEN: User gibt positives Feedback
        WHEN: SubmitFeedbackUseCase.execute()
        THEN: RAGFeedback erstellt und gespeichert
        """
        mock_repo = AsyncMock()
        mock_event_publisher = AsyncMock()
        
        use_case = SubmitFeedbackUseCase(mock_repo, mock_event_publisher)

        chat_message_id = 123
        user_id = 1
        rating = "positive"
        comment = "Sehr hilfreich!"

        saved_feedback = RAGFeedback(
            id=1,
            chat_message_id=chat_message_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
            submitted_at=datetime.utcnow()
        )
        mock_repo.get_by_message_id.return_value = None  # Kein existierendes Feedback
        mock_repo.save.return_value = saved_feedback

        result = await use_case.execute(
            chat_message_id=chat_message_id,
            user_id=user_id,
            rating=rating,
            comment=comment
        )

        assert result.id == 1
        assert result.rating == rating
        assert result.comment == comment
        mock_repo.save.assert_called_once()
        mock_event_publisher.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_feedback_without_comment(self):
        """
        GIVEN: User gibt Feedback ohne Kommentar
        WHEN: SubmitFeedbackUseCase.execute()
        THEN: RAGFeedback ohne Kommentar erstellt
        """
        mock_repo = AsyncMock()
        mock_event_publisher = AsyncMock()
        
        use_case = SubmitFeedbackUseCase(mock_repo, mock_event_publisher)

        saved_feedback = RAGFeedback(
            id=2,
            chat_message_id=456,
            user_id=2,
            rating="negative",
            comment=None,
            submitted_at=datetime.utcnow()
        )
        mock_repo.get_by_message_id.return_value = None  # Kein existierendes Feedback
        mock_repo.save.return_value = saved_feedback

        result = await use_case.execute(
            chat_message_id=456,
            user_id=2,
            rating="negative",
            comment=None
        )

        assert result.comment is None
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_feedback_prevents_duplicate(self):
        """
        GIVEN: User hat bereits Feedback für diese Message gegeben
        WHEN: SubmitFeedbackUseCase.execute()
        THEN: ValueError raised
        """
        mock_repo = AsyncMock()
        mock_event_publisher = AsyncMock()
        
        use_case = SubmitFeedbackUseCase(mock_repo, mock_event_publisher)

        existing_feedback = RAGFeedback(
            id=3,
            chat_message_id=789,
            user_id=3,
            rating="positive",
            comment=None,
            submitted_at=datetime.utcnow()
        )
        mock_repo.get_by_message_id.return_value = existing_feedback

        with pytest.raises(ValueError, match="Feedback already exists"):
            await use_case.execute(
                chat_message_id=789,
                user_id=3,
                rating="positive",
                comment=None
            )


class TestGetFeedbackStatisticsUseCase:
    """Test GetFeedbackStatisticsUseCase"""

    @pytest.mark.asyncio
    async def test_get_statistics_for_message(self):
        """
        GIVEN: Feedback-Statistiken für eine Message
        WHEN: GetFeedbackStatisticsUseCase.execute()
        THEN: Korrekte Statistiken zurückgegeben
        """
        mock_repo = AsyncMock()
        use_case = GetFeedbackStatisticsUseCase(mock_repo)

        mock_repo.get_statistics.return_value = {
            "total": 5,
            "positive": 3,
            "negative": 1,
            "neutral": 1,
            "average_rating": 0.6  # (3*1 + 1*0 + 1*0.5) / 5
        }

        result = await use_case.execute(chat_message_id=123)

        assert result["total"] == 5
        assert result["positive"] == 3
        assert result["negative"] == 1
        assert result["neutral"] == 1
        mock_repo.get_statistics.assert_called_once_with(
            chat_message_id=123,
            user_id=None
        )

    @pytest.mark.asyncio
    async def test_get_statistics_for_user(self):
        """
        GIVEN: Feedback-Statistiken für einen User
        WHEN: GetFeedbackStatisticsUseCase.execute()
        THEN: Korrekte Statistiken zurückgegeben
        """
        mock_repo = AsyncMock()
        use_case = GetFeedbackStatisticsUseCase(mock_repo)

        mock_repo.get_statistics.return_value = {
            "total": 10,
            "positive": 7,
            "negative": 2,
            "neutral": 1,
            "average_rating": 0.75
        }

        result = await use_case.execute(user_id=1)

        assert result["total"] == 10
        assert result["positive"] == 7
        mock_repo.get_statistics.assert_called_once_with(
            chat_message_id=None,
            user_id=1
        )

