"""
Tests für RAG Analytics Use Cases

TDD: Tests FIRST für GetRAGAnalyticsUseCase
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from contexts.ragintegration.application.use_cases import GetRAGAnalyticsUseCase


class TestGetRAGAnalyticsUseCase:
    """Test GetRAGAnalyticsUseCase"""

    @pytest.fixture
    def mock_repos(self):
        """Fixture für gemockte Repositories."""
        return {
            "feedback_repo": AsyncMock(),
            "audit_repo": AsyncMock(),
            "chat_message_repo": AsyncMock()
        }

    @pytest.mark.asyncio
    async def test_get_analytics_returns_comprehensive_stats(self, mock_repos):
        """
        GIVEN: Analytics-Daten aus verschiedenen Repositories
        WHEN: GetRAGAnalyticsUseCase.execute()
        THEN: Umfassende Statistiken zurückgegeben
        """
        # Mock Feedback Statistics
        mock_repos["feedback_repo"].get_statistics.return_value = {
            "total": 50,
            "positive": 35,
            "negative": 10,
            "neutral": 5,
            "average_rating": 0.75
        }

        # Mock Audit Log Statistics (Queries, Chunking, Indexing)
        mock_repos["audit_repo"].get_by_user_id.return_value = []
        # Mock: Zähle verschiedene Actions
        # (In echter Implementierung würde man SQL-Queries verwenden)

        # Mock Chat Message Count
        mock_repos["chat_message_repo"].get_all.return_value = [
            MagicMock(id=i, role="assistant", created_at=datetime.utcnow() - timedelta(days=i))
            for i in range(100)
        ]

        use_case = GetRAGAnalyticsUseCase(**mock_repos)

        result = await use_case.execute()

        assert "feedback" in result
        assert "queries" in result
        assert "chunking" in result
        assert "indexing" in result
        assert result["feedback"]["total"] == 50
        assert result["feedback"]["average_rating"] == 0.75

    @pytest.mark.asyncio
    async def test_get_analytics_with_time_range(self, mock_repos):
        """
        GIVEN: Analytics-Daten mit Zeitbereich
        WHEN: GetRAGAnalyticsUseCase.execute() mit start_date/end_date
        THEN: Gefilterte Statistiken zurückgegeben
        """
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        mock_repos["feedback_repo"].get_statistics.return_value = {
            "total": 20,
            "positive": 15,
            "negative": 3,
            "neutral": 2,
            "average_rating": 0.8
        }

        use_case = GetRAGAnalyticsUseCase(**mock_repos)

        result = await use_case.execute(
            start_date=start_date,
            end_date=end_date
        )

        assert result["feedback"]["total"] == 20
        # Zeitbereich sollte in Details enthalten sein
        assert "time_range" in result or "start_date" in result

