"""
Unit Test: Search Quality Metrics - Feedback NULL Handling

Ziel:
- Sicherstellen, dass fehlende (NULL/None) Feedback-Ratings die Metrik-Berechnung nicht crashen.
"""

from __future__ import annotations


def test_calculate_relevance_from_feedback_handles_none_and_empty() -> None:
    """Missing/empty feedback ratings should default to neutral (0.5) and not crash."""
    from contexts.ragintegration.infrastructure.search_quality_metrics import (
        SearchQualityMetricsService,
    )

    svc = SearchQualityMetricsService()

    relevance = svc._calculate_relevance_from_feedback(
        feedback_ratings=[None, "positive", "NEGATIVE", "", "neutral"],
        num_results=6,
    )

    assert relevance == [0.5, 1.0, 0.0, 0.5, 0.5, 0.5]


