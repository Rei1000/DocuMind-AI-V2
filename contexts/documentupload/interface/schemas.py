"""
Pydantic Schemas für Document Upload Context

Request/Response Models für API-Endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ChangeWorkflowStatusRequest(BaseModel):
    """Request Schema für Status-Änderung."""
    
    document_id: int = Field(..., description="Dokument ID")
    new_status: str = Field(..., description="Neuer Workflow-Status")
    user_id: int = Field(..., description="User ID des Änderers")
    reason: str = Field(..., description="Grund für die Änderung")
    comment: Optional[str] = Field(None, description="Optionaler Kommentar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": 123,
                "new_status": "reviewed",
                "user_id": 456,
                "reason": "Teamleiter-Freigabe",
                "comment": "Alle Prüfpunkte OK"
            }
        }


class ChangeWorkflowStatusResponse(BaseModel):
    """Response Schema für Status-Änderung."""
    
    success: bool = Field(..., description="Erfolg der Operation")
    message: str = Field(..., description="Status-Meldung")
    document_id: int = Field(..., description="Dokument ID")
    new_status: str = Field(..., description="Neuer Status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Status erfolgreich geändert",
                "document_id": 123,
                "new_status": "reviewed"
            }
        }


class WorkflowStatusChangeSchema(BaseModel):
    """Schema für Workflow-Status-Änderung (Audit Trail)."""
    
    id: int = Field(..., description="Change ID")
    upload_document_id: int = Field(..., description="Dokument ID")
    from_status: Optional[str] = Field(None, description="Vorheriger Status")
    to_status: str = Field(..., description="Neuer Status")
    changed_by_user_id: int = Field(..., description="User ID des Änderers")
    changed_at: str = Field(..., description="Zeitstempel der Änderung (ISO)")
    change_reason: str = Field(..., description="Grund für die Änderung")
    comment: Optional[str] = Field(None, description="Optionaler Kommentar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "upload_document_id": 123,
                "from_status": "draft",
                "to_status": "reviewed",
                "changed_by_user_id": 456,
                "changed_at": "2025-10-22T10:30:00Z",
                "change_reason": "Teamleiter-Freigabe",
                "comment": "Alle Prüfpunkte OK"
            }
        }


class DocumentCommentSchema(BaseModel):
    """Schema für Dokument-Kommentar."""
    
    id: int = Field(..., description="Comment ID")
    upload_document_id: int = Field(..., description="Dokument ID")
    comment_text: str = Field(..., description="Kommentar-Text")
    comment_type: str = Field(..., description="Typ des Kommentars")
    page_number: Optional[int] = Field(None, description="Seiten-Nummer (optional)")
    created_by_user_id: int = Field(..., description="User ID des Erstellers")
    created_at: str = Field(..., description="Erstellungs-Zeitstempel (ISO)")
    status_change_id: Optional[int] = Field(None, description="Status-Change ID (optional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "upload_document_id": 123,
                "comment_text": "Das Dokument ist unvollständig",
                "comment_type": "rejection",
                "page_number": 2,
                "created_by_user_id": 456,
                "created_at": "2025-10-22T10:30:00Z",
                "status_change_id": 1
            }
        }


class AllowedTransitionsResponse(BaseModel):
    """Response Schema für erlaubte Workflow-Transitions."""
    
    document_id: int = Field(..., description="Dokument ID")
    current_status: str = Field(..., description="Aktueller Status")
    allowed_transitions: List[str] = Field(..., description="Liste erlaubter Ziel-Status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": 123,
                "current_status": "draft",
                "allowed_transitions": ["reviewed", "rejected"]
            }
        }


class WorkflowDocumentSummary(BaseModel):
    """Schema für Dokument-Zusammenfassung im Workflow."""
    
    id: int = Field(..., description="Dokument ID")
    filename: str = Field(..., description="Dateiname")
    version: str = Field(..., description="Version")
    workflow_status: str = Field(..., description="Workflow-Status")
    uploaded_at: str = Field(..., description="Upload-Zeitstempel (ISO)")
    interest_group_ids: List[int] = Field(..., description="Interest Group IDs")
    document_type: Optional[str] = Field(None, description="Dokumenttyp")
    qm_chapter: Optional[str] = Field(None, description="QM-Kapitel")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "filename": "Arbeitsanweisung.pdf",
                "version": "v1.0",
                "workflow_status": "draft",
                "uploaded_at": "2025-10-22T10:00:00Z",
                "interest_group_ids": [1, 2],
                "document_type": "Arbeitsanweisung",
                "qm_chapter": "5.2"
            }
        }


# Legacy Schemas für bestehenden Document Upload Router
class AssignInterestGroupsRequest(BaseModel):
    """Request Schema für Interest Groups Zuweisung."""
    
    interest_group_ids: List[int] = Field(..., description="Liste der Interest Group IDs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "interest_group_ids": [1, 2, 3]
            }
        }


class AssignInterestGroupsResponse(BaseModel):
    """Response Schema für Interest Groups Zuweisung."""
    
    success: bool = Field(..., description="Erfolg der Operation")
    message: str = Field(..., description="Status-Meldung")
    document_id: int = Field(..., description="Dokument ID")
    assigned_interest_group_ids: List[int] = Field(..., description="Zugewiesene Interest Group IDs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Interest Groups erfolgreich zugewiesen",
                "document_id": 123,
                "assigned_interest_group_ids": [1, 2, 3]
            }
        }


class UploadDocumentRequest(BaseModel):
    """Request Schema für Dokument-Upload."""
    
    filename: str = Field(..., description="Dateiname")
    original_filename: str = Field(..., description="Original-Dateiname")
    document_type_id: int = Field(..., description="Dokumenttyp ID")
    qm_chapter: Optional[str] = Field(None, description="QM-Kapitel")
    version: str = Field(..., description="Version")
    processing_method: str = Field(..., description="Verarbeitungsmethode (ocr/vision)")
    interest_group_ids: Optional[List[int]] = Field(None, description="Interest Group IDs (optional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "document.pdf",
                "original_filename": "Arbeitsanweisung.pdf",
                "document_type_id": 1,
                "qm_chapter": "5.2",
                "version": "v1.0",
                "processing_method": "vision",
                "interest_group_ids": [1, 2]
            }
        }


class UploadedDocumentSchema(BaseModel):
    """Schema für hochgeladenes Dokument."""
    
    id: int = Field(..., description="Dokument ID")
    filename: str = Field(..., description="Dateiname")
    version: str = Field(..., description="Version")
    workflow_status: Optional[str] = Field("draft", description="Workflow-Status")
    uploaded_at: str = Field(..., description="Upload-Zeitstempel (ISO)")
    interest_group_ids: Optional[List[int]] = Field(None, description="Interest Group IDs")
    document_type: Optional[str] = Field(None, description="Dokumenttyp")
    qm_chapter: Optional[str] = Field(None, description="QM-Kapitel")
    preview_url: Optional[str] = Field(None, description="Preview-URL")
    file_size: Optional[int] = Field(None, description="Dateigröße in Bytes")
    file_type: Optional[str] = Field(None, description="Dateityp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "filename": "Arbeitsanweisung.pdf",
                "version": "v1.0",
                "workflow_status": "draft",
                "uploaded_at": "2025-01-22T10:30:00Z",
                "interest_group_ids": [1, 2],
                "document_type": "Arbeitsanweisung",
                "qm_chapter": "5.2",
                "preview_url": None,
                "file_size": 1024000,
                "file_type": "pdf"
            }
        }


class UploadDocumentResponse(BaseModel):
    """Response Schema für Dokument-Upload."""
    
    success: bool = Field(..., description="Erfolg der Operation")
    message: str = Field(..., description="Status-Meldung")
    document: UploadedDocumentSchema = Field(..., description="Hochgeladenes Dokument")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Dokument erfolgreich hochgeladen",
                "document": {
                    "id": 123,
                    "filename": "Arbeitsanweisung.pdf",
                    "version": "v1.0",
                    "workflow_status": "draft",
                    "uploaded_at": "2025-01-22T10:30:00Z",
                    "interest_group_ids": [1, 2],
                    "document_type": "Arbeitsanweisung",
                    "qm_chapter": "5.2",
                    "preview_url": None,
                    "file_size": 1024000,
                    "file_type": "pdf"
                }
            }
        }


class GeneratePreviewResponse(BaseModel):
    """Response Schema für Preview-Generierung."""
    
    success: bool = Field(..., description="Erfolg der Operation")
    message: str = Field(..., description="Status-Meldung")
    preview_url: Optional[str] = Field(None, description="URL zum Preview-Bild")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Preview erfolgreich generiert",
                "preview_url": "/uploads/previews/document_123_preview.png"
            }
        }




class GetUploadsListResponse(BaseModel):
    """Response Schema für Upload-Liste."""
    
    uploads: List[UploadedDocumentSchema] = Field(..., description="Liste der Uploads")
    total: int = Field(..., description="Gesamtanzahl der Uploads")
    
    class Config:
        json_schema_extra = {
            "example": {
                "uploads": [
                    {
                        "id": 123,
                        "filename": "Arbeitsanweisung.pdf",
                        "version": "v1.0",
                        "workflow_status": "draft",
                        "uploaded_at": "2025-10-22T10:00:00Z",
                        "interest_group_ids": [1, 2],
                        "document_type": "Arbeitsanweisung",
                        "qm_chapter": "5.2",
                        "preview_url": "/uploads/previews/document_123_preview.png"
                    }
                ],
                "total": 1
            }
        }


class DeleteUploadResponse(BaseModel):
    """Response Schema für Upload-Löschung."""
    
    success: bool = Field(..., description="Erfolg der Operation")
    message: str = Field(..., description="Status-Meldung")
    deleted_document_id: int = Field(..., description="Gelöschte Dokument ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Dokument erfolgreich gelöscht",
                "deleted_document_id": 123
            }
        }


class ErrorResponse(BaseModel):
    """Response Schema für Fehler."""
    
    success: bool = Field(False, description="Erfolg der Operation")
    message: str = Field(..., description="Fehler-Meldung")
    error_code: Optional[str] = Field(None, description="Fehler-Code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Dokument nicht gefunden",
                "error_code": "DOCUMENT_NOT_FOUND"
            }
        }


class DocumentPageSchema(BaseModel):
    """Schema für Dokument-Seite."""
    
    id: int = Field(..., description="Seiten ID")
    upload_document_id: int = Field(..., description="Dokument ID")
    page_number: int = Field(..., description="Seiten-Nummer")
    file_path: Optional[str] = Field(None, description="Pfad zur Seiten-Datei")
    preview_url: Optional[str] = Field(None, description="Preview-URL")
    ai_processing_status: Optional[str] = Field("pending", description="AI-Verarbeitungs-Status")
    ai_processing_result: Optional[str] = Field(None, description="AI-Verarbeitungs-Ergebnis")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "upload_document_id": 123,
                "page_number": 1,
                "file_path": "/uploads/documents/document_123_page_1.png",
                "preview_url": "/uploads/previews/document_123_page_1_preview.png",
                "ai_processing_status": "completed",
                "ai_processing_result": "{\"text\": \"Arbeitsanweisung für...\", \"confidence\": 0.95}"
            }
        }


class InterestGroupAssignmentSchema(BaseModel):
    """Schema für Interest Group Zuweisung."""
    
    id: int = Field(..., description="Zuweisungs ID")
    upload_document_id: int = Field(..., description="Dokument ID")
    interest_group_id: int = Field(..., description="Interest Group ID")
    assigned_at: str = Field(..., description="Zuweisungs-Zeitstempel (ISO)")
    assigned_by_user_id: int = Field(..., description="User ID des Zuweisenden")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "upload_document_id": 123,
                "interest_group_id": 2,
                "assigned_at": "2025-10-22T10:00:00Z",
                "assigned_by_user_id": 456
            }
        }


class UploadedDocumentDetailSchema(BaseModel):
    """Schema für detaillierte Dokument-Informationen."""
    
    document: Optional[UploadedDocumentSchema] = Field(None, description="Dokument-Informationen")
    pages: List[DocumentPageSchema] = Field(default_factory=list, description="Dokument-Seiten")
    interest_group_assignments: List[InterestGroupAssignmentSchema] = Field(default_factory=list, description="Interest Group Zuweisungen")
    workflow_history: List[WorkflowStatusChangeSchema] = Field(default_factory=list, description="Workflow-Historie")
    comments: List[DocumentCommentSchema] = Field(default_factory=list, description="Dokument-Kommentare")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document": {
                    "id": 123,
                    "filename": "Arbeitsanweisung.pdf",
                    "version": "v1.0",
                    "workflow_status": "draft",
                    "uploaded_at": "2025-10-22T10:00:00Z",
                    "interest_group_ids": [1, 2],
                    "document_type": "Arbeitsanweisung",
                    "qm_chapter": "5.2",
                    "preview_url": "/uploads/previews/document_123_preview.png",
                    "file_size": 1024000,
                    "file_type": "application/pdf"
                },
                "pages": [],
                "interest_group_assignments": [],
                "workflow_history": [],
                "comments": []
            }
        }


class AIProcessingResultSchema(BaseModel):
    """Schema für AI-Verarbeitungsergebnisse."""
    
    id: int = Field(..., description="Processing Result ID")
    document_page_id: int = Field(..., description="Dokument-Seiten ID")
    processing_method: str = Field(..., description="Verarbeitungsmethode")
    ai_model: str = Field(..., description="AI-Modell")
    processing_status: str = Field(..., description="Verarbeitungsstatus")
    result_data: Optional[dict] = Field(None, description="AI-Verarbeitungsergebnis")
    confidence_score: Optional[float] = Field(None, description="Vertrauenswert")
    processing_time_ms: Optional[int] = Field(None, description="Verarbeitungszeit in ms")
    created_at: str = Field(..., description="Erstellungszeitpunkt")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "document_page_id": 123,
                "processing_method": "vision",
                "ai_model": "gpt-4-vision",
                "processing_status": "completed",
                "result_data": {"text": "Extracted text content"},
                "confidence_score": 0.95,
                "processing_time_ms": 2500,
                "created_at": "2025-10-22T10:00:00Z"
            }
        }


class GetUploadDetailsResponse(BaseModel):
    """Response Schema für Upload-Details."""
    
    success: bool = Field(..., description="Erfolg der Operation")
    document: UploadedDocumentDetailSchema = Field(..., description="Dokument-Details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "document": {
                    "document": {
                        "id": 123,
                        "filename": "Arbeitsanweisung.pdf",
                        "version": "v1.0",
                        "workflow_status": "draft",
                        "uploaded_at": "2025-10-22T10:00:00Z",
                        "interest_group_ids": [1, 2],
                        "document_type": "Arbeitsanweisung",
                        "qm_chapter": "5.2",
                        "preview_url": "/uploads/previews/document_123_preview.png"
                    },
                    "pages": [],
                    "interest_group_assignments": [],
                    "workflow_history": [],
                    "comments": []
                }
            }
        }