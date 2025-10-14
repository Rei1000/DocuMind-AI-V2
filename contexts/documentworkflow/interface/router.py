"""
Document Workflow FastAPI Router.

API Endpoints für Document Workflow Management mit role-based permissions.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.app.database import get_db
from contexts.accesscontrol.interface.guard_router import get_current_user

from ..domain.entities import WorkflowStatus, CommentType
from ..application.use_cases import (
    ChangeDocumentStatusUseCase,
    AddDocumentCommentUseCase,
    GetDocumentWorkflowUseCase,
    GetDocumentsByStatusUseCase
)
from ..infrastructure.repositories import (
    SQLAlchemyDocumentWorkflowRepository,
    SQLAlchemyStatusChangeRepository,
    SQLAlchemyDocumentCommentRepository
)

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class StatusChangeRequest(BaseModel):
    """Request für Status-Änderung."""
    new_status: str = Field(..., description="Neuer Status (draft, reviewed, approved, rejected)")
    reason: Optional[str] = Field(None, description="Grund für die Änderung")
    comment: Optional[str] = Field(None, description="Optionaler Kommentar")

class CommentCreateRequest(BaseModel):
    """Request für neuen Kommentar."""
    comment_text: str = Field(..., min_length=1, max_length=2000, description="Kommentar-Text")
    comment_type: str = Field(default="general", description="Kommentar-Typ (general, review, rejection, approval)")
    page_number: Optional[int] = Field(None, description="Bezieht sich auf bestimmte Seite")

class WorkflowStatusResponse(BaseModel):
    """Response für Workflow-Status."""
    document_id: int
    current_status: str
    allowed_transitions: List[str]
    can_comment: bool
    user_permissions: Dict[str, Any]

class StatusChangeResponse(BaseModel):
    """Response für Status-Änderung."""
    id: int
    document_id: int
    from_status: Optional[str]
    to_status: str
    changed_by_user_id: int
    changed_at: str
    change_reason: Optional[str]
    comment: Optional[str]

class CommentResponse(BaseModel):
    """Response für Kommentar."""
    id: int
    document_id: int
    comment_text: str
    comment_type: str
    page_number: Optional[int]
    created_by_user_id: int
    created_at: str
    status_change_id: Optional[int]

class WorkflowInfoResponse(BaseModel):
    """Vollständige Workflow-Information."""
    workflow: WorkflowStatusResponse
    history: List[StatusChangeResponse]
    comments: List[CommentResponse]

class DocumentListResponse(BaseModel):
    """Response für Dokumentenliste."""
    documents: List[Dict[str, Any]]
    total_count: int
    status_filter: Optional[str]

# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(prefix="/api/document-workflow", tags=["Document Workflow"])

def get_workflow_repositories(db: Session = Depends(get_db)):
    """Dependency Injection für Repositories."""
    workflow_repo = SQLAlchemyDocumentWorkflowRepository(db)
    status_change_repo = SQLAlchemyStatusChangeRepository(db)
    comment_repo = SQLAlchemyDocumentCommentRepository(db)
    return workflow_repo, status_change_repo, comment_repo

def get_user_permissions(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Extrahiere User-Permissions aus JWT."""
    return {
        "user_id": current_user.get("user_id"),
        "user_level": current_user.get("level", 1),
        "interest_groups": current_user.get("interest_groups", [])
    }

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.put("/documents/{document_id}/status")
async def change_document_status(
    document_id: int,
    request: StatusChangeRequest,
    repos = Depends(get_workflow_repositories),
    user_perms = Depends(get_user_permissions)
):
    """
    Ändere Document Status.
    
    Prüft Berechtigungen und führt Status-Änderung mit Audit Trail durch.
    """
    workflow_repo, status_change_repo, comment_repo = repos
    
    # Validiere Status
    try:
        new_status = WorkflowStatus(request.new_status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {request.new_status}. Valid: draft, reviewed, approved, rejected"
        )
    
    # Hole Document Interest Groups (vereinfacht - sollte aus DB kommen)
    document_interest_groups = [1, 2, 3]  # TODO: Aus DB laden
    
    # Führe Use Case aus
    use_case = ChangeDocumentStatusUseCase(workflow_repo, status_change_repo, comment_repo)
    
    try:
        result = await use_case.execute(
            document_id=document_id,
            new_status=new_status,
            user_id=user_perms["user_id"],
            user_level=user_perms["user_level"],
            user_interest_groups=user_perms["interest_groups"],
            document_interest_groups=document_interest_groups,
            reason=request.reason,
            comment_text=request.comment
        )
        
        # Konvertiere zu Response
        return {
            "success": True,
            "message": f"Status changed to {new_status.value}",
            "status_change": {
                "id": result["status_change"].id,
                "from_status": result["status_change"].from_status.value if result["status_change"].from_status else None,
                "to_status": result["status_change"].to_status.value,
                "changed_at": result["status_change"].changed_at.isoformat(),
                "reason": result["status_change"].change_reason
            },
            "workflow": {
                "current_status": result["workflow"].current_status.value,
                "updated_at": result["workflow"].updated_at.isoformat()
            }
        }
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/documents/{document_id}/comments")
async def add_document_comment(
    document_id: int,
    request: CommentCreateRequest,
    repos = Depends(get_workflow_repositories),
    user_perms = Depends(get_user_permissions)
):
    """
    Füge Kommentar zu Dokument hinzu.
    
    Erlaubt Kommentare mit optionalem Seitenbezug.
    """
    workflow_repo, status_change_repo, comment_repo = repos
    
    # Validiere Comment Type
    try:
        comment_type = CommentType(request.comment_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid comment type: {request.comment_type}. Valid: general, review, rejection, approval"
        )
    
    # Hole Document Interest Groups (vereinfacht)
    document_interest_groups = [1, 2, 3]  # TODO: Aus DB laden
    
    # Führe Use Case aus
    use_case = AddDocumentCommentUseCase(comment_repo)
    
    try:
        comment = await use_case.execute(
            document_id=document_id,
            comment_text=request.comment_text,
            user_id=user_perms["user_id"],
            user_level=user_perms["user_level"],
            user_interest_groups=user_perms["interest_groups"],
            document_interest_groups=document_interest_groups,
            page_number=request.page_number,
            comment_type=comment_type
        )
        
        return CommentResponse(
            id=comment.id,
            document_id=comment.document_id,
            comment_text=comment.comment_text,
            comment_type=comment.comment_type.value,
            page_number=comment.page_number,
            created_by_user_id=comment.created_by_user_id,
            created_at=comment.created_at.isoformat(),
            status_change_id=comment.status_change_id
        )
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/documents/{document_id}")
async def get_document_workflow(
    document_id: int,
    repos = Depends(get_workflow_repositories),
    user_perms = Depends(get_user_permissions)
):
    """
    Hole Workflow-Informationen für ein Dokument.
    
    Inkludiert Status, History, Kommentare und erlaubte Aktionen.
    """
    workflow_repo, status_change_repo, comment_repo = repos
    
    # Hole Document Interest Groups (vereinfacht)
    document_interest_groups = [1, 2, 3]  # TODO: Aus DB laden
    
    # Führe Use Case aus
    use_case = GetDocumentWorkflowUseCase(workflow_repo, status_change_repo, comment_repo)
    
    try:
        result = await use_case.execute(
            document_id=document_id,
            user_id=user_perms["user_id"],
            user_level=user_perms["user_level"],
            user_interest_groups=user_perms["interest_groups"],
            document_interest_groups=document_interest_groups
        )
        
        # Konvertiere zu Response
        return WorkflowInfoResponse(
            workflow=WorkflowStatusResponse(
                document_id=document_id,
                current_status=result["current_status"].value,
                allowed_transitions=[s.value for s in result["allowed_transitions"]],
                can_comment=result["can_comment"],
                user_permissions=result["user_permissions"]
            ),
            history=[
                StatusChangeResponse(
                    id=change.id,
                    document_id=change.document_id,
                    from_status=change.from_status.value if change.from_status else None,
                    to_status=change.to_status.value,
                    changed_by_user_id=change.changed_by_user_id,
                    changed_at=change.changed_at.isoformat(),
                    change_reason=change.change_reason,
                    comment=change.comment
                ) for change in result["history"]
            ],
            comments=[
                CommentResponse(
                    id=comment.id,
                    document_id=comment.document_id,
                    comment_text=comment.comment_text,
                    comment_type=comment.comment_type.value,
                    page_number=comment.page_number,
                    created_by_user_id=comment.created_by_user_id,
                    created_at=comment.created_at.isoformat(),
                    status_change_id=comment.status_change_id
                ) for comment in result["comments"]
            ]
        )
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/documents")
async def get_documents_by_status(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    repos = Depends(get_workflow_repositories),
    user_perms = Depends(get_user_permissions)
):
    """
    Hole Dokumente nach Workflow-Status.
    
    Filtert nach User-Berechtigungen und Interest Groups.
    """
    workflow_repo, status_change_repo, comment_repo = repos
    
    # Validiere Status wenn angegeben
    workflow_status = None
    if status:
        try:
            workflow_status = WorkflowStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Valid: draft, reviewed, approved, rejected"
            )
    
    # Führe Use Case aus
    use_case = GetDocumentsByStatusUseCase(workflow_repo)
    
    try:
        documents = await use_case.execute(
            status=workflow_status,
            user_id=user_perms["user_id"],
            user_level=user_perms["user_level"],
            user_interest_groups=user_perms["interest_groups"],
            limit=limit,
            offset=offset
        )
        
        return DocumentListResponse(
            documents=documents,
            total_count=len(documents),
            status_filter=status
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/audit-trail/{document_id}")
async def get_audit_trail(
    document_id: int,
    limit: int = 50,
    repos = Depends(get_workflow_repositories),
    user_perms = Depends(get_user_permissions)
):
    """
    Hole Audit Trail für ein Dokument.
    
    Zeigt alle Status-Änderungen und Kommentare chronologisch.
    """
    workflow_repo, status_change_repo, comment_repo = repos
    
    try:
        # Hole Status Changes
        status_changes = await status_change_repo.get_by_document_id(document_id, limit)
        
        # Hole Kommentare
        comments = await comment_repo.get_by_document_id(document_id, limit=limit)
        
        return {
            "document_id": document_id,
            "status_changes": [
                StatusChangeResponse(
                    id=change.id,
                    document_id=change.document_id,
                    from_status=change.from_status.value if change.from_status else None,
                    to_status=change.to_status.value,
                    changed_by_user_id=change.changed_by_user_id,
                    changed_at=change.changed_at.isoformat(),
                    change_reason=change.change_reason,
                    comment=change.comment
                ) for change in status_changes
            ],
            "comments": [
                CommentResponse(
                    id=comment.id,
                    document_id=comment.document_id,
                    comment_text=comment.comment_text,
                    comment_type=comment.comment_type.value,
                    page_number=comment.page_number,
                    created_by_user_id=comment.created_by_user_id,
                    created_at=comment.created_at.isoformat(),
                    status_change_id=comment.status_change_id
                ) for comment in comments
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
