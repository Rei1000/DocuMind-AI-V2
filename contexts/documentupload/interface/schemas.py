"""
Pydantic Schemas für Document Upload Context

Schemas definieren die API-Contracts (Request/Response DTOs).
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


# ============================================================================
# WORKFLOW SCHEMAS
# ============================================================================

class WorkflowStatus(str, Enum):
    """Workflow-Status Enum für API."""
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"


class ChangeWorkflowStatusRequest(BaseModel):
    """Request Schema für Workflow-Status-Änderung."""
    document_id: int = Field(..., description="Dokument ID")
    new_status: WorkflowStatus = Field(..., description="Neuer Workflow-Status")
    reason: str = Field(..., description="Grund für die Änderung")
    comment: Optional[str] = Field(None, description="Optionaler Kommentar")
    
    @validator('reason')
    def validate_reason(cls, v):
        """Validiere reason."""
        if not v or len(v.strip()) == 0:
            raise ValueError("reason cannot be empty")
        return v.strip()


class WorkflowStatusChangeSchema(BaseModel):
    """Schema für Workflow-Status-Änderung."""
    id: int = Field(..., description="Status-Change ID")
    document_id: int = Field(..., description="Dokument ID")
    from_status: str = Field(..., description="Vorheriger Status")
    to_status: str = Field(..., description="Neuer Status")
    changed_by_user_id: int = Field(..., description="User ID des Änderers")
    reason: str = Field(..., description="Grund für die Änderung")
    created_at: datetime = Field(..., description="Zeitstempel der Änderung")


class ChangeWorkflowStatusResponse(BaseModel):
    """Response Schema für Workflow-Status-Änderung."""
    success: bool = Field(..., description="Erfolg der Operation")
    message: str = Field(..., description="Nachricht")
    document_id: int = Field(..., description="Dokument ID")
    new_status: str = Field(..., description="Neuer Status")
    changed_by: str = Field(..., description="Name des Änderers")
    changed_at: datetime = Field(..., description="Zeitstempel der Änderung")


class WorkflowDocumentSchema(BaseModel):
    """Schema für Workflow-Dokument."""
    id: int = Field(..., description="Dokument ID")
    filename: str = Field(..., description="Dateiname")
    version: str = Field(..., description="Version")
    workflow_status: str = Field(..., description="Workflow-Status")
    uploaded_at: str = Field(..., description="Upload-Zeitstempel")
    interest_group_ids: List[int] = Field(default_factory=list, description="Interest Group IDs")
    document_type: Optional[int] = Field(None, description="Dokumenttyp ID")
    qm_chapter: Optional[str] = Field(None, description="QM-Kapitel")
    preview_url: Optional[str] = Field(None, description="Preview-URL")


class AllowedTransitionsResponse(BaseModel):
    """Response Schema für erlaubte Transitions."""
    current_status: str = Field(..., description="Aktueller Status")
    allowed_transitions: List[str] = Field(..., description="Erlaubte Transitions")
    user_level: int = Field(..., description="User-Level")


class GetDocumentsByStatusResponse(BaseModel):
    """Response Schema für Dokumente nach Status."""
    success: bool = Field(..., description="Erfolg der Operation")
    data: dict = Field(..., description="Daten-Container mit documents Array")


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class UploadDocumentRequest(BaseModel):
    """
    Request Schema für Document Upload.
    
    Wird zusammen mit File Upload (multipart/form-data) verwendet.
    """
    filename: str = Field(..., description="Dateiname (wird normalisiert)")
    original_filename: str = Field(..., description="Original-Dateiname")
    document_type_id: int = Field(..., description="Dokumenttyp ID")
    qm_chapter: str = Field(..., description="QM-Kapitel (z.B. '1.2.3')")
    version: str = Field(..., description="Version (z.B. 'v1.0')")
    processing_method: str = Field(..., description="Verarbeitungsmethode: 'ocr' oder 'vision'")
    
    @validator('processing_method')
    def validate_processing_method(cls, v):
        """Validiere processing_method."""
        if v not in ['ocr', 'vision']:
            raise ValueError("processing_method must be 'ocr' or 'vision'")
        return v
    
    @validator('qm_chapter')
    def validate_qm_chapter(cls, v):
        """Validiere QM-Kapitel Format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("qm_chapter cannot be empty")
        return v.strip()
    
    @validator('version')
    def validate_version(cls, v):
        """Validiere Version Format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("version cannot be empty")
        return v.strip()


class AssignInterestGroupsRequest(BaseModel):
    """
    Request Schema für Interest Group Assignment.
    """
    interest_group_ids: List[int] = Field(..., description="Liste von Interest Group IDs")
    
    @validator('interest_group_ids')
    def validate_interest_group_ids(cls, v):
        """Validiere Interest Group IDs."""
        if not v or len(v) == 0:
            raise ValueError("At least one interest group must be assigned")
        
        # Prüfe auf Duplikate
        if len(v) != len(set(v)):
            raise ValueError("Duplicate interest group IDs not allowed")
        
        return v


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class AIProcessingResultSchema(BaseModel):
    """
    Response Schema für AI Processing Result.
    """
    id: int
    document_page_id: int
    prompt_template_id: int
    ai_model_used: str
    raw_response: str
    parsed_json: Optional[dict]
    tokens_sent: Optional[int]
    tokens_received: Optional[int]
    processing_time_ms: Optional[int]
    status: str
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentPageSchema(BaseModel):
    """
    Response Schema für DocumentPage.
    """
    id: int
    upload_document_id: int
    page_number: int
    preview_image_path: str
    thumbnail_path: Optional[str]
    width: Optional[int]
    height: Optional[int]
    created_at: datetime
    ai_processing_result: Optional[AIProcessingResultSchema] = None
    
    class Config:
        from_attributes = True


class InterestGroupAssignmentSchema(BaseModel):
    """
    Response Schema für InterestGroupAssignment.
    """
    id: int
    upload_document_id: int
    interest_group_id: int
    assigned_by_user_id: int
    assigned_at: datetime
    
    class Config:
        from_attributes = True


class UploadedDocumentSchema(BaseModel):
    """
    Response Schema für UploadedDocument.
    """
    id: int
    filename: str
    original_filename: str
    file_size_bytes: int
    file_type: str
    document_type_id: int
    qm_chapter: str
    version: str
    page_count: int
    uploaded_by_user_id: int
    uploaded_at: datetime
    file_path: str
    processing_method: str
    processing_status: str
    workflow_status: Optional[str] = "draft"
    
    class Config:
        from_attributes = True


class UploadedDocumentDetailSchema(UploadedDocumentSchema):
    """
    Response Schema für UploadedDocument mit Pages und Interest Groups.
    """
    pages: List[DocumentPageSchema] = []
    interest_groups: List[InterestGroupAssignmentSchema] = []


class UploadDocumentResponse(BaseModel):
    """
    Response Schema für erfolgreichen Upload.
    """
    success: bool
    message: str
    document: UploadedDocumentSchema


class GeneratePreviewResponse(BaseModel):
    """
    Response Schema für Preview-Generierung.
    """
    success: bool
    message: str
    pages_generated: int
    pages: List[DocumentPageSchema]


class AssignInterestGroupsResponse(BaseModel):
    """
    Response Schema für Interest Group Assignment.
    """
    success: bool
    message: str
    assignments: List[InterestGroupAssignmentSchema]


class GetUploadDetailsResponse(BaseModel):
    """
    Response Schema für Upload Details.
    """
    success: bool
    document: UploadedDocumentDetailSchema


class GetUploadsListResponse(BaseModel):
    """
    Response Schema für Upload Liste.
    """
    success: bool
    total: int
    documents: List[UploadedDocumentSchema]


class DeleteUploadResponse(BaseModel):
    """
    Response Schema für Upload Deletion.
    """
    success: bool
    message: str


# ============================================================================
# ERROR SCHEMAS
# ============================================================================

class ErrorResponse(BaseModel):
    """
    Response Schema für Fehler.
    """
    success: bool = False
    error: str
    details: Optional[str] = None

