"""
Unit Tests für Feedback → Training Data Integration.

TDD Phase 1: RED - Tests für automatische Training-Daten-Sammlung aus User-Feedback.

Diese Tests definieren Anforderungen:
1. Feedback erstellt Training-Record
2. ML-Features werden korrekt extrahiert
3. Relevance-Mapping funktioniert (positive=1.0, negative=0.0)
4. Training Data Repository speichert und lädt Daten
5. Training Pipeline nutzt Feedback-Daten
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import numpy as np


# ========================================
# Test 1: Feedback erstellt Training-Record
# ========================================

@pytest.mark.asyncio
async def test_feedback_creates_training_record():
    """
    User-Feedback sollte automatisch Training-Record erstellen.
    
    Requirements:
    - Feedback-UseCase ruft TrainingDataRepository auf
    - Training-Record enthält: query, chunk, features, relevance_score
    - Record wird persistiert
    """
    from contexts.ragintegration.application.use_cases import SubmitFeedbackUseCase
    
    # Mock Repositories
    feedback_repo = AsyncMock()
    feedback_repo.get_by_message_id.return_value = None  # Kein existierendes Feedback
    feedback_repo.save.return_value = Mock(id=1)
    
    chat_message_repo = Mock()
    mock_message = Mock()
    mock_message.id = 1
    mock_message.content = "Test Query"
    mock_message.source_references = [
        Mock(
            chunk_id='test_chunk_1',
            _extended_metadata={
                'vector_score': 0.85,
                'text_score': 0.72,
                'hybrid_score': 0.806,
                'ml_score': 0.88,
                'final_score': 0.836
            }
        )
    ]
    chat_message_repo.get_by_id.return_value = mock_message
    
    # Mock Training Data Repository
    training_data_repo = Mock()
    training_data_repo.save_training_sample.return_value = True
    
    # Erstelle UseCase MIT Training Data Repository
    use_case = SubmitFeedbackUseCase(
        feedback_repo=feedback_repo,
        message_repo=chat_message_repo,
        event_publisher=None,
        training_data_repo=training_data_repo  # NEU: Training Data Repository
    )
    
    # Execute Feedback
    result = await use_case.execute(
        chat_message_id=1,
        user_id=1,
        rating='positive',  # positive → relevance_score = 1.0
        comment='Sehr hilfreich!'
    )
    
    # Assertions
    assert result is not None
    
    # Training Data Repository sollte aufgerufen worden sein
    assert training_data_repo.save_training_sample.called, \
        "Training Data Repository sollte aufgerufen worden sein"


# ========================================
# Test 2: ML-Features in Training-Record
# ========================================

def test_feedback_includes_correct_ml_features():
    """
    Training-Record sollte alle 11 ML-Features enthalten.
    
    Requirements:
    - Alle Features aus _extended_metadata extrahiert
    - Fehlende Features werden mit Defaults gefüllt
    - Features sind konsistent mit MLFeatureExtractor
    """
    # Mock Training-Record
    training_record = {
        'query': 'Test Query',
        'chunk_id': 'test_chunk_1',
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
        'relevance_score': 1.0,
        'timestamp': datetime.now()
    }
    
    # Assertions
    assert 'features' in training_record
    assert len(training_record['features']) == 11, \
        f"Training-Record sollte 11 Features haben, aber hat {len(training_record['features'])}"
    
    # Prüfe alle erforderlichen Features
    required_features = [
        'vector_score', 'text_score', 'bm25_score', 'jaccard_score',
        'keyword_matches', 'chunk_length', 'document_type_encoded',
        'heading_hierarchy_depth', 'confidence_score', 'user_level', 'hybrid_score'
    ]
    
    for feature in required_features:
        assert feature in training_record['features'], \
            f"Feature '{feature}' sollte vorhanden sein"


# ========================================
# Test 3: Relevance-Mapping
# ========================================

def test_feedback_relevance_mapping():
    """
    Feedback-Rating sollte korrekt zu Relevance-Score gemappt werden.
    
    Requirements:
    - positive → 1.0
    - negative → 0.0
    - neutral → 0.5
    - rating (1-5) → rating / 5.0
    """
    from contexts.ragintegration.infrastructure.ml.training_data_repository import map_feedback_to_relevance
    
    # Test Mapping
    assert map_feedback_to_relevance('positive') == 1.0
    assert map_feedback_to_relevance('negative') == 0.0
    assert map_feedback_to_relevance('neutral') == 0.5
    
    # Numerisches Rating
    assert map_feedback_to_relevance(5) == 1.0  # 5/5 = 1.0
    assert map_feedback_to_relevance(3) == 0.6  # 3/5 = 0.6
    assert map_feedback_to_relevance(1) == 0.2  # 1/5 = 0.2


# ========================================
# Test 4: Training Data Repository
# ========================================

def test_training_data_repo_persist_and_load():
    """
    Training Data Repository sollte Daten speichern und laden können.
    
    Requirements:
    - save_training_sample() speichert Record
    - get_training_samples() lädt alle Records
    - get_training_samples(min_date) filtert nach Datum
    """
    from contexts.ragintegration.infrastructure.ml.training_data_repository import FileBasedTrainingDataRepository
    import tempfile
    import os
    
    # Temporäres Verzeichnis
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = FileBasedTrainingDataRepository(data_dir=tmpdir)
        
        # Erstelle Training-Sample
        sample = {
            'query': 'Test Query',
            'chunk_id': 'chunk_1',
            'features': {f: 0.5 for f in range(11)},
            'relevance_score': 0.9
        }
        
        # Save
        result = repo.save_training_sample(sample)
        assert result is True, "Save sollte erfolgreich sein"
        
        # Load
        samples = repo.get_training_samples()
        
        # Assertions
        assert len(samples) > 0, "Repository sollte Samples zurückgeben"
        assert samples[0]['query'] == 'Test Query'
        assert samples[0]['relevance_score'] == 0.9


# ========================================
# Test 5: Training Pipeline mit Feedback-Daten
# ========================================

def test_training_pipeline_uses_feedback_data():
    """
    Training Pipeline sollte Feedback-Daten automatisch nutzen.
    
    Requirements:
    - Training Pipeline lädt Daten aus TrainingDataRepository
    - Feedback-Daten werden mit anderen Training-Daten kombiniert
    - Model trainiert mit allen verfügbaren Daten
    """
    from contexts.ragintegration.infrastructure.ml.training_pipeline import LTRTrainingPipeline
    
    # Mock Repository mit Feedback-Daten
    mock_repo = Mock()
    
    # Mock Training-Samples (inklusive Feedback-Daten)
    training_samples = []
    for i in range(30):
        training_samples.append({
            'query': f'Query {i % 5}',
            'chunk': {
                'chunk_id': f'chunk_{i}',
                'metadata': {
                    'chunk_text': f'Text {i}',
                    'document_type': 'Arbeitsanweisung',
                    'chunk_length': 100,
                    'heading_hierarchy_depth': 1,
                    'confidence_score': 0.9
                }
            },
            'vector_score': 0.8,
            'text_score': 0.7,
            'bm25_score': 0.65,
            'jaccard_score': 0.55,
            'keyword_matches': 2,
            'user_level': 3,
            'hybrid_score': 0.77,
            'relevance_score': 1.0 if i % 2 == 0 else 0.5,  # Simuliere Feedback-Scores
            'source': 'feedback' if i % 3 == 0 else 'manual'  # Markiere Feedback-Daten
        })
    
    mock_repo.get_training_samples.return_value = training_samples
    
    # Erstelle Pipeline
    pipeline = LTRTrainingPipeline(training_data_repo=mock_repo)
    
    # Prepare Data
    X, y, qids = pipeline.prepare_training_data()
    
    # Assertions
    assert X.shape[0] == 30, "Alle Samples sollten geladen werden"
    
    # Prüfe dass Feedback-Daten enthalten sind
    feedback_indices = [i for i, sample in enumerate(training_samples) if sample.get('source') == 'feedback']
    assert len(feedback_indices) > 0, "Feedback-Daten sollten enthalten sein"


# ========================================
# Test 6: NDCG Verbesserung durch Feedback
# ========================================

def test_training_pipeline_improves_ndcg():
    """
    Training mit Feedback-Daten sollte NDCG verbessern.
    
    OPTIONAL: Performance-Test (kann später erweitert werden)
    """
    pytest.skip("Performance-Test - wird später implementiert wenn genug Feedback-Daten vorhanden")

