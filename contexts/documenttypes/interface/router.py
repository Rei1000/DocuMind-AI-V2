"""
Interface Layer: DocumentTypes Context

FastAPI Router für DocumentType REST API.
Exponiert die Anwendungslogik nach außen.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database import get_db
from contexts.accesscontrol.interface.guard_router import get_current_user

from ..application.services import DocumentTypeService
from ..infrastructure.repositories import SQLAlchemyDocumentTypeRepository


router = APIRouter(prefix="/api/document-types", tags=["Document Types"])


# === PYDANTIC SCHEMAS ===

class DocumentTypeCreate(BaseModel):
    """Schema: Create Document Type Request"""
    name: str = Field(..., min_length=1, max_length=100, description="Anzeigename")
    code: str = Field(..., min_length=1, max_length=50, description="Technischer Code (UPPERCASE)")
    description: str = Field("", description="Detaillierte Beschreibung")
    allowed_file_types: List[str] = Field(default_factory=lambda: [".pdf"], description="Erlaubte Dateitypen")
    max_file_size_mb: int = Field(10, gt=0, le=100, description="Max Dateigröße in MB")
    requires_ocr: bool = Field(False, description="OCR benötigt?")
    requires_vision: bool = Field(False, description="Vision AI benötigt?")
    sort_order: int = Field(0, description="Sortierung")


class DocumentTypeUpdate(BaseModel):
    """Schema: Update Document Type Request"""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    allowed_file_types: List[str] | None = None
    max_file_size_mb: int | None = Field(None, gt=0, le=100)
    requires_ocr: bool | None = None
    requires_vision: bool | None = None
    default_prompt_template_id: int | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class DocumentTypeResponse(BaseModel):
    """Schema: Document Type Response"""
    id: int
    name: str
    code: str
    description: str
    allowed_file_types: List[str]
    max_file_size_mb: int
    requires_ocr: bool
    requires_vision: bool
    default_prompt_template_id: int | None
    is_active: bool
    sort_order: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


# === DEPENDENCY INJECTION ===

def get_document_type_service(db: Session = Depends(get_db)) -> DocumentTypeService:
    """
    Dependency: Initialize DocumentTypeService with Repository
    
    Implements Dependency Injection for Service Layer.
    """
    repository = SQLAlchemyDocumentTypeRepository(db)
    return DocumentTypeService(repository)


# === API ENDPOINTS ===

@router.get("/", response_model=List[DocumentTypeResponse])
async def list_document_types(
    active_only: bool = True,
    service: DocumentTypeService = Depends(get_document_type_service),
    current_user: dict = Depends(get_current_user)
):
    """
    GET /api/document-types
    
    Liste alle Dokumenttypen.
    
    Query Parameters:
        active_only: Nur aktive Typen? (default: true)
    
    Returns:
        Liste von DocumentType Objekten (sortiert nach sort_order)
    
    Permissions:
        Authenticated user
    """
    document_types = service.list_document_types(active_only=active_only)
    
    return [
        DocumentTypeResponse(
            id=dt.id,
            name=dt.name,
            code=dt.code,
            description=dt.description,
            allowed_file_types=dt.allowed_file_types,
            max_file_size_mb=dt.max_file_size_mb,
            requires_ocr=dt.requires_ocr,
            requires_vision=dt.requires_vision,
            default_prompt_template_id=dt.default_prompt_template_id,
            is_active=dt.is_active,
            sort_order=dt.sort_order,
            created_at=dt.created_at.isoformat() if dt.created_at else "",
            updated_at=dt.updated_at.isoformat() if dt.updated_at else ""
        )
        for dt in document_types
    ]


@router.get("/{document_type_id}", response_model=DocumentTypeResponse)
async def get_document_type(
    document_type_id: int,
    service: DocumentTypeService = Depends(get_document_type_service),
    current_user: dict = Depends(get_current_user)
):
    """
    GET /api/document-types/{id}
    
    Hole einzelnen Dokumenttyp by ID.
    
    Returns:
        DocumentType Objekt
    
    Raises:
        404: DocumentType nicht gefunden
    
    Permissions:
        Authenticated user
    """
    document_type = service.get_document_type(document_type_id)
    
    if not document_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DocumentType mit ID {document_type_id} nicht gefunden"
        )
    
    return DocumentTypeResponse(
        id=document_type.id,
        name=document_type.name,
        code=document_type.code,
        description=document_type.description,
        allowed_file_types=document_type.allowed_file_types,
        max_file_size_mb=document_type.max_file_size_mb,
        requires_ocr=document_type.requires_ocr,
        requires_vision=document_type.requires_vision,
        default_prompt_template_id=document_type.default_prompt_template_id,
        is_active=document_type.is_active,
        sort_order=document_type.sort_order,
        created_at=document_type.created_at.isoformat() if document_type.created_at else "",
        updated_at=document_type.updated_at.isoformat() if document_type.updated_at else ""
    )


@router.post("/", response_model=DocumentTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_document_type(
    data: DocumentTypeCreate,
    service: DocumentTypeService = Depends(get_document_type_service),
    current_user: dict = Depends(get_current_user)
):
    """
    POST /api/document-types
    
    Erstelle neuen Dokumenttyp.
    
    Body:
        DocumentTypeCreate Schema
    
    Returns:
        Erstellter DocumentType
    
    Raises:
        400: Code bereits vorhanden oder Validation fehlgeschlagen
    
    Permissions:
        Authenticated user (idealerweise Admin)
    """
    try:
        document_type = service.create_document_type(
            name=data.name,
            code=data.code,
            description=data.description,
            allowed_file_types=data.allowed_file_types,
            max_file_size_mb=data.max_file_size_mb,
            requires_ocr=data.requires_ocr,
            requires_vision=data.requires_vision,
            created_by=current_user.get("user_id"),
            sort_order=data.sort_order
        )
        
        return DocumentTypeResponse(
            id=document_type.id,
            name=document_type.name,
            code=document_type.code,
            description=document_type.description,
            allowed_file_types=document_type.allowed_file_types,
            max_file_size_mb=document_type.max_file_size_mb,
            requires_ocr=document_type.requires_ocr,
            requires_vision=document_type.requires_vision,
            default_prompt_template_id=document_type.default_prompt_template_id,
            is_active=document_type.is_active,
            sort_order=document_type.sort_order,
            created_at=document_type.created_at.isoformat() if document_type.created_at else "",
            updated_at=document_type.updated_at.isoformat() if document_type.updated_at else ""
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{document_type_id}", response_model=DocumentTypeResponse)
async def update_document_type(
    document_type_id: int,
    data: DocumentTypeUpdate,
    service: DocumentTypeService = Depends(get_document_type_service),
    current_user: dict = Depends(get_current_user)
):
    """
    PUT /api/document-types/{id}
    
    Aktualisiere existierenden Dokumenttyp.
    
    Body:
        DocumentTypeUpdate Schema (nur geänderte Felder)
    
    Returns:
        Aktualisierter DocumentType
    
    Raises:
        404: DocumentType nicht gefunden
        400: Validation fehlgeschlagen
    
    Permissions:
        Authenticated user (idealerweise Admin)
    """
    try:
        # Convert None values to not pass them
        update_data = {k: v for k, v in data.dict().items() if v is not None}
        
        document_type = service.update_document_type(document_type_id, **update_data)
        
        return DocumentTypeResponse(
            id=document_type.id,
            name=document_type.name,
            code=document_type.code,
            description=document_type.description,
            allowed_file_types=document_type.allowed_file_types,
            max_file_size_mb=document_type.max_file_size_mb,
            requires_ocr=document_type.requires_ocr,
            requires_vision=document_type.requires_vision,
            default_prompt_template_id=document_type.default_prompt_template_id,
            is_active=document_type.is_active,
            sort_order=document_type.sort_order,
            created_at=document_type.created_at.isoformat() if document_type.created_at else "",
            updated_at=document_type.updated_at.isoformat() if document_type.updated_at else ""
        )
    except ValueError as e:
        if "nicht gefunden" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{document_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_type(
    document_type_id: int,
    service: DocumentTypeService = Depends(get_document_type_service),
    current_user: dict = Depends(get_current_user)
):
    """
    DELETE /api/document-types/{id}
    
    Lösche Dokumenttyp (Soft Delete - deactivate).
    
    Returns:
        204 No Content
    
    Raises:
        404: DocumentType nicht gefunden
    
    Permissions:
        Authenticated user (idealerweise Admin)
    """
    success = service.delete_document_type(document_type_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DocumentType mit ID {document_type_id} nicht gefunden"
        )
    
    return None

