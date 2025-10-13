"""
Interface Layer: PromptTemplates Context

FastAPI Router für PromptTemplate REST API.
Exponiert die Anwendungslogik nach außen.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database import get_db
from contexts.accesscontrol.interface.guard_router import get_current_user

from ..application.services import PromptTemplateService
from ..infrastructure.repositories import SQLAlchemyPromptTemplateRepository


router = APIRouter(prefix="/api/prompt-templates", tags=["Prompt Templates"])


# === PYDANTIC SCHEMAS ===

class PromptTemplateCreate(BaseModel):
    """Schema: Create Prompt Template Request"""
    name: str = Field(..., min_length=1, max_length=200)
    prompt_text: str = Field(..., min_length=1)
    description: str = Field("", max_length=1000)
    document_type_id: Optional[int] = None
    ai_model: str = Field("gpt-4o-mini", max_length=100)
    temperature: float = Field(0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(4000, gt=0, le=200000)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    detail_level: str = Field("high", pattern="^(high|low)$")
    system_instructions: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class PromptTemplateFromPlayground(BaseModel):
    """Schema: Create Template from Playground"""
    name: str = Field(..., min_length=1, max_length=200)
    prompt_text: str = Field(..., min_length=1)
    ai_model: str
    temperature: float = Field(ge=0.0, le=2.0)
    max_tokens: int = Field(gt=0, le=200000)
    top_p: float = Field(ge=0.0, le=1.0)
    detail_level: str = Field(pattern="^(high|low)$")
    tokens_sent: int
    tokens_received: int
    response_time_ms: float
    description: str = Field("", max_length=1000)
    document_type_id: Optional[int] = None
    example_output: Optional[str] = None
    version: Optional[str] = Field("1.0", max_length=20)


class PromptTemplateUpdate(BaseModel):
    """Schema: Update Prompt Template Request"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    prompt_text: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, max_length=1000)
    document_type_id: Optional[int] = None
    ai_model: Optional[str] = Field(None, max_length=100)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0, le=200000)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    detail_level: Optional[str] = Field(None, pattern="^(high|low)$")
    system_instructions: Optional[str] = None
    tags: Optional[List[str]] = None


class PromptTemplateResponse(BaseModel):
    """Schema: Prompt Template Response"""
    id: int
    name: str
    description: str
    prompt_text: str
    system_instructions: Optional[str]
    document_type_id: Optional[int]
    ai_model: str
    temperature: float
    max_tokens: int
    top_p: float
    detail_level: str
    status: str
    version: str
    tested_successfully: bool
    success_count: int
    last_used_at: Optional[str]
    tags: List[str]
    example_input: Optional[str]
    example_output: Optional[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


# === DEPENDENCY INJECTION ===

def get_service(db: Session = Depends(get_db)) -> PromptTemplateService:
    """Dependency: Initialize PromptTemplateService"""
    repository = SQLAlchemyPromptTemplateRepository(db)
    return PromptTemplateService(repository)


# === API ENDPOINTS ===

@router.get("/", response_model=List[PromptTemplateResponse])
async def list_templates(
    status: Optional[str] = None,
    document_type_id: Optional[int] = None,
    active_only: bool = False,
    service: PromptTemplateService = Depends(get_service),
    current_user: dict = Depends(get_current_user)
):
    """
    GET /api/prompt-templates
    
    Liste alle Prompt Templates mit optionalen Filtern.
    """
    from ..domain.entities import PromptStatus
    
    status_enum = PromptStatus(status) if status else None
    templates = service.list_templates(
        status=status_enum,
        document_type_id=document_type_id,
        active_only=active_only
    )
    
    return [_to_response(t) for t in templates]


@router.get("/{template_id}", response_model=PromptTemplateResponse)
async def get_template(
    template_id: int,
    service: PromptTemplateService = Depends(get_service),
    current_user: dict = Depends(get_current_user)
):
    """GET /api/prompt-templates/{id}"""
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template mit ID {template_id} nicht gefunden"
        )
    return _to_response(template)


@router.post("/", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: PromptTemplateCreate,
    service: PromptTemplateService = Depends(get_service),
    current_user: dict = Depends(get_current_user)
):
    """POST /api/prompt-templates - Erstelle neues Template"""
    try:
        template = service.create_template(
            name=data.name,
            prompt_text=data.prompt_text,
            description=data.description,
            document_type_id=data.document_type_id,
            ai_model=data.ai_model,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
            top_p=data.top_p,
            detail_level=data.detail_level,
            system_instructions=data.system_instructions,
            created_by=current_user.get("user_id"),
            tags=data.tags
        )
        return _to_response(template)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/from-playground", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_from_playground(
    data: PromptTemplateFromPlayground,
    service: PromptTemplateService = Depends(get_service),
    current_user: dict = Depends(get_current_user)
):
    """POST /api/prompt-templates/from-playground - Speichere aus AI Playground"""
    try:
        template = service.create_from_playground(
            name=data.name,
            prompt_text=data.prompt_text,
            ai_model=data.ai_model,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
            top_p=data.top_p,
            detail_level=data.detail_level,
            tokens_sent=data.tokens_sent,
            tokens_received=data.tokens_received,
            response_time_ms=data.response_time_ms,
            description=data.description,
            document_type_id=data.document_type_id,
            created_by=current_user.get("user_id"),
            example_output=data.example_output,
            version=data.version
        )
        return _to_response(template)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{template_id}", response_model=PromptTemplateResponse)
async def update_template(
    template_id: int,
    data: PromptTemplateUpdate,
    service: PromptTemplateService = Depends(get_service),
    current_user: dict = Depends(get_current_user)
):
    """PUT /api/prompt-templates/{id}"""
    try:
        update_data = {k: v for k, v in data.dict().items() if v is not None}
        template = service.update_template(template_id, **update_data)
        return _to_response(template)
    except ValueError as e:
        if "nicht gefunden" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{template_id}/activate", response_model=PromptTemplateResponse)
async def activate_template(
    template_id: int,
    service: PromptTemplateService = Depends(get_service),
    current_user: dict = Depends(get_current_user)
):
    """POST /api/prompt-templates/{id}/activate"""
    try:
        template = service.activate_template(template_id)
        return _to_response(template)
    except ValueError as e:
        if "nicht gefunden" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{template_id}/archive", response_model=PromptTemplateResponse)
async def archive_template(
    template_id: int,
    service: PromptTemplateService = Depends(get_service),
    current_user: dict = Depends(get_current_user)
):
    """POST /api/prompt-templates/{id}/archive"""
    try:
        template = service.archive_template(template_id)
        return _to_response(template)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    service: PromptTemplateService = Depends(get_service),
    current_user: dict = Depends(get_current_user)
):
    """DELETE /api/prompt-templates/{id}"""
    success = service.delete_template(template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template mit ID {template_id} nicht gefunden"
        )
    return None


# === HELPER FUNCTIONS ===

def _to_response(template) -> PromptTemplateResponse:
    """Convert Domain Entity to Response Schema"""
    return PromptTemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        prompt_text=template.prompt_text,
        system_instructions=template.system_instructions,
        document_type_id=template.document_type_id,
        ai_model=template.ai_model,
        temperature=template.temperature,
        max_tokens=template.max_tokens,
        top_p=template.top_p,
        detail_level=template.detail_level,
        status=template.status.value if hasattr(template.status, 'value') else template.status,
        version=template.version,
        tested_successfully=template.tested_successfully,
        success_count=template.success_count,
        last_used_at=template.last_used_at.isoformat() if template.last_used_at else None,
        tags=template.tags,
        example_input=template.example_input,
        example_output=template.example_output,
        created_at=template.created_at.isoformat() if template.created_at else "",
        updated_at=template.updated_at.isoformat() if template.updated_at else ""
    )

