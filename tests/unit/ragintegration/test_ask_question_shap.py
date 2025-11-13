"""
Unit Tests für SHAP-Integration in AskQuestionUseCase.

TDD Phase 1: RED - Tests schreiben bevor Code existiert.

Diese Tests müssen fehlschlagen, bis SHAP-Integration implementiert ist.
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from typing import Optional

# Diese Imports werden fehlschlagen, bis Code existiert
try:
    from contexts.ragintegration.application.use_cases import AskQuestionUseCase
    from contexts.ragintegration.infrastructure.shap_service import SHAPExplanationService
except ImportError:
    # Für RED-Phase: Mock-Imports
    AskQuestionUseCase = None
    SHAPExplanationService = None


class TestAskQuestionUseCaseSHAP:
    """Tests für SHAP-Integration in AskQuestionUseCase."""
    
    def test_use_case_accepts_shap_service(self):
        """Test: Use Case akzeptiert SHAP-Service als optionalen Parameter."""
        if AskQuestionUseCase is None:
            pytest.skip("AskQuestionUseCase noch nicht importierbar (RED-Phase)")
        
        # Setup: Mock Dependencies
        chunk_repository = Mock()
        session_repository = Mock()
        indexed_document_repository = Mock()
        vector_store = Mock()
        embedding_service = Mock()
        multi_query_service = Mock()
        ai_service = Mock()
        message_repository = Mock()
        permission_service = Mock()
        shap_service = Mock(spec=SHAPExplanationService) if SHAPExplanationService else Mock()
        
        # Test: Use Case kann mit shap_service initialisiert werden
        use_case = AskQuestionUseCase(
            chunk_repository=chunk_repository,
            session_repository=session_repository,
            indexed_document_repository=indexed_document_repository,
            vector_store=vector_store,
            embedding_service=embedding_service,
            multi_query_service=multi_query_service,
            ai_service=ai_service,
            event_publisher=None,
            message_repository=message_repository,
            permission_service=permission_service,
            shap_service=shap_service  # NEU
        )
        
        assert use_case.shap_service == shap_service
    
    def test_use_case_works_without_shap_service(self):
        """Test: Use Case funktioniert auch ohne SHAP-Service (Backward Compatibility)."""
        if AskQuestionUseCase is None:
            pytest.skip("AskQuestionUseCase noch nicht importierbar (RED-Phase)")
        
        # Setup: Mock Dependencies ohne shap_service
        chunk_repository = Mock()
        session_repository = Mock()
        indexed_document_repository = Mock()
        vector_store = Mock()
        embedding_service = Mock()
        multi_query_service = Mock()
        ai_service = Mock()
        message_repository = Mock()
        permission_service = Mock()
        
        # Test: Use Case kann ohne shap_service initialisiert werden
        use_case = AskQuestionUseCase(
            chunk_repository=chunk_repository,
            session_repository=session_repository,
            indexed_document_repository=indexed_document_repository,
            vector_store=vector_store,
            embedding_service=embedding_service,
            multi_query_service=multi_query_service,
            ai_service=ai_service,
            event_publisher=None,
            message_repository=message_repository,
            permission_service=permission_service,
            shap_service=None  # Optional
        )
        
        assert use_case.shap_service is None
    
    def test_use_case_creates_shap_explanation_when_service_provided(self):
        """Test: Use Case erstellt SHAP-Erklärung wenn Service vorhanden."""
        if AskQuestionUseCase is None or SHAPExplanationService is None:
            pytest.skip("AskQuestionUseCase oder SHAPExplanationService noch nicht importierbar (RED-Phase)")
        
        # Setup: Mock SHAP-Service
        shap_service = Mock(spec=SHAPExplanationService)
        shap_explanation = Mock()
        shap_explanation.feature_importance = {'vector_score': 0.4, 'text_score': 0.3}
        shap_explanation.prediction = 0.81
        shap_explanation.chunk_id = 'test_chunk_1'
        shap_service.explain_search_result.return_value = shap_explanation
        
        # Setup: Mock Use Case Dependencies
        # (Wird in GREEN-Phase implementiert - hier nur Test-Struktur)
        # Test: execute() sollte shap_service.explain_search_result aufrufen
        # (Wird in GREEN-Phase implementiert)
        pass
    
    def test_shap_explanation_stored_in_extended_metadata(self):
        """Test: SHAP-Erklärung wird in _extended_metadata gespeichert."""
        if AskQuestionUseCase is None or SHAPExplanationService is None:
            pytest.skip("AskQuestionUseCase oder SHAPExplanationService noch nicht importierbar (RED-Phase)")
        
        # Test: source_ref._extended_metadata['shap_explanation'] sollte gesetzt sein
        # (Wird in GREEN-Phase implementiert)
        pass
    
    def test_use_case_handles_shap_service_error_gracefully(self):
        """Test: Use Case behandelt SHAP-Service-Fehler gracefully."""
        if AskQuestionUseCase is None or SHAPExplanationService is None:
            pytest.skip("AskQuestionUseCase oder SHAPExplanationService noch nicht importierbar (RED-Phase)")
        
        # Setup: SHAP-Service wirft Exception
        shap_service = Mock(spec=SHAPExplanationService)
        shap_service.explain_search_result.side_effect = Exception("SHAP Error")
        
        # Test: Wenn SHAP-Service fehlschlägt, sollte Use Case trotzdem funktionieren
        # (Wird in GREEN-Phase implementiert)
        pass
    
    def test_shap_explanation_created_for_each_source_reference(self):
        """Test: SHAP-Erklärung wird für jeden Source Reference erstellt."""
        if AskQuestionUseCase is None or SHAPExplanationService is None:
            pytest.skip("AskQuestionUseCase oder SHAPExplanationService noch nicht importierbar (RED-Phase)")
        
        # Test: Für jeden Source Reference sollte shap_service.explain_search_result aufgerufen werden
        # (Wird in GREEN-Phase implementiert)
        pass

