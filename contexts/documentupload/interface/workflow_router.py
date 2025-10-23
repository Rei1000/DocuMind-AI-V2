"""
Workflow Router für Document Upload Context.

FastAPI Router für Workflow-bezogene Endpoints:
- Status-Änderungen
- Workflow-Historie
- Permission-Checks
- Interest Groups Filter
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.app.database import get_db
from backend.app.models import User
from contexts.accesscontrol.interface.guard_router import get_current_user
from ..application.use_cases import (
    ChangeDocumentWorkflowStatusUseCase,
    GetWorkflowHistoryUseCase,
    GetDocumentsByWorkflowStatusUseCase
)
from ..infrastructure.repositories import (
    SQLAlchemyUploadRepository,
    SQLAlchemyWorkflowHistoryRepository,
    SQLAlchemyDocumentCommentRepository
)
from ..infrastructure.permission_service import SQLAlchemyWorkflowPermissionService
from .schemas import (
    ChangeWorkflowStatusRequest,
    ChangeWorkflowStatusResponse,
    WorkflowStatusChangeSchema,
    AllowedTransitionsResponse,
    WorkflowDocumentSchema
)

router = APIRouter(prefix="/document-workflow", tags=["Document Workflow"])


@router.post("/change-status", response_model=ChangeWorkflowStatusResponse)
async def change_workflow_status(
    request: ChangeWorkflowStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ändere Workflow-Status eines Dokuments.
    
    Args:
        request: Status-Änderungs-Request
        db: Database Session
        current_user: Aktueller User (für Permission-Check)
        
    Returns:
        ChangeWorkflowStatusResponse mit Ergebnis
        
    Raises:
        HTTPException: Bei Fehlern (404, 403, 400)
    """
    try:
        # Repositories initialisieren
        upload_repo = SQLAlchemyUploadRepository(db)
        history_repo = SQLAlchemyWorkflowHistoryRepository(db)
        permission_service = SQLAlchemyWorkflowPermissionService(db)
        
        # Use Case ausführen
        use_case = ChangeDocumentWorkflowStatusUseCase(
            upload_repository=upload_repo,
            history_repository=history_repo,
            permission_service=permission_service
        )
        
        # Status ändern
        updated_document = await use_case.execute(
            document_id=request.document_id,
            new_status=request.new_status,
            user_id=current_user.id,
            reason=request.reason
        )
        
        return ChangeWorkflowStatusResponse(
            success=True,
            message=f"Status erfolgreich geändert zu {request.new_status}",
            document_id=request.document_id,
            new_status=request.new_status,
            changed_by=current_user.full_name,
            changed_at=datetime.utcnow()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/status/{status}", response_model=List[WorkflowDocumentSchema])
async def get_documents_by_status(
    status: str,
    interest_group_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Hole Dokumente nach Workflow-Status.
    
    Args:
        status: Workflow-Status (draft, reviewed, approved, rejected)
        interest_group_ids: Optional filter by Interest Groups
        db: Database Session
        current_user: Aktueller User (für Permission-Check)
        
    Returns:
        Liste der Dokumente mit dem Status
        
    Raises:
        HTTPException: Bei ungültigem Status (400)
    """
    try:
        # Validiere Status
        valid_statuses = ["draft", "reviewed", "approved", "rejected"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Must be one of: {valid_statuses}"
            )
        
        # Repositories initialisieren
        upload_repo = SQLAlchemyUploadRepository(db)
        
        # Use Case ausführen
        use_case = GetDocumentsByWorkflowStatusUseCase(upload_repo)
        
        # Dokumente laden
        documents = await use_case.execute(
            status=status,
            interest_group_ids=interest_group_ids
        )
        
        # Konvertiere zu Response Schema
        return [
            WorkflowDocumentSchema(
                id=doc.id,
                filename=doc.metadata.filename,
                version=doc.metadata.version,
                workflow_status=doc.workflow_status.value,
                uploaded_at=doc.uploaded_at.isoformat(),
                interest_group_ids=doc.interest_group_ids,
                document_type=doc.document_type_id,
                qm_chapter=doc.metadata.qm_chapter,
                preview_url=f"/api/documents/{doc.id}/preview"
            )
            for doc in documents
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/history/{document_id}", response_model=List[WorkflowStatusChangeSchema])
async def get_workflow_history(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Hole Workflow-Historie eines Dokuments.
    
    Args:
        document_id: Dokument ID
        db: Database Session
        current_user: Aktueller User
        
    Returns:
        Liste der Status-Änderungen (chronologisch sortiert)
        
    Raises:
        HTTPException: Bei Fehlern (404, 500)
    """
    try:
        # Repository initialisieren
        history_repo = SQLAlchemyWorkflowHistoryRepository(db)
        
        # Use Case ausführen
        use_case = GetWorkflowHistoryUseCase(history_repo)
        
        # Historie laden
        history = await use_case.execute(document_id)
        
        # Konvertiere zu Response Schema
        return [
            WorkflowStatusChangeSchema(
                id=change.id,
                document_id=change.document_id,
                from_status=change.from_status.value,
                to_status=change.to_status.value,
                changed_by_user_id=change.changed_by_user_id,
                reason=change.reason,
                created_at=change.created_at
            )
            for change in history
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/allowed-transitions/{document_id}", response_model=AllowedTransitionsResponse)
async def get_allowed_transitions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Hole erlaubte Status-Transitions für ein Dokument.
    
    Args:
        document_id: Dokument ID
        db: Database Session
        current_user: Aktueller User
        
    Returns:
        AllowedTransitionsResponse mit erlaubten Transitions
        
    Raises:
        HTTPException: Bei Fehlern (404, 500)
    """
    try:
        # Repositories initialisieren
        upload_repo = SQLAlchemyUploadRepository(db)
        permission_service = SQLAlchemyWorkflowPermissionService(db)
        
        # Dokument laden
        document = await upload_repo.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # User Level ermitteln
        user_level = await permission_service.get_user_level(current_user.id)
        
        # Erlaubte Transitions ermitteln
        allowed_transitions = []
        current_status = document.workflow_status.value
        
        # Alle möglichen Transitions prüfen
        possible_transitions = {
            "draft": ["reviewed"],
            "reviewed": ["approved", "rejected"],
            "rejected": ["draft"],
            "approved": []  # Approved ist final
        }
        
        for target_status in possible_transitions.get(current_status, []):
            can_change = await permission_service.can_change_status(
                current_user.id, document.workflow_status, target_status
            )
            if can_change:
                allowed_transitions.append(target_status)
        
        return AllowedTransitionsResponse(
            current_status=current_status,
            allowed_transitions=allowed_transitions,
            user_level=user_level
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{document_id}", response_model=WorkflowDocumentSchema)
async def get_document_workflow_info(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Hole Workflow-Info für ein einzelnes Dokument.
    
    Args:
        document_id: Dokument ID
        db: Database Session
        current_user: Aktueller User
        
    Returns:
        WorkflowDocumentSchema mit Dokument-Info
        
    Raises:
        HTTPException: Bei Fehlern (404, 500)
    """
    try:
        # Repository initialisieren
        upload_repo = SQLAlchemyUploadRepository(db)
        
        # Dokument laden
        document = await upload_repo.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Konvertiere zu Response Schema
        return WorkflowDocumentSchema(
            id=document.id,
            filename=document.metadata.filename,
            version=document.metadata.version,
            workflow_status=document.workflow_status.value,
            uploaded_at=document.uploaded_at.isoformat(),
            interest_group_ids=document.interest_group_ids,
            document_type=document.document_type_id,
            qm_chapter=document.metadata.qm_chapter,
            preview_url=f"/api/documents/{document.id}/preview"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
