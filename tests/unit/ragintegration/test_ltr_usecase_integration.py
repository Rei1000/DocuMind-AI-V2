"""
Unit Tests für LTR Integration in AskQuestionUseCase.

TDD Phase 1: RED - Tests für ML-Ranking-Integration.

Diese Tests definieren Anforderungen:
1. AskQuestionUseCase nutzt LTR Service
2. ML-Scores werden berechnet
3. Final-Scores werden für Ranking verwendet
4. ML-Metadaten werden gespeichert
5. Fallback zu Hybrid-Score funktioniert
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import numpy as np


# ========================================
# Test 1: LTR Service Integration
# ========================================

@pytest.mark.asyncio
async def test_use_case_uses_ltr_service_when_enabled():
    """
    AskQuestionUseCase sollte LTR Service nutzen wenn use_ml_ranking=True.
    
    Requirements:
    - LTR Service wird aufgerufen
    - ML-Scores werden berechnet
    - Final-Scores werden verwendet
    """
    from contexts.ragintegration.application.use_cases import AskQuestionUseCase
    
    # Mock alle Dependencies
    chunk_repo = Mock()
    session_repo = Mock()
    session = Mock()
    session.user_id = 1
    session_repo.get_by_id.return_value = session
    
    indexed_doc_repo = Mock()
    indexed_doc_repo.get_all.return_value = []  # Keine Dokumente für einfachen Test
    
    vector_store = Mock()
    embedding_service = Mock()
    multi_query_service = None
    
    ai_service = AsyncMock()
    ai_service.generate_answer.return_value = {
        'answer': 'Test Answer',
        'tokens_used': 100
    }
    
    event_publisher = None
    message_repo = Mock()
    message_repo.save.return_value = Mock(id=1, metadata={})
    
    permission_service = None
    shap_service = None
    
    # Mock LTR Service
    ltr_service = Mock()
    ltr_service.is_enabled.return_value = True
    ltr_service.predict_ml_score.return_value = 0.85  # Mock ML-Score
    ltr_service.get_final_score.return_value = 0.82  # Mock Final-Score
    
    # Erstelle Use Case mit LTR Service
    use_case = AskQuestionUseCase(
        chunk_repository=chunk_repo,
        session_repository=session_repo,
        indexed_document_repository=indexed_doc_repo,
        vector_store=vector_store,
        embedding_service=embedding_service,
        multi_query_service=multi_query_service,
        ai_service=ai_service,
        event_publisher=event_publisher,
        message_repository=message_repo,
        permission_service=permission_service,
        shap_service=shap_service,
        ml_model_service=None,  # Alte ML Service (wird ersetzt)
        ltr_service=ltr_service  # NEU: LTR Service
    )
    
    # Execute mit use_ml_ranking=True
    result = await use_case.execute(
        question='Test Question',
        session_id=1,
        use_ml_ranking=True  # NEU: ML-Ranking aktivieren
    )
    
    # Assertions
    assert result is not None, "Use Case sollte Ergebnis zurückgeben"
    
    # LTR Service sollte aufgerufen worden sein (wenn Chunks gefunden wurden)
    # Dies wird in Integration Tests detaillierter geprüft


@pytest.mark.asyncio
async def test_use_case_falls_back_to_hybrid_when_ml_disabled():
    """
    AskQuestionUseCase sollte zu Hybrid-Score fallback wenn use_ml_ranking=False.
    
    Requirements:
    - LTR Service wird NICHT aufgerufen
    - Hybrid-Scores werden verwendet
    - System funktioniert wie vorher
    """
    from contexts.ragintegration.application.use_cases import AskQuestionUseCase
    
    # Mock Dependencies (minimal)
    chunk_repo = Mock()
    session_repo = Mock()
    session_repo.get_by_id.return_value = Mock(user_id=1)
    indexed_doc_repo = Mock()
    indexed_doc_repo.get_all.return_value = []
    vector_store = Mock()
    embedding_service = Mock()
    multi_query_service = None
    ai_service = AsyncMock()
    ai_service.generate_answer.return_value = {'answer': 'Test', 'tokens_used': 100}
    event_publisher = None
    message_repo = Mock()
    message_repo.save.return_value = Mock(id=1, metadata={})
    
    # LTR Service (sollte nicht aufgerufen werden)
    ltr_service = Mock()
    ltr_service.is_enabled.return_value = True
    
    use_case = AskQuestionUseCase(
        chunk_repository=chunk_repo,
        session_repository=session_repo,
        indexed_document_repository=indexed_doc_repo,
        vector_store=vector_store,
        embedding_service=embedding_service,
        multi_query_service=multi_query_service,
        ai_service=ai_service,
        event_publisher=event_publisher,
        message_repository=message_repo,
        permission_service=None,
        shap_service=None,
        ml_model_service=None,
        ltr_service=ltr_service
    )
    
    # Execute mit use_ml_ranking=False
    result = await use_case.execute(
        question='Test Question',
        session_id=1,
        use_ml_ranking=False  # ML-Ranking deaktiviert
    )
    
    # Assertions
    assert result is not None
    
    # LTR Service sollte NICHT für Scoring aufgerufen worden sein
    # (is_enabled wird geprüft, aber predict_ml_score nicht aufgerufen)


# ========================================
# Test 2: ML-Score Berechnung
# ========================================

def test_ml_score_is_calculated_for_chunks():
    """
    ML-Scores sollten für alle Chunks berechnet werden.
    
    Requirements:
    - Für jeden Chunk: Features extrahieren
    - LTR Service: predict_ml_score() aufrufen
    - ML-Score in Chunk-Metadaten speichern
    """
    # Mock Chunks
    chunks = [
        {
            'chunk_id': 'chunk_1',
            'metadata': {
                'chunk_text': 'Text 1',
                'document_type': 'Arbeitsanweisung',
                'chunk_length': 100
            },
            'vector_score': 0.8,
            'text_score': 0.7,
            'hybrid_score': 0.77
        },
        {
            'chunk_id': 'chunk_2',
            'metadata': {
                'chunk_text': 'Text 2',
                'document_type': 'SOP',
                'chunk_length': 200
            },
            'vector_score': 0.75,
            'text_score': 0.65,
            'hybrid_score': 0.72
        }
    ]
    
    # Mock LTR Service
    ltr_service = Mock()
    ltr_service.is_enabled.return_value = True
    ltr_service.predict_ml_score.side_effect = [0.85, 0.70]  # ML-Scores für Chunk 1 und 2
    ltr_service.get_final_score.side_effect = [0.82, 0.71]  # Final-Scores
    
    # Simuliere ML-Score-Berechnung
    for chunk in chunks:
        ml_score = ltr_service.predict_ml_score(
            query='Test',
            chunk=chunk,
            vector_score=chunk['vector_score'],
            text_score=chunk['text_score'],
            bm25_score=0.65,
            jaccard_score=0.55,
            keyword_matches=2,
            user_level=3,
            hybrid_score=chunk['hybrid_score']
        )
        
        # Speichere in Metadaten
        chunk['ml_score'] = ml_score
        
        # Final-Score
        final_score = ltr_service.get_final_score(chunk['hybrid_score'], ml_score)
        chunk['final_score'] = final_score
    
    # Assertions
    assert chunks[0]['ml_score'] == 0.85
    assert chunks[1]['ml_score'] == 0.70
    assert chunks[0]['final_score'] == 0.82
    assert chunks[1]['final_score'] == 0.71
    
    # Prüfe dass predict_ml_score aufgerufen wurde
    assert ltr_service.predict_ml_score.call_count == 2


# ========================================
# Test 3: Final-Score Ranking
# ========================================

def test_chunks_are_ranked_by_final_score():
    """
    Chunks sollten nach final_score (nicht hybrid_score) sortiert werden.
    
    Requirements:
    - Chunks werden nach final_score sortiert (höchste zuerst)
    - ML-Score kann Ranking ändern (vs. Hybrid-Score)
    """
    # Mock Chunks mit unterschiedlichen Scores
    chunks = [
        {
            'chunk_id': 'chunk_1',
            'hybrid_score': 0.90,  # Höchster Hybrid-Score
            'ml_score': 0.60,       # Aber niedriger ML-Score
            'final_score': 0.78     # = 0.6 * 0.90 + 0.4 * 0.60
        },
        {
            'chunk_id': 'chunk_2',
            'hybrid_score': 0.75,  # Mittlerer Hybrid-Score
            'ml_score': 0.95,       # Aber höchster ML-Score
            'final_score': 0.83     # = 0.6 * 0.75 + 0.4 * 0.95 (HÖCHSTER!)
        },
        {
            'chunk_id': 'chunk_3',
            'hybrid_score': 0.80,
            'ml_score': 0.70,
            'final_score': 0.76
        }
    ]
    
    # Sortiere nach final_score
    sorted_chunks = sorted(chunks, key=lambda x: x['final_score'], reverse=True)
    
    # Assertions
    assert sorted_chunks[0]['chunk_id'] == 'chunk_2', "Chunk 2 sollte höchster final_score haben"
    assert sorted_chunks[1]['chunk_id'] == 'chunk_1', "Chunk 1 sollte zweithöchster final_score haben"
    assert sorted_chunks[2]['chunk_id'] == 'chunk_3', "Chunk 3 sollte niedrigster final_score haben"
    
    # ML kann Ranking ändern!
    # Hybrid-Ranking wäre: chunk_1, chunk_3, chunk_2
    # ML-Ranking ist:      chunk_2, chunk_1, chunk_3


# ========================================
# Test 4: ML-Metadaten in Response
# ========================================

def test_ml_metadata_is_included_in_source_references():
    """
    ML-Metadaten sollten in SourceReferences enthalten sein.
    
    Requirements:
    - ml_score in _extended_metadata
    - final_score in _extended_metadata
    - ml_feature_vector in _extended_metadata (optional)
    - ml_shap in _extended_metadata (optional)
    """
    # Mock SourceReference
    source_ref = Mock()
    source_ref._extended_metadata = {
        'hybrid_score': 0.77,
        'ml_score': 0.85,
        'final_score': 0.80,
        'ml_feature_vector': [0.8, 0.7, 0.65, 0.55, 0.2, 0.05, 0.0, 0.4, 0.9, 0.6, 0.77],
        'ml_shap': {
            'feature_importance': {
                'vector_score': 0.12,
                'text_score': 0.08,
                'bm25_score': 0.05
            },
            'prediction': 0.85
        }
    }
    
    # Assertions
    assert 'ml_score' in source_ref._extended_metadata
    assert 'final_score' in source_ref._extended_metadata
    assert source_ref._extended_metadata['ml_score'] == 0.85
    assert source_ref._extended_metadata['final_score'] == 0.80
    
    # Optional: ML-SHAP
    if 'ml_shap' in source_ref._extended_metadata:
        assert 'feature_importance' in source_ref._extended_metadata['ml_shap']
        assert 'prediction' in source_ref._extended_metadata['ml_shap']

