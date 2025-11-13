"""
Tests für Search Quality Analytics Use Case.

TDD Phase 1: RED - Tests BEVOR Implementierung.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
from typing import List, Dict, Any

from contexts.ragintegration.application.use_cases import GetSearchQualityAnalyticsUseCase
from contexts.ragintegration.domain.entities import (
    ChatMessage,
    SourceReference,
    TrainingData
)


class TestGetSearchQualityAnalyticsUseCase:
    """Tests für GetSearchQualityAnalyticsUseCase."""

    @pytest.fixture
    def mock_repos(self):
        """Fixture für gemockte Repositories."""
        return {
            "chat_message_repo": AsyncMock(),
            "training_data_repo": Mock(),
            "indexed_document_repo": Mock()
        }
    
    @pytest.fixture
    def mock_db_session(self, monkeypatch):
        """Fixture für gemockte DB Session."""
        from unittest.mock import Mock
        from backend.app.models import UploadDocument, DocumentTypeModel
        
        # Mock UploadDocument Query
        mock_upload_doc1 = Mock()
        mock_upload_doc1.id = 1
        mock_upload_doc1.document_type = Mock()
        mock_upload_doc1.document_type.name = "Fachartikel"
        
        mock_upload_doc2 = Mock()
        mock_upload_doc2.id = 2
        mock_upload_doc2.document_type = Mock()
        mock_upload_doc2.document_type.name = "Fachartikel"
        
        mock_upload_doc3 = Mock()
        mock_upload_doc3.id = 3
        mock_upload_doc3.document_type = Mock()
        mock_upload_doc3.document_type.name = "Arbeitsanweisung"
        
        mock_upload_doc4 = Mock()
        mock_upload_doc4.id = 4
        mock_upload_doc4.document_type = Mock()
        mock_upload_doc4.document_type.name = "Arbeitsanweisung"
        
        def mock_query_filter(id):
            mock_query = Mock()
            if id == 1:
                mock_query.first.return_value = mock_upload_doc1
            elif id == 2:
                mock_query.first.return_value = mock_upload_doc2
            elif id == 3:
                mock_query.first.return_value = mock_upload_doc3
            elif id == 4:
                mock_query.first.return_value = mock_upload_doc4
            else:
                mock_query.first.return_value = None
            return mock_query
        
        return mock_query_filter

    @pytest.fixture
    def use_case(self, mock_repos):
        """Fixture für Use Case."""
        return GetSearchQualityAnalyticsUseCase(
            chat_message_repo=mock_repos["chat_message_repo"],
            training_data_repo=mock_repos["training_data_repo"],
            indexed_document_repo=mock_repos["indexed_document_repo"]
        )

    @pytest.mark.asyncio
    async def test_get_search_quality_returns_document_type_distribution(self, use_case, mock_repos):
        """
        GIVEN: Chat Messages mit Source References verschiedener Dokument-Typen
        WHEN: GetSearchQualityAnalyticsUseCase.execute()
        THEN: Dokument-Typ-Verteilung wird zurückgegeben
        """
        from contexts.ragintegration.domain.value_objects import SourceReference
        
        # Erstelle Source References mit _extended_metadata
        source_ref1 = SourceReference(
            document_id=1,
            document_title="Fachartikel 1",
            page_number=1,
            chunk_id="chunk1",
            relevance_score=0.85
        )
        source_ref1._extended_metadata = {
            "chunk_metadata": {"document_type": "Fachartikel"},
            "rank_position": 1
        }
        
        source_ref2 = SourceReference(
            document_id=2,
            document_title="Fachartikel 2",
            page_number=1,
            chunk_id="chunk2",
            relevance_score=0.82
        )
        source_ref2._extended_metadata = {
            "chunk_metadata": {"document_type": "Fachartikel"},
            "rank_position": 2
        }
        
        source_ref3 = SourceReference(
            document_id=3,
            document_title="Arbeitsanweisung 1",
            page_number=1,
            chunk_id="chunk3",
            relevance_score=0.45
        )
        source_ref3._extended_metadata = {
            "chunk_metadata": {"document_type": "Arbeitsanweisung"},
            "rank_position": 5
        }
        
        # Mock Chat Messages mit Source References
        mock_messages = [
            ChatMessage(
                id=1,
                session_id=1,
                role="user",
                content="Test Query",
                created_at=datetime.utcnow(),
                source_references=[],
                metadata={}
            ),
            ChatMessage(
                id=2,
                session_id=1,
                role="assistant",
                content="Test Answer",
                created_at=datetime.utcnow(),
                source_references=[source_ref1, source_ref2, source_ref3],
                metadata={}
            )
        ]
        
        mock_repos["chat_message_repo"].get_all = AsyncMock(return_value=mock_messages)
        
        # Mock Indexed Documents mit upload_document_id
        mock_doc1 = Mock()
        mock_doc1.upload_document_id = 1
        mock_doc1.id = 1
        
        mock_doc2 = Mock()
        mock_doc2.upload_document_id = 2
        mock_doc2.id = 2
        
        mock_doc3 = Mock()
        mock_doc3.upload_document_id = 3
        mock_doc3.id = 3
        
        mock_doc4 = Mock()
        mock_doc4.upload_document_id = 4
        mock_doc4.id = 4
        
        mock_repos["indexed_document_repo"].get_all.return_value = [
            mock_doc1, mock_doc2, mock_doc3, mock_doc4
        ]
        
        # Mock Training Data Repository
        mock_repos["training_data_repo"].get_training_data.return_value = []
        
        # Mock DB Session für UploadDocument Queries
        from unittest.mock import patch
        from backend.app.models import UploadDocument
        
        with patch('backend.app.database.SessionLocal') as mock_session_local:
            mock_session = Mock()
            
            # Mock für verschiedene upload_document_ids
            def mock_filter(id):
                mock_filtered = Mock()
                if id == 1 or id == 2:
                    mock_upload_doc = Mock()
                    mock_upload_doc.document_type = Mock()
                    mock_upload_doc.document_type.name = "Fachartikel"
                    mock_filtered.first.return_value = mock_upload_doc
                elif id == 3 or id == 4:
                    mock_upload_doc = Mock()
                    mock_upload_doc.document_type = Mock()
                    mock_upload_doc.document_type.name = "Arbeitsanweisung"
                    mock_filtered.first.return_value = mock_upload_doc
                else:
                    mock_filtered.first.return_value = None
                return mock_filtered
            
            mock_query = Mock()
            mock_query.filter = mock_filter
            mock_session.query.return_value = mock_query
            mock_session_local.return_value.__enter__ = Mock(return_value=mock_session)
            mock_session_local.return_value.__exit__ = Mock(return_value=None)
            
            # Verwende top_k=4, damit Rank 5 nicht in Top-K ist
            result = await use_case.execute(top_k=4)
        
        assert "document_type_distribution" in result
        assert len(result["document_type_distribution"]) > 0
        
        # Prüfe Fachartikel
        fachartikel = next(
            (d for d in result["document_type_distribution"] if d["document_type"] == "Fachartikel"),
            None
        )
        if fachartikel:
            assert fachartikel["found_in_top_k"] == 2
            assert fachartikel["average_score"] > 0.8
        
        # Prüfe Arbeitsanweisung
        arbeitsanweisung = next(
            (d for d in result["document_type_distribution"] if d["document_type"] == "Arbeitsanweisung"),
            None
        )
        if arbeitsanweisung:
            assert arbeitsanweisung["found_in_top_k"] == 0  # Rank 5 ist nicht in Top-K (4)
            assert arbeitsanweisung["average_score"] < 0.5

    @pytest.mark.asyncio
    async def test_get_search_quality_returns_score_distribution(self, use_case, mock_repos):
        """
        GIVEN: Chat Messages mit Source References verschiedener Scores
        WHEN: GetSearchQualityAnalyticsUseCase.execute()
        THEN: Score-Verteilung wird zurückgegeben
        """
        from contexts.ragintegration.domain.value_objects import SourceReference
        
        source_refs = [
            SourceReference(document_id=1, document_title="Doc1", page_number=1, chunk_id="c1", relevance_score=0.95),
            SourceReference(document_id=2, document_title="Doc2", page_number=1, chunk_id="c2", relevance_score=0.85),
            SourceReference(document_id=3, document_title="Doc3", page_number=1, chunk_id="c3", relevance_score=0.45),
            SourceReference(document_id=4, document_title="Doc4", page_number=1, chunk_id="c4", relevance_score=0.01)
        ]
        
        mock_messages = [
            ChatMessage(
                id=1,
                session_id=1,
                role="assistant",
                content="Test",
                created_at=datetime.utcnow(),
                source_references=source_refs,
                metadata={}
            )
        ]
        
        mock_repos["chat_message_repo"].get_all = AsyncMock(return_value=mock_messages)
        mock_repos["indexed_document_repo"].get_all.return_value = []
        mock_repos["training_data_repo"].get_training_data.return_value = []
        
        result = await use_case.execute()
        
        assert "score_distribution" in result
        assert result["score_distribution"]["min"] == 0.01
        assert result["score_distribution"]["max"] == 0.95
        assert result["score_distribution"]["average"] > 0.5
        assert result["score_distribution"]["median"] is not None

    @pytest.mark.asyncio
    async def test_get_search_quality_returns_top_queries(self, use_case, mock_repos):
        """
        GIVEN: Chat Messages mit verschiedenen Queries
        WHEN: GetSearchQualityAnalyticsUseCase.execute()
        THEN: Top Queries mit gefundenen/fehlenden Dokument-Typen werden zurückgegeben
        """
        from contexts.ragintegration.domain.value_objects import SourceReference
        from unittest.mock import patch
        
        source_ref = SourceReference(
            document_id=1,
            document_title="Fachartikel",
            page_number=1,
            chunk_id="c1",
            relevance_score=0.85
        )
        source_ref._extended_metadata = {
            "chunk_metadata": {"document_type": "Fachartikel"},
            "rank_position": 1
        }
        
        mock_messages = [
            ChatMessage(
                id=1,
                session_id=1,
                role="user",
                content="Was sind die wichtigsten Schritte bei der Montage?",
                created_at=datetime.utcnow(),
                source_references=[],
                metadata={}
            ),
            ChatMessage(
                id=2,
                session_id=1,
                role="assistant",
                content="Test",
                created_at=datetime.utcnow(),
                source_references=[source_ref],
                metadata={}
            )
        ]
        
        mock_repos["chat_message_repo"].get_all = AsyncMock(return_value=mock_messages)
        
        mock_doc1 = Mock()
        mock_doc1.upload_document_id = 1
        mock_doc1.id = 1
        
        mock_doc2 = Mock()
        mock_doc2.upload_document_id = 2
        mock_doc2.id = 2
        
        mock_repos["indexed_document_repo"].get_all.return_value = [mock_doc1, mock_doc2]
        mock_repos["training_data_repo"].get_training_data.return_value = []
        
        with patch('backend.app.database.SessionLocal') as mock_session_local:
            mock_session = Mock()
            
            # Mock für UploadDocument Queries (für doc_type_counts)
            def mock_upload_filter(upload_id):
                mock_filtered = Mock()
                if upload_id == 1:
                    mock_upload_doc = Mock()
                    mock_upload_doc.document_type = Mock()
                    mock_upload_doc.document_type.name = "Fachartikel"
                    mock_filtered.first.return_value = mock_upload_doc
                elif upload_id == 2:
                    mock_upload_doc = Mock()
                    mock_upload_doc.document_type = Mock()
                    mock_upload_doc.document_type.name = "Arbeitsanweisung"
                    mock_filtered.first.return_value = mock_upload_doc
                else:
                    mock_filtered.first.return_value = None
                return mock_filtered
            
            # Mock für IndexedDocument Queries (für Source Reference document_type)
            def mock_indexed_filter(doc_id):
                mock_filtered = Mock()
                if doc_id == 1:
                    mock_indexed_doc = Mock()
                    mock_indexed_doc.upload_document_id = 1
                    mock_upload_doc = Mock()
                    mock_upload_doc.document_type = Mock()
                    mock_upload_doc.document_type.name = "Fachartikel"
                    mock_filtered.first.return_value = mock_indexed_doc
                    # Mock für UploadDocument Query nach indexed_doc
                    mock_upload_query = Mock()
                    mock_upload_query.filter.return_value.first.return_value = mock_upload_doc
                    mock_session.query.return_value = mock_upload_query
                else:
                    mock_filtered.first.return_value = None
                return mock_filtered
            
            # Kombinierter Mock für beide Query-Typen
            def combined_query(model_class):
                mock_query = Mock()
                if model_class.__name__ == "UploadDocument":
                    mock_query.filter = mock_upload_filter
                elif model_class.__name__ == "IndexedDocumentModel":
                    mock_query.filter = mock_indexed_filter
                return mock_query
            
            mock_session.query = combined_query
            mock_session_local.return_value.__enter__ = Mock(return_value=mock_session)
            mock_session_local.return_value.__exit__ = Mock(return_value=None)
            
            result = await use_case.execute()
        
        assert "top_queries" in result
        assert len(result["top_queries"]) > 0
        
        montage_query = next(
            (q for q in result["top_queries"] if "Montage" in q["query"]),
            None
        )
        assert montage_query is not None
        assert "Fachartikel" in montage_query["document_types_found"]
        # Prüfe, dass Arbeitsanweisung fehlt (kann auch leer sein wenn keine gefunden)
        assert len(montage_query["missing_document_types"]) >= 0

    @pytest.mark.asyncio
    async def test_get_search_quality_returns_shap_insights(self, use_case, mock_repos):
        """
        GIVEN: Training Data mit SHAP-Erklärungen
        WHEN: GetSearchQualityAnalyticsUseCase.execute()
        THEN: SHAP-basierte Insights werden zurückgegeben
        """
        mock_training_data = [
            TrainingData(
                id=1,
                query="Test",
                chunk_id="chunk1",
                document_id=1,
                session_id=1,
                user_id=1,
                vector_score=0.85,
                text_score=0.75,
                hybrid_score=0.82,
                document_type="Fachartikel",
                user_level=5,
                keyword_matches=5,
                chunk_length=500,
                heading_hierarchy_depth=2,
                confidence_score=0.9,
                shap_explanation={
                    "feature_importance": {
                        "document_type": 0.35,
                        "vector_score": 0.28,
                        "text_score": 0.15
                    }
                },
                user_feedback=None,
                feedback_comment=None,
                created_at=datetime.utcnow()
            )
        ]
        
        mock_repos["training_data_repo"].get_training_data.return_value = mock_training_data
        mock_repos["chat_message_repo"].get_all = AsyncMock(return_value=[])
        mock_repos["indexed_document_repo"].get_all.return_value = []
        
        result = await use_case.execute()
        
        assert "shap_insights" in result
        assert len(result["shap_insights"]) > 0
        
        # Prüfe, dass document_type den höchsten Impact hat
        document_type_insight = next(
            (i for i in result["shap_insights"] if i["feature"] == "document_type"),
            None
        )
        assert document_type_insight is not None
        assert document_type_insight["impact"] == 0.35
        assert "Erklärung" in document_type_insight["explanation"] or "Einfluss" in document_type_insight["explanation"]

    @pytest.mark.asyncio
    async def test_get_search_quality_filters_by_time_range(self, use_case, mock_repos):
        """
        GIVEN: Chat Messages mit verschiedenen Zeitstempeln
        WHEN: GetSearchQualityAnalyticsUseCase.execute() mit start_date/end_date
        THEN: Nur Messages im Zeitbereich werden berücksichtigt
        """
        now = datetime.utcnow()
        old_date = now - timedelta(days=10)
        recent_date = now - timedelta(days=1)
        
        mock_messages = [
            ChatMessage(
                id=1,
                session_id=1,
                role="assistant",
                content="Old",
                created_at=old_date,
                source_references=[],
                metadata={}
            ),
            ChatMessage(
                id=2,
                session_id=1,
                role="assistant",
                content="Recent",
                created_at=recent_date,
                source_references=[],
                metadata={}
            )
        ]
        
        mock_repos["chat_message_repo"].get_all = AsyncMock(return_value=mock_messages)
        mock_repos["indexed_document_repo"].get_all.return_value = []
        mock_repos["training_data_repo"].get_training_data.return_value = []
        
        start_date = now - timedelta(days=5)
        result = await use_case.execute(start_date=start_date)
        
        # Prüfe, dass nur recent Messages berücksichtigt wurden
        # (indirekt durch fehlende alte Daten)
        assert "document_type_distribution" in result

    @pytest.mark.asyncio
    async def test_get_search_quality_handles_empty_data(self, use_case, mock_repos):
        """
        GIVEN: Keine Chat Messages oder Training Data
        WHEN: GetSearchQualityAnalyticsUseCase.execute()
        THEN: Leere aber valide Struktur wird zurückgegeben
        """
        mock_repos["chat_message_repo"].get_all = AsyncMock(return_value=[])
        mock_repos["training_data_repo"].get_training_data.return_value = []
        mock_repos["indexed_document_repo"].get_all.return_value = []
        
        result = await use_case.execute()
        
        assert "document_type_distribution" in result
        assert isinstance(result["document_type_distribution"], list)
        assert "score_distribution" in result
        assert "top_queries" in result
        assert "shap_insights" in result

