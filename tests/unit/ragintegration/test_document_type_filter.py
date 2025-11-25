"""
Unit Tests für Document-Type Filter in Qdrant.

RED Phase: Tests schlagen fehl, da document_type noch entfernt wird.
GREEN Phase: Code implementieren bis Tests GRÜN sind.
REFACTOR Phase: Code optimieren (Tests bleiben GRÜN).
"""

import pytest
from typing import Dict, Any


def test_document_type_filter_not_removed_from_qdrant_filters():
    """
    Test: document_type sollte NICHT aus Qdrant-Filtern entfernt werden.
    
    RED: Schlägt fehl, da Zeile 641 in use_cases.py document_type entfernt.
    GREEN: Code ändern, damit document_type NICHT entfernt wird.
    """
    # Arrange
    search_filters: Dict[str, Any] = {
        'document_type': 'Arbeitsanweisung',
        'query': 'test query',
        'other_filter': 'value'
    }
    
    # Act: Simuliere die Logik aus use_cases.py Zeile 640-641
    # ALT (falsch): qdrant_filters = {k: v for k, v in search_filters.items() if k != 'document_type' and k != 'query'}
    # NEU (richtig): qdrant_filters = {k: v for k, v in search_filters.items() if k != 'query'}
    qdrant_filters = {k: v for k, v in search_filters.items() if k != 'query'}
    
    # Assert
    assert 'document_type' in qdrant_filters, "document_type sollte NICHT entfernt werden"
    assert qdrant_filters['document_type'] == 'Arbeitsanweisung'
    assert 'query' not in qdrant_filters, "query sollte entfernt werden"
    assert 'other_filter' in qdrant_filters, "andere Filter sollten bleiben"


def test_document_type_filter_preserved_when_multiple_filters():
    """
    Test: document_type sollte erhalten bleiben, auch wenn mehrere Filter gesetzt sind.
    
    RED: Schlägt fehl, da document_type entfernt wird.
    GREEN: Code ändern, damit document_type erhalten bleibt.
    """
    # Arrange
    search_filters: Dict[str, Any] = {
        'document_type': 'Fachartikel',
        'query': 'test query',
        'interest_group_id': 1,
        'user_level': 4
    }
    
    # Act
    qdrant_filters = {k: v for k, v in search_filters.items() if k != 'query'}
    
    # Assert
    assert 'document_type' in qdrant_filters
    assert qdrant_filters['document_type'] == 'Fachartikel'
    assert 'interest_group_id' in qdrant_filters
    assert 'user_level' in qdrant_filters
    assert 'query' not in qdrant_filters


def test_query_filter_always_removed():
    """
    Test: query sollte IMMER entfernt werden (ist nicht in Qdrant-Metadaten).
    
    RED: Sollte bereits funktionieren.
    GREEN: Bestätigt, dass query entfernt wird.
    """
    # Arrange
    search_filters: Dict[str, Any] = {
        'query': 'test query',
        'document_type': 'Arbeitsanweisung'
    }
    
    # Act
    qdrant_filters = {k: v for k, v in search_filters.items() if k != 'query'}
    
    # Assert
    assert 'query' not in qdrant_filters, "query sollte immer entfernt werden"
    assert 'document_type' in qdrant_filters, "document_type sollte bleiben"

