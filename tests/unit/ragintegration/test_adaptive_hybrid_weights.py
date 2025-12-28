"""
Unit Tests für adaptive Hybrid-Score-Gewichtung.

RED Phase: Tests schlagen fehl, da _get_adaptive_weights() noch nicht existiert.
GREEN Phase: Code implementieren bis Tests GRÜN sind.
REFACTOR Phase: Code optimieren (Tests bleiben GRÜN).
"""

import pytest
from contexts.ragintegration.infrastructure.vector_store_adapter import QdrantVectorStoreAdapter


def test_adaptive_weights_keyword_query():
    """
    Test: Keyword-basierte Queries sollten 50/50 Gewichtung haben.
    
    RED: Schlägt fehl, da Funktion nicht existiert.
    GREEN: Funktion implementieren mit Keyword-Erkennung.
    """
    # Arrange
    query = "Montage Schritte Zusammenbau Installation"
    
    # Act
    vector_weight, text_weight = QdrantVectorStoreAdapter._get_adaptive_weights(query)
    
    # Assert
    assert vector_weight == 0.5, f"Keyword-Query sollte 50% Vector haben, bekam {vector_weight}"
    assert text_weight == 0.5, f"Keyword-Query sollte 50% Text haben, bekam {text_weight}"


def test_adaptive_weights_semantic_query():
    """
    Test: Semantische Queries sollten 70/30 Gewichtung haben.
    
    RED: Schlägt fehl, da Funktion nicht existiert.
    GREEN: Funktion implementieren mit semantischer Query-Erkennung.
    """
    # Arrange
    query = "Wie funktioniert das?"
    
    # Act
    vector_weight, text_weight = QdrantVectorStoreAdapter._get_adaptive_weights(query)
    
    # Assert
    assert vector_weight == 0.7, f"Semantische Query sollte 70% Vector haben, bekam {vector_weight}"
    assert text_weight == 0.3, f"Semantische Query sollte 30% Text haben, bekam {text_weight}"


def test_adaptive_weights_stop_words_ignored():
    """
    Test: Stop-Wörter sollten bei Keyword-Erkennung ignoriert werden.
    
    RED: Schlägt fehl, da Funktion nicht existiert.
    GREEN: Funktion implementieren mit Stop-Wort-Filterung.
    """
    # Arrange
    query = "der die das und Montage Schritte Zusammenbau"
    
    # Act
    vector_weight, text_weight = QdrantVectorStoreAdapter._get_adaptive_weights(query)
    
    # Assert
    # "Montage", "Schritte", "Zusammenbau" sind 3 wichtige Keywords → 50/50 (> 2)
    assert vector_weight == 0.5, "Stop-Wörter sollten ignoriert werden, 3+ wichtige Keywords sollten 50/50 ergeben"
    assert text_weight == 0.5


def test_adaptive_weights_single_keyword():
    """
    Test: Einzelnes Keyword sollte 70/30 Gewichtung haben (nicht genug für 50/50).
    
    RED: Schlägt fehl, da Funktion nicht existiert.
    GREEN: Funktion implementieren mit Schwellenwert-Logik.
    """
    # Arrange
    query = "Montage"
    
    # Act
    vector_weight, text_weight = QdrantVectorStoreAdapter._get_adaptive_weights(query)
    
    # Assert
    # Nur 1 Keyword → 70/30 (nicht genug für 50/50)
    assert vector_weight == 0.7, "Einzelnes Keyword sollte 70/30 ergeben"
    assert text_weight == 0.3


def test_adaptive_weights_three_keywords():
    """
    Test: Drei Keywords sollten 50/50 Gewichtung haben.
    
    RED: Schlägt fehl, da Funktion nicht existiert.
    GREEN: Funktion implementieren mit Schwellenwert > 2.
    """
    # Arrange
    query = "Montage Schritte Zusammenbau"
    
    # Act
    vector_weight, text_weight = QdrantVectorStoreAdapter._get_adaptive_weights(query)
    
    # Assert
    # 3 Keywords → 50/50
    assert vector_weight == 0.5, "Drei Keywords sollten 50/50 ergeben"
    assert text_weight == 0.5


def test_adaptive_weights_empty_query():
    """
    Test: Leere Query sollte 70/30 Gewichtung haben (Fallback).
    
    RED: Schlägt fehl, da Funktion nicht existiert.
    GREEN: Funktion implementieren mit Fallback-Logik.
    """
    # Arrange
    query = ""
    
    # Act
    vector_weight, text_weight = QdrantVectorStoreAdapter._get_adaptive_weights(query)
    
    # Assert
    # Leere Query → Fallback 70/30
    assert vector_weight == 0.7, "Leere Query sollte Fallback 70/30 haben"
    assert text_weight == 0.3


def test_adaptive_weights_only_stop_words():
    """
    Test: Query nur mit Stop-Wörtern sollte 70/30 Gewichtung haben.
    
    RED: Schlägt fehl, da Funktion nicht existiert.
    GREEN: Funktion implementieren mit Stop-Wort-Filterung.
    """
    # Arrange
    query = "der die das und oder aber"
    
    # Act
    vector_weight, text_weight = QdrantVectorStoreAdapter._get_adaptive_weights(query)
    
    # Assert
    # Nur Stop-Wörter → 70/30 (keine wichtigen Keywords)
    assert vector_weight == 0.7, "Nur Stop-Wörter sollte 70/30 ergeben"
    assert text_weight == 0.3

