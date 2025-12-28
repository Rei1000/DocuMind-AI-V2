"""
Unit Tests für dynamischen Score-Threshold.

RED Phase: Tests schlagen fehl, da get_dynamic_threshold() noch nicht existiert.
GREEN Phase: Code implementieren bis Tests GRÜN sind.
REFACTOR Phase: Code optimieren (Tests bleiben GRÜN).
"""

import pytest
from contexts.ragintegration.application.use_cases import get_dynamic_threshold


def test_dynamic_threshold_openai():
    """
    Test: OpenAI Embeddings sollten niedrigen Threshold haben (0.01).
    
    RED: Schlägt fehl, da Funktion nicht existiert.
    GREEN: Funktion implementieren mit OpenAI-Erkennung.
    """
    # Arrange
    embedding_model = "text-embedding-3-small"
    base_threshold = 0.01
    
    # Act
    threshold = get_dynamic_threshold(embedding_model, base_threshold)
    
    # Assert
    assert threshold == 0.01, "OpenAI sollte niedrigen Threshold behalten"


def test_dynamic_threshold_openai_ada():
    """
    Test: OpenAI Ada Embeddings sollten auch niedrigen Threshold haben.
    
    RED: Schlägt fehl, da Funktion nicht existiert.
    GREEN: Funktion implementieren mit OpenAI-Erkennung.
    """
    # Arrange
    embedding_model = "text-embedding-ada-002"
    base_threshold = 0.01
    
    # Act
    threshold = get_dynamic_threshold(embedding_model, base_threshold)
    
    # Assert
    assert threshold == 0.01, "OpenAI Ada sollte niedrigen Threshold behalten"


def test_dynamic_threshold_google_gemini():
    """
    Test: Google Gemini Embeddings sollten höheren Threshold haben (0.3-0.5).
    
    RED: Schlägt fehl, da Funktion nicht existiert.
    GREEN: Funktion implementieren mit Google Gemini-Erkennung.
    """
    # Arrange
    embedding_model = "text-embedding-004"
    base_threshold = 0.01
    
    # Act
    threshold = get_dynamic_threshold(embedding_model, base_threshold)
    
    # Assert
    assert threshold >= 0.3, f"Google Gemini sollte Threshold >= 0.3 haben, bekam {threshold}"
    assert threshold <= 0.5, f"Google Gemini sollte Threshold <= 0.5 haben, bekam {threshold}"


def test_dynamic_threshold_google_gemini_case_insensitive():
    """
    Test: Google Gemini Erkennung sollte case-insensitive sein.
    
    RED: Schlägt fehl, da Funktion nicht existiert.
    GREEN: Funktion implementieren mit case-insensitive Erkennung.
    """
    # Arrange
    embedding_model = "TEXT-EMBEDDING-004"
    base_threshold = 0.01
    
    # Act
    threshold = get_dynamic_threshold(embedding_model, base_threshold)
    
    # Assert
    assert threshold >= 0.3, "Google Gemini sollte auch bei Großbuchstaben erkannt werden"


def test_dynamic_threshold_sentence_transformers():
    """
    Test: Sentence Transformers sollten sehr hohen Threshold haben (0.5-0.7).
    
    RED: Schlägt fehl, da Funktion nicht existiert.
    GREEN: Funktion implementieren mit Sentence Transformers-Erkennung.
    """
    # Arrange
    embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
    base_threshold = 0.01
    
    # Act
    threshold = get_dynamic_threshold(embedding_model, base_threshold)
    
    # Assert
    assert threshold >= 0.5, f"Sentence Transformers sollte Threshold >= 0.5 haben, bekam {threshold}"
    assert threshold <= 0.7, f"Sentence Transformers sollte Threshold <= 0.7 haben, bekam {threshold}"


def test_dynamic_threshold_sentence_transformers_all_minilm():
    """
    Test: all-MiniLM Modelle sollten als Sentence Transformers erkannt werden.
    
    RED: Schlägt fehl, da Funktion nicht existiert.
    GREEN: Funktion implementieren mit all-minilm Erkennung.
    """
    # Arrange
    embedding_model = "all-minilm-l6-v2"
    base_threshold = 0.01
    
    # Act
    threshold = get_dynamic_threshold(embedding_model, base_threshold)
    
    # Assert
    assert threshold >= 0.5, "all-MiniLM sollte als Sentence Transformers erkannt werden"


def test_dynamic_threshold_unknown_model():
    """
    Test: Unbekannte Modelle sollten Fallback auf base_threshold haben.
    
    RED: Schlägt fehl, da Funktion nicht existiert.
    GREEN: Funktion implementieren mit Fallback-Logik.
    """
    # Arrange
    embedding_model = "unknown-model-v1"
    base_threshold = 0.01
    
    # Act
    threshold = get_dynamic_threshold(embedding_model, base_threshold)
    
    # Assert
    assert threshold == base_threshold, "Unbekannte Modelle sollten base_threshold verwenden"


def test_dynamic_threshold_custom_base_threshold():
    """
    Test: Custom base_threshold sollte respektiert werden.
    
    RED: Schlägt fehl, da Funktion nicht existiert.
    GREEN: Funktion implementieren mit base_threshold-Parameter.
    """
    # Arrange
    embedding_model = "text-embedding-3-small"
    base_threshold = 0.05
    
    # Act
    threshold = get_dynamic_threshold(embedding_model, base_threshold)
    
    # Assert
    assert threshold == 0.05, "Custom base_threshold sollte respektiert werden"

