"""
E2E-Regressionstests für dynamische RAG-Filterparameter.

Diese Tests validieren den kompletten API-Pfad für `/api/rag/chat/ask`
und stellen sicher, dass Filter- und Ranking-Parameter unverändert bis
zum AskQuestionUseCase durchgereicht werden.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Dict, Generator, Tuple

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from contexts.ragintegration.domain.entities import ChatMessage
from contexts.ragintegration.interface import router as rag_router


class _DummyRAGAIService:
    """Leichter Stub für RAGAIService in Endpoint-Tests."""

    def __init__(self, rag_chat_prompt_repo: Any) -> None:
        self.rag_chat_prompt_repo = rag_chat_prompt_repo


class _DummyPermissionService:
    """Leichter Stub für Permission-Service."""

    def __init__(self, db_session: Any) -> None:
        self.db_session = db_session


class _DummyBackgroundDataService:
    """Leichter Stub für SHAP Background Service."""

    def __init__(self, max_records: int, feature_extractor: Any) -> None:
        self.max_records = max_records
        self.feature_extractor = feature_extractor

    def get_background_data(self, n_samples: int = 50) -> list[Any]:
        return []


class _DummyFeatureExtractor:
    """Leichter Stub für SHAP FeatureExtractor."""


class _DummyRankingModelWrapper:
    """Leichter Stub für SHAP RankingModelWrapper."""


class _DummySHAPExplainerService:
    """Leichter Stub für SHAPExplainerService."""

    def __init__(
        self,
        model: Any,
        feature_extractor: Any,
        background_data: list[Any],
        n_background_samples: int,
        db_session: Any = None,
    ) -> None:
        self.model = model
        self.feature_extractor = feature_extractor
        self.background_data = background_data
        self.n_background_samples = n_background_samples
        self.db_session = db_session
        self._background_data_service = None


class _DummyTrainingDataRepository:
    """Leichter Stub für TrainingData Repository."""

    def __init__(self, db_session: Any) -> None:
        self.db_session = db_session


class _DummyMLModelService:
    """Leichter Stub für MLModelService."""

    def __init__(self, training_data_repo: Any) -> None:
        self.training_data_repo = training_data_repo


class _DummyLTRService:
    """Leichter Stub für LTRService."""

    def __init__(self, model_dir: str, model_name: str, enable_ml: bool) -> None:
        self.model_dir = model_dir
        self.model_name = model_name
        self.enable_ml = enable_ml
        self.model_path = f"{model_dir}/{model_name}"

    def is_enabled(self) -> bool:
        return False


@pytest.fixture
def configured_e2e_app(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Tuple[Any, Dict[str, Any]], None, None]:
    """
    Konfiguriere App + Dependency-Overrides für stabile Filter-E2E-Tests.
    """
    captured: Dict[str, Any] = {}

    class _CaptureAskQuestionUseCase:
        """Fängt execute()-Parameter ab und liefert gültige ChatMessage."""

        def __init__(self, **kwargs: Any) -> None:
            captured["init_kwargs"] = kwargs

        async def execute(self, **kwargs: Any) -> ChatMessage:
            captured["execute_kwargs"] = kwargs
            return ChatMessage(
                id=999,
                session_id=int(kwargs["session_id"]),
                role="assistant",
                content="ok",
                created_at=datetime.now(timezone.utc),
                source_references=[],
                ai_model_used=kwargs.get("model_id", "gpt-4o-mini"),
                metadata={"tokens_used": 7},
            )

    # Halte SHAP-Pfad leichtgewichtig.
    monkeypatch.setenv("PERSIST_TO_DB", "false")

    monkeypatch.setattr(rag_router, "AskQuestionUseCase", _CaptureAskQuestionUseCase)
    monkeypatch.setattr(
        "contexts.ragintegration.infrastructure.ai_service.RAGAIService",
        _DummyRAGAIService,
    )
    monkeypatch.setattr(
        "contexts.documentupload.infrastructure.permission_service.SQLAlchemyWorkflowPermissionService",
        _DummyPermissionService,
    )
    monkeypatch.setattr(
        "contexts.ragintegration.infrastructure.shap_real_attribution.SHAPExplainerService",
        _DummySHAPExplainerService,
    )
    monkeypatch.setattr(
        "contexts.ragintegration.infrastructure.shap_real_attribution.FeatureExtractor",
        _DummyFeatureExtractor,
    )
    monkeypatch.setattr(
        "contexts.ragintegration.infrastructure.shap_real_attribution.RankingModelWrapper",
        _DummyRankingModelWrapper,
    )
    monkeypatch.setattr(
        "contexts.ragintegration.infrastructure.shap_background_data_service.SHAPBackgroundDataService",
        _DummyBackgroundDataService,
    )
    monkeypatch.setattr(
        "contexts.ragintegration.infrastructure.repositories.SQLAlchemyTrainingDataRepository",
        _DummyTrainingDataRepository,
    )
    monkeypatch.setattr(
        "contexts.ragintegration.infrastructure.ml_model_service.MLModelService",
        _DummyMLModelService,
    )
    monkeypatch.setattr(
        "contexts.ragintegration.infrastructure.ml.ltr_service.LTRService",
        _DummyLTRService,
    )

    session_repo = SimpleNamespace(find_by_id=lambda session_id: SimpleNamespace(id=session_id, user_id=1))
    chat_message_repo = SimpleNamespace(save=lambda message: message)

    rag_adapter = SimpleNamespace(
        rag_chat_prompt_repo=object(),
        document_chunk_repo=object(),
        chat_session_repo=session_repo,
        indexed_document_repo=object(),
        vector_store=object(),
        embedding_service=object(),
        multi_query_service=object(),
        chat_message_repo=chat_message_repo,
        search_quality_metrics_repo=object(),
    )

    app.dependency_overrides[rag_router.get_current_user] = lambda: {"id": 1, "user_id": 1}
    app.dependency_overrides[rag_router.get_db_session] = lambda: object()
    app.dependency_overrides[rag_router.get_rag_adapter] = lambda: rag_adapter
    app.dependency_overrides[rag_router.get_ai_service] = lambda: object()

    try:
        yield app, captured
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, expected",
    [
        (
            {
                "question": "trägheitsmoment",
                "session_id": 77,
                "model": "gemini-2.5-flash",
                "top_k": 8,
                "score_threshold": 0.019,
                "use_hybrid_search": True,
                "use_multi_query": True,
                "use_ml_ranking": True,
                "adaptive_min_avg_score": 0.11,
                "adaptive_min_max_score": 0.21,
                "filters": {
                    "document_type": "1",
                    "page_numbers": [2, 7],
                    "date_from": "2025-01-01",
                    "date_to": "2026-01-01",
                    "query": "schnellsuche"
                },
            },
            {
                "use_multi_query": True,
                "use_ml_ranking": True,
                "use_hybrid_search": True,
                "top_k": 8,
                "score_threshold": 0.019,
                "adaptive_min_avg_score": 0.11,
                "adaptive_min_max_score": 0.21,
            },
        ),
        (
            {
                "question": "trägheitsmoment",
                "session_id": 77,
                "model": "gemini-2.5-flash",
                "top_k": 3,
                "score_threshold": 0.005,
                "use_hybrid_search": False,
                "use_multi_query": False,
                "use_ml_ranking": False,
                "adaptive_min_avg_score": 0.02,
                "adaptive_min_max_score": 0.04,
                "filters": {
                    "document_type": "",
                    "page_numbers": [],
                    "query": ""
                },
            },
            {
                "use_multi_query": False,
                "use_ml_ranking": False,
                "use_hybrid_search": False,
                "top_k": 3,
                "score_threshold": 0.005,
                "adaptive_min_avg_score": 0.02,
                "adaptive_min_max_score": 0.04,
            },
        ),
    ],
)
async def test_chat_ask_filter_matrix_passthrough(
    configured_e2e_app: Tuple[Any, Dict[str, Any]],
    payload: Dict[str, Any],
    expected: Dict[str, Any],
) -> None:
    """
    Validiert, dass alle Filter-/Ranking-Optionen dynamisch durchgereicht werden.
    """
    test_app, captured = configured_e2e_app

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.post("/api/rag/chat/ask", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "ok"
    assert body["model_used"] == payload["model"]

    execute_kwargs = captured.get("execute_kwargs")
    assert execute_kwargs is not None

    assert execute_kwargs["question"] == payload["question"]
    assert execute_kwargs["session_id"] == payload["session_id"]
    assert execute_kwargs["model_id"] == payload["model"]
    assert execute_kwargs["filters"] == payload["filters"]
    assert execute_kwargs["use_multi_query"] == expected["use_multi_query"]
    assert execute_kwargs["use_ml_ranking"] == expected["use_ml_ranking"]
    assert execute_kwargs["use_hybrid_search"] == expected["use_hybrid_search"]
    assert execute_kwargs["top_k"] == expected["top_k"]
    assert execute_kwargs["score_threshold"] == expected["score_threshold"]
    assert execute_kwargs["adaptive_min_avg_score"] == expected["adaptive_min_avg_score"]
    assert execute_kwargs["adaptive_min_max_score"] == expected["adaptive_min_max_score"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, expected",
    [
        (
            {
                "question": "trägheitsmoment",
                "session_id": 81,
                "top_k": 1,
                "score_threshold": 0.0,
                "use_hybrid_search": True,
                "use_multi_query": False,
                "use_ml_ranking": False,
                "adaptive_min_avg_score": 0.0,
                "adaptive_min_max_score": 0.0,
                "filters": {"document_type": "11"},
            },
            {
                "model_id": "gpt-4o-mini",
                "top_k": 1,
                "score_threshold": 0.0,
                "adaptive_min_avg_score": 0.0,
                "adaptive_min_max_score": 0.0,
            },
        ),
        (
            {
                "question": "trägheitsmoment",
                "session_id": 82,
                "model": "gemini-2.5-flash",
                "top_k": 20,
                "score_threshold": 0.05,
                "use_hybrid_search": False,
                "use_multi_query": True,
                "use_ml_ranking": True,
                "adaptive_min_avg_score": 0.5,
                "adaptive_min_max_score": 0.5,
                "filters": {"document_type": "11", "page_numbers": [1]},
            },
            {
                "model_id": "gemini-2.5-flash",
                "top_k": 20,
                "score_threshold": 0.05,
                "adaptive_min_avg_score": 0.5,
                "adaptive_min_max_score": 0.5,
            },
        ),
        (
            {
                "question": "trägheitsmoment",
                "session_id": 83,
            },
            {
                "model_id": "gpt-4o-mini",
                "top_k": 5,
                "score_threshold": 0.02,
                "adaptive_min_avg_score": 0.15,
                "adaptive_min_max_score": 0.25,
            },
        ),
    ],
)
async def test_chat_ask_filter_boundaries_and_defaults(
    configured_e2e_app: Tuple[Any, Dict[str, Any]],
    payload: Dict[str, Any],
    expected: Dict[str, Any],
) -> None:
    """
    Validiert Grenzwerte und Default-Werte für alle relevanten Filterparameter.
    """
    test_app, captured = configured_e2e_app

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.post("/api/rag/chat/ask", json=payload)

    assert response.status_code == 200
    execute_kwargs = captured.get("execute_kwargs")
    assert execute_kwargs is not None

    assert execute_kwargs["model_id"] == expected["model_id"]
    assert execute_kwargs["top_k"] == expected["top_k"]
    assert execute_kwargs["score_threshold"] == expected["score_threshold"]
    assert execute_kwargs["adaptive_min_avg_score"] == expected["adaptive_min_avg_score"]
    assert execute_kwargs["adaptive_min_max_score"] == expected["adaptive_min_max_score"]
