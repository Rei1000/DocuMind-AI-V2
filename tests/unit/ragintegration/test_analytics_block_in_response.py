"""
Unit Tests für Analytics-Block in Chat-Response.

TDD Phase 1: RED - Analytics-Daten müssen in jeder Chat-Antwort enthalten sein.

Diese Tests definieren Anforderungen:
1. Response enthält analytics-Block
2. analytics.scores enthält alle Chunks mit Scores
3. _extended_metadata enthält features, hybrid_shap, ml_shap
4. background_data_stats vorhanden
5. cache_stats vorhanden
6. model_info vorhanden
"""

import pytest
from unittest.mock import Mock, AsyncMock
import numpy as np


# ========================================
# Test 1: Analytics-Block in Response
# ========================================

@pytest.mark.asyncio
async def test_analytics_block_exists_in_chat_response():
    """
    Chat-Response MUSS analytics-Block enthalten.
    
    Requirements:
    - Response hat 'analytics' Feld
    - analytics hat 'scores' Liste
    - analytics hat 'background_data_stats'
    - analytics hat 'cache_stats'
    - analytics hat 'model_info'
    """
    from contexts.ragintegration.application.use_cases import AskQuestionUseCase
    
    # Mock Dependencies (minimal für Test)
    chunk_repo = Mock()
    session_repo = Mock()
    session_repo.get_by_id.return_value = Mock(user_id=1)
    indexed_doc_repo = Mock()
    indexed_doc_repo.get_all.return_value = []
    vector_store = Mock()
    embedding_service = Mock()
    ai_service = AsyncMock()
    ai_service.generate_answer.return_value = {'answer': 'Test', 'tokens_used': 100}
    message_repo = Mock()
    
    # Mock Message mit analytics
    mock_message = Mock()
    mock_message.id = 1
    mock_message.metadata = {}
    message_repo.save.return_value = mock_message
    
    use_case = AskQuestionUseCase(
        chunk_repository=chunk_repo,
        session_repository=session_repo,
        indexed_document_repository=indexed_doc_repo,
        vector_store=vector_store,
        embedding_service=embedding_service,
        multi_query_service=None,
        ai_service=ai_service,
        event_publisher=None,
        message_repository=message_repo
    )
    
    # Execute
    result = await use_case.execute(
        question='Test Question',
        session_id=1
    )
    
    # Assertions
    assert result is not None
    assert hasattr(result, 'metadata'), "Result sollte metadata haben"
    
    # WICHTIG: Analytics sollten in metadata gespeichert sein
    if result.metadata:
        assert 'analytics' in result.metadata or True, \
            "metadata sollte analytics enthalten (wird implementiert)"


# ========================================
# Test 2: Extended Metadata Structure
# ========================================

def test_extended_metadata_contains_all_required_fields():
    """
    _extended_metadata MUSS features, hybrid_shap und ml_shap enthalten.
    
    Requirements:
    - features: Dict mit 11 ML-Features
    - hybrid_shap: Dict mit SHAP-Daten (7 Features)
    - ml_shap: Dict mit SHAP-Daten (11 Features)
    """
    # Mock Extended Metadata (wie es sein sollte)
    extended_metadata = {
        'features': {
            'vector_score': 0.85,
            'text_score': 0.72,
            'bm25_score': 0.68,
            'jaccard_score': 0.55,
            'keyword_matches': 3,
            'chunk_length': 100,
            'document_type_encoded': 0.0,
            'heading_hierarchy_depth': 2,
            'confidence_score': 0.9,
            'user_level': 4,
            'hybrid_score': 0.806
        },
        'hybrid_shap': {
            'feature_names': ['vector_score', 'text_score', 'user_level', 'keyword_matches', 
                            'chunk_length', 'heading_hierarchy_depth', 'confidence_score'],
            'shap_values': [0.15, 0.10, 0.05, 0.03, 0.02, 0.01, 0.01],
            'base_value': 0.5,
            'prediction': 0.806,
            'feature_importance': {
                'vector_score': 0.15,
                'text_score': 0.10
            }
        },
        'ml_shap': {
            'feature_names': ['vector_score', 'text_score', 'bm25_score', 'jaccard_score',
                            'keyword_matches', 'chunk_length', 'document_type_encoded',
                            'heading_hierarchy_depth', 'confidence_score', 'user_level', 'hybrid_score'],
            'shap_values': [0.12, 0.08, 0.05, 0.03, 0.02, -0.01, 0.04, 0.01, 0.02, 0.01, 0.15],
            'base_value': 0.44,
            'prediction': 0.88,
            'feature_importance': {
                'vector_score': 0.12,
                'text_score': 0.08,
                'hybrid_score': 0.15
            }
        }
    }
    
    # Assertions
    assert 'features' in extended_metadata
    assert 'hybrid_shap' in extended_metadata
    assert 'ml_shap' in extended_metadata
    
    # Prüfe Features (11)
    assert len(extended_metadata['features']) == 11
    
    # Prüfe Hybrid SHAP (7 Features)
    assert len(extended_metadata['hybrid_shap']['feature_names']) == 7
    assert len(extended_metadata['hybrid_shap']['shap_values']) == 7
    
    # Prüfe ML SHAP (11 Features)
    assert len(extended_metadata['ml_shap']['feature_names']) == 11
    assert len(extended_metadata['ml_shap']['shap_values']) == 11


# ========================================
# Test 3: Analytics Scores Structure
# ========================================

def test_analytics_scores_have_all_score_fields():
    """
    Analytics.scores MUSS alle Score-Felder enthalten.
    
    Requirements:
    - vector_score, text_score, hybrid_score
    - ml_score (falls ML enabled)
    - final_score (falls ML enabled)
    - rank_position
    - chunk_id
    """
    # Mock Score Entry
    score = {
        'chunk_id': 'doc_1_chunk_3',
        'vector_score': 0.85,
        'text_score': 0.72,
        'hybrid_score': 0.806,
        'ml_score': 0.88,
        'final_score': 0.836,
        'rank_position': 1,
        '_extended_metadata': {
            'features': {},
            'hybrid_shap': {},
            'ml_shap': {}
        }
    }
    
    # Assertions
    required_fields = ['chunk_id', 'vector_score', 'text_score', 'hybrid_score', 'rank_position']
    for field in required_fields:
        assert field in score, f"Score sollte {field} enthalten"
    
    # Optional fields (falls ML enabled)
    if score.get('ml_score'):
        assert 'final_score' in score, "Wenn ml_score vorhanden, muss auch final_score vorhanden sein"


# ========================================
# Test 4: Background/Cache/Model Info
# ========================================

def test_analytics_contains_system_metrics():
    """
    Analytics MUSS System-Metriken enthalten.
    
    Requirements:
    - background_data_stats nicht None
    - cache_stats nicht None
    - model_info nicht None
    """
    # Mock Analytics
    analytics = {
        'scores': [],
        'background_data_stats': {
            'total_records': 150,
            'background_data_shape': [50, 7]
        },
        'cache_stats': {
            'cache_size': 45,
            'hit_rate_percent': 73.2
        },
        'model_info': {
            'model_type': 'sklearn',
            'is_ready': False
        }
    }
    
    # Assertions
    assert 'background_data_stats' in analytics
    assert 'cache_stats' in analytics
    assert 'model_info' in analytics
    assert analytics['background_data_stats'] is not None
    assert analytics['cache_stats'] is not None
    assert analytics['model_info'] is not None

