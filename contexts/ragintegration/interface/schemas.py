"""
Interface Layer: Pydantic Schemas für RAG Integration

Definiert die Request/Response Schemas für die FastAPI Endpoints.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class DocumentStatus(str, Enum):
    """Status eines indexierten Dokuments."""
    INDEXED = "indexed"
    PROCESSING = "processing"
    FAILED = "failed"


class ChunkType(str, Enum):
    """Typ eines Dokument-Chunks."""
    TEXT = "text"
    VISION_EXTRACTED = "vision_extracted"
    PAGE_BOUNDARY = "page_boundary"
    PLAIN_TEXT = "plain_text"


class MessageRole(str, Enum):
    """Rolle einer Chat-Nachricht."""
    USER = "user"
    ASSISTANT = "assistant"


# Request Schemas
class IndexDocumentRequest(BaseModel):
    """Request Schema für Dokument-Indexierung."""
    upload_document_id: int = Field(..., description="ID des Upload-Dokuments")
    force_reindex: bool = Field(False, description="Erzwinge Re-Indexierung")
    chunking_strategy: Optional[str] = Field(None, description="Optional: Chunking-Strategie (openai_1536/gemini_768/local_384). Falls nicht angegeben, wird automatisch die beste verfügbare Strategie gewählt.")


class AskQuestionRequest(BaseModel):  # type: ignore
    """Request Schema für Fragen an das RAG System."""
    question: str = Field(..., min_length=3, max_length=1000, description="Die Frage")
    session_id: Optional[int] = Field(None, description="Chat-Session ID")
    model: str = Field("gpt-4o-mini", description="AI Model für Antwort")
    top_k: int = Field(5, ge=1, le=20, description="Anzahl der relevanten Chunks")
    score_threshold: float = Field(0.01, ge=0.0, le=0.02, description="Mindest-Relevanz-Score (0.0-0.02 für OpenAI Embeddings)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Suchfilter")
    use_hybrid_search: bool = Field(True, description="Verwende Hybrid Search")
    use_multi_query: bool = Field(False, description="Verwende MultiQuery für Query-Expansion (erstellt automatisch Varianten)")
    use_ml_reranking: Optional[bool] = Field(False, description="Verwende ML Re-Ranking (deprecated - use use_ml_ranking)")
    use_ml_ranking: Optional[bool] = Field(False, description="Verwende Learning-to-Rank ML-Modell (v2.7.0)")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="AI Temperature (0.0-2.0, optional)")  # NEU v2.10.3
    max_tokens: Optional[int] = Field(None, ge=1, le=8000, description="Max Tokens (1-8000, optional)")  # NEU v2.10.3
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top P (0.0-1.0, optional)")  # NEU v2.10.3


class CreateSessionRequest(BaseModel):
    """Request Schema für neue Chat-Session."""
    user_id: int = Field(..., description="User ID")
    session_name: str = Field(..., min_length=1, max_length=200, description="Name der Session")


class SearchDocumentsRequest(BaseModel):
    """Request Schema für Dokument-Suche."""
    query: str = Field(..., min_length=3, max_length=1000, description="Suchanfrage")
    top_k: int = Field(10, ge=1, le=50, description="Anzahl der Ergebnisse")
    score_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Mindest-Relevanz-Score")
    document_type: Optional[str] = Field(None, description="Filter nach Dokumenttyp")
    page_numbers: Optional[List[int]] = Field(None, description="Filter nach Seitenzahlen")
    use_hybrid_search: bool = Field(True, description="Verwende Hybrid Search")


class ReindexDocumentRequest(BaseModel):
    """Request Schema für Dokument-Re-Indexierung."""
    document_id: int = Field(..., description="ID des indexierten Dokuments")
    force_reindex: bool = Field(True, description="Erzwinge Re-Indexierung")


# Response Schemas
class SourceReferenceResponse(BaseModel):
    """Response Schema für Quellen-Referenz.
    
    Erweitert um Transparenz-Metadaten für bessere Nachvollziehbarkeit:
    - Score-Aufschlüsselung (Vector-Score vs. Text-Score)
    - Ranking-Informationen
    - Filter-Status
    - Chunk-Metadaten
    """
    document_id: int
    document_title: str
    page_number: int
    chunk_id: Union[int, str]  # WICHTIG: chunk_id kann String (z.B. "doc_14_page_1_text") oder int sein
    preview_image_path: Optional[str]
    relevance_score: float  # Legacy-Feld, entspricht hybrid_score
    text_excerpt: str
    
    # NEU: Detaillierte Score-Informationen (Phase 1: RAG Transparenz)
    vector_score: Optional[float] = Field(None, description="Reine Vektor-Ähnlichkeit (0-1)")
    text_score: Optional[float] = Field(None, description="Text-Matching-Score (0-1)")
    hybrid_score: Optional[float] = Field(None, description="Kombinierter Score (0-1), entspricht relevance_score")
    ml_score: Optional[float] = Field(None, description="ML-Score aus Learning-to-Rank Modell (v2.7.0)")
    final_score: Optional[float] = Field(None, description="Final-Score (kombiniert Hybrid + ML, v2.7.0)")
    
    # NEU: Ranking-Informationen
    rank_position: Optional[int] = Field(None, ge=1, description="Position im Ranking (1 = bestes Ergebnis)")
    total_candidates: Optional[int] = Field(None, ge=1, description="Anzahl der gefundenen Kandidaten vor Filtering")
    
    # NEU: Filter-Informationen
    passed_rbac_filter: Optional[bool] = Field(None, description="Wurde durch RBAC-Filter durchgelassen?")
    passed_score_threshold: Optional[bool] = Field(None, description="Erfüllt score_threshold?")
    
    # NEU: Chunk-Metadaten
    chunk_metadata: Optional[Dict[str, Any]] = Field(None, description="Chunk-Metadaten (Heading-Hierarchy, Confidence-Score, etc.)")
    
    # NEU: Query-Text für Text-Highlighting (Phase 3)
    query_text: Optional[str] = Field(None, description="Die ursprüngliche Query, die zu diesem Source Reference führte (für Text-Highlighting)")
    
    @validator('relevance_score')
    def validate_relevance_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Relevance score must be between 0.0 and 1.0')
        return v
    
    @validator('vector_score', 'text_score', 'hybrid_score')
    def validate_score_range(cls, v):
        """Validiere dass Scores zwischen 0 und 1 liegen."""
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError('Score must be between 0.0 and 1.0')
        return v


class StructuredDataResponse(BaseModel):
    """Response Schema für strukturierte Daten."""
    data_type: str
    content: Dict[str, Any]
    confidence: float = Field(..., ge=0.0, le=1.0)


class ChatMessageResponse(BaseModel):
    """Response Schema für Chat-Nachricht."""
    id: int
    role: MessageRole
    content: str
    source_references: Optional[List[SourceReferenceResponse]]
    structured_data: Optional[List[StructuredDataResponse]]
    ai_model_used: Optional[str] = None  # AI Model das für diese Nachricht verwendet wurde
    metadata: Optional[Dict[str, Any]] = None  # Metadaten für Transparency Layer (processing_time_ms, tokens_used, query_params)
    created_at: datetime


class ChatSessionResponse(BaseModel):
    """Response Schema für Chat-Session."""
    id: int
    session_name: str
    created_at: datetime
    last_activity: Optional[datetime] = None
    message_count: int


class DocumentChunkResponse(BaseModel):
    """Response Schema für Dokument-Chunk."""
    id: int
    chunk_text: str
    chunk_index: int
    page_numbers: List[int]
    heading_hierarchy: List[str]
    document_type: str
    confidence_score: float
    chunk_type: ChunkType
    token_count: int
    created_at: datetime


class IndexedDocumentResponse(BaseModel):
    """Response Schema für indexiertes Dokument."""
    id: int
    upload_document_id: int
    document_title: str
    document_type: str
    status: DocumentStatus
    indexed_at: datetime
    total_chunks: int
    last_updated: datetime


class SearchResultResponse(BaseModel):
    """Response Schema für Suchergebnis."""
    chunk_id: int
    score: float
    chunk_text: str
    source_reference: SourceReferenceResponse
    metadata: Dict[str, Any]


class AskQuestionResponse(BaseModel):
    """Response Schema für RAG-Antwort."""
    answer: str
    source_references: List[SourceReferenceResponse]
    structured_data: Optional[List[StructuredDataResponse]]
    suggested_questions: Optional[List[str]]
    search_results: List[SearchResultResponse]
    model_used: str
    processing_time_ms: int
    tokens_used: Optional[int]
    message_id: Optional[int] = None  # NEU: Message-ID für Prompt Viewer
    analytics: Optional[Dict[str, Any]] = None  # NEU v2.7.0: Analytics-Block für Dashboard


class SearchDocumentsResponse(BaseModel):
    """Response Schema für Dokument-Suche."""
    results: List[SearchResultResponse]
    total_results: int
    query: str
    filters_applied: Dict[str, Any]
    search_time_ms: int


class IndexDocumentResponse(BaseModel):
    """Response Schema für Dokument-Indexierung."""
    success: bool
    document: IndexedDocumentResponse
    chunks_created: int
    processing_time_ms: int
    message: str


class ReindexDocumentResponse(BaseModel):
    """Response Schema für Dokument-Re-Indexierung."""
    success: bool
    document: IndexedDocumentResponse
    old_chunks_deleted: int
    new_chunks_created: int
    processing_time_ms: int
    message: str


class DocumentIndexStatusResponse(BaseModel):
    """Response Schema für Indexierungs-Status-Prüfung."""
    is_indexed: bool = Field(..., description="Ist das Dokument indexiert?")
    indexed_document_id: Optional[int] = Field(None, description="ID des indexierten Dokuments (falls indexiert)")
    indexed_at: Optional[datetime] = Field(None, description="Zeitstempel der Indexierung (falls indexiert)")
    total_chunks: Optional[int] = Field(None, description="Anzahl Chunks (falls indexiert)")


class ChatHistoryResponse(BaseModel):
    """Response Schema für Chat-Historie."""
    session: ChatSessionResponse
    messages: List[ChatMessageResponse]
    total_messages: int


class SystemInfoResponse(BaseModel):
    """Response Schema für System-Informationen."""
    vector_store: Dict[str, Any]
    embedding_service: Dict[str, Any]
    repositories: Dict[str, str]
    services: Dict[str, str]
    total_documents: int
    total_chunks: int


class HealthCheckResponse(BaseModel):
    """Response Schema für Health Check."""
    overall_status: str
    services: Dict[str, str]
    errors: List[str]
    timestamp: datetime


class UsageStatisticsResponse(BaseModel):
    """Response Schema für Nutzungsstatistiken."""
    documents: Dict[str, Any]
    chunks: Dict[str, Any]
    vector_store: Dict[str, Any]
    last_updated: datetime


# Error Schemas
class ErrorResponse(BaseModel):
    """Response Schema für Fehler."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationErrorResponse(BaseModel):
    """Response Schema für Validierungsfehler."""
    error: str = "Validation Error"
    details: List[Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Utility Schemas
class PaginationParams(BaseModel):
    """Schema für Pagination-Parameter."""
    page: int = Field(1, ge=1, description="Seitennummer")
    size: int = Field(10, ge=1, le=100, description="Anzahl pro Seite")


class PaginatedResponse(BaseModel):
    """Schema für paginierte Antworten."""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    
    @validator('pages', always=True)
    def calculate_pages(cls, v, values):
        total = values.get('total', 0)
        size = values.get('size', 10)
        return (total + size - 1) // size if total > 0 else 0


# Filter Schemas
class DocumentFilter(BaseModel):
    """Schema für Dokument-Filter."""
    status: Optional[DocumentStatus] = None
    document_type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class ChunkFilter(BaseModel):
    """Schema für Chunk-Filter."""
    document_type: Optional[str] = None
    chunk_type: Optional[ChunkType] = None
    page_numbers: Optional[List[int]] = None
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class SessionFilter(BaseModel):
    """Schema für Session-Filter."""
    user_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_message_count: Optional[int] = Field(None, ge=0)


# ============================================================================
# CHUNK PREVIEW SCHEMAS (PHASE 2.1)
# ============================================================================

class ChunkMetadataResponse(BaseModel):
    """Response Schema für Chunk-Metadaten."""
    page_numbers: List[int] = Field(..., description="Seitennummern dieses Chunks")
    heading_hierarchy: List[str] = Field(default_factory=list, description="Überschriften-Hierarchie")
    chunk_type: str = Field(..., description="Chunk-Typ (z.B. 'section', 'metadata')")
    token_count: Optional[int] = Field(None, description="Anzahl Tokens")
    sentence_count: Optional[int] = Field(None, description="Anzahl Sätze")
    has_overlap: bool = Field(False, description="Hat Overlap mit anderen Chunks")
    overlap_sentence_count: int = Field(0, description="Anzahl Overlap-Sätze")


class ChunkPreviewResponse(BaseModel):
    """Response Schema für einzelnen Chunk (Vorschau)."""
    id: int = Field(..., description="Chunk ID")
    chunk_id: str = Field(..., description="Eindeutige Chunk-ID")
    chunk_text: str = Field(..., description="Chunk-Text (kann gekürzt sein für Vorschau)")
    metadata: ChunkMetadataResponse = Field(..., description="Chunk-Metadaten")
    indexed_document_id: int = Field(..., description="ID des indexierten Dokuments")
    created_at: datetime = Field(..., description="Erstellungszeitpunkt")


class ChunksListResponse(BaseModel):
    """Response Schema für Liste von Chunks."""
    document_id: int = Field(..., description="Upload Document ID")
    indexed_document_id: Optional[int] = Field(None, description="Indexed Document ID (falls indexiert)")
    total_chunks: int = Field(..., description="Gesamtanzahl Chunks")
    chunks: List[ChunkPreviewResponse] = Field(..., description="Liste der Chunks")


# ============================================================================
# CHUNK EDITOR REQUEST SCHEMAS (PHASE 2.2)
# ============================================================================

class EditChunkRequest(BaseModel):
    """Request Schema für Chunk-Bearbeitung."""
    new_text: str = Field(..., min_length=1, description="Neuer Chunk-Text")


class SplitChunkRequest(BaseModel):
    """Request Schema für Chunk-Split."""
    split_position: int = Field(..., ge=0, description="Split-Position (Character-Index)")
    overlap_sentences: int = Field(0, ge=0, le=10, description="Anzahl Overlap-Sätze zwischen den beiden Chunks (0-10, Standard: 0)")


class MergeChunksRequest(BaseModel):
    """Request Schema für Chunk-Merge."""
    chunk_ids: List[int] = Field(..., min_items=2, description="Liste von Chunk IDs (mindestens 2)")


# ============================================================================
# CHUNKING STRATEGY SELECTOR SCHEMAS (PHASE 2.3)
# ============================================================================

class ChunkingStrategyOption(BaseModel):
    """Schema für eine Chunking-Strategie-Option."""
    id: str = Field(..., description="Eindeutige Strategie-ID")
    name: str = Field(..., description="Anzeigename")
    description: str = Field(..., description="Beschreibung der Strategie")
    embedding_provider: str = Field(..., description="Embedding-Provider (openai/gemini/local)")
    embedding_dimensions: int = Field(..., description="Anzahl Embedding-Dimensionen")
    recommended_for: List[str] = Field(default_factory=list, description="Empfohlen für Dokumenttypen")
    is_default: bool = Field(False, description="Ist Standard-Strategie")


class ChunkingStrategiesResponse(BaseModel):
    """Response Schema für verfügbare Chunking-Strategien."""
    strategies: List[ChunkingStrategyOption] = Field(..., description="Liste verfügbarer Strategien")
    default_strategy: str = Field(..., description="ID der Standard-Strategie")
    document_type_suggestion: Optional[str] = Field(None, description="Empfohlene Strategie für Dokumenttyp")


# ============================================================================
# RAG CHAT PROMPT VIEWER SCHEMAS (PHASE 3.1)
# ============================================================================

class PromptViewerResponse(BaseModel):
    """Response Schema für Prompt-Viewer mit vollständiger Traceability."""
    message_id: int = Field(..., description="Chat Message ID")
    question: str = Field(..., description="User-Frage")
    prompt_text: Optional[str] = Field(None, description="Vollständiger Prompt der verwendet wurde (kann None sein wenn INVALID)")
    prompt_state: str = Field(..., description="State des Prompts: 'valid' | 'invalid'")
    context_chunks: List[Dict[str, Any]] = Field(default_factory=list, description="Verwendete Chunks (vereinfacht)")
    document_type: Optional[str] = Field(None, description="Dokumenttyp (falls erkannt)")
    model_used: str = Field(..., description="Verwendetes AI-Modell")
    tokens_used: Optional[int] = Field(None, description="Anzahl verwendeter Tokens")
    # Erweiterte Metadaten für Traceability
    prompt_type: Optional[str] = Field(None, description="Prompt-Typ: custom | standard | generic")
    document_type_selected: Optional[str] = Field(None, description="User-Intent (aus Filter)")
    document_type_effective: Optional[str] = Field(None, description="Tatsächlich verwendet")


# ============================================================================
# RAG FEEDBACK SCHEMAS (PHASE 4.1)
# ============================================================================

class SubmitFeedbackRequest(BaseModel):
    """Request Schema für Feedback-Abgabe."""
    chat_message_id: int = Field(..., description="Chat Message ID (Assistant-Message)")
    rating: str = Field(..., description="Bewertung: 'positive', 'negative', 'neutral'")
    comment: Optional[str] = Field(None, max_length=2000, description="Optionaler Kommentar (max 2000 Zeichen)")


class FeedbackResponse(BaseModel):
    """Response Schema für Feedback."""
    id: int = Field(..., description="Feedback ID")
    chat_message_id: int = Field(..., description="Chat Message ID")
    user_id: int = Field(..., description="User ID")
    rating: str = Field(..., description="Bewertung")
    comment: Optional[str] = Field(None, description="Kommentar")
    submitted_at: datetime = Field(..., description="Zeitstempel")


class FeedbackStatisticsResponse(BaseModel):
    """Response Schema für Feedback-Statistiken."""
    total: int = Field(..., description="Gesamtanzahl Feedbacks")
    positive: int = Field(..., description="Anzahl positive Feedbacks")
    negative: int = Field(..., description="Anzahl negative Feedbacks")
    neutral: int = Field(..., description="Anzahl neutrale Feedbacks")
    average_rating: float = Field(..., description="Durchschnittliches Rating (0.0-1.0)")


# ============================================================================
# RAG ANALYTICS SCHEMAS (PHASE 4.2)
# ============================================================================

class QueryStatisticsResponse(BaseModel):
    """Response Schema für Query-Statistiken."""
    total: int = Field(..., description="Gesamtanzahl Queries")
    average_duration_ms: float = Field(..., description="Durchschnittliche Query-Dauer in ms")
    success_rate: float = Field(..., description="Erfolgsrate (0.0-1.0)")


class ChunkingStatisticsResponse(BaseModel):
    """Response Schema für Chunking-Statistiken."""
    started: int = Field(..., description="Anzahl gestarteter Chunking-Prozesse")
    completed: int = Field(..., description="Anzahl abgeschlossener Chunking-Prozesse")
    failed: int = Field(..., description="Anzahl fehlgeschlagener Chunking-Prozesse")
    success_rate: float = Field(..., description="Erfolgsrate (0.0-100.0)")


class IndexingStatisticsResponse(BaseModel):
    """Response Schema für Indexing-Statistiken."""
    started: int = Field(..., description="Anzahl gestarteter Indexierungs-Prozesse")
    completed: int = Field(..., description="Anzahl abgeschlossener Indexierungs-Prozesse")
    failed: int = Field(..., description="Anzahl fehlgeschlagener Indexierungs-Prozesse")
    success_rate: float = Field(..., description="Erfolgsrate (0.0-100.0)")


class MessageStatisticsResponse(BaseModel):
    """Response Schema für Message-Statistiken."""
    total: int = Field(..., description="Gesamtanzahl Messages")
    assistant: int = Field(..., description="Anzahl Assistant-Messages")
    user: int = Field(..., description="Anzahl User-Messages")


class QualityMetricsResponse(BaseModel):
    """Response Schema für Quality-Metriken."""
    score: float = Field(..., description="Quality Score (0-100)")
    trend: str = Field(..., description="Trend: 'improving', 'stable', 'declining'")


# ============================================================================
# RAG CHAT PROMPT SCHEMAS (PHASE 1)
# ============================================================================

class SaveRAGChatPromptRequest(BaseModel):
    """Request Schema für RAG Chat Prompt speichern."""
    prompt_text: str = Field(..., min_length=1, description="RAG Chat Prompt-Text")
    multi_query_prompt_text: Optional[str] = Field(None, description="Multi-Query Prompt-Text (optional, PHASE 2)")


class RAGChatPromptResponse(BaseModel):
    """Response Schema für RAG Chat Prompt."""
    id: int
    document_type_id: Optional[int]  # None = Default-Prompt
    prompt_text: str
    multi_query_prompt_text: Optional[str] = None
    is_custom: bool = Field(True, description="Immer True (nur Custom Prompts werden gespeichert)")
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime


class SHAPStatisticsResponse(BaseModel):
    """Response Schema für SHAP-Statistiken."""
    total_explanations: int = Field(..., ge=0, description="Gesamtanzahl der SHAP-Erklärungen")
    average_feature_count: float = Field(..., ge=0, description="Durchschnittliche Anzahl Features pro Erklärung")
    top_features: List[Dict[str, Any]] = Field(..., description="Top Features nach durchschnittlicher Importance")


class MLPerformanceResponse(BaseModel):
    """Response Schema für ML-Model Performance."""
    model_accuracy: float = Field(..., ge=0.0, le=1.0, description="Model Accuracy (0-1)")
    precision: float = Field(..., ge=0.0, le=1.0, description="Precision (0-1)")
    recall: float = Field(..., ge=0.0, le=1.0, description="Recall (0-1)")
    f1_score: float = Field(..., ge=0.0, le=1.0, description="F1-Score (0-1)")
    training_samples: int = Field(..., ge=0, description="Anzahl der Trainings-Samples")
    
    @validator('model_accuracy', 'precision', 'recall', 'f1_score')
    def validate_score_range(cls, v):
        """Validiere dass Scores zwischen 0 und 1 liegen."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Score must be between 0.0 and 1.0')
        return v


class OptimizationHistoryResponse(BaseModel):
    """Response Schema für Optimization History Eintrag."""
    date: str = Field(..., description="Datum der Optimierung (ISO format)")
    action: str = Field(..., description="Beschreibung der Optimierung")
    before_score: float = Field(..., ge=0.0, le=1.0, description="Score vor Optimierung")
    after_score: float = Field(..., ge=0.0, le=1.0, description="Score nach Optimierung")
    improvement: float = Field(..., description="Verbesserung (after_score - before_score)")


# ============================================================================
# SEARCH QUALITY ANALYTICS SCHEMAS (PHASE 5)
# ============================================================================

class DocumentTypeDistributionResponse(BaseModel):
    """Response Schema für Dokument-Typ-Verteilung."""
    document_type: str = Field(..., description="Name des Dokument-Typs")
    count: int = Field(..., ge=0, description="Anzahl Dokumente dieses Typs im System")
    average_score: float = Field(..., ge=0.0, le=1.0, description="Durchschnittlicher Relevanz-Score")
    found_in_top_k: int = Field(..., ge=0, description="Anzahl Dokumente dieses Typs in Top-K Suchergebnissen")


class ScoreDistributionResponse(BaseModel):
    """Response Schema für Score-Verteilung."""
    min: float = Field(..., ge=0.0, le=1.0, description="Minimaler Score")
    max: float = Field(..., ge=0.0, le=1.0, description="Maximaler Score")
    average: float = Field(..., ge=0.0, le=1.0, description="Durchschnittlicher Score")
    median: float = Field(..., ge=0.0, le=1.0, description="Median Score")


class TopQueryResponse(BaseModel):
    """Response Schema für Top Query."""
    query: str = Field(..., description="Die ursprüngliche Query")
    document_types_found: List[str] = Field(..., description="Gefundene Dokument-Typen")
    missing_document_types: List[str] = Field(..., description="Fehlende Dokument-Typen (im System vorhanden, aber nicht gefunden)")
    average_score: float = Field(..., ge=0.0, le=1.0, description="Durchschnittlicher Score für diese Query")


class SHAPInsightResponse(BaseModel):
    """Response Schema für SHAP-Insight."""
    feature: str = Field(..., description="Name des Features")
    impact: float = Field(..., ge=0.0, description="Durchschnittliche Importance (Impact)")
    explanation: str = Field(..., description="Erklärung des Features und seines Einflusses")


class SearchQualityAnalyticsResponse(BaseModel):
    """Response Schema für Search Quality Analytics."""
    document_type_distribution: List[DocumentTypeDistributionResponse] = Field(..., description="Dokument-Typ-Verteilung in Suchergebnissen")
    score_distribution: ScoreDistributionResponse = Field(..., description="Score-Verteilung")
    top_queries: List[TopQueryResponse] = Field(..., description="Top Queries mit gefundenen/fehlenden Dokument-Typen")
    shap_insights: List[SHAPInsightResponse] = Field(..., description="SHAP-basierte Insights")


class RAGAnalyticsResponse(BaseModel):
    """Response Schema für umfassende RAG Analytics."""
    feedback: FeedbackStatisticsResponse = Field(..., description="Feedback-Statistiken")
    queries: QueryStatisticsResponse = Field(..., description="Query-Statistiken")
    chunking: ChunkingStatisticsResponse = Field(..., description="Chunking-Statistiken")
    indexing: IndexingStatisticsResponse = Field(..., description="Indexing-Statistiken")
    messages: MessageStatisticsResponse = Field(..., description="Message-Statistiken")
    quality: QualityMetricsResponse = Field(..., description="Quality-Metriken")
    shap: Optional[SHAPStatisticsResponse] = Field(None, description="SHAP-Statistiken (optional)")
    ml_performance: Optional[MLPerformanceResponse] = Field(None, description="ML-Model Performance (optional)")
    optimization_history: Optional[List[OptimizationHistoryResponse]] = Field(None, description="Optimization History (optional)")


class SHAPExplanationResponse(BaseModel):
    """Response Schema für SHAP Explanation.
    
    Repräsentiert eine SHAP-Erklärung für einen RAG-Such-Ergebnis.
    """
    feature_importance: Dict[str, float] = Field(..., description="Feature-Importance-Werte (Dict[feature_name, importance])")
    base_value: float = Field(..., ge=0.0, le=1.0, description="Base Value (Durchschnittlicher Score)")
    shap_values: List[float] = Field(..., description="SHAP Values (Liste von Importance-Werten)")
    expected_value: float = Field(..., ge=0.0, le=1.0, description="Expected Value (Erwarteter Score)")
    prediction: float = Field(..., ge=0.0, le=1.0, description="Prediction (Tatsächlicher Score)")
    query: str = Field(..., description="Die ursprüngliche Query")
    chunk_id: str = Field(..., description="Chunk-ID")
    timestamp: datetime = Field(..., description="Timestamp der Erklärung")
    features: Dict[str, float] = Field(..., description="Normalisierte Feature-Werte")
    
    @validator('prediction', 'base_value', 'expected_value')
    def validate_score_range(cls, v):
        """Validiere dass Scores zwischen 0 und 1 liegen."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Score must be between 0.0 and 1.0')
        return v


# ============================================
# SHAP Analytics Schemas (Phase 2)
# ============================================

class SHAPFeatureImportanceResponse(BaseModel):
    """Response Schema für SHAP Feature Importance.
    
    Zeigt die Wichtigkeit jedes Features für das Ranking-Ergebnis.
    """
    feature_name: str = Field(..., description="Feature-Name (z.B. 'vector_score')")
    importance: float = Field(..., description="SHAP-Wert (positive/negative)")
    normalized_importance: float = Field(..., description="Normalisierte Importance (0-1)")
    description: str = Field(..., description="Feature-Beschreibung")
    
    class Config:
        json_schema_extra = {
            "example": {
                "feature_name": "vector_score",
                "importance": 0.15,
                "normalized_importance": 0.35,
                "description": "Vektor-Ähnlichkeits-Score (Embedding-basiert)"
            }
        }


class SHAPWaterfallDataResponse(BaseModel):
    """Response Schema für SHAP Waterfall Chart Daten.
    
    Daten für Waterfall-Visualisierung: Zeigt wie jedes Feature zur finalen Prediction beiträgt.
    """
    base_value: float = Field(..., description="Base Value (Durchschnitt)")
    expected_value: float = Field(..., description="Expected Value (= base_value für KernelExplainer)")
    prediction: float = Field(..., description="Finale Prediction (Hybrid Score)")
    features: List[Dict[str, Any]] = Field(..., description="Features mit SHAP-Werten")
    
    class Config:
        json_schema_extra = {
            "example": {
                "base_value": 0.5,
                "expected_value": 0.5,
                "prediction": 0.78,
                "features": [
                    {"name": "vector_score", "value": 0.85, "shap_value": 0.15},
                    {"name": "text_score", "value": 0.72, "shap_value": 0.10},
                    {"name": "keyword_matches", "value": 0.2, "shap_value": 0.03}
                ]
            }
        }


class SHAPAnalyticsResponse(BaseModel):
    """Response Schema für SHAP Analytics Dashboard.
    
    Umfassendes Analytics-Dashboard mit SHAP-Daten für Frontend-Visualisierungen.
    """
    # Feature Importance (für Bar Chart)
    feature_importance: List[SHAPFeatureImportanceResponse] = Field(
        ..., 
        description="Feature Importance sortiert nach absoluter Importance"
    )
    
    # Waterfall Data (für Waterfall Chart)
    waterfall_data: SHAPWaterfallDataResponse = Field(
        ..., 
        description="Daten für SHAP Waterfall Visualisierung"
    )
    
    # Background Data Statistics
    background_data_stats: Dict[str, Any] = Field(
        ..., 
        description="Statistiken über Background-Daten"
    )
    
    # Model Info
    model_info: Dict[str, str] = Field(
        ..., 
        description="Informationen über das Ranking-Modell"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "feature_importance": [
                    {
                        "feature_name": "vector_score",
                        "importance": 0.15,
                        "normalized_importance": 0.35,
                        "description": "Vektor-Ähnlichkeits-Score"
                    }
                ],
                "waterfall_data": {
                    "base_value": 0.5,
                    "expected_value": 0.5,
                    "prediction": 0.78,
                    "features": []
                },
                "background_data_stats": {
                    "total_records": 150,
                    "background_data_shape": [50, 7]
                },
                "model_info": {
                    "model_type": "RankingModelWrapper",
                    "explainer_type": "KernelExplainer"
                }
            }
        }


class BackgroundDataStatsResponse(BaseModel):
    """Response Schema für Background Data Statistiken."""
    total_records: int = Field(..., description="Anzahl gesammelter Records")
    background_data_shape: Optional[List[int]] = Field(None, description="Shape der Background-Daten [n_samples, n_features]")
    last_update: Optional[str] = Field(None, description="Letztes Update (ISO-Format)")
    oldest_record: Optional[str] = Field(None, description="Ältester Record (ISO-Format)")
    newest_record: Optional[str] = Field(None, description="Neuester Record (ISO-Format)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_records": 150,
                "background_data_shape": [50, 7],
                "last_update": "2025-11-13T10:30:00",
                "oldest_record": "2025-11-12T14:20:00",
                "newest_record": "2025-11-13T10:30:00"
            }
        }


# ============================================================================
# SEARCH QUALITY METRICS SCHEMAS (v2.9.0)
# ============================================================================

class SearchQualityMetricsResponse(BaseModel):
    """Response Schema für Search Quality Metrics."""
    query: str = Field(..., description="Die ursprüngliche Query")
    timestamp: str = Field(..., description="Zeitstempel (ISO-Format)")
    
    # Precision & Recall
    precision_at_1: float = Field(..., ge=0.0, le=1.0, description="Precision@1")
    precision_at_3: float = Field(..., ge=0.0, le=1.0, description="Precision@3")
    precision_at_5: float = Field(..., ge=0.0, le=1.0, description="Precision@5")
    precision_at_10: float = Field(..., ge=0.0, le=1.0, description="Precision@10")
    
    recall_at_1: float = Field(..., ge=0.0, le=1.0, description="Recall@1")
    recall_at_3: float = Field(..., ge=0.0, le=1.0, description="Recall@3")
    recall_at_5: float = Field(..., ge=0.0, le=1.0, description="Recall@5")
    recall_at_10: float = Field(..., ge=0.0, le=1.0, description="Recall@10")
    
    # Ranking Metriken
    ndcg_at_1: float = Field(..., ge=0.0, le=1.0, description="NDCG@1")
    ndcg_at_3: float = Field(..., ge=0.0, le=1.0, description="NDCG@3")
    ndcg_at_5: float = Field(..., ge=0.0, le=1.0, description="NDCG@5")
    ndcg_at_10: float = Field(..., ge=0.0, le=1.0, description="NDCG@10")
    
    mrr: float = Field(..., ge=0.0, le=1.0, description="Mean Reciprocal Rank")
    
    # Zusätzliche Metriken
    average_relevance_score: float = Field(..., ge=0.0, le=1.0, description="Durchschnittlicher Relevance-Score")
    num_relevant_results: int = Field(..., ge=0, description="Anzahl relevanter Ergebnisse")
    num_total_results: int = Field(..., ge=0, description="Gesamtanzahl Ergebnisse")
    
    # Feedback-Status
    has_feedback: bool = Field(False, description="Wurde Feedback für diese Query gegeben?")
    num_feedback_items: int = Field(0, ge=0, description="Anzahl der Feedback-Einträge (Message-Level + Chunk-Level)")
    
    # Ranking-Vergleich (Hybrid vs ML)
    hybrid_ndcg_at_10: Optional[float] = Field(None, ge=0.0, le=1.0, description="NDCG@10 für Hybrid-Ranking")
    ml_ndcg_at_10: Optional[float] = Field(None, ge=0.0, le=1.0, description="NDCG@10 für ML-Ranking")
    
    # Metadaten
    session_id: Optional[int] = Field(None, description="Chat-Session-ID")
    user_id: Optional[int] = Field(None, description="User-ID")
    document_type: Optional[str] = Field(None, description="Document Type")
    
    # NEU v2.10.1: Filter-Informationen
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="Angewendete Filter (document_type, interest_groups, etc.)")
    score_threshold: Optional[float] = Field(None, description="Score Threshold der verwendet wurde")
    top_k_limit: Optional[int] = Field(None, description="Top-K Limit der verwendet wurde")
    feedback_coverage: Optional[float] = Field(None, ge=0.0, le=1.0, description="Anteil der Chunks mit Feedback (0-1)")
    
    # NEU v2.10.3: AI-Modell-Einstellungen
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="AI Temperature (0.0-2.0)")
    max_tokens: Optional[int] = Field(None, ge=1, le=8000, description="Max Tokens (1-8000)")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top P (0.0-1.0)")
    
    # NEU v2.10.4: Normalisierte Relevance Scores für Frontend
    normalized_relevance_scores: Optional[Dict[str, float]] = Field(
        None, 
        description="Mapping von chunk_id zu normalisiertem Relevance Score (0-1)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "vertikale verformung",
                "timestamp": "2025-01-27T10:30:00",
                "precision_at_1": 0.8,
                "precision_at_3": 0.75,
                "precision_at_5": 0.7,
                "precision_at_10": 0.65,
                "recall_at_1": 0.4,
                "recall_at_3": 0.6,
                "recall_at_5": 0.7,
                "recall_at_10": 0.8,
                "ndcg_at_1": 0.8,
                "ndcg_at_3": 0.75,
                "ndcg_at_5": 0.72,
                "ndcg_at_10": 0.68,
                "mrr": 0.85,
                "average_relevance_score": 0.72,
                "num_relevant_results": 8,
                "num_total_results": 10,
                "hybrid_ndcg_at_10": 0.65,
                "ml_ndcg_at_10": 0.68,
                "session_id": 1,
                "user_id": 1,
                "document_type": "Fachartikel"
            }
        }


class AggregatedSearchQualityMetricsResponse(BaseModel):
    """Response Schema für aggregierte Search Quality Metrics."""
    num_queries: int = Field(..., ge=0, description="Anzahl analysierter Queries")
    
    # Durchschnittliche Metriken
    average_precision_at_1: float = Field(..., ge=0.0, le=1.0)
    average_precision_at_3: float = Field(..., ge=0.0, le=1.0)
    average_precision_at_5: float = Field(..., ge=0.0, le=1.0)
    average_precision_at_10: float = Field(..., ge=0.0, le=1.0)
    
    average_recall_at_1: float = Field(..., ge=0.0, le=1.0)
    average_recall_at_3: float = Field(..., ge=0.0, le=1.0)
    average_recall_at_5: float = Field(..., ge=0.0, le=1.0)
    average_recall_at_10: float = Field(..., ge=0.0, le=1.0)
    
    average_ndcg_at_1: float = Field(..., ge=0.0, le=1.0)
    average_ndcg_at_3: float = Field(..., ge=0.0, le=1.0)
    average_ndcg_at_5: float = Field(..., ge=0.0, le=1.0)
    average_ndcg_at_10: float = Field(..., ge=0.0, le=1.0)
    
    average_mrr: float = Field(..., ge=0.0, le=1.0)
    average_relevance_score: float = Field(..., ge=0.0, le=1.0)
    average_num_relevant: float = Field(..., ge=0.0)
    average_num_total: float = Field(..., ge=0.0)
    
    # Hybrid vs ML Vergleich
    hybrid_vs_ml_comparison: Dict[str, Any] = Field(..., description="Vergleich Hybrid vs ML Ranking")
    
    class Config:
        json_schema_extra = {
            "example": {
                "num_queries": 50,
                "average_precision_at_10": 0.68,
                "average_recall_at_10": 0.75,
                "average_ndcg_at_10": 0.70,
                "average_mrr": 0.82,
                "hybrid_vs_ml_comparison": {
                    "hybrid_avg_ndcg_at_10": 0.65,
                    "ml_avg_ndcg_at_10": 0.70,
                    "improvement_percent": 7.7
                }
            }
        }


# ============================================================================
# TREND ANALYSIS SCHEMAS (v2.9.0)
# ============================================================================

class TrendDataPoint(BaseModel):
    """Einzelner Datenpunkt für Trend-Analyse."""
    date: str = Field(..., description="Datum (ISO-Format)")
    query: str = Field(..., description="Die ursprüngliche Query")
    precision_at_10: float = Field(..., ge=0.0, le=1.0)
    recall_at_10: float = Field(..., ge=0.0, le=1.0)
    ndcg_at_10: float = Field(..., ge=0.0, le=1.0)
    mrr: float = Field(..., ge=0.0, le=1.0)
    session_id: Optional[int] = None
    user_id: Optional[int] = None
    document_type: Optional[str] = None


class TrendAnalysisResponse(BaseModel):
    """Response Schema für Trend-Analyse."""
    start_date: str = Field(..., description="Start-Datum (ISO-Format)")
    end_date: str = Field(..., description="End-Datum (ISO-Format)")
    data_points: List[TrendDataPoint] = Field(..., description="Datenpunkte über Zeit")
    aggregated_metrics: Dict[str, Any] = Field(..., description="Aggregierte Metriken")
    trends: Dict[str, str] = Field(..., description="Trend-Analyse (improving/stable/degrading)")
    alerts: List[Dict[str, Any]] = Field(default_factory=list, description="Alerts bei Qualitätsverschlechterung")


class BeforeAfterComparisonResponse(BaseModel):
    """Response Schema für Vorher/Nachher Vergleich."""
    query: str = Field(..., description="Die Query")
    before_date: str = Field(..., description="Vorher-Datum (ISO-Format)")
    after_date: str = Field(..., description="Nachher-Datum (ISO-Format)")
    before_metrics: SearchQualityMetricsResponse = Field(..., description="Metriken vorher")
    after_metrics: SearchQualityMetricsResponse = Field(..., description="Metriken nachher")
    improvements: Dict[str, float] = Field(..., description="Verbesserungen (Delta)")
    changes: List[Dict[str, Any]] = Field(..., description="Detaillierte Änderungen")


class AlertResponse(BaseModel):
    """Response Schema für Alert."""
    id: int = Field(..., description="Alert ID")
    type: str = Field(..., description="Alert-Typ (quality_degradation, improvement, threshold)")
    severity: str = Field(..., description="Schweregrad (low, medium, high, critical)")
    message: str = Field(..., description="Alert-Nachricht")
    query: Optional[str] = Field(None, description="Betroffene Query")
    timestamp: str = Field(..., description="Zeitstempel (ISO-Format)")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Relevante Metriken")
    actionable: bool = Field(True, description="Kann der User etwas tun?")
    undo_available: bool = Field(False, description="Ist Undo verfügbar?")


# ============================================================================
# CHUNK FEEDBACK SCHEMAS (v2.9.0)
# ============================================================================

class SubmitChunkFeedbackRequest(BaseModel):
    """Request Schema für Chunk-Level Feedback."""
    chunk_id: str = Field(..., description="ID des Chunks")
    chat_message_id: int = Field(..., description="Chat Message ID (Assistant-Message)")
    document_id: int = Field(..., description="Dokument ID des Chunks")
    rating: str = Field(..., description="Bewertung: 'positive', 'negative', 'neutral'")
    comment: Optional[str] = Field(None, max_length=2000, description="Optionaler Kommentar (max 2000 Zeichen)")

    @validator('rating')
    def validate_rating(cls, v):
        if v not in ['positive', 'negative', 'neutral']:
            raise ValueError("rating must be 'positive', 'negative', or 'neutral'")
        return v


class ChunkFeedbackResponse(BaseModel):
    """Response Schema für Chunk-Level Feedback."""
    id: int = Field(..., description="Feedback ID")
    chunk_id: str = Field(..., description="ID des Chunks")
    chat_message_id: int = Field(..., description="Chat Message ID")
    document_id: int = Field(..., description="Dokument ID")
    user_id: int = Field(..., description="User ID")
    rating: str = Field(..., description="Bewertung")
    comment: Optional[str] = Field(None, description="Kommentar")
    submitted_at: datetime = Field(..., description="Zeitstempel")


class SHAPHistoryEntryResponse(BaseModel):
    """Response Schema für einen SHAP-Historie-Eintrag."""
    id: int = Field(..., description="Training Data ID")
    query: str = Field(..., description="Die ursprüngliche Query")
    chunk_id: str = Field(..., description="Chunk ID")
    document_id: int = Field(..., description="Dokument ID")
    created_at: datetime = Field(..., description="Zeitstempel")
    shap_explanation: Optional[Dict[str, Any]] = Field(None, description="SHAP-Erklärung (JSON)")
    user_feedback: Optional[str] = Field(None, description="User-Feedback falls vorhanden")
    feedback_comment: Optional[str] = Field(None, description="Feedback-Kommentar falls vorhanden")
    hybrid_score: float = Field(..., description="Hybrid Score")


class SHAPHistoryResponse(BaseModel):
    """Response Schema für SHAP-Historie."""
    entries: List[SHAPHistoryEntryResponse] = Field(..., description="Liste von SHAP-Historie-Einträgen")
    total: int = Field(..., description="Gesamtanzahl Einträge")
    has_more: bool = Field(..., description="Gibt es weitere Einträge?")
