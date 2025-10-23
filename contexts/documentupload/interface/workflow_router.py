"""
Workflow Router für Document Upload Context

FastAPI Router für Workflow-bezogene Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.database import get_db
from ...accesscontrol.interface.guard_router import get_current_user
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
from ..infrastructure.permission_service import WorkflowPermissionServiceImpl
from .schemas import (
    ChangeWorkflowStatusRequest,
    ChangeWorkflowStatusResponse,
    WorkflowStatusChangeSchema,
    DocumentCommentSchema,
    AllowedTransitionsResponse
)
from ..domain.value_objects import WorkflowStatus

router = APIRouter(prefix="/api/document-workflow", tags=["Document Workflow"])


# Dependency Injection
def get_upload_repository(db: Session = Depends(get_db)):
    return SQLAlchemyUploadRepository(db)


def get_workflow_history_repository(db: Session = Depends(get_db)):
    return SQLAlchemyWorkflowHistoryRepository(db)


def get_document_comment_repository(db: Session = Depends(get_db)):
    return SQLAlchemyDocumentCommentRepository(db)


def get_permission_service(db: Session = Depends(get_db)):
    return WorkflowPermissionServiceImpl(db)


def get_event_publisher():
    # TODO: Implement real event publisher
    from unittest.mock import Mock
    return Mock()


@router.post("/change-status", response_model=ChangeWorkflowStatusResponse)
async def change_document_status(
    request: ChangeWorkflowStatusRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    upload_repo=Depends(get_upload_repository),
    workflow_history_repo=Depends(get_workflow_history_repository),
    comment_repo=Depends(get_document_comment_repository),
    permission_service=Depends(get_permission_service),
    event_publisher=Depends(get_event_publisher)
):
    """
    Ändere Dokument-Workflow-Status.
    
    Permissions: Level 3+ (je nach Transition)
    """
    try:
        use_case = ChangeDocumentWorkflowStatusUseCase(
            upload_repository=upload_repo,
            workflow_history_repository=workflow_history_repo,
            document_comment_repository=comment_repo,
            permission_service=permission_service,
            event_publisher=event_publisher
        )
        
        updated_document = await use_case.execute(
            document_id=request.document_id,
            new_status=WorkflowStatus(request.new_status),
            user_id=request.user_id,
            reason=request.reason,
            comment=request.comment
        )
        
        return ChangeWorkflowStatusResponse(
            success=True,
            message="Status erfolgreich geändert",
            document_id=updated_document.id,
            new_status=updated_document.workflow_status.value
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/status/{status}", response_model=List[dict])
async def get_documents_by_status(
    status: str,
    user_id: int,
    interest_group_ids: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    upload_repo=Depends(get_upload_repository),
    permission_service=Depends(get_permission_service)
):
    """
    Hole Dokumente nach Workflow-Status.
    
    Query: ?interest_group_ids=1,2
    Permissions: Level 2+
    """
    try:
        # Parse interest group IDs
        group_ids = None
        if interest_group_ids:
            group_ids = [int(id.strip()) for id in interest_group_ids.split(",")]
        
        use_case = GetDocumentsByWorkflowStatusUseCase(
            upload_repository=upload_repo,
            permission_service=permission_service
        )
        
        documents = await use_case.execute(
            status=WorkflowStatus(status),
            user_id=user_id,
            interest_group_ids=group_ids
        )
        
        # Convert to dict format for JSON response
        return [
            {
                "id": doc.id,
                "filename": doc.metadata.original_filename,
                "version": doc.metadata.version,
                "workflow_status": doc.workflow_status.value,
                "uploaded_at": doc.uploaded_at.isoformat(),
                "interest_group_ids": doc.interest_group_ids
            }
            for doc in documents
        ]
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/history/{document_id}", response_model=List[WorkflowStatusChangeSchema])
async def get_workflow_history(
    document_id: int,
    user_id: int,
    workflow_history_repo=Depends(get_workflow_history_repository),
    permission_service=Depends(get_permission_service)
):
    """
    Hole Workflow-Historie für ein Dokument.
    
    Permissions: Level 2+ (nur eigene Groups)
    """
    try:
        use_case = GetWorkflowHistoryUseCase(
            workflow_history_repository=workflow_history_repo,
            permission_service=permission_service
        )
        
        history = await use_case.execute(document_id, user_id)
        
        return [
            WorkflowStatusChangeSchema(
                id=change.id,
                upload_document_id=change.upload_document_id,
                from_status=change.from_status.value if change.from_status else None,
                to_status=change.to_status.value,
                changed_by_user_id=change.changed_by_user_id,
                changed_at=change.changed_at.isoformat(),
                change_reason=change.change_reason,
                comment=change.comment
            )
            for change in history
        ]
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/allowed-transitions/{document_id}", response_model=AllowedTransitionsResponse)
async def get_allowed_transitions(
    document_id: int,
    user_id: int,
    upload_repo=Depends(get_upload_repository),
    permission_service=Depends(get_permission_service)
):
    """
    Hole erlaubte Workflow-Transitions für ein Dokument.
    
    Permissions: Level 2+
    Returns: Liste erlaubter Ziel-Status
    """
    try:
        # Lade Dokument
        document = await upload_repo.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Hole erlaubte Transitions
        allowed_transitions = permission_service.get_allowed_transitions(
            user_id, document.workflow_status
        )
        
        return AllowedTransitionsResponse(
            document_id=document_id,
            current_status=document.workflow_status.value,
            allowed_transitions=[status.value for status in allowed_transitions]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
