"""
Unit Tests für RAG Integration Value Objects.

TDD Approach: Diese Tests werden ZUERST geschrieben, dann die Value Objects implementiert.
"""

import pytest
from contexts.ragintegration.domain.value_objects import (
    EmbeddingVector,
    ChunkMetadata,
    SourceReference,
    SearchQuery
)


class TestEmbeddingVector:
    """Tests für EmbeddingVector Value Object."""
    
    def test_create_valid_embedding_vector(self):
        """Test: Erstelle gültigen EmbeddingVector."""
        vector_data = [0.1, 0.2, 0.3] * 512  # 1536 dimensions
        embedding = EmbeddingVector(vector_data)
        
        assert len(embedding.vector) == 1536
        assert embedding.vector[0] == 0.1
        assert embedding.vector[1] == 0.2
        assert embedding.vector[2] == 0.3
    
    def test_embedding_vector_requires_correct_dimensions(self):
        """Test: EmbeddingVector muss 1536 Dimensionen haben."""
        with pytest.raises(ValueError, match="Embedding vector must have exactly 1536 dimensions"):
            EmbeddingVector([0.1, 0.2])  # Nur 2 Dimensionen
    
    def test_embedding_vector_immutable(self):
        """Test: EmbeddingVector ist unveränderlich."""
        vector_data = [0.1, 0.2, 0.3] * 512
        embedding = EmbeddingVector(vector_data)
        
        # Versuche Änderung
        with pytest.raises(TypeError):
            embedding.vector[0] = 0.5
    
    def test_embedding_vector_get_dimensions(self):
        """Test: Returniere Anzahl Dimensionen."""
        vector_data = [0.1, 0.2, 0.3] * 512
        embedding = EmbeddingVector(vector_data)
        
        assert embedding.get_dimensions() == 1536
    
    def test_embedding_vector_get_preview(self):
        """Test: Returniere Preview der ersten 10 Dimensionen."""
        vector_data = [0.1, 0.2, 0.3] * 512
        embedding = EmbeddingVector(vector_data)
        
        preview = embedding.get_preview()
        assert len(preview) == 10
        assert preview[0] == 0.1
        assert preview[1] == 0.2
        assert preview[2] == 0.3


class TestChunkMetadata:
    """Tests für ChunkMetadata Value Object."""
    
    def test_create_valid_chunk_metadata(self):
        """Test: Erstelle gültige ChunkMetadata."""
        metadata = ChunkMetadata(
            page_numbers=[1, 2],
            heading_hierarchy=["1. Arbeitsanweisung", "1.1 Vorbereitung"],
            document_type_id=1,
            confidence=0.95,
            chunk_type="text",
            token_count=150
        )
        
        assert metadata.page_numbers == [1, 2]
        assert len(metadata.heading_hierarchy) == 2
        assert metadata.document_type_id == 1
        assert metadata.confidence == 0.95
        assert metadata.chunk_type == "text"
        assert metadata.token_count == 150
    
    def test_chunk_metadata_requires_positive_document_type_id(self):
        """Test: document_type_id muss positiv sein."""
        with pytest.raises(ValueError, match="document_type_id must be positive"):
            ChunkMetadata(
                page_numbers=[1],
                heading_hierarchy=[],
                document_type_id=-1,
                confidence=0.95,
                chunk_type="text",
                token_count=100
            )
    
    def test_chunk_metadata_confidence_range(self):
        """Test: confidence muss zwischen 0 und 1 liegen."""
        with pytest.raises(ValueError, match="confidence must be between 0 and 1"):
            ChunkMetadata(
                page_numbers=[1],
                heading_hierarchy=[],
                document_type_id=1,
                confidence=1.5,
                chunk_type="text",
                token_count=100
            )
    
    def test_chunk_metadata_valid_chunk_type(self):
        """Test: chunk_type muss gültig sein."""
        with pytest.raises(ValueError, match="chunk_type must be one of"):
            ChunkMetadata(
                page_numbers=[1],
                heading_hierarchy=[],
                document_type_id=1,
                confidence=0.95,
                chunk_type="invalid",
                token_count=100
            )
    
    def test_chunk_metadata_requires_positive_token_count(self):
        """Test: token_count muss positiv sein."""
        with pytest.raises(ValueError, match="token_count must be positive"):
            ChunkMetadata(
                page_numbers=[1],
                heading_hierarchy=[],
                document_type_id=1,
                confidence=0.95,
                chunk_type="text",
                token_count=0
            )
    
    def test_chunk_metadata_get_page_count(self):
        """Test: Returniere Anzahl Seiten."""
        metadata = ChunkMetadata(
            page_numbers=[1, 2, 3],
            heading_hierarchy=[],
            document_type_id=1,
            confidence=0.95,
            chunk_type="text",
            token_count=100
        )
        
        assert metadata.get_page_count() == 3
    
    def test_chunk_metadata_is_multi_page(self):
        """Test: Prüfe ob Chunk über mehrere Seiten geht."""
        metadata_single = ChunkMetadata(
            page_numbers=[1],
            heading_hierarchy=[],
            document_type_id=1,
            confidence=0.95,
            chunk_type="text",
            token_count=100
        )
        
        metadata_multi = ChunkMetadata(
            page_numbers=[1, 2],
            heading_hierarchy=[],
            document_type_id=1,
            confidence=0.95,
            chunk_type="text",
            token_count=100
        )
        
        assert metadata_single.is_multi_page() is False
        assert metadata_multi.is_multi_page() is True
    
    def test_chunk_metadata_get_heading_path(self):
        """Test: Returniere Heading-Pfad als String."""
        metadata = ChunkMetadata(
            page_numbers=[1],
            heading_hierarchy=["1. Arbeitsanweisung", "1.1 Vorbereitung"],
            document_type_id=1,
            confidence=0.95,
            chunk_type="text",
            token_count=100
        )
        
        assert metadata.get_heading_path() == "1. Arbeitsanweisung > 1.1 Vorbereitung"


class TestSourceReference:
    """Tests für SourceReference Value Object."""
    
    def test_create_valid_source_reference(self):
        """Test: Erstelle gültige SourceReference."""
        source = SourceReference(
            document_id=42,
            document_title="SOP-001 Montage Anleitung",
            page_number=3,
            chunk_id="doc_42_chunk_5",
            preview_image_path="uploads/2025/01/preview.jpg",
            relevance_score=0.95,
            text_excerpt="Wichtige Sicherheitshinweise..."
        )
        
        assert source.document_id == 42
        assert source.document_title == "SOP-001 Montage Anleitung"
        assert source.page_number == 3
        assert source.chunk_id == "doc_42_chunk_5"
        assert source.preview_image_path == "uploads/2025/01/preview.jpg"
        assert source.relevance_score == 0.95
        assert len(source.text_excerpt) > 0
    
    def test_source_reference_requires_positive_document_id(self):
        """Test: document_id muss positiv sein."""
        with pytest.raises(ValueError, match="document_id must be positive"):
            SourceReference(
                document_id=-1,
                document_title="Test",
                page_number=1,
                chunk_id="chunk_1",
                preview_image_path="preview.jpg",
                relevance_score=0.95,
                text_excerpt="Test"
            )
    
    def test_source_reference_requires_positive_page_number(self):
        """Test: page_number muss positiv sein."""
        with pytest.raises(ValueError, match="page_number must be positive"):
            SourceReference(
                document_id=42,
                document_title="Test",
                page_number=0,
                chunk_id="chunk_1",
                preview_image_path="preview.jpg",
                relevance_score=0.95,
                text_excerpt="Test"
            )
    
    def test_source_reference_relevance_score_range(self):
        """Test: relevance_score muss zwischen 0 und 1 liegen."""
        with pytest.raises(ValueError, match="relevance_score must be between 0 and 1"):
            SourceReference(
                document_id=42,
                document_title="Test",
                page_number=1,
                chunk_id="chunk_1",
                preview_image_path="preview.jpg",
                relevance_score=1.5,
                text_excerpt="Test"
            )
    
    def test_source_reference_text_excerpt_not_empty(self):
        """Test: text_excerpt darf nicht leer sein."""
        with pytest.raises(ValueError, match="text_excerpt cannot be empty"):
            SourceReference(
                document_id=42,
                document_title="Test",
                page_number=1,
                chunk_id="chunk_1",
                preview_image_path="preview.jpg",
                relevance_score=0.95,
                text_excerpt=""
            )
    
    def test_source_reference_get_confidence_level(self):
        """Test: Returniere Confidence Level."""
        source_high = SourceReference(
            document_id=42,
            document_title="Test",
            page_number=1,
            chunk_id="chunk_1",
            preview_image_path="preview.jpg",
            relevance_score=0.95,
            text_excerpt="Test"
        )
        
        source_medium = SourceReference(
            document_id=42,
            document_title="Test",
            page_number=1,
            chunk_id="chunk_1",
            preview_image_path="preview.jpg",
            relevance_score=0.75,
            text_excerpt="Test"
        )
        
        source_low = SourceReference(
            document_id=42,
            document_title="Test",
            page_number=1,
            chunk_id="chunk_1",
            preview_image_path="preview.jpg",
            relevance_score=0.60,
            text_excerpt="Test"
        )
        
        assert source_high.get_confidence_level() == "high"
        assert source_medium.get_confidence_level() == "medium"
        assert source_low.get_confidence_level() == "low"
    
    def test_source_reference_get_preview_url(self):
        """Test: Returniere Preview URL."""
        source = SourceReference(
            document_id=42,
            document_title="Test",
            page_number=1,
            chunk_id="chunk_1",
            preview_image_path="uploads/2025/01/preview.jpg",
            relevance_score=0.95,
            text_excerpt="Test"
        )
        
        assert source.get_preview_url() == "/data/uploads/uploads/2025/01/preview.jpg"


class TestSearchQuery:
    """Tests für SearchQuery Value Object."""
    
    def test_create_valid_search_query(self):
        """Test: Erstelle gültige SearchQuery."""
        query = SearchQuery(
            text="Welche Sicherheitshinweise gibt es?",
            filters={
                "document_type_ids": [1, 2],
                "interest_group_ids": [3, 4]
            },
            top_k=10,
            min_relevance=0.7
        )
        
        assert query.text == "Welche Sicherheitshinweise gibt es?"
        assert query.filters["document_type_ids"] == [1, 2]
        assert query.filters["interest_group_ids"] == [3, 4]
        assert query.top_k == 10
        assert query.min_relevance == 0.7
    
    def test_search_query_text_not_empty(self):
        """Test: text darf nicht leer sein."""
        with pytest.raises(ValueError, match="text cannot be empty"):
            SearchQuery(
                text="",
                filters={},
                top_k=10,
                min_relevance=0.7
            )
    
    def test_search_query_requires_positive_top_k(self):
        """Test: top_k muss positiv sein."""
        with pytest.raises(ValueError, match="top_k must be positive"):
            SearchQuery(
                text="Test",
                filters={},
                top_k=0,
                min_relevance=0.7
            )
    
    def test_search_query_relevance_range(self):
        """Test: min_relevance muss zwischen 0 und 1 liegen."""
        with pytest.raises(ValueError, match="min_relevance must be between 0 and 1"):
            SearchQuery(
                text="Test",
                filters={},
                top_k=10,
                min_relevance=1.5
            )
    
    def test_search_query_get_normalized_text(self):
        """Test: Returniere normalisierten Text."""
        query = SearchQuery(
            text="  Welche Sicherheitshinweise gibt es?  ",
            filters={},
            top_k=10,
            min_relevance=0.7
        )
        
        assert query.get_normalized_text() == "welche sicherheitshinweise gibt es?"
    
    def test_search_query_has_filters(self):
        """Test: Prüfe ob Filter vorhanden sind."""
        query_with_filters = SearchQuery(
            text="Test",
            filters={"document_type_ids": [1]},
            top_k=10,
            min_relevance=0.7
        )
        
        query_without_filters = SearchQuery(
            text="Test",
            filters={},
            top_k=10,
            min_relevance=0.7
        )
        
        assert query_with_filters.has_filters() is True
        assert query_without_filters.has_filters() is False
    
    def test_search_query_get_filter_values(self):
        """Test: Returniere Filter-Werte."""
        query = SearchQuery(
            text="Test",
            filters={
                "document_type_ids": [1, 2],
                "interest_group_ids": [3, 4]
            },
            top_k=10,
            min_relevance=0.7
        )
        
        doc_types = query.get_filter_values("document_type_ids")
        interest_groups = query.get_filter_values("interest_group_ids")
        
        assert doc_types == [1, 2]
        assert interest_groups == [3, 4]
