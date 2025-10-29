"""
FastAPI Router für Document Upload Context

Dieser Router stellt die HTTP API für Document Upload bereit.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from contexts.accesscontrol.interface.guard_router import get_current_user
from contexts.users.domain.entities import User

from ..application.use_cases import (
    UploadDocumentUseCase,
    GeneratePreviewUseCase,
    AssignInterestGroupsUseCase,
    GetUploadDetailsUseCase
)
from ..infrastructure.repositories import (
    SQLAlchemyUploadRepository,
    SQLAlchemyDocumentPageRepository,
    SQLAlchemyInterestGroupAssignmentRepository
)
from ..infrastructure.file_storage import LocalFileStorageService
from ..infrastructure.pdf_splitter import PDFSplitterService
from ..infrastructure.image_processor import ImageProcessorService

from .schemas import (
    UploadDocumentRequest,
    AssignInterestGroupsRequest,
    UploadDocumentResponse,
    GeneratePreviewResponse,
    AssignInterestGroupsResponse,
    GetUploadDetailsResponse,
    GetUploadsListResponse,
    DeleteUploadResponse,
    ErrorResponse,
    UploadedDocumentSchema,
    DocumentPageSchema,
    InterestGroupAssignmentSchema
)

router = APIRouter(prefix="/api/document-upload", tags=["Document Upload"])


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_upload_repository(db: Session = Depends(get_db)) -> SQLAlchemyUploadRepository:
    """Factory für UploadRepository."""
    return SQLAlchemyUploadRepository(db)


def get_page_repository(db: Session = Depends(get_db)) -> SQLAlchemyDocumentPageRepository:
    """Factory für DocumentPageRepository."""
    return SQLAlchemyDocumentPageRepository(db)


def get_assignment_repository(db: Session = Depends(get_db)) -> SQLAlchemyInterestGroupAssignmentRepository:
    """Factory für InterestGroupAssignmentRepository."""
    return SQLAlchemyInterestGroupAssignmentRepository(db)


def get_file_storage() -> LocalFileStorageService:
    """Factory für FileStorageService."""
    return LocalFileStorageService()


def get_pdf_splitter() -> PDFSplitterService:
    """Factory für PDFSplitterService."""
    return PDFSplitterService(dpi=200)


def get_image_processor() -> ImageProcessorService:
    """Factory für ImageProcessorService."""
    return ImageProcessorService(thumbnail_size=(200, 200), jpeg_quality=85)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/upload",
    response_model=UploadDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Document",
    description="Upload ein neues Dokument (PDF, DOCX, PNG, JPG). Nur für Quality Manager (Level 4)."
)
async def upload_document(
    file: UploadFile = File(..., description="Dokument-Datei"),
    filename: str = Form(..., description="Dateiname"),
    original_filename: str = Form(..., description="Original-Dateiname"),
    document_type_id: int = Form(..., description="Dokumenttyp ID"),
    qm_chapter: str = Form(..., description="QM-Kapitel"),
    version: str = Form(..., description="Version"),
    processing_method: str = Form(..., description="Verarbeitungsmethode (ocr/vision)"),
    current_user: User = Depends(get_current_user),
    upload_repo: SQLAlchemyUploadRepository = Depends(get_upload_repository),
    file_storage: LocalFileStorageService = Depends(get_file_storage)
):
    """
    Upload ein neues Dokument.
    
    **Permissions:** Nur Quality Manager (Level 4)
    
    **Workflow:**
    1. Validiere User-Permission (Level 4)
    2. Validiere File-Type (PDF, DOCX, PNG, JPG)
    3. Speichere Datei im File Storage
    4. Erstelle UploadedDocument Entity
    5. Speichere in DB
    6. Returniere Upload-Details
    
    **Returns:**
    - 201: Upload erfolgreich
    - 403: Keine Permission
    - 400: Ungültiger File-Type oder Daten
    """
    # Permission Check: Level 4 (QM-Manager) oder Level 5 (QMS Admin)
    # current_user is a dict from JWT decode with: id, email, roles, permissions
    user_id = current_user.get('id') if isinstance(current_user, dict) else getattr(current_user, 'id', None)
    user_email = current_user.get('email') if isinstance(current_user, dict) else getattr(current_user, 'email', None)
    
    # Check if user is qms.admin (Level 5) - direct access
    if user_email == "qms.admin@company.com":
        # QMS Admin has full access
        pass
    else:
        # For other users: Check if they have Level 4 in any Interest Group
        # Query UserGroupMembership to check permission_level
        from backend.app.models import UserGroupMembership
        from backend.app.database import get_db
        
        db = next(get_db())
        membership = db.query(UserGroupMembership).filter(
            UserGroupMembership.user_id == user_id,
            UserGroupMembership.permission_level >= 4
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Quality Managers (Level 4) or QMS Administrators can upload documents"
            )
    
    try:
        # Validiere File-Type
        file_extension = file.filename.split('.')[-1].lower()
        allowed_extensions = ['pdf', 'docx', 'png', 'jpg', 'jpeg']
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Lese File Content
        file_content = await file.read()
        file_size_bytes = len(file_content)
        
        # Speichere Datei (mit BytesIO da Stream schon gelesen)
        import io
        file_bytes = io.BytesIO(file_content)
        file_path = await file_storage.save_document(
            file=file_bytes,
            filename=filename
        )
        
        # Erstelle UploadDocumentRequest
        upload_request = UploadDocumentRequest(
            filename=filename,
            original_filename=original_filename,
            document_type_id=document_type_id,
            qm_chapter=qm_chapter,
            version=version,
            processing_method=processing_method
        )
        
        # Execute Use Case
        use_case = UploadDocumentUseCase(upload_repo)
        
        uploaded_document = await use_case.execute(
            original_filename=upload_request.original_filename,
            file_size_bytes=file_size_bytes,
            document_type_id=upload_request.document_type_id,
            qm_chapter=upload_request.qm_chapter,
            version=upload_request.version,
            file_path=file_path,
            processing_method=upload_request.processing_method,
            uploaded_by_user_id=current_user.get('id') if isinstance(current_user, dict) else current_user.id
        )
        
        # Konvertiere zu Schema
        document_schema = UploadedDocumentSchema(
            id=uploaded_document.id,
            filename=uploaded_document.metadata.filename,
            original_filename=uploaded_document.metadata.original_filename,
            file_size_bytes=uploaded_document.file_size_bytes,
            file_type=uploaded_document.file_type.value,
            document_type_id=uploaded_document.document_type_id,
            qm_chapter=uploaded_document.metadata.qm_chapter,
            version=uploaded_document.metadata.version,
            page_count=uploaded_document.page_count,
            uploaded_by_user_id=uploaded_document.uploaded_by_user_id,
            uploaded_at=uploaded_document.uploaded_at,
            file_path=str(uploaded_document.file_path),
            processing_method=uploaded_document.processing_method.value,
            processing_status=uploaded_document.processing_status.value
        )
        
        return UploadDocumentResponse(
            success=True,
            message=f"Document '{filename}' uploaded successfully",
            document=document_schema
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.post(
    "/{document_id}/generate-preview",
    response_model=GeneratePreviewResponse,
    summary="Generate Preview",
    description="Generiere Preview-Bilder für ein Dokument (Split in Einzelseiten)."
)
async def generate_preview(
    document_id: int,
    current_user: User = Depends(get_current_user),
    upload_repo: SQLAlchemyUploadRepository = Depends(get_upload_repository),
    page_repo: SQLAlchemyDocumentPageRepository = Depends(get_page_repository),
    file_storage: LocalFileStorageService = Depends(get_file_storage),
    pdf_splitter: PDFSplitterService = Depends(get_pdf_splitter),
    image_processor: ImageProcessorService = Depends(get_image_processor)
):
    """
    Generiere Preview-Bilder für ein Dokument.
    
    **Workflow:**
    1. Lade UploadedDocument
    2. Lade Original-Datei
    3. Split PDF/DOCX in Einzelseiten (oder verwende PNG/JPG direkt)
    4. Generiere Thumbnails
    5. Speichere Preview-Bilder
    6. Erstelle DocumentPage Entities
    7. Speichere in DB
    
    **Returns:**
    - 200: Preview erfolgreich generiert
    - 404: Dokument nicht gefunden
    """
    try:
        # 1. Lade Dokument
        document = await upload_repo.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        # 2. Bestimme File-Typ und verarbeite
        file_extension = document.file_type.value.lower()
        page_data = []
        
        if file_extension == 'pdf':
            # PDF: Split in Pages und generiere Previews
            pdf_path = file_storage.get_absolute_path(document.file_path.path)
            page_images = await pdf_splitter.split_pdf_to_images(pdf_path)
            
            for page_num, img in enumerate(page_images, start=1):
                # Konvertiere PIL Image zu Bytes
                import io
                preview_bytes = io.BytesIO()
                img.save(preview_bytes, format='JPEG', quality=95)
                preview_bytes.seek(0)
                
                # Speichere Preview
                preview_path = await file_storage.save_preview(preview_bytes, document_id, page_num)
                
                # Generiere Thumbnail
                thumbnail = await image_processor.create_thumbnail(img, maintain_aspect_ratio=True)
                thumbnail_bytes = io.BytesIO()
                thumbnail.save(thumbnail_bytes, format='JPEG', quality=85)
                thumbnail_bytes.seek(0)
                
                # Speichere Thumbnail
                thumbnail_path = await file_storage.save_thumbnail(thumbnail_bytes, document_id, page_num)
                
                page_data.append({
                    'page_number': page_num,
                    'preview_image_path': preview_path,
                    'thumbnail_path': thumbnail_path,
                    'width': img.width,
                    'height': img.height
                })
        
        elif file_extension in ['png', 'jpg', 'jpeg']:
            # Image: Single Page
            image_path = file_storage.get_absolute_path(document.file_path.path)
            from PIL import Image
            import io
            img = Image.open(image_path)
            
            # Auto-rotate if needed
            img = await image_processor.auto_rotate(img)
            
            # Konvertiere PIL Image zu Bytes
            preview_bytes = io.BytesIO()
            img.save(preview_bytes, format='JPEG', quality=95)
            preview_bytes.seek(0)
            
            # Speichere Preview
            preview_path = await file_storage.save_preview(preview_bytes, document_id, 1)
            
            # Generiere Thumbnail
            thumbnail = await image_processor.create_thumbnail(img, maintain_aspect_ratio=True)
            thumbnail_bytes = io.BytesIO()
            thumbnail.save(thumbnail_bytes, format='JPEG', quality=85)
            thumbnail_bytes.seek(0)
            
            # Speichere Thumbnail
            thumbnail_path = await file_storage.save_thumbnail(thumbnail_bytes, document_id, 1)
            
            page_data.append({
                'page_number': 1,
                'preview_image_path': preview_path,
                'thumbnail_path': thumbnail_path,
                'width': img.width,
                'height': img.height
            })
        
        elif file_extension == 'docx':
            # DOCX: Convert to PDF, then split
            # TODO: Implement DOCX → PDF conversion
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="DOCX preview generation not yet implemented"
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_extension}"
            )
        
        # 3. Execute Use Case mit generierten Page-Daten
        use_case = GeneratePreviewUseCase(
            upload_repo,
            page_repo
        )
        
        pages = await use_case.execute(document_id, page_data)
        
        # Konvertiere zu Schema
        page_schemas = [
            DocumentPageSchema(
                id=page.id,
                upload_document_id=page.upload_document_id,
                page_number=page.page_number,
                preview_image_path=str(page.preview_image_path),
                thumbnail_path=str(page.thumbnail_path) if page.thumbnail_path else None,
                width=page.dimensions.width if page.dimensions else None,
                height=page.dimensions.height if page.dimensions else None,
                created_at=page.created_at
            )
            for page in pages
        ]
        
        return GeneratePreviewResponse(
            success=True,
            message=f"Generated {len(pages)} preview pages",
            pages_generated=len(pages),
            pages=page_schemas
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview generation failed: {str(e)}"
        )


@router.post(
    "/{document_id}/assign-interest-groups",
    response_model=AssignInterestGroupsResponse,
    summary="Assign Interest Groups",
    description="Weise Interest Groups einem Dokument zu."
)
async def assign_interest_groups(
    document_id: int,
    request: AssignInterestGroupsRequest,
    current_user: User = Depends(get_current_user),
    upload_repo: SQLAlchemyUploadRepository = Depends(get_upload_repository),
    assignment_repo: SQLAlchemyInterestGroupAssignmentRepository = Depends(get_assignment_repository)
):
    """
    Weise Interest Groups einem Dokument zu.
    
    **Permissions:** Nur Quality Manager (Level 4)
    
    **Returns:**
    - 200: Assignment erfolgreich
    - 403: Keine Permission
    - 404: Dokument nicht gefunden
    - 400: Duplikate oder ungültige IDs
    """
    # Permission Check: Level 4 (QM-Manager) oder Level 5 (QMS Admin)
    # current_user is a dict from JWT decode with: id, email, roles, permissions
    user_id = current_user.get('id') if isinstance(current_user, dict) else getattr(current_user, 'id', None)
    user_email = current_user.get('email') if isinstance(current_user, dict) else getattr(current_user, 'email', None)
    
    # Check if user is qms.admin (Level 5) - direct access
    if user_email == "qms.admin@company.com":
        # QMS Admin has full access
        pass
    else:
        # For other users: Check if they have Level 4 in any Interest Group
        # Query UserGroupMembership to check permission_level
        from backend.app.models import UserGroupMembership
        from backend.app.database import get_db
        
        db = next(get_db())
        membership = db.query(UserGroupMembership).filter(
            UserGroupMembership.user_id == user_id,
            UserGroupMembership.permission_level >= 4
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Quality Managers (Level 4) or QMS Administrators can assign interest groups"
            )
    
    try:
        # Execute Use Case
        use_case = AssignInterestGroupsUseCase(upload_repo, assignment_repo)
        
        assignments = await use_case.execute(
            document_id=document_id,
            interest_group_ids=request.interest_group_ids,
            assigned_by_user_id=current_user.get('id') if isinstance(current_user, dict) else current_user.id
        )
        
        # Konvertiere zu Schema
        assignment_schemas = [
            InterestGroupAssignmentSchema(
                id=assignment.id,
                upload_document_id=assignment.upload_document_id,
                interest_group_id=assignment.interest_group_id,
                assigned_by_user_id=assignment.assigned_by_user_id,
                assigned_at=assignment.assigned_at
            )
            for assignment in assignments
        ]
        
        return AssignInterestGroupsResponse(
            success=True,
            message=f"Assigned {len(assignments)} interest groups",
            assignments=assignment_schemas
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assignment failed: {str(e)}"
        )


@router.get(
    "/{document_id}",
    response_model=GetUploadDetailsResponse,
    summary="Get Upload Details",
    description="Lade Details eines Uploads (mit Pages und Interest Groups)."
)
async def get_upload_details(
    document_id: int,
    current_user: User = Depends(get_current_user),
    upload_repo: SQLAlchemyUploadRepository = Depends(get_upload_repository),
    page_repo: SQLAlchemyDocumentPageRepository = Depends(get_page_repository),
    assignment_repo: SQLAlchemyInterestGroupAssignmentRepository = Depends(get_assignment_repository),
    db: Session = Depends(get_db)
):
    """
    Lade Upload Details mit Pages und Interest Groups.
    
    **Returns:**
    - 200: Details geladen
    - 404: Dokument nicht gefunden
    """
    try:
        # Execute Use Case
        use_case = GetUploadDetailsUseCase(upload_repo, page_repo, assignment_repo)
        
        result = await use_case.execute(document_id)
        document = result['document']
        pages = result['pages']
        assignments = result['assignments']
        
        # Lade AI Processing Results für alle Pages
        from ..infrastructure.repositories import SQLAlchemyAIResponseRepository
        from .schemas import AIProcessingResultSchema
        ai_response_repo = SQLAlchemyAIResponseRepository(db)
        
        # Map page_id -> ai_response
        ai_responses_by_page = {}
        for page in pages:
            ai_response = await ai_response_repo.get_by_page_id(page.id)
            if ai_response:
                # Parse JSON if possible
                try:
                    import json
                    parsed_json = json.loads(ai_response.json_response) if ai_response.json_response else None
                except:
                    parsed_json = None
                
                ai_responses_by_page[page.id] = AIProcessingResultSchema(
                    id=ai_response.id,
                    document_page_id=ai_response.upload_document_page_id,
                    prompt_template_id=ai_response.prompt_template_id,
                    ai_model_used=ai_response.model_name,
                    raw_response=ai_response.json_response,
                    parsed_json=parsed_json,
                    tokens_sent=ai_response.tokens_sent,
                    tokens_received=ai_response.tokens_received,
                    processing_time_ms=ai_response.response_time_ms,
                    status="success" if ai_response.processing_status == "completed" else "failed",
                    error_message=ai_response.error_message,
                    created_at=ai_response.processed_at
                )
        
        # Konvertiere zu Schema
        from .schemas import UploadedDocumentDetailSchema
        
        document_schema = UploadedDocumentDetailSchema(
            id=document.id,
            filename=document.metadata.filename,
            original_filename=document.metadata.original_filename,
            file_size_bytes=document.file_size_bytes,
            file_type=document.file_type.value,
            document_type_id=document.document_type_id,
            qm_chapter=document.metadata.qm_chapter or "",
            version=document.metadata.version,
            page_count=len(pages),  # Use actual pages count
            uploaded_by_user_id=document.uploaded_by_user_id,
            uploaded_at=document.uploaded_at,
            file_path=str(document.file_path),
            processing_method=document.processing_method.value,
            processing_status=document.processing_status.value,
            workflow_status=document.workflow_status.value,
            pages=[
                DocumentPageSchema(
                    id=page.id,
                    upload_document_id=page.upload_document_id,
                    page_number=page.page_number,
                    preview_image_path=str(page.preview_image_path),
                    thumbnail_path=str(page.thumbnail_path) if page.thumbnail_path else None,
                    width=page.dimensions.width if page.dimensions else None,
                    height=page.dimensions.height if page.dimensions else None,
                    created_at=page.created_at,
                    ai_processing_result=ai_responses_by_page.get(page.id)
                )
                for page in pages
            ],
            interest_groups=[
                InterestGroupAssignmentSchema(
                    id=assignment.id,
                    upload_document_id=assignment.upload_document_id,
                    interest_group_id=assignment.interest_group_id,
                    assigned_by_user_id=assignment.assigned_by_user_id,
                    assigned_at=assignment.assigned_at
                )
                for assignment in assignments
            ]
        )
        
        return GetUploadDetailsResponse(
            success=True,
            document=document_schema
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load details: {str(e)}"
        )


@router.get(
    "/",
    response_model=GetUploadsListResponse,
    summary="Get Uploads List",
    description="Lade Liste aller Uploads mit optionalen Filtern."
)
async def get_uploads_list(
    user_id: Optional[int] = None,
    document_type_id: Optional[int] = None,
    processing_status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    upload_repo: SQLAlchemyUploadRepository = Depends(get_upload_repository)
):
    """
    Lade Liste aller Uploads.
    
    **Query Parameters:**
    - user_id: Filter nach Uploader
    - document_type_id: Filter nach Dokumenttyp
    - processing_status: Filter nach Status (pending/processing/completed/failed)
    - limit: Max Anzahl Ergebnisse (default: 100)
    - offset: Offset für Pagination (default: 0)
    
    **Returns:**
    - 200: Liste geladen
    """
    try:
        documents = await upload_repo.get_all(
            user_id=user_id,
            document_type_id=document_type_id,
            processing_status=processing_status,
            limit=limit,
            offset=offset
        )
        
        # Konvertiere zu Schema
        document_schemas = [
            UploadedDocumentSchema(
                id=doc.id,
                filename=doc.metadata.filename,
                original_filename=doc.metadata.original_filename,
                file_size_bytes=doc.file_size_bytes,
                file_type=doc.file_type.value,
                document_type_id=doc.document_type_id,
                qm_chapter=doc.metadata.qm_chapter,
                version=doc.metadata.version,
                page_count=doc.page_count,
                uploaded_by_user_id=doc.uploaded_by_user_id,
                uploaded_at=doc.uploaded_at,
                file_path=str(doc.file_path),
                processing_method=doc.processing_method.value,
                workflow_status=doc.workflow_status.value
            )
            for doc in documents
        ]
        
        return GetUploadsListResponse(
            success=True,
            total=len(document_schemas),
            documents=document_schemas
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load uploads: {str(e)}"
        )


@router.delete(
    "/{document_id}",
    response_model=DeleteUploadResponse,
    summary="Delete Upload",
    description="Lösche ein Upload (inkl. Pages, Assignments, Files)."
)
async def delete_upload(
    document_id: int,
    current_user: User = Depends(get_current_user),
    upload_repo: SQLAlchemyUploadRepository = Depends(get_upload_repository),
    page_repo: SQLAlchemyDocumentPageRepository = Depends(get_page_repository),
    assignment_repo: SQLAlchemyInterestGroupAssignmentRepository = Depends(get_assignment_repository),
    file_storage: LocalFileStorageService = Depends(get_file_storage)
):
    """
    Lösche ein Upload.
    
    **Permissions:** Nur Quality Manager (Level 4)
    
    **Workflow:**
    1. Lade Document
    2. Lösche Files (Document, Previews, Thumbnails)
    3. Lösche Pages (DB)
    4. Lösche Assignments (DB)
    5. Lösche Document (DB)
    
    **Returns:**
    - 200: Deletion erfolgreich
    - 403: Keine Permission
    - 404: Dokument nicht gefunden
    """
    # Permission Check
    user_permission_level = current_user.get('permission_level', 0)
    user_email = current_user.get('email', '')
    
    # QMS Admin (Level 5) oder Quality Manager (Level 4) können löschen
    if user_permission_level < 4 and user_email != 'qms.admin@company.com':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Quality Managers (Level 4+) can delete documents"
        )
    
    try:
        # Lade Document
        document = await upload_repo.get_by_id(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        # Lösche Files
        await file_storage.delete_document(str(document.file_path))
        await file_storage.delete_previews(document_id)
        await file_storage.delete_thumbnails(document_id)
        
        # Lösche Pages
        await page_repo.delete_by_document_id(document_id)
        
        # Lösche Assignments
        await assignment_repo.delete_by_document_id(document_id)
        
        # Lösche Document
        success = await upload_repo.delete(document_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document"
            )
        
        return DeleteUploadResponse(
            success=True,
            message=f"Document {document_id} deleted successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion failed: {str(e)}"
        )


@router.post(
    "/{document_id}/process-page/{page_number}",
    response_model=dict,
    summary="Process Document Page with AI",
    description="Verarbeite eine Dokumentseite mit AI-Modell (Standard-Prompt des Dokumenttyps)."
)
async def process_document_page(
    document_id: int,
    page_number: int,
    current_user: User = Depends(get_current_user),
    upload_repo: SQLAlchemyUploadRepository = Depends(get_upload_repository),
    page_repo: SQLAlchemyDocumentPageRepository = Depends(get_page_repository)
):
    """
    Verarbeite eine Dokumentseite mit AI.
    
    **Workflow:**
    1. Hole Standard-Prompt für Dokumenttyp
    2. Lade Seiten-Bild
    3. Sende an AI-Modell
    4. Speichere JSON-Response
    
    **Returns:**
    - 200: Verarbeitung erfolgreich
    - 404: Dokument/Seite nicht gefunden
    - 400: Kein Standard-Prompt für Dokumenttyp
    """
    try:
        from ..application.use_cases import ProcessDocumentPageUseCase
        from ..infrastructure.ai_processing_service import AIPlaygroundProcessingService
        from ..infrastructure.repositories import SQLAlchemyAIResponseRepository
        from contexts.aiplayground.application.services import AIPlaygroundService
        from contexts.prompttemplates.infrastructure.repositories import SQLAlchemyPromptTemplateRepository
        from backend.app.database import get_db
        
        # Get DB Session
        db = next(get_db())
        
        # Initialize Repositories & Services
        ai_response_repo = SQLAlchemyAIResponseRepository(db)
        prompt_template_repo = SQLAlchemyPromptTemplateRepository(db)
        ai_playground_service = AIPlaygroundService()
        ai_processing_service = AIPlaygroundProcessingService(ai_playground_service)
        
        # Initialize Use Case
        use_case = ProcessDocumentPageUseCase(
            upload_repo=upload_repo,
            page_repo=page_repo,
            ai_response_repo=ai_response_repo,
            prompt_template_repo=prompt_template_repo,
            ai_processing_service=ai_processing_service
        )
        
        # Execute
        result = await use_case.execute(
            upload_document_id=document_id,
            page_number=page_number
        )
        
        # Return Response (Frontend-kompatibel)
        # Parse JSON response if possible
        try:
            import json
            parsed_json = json.loads(result.json_response) if result.json_response else None
        except:
            parsed_json = None
        
        return {
            "success": True,
            "message": f"Page {page_number} processed successfully",
            "result": {
                "id": result.id,
                "document_page_id": result.upload_document_page_id,
                "prompt_template_id": result.prompt_template_id,
                "ai_model_used": result.model_name,
                "raw_response": result.json_response,
                "parsed_json": parsed_json,
                "tokens_sent": result.tokens_sent,
                "tokens_received": result.tokens_received,
                "processing_time_ms": result.response_time_ms,
                "status": "success" if result.processing_status == "completed" else "failed",
                "error_message": result.error_message if hasattr(result, 'error_message') else None,
                "created_at": result.processed_at.isoformat()
            }
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )

