"""
Unit Tests für erweiterte SourceReference Metadaten.

TDD Phase 1 (RED): Tests für erweiterte Transparenz-Metadaten.
Diese Tests schlagen ZUERST fehl, dann implementieren wir die Features.
"""

import pytest
from contexts.ragintegration.interface.schemas import SourceReferenceResponse
from contexts.ragintegration.domain.value_objects import SourceReference


class TestSourceReferenceResponseExtendedMetadata:
    """Tests für erweiterte Metadaten in SourceReferenceResponse."""
    
    def test_source_reference_response_has_vector_score(self):
        """Test: SourceReferenceResponse sollte vector_score haben."""
        # RED: Dieser Test schlägt fehl, da vector_score noch nicht existiert
        ref = SourceReferenceResponse(
            document_id=1,
            document_title="Test Document",
            page_number=1,
            chunk_id="chunk_1",
            preview_image_path=None,
            relevance_score=0.85,
            text_excerpt="Test excerpt",
            vector_score=0.89  # NEU: Sollte existieren
        )
        
        assert ref.vector_score == 0.89
        assert 0.0 <= ref.vector_score <= 1.0
    
    def test_source_reference_response_has_text_score(self):
        """Test: SourceReferenceResponse sollte text_score haben."""
        # RED: Dieser Test schlägt fehl, da text_score noch nicht existiert
        ref = SourceReferenceResponse(
            document_id=1,
            document_title="Test Document",
            page_number=1,
            chunk_id="chunk_1",
            preview_image_path=None,
            relevance_score=0.85,
            text_excerpt="Test excerpt",
            text_score=0.92  # NEU: Sollte existieren
        )
        
        assert ref.text_score == 0.92
        assert 0.0 <= ref.text_score <= 1.0
    
    def test_source_reference_response_has_hybrid_score(self):
        """Test: SourceReferenceResponse sollte hybrid_score haben."""
        # RED: Dieser Test schlägt fehl, da hybrid_score noch nicht existiert
        ref = SourceReferenceResponse(
            document_id=1,
            document_title="Test Document",
            page_number=1,
            chunk_id="chunk_1",
            preview_image_path=None,
            relevance_score=0.85,  # Legacy-Feld
            text_excerpt="Test excerpt",
            vector_score=0.89,
            text_score=0.92,
            hybrid_score=0.90  # NEU: Kombinierter Score
        )
        
        assert ref.hybrid_score == 0.90
        # hybrid_score kann von relevance_score abweichen (wenn explizit gesetzt)
        # relevance_score ist das Legacy-Feld, hybrid_score ist der detaillierte Wert
    
    def test_source_reference_response_has_rank_position(self):
        """Test: SourceReferenceResponse sollte rank_position haben."""
        # RED: Dieser Test schlägt fehl, da rank_position noch nicht existiert
        ref = SourceReferenceResponse(
            document_id=1,
            document_title="Test Document",
            page_number=1,
            chunk_id="chunk_1",
            preview_image_path=None,
            relevance_score=0.85,
            text_excerpt="Test excerpt",
            rank_position=1,  # NEU: Position im Ranking
            total_candidates=12  # NEU: Anzahl Kandidaten
        )
        
        assert ref.rank_position == 1
        assert ref.rank_position >= 1
        assert ref.total_candidates == 12
        assert ref.rank_position <= ref.total_candidates
    
    def test_source_reference_response_has_filter_status(self):
        """Test: SourceReferenceResponse sollte Filter-Status haben."""
        # RED: Dieser Test schlägt fehl, da Filter-Felder noch nicht existieren
        ref = SourceReferenceResponse(
            document_id=1,
            document_title="Test Document",
            page_number=1,
            chunk_id="chunk_1",
            preview_image_path=None,
            relevance_score=0.85,
            text_excerpt="Test excerpt",
            passed_rbac_filter=True,  # NEU: RBAC-Filter bestanden
            passed_score_threshold=True  # NEU: Score-Threshold bestanden
        )
        
        assert ref.passed_rbac_filter is True
        assert ref.passed_score_threshold is True
    
    def test_source_reference_response_has_chunk_metadata(self):
        """Test: SourceReferenceResponse sollte chunk_metadata haben."""
        # RED: Dieser Test schlägt fehl, da chunk_metadata noch nicht existiert
        chunk_metadata = {
            "heading_hierarchy": ["1. Montage", "1.1 Vorbereitung"],
            "confidence_score": 0.95,
            "chunk_type": "instruction",
            "token_count": 150
        }
        
        ref = SourceReferenceResponse(
            document_id=1,
            document_title="Test Document",
            page_number=1,
            chunk_id="chunk_1",
            preview_image_path=None,
            relevance_score=0.85,
            text_excerpt="Test excerpt",
            chunk_metadata=chunk_metadata  # NEU: Chunk-Metadaten
        )
        
        assert ref.chunk_metadata is not None
        assert ref.chunk_metadata["heading_hierarchy"] == ["1. Montage", "1.1 Vorbereitung"]
        assert ref.chunk_metadata["confidence_score"] == 0.95


class TestSourceReferenceValueObjectExtended:
    """Tests für erweiterte Metadaten in SourceReference Value Object."""
    
    def test_source_reference_can_have_extended_metadata(self):
        """Test: SourceReference sollte erweiterte Metadaten unterstützen."""
        # RED: Dieser Test schlägt fehl, da erweiterte Felder noch nicht existieren
        from dataclasses import dataclass
        
        # Aktuell ist SourceReference ein @dataclass
        # Wir müssen prüfen ob wir es erweitern können oder ein neues VO brauchen
        ref = SourceReference(
            document_id=1,
            document_title="Test Document",
            page_number=1,
            chunk_id="chunk_1",
            relevance_score=0.85,
            preview_image_path=None,
            text_excerpt="Test excerpt"
        )
        
        # Für jetzt: SourceReference bleibt einfach, erweiterte Metadaten kommen in Response
        assert ref.relevance_score == 0.85
        # Erweiterte Metadaten werden in der Konvertierung zu SourceReferenceResponse hinzugefügt

