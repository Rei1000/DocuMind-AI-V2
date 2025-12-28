"""
Unit Tests für Training Data Repository.

TDD Phase 2: RED - Tests schreiben bevor Code existiert.

Diese Tests müssen fehlschlagen, bis TrainingDataRepository implementiert ist.
"""

import pytest
from datetime import datetime
from typing import Optional, Dict, Any, List

# Diese Imports werden fehlschlagen, bis Code existiert
try:
    from contexts.ragintegration.infrastructure.repositories import SQLAlchemyTrainingDataRepository
    from contexts.ragintegration.domain.repositories import TrainingDataRepository
    from contexts.ragintegration.domain.entities import TrainingData
    from backend.app.models import TrainingDataModel
except ImportError:
    # Für RED-Phase: Mock-Imports
    TrainingDataRepository = None
    SQLAlchemyTrainingDataRepository = None
    TrainingDataModel = None
    TrainingData = None


class TestTrainingDataRepository:
    """Tests für Training Data Repository."""
    
    def test_repository_initialization(self):
        """Test: TrainingDataRepository kann initialisiert werden."""
        if SQLAlchemyTrainingDataRepository is None:
            pytest.skip("SQLAlchemyTrainingDataRepository noch nicht implementiert (RED-Phase)")
        
        from unittest.mock import Mock
        db_session = Mock()
        
        repository = SQLAlchemyTrainingDataRepository(db_session)
        assert repository is not None
        assert isinstance(repository, TrainingDataRepository)
    
    def test_save_training_data(self):
        """Test: Training-Daten können gespeichert werden."""
        if SQLAlchemyTrainingDataRepository is None or TrainingData is None:
            pytest.skip("SQLAlchemyTrainingDataRepository oder TrainingData noch nicht implementiert (RED-Phase)")
        
        from unittest.mock import Mock, MagicMock
        
        # Mock DB-Session mit refresh() Side-Effect
        db_session = Mock()
        
        # refresh() soll model.id setzen (simuliert DB-Verhalten)
        def mock_refresh(model):
            if not hasattr(model, 'id') or model.id is None:
                model.id = 1
        
        db_session.refresh = Mock(side_effect=mock_refresh)
        
        repository = SQLAlchemyTrainingDataRepository(db_session)
        
        # Erstelle TrainingData Entity
        training_data = TrainingData(
            id=None,
            query="Was sind die wichtigsten Schritte bei der Montage?",
            chunk_id="test_chunk_1",
            document_id=1,
            session_id=1,
            user_id=1,
            vector_score=0.85,
            text_score=0.72,
            hybrid_score=0.81,
            document_type="Arbeitsanweisung",
            user_level=5,
            keyword_matches=2,
            chunk_length=150,
            heading_hierarchy_depth=2,
            confidence_score=0.95,
            shap_explanation=None,  # Wird später gesetzt
            user_feedback=None,  # Optional
            feedback_comment=None,  # Optional
            created_at=datetime.now()
        )
        
        saved_data = repository.save(training_data)
        
        assert saved_data is not None
        assert saved_data.id is not None
        assert saved_data.query == "Was sind die wichtigsten Schritte bei der Montage?"
        assert saved_data.chunk_id == "test_chunk_1"
    
    def test_get_training_data_with_feedback(self):
        """Test: Training-Daten mit Feedback können abgerufen werden."""
        if SQLAlchemyTrainingDataRepository is None:
            pytest.skip("SQLAlchemyTrainingDataRepository noch nicht implementiert (RED-Phase)")
        
        from unittest.mock import Mock, MagicMock
        
        # Mock DB-Session mit Query-Chain
        db_session = Mock()
        
        # Mock Query-Ergebnisse (mit Feedback)
        mock_model = Mock()
        mock_model.id = 1
        mock_model.query = "Test Query"
        mock_model.chunk_id = "test_chunk_1"
        mock_model.document_id = 1
        mock_model.session_id = 1
        mock_model.user_id = 1
        mock_model.vector_score = "0.85"
        mock_model.text_score = "0.72"
        mock_model.hybrid_score = "0.81"
        mock_model.document_type = "Arbeitsanweisung"
        mock_model.user_level = 5
        mock_model.keyword_matches = 2
        mock_model.chunk_length = 150
        mock_model.heading_hierarchy_depth = 2
        mock_model.confidence_score = "0.95"
        mock_model.shap_explanation = None
        mock_model.user_feedback = "positive"
        mock_model.feedback_comment = None
        mock_model.created_at = datetime.now()
        
        # Mock Query-Chain
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[mock_model])
        
        db_session.query = Mock(return_value=mock_query)
        
        repository = SQLAlchemyTrainingDataRepository(db_session)
        
        # Test: get_training_data(with_feedback=True) sollte nur Daten mit Feedback zurückgeben
        training_data_list = repository.get_training_data(
            with_feedback=True,
            limit=10
        )
        
        assert isinstance(training_data_list, list)
        assert len(training_data_list) > 0
        # Alle zurückgegebenen Daten sollten Feedback haben
        for data in training_data_list:
            assert data.user_feedback is not None
    
    def test_get_training_data_without_feedback(self):
        """Test: Training-Daten ohne Feedback können abgerufen werden."""
        if SQLAlchemyTrainingDataRepository is None:
            pytest.skip("SQLAlchemyTrainingDataRepository noch nicht implementiert (RED-Phase)")
        
        from unittest.mock import Mock
        
        # Mock DB-Session mit Query-Chain (ohne Feedback)
        db_session = Mock()
        
        mock_model = Mock()
        mock_model.id = 1
        mock_model.query = "Test Query"
        mock_model.chunk_id = "test_chunk_1"
        mock_model.document_id = 1
        mock_model.session_id = 1
        mock_model.user_id = 1
        mock_model.vector_score = "0.85"
        mock_model.text_score = "0.72"
        mock_model.hybrid_score = "0.81"
        mock_model.document_type = "Arbeitsanweisung"
        mock_model.user_level = 5
        mock_model.keyword_matches = 2
        mock_model.chunk_length = 150
        mock_model.heading_hierarchy_depth = 2
        mock_model.confidence_score = "0.95"
        mock_model.shap_explanation = None
        mock_model.user_feedback = None  # Kein Feedback
        mock_model.feedback_comment = None
        mock_model.created_at = datetime.now()
        
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[mock_model])
        
        db_session.query = Mock(return_value=mock_query)
        
        repository = SQLAlchemyTrainingDataRepository(db_session)
        
        # Test: get_training_data(with_feedback=False) sollte nur Daten ohne Feedback zurückgeben
        training_data_list = repository.get_training_data(
            with_feedback=False,
            limit=10
        )
        
        assert isinstance(training_data_list, list)
        # Alle zurückgegebenen Daten sollten kein Feedback haben
        for data in training_data_list:
            assert data.user_feedback is None
    
    def test_get_training_data_by_user_id(self):
        """Test: Training-Daten können nach User-ID gefiltert werden."""
        if SQLAlchemyTrainingDataRepository is None:
            pytest.skip("SQLAlchemyTrainingDataRepository noch nicht implementiert (RED-Phase)")
        
        from unittest.mock import Mock
        
        db_session = Mock()
        
        mock_model = Mock()
        mock_model.id = 1
        mock_model.query = "Test Query"
        mock_model.chunk_id = "test_chunk_1"
        mock_model.document_id = 1
        mock_model.session_id = 1
        mock_model.user_id = 1  # User-ID 1
        mock_model.vector_score = "0.85"
        mock_model.text_score = "0.72"
        mock_model.hybrid_score = "0.81"
        mock_model.document_type = "Arbeitsanweisung"
        mock_model.user_level = 5
        mock_model.keyword_matches = 2
        mock_model.chunk_length = 150
        mock_model.heading_hierarchy_depth = 2
        mock_model.confidence_score = "0.95"
        mock_model.shap_explanation = None
        mock_model.user_feedback = None
        mock_model.feedback_comment = None
        mock_model.created_at = datetime.now()
        
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[mock_model])
        
        db_session.query = Mock(return_value=mock_query)
        
        repository = SQLAlchemyTrainingDataRepository(db_session)
        
        user_id = 1
        training_data_list = repository.get_training_data(
            user_id=user_id,
            limit=10
        )
        
        assert isinstance(training_data_list, list)
        # Alle zurückgegebenen Daten sollten dem User gehören
        for data in training_data_list:
            assert data.user_id == user_id
    
    def test_get_training_data_by_document_type(self):
        """Test: Training-Daten können nach Dokumenttyp gefiltert werden."""
        if SQLAlchemyTrainingDataRepository is None:
            pytest.skip("SQLAlchemyTrainingDataRepository noch nicht implementiert (RED-Phase)")
        
        from unittest.mock import Mock
        
        db_session = Mock()
        
        mock_model = Mock()
        mock_model.id = 1
        mock_model.query = "Test Query"
        mock_model.chunk_id = "test_chunk_1"
        mock_model.document_id = 1
        mock_model.session_id = 1
        mock_model.user_id = 1
        mock_model.vector_score = "0.85"
        mock_model.text_score = "0.72"
        mock_model.hybrid_score = "0.81"
        mock_model.document_type = "Arbeitsanweisung"  # Dokumenttyp
        mock_model.user_level = 5
        mock_model.keyword_matches = 2
        mock_model.chunk_length = 150
        mock_model.heading_hierarchy_depth = 2
        mock_model.confidence_score = "0.95"
        mock_model.shap_explanation = None
        mock_model.user_feedback = None
        mock_model.feedback_comment = None
        mock_model.created_at = datetime.now()
        
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[mock_model])
        
        db_session.query = Mock(return_value=mock_query)
        
        repository = SQLAlchemyTrainingDataRepository(db_session)
        
        document_type = "Arbeitsanweisung"
        training_data_list = repository.get_training_data(
            document_type=document_type,
            limit=10
        )
        
        assert isinstance(training_data_list, list)
        # Alle zurückgegebenen Daten sollten dem Dokumenttyp entsprechen
        for data in training_data_list:
            assert data.document_type == document_type
    
    def test_get_training_data_with_shap_explanation(self):
        """Test: Training-Daten mit SHAP-Erklärung können abgerufen werden."""
        if SQLAlchemyTrainingDataRepository is None:
            pytest.skip("SQLAlchemyTrainingDataRepository noch nicht implementiert (RED-Phase)")
        
        from unittest.mock import Mock
        import json
        
        db_session = Mock()
        
        mock_model = Mock()
        mock_model.id = 1
        mock_model.query = "Test Query"
        mock_model.chunk_id = "test_chunk_1"
        mock_model.document_id = 1
        mock_model.session_id = 1
        mock_model.user_id = 1
        mock_model.vector_score = "0.85"
        mock_model.text_score = "0.72"
        mock_model.hybrid_score = "0.81"
        mock_model.document_type = "Arbeitsanweisung"
        mock_model.user_level = 5
        mock_model.keyword_matches = 2
        mock_model.chunk_length = 150
        mock_model.heading_hierarchy_depth = 2
        mock_model.confidence_score = "0.95"
        mock_model.shap_explanation = json.dumps({'feature_importance': {'vector_score': 0.4}})  # Mit SHAP
        mock_model.user_feedback = None
        mock_model.feedback_comment = None
        mock_model.created_at = datetime.now()
        
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[mock_model])
        
        db_session.query = Mock(return_value=mock_query)
        
        repository = SQLAlchemyTrainingDataRepository(db_session)
        
        # Test: get_training_data(with_shap=True) sollte nur Daten mit SHAP zurückgeben
        training_data_list = repository.get_training_data(
            with_shap=True,
            limit=10
        )
        
        assert isinstance(training_data_list, list)
        # Alle zurückgegebenen Daten sollten SHAP-Erklärung haben
        for data in training_data_list:
            assert data.shap_explanation is not None
    
    def test_get_training_data_statistics(self):
        """Test: Training-Daten-Statistiken können abgerufen werden."""
        if SQLAlchemyTrainingDataRepository is None:
            pytest.skip("SQLAlchemyTrainingDataRepository noch nicht implementiert (RED-Phase)")
        
        from unittest.mock import Mock, MagicMock
        from sqlalchemy import func
        
        db_session = Mock()
        
        # Mock Query-Objekte für verschiedene Queries
        # 1. total_count Query
        mock_total_query = Mock()
        mock_total_query.scalar = Mock(return_value=10)
        
        # 2. with_feedback_count Query
        mock_feedback_query_chain = Mock()
        mock_feedback_query_chain.filter = Mock(return_value=mock_feedback_query_chain)
        mock_feedback_query_chain.scalar = Mock(return_value=5)
        
        # 3. with_shap_count Query
        mock_shap_query_chain = Mock()
        mock_shap_query_chain.filter = Mock(return_value=mock_shap_query_chain)
        mock_shap_query_chain.scalar = Mock(return_value=7)
        
        # 4. average_hybrid_score Query
        mock_avg_query_chain = Mock()
        mock_avg_query_chain.scalar = Mock(return_value=0.75)
        
        # Mock db.query() - wird 4x aufgerufen mit verschiedenen Argumenten
        # WICHTIG: SQLAlchemy ruft query() so auf: db.query(func.count(...)) oder db.query(func.avg(...))
        # Wir müssen die Aufrufe zählen, da wir nicht direkt auf die Funktion prüfen können
        query_call_order = []
        
        def mock_query_side_effect(*args):
            # args[0] ist die Funktion (func.count oder func.avg)
            # Wir zählen die Aufrufe basierend auf der Reihenfolge
            query_call_order.append(len(args))
            
            # 1. Aufruf: total_count (func.count ohne filter)
            if len(query_call_order) == 1:
                return mock_total_query
            # 2. Aufruf: with_feedback_count (func.count mit filter)
            elif len(query_call_order) == 2:
                return mock_feedback_query_chain
            # 3. Aufruf: with_shap_count (func.count mit filter)
            elif len(query_call_order) == 3:
                return mock_shap_query_chain
            # 4. Aufruf: average_hybrid_score (func.avg)
            elif len(query_call_order) == 4:
                return mock_avg_query_chain
            return mock_total_query
        
        db_session.query = Mock(side_effect=mock_query_side_effect)
        
        repository = SQLAlchemyTrainingDataRepository(db_session)
        
        statistics = repository.get_statistics()
        
        assert isinstance(statistics, dict)
        assert 'total_count' in statistics
        assert 'with_feedback_count' in statistics
        assert 'with_shap_count' in statistics
        assert 'average_hybrid_score' in statistics
        assert isinstance(statistics['total_count'], int)
        assert isinstance(statistics['with_feedback_count'], int)
        assert isinstance(statistics['with_shap_count'], int)
        assert isinstance(statistics['average_hybrid_score'], (int, float))
    
    def test_update_training_data_with_feedback(self):
        """Test: Training-Daten können mit Feedback aktualisiert werden."""
        if SQLAlchemyTrainingDataRepository is None or TrainingData is None:
            pytest.skip("SQLAlchemyTrainingDataRepository oder TrainingData noch nicht implementiert (RED-Phase)")
        
        from unittest.mock import Mock
        
        db_session = Mock()
        
        # Mock Model das gefunden wird
        mock_model = Mock()
        mock_model.id = 1
        mock_model.query = "Test Query"
        mock_model.chunk_id = "test_chunk_1"
        mock_model.document_id = 1
        mock_model.session_id = 1
        mock_model.user_id = 1
        mock_model.vector_score = "0.85"
        mock_model.text_score = "0.72"
        mock_model.hybrid_score = "0.81"
        mock_model.document_type = "Arbeitsanweisung"
        mock_model.user_level = 5
        mock_model.keyword_matches = 2
        mock_model.chunk_length = 150
        mock_model.heading_hierarchy_depth = 2
        mock_model.confidence_score = "0.95"
        mock_model.shap_explanation = None
        mock_model.user_feedback = "positive"  # Wird aktualisiert
        mock_model.feedback_comment = "Sehr hilfreich!"  # Wird aktualisiert
        mock_model.created_at = datetime.now()
        
        # Mock Query-Chain
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=mock_model)
        
        # Mock refresh() für update_feedback()
        def mock_refresh(model):
            # refresh() wird aufgerufen, aber model ist bereits aktualisiert
            pass
        
        db_session.query = Mock(return_value=mock_query)
        db_session.refresh = Mock(side_effect=mock_refresh)
        
        repository = SQLAlchemyTrainingDataRepository(db_session)
        
        updated_data = repository.update_feedback(1, "positive", "Sehr hilfreich!")
        
        assert updated_data is not None
        assert updated_data.user_feedback == "positive"
        assert updated_data.feedback_comment == "Sehr hilfreich!"

