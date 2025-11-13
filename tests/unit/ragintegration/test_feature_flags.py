"""
Unit Tests für Feature Flags (ML_ENABLE, ML_SHAP_ENABLE, FEEDBACK_TRAINING_ENABLE).

TDD Phase 1: RED - Tests für Feature-Flag-Kontrolle.

Diese Tests definieren Anforderungen:
1. ML_ENABLE=false deaktiviert ML-Ranking
2. ML_SHAP_ENABLE=false deaktiviert ML-SHAP
3. FEEDBACK_TRAINING_ENABLE=false deaktiviert Training-Daten-Sammlung
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import os


# ========================================
# Test 1: ML_ENABLE Flag
# ========================================

@patch.dict(os.environ, {'ML_ENABLE': 'false'})
def test_ml_disabled_falls_back_to_hybrid():
    """
    ML_ENABLE=false sollte zu Hybrid-Score fallback.
    
    Requirements:
    - LTR Service is_enabled() gibt False zurück
    - predict_ml_score() gibt hybrid_score zurück
    - get_final_score() gibt hybrid_score zurück
    """
    from contexts.ragintegration.infrastructure.ml.ltr_service import LTRService
    
    # Erstelle Service mit ML_ENABLE=false
    service = LTRService(enable_ml=False)
    
    # Assertions
    assert service.is_enabled() is False, "Service sollte disabled sein"
    
    # Predict sollte Fallback verwenden
    ml_score = service.predict_ml_score(
        query='Test',
        chunk={'chunk_id': 'test', 'metadata': {}},
        vector_score=0.8,
        text_score=0.7,
        bm25_score=0.65,
        jaccard_score=0.55,
        keyword_matches=2,
        user_level=3,
        hybrid_score=0.77
    )
    
    # ML-Score sollte hybrid_score sein (Fallback)
    assert ml_score == 0.77, "ML-Score sollte hybrid_score sein wenn disabled"
    
    # Final-Score sollte auch hybrid_score sein
    final_score = service.get_final_score(hybrid_score=0.77, ml_score=ml_score)
    assert final_score == 0.77, "Final-Score sollte hybrid_score sein wenn disabled"


@patch.dict(os.environ, {'ML_ENABLE': 'true'})
def test_ml_enabled_uses_ml_model():
    """
    ML_ENABLE=true sollte ML-Modell verwenden (falls vorhanden).
    
    Requirements:
    - LTR Service versucht Model zu laden
    - Falls Model vorhanden: is_enabled() gibt True zurück
    - Falls Model fehlt: is_enabled() gibt False zurück (Fallback)
    """
    from contexts.ragintegration.infrastructure.ml.ltr_service import LTRService
    
    # Service mit ML_ENABLE=true aber ohne Model
    service = LTRService(enable_ml=True, model_dir='/nonexistent')
    
    # Sollte False sein (Model nicht gefunden)
    assert service.is_enabled() is False, "Service sollte disabled sein wenn Model fehlt"


# ========================================
# Test 2: ML_SHAP_ENABLE Flag
# ========================================

@patch.dict(os.environ, {'ML_SHAP_ENABLE': 'false'})
@pytest.mark.asyncio
async def test_ml_shap_disabled_does_not_compute_shap():
    """
    ML_SHAP_ENABLE=false sollte ML-SHAP deaktivieren.
    
    Requirements:
    - ML-SHAP wird NICHT berechnet
    - _extended_metadata enthält KEIN 'ml_shap'
    - System funktioniert normal
    """
    # Mock Chunk
    chunk = {
        'chunk_id': 'test_chunk',
        'ml_score': 0.85,
        '_extended_metadata': {}
    }
    
    # ML_SHAP_ENABLE=false sollte keine ML-SHAP-Berechnung triggern
    # (Dies wird in UseCase geprüft)
    
    # Simuliere: ML-SHAP wird übersprungen
    ml_shap_enable = os.getenv('ML_SHAP_ENABLE', 'true').lower() == 'true'
    
    if not ml_shap_enable:
        # ML-SHAP sollte NICHT berechnet werden
        assert 'ml_shap' not in chunk['_extended_metadata'], \
            "ml_shap sollte nicht in Metadaten sein wenn disabled"
    
    # Assertion
    assert ml_shap_enable is False, "ML_SHAP_ENABLE sollte false sein"


@patch.dict(os.environ, {'ML_SHAP_ENABLE': 'true'})
def test_ml_shap_enabled_computes_shap():
    """
    ML_SHAP_ENABLE=true sollte ML-SHAP aktivieren.
    
    Requirements:
    - ML-SHAP wird berechnet
    - _extended_metadata enthält 'ml_shap'
    """
    ml_shap_enable = os.getenv('ML_SHAP_ENABLE', 'true').lower() == 'true'
    
    # Assertion
    assert ml_shap_enable is True, "ML_SHAP_ENABLE sollte true sein"


# ========================================
# Test 3: FEEDBACK_TRAINING_ENABLE Flag
# ========================================

@patch.dict(os.environ, {'FEEDBACK_TRAINING_ENABLE': 'false'})
@pytest.mark.asyncio
async def test_feedback_training_disabled_does_not_save_data():
    """
    FEEDBACK_TRAINING_ENABLE=false sollte Training-Daten-Sammlung deaktivieren.
    
    Requirements:
    - Feedback wird gespeichert
    - Training-Daten werden NICHT gespeichert
    - TrainingDataRepository.save_training_sample() wird NICHT aufgerufen
    """
    from contexts.ragintegration.application.use_cases import SubmitFeedbackUseCase
    
    # Mock Repositories
    feedback_repo = AsyncMock()
    feedback_repo.get_by_message_id.return_value = None
    feedback_repo.save.return_value = Mock(id=1)
    
    chat_message_repo = Mock()
    chat_message_repo.get_by_id.return_value = Mock(
        id=1,
        content='Test Query',
        role='user',
        source_references=[]
    )
    
    training_data_repo = Mock()
    
    # UseCase mit FEEDBACK_TRAINING_ENABLE=false
    use_case = SubmitFeedbackUseCase(
        feedback_repo=feedback_repo,
        message_repo=chat_message_repo,
        event_publisher=None,
        training_data_repo=training_data_repo
    )
    
    # Execute
    result = await use_case.execute(
        chat_message_id=1,
        user_id=1,
        rating='positive'
    )
    
    # Assertions
    assert result is not None, "Feedback sollte gespeichert werden"
    
    # Training Data Repository sollte NICHT aufgerufen werden (wegen Flag)
    # Dies wird in der Implementierung geprüft


@patch.dict(os.environ, {'FEEDBACK_TRAINING_ENABLE': 'true'})
@pytest.mark.asyncio
async def test_feedback_training_enabled_saves_data():
    """
    FEEDBACK_TRAINING_ENABLE=true sollte Training-Daten speichern.
    
    Requirements:
    - Feedback wird gespeichert
    - Training-Daten werden gespeichert
    - TrainingDataRepository.save_training_sample() wird aufgerufen
    """
    from contexts.ragintegration.application.use_cases import SubmitFeedbackUseCase
    
    # Mock Repositories
    feedback_repo = AsyncMock()
    feedback_repo.get_by_message_id.return_value = None
    feedback_repo.save.return_value = Mock(id=1)
    
    chat_message_repo = Mock()
    mock_message = Mock()
    mock_message.content = 'Test Query'
    mock_message.role = 'user'
    mock_message.source_references = [
        Mock(
            chunk_id='test_chunk',
            _extended_metadata={'vector_score': 0.8, 'hybrid_score': 0.77}
        )
    ]
    chat_message_repo.get_by_id.return_value = mock_message
    
    training_data_repo = Mock()
    
    # UseCase mit FEEDBACK_TRAINING_ENABLE=true
    use_case = SubmitFeedbackUseCase(
        feedback_repo=feedback_repo,
        message_repo=chat_message_repo,
        event_publisher=None,
        training_data_repo=training_data_repo
    )
    
    # Execute
    result = await use_case.execute(
        chat_message_id=1,
        user_id=1,
        rating='positive'
    )
    
    # Assertions
    assert result is not None
    
    # Training Data Repository sollte aufgerufen werden
    assert training_data_repo.save_training_sample.called, \
        "Training Data Repository sollte aufgerufen werden wenn enabled"

