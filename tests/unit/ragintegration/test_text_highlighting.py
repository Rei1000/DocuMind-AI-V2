"""
Unit Tests für Text-Highlighting-Logik.

TDD Phase 1 (RED): Tests für Text-Highlighting (Query-Wörter im Chunk-Text hervorheben).
Diese Tests schlagen ZUERST fehl, dann implementieren wir die Features.
"""

import pytest


class TestTextHighlighting:
    """Tests für Text-Highlighting-Funktionalität."""
    
    def test_highlight_query_words_in_chunk_text(self):
        """Test: Query-Wörter sollten im Chunk-Text hervorgehoben werden."""
        # RED: Diese Funktion existiert noch nicht
        from contexts.ragintegration.application.services import highlight_query_words
        
        chunk_text = "Die Montage erfolgt in drei Schritten. Zuerst die Vorbereitung, dann die Montage selbst."
        query = "Montage Vorbereitung"
        
        highlighted = highlight_query_words(chunk_text, query)
        
        # Prüfe dass Query-Wörter hervorgehoben sind
        assert "Montage" in highlighted
        assert "Vorbereitung" in highlighted
        # Prüfe dass Highlighting-Markup vorhanden ist (z.B. <mark> tags oder ähnlich)
        assert "<mark" in highlighted or "highlight" in highlighted.lower()
    
    def test_highlight_case_insensitive(self):
        """Test: Highlighting sollte case-insensitive sein."""
        from contexts.ragintegration.application.services import highlight_query_words
        
        chunk_text = "Die MONTAGE erfolgt in drei Schritten."
        query = "montage"
        
        highlighted = highlight_query_words(chunk_text, query)
        
        # "MONTAGE" sollte auch hervorgehoben werden (case-insensitive)
        assert "MONTAGE" in highlighted or "montage" in highlighted.lower()
    
    def test_highlight_partial_word_matches(self):
        """Test: Highlighting sollte auch Teilwort-Matches finden."""
        from contexts.ragintegration.application.services import highlight_query_words
        
        chunk_text = "Die Montageanleitung beschreibt die Montage."
        query = "Montage"
        
        highlighted = highlight_query_words(chunk_text, query)
        
        # "Montage" in "Montageanleitung" sollte auch hervorgehoben werden
        assert "Montage" in highlighted
    
    def test_highlight_multiple_query_words(self):
        """Test: Mehrere Query-Wörter sollten alle hervorgehoben werden."""
        from contexts.ragintegration.application.services import highlight_query_words
        
        chunk_text = "Die Montage erfolgt in drei Schritten. Zuerst die Vorbereitung, dann die Montage selbst."
        query = "Montage Vorbereitung Schritten"
        
        highlighted = highlight_query_words(chunk_text, query)
        
        # Alle drei Wörter sollten hervorgehoben sein
        assert "Montage" in highlighted
        assert "Vorbereitung" in highlighted
        assert "Schritten" in highlighted
    
    def test_highlight_empty_query_returns_original(self):
        """Test: Leere Query sollte originalen Text zurückgeben."""
        from contexts.ragintegration.application.services import highlight_query_words
        
        chunk_text = "Die Montage erfolgt in drei Schritten."
        query = ""
        
        highlighted = highlight_query_words(chunk_text, query)
        
        assert highlighted == chunk_text
    
    def test_highlight_handles_special_characters(self):
        """Test: Highlighting sollte Sonderzeichen korrekt behandeln."""
        from contexts.ragintegration.application.services import highlight_query_words
        
        chunk_text = "Die Montage (Schritt 1) erfolgt mit Werkzeug A."
        query = "Montage (Schritt 1)"
        
        highlighted = highlight_query_words(chunk_text, query)
        
        # Sonderzeichen sollten korrekt behandelt werden
        assert "Montage" in highlighted
        assert "Schritt" in highlighted


class TestTFIDFBasedHighlighting:
    """Tests für TF-IDF-basierte Feature-Importance."""
    
    def test_calculate_tfidf_scores_for_chunk(self):
        """Test: TF-IDF-Scores sollten für Chunk-Text berechnet werden."""
        # RED: Diese Funktion existiert noch nicht
        from contexts.ragintegration.application.services import calculate_tfidf_scores
        
        chunk_text = "Die Montage erfolgt in drei Schritten. Zuerst die Vorbereitung, dann die Montage selbst."
        query = "Montage Vorbereitung"
        
        scores = calculate_tfidf_scores(chunk_text, query)
        
        # Scores sollten ein Dict mit Wörtern als Keys sein (lowercase)
        assert isinstance(scores, dict)
        assert "montage" in scores or "Montage" in scores
        assert "vorbereitung" in scores or "Vorbereitung" in scores
        # Prüfe dass Scores > 0 sind (case-insensitive)
        montage_score = scores.get("montage") or scores.get("Montage", 0)
        vorbereitung_score = scores.get("vorbereitung") or scores.get("Vorbereitung", 0)
        assert montage_score > 0
        assert vorbereitung_score > 0
    
    def test_tfidf_scores_ordered_by_importance(self):
        """Test: TF-IDF-Scores sollten nach Wichtigkeit sortiert sein."""
        from contexts.ragintegration.application.services import calculate_tfidf_scores
        
        chunk_text = "Die Montage erfolgt in drei Schritten. Zuerst die Vorbereitung, dann die Montage selbst."
        query = "Montage Vorbereitung"
        
        scores = calculate_tfidf_scores(chunk_text, query)
        
        # Top-Wörter sollten die höchsten Scores haben
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_word = sorted_scores[0][0]
        
        # "Montage" sollte wahrscheinlich höchster Score sein (kommt 2x vor)
        # TF-IDF gibt lowercase zurück
        assert top_word.lower() in ["montage", "vorbereitung"]

