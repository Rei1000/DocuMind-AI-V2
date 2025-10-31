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


class AskQuestionRequest(BaseModel):
    """Request Schema für Fragen an das RAG System."""
    question: str = Field(..., min_length=3, max_length=1000, description="Die Frage")
    session_id: Optional[int] = Field(None, description="Chat-Session ID")
    model: str = Field("gpt-4o-mini", description="AI Model für Antwort")
    top_k: int = Field(5, ge=1, le=20, description="Anzahl der relevanten Chunks")
    score_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Mindest-Relevanz-Score")
    filters: Optional[Dict[str, Any]] = Field(None, description="Suchfilter")
    use_hybrid_search: bool = Field(True, description="Verwende Hybrid Search")


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
    """Response Schema für Quellen-Referenz."""
    document_id: int
    document_title: str
    page_number: int
    chunk_id: int
    preview_image_path: Optional[str]
    relevance_score: float
    text_excerpt: str
    
    @validator('relevance_score')
    def validate_relevance_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Relevance score must be between 0.0 and 1.0')
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
