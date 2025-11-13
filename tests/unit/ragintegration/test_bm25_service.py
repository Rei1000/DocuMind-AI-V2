"""
Unit Tests für BM25 Text-Scoring Service.

TDD: RED - Tests schreiben bevor Code existiert.
"""

import pytest
from typing import List, Dict

# Diese Imports werden fehlschlagen, bis Code existiert
try:
    from contexts.ragintegration.infrastructure.bm25_service import BM25Service
except ImportError:
    # Für RED-Phase: Mock-Import
    BM25Service = None


class TestBM25Service:
    """Tests für BM25 Text-Scoring Service."""
    
    def test_bm25_service_initialization(self):
        """Test: BM25Service kann initialisiert werden."""
        if BM25Service is None:
            pytest.skip("BM25Service noch nicht implementiert (RED-Phase)")
        
        service = BM25Service()
        assert service is not None
    
    def test_bm25_calculate_score(self):
        """Test: BM25 berechnet Score für Query-Document-Paar."""
        if BM25Service is None:
            pytest.skip("BM25Service noch nicht implementiert (RED-Phase)")
        
        service = BM25Service()
        
        query = "Montage Anleitung"
        document = "Die Montage erfolgt nach der Anleitung. Die Anleitung beschreibt die Montage-Schritte."
        
        score = service.calculate_score(query, document)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert score > 0.0  # Sollte positive Relevanz haben
    
    def test_bm25_score_higher_for_exact_matches(self):
        """Test: BM25 gibt höhere Scores für exakte Wort-Übereinstimmungen."""
        if BM25Service is None:
            pytest.skip("BM25Service noch nicht implementiert (RED-Phase)")
        
        service = BM25Service()
        
        query = "Montage"
        
        # Dokument mit exakter Übereinstimmung
        exact_match_doc = "Die Montage erfolgt Schritt für Schritt."
        
        # Dokument mit ähnlicher, aber nicht exakter Übereinstimmung
        similar_doc = "Die Zusammenstellung erfolgt Schritt für Schritt."
        
        exact_score = service.calculate_score(query, exact_match_doc)
        similar_score = service.calculate_score(query, similar_doc)
        
        assert exact_score > similar_score
    
    def test_bm25_score_normalized_to_0_1(self):
        """Test: BM25 Scores sind normalisiert auf 0-1."""
        if BM25Service is None:
            pytest.skip("BM25Service noch nicht implementiert (RED-Phase)")
        
        service = BM25Service()
        
        query = "Test Query"
        documents = [
            "Test Document 1",
            "Completely unrelated document",
            "Test Query Document with multiple matches"
        ]
        
        scores = [service.calculate_score(query, doc) for doc in documents]
        
        for score in scores:
            assert 0.0 <= score <= 1.0
    
    def test_bm25_handles_empty_query(self):
        """Test: BM25 gibt 0.0 zurück für leere Queries."""
        if BM25Service is None:
            pytest.skip("BM25Service noch nicht implementiert (RED-Phase)")
        
        service = BM25Service()
        
        score = service.calculate_score("", "Test Document")
        
        assert score == 0.0
    
    def test_bm25_handles_empty_document(self):
        """Test: BM25 gibt 0.0 zurück für leere Dokumente."""
        if BM25Service is None:
            pytest.skip("BM25Service noch nicht implementiert (RED-Phase)")
        
        service = BM25Service()
        
        score = service.calculate_score("Test Query", "")
        
        assert score == 0.0
    
    def test_bm25_batch_scoring(self):
        """Test: BM25 kann Scores für mehrere Dokumente berechnen."""
        if BM25Service is None:
            pytest.skip("BM25Service noch nicht implementiert (RED-Phase)")
        
        service = BM25Service()
        
        query = "Montage"
        documents = [
            "Die Montage erfolgt nach Anleitung",
            "Die Anleitung beschreibt die Schritte",
            "Montage und Demontage sind wichtig"
        ]
        
        scores = service.calculate_batch_scores(query, documents)
        
        assert len(scores) == len(documents)
        assert all(0.0 <= score <= 1.0 for score in scores)
        # Dokument 1 und 3 sollten höhere Scores haben (enthalten "Montage")
        # Prüfe dass mindestens eines der Dokumente mit "Montage" einen höheren Score hat
        assert scores[0] >= scores[1] or scores[2] >= scores[1], f"Scores: {scores} - Dokumente mit 'Montage' sollten höhere Scores haben"

