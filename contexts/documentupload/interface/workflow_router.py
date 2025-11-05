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
from .schemas import (
    ChangeWorkflowStatusRequest,
    ChangeWorkflowStatusResponse,
    GetDocumentsByStatusResponse,
    WorkflowDocumentSchema,
    WorkflowStatusChangeSchema,
    WorkflowInfoResponse,
    RejectDocumentRequest,
    RejectDocumentResponse,
    SoftDeleteDocumentRequest,
    SoftDeleteDocumentResponse,
    ArchiveDocumentRequest,
    ArchiveDocumentResponse,
    HardDeleteDocumentRequest,
    HardDeleteDocumentResponse,
    UploadedDocumentSchema
)
from ..application.use_cases import (
    ChangeDocumentWorkflowStatusUseCase,
    GetWorkflowHistoryUseCase,
    GetDocumentsByWorkflowStatusUseCase,
    SoftDeleteDocumentUseCase,
    ArchiveDocumentUseCase,
    GetArchivedDocumentsUseCase,
    HardDeleteDocumentUseCase
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
    WorkflowDocumentSchema,
    GetDocumentsByStatusResponse
)

router = APIRouter(prefix="/api/document-workflow", tags=["Document Workflow"])

# NEU Phase 5: Event Publisher Dependency Injection
_event_publisher = None

def get_event_publisher():
    """
    Dependency für Event Publisher.
    
    NEU Phase 5: Singleton Pattern für Event Publisher mit Handler Registration.
    """
    global _event_publisher
    if _event_publisher is None:
        from contexts.documentupload.infrastructure.event_publisher import (
            InMemoryEventPublisher
        )
        from backend.app.events import setup_event_handlers
        
        _event_publisher = InMemoryEventPublisher()
        setup_event_handlers(_event_publisher)
    
    return _event_publisher


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
            user_id=current_user.get('id', 1),  # Fallback to user 1 if not found
            reason=request.reason
        )
        
        return ChangeWorkflowStatusResponse(
            success=True,
            message=f"Status erfolgreich geändert zu {request.new_status}",
            document_id=request.document_id,
            new_status=request.new_status,
            changed_by=current_user.get('full_name', current_user.get('email', 'Unknown User')),
            changed_at=datetime.utcnow()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/reject", response_model=RejectDocumentResponse)
async def reject_document(
    request: RejectDocumentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    event_publisher = Depends(get_event_publisher)  # NEU Phase 5
):
    """
    Weise Dokument zurück (Rejection mit Kommentar-Pflicht).
    
    NEU Phase 3: Rejection erfordert Kommentar (MUSS).
    Nach Rejection verschwindet Dokument aus Kanban, bleibt in Tabelle sichtbar.
    
    Args:
        request: Rejection-Request mit document_id und rejection_reason
        db: Database Session
        current_user: Aktueller User (für Permission-Check)
        
    Returns:
        RejectDocumentResponse mit Ergebnis
        
    Raises:
        HTTPException: Bei Fehlern (404, 403, 400)
    """
    from ..infrastructure.repositories import SQLAlchemyUploadRepository
    from ..infrastructure.document_comment_repository import SQLAlchemyDocumentCommentRepository
    from ..application.use_cases import RejectDocumentUseCase
    
    try:
        user_id = current_user.get('id', 1) if isinstance(current_user, dict) else getattr(current_user, 'id', 1)
        user_name = current_user.get('full_name', current_user.get('email', 'Unknown User')) if isinstance(current_user, dict) else getattr(current_user, 'email', 'Unknown User')
        
        # Repositories initialisieren
        upload_repo = SQLAlchemyUploadRepository(db)
        comment_repo = SQLAlchemyDocumentCommentRepository(db)
        
        # Use Case ausführen
        use_case = RejectDocumentUseCase(
            upload_repository=upload_repo,
            comment_repository=comment_repo,
            event_publisher=event_publisher  # NEU Phase 5
        )
        
        # Dokument zurückweisen
        updated_document = await use_case.execute(
            document_id=request.document_id,
            rejected_by_user_id=user_id,
            rejection_reason=request.rejection_reason
        )
        
        return RejectDocumentResponse(
            success=True,
            message="Dokument erfolgreich zurückgewiesen",
            document_id=request.document_id,
            new_status="rejected",
            rejected_by=user_name,
            rejected_at=datetime.utcnow()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/soft-delete", response_model=SoftDeleteDocumentResponse)
async def soft_delete_document(
    request: SoftDeleteDocumentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    event_publisher = Depends(get_event_publisher)  # NEU Phase 5
):
    """
    Lösche Dokument (Soft Delete).
    
    NEU Phase 1.3: Soft Delete statt Hard Delete.
    Dokument bleibt in DB für Audit, wird aber als gelöscht markiert.
    
    Args:
        request: Soft Delete Request mit document_id und deletion_reason
        db: Database Session
        current_user: Aktueller User (für Permission-Check)
        
    Returns:
        SoftDeleteDocumentResponse mit aktualisiertem Dokument
        
    Raises:
        HTTPException: Bei Fehlern (404, 403, 400)
    """
    from ..infrastructure.repositories import SQLAlchemyUploadRepository
    from ..application.use_cases import SoftDeleteDocumentUseCase
    
    try:
        user_id = current_user.get('id', 1) if isinstance(current_user, dict) else getattr(current_user, 'id', 1)
        
        # Repositories initialisieren
        upload_repo = SQLAlchemyUploadRepository(db)
        
        # Use Case ausführen
        use_case = SoftDeleteDocumentUseCase(
            upload_repository=upload_repo,
            event_publisher=event_publisher  # NEU Phase 5
        )
        
        # Dokument soft-deleten
        updated_document = await use_case.execute(
            document_id=request.document_id,
            deleted_by_user_id=user_id,
            reason=request.deletion_reason
        )
        
        # Konvertiere zu Schema
        from ..interface.schemas import UploadedDocumentSchema
        from contexts.documenttypes.infrastructure.repositories import SQLAlchemyDocumentTypeRepository
        
        # Lade Document Type Name
        doc_type_repo = SQLAlchemyDocumentTypeRepository(db)
        doc_type_name = None
        if updated_document.document_type_id:
            doc_type = doc_type_repo.get_by_id(updated_document.document_type_id)  # FIX: Nicht async, kein await
            if doc_type:
                doc_type_name = doc_type.name
        
        # Lade User Name
        from backend.app.models import User as UserModel
        user = db.query(UserModel).filter(UserModel.id == updated_document.uploaded_by_user_id).first()
        uploaded_by_user_name = user.email if user else None
        
        document_schema = UploadedDocumentSchema(
            id=updated_document.id,
            filename=updated_document.metadata.filename,
            original_filename=updated_document.metadata.original_filename,
            file_size_bytes=updated_document.file_size_bytes,
            file_type=updated_document.file_type.value,
            document_type_id=updated_document.document_type_id,
            qm_chapter=updated_document.metadata.qm_chapter,
            version=updated_document.metadata.version or "",
            page_count=updated_document.page_count,
            uploaded_by_user_id=updated_document.uploaded_by_user_id,
            uploaded_by_user_name=uploaded_by_user_name,
            uploaded_at=updated_document.uploaded_at,
            file_path=str(updated_document.file_path),
            processing_method=updated_document.processing_method.value,
            processing_status=updated_document.processing_status.value,
            workflow_status=updated_document.workflow_status.value,
            document_type_name=doc_type_name,
            file_hash=updated_document.file_hash.value if updated_document.file_hash else None,
            is_duplicate=updated_document.is_duplicate,
            duplicate_of_document_id=updated_document.duplicate_of_document_id,
            document_series_id=updated_document.document_series_id,
            parent_document_id=updated_document.parent_document_id,
            is_current_version=updated_document.is_current_version,
            deleted_at=updated_document.deleted_at,  # NEU Phase 1.3
            deleted_by_user_id=updated_document.deleted_by_user_id,  # NEU Phase 1.3
            deletion_reason=updated_document.deletion_reason  # NEU Phase 1.3
        )
        
        return SoftDeleteDocumentResponse(
            success=True,
            message="Dokument erfolgreich gelöscht (Soft Delete)",
            document=document_schema
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/archive", response_model=ArchiveDocumentResponse)
async def archive_document(
    request: ArchiveDocumentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    event_publisher = Depends(get_event_publisher)  # NEU Phase 5
):
    """
    Archiviere Dokument.
    
    NEU Phase 1.4: Archivierung für alte Versionen oder nicht mehr benötigte Dokumente.
    Dokument bleibt in DB für Audit-Zwecke, wird aber aus aktivem Workflow entfernt.
    
    Args:
        request: Archive Request mit document_id und optionalem archive_reason
        db: Database Session
        current_user: Aktueller User (für Permission-Check)
        
    Returns:
        ArchiveDocumentResponse mit archiviertem Dokument
        
    Raises:
        404: Dokument nicht gefunden
        400: Ungültige Parameter
        500: Server-Fehler
    """
    try:
        user_id = current_user.get('id', 1) if isinstance(current_user, dict) else getattr(current_user, 'id', 1)
        
        # Use Case initialisieren
        upload_repo = SQLAlchemyUploadRepository(db)
        archive_use_case = ArchiveDocumentUseCase(
            upload_repository=upload_repo,
            event_publisher=event_publisher  # NEU Phase 5
        )
        
        # Dokument archivieren
        document = await archive_use_case.execute(
            document_id=request.document_id,
            archived_by_user_id=user_id,
            reason=request.archive_reason
        )
        
        # Response Schema erstellen
        user_name = current_user.get('full_name', current_user.get('email', 'Unknown')) if isinstance(current_user, dict) else (current_user.full_name or current_user.email)
        
        return ArchiveDocumentResponse(
            success=True,
            message="Document archived successfully",
            document_id=document.id,
            new_status="archived",
            archived_by=user_name,
            archived_at=document.archived_at
        )
    except ValueError as e:
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Archivieren: {str(e)}")


@router.get("/status/{status}", response_model=GetDocumentsByStatusResponse)
async def get_documents_by_status(
    status: str,
    interest_group_ids: Optional[List[int]] = Query(None),
    document_type_id: Optional[int] = Query(None),
    exclude_rag_indexed: bool = Query(True, description="Wenn True, werden RAG-indexierte Dokumente ausgeschlossen (für Kanban-Workflow)"),  # NEU: Query-Parameter
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
        Wrapped Response mit Dokumenten-Liste
        
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
        
        # Konvertiere String zu WorkflowStatus Enum
        from ..domain.value_objects import WorkflowStatus
        workflow_status = WorkflowStatus(status)
        
        # Dokumente laden (exclude_rag_indexed wird vom Query-Parameter gesteuert)
        # NEU Phase 3: Rejected Dokumente für Kanban ausschließen
        exclude_rejected = exclude_rag_indexed  # Wenn Kanban (exclude_rag_indexed=True), dann auch rejected ausschließen
        documents = await use_case.execute(
            status=workflow_status,
            interest_group_ids=interest_group_ids,
            document_type_id=document_type_id,
            exclude_rag_indexed=exclude_rag_indexed,  # Query-Parameter: True für Kanban, False für Tabelle
            exclude_rejected=exclude_rejected  # NEU Phase 3: Rejected für Kanban ausschließen
        )
        
        # Lade Document Type Repository für Namen
        from contexts.documenttypes.infrastructure.repositories import SQLAlchemyDocumentTypeRepository
        doc_type_repo = SQLAlchemyDocumentTypeRepository(db)
        
        # Konvertiere zu Response Schema
        document_schemas = []
        for doc in documents:
            # Lade Document Type Name
            doc_type_name = None
            if doc.document_type_id:
                try:
                    doc_type = doc_type_repo.get_by_id(doc.document_type_id)
                    doc_type_name = doc_type.name if doc_type else None
                except:
                    doc_type_name = None
            
            # Lade Verantwortlicher User (letzter Status-Änderer)
            responsible_user_id = None
            responsible_user_name = None
            try:
                from contexts.documentupload.infrastructure.workflow_history_repository import SQLAlchemyWorkflowHistoryRepository
                history_repo = SQLAlchemyWorkflowHistoryRepository(db)
                latest_change = await history_repo.get_latest_by_document_id(doc.id)
                if latest_change:
                    responsible_user_id = latest_change.changed_by_user_id
                    # Lade User-Name
                    user = db.query(User).filter(User.id == responsible_user_id).first()
                    responsible_user_name = user.full_name if user else f"User {responsible_user_id}"
            except:
                pass
            
            # Lade Betroffene Abteilungen (aus Interest Groups)
            affected_departments = []
            try:
                from contexts.interestgroups.infrastructure.repositories import SQLAlchemyInterestGroupRepository
                ig_repo = SQLAlchemyInterestGroupRepository(db)
                for ig_id in doc.interest_group_ids:
                    ig = ig_repo.get_by_id(ig_id)
                    if ig:
                        affected_departments.append(ig.name)
            except:
                pass
            
            # NEU: Lade RAG Indexierungs-Status (effizient für alle Dokumente)
            is_indexed = None
            indexed_at = None
            try:
                from contexts.ragintegration.infrastructure.repositories import SQLAlchemyIndexedDocumentRepository
                rag_repo = SQLAlchemyIndexedDocumentRepository(db)
                indexed_doc = rag_repo.get_by_upload_document_id(doc.id)
                if indexed_doc:
                    is_indexed = True
                    indexed_at = indexed_doc.indexed_at.isoformat() if indexed_doc.indexed_at else None
                else:
                    is_indexed = False
            except:
                # Bei Fehler: Index-Status bleibt None (optional)
                pass
            
            # NEU: Duplikat-Felder (Phase 1.1) - Berechnung VOR Funktionsaufruf
            # WICHTIG: Sicherstellen dass is_duplicate ein Boolean ist (nicht String/None)
            is_duplicate_raw = getattr(doc, 'is_duplicate', False)
            duplicate_of_id_raw = getattr(doc, 'duplicate_of_document_id', None)
            
            # Konvertiere zu Boolean (SQLite gibt manchmal Integer 0/1 zurück)
            # WICHTIG: bool(0) = False, bool(1) = True
            is_duplicate_value = bool(is_duplicate_raw) if is_duplicate_raw is not None else False
            duplicate_of_document_id_value = int(duplicate_of_id_raw) if duplicate_of_id_raw else None
            
            # DEBUG: Logge für alle Dokumente
            print(f"[DEBUG] Document {doc.id}: is_duplicate_raw={is_duplicate_raw}, is_duplicate_value={is_duplicate_value}, duplicate_of={duplicate_of_document_id_value}")
            
            document_schemas.append(WorkflowDocumentSchema(
                id=doc.id,
                filename=doc.metadata.filename,
                original_filename=getattr(doc.metadata, 'original_filename', doc.metadata.filename),
                file_type=getattr(doc, 'file_type', 'unknown'),
                file_size_bytes=getattr(doc, 'file_size_bytes', 0),
                version=doc.metadata.version,
                workflow_status=doc.workflow_status.value,
                uploaded_at=doc.uploaded_at.isoformat(),
                interest_group_ids=getattr(doc, 'interest_group_ids', []),
                document_type=doc.document_type_id,
                document_type_name=doc_type_name,
                qm_chapter=doc.metadata.qm_chapter,
                page_count=len(doc.pages) if hasattr(doc, 'pages') and doc.pages else 0,
                preview_url=f"/api/documents/{doc.id}/preview",
                
                # NEU: RAG Indexierungs-Status
                is_indexed=is_indexed,
                indexed_at=indexed_at,
                
                # Verantwortlicher User & Betroffene Abteilungen
                responsible_user_id=responsible_user_id,
                responsible_user_name=responsible_user_name,
                affected_departments=affected_departments,
                
                # NEU: Duplikat-Felder (Phase 1.1)
                is_duplicate=is_duplicate_value,
                duplicate_of_document_id=duplicate_of_document_id_value,
            ))
        
        # Return wrapped response
        return GetDocumentsByStatusResponse(
            success=True,
            data={"documents": document_schemas}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{document_id}/allowed-transitions")
async def get_allowed_transitions(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Hole erlaubte Status-Transitions für ein Dokument.
    
    Args:
        document_id: ID des Dokuments
        current_user: Aktueller Benutzer
        db: Datenbank-Session
        
    Returns:
        Liste der erlaubten Status-Transitions
    """
    try:
        # QMS Admin (Level 5) kann alles
        if current_user.get('email') == 'qms.admin@company.com':
            return {
                "allowed_transitions": ["draft", "reviewed", "approved", "rejected"]
            }
        
        # TODO: Level-basierte Permissions implementieren
        # Für jetzt: Standard-User können nur draft -> reviewed
        return {"allowed_transitions": ["reviewed"]}
        
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
        # Debug: Prüfe direkt in der Datenbank
        from backend.app.models import DocumentStatusChange as DocumentStatusChangeModel
        status_changes = db.query(DocumentStatusChangeModel).filter(
            DocumentStatusChangeModel.upload_document_id == document_id
        ).order_by(DocumentStatusChangeModel.created_at.asc()).all()
        
        print(f"[DEBUG] Found {len(status_changes)} status changes for document {document_id}")
        for change in status_changes:
            print(f"[DEBUG] Status change: {change.from_status} -> {change.to_status} by user {change.changed_by_user_id}")
        
        # Konvertiere direkt zu Response Schema (ohne Use Case)
        result = []
        for change in status_changes:
            try:
                # Lade User-Namen für bessere Audit-Trail Anzeige
                user_name = f"User {change.changed_by_user_id}"  # Fallback
                try:
                    from backend.app.models import User
                    user = db.query(User).filter(User.id == change.changed_by_user_id).first()
                    if user:
                        user_name = user.email or user.full_name or f"User {change.changed_by_user_id}"
                        print(f"[DEBUG] Loaded user {change.changed_by_user_id}: {user_name}")
                    else:
                        print(f"[DEBUG] User {change.changed_by_user_id} not found in database")
                        user_name = f"User {change.changed_by_user_id}"  # Fallback wenn User nicht gefunden
                except Exception as e:
                    print(f"[DEBUG] Error loading user {change.changed_by_user_id}: {str(e)}")
                    user_name = f"User {change.changed_by_user_id}"  # Fallback bei Fehler
                
                result.append(WorkflowStatusChangeSchema(
                    id=change.id,
                    document_id=change.upload_document_id,
                    from_status=change.from_status,
                    to_status=change.to_status,
                    changed_by_user_id=change.changed_by_user_id,
                    changed_by_user_name=user_name,  # Neues Feld für Username
                    reason=change.change_reason,
                    created_at=change.created_at.isoformat() if change.created_at else ""
                ))
            except Exception as e:
                print(f"[DEBUG] Error converting change {change.id}: {str(e)}")
                continue
        
        print(f"[DEBUG] Returning {len(result)} status changes")
        return result
        
    except Exception as e:
        print(f"[DEBUG] Error in get_workflow_history: {str(e)}")
        import traceback
        traceback.print_exc()
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
        user_level = permission_service.get_user_level(current_user.id)
        
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
            can_change = permission_service.can_change_status(
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


@router.get("/archive", response_model=List[WorkflowDocumentSchema])
async def get_archived_documents(
    limit: int = Query(100, ge=1, le=500, description="Maximale Anzahl Ergebnisse"),
    offset: int = Query(0, ge=0, description="Offset für Pagination"),
    document_type_id: Optional[int] = Query(None, description="Filter nach Dokumenttyp"),
    deleted_before: Optional[datetime] = Query(None, description="Filter: gelöscht vor diesem Datum"),
    deleted_after: Optional[datetime] = Query(None, description="Filter: gelöscht nach diesem Datum"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Hole alle gelöschten Dokumente (Archiv).
    
    Nur Level 4+ (QM-Mitarbeiter) dürfen Archiv einsehen.
    """
    from ..infrastructure.repositories import SQLAlchemyUploadRepository
    
    try:
        # RBAC: Nur Level 4+ (QM-Mitarbeiter) ODER QMS Admin
        # DEBUG: Prüfe current_user Typ
        if isinstance(current_user, dict):
            user_level = current_user.get('user_level', 0)
            is_qms_admin = current_user.get('is_qms_admin', False)
        else:
            # User Model - extrahiere aus Attributen
            user_level = getattr(current_user, 'user_level', 0)
            is_qms_admin = getattr(current_user, 'is_qms_admin', False)
        
        # DEBUG: Log für Troubleshooting
        print(f"[DEBUG Archive] current_user type: {type(current_user)}, user_level: {user_level}, is_qms_admin: {is_qms_admin}")
        
        if user_level < 4 and not is_qms_admin:
            raise HTTPException(
                status_code=403,
                detail=f"Nur QM-Mitarbeiter (Level 4+) oder QMS Admins können Archiv einsehen (aktuell: Level {user_level}, Admin: {is_qms_admin})"
            )
        
        # Repositories initialisieren
        upload_repo = SQLAlchemyUploadRepository(db)
        
        # Use Case ausführen
        use_case = GetArchivedDocumentsUseCase(upload_repository=upload_repo)
        documents = await use_case.execute(
            limit=limit,
            offset=offset,
            document_type_id=document_type_id,
            deleted_before=deleted_before,
            deleted_after=deleted_after
        )
        
        # Konvertiere zu WorkflowDocumentSchema
        document_schemas = []
        for doc in documents:
            is_duplicate_raw = getattr(doc, 'is_duplicate', False)
            is_duplicate_value = bool(is_duplicate_raw) if is_duplicate_raw is not None else False
            duplicate_of_document_id_value = getattr(doc, 'duplicate_of_document_id', None) if is_duplicate_value else None
            
            # NEU: Lade document_type_name aus DocumentType Repository
            document_type_name = None
            if doc.document_type_id:
                try:
                    from contexts.documenttypes.infrastructure.repositories import SQLAlchemyDocumentTypeRepository
                    doc_type_repo = SQLAlchemyDocumentTypeRepository(db)
                    doc_type = doc_type_repo.get_by_id(doc.document_type_id)
                    document_type_name = doc_type.name if doc_type else None
                except Exception as e:
                    print(f"WARNING: Could not load document type name for document {doc.id}: {e}")
                    document_type_name = None
            
            # Konvertiere uploaded_at zu String (ISO Format)
            uploaded_at_str = doc.uploaded_at.isoformat() if isinstance(doc.uploaded_at, datetime) else str(doc.uploaded_at) if doc.uploaded_at else ""
            
            # Konvertiere processing_status zu String
            processing_status_str = None
            if doc.processing_status:
                if hasattr(doc.processing_status, 'value'):
                    processing_status_str = doc.processing_status.value
                else:
                    processing_status_str = str(doc.processing_status)
            
            document_schemas.append(WorkflowDocumentSchema(
                id=doc.id,
                original_filename=doc.metadata.original_filename if doc.metadata else getattr(doc, 'original_filename', 'Unknown'),
                filename=doc.metadata.filename if doc.metadata else getattr(doc, 'filename', 'Unknown'),  # NEU: filename ist auch required
                document_type=doc.document_type_id,  # WICHTIG: document_type (nicht document_type_id) im Schema
                document_type_name=document_type_name,  # NEU: Wird jetzt aus Repository geladen
                qm_chapter=doc.metadata.qm_chapter if doc.metadata else getattr(doc, 'qm_chapter', None),
                workflow_status=doc.workflow_status.value if hasattr(doc.workflow_status, 'value') else str(doc.workflow_status),
                uploaded_at=uploaded_at_str,  # WICHTIG: String erforderlich
                # uploaded_by_user_id ist NICHT in WorkflowDocumentSchema (nur in UploadedDocumentSchema)
                # processing_status ist NICHT in WorkflowDocumentSchema (nur in UploadedDocumentSchema)
                file_size_bytes=doc.file_size_bytes,
                file_type=doc.file_type.value if hasattr(doc.file_type, 'value') else str(doc.file_type) if doc.file_type else 'unknown',
                version=doc.metadata.version if doc.metadata else getattr(doc, 'version', 'v1.0'),
                interest_group_ids=[],  # WICHTIG: Required field, wird später geladen wenn nötig
                is_duplicate=is_duplicate_value,
                duplicate_of_document_id=duplicate_of_document_id_value,
                # deleted_at, deleted_by_user_id, deletion_reason sind NICHT in WorkflowDocumentSchema (nur in UploadedDocumentSchema)
                is_indexed=False,
                indexed_at=None
            ))
        
        return document_schemas
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{document_id}", response_model=WorkflowInfoResponse)
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
        return WorkflowInfoResponse(
            success=True,
            message="Workflow info loaded successfully",
            document_id=document.id,
            workflow={
                "current_status": document.workflow_status.value,
                "allowed_transitions": ["reviewed", "approved", "rejected"]  # TODO: Implement proper transition logic
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# WICHTIG: Die /archive Route wurde nach oben verschoben (bei Zeile 715, vor /{document_id})
# damit FastAPI die spezifische Route zuerst matched. Diese Duplikat-Definition wurde entfernt.


@router.delete("/hard-delete/{document_id}", response_model=HardDeleteDocumentResponse)
async def hard_delete_document(
    document_id: int,
    confirmation: str = Query(..., description="Zur Bestätigung: 'LÖSCHEN' eingeben"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endgültige Löschung (nur Level 5 - Admin)."""
    from ..infrastructure.repositories import (
        SQLAlchemyUploadRepository,
        SQLAlchemyDocumentPageRepository
    )
    
    try:
        # RBAC: Nur Level 5 (Admin)
        user_id = current_user.get('id', 1) if isinstance(current_user, dict) else getattr(current_user, 'id', 1)
        user_level = current_user.get('user_level', 1) if isinstance(current_user, dict) else getattr(current_user, 'user_level', 1)
        
        if user_level < 5:
            raise HTTPException(
                status_code=403,
                detail="Nur Administratoren (Level 5) können Dokumente endgültig löschen"
            )
        
        # Repositories initialisieren
        upload_repo = SQLAlchemyUploadRepository(db)
        page_repo = SQLAlchemyDocumentPageRepository(db)
        
        # Use Case ausführen
        # Event Publisher für EDD
        event_publisher = get_event_publisher()
        
        use_case = HardDeleteDocumentUseCase(
            upload_repository=upload_repo,
            page_repository=page_repo,
            event_publisher=event_publisher  # EDD: Publiziere DocumentHardDeletedEvent
        )
        result = await use_case.execute(
            document_id=document_id,
            deleted_by_user_id=user_id,
            confirmation=confirmation
        )
        
        return HardDeleteDocumentResponse(
            success=result["success"],
            message=result["message"],
            files_deleted=result.get("files_deleted", [])
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
