"""
AI Playground FastAPI Router

External Interface für AI Playground.
Nur für QMS Admin zugänglich!
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from pydantic import BaseModel, Field
import base64

from contexts.aiplayground.application.services import AIPlaygroundService
from contexts.aiplayground.domain.value_objects import ModelConfig

# Import Admin-Check Dependency
from contexts.accesscontrol.interface.guard_router import get_current_user


# ===== PYDANTIC SCHEMAS =====

class ModelConfigSchema(BaseModel):
    """Schema: Model Configuration"""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, gt=0, le=200000)  # Erhöht für GPT-5 Mini (128k)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=None, ge=1)
    detail_level: str = Field(default="high", pattern="^(high|low)$", description="Bilderkennung Detail-Level (nur OpenAI)")


class TestModelRequest(BaseModel):
    """Schema: Test Model Request"""
    model_id: str = Field(..., description="Model ID (z.B. 'gpt-4')")
    prompt: str = Field(..., min_length=1, description="User Prompt")
    config: Optional[ModelConfigSchema] = None
    image_data: Optional[str] = Field(None, description="Base64-encoded image data")


class CompareModelsRequest(BaseModel):
    """Schema: Compare Models Request"""
    model_ids: List[str] = Field(..., min_items=2, max_items=5, description="Liste von Model IDs")
    prompt: str = Field(..., min_length=1, description="User Prompt")
    config: Optional[ModelConfigSchema] = None
    image_data: Optional[str] = Field(None, description="Base64-encoded image data")


class TestResultSchema(BaseModel):
    """Schema: Test Result Response"""
    model_name: str
    provider: str
    prompt: str
    response: str
    tokens_sent: int
    tokens_received: int
    total_tokens: int
    response_time: float
    response_time_ms: float
    success: bool
    error_message: Optional[str] = None
    timestamp: Optional[str] = None
    text_tokens: Optional[int] = None  # Token-Breakdown für Transparenz
    image_tokens: Optional[int] = None


class ConnectionTestSchema(BaseModel):
    """Schema: Connection Test Response"""
    provider: str
    model_name: str
    success: bool
    latency: Optional[float] = None
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: Optional[str] = None


class ModelSchema(BaseModel):
    """Schema: Available Model"""
    id: str
    name: str
    provider: str
    model_id: str
    description: str
    max_tokens_supported: int
    is_configured: bool


# ===== ROUTER =====

router = APIRouter(prefix="/api/ai-playground", tags=["AI Playground"])


# ===== HELPER FUNCTIONS =====

def check_admin_permission(current_user: dict = Depends(get_current_user)):
    """
    Dependency: Check if user is QMS Admin
    
    Raises:
        HTTPException 403: Wenn User kein Admin ist
    """
    # Check if user is qms.admin
    email = current_user.get("email", "")
    
    # Admin check: qms.admin or admin@documind.ai
    is_admin = (
        email == "qms.admin@company.com" or
        email == "admin@documind.ai" or
        "system_administration" in current_user.get("permissions", [])
    )
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Zugriff verweigert. Nur QMS Admin hat Zugang zum AI Playground."
        )
    
    return current_user


def get_service() -> AIPlaygroundService:
    """Dependency: Get AI Playground Service"""
    return AIPlaygroundService()


def convert_config(schema: Optional[ModelConfigSchema]) -> Optional[ModelConfig]:
    """Convert Pydantic Schema to Domain Value Object"""
    if schema is None:
        return None
    
    return ModelConfig(
        temperature=schema.temperature,
        max_tokens=schema.max_tokens,
        top_p=schema.top_p,
        top_k=schema.top_k,
        detail_level=schema.detail_level  # ← Jetzt übergeben!
    )


# ===== ENDPOINTS =====

@router.get("/models", response_model=List[ModelSchema])
async def list_models(
    _: dict = Depends(check_admin_permission),
    service: AIPlaygroundService = Depends(get_service)
):
    """
    GET /api/ai-playground/models
    
    Liste aller verfügbaren AI-Modelle mit Status.
    
    Returns:
        Liste von verfügbaren Modellen
    
    Permissions:
        Nur QMS Admin
    """
    models = service.get_available_models()
    return models


@router.post("/test-connection", response_model=ConnectionTestSchema)
async def test_connection(
    model_id: str,
    _: dict = Depends(check_admin_permission),
    service: AIPlaygroundService = Depends(get_service)
):
    """
    POST /api/ai-playground/test-connection
    
    Teste Verbindung zu AI-Provider für ein Modell.
    
    Args:
        model_id: Model ID (z.B. "gpt-4")
    
    Returns:
        Connection Test Result
    
    Permissions:
        Nur QMS Admin
    """
    result = await service.test_connection(model_id)
    return result.to_dict()


@router.post("/test", response_model=TestResultSchema)
async def test_model(
    request: TestModelRequest,
    _: dict = Depends(check_admin_permission),
    service: AIPlaygroundService = Depends(get_service)
):
    """
    POST /api/ai-playground/test
    
    Teste AI-Modell mit Prompt (und optional Bild).
    
    Args:
        request: Test Request mit model_id, prompt, config, image_data (optional)
    
    Returns:
        Test Result mit Response und Metrics
    
    Permissions:
        Nur QMS Admin
    """
    config = convert_config(request.config)
    
    result = await service.test_model(
        model_id=request.model_id,
        prompt=request.prompt,
        config=config,
        image_data=request.image_data
    )
    
    return result.to_dict()


@router.post("/compare", response_model=List[TestResultSchema])
async def compare_models(
    request: CompareModelsRequest,
    _: dict = Depends(check_admin_permission),
    service: AIPlaygroundService = Depends(get_service)
):
    """
    POST /api/ai-playground/compare
    
    Vergleiche mehrere AI-Modelle mit demselben Prompt (und optional Bild).
    
    Args:
        request: Compare Request mit model_ids, prompt, config, image_data (optional)
    
    Returns:
        Liste von Test Results (eins pro Modell)
    
    Permissions:
        Nur QMS Admin
    """
    if len(request.model_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mindestens 2 Modelle erforderlich für Vergleich"
        )
    
    if len(request.model_ids) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximal 5 Modelle können gleichzeitig verglichen werden"
        )
    
    config = convert_config(request.config)
    
    results = await service.compare_models(
        model_ids=request.model_ids,
        prompt=request.prompt,
        config=config,
        image_data=request.image_data
    )
    
    return [r.to_dict() for r in results]


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    _: dict = Depends(check_admin_permission)
):
    """
    POST /api/ai-playground/upload-image
    
    Upload ein Bild/Dokument und konvertiere zu Base64.
    
    Args:
        file: Hochgeladene Datei (JPG, PNG, PDF, etc.)
    
    Returns:
        Base64-encoded Bild-Daten und Metadaten
    
    Permissions:
        Nur QMS Admin
    """
    # Validiere Dateiformat
    allowed_types = [
        "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp",
        "application/pdf"
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dateiformat nicht unterstützt: {file.content_type}. Erlaubt: JPG, PNG, GIF, WEBP, PDF"
        )
    
    # Lese Datei
    content = await file.read()
    
    # Validiere Größe (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Datei zu groß. Maximum: 10MB, Aktuell: {len(content) / 1024 / 1024:.2f}MB"
        )
    
    # Konvertiere zu Base64
    base64_data = base64.b64encode(content).decode('utf-8')
    
    return {
        "success": True,
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(content),
        "size_mb": round(len(content) / 1024 / 1024, 2),
        "base64_data": base64_data
    }


@router.get("/health")
async def health_check(
    _: dict = Depends(check_admin_permission)
):
    """
    GET /api/ai-playground/health
    
    Health Check für AI Playground
    
    Permissions:
        Nur QMS Admin
    """
    return {
        "status": "healthy",
        "service": "AI Playground",
        "version": "1.0.0"
    }

