"""
Use Cases für Document Upload Context

Use Cases orchestrieren die Business Logic und koordinieren zwischen
Domain Entities, Repositories und Services.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Protocol
from ..domain.entities import (
    UploadedDocument,
    DocumentPage,
    InterestGroupAssignment,
    AIProcessingResult,
    WorkflowStatusChange,
    DocumentComment
)
from ..domain.value_objects import (
    FileType,
    ProcessingMethod,
    ProcessingStatus,
    DocumentMetadata,
    PageDimensions,
    FilePath,
    WorkflowStatus
)
from ..domain.repositories import (
    UploadRepository,
    DocumentPageRepository,
    InterestGroupAssignmentRepository,
    AIResponseRepository,
    WorkflowHistoryRepository,
    DocumentCommentRepository
)
from ..domain.events import (
    DocumentUploadedEvent,
    PagesGeneratedEvent,
    InterestGroupsAssignedEvent,
    DocumentWorkflowChangedEvent
)
from .ports import WorkflowPermissionService


# ==================== SERVICE INTERFACES (PORTS) ====================

class AIProcessingService(Protocol):
    """
    Port: Interface für AI-Processing Service.
    
    Dieser Service ist verantwortlich für die Verarbeitung von Dokumentseiten
    mit AI-Modellen aus dem aiplayground Context.
    """
    
    async def process_page(
        self,
        page_image_path: str,
        prompt_text: str,
        ai_model_id: str,  # String Model ID
        temperature: float,
        max_tokens: int,
        top_p: float,
        detail_level: str
    ) -> Dict[str, Any]:
        """
        Verarbeite eine Dokumentseite mit AI-Modell.
        
        Args:
            page_image_path: Pfad zum Seiten-Bild
            prompt_text: Prompt für AI-Modell
            ai_model_id: ID des AI-Modells
            temperature: Temperature-Wert
            max_tokens: Max Tokens
            top_p: Top-P Wert
            detail_level: Detail Level (high/low)
            
        Returns:
            Dict mit:
                - json_response: Strukturierte JSON-Antwort (String)
                - tokens_sent: Anzahl gesendeter Tokens
                - tokens_received: Anzahl empfangener Tokens
                - total_tokens: Gesamtzahl Tokens
                - response_time_ms: Response-Zeit in Millisekunden
                
        Raises:
            AIProcessingError: Bei Verarbeitungsfehler
        """
        ...


class PromptTemplateRepository(Protocol):
    """
    Port: Interface für PromptTemplate Repository.
    
    Wird benötigt um Standard-Prompts für Dokumenttypen zu laden.
    """
    
    async def get_default_for_document_type(self, document_type_id: int) -> Optional[Any]:
        """
        Hole Standard-Prompt-Template für Dokumenttyp.
        
        Args:
            document_type_id: Dokumenttyp ID
            
        Returns:
            PromptTemplate oder None
        """
        ...


class UploadDocumentUseCase:
    """
    Use Case: Dokument hochladen.
    
    Verantwortlichkeiten:
    - Validiere Upload-Daten
    - Erstelle UploadedDocument Entity
    - Speichere in Repository
    - Publiziere DocumentUploadedEvent
    
    Args:
        upload_repo: UploadRepository Interface
    """
    
    def __init__(self, upload_repo: UploadRepository):
        self.upload_repo = upload_repo
    
    async def execute(
        self,
        original_filename: str,
        file_size_bytes: int,
        document_type_id: int,
        qm_chapter: Optional[str],
        version: str,
        file_path: str,
        processing_method: str,
        uploaded_by_user_id: int
    ) -> UploadedDocument:
        """
        Führe Upload aus.
        
        Args:
            original_filename: Original Dateiname vom User
            file_size_bytes: Dateigröße in Bytes
            document_type_id: Dokumenttyp ID
            qm_chapter: QM-Kapitel (optional)
            version: Versionsnummer (z.B. v1.0.0)
            file_path: Pfad zum gespeicherten File
            processing_method: 'ocr' oder 'vision'
            uploaded_by_user_id: User ID des Uploaders
            
        Returns:
            UploadedDocument mit ID
            
        Raises:
            ValueError: Bei Validierungs-Fehler
        """
        # 1. Validiere und erstelle Value Objects
        file_type = FileType.from_filename(original_filename)
        
        # Generiere internen Dateinamen (timestamp + original)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{original_filename}"
        
        metadata = DocumentMetadata(
            filename=filename,
            original_filename=original_filename,
            qm_chapter=qm_chapter,
            version=version
        )
        
        file_path_vo = FilePath(file_path)
        processing_method_vo = ProcessingMethod(processing_method)
        
        # 2. Erstelle UploadedDocument Entity
        document = UploadedDocument(
            id=None,  # Wird von Repository gesetzt
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            document_type_id=document_type_id,
            metadata=metadata,
            file_path=file_path_vo,
            processing_method=processing_method_vo,
            processing_status=ProcessingStatus.PENDING,
            uploaded_by_user_id=uploaded_by_user_id,
            uploaded_at=datetime.utcnow(),
            pages=[],
            interest_group_ids=[]
        )
        
        # 3. Speichere in Repository
        saved_document = await self.upload_repo.save(document)
        
        # 4. Publiziere Event (TODO: Event Bus implementieren)
        event = DocumentUploadedEvent(
            document_id=saved_document.id,
            filename=filename,
            document_type_id=document_type_id,
            uploaded_by_user_id=uploaded_by_user_id,
            page_count=0,  # Noch keine Pages
            interest_group_ids=[],
            timestamp=datetime.utcnow()
        )
        # await self.event_bus.publish(event)
        
        return saved_document


class GeneratePreviewUseCase:
    """
    Use Case: Preview-Bilder generieren.
    
    Verantwortlichkeiten:
    - Lade UploadedDocument
    - Erstelle DocumentPage Entities
    - Speichere in Repository
    - Publiziere PagesGeneratedEvent
    
    Args:
        upload_repo: UploadRepository Interface
        page_repo: DocumentPageRepository Interface
    """
    
    def __init__(
        self,
        upload_repo: UploadRepository,
        page_repo: DocumentPageRepository
    ):
        self.upload_repo = upload_repo
        self.page_repo = page_repo
    
    async def execute(
        self,
        document_id: int,
        page_data: List[dict]
    ) -> List[DocumentPage]:
        """
        Generiere Previews für Dokument.
        
        Args:
            document_id: ID des Dokuments
            page_data: Liste von Page-Daten:
                [
                    {
                        'page_number': 1,
                        'preview_image_path': '/path/to/preview.jpg',
                        'thumbnail_path': '/path/to/thumb.jpg',
                        'width': 1000,
                        'height': 1414
                    },
                    ...
                ]
            
        Returns:
            Liste von DocumentPage Entities
            
        Raises:
            ValueError: Wenn Dokument nicht gefunden
        """
        # 1. Lade Dokument
        document = await self.upload_repo.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # 2. Erstelle DocumentPage Entities
        pages = []
        for data in page_data:
            page = DocumentPage(
                id=None,
                upload_document_id=document_id,
                page_number=data['page_number'],
                preview_image_path=FilePath(data['preview_image_path']),
                thumbnail_path=FilePath(data['thumbnail_path']) if data.get('thumbnail_path') else None,
                dimensions=PageDimensions(
                    width=data['width'],
                    height=data['height']
                ) if data.get('width') and data.get('height') else None,
                created_at=datetime.utcnow()
            )
            
            # 3. Speichere Page
            saved_page = await self.page_repo.save(page)
            pages.append(saved_page)
            
            # 4. Füge zu Document Aggregate hinzu
            document.add_page(saved_page)
        
        # 5. Update Document (page_count)
        await self.upload_repo.save(document)
        
        # 6. Publiziere Event
        event = PagesGeneratedEvent(
            document_id=document_id,
            page_count=len(pages),
            timestamp=datetime.utcnow()
        )
        # await self.event_bus.publish(event)
        
        return pages


class AssignInterestGroupsUseCase:
    """
    Use Case: Interest Groups zuweisen.
    
    Verantwortlichkeiten:
    - Lade UploadedDocument
    - Erstelle InterestGroupAssignment Entities
    - Speichere in Repository
    - Publiziere InterestGroupsAssignedEvent
    
    Args:
        upload_repo: UploadRepository Interface
        assignment_repo: InterestGroupAssignmentRepository Interface
    """
    
    def __init__(
        self,
        upload_repo: UploadRepository,
        assignment_repo: InterestGroupAssignmentRepository
    ):
        self.upload_repo = upload_repo
        self.assignment_repo = assignment_repo
    
    async def execute(
        self,
        document_id: int,
        interest_group_ids: List[int],
        assigned_by_user_id: int
    ) -> List[InterestGroupAssignment]:
        """
        Weise Interest Groups zu.
        
        Args:
            document_id: ID des Dokuments
            interest_group_ids: Liste von Interest Group IDs
            assigned_by_user_id: User ID des Zuweisers
            
        Returns:
            Liste von InterestGroupAssignment Entities
            
        Raises:
            ValueError: Wenn Dokument nicht gefunden oder Group bereits zugewiesen
        """
        # 1. Lade Dokument
        document = await self.upload_repo.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # 2. Erstelle Assignments
        assignments = []
        for group_id in interest_group_ids:
            # Prüfe ob bereits zugewiesen
            exists = await self.assignment_repo.exists(document_id, group_id)
            if exists:
                raise ValueError(f"Interest group {group_id} already assigned to document {document_id}")
            
            assignment = InterestGroupAssignment(
                id=None,
                upload_document_id=document_id,
                interest_group_id=group_id,
                assigned_by_user_id=assigned_by_user_id,
                assigned_at=datetime.utcnow()
            )
            
            # 3. Speichere Assignment
            saved_assignment = await self.assignment_repo.save(assignment)
            assignments.append(saved_assignment)
            
            # 4. Füge zu Document Aggregate hinzu
            document.assign_interest_group(group_id)
        
        # 5. Update Document
        await self.upload_repo.save(document)
        
        # 6. Publiziere Event
        event = InterestGroupsAssignedEvent(
            document_id=document_id,
            interest_group_ids=interest_group_ids,
            assigned_by_user_id=assigned_by_user_id,
            timestamp=datetime.utcnow()
        )
        # await self.event_bus.publish(event)
        
        return assignments


class GetUploadDetailsUseCase:
    """
    Use Case: Upload-Details abrufen.
    
    Verantwortlichkeiten:
    - Lade UploadedDocument
    - Lade zugehörige Pages
    - Lade zugehörige Assignments
    - Returniere aggregierte Daten
    
    Args:
        upload_repo: UploadRepository Interface
        page_repo: DocumentPageRepository Interface
        assignment_repo: InterestGroupAssignmentRepository Interface
    """
    
    def __init__(
        self,
        upload_repo: UploadRepository,
        page_repo: DocumentPageRepository,
        assignment_repo: InterestGroupAssignmentRepository
    ):
        self.upload_repo = upload_repo
        self.page_repo = page_repo
        self.assignment_repo = assignment_repo
    
    async def execute(self, document_id: int) -> dict:
        """
        Lade Upload-Details.
        
        Args:
            document_id: ID des Dokuments
            
        Returns:
            Dict mit aggregierten Daten:
            {
                'document': UploadedDocument,
                'pages': List[DocumentPage],
                'assignments': List[InterestGroupAssignment]
            }
            
        Raises:
            ValueError: Wenn Dokument nicht gefunden
        """
        # 1. Lade Dokument
        document = await self.upload_repo.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # 2. Lade Pages
        pages = await self.page_repo.get_by_document_id(document_id)
        
        # 3. Lade Assignments
        assignments = await self.assignment_repo.get_by_document_id(document_id)
        
        return {
            'document': document,
            'pages': pages,
            'assignments': assignments
        }


class ProcessDocumentPageUseCase:
    """
    Use Case: Verarbeite eine Dokumentseite mit AI.
    
    Workflow:
    1. Lade DocumentPage
    2. Lade UploadDocument (für Dokumenttyp)
    3. Hole Standard-Prompt-Template für Dokumenttyp
    4. Verarbeite Seite mit AI-Service
    5. Erstelle AIProcessingResult
    6. Speichere in Repository
    
    Args:
        upload_repo: UploadRepository Interface
        page_repo: DocumentPageRepository Interface
        ai_response_repo: AIResponseRepository Interface
        prompt_template_repo: PromptTemplateRepository Interface
        ai_processing_service: AIProcessingService Interface
    """
    
    def __init__(
        self,
        upload_repo: UploadRepository,
        page_repo: DocumentPageRepository,
        ai_response_repo: AIResponseRepository,
        prompt_template_repo: PromptTemplateRepository,
        ai_processing_service: AIProcessingService
    ):
        self.upload_repo = upload_repo
        self.page_repo = page_repo
        self.ai_response_repo = ai_response_repo
        self.prompt_template_repo = prompt_template_repo
        self.ai_processing_service = ai_processing_service
    
    async def execute(
        self,
        upload_document_id: int,
        page_number: int
    ) -> AIProcessingResult:
        """
        Verarbeite eine Dokumentseite mit AI.
        
        Args:
            upload_document_id: ID des Upload-Dokuments
            page_number: Seiten-Nummer (1-basiert)
            
        Returns:
            AIProcessingResult Entity
            
        Raises:
            ValueError: Wenn Dokument/Seite nicht gefunden oder kein Standard-Prompt existiert
            AIProcessingError: Bei AI-Verarbeitungsfehler
        """
        # 1. Lade Upload-Dokument
        print(f"[ProcessDocumentPageUseCase] Loading document {upload_document_id}")
        document = await self.upload_repo.get_by_id(upload_document_id)
        if not document:
            raise ValueError(f"Document {upload_document_id} not found")
        print(f"[ProcessDocumentPageUseCase] Document loaded: type_id={document.document_type_id}")
        
        # 2. Lade alle Pages des Dokuments
        print(f"[ProcessDocumentPageUseCase] Loading pages for document {upload_document_id}")
        pages = await self.page_repo.get_by_document_id(upload_document_id)
        if not pages:
            raise ValueError(f"No pages found for document {upload_document_id}")
        print(f"[ProcessDocumentPageUseCase] Found {len(pages)} pages")
        
        # 3. Finde die gewünschte Page
        page = None
        for p in pages:
            if p.page_number == page_number:
                page = p
                break
        
        if not page:
            raise ValueError(f"Page {page_number} not found for document {upload_document_id}")
        print(f"[ProcessDocumentPageUseCase] Page {page_number} found: {page.preview_image_path}")
        
        # 4. Hole Standard-Prompt-Template für Dokumenttyp
        print(f"[ProcessDocumentPageUseCase] Loading prompt template for document type {document.document_type_id}")
        prompt_template = await self.prompt_template_repo.get_default_for_document_type(
            document.document_type_id
        )
        if not prompt_template:
            raise ValueError(
                f"No default prompt template found for document type {document.document_type_id}"
            )
        print(f"[ProcessDocumentPageUseCase] Prompt template loaded: {prompt_template.name}, model={prompt_template.ai_model}")
        
        # 5. Prüfe ob bereits ein AIProcessingResult für diese Seite existiert
        print(f"[ProcessDocumentPageUseCase] Checking for existing AI result for page {page.id}")
        existing_result = await self.ai_response_repo.get_by_page_id(page.id)
        
        # 6. Verarbeite Seite mit AI-Service
        try:
            print(f"[ProcessDocumentPageUseCase] Starting AI processing...")
            ai_result = await self.ai_processing_service.process_page(
                page_image_path=str(page.preview_image_path),  # Convert FilePath to string
                prompt_text=prompt_template.prompt_text,
                ai_model_id=prompt_template.ai_model,  # String, nicht ID
                temperature=prompt_template.temperature,
                max_tokens=prompt_template.max_tokens,
                top_p=prompt_template.top_p,
                detail_level=prompt_template.detail_level or "high"
            )
            print(f"[ProcessDocumentPageUseCase] AI processing completed successfully")
            
            if existing_result:
                # 7a. UPDATE: Aktualisiere existierendes Result
                print(f"[ProcessDocumentPageUseCase] Updating existing AI result (ID: {existing_result.id})")
                existing_result.update_with_new_data(ai_result)
                saved_result = await self.ai_response_repo.update_result(existing_result)
                print(f"[ProcessDocumentPageUseCase] AI result updated successfully")
            else:
                # 7b. INSERT: Erstelle neues Result
                print(f"[ProcessDocumentPageUseCase] Creating new AI result")
                processing_result = AIProcessingResult(
                    id=None,
                    upload_document_id=upload_document_id,
                    upload_document_page_id=page.id,
                    prompt_template_id=prompt_template.id,
                    ai_model_id=prompt_template.ai_model,  # String, nicht ID
                    model_name=ai_result.get("model_name", "unknown"),
                    json_response=ai_result["json_response"],
                    processing_status="completed",
                    tokens_sent=ai_result.get("tokens_sent"),
                    tokens_received=ai_result.get("tokens_received"),
                    total_tokens=ai_result.get("total_tokens"),
                    response_time_ms=ai_result.get("response_time_ms"),
                    processed_at=datetime.utcnow()
                )
                saved_result = await self.ai_response_repo.save(processing_result)
                print(f"[ProcessDocumentPageUseCase] AI result created successfully")
            
            return saved_result
            
        except Exception as e:
            # Bei Fehler: Erstelle Failed-Result
            error_result = AIProcessingResult(
                id=None,
                upload_document_id=upload_document_id,
                upload_document_page_id=page.id,
                prompt_template_id=prompt_template.id,
                ai_model_id=prompt_template.ai_model,  # String, nicht ID
                model_name="unknown",
                json_response="{}",
                processing_status="failed",
                tokens_sent=0,
                tokens_received=0,
                total_tokens=0,
                response_time_ms=0,
                error_message=str(e),
                processed_at=datetime.utcnow()
            )
            
            # Speichere Failed-Result für Audit-Trail
            await self.ai_response_repo.save(error_result)
            
            # Re-raise Exception
            raise


# ==================== WORKFLOW USE CASES ====================

class ChangeDocumentWorkflowStatusUseCase:
    """
    Use Case: Ändere Workflow-Status eines Dokuments.
    
    Orchestriert die Business Logic für Status-Änderungen:
    1. Validiere Berechtigung
    2. Ändere Status in Domain Entity
    3. Speichere Änderung
    4. Erstelle History-Eintrag
    """
    
    def __init__(
        self,
        upload_repository: UploadRepository,
        history_repository: WorkflowHistoryRepository,
        permission_service: WorkflowPermissionService
    ):
        self.upload_repository = upload_repository
        self.history_repository = history_repository
        self.permission_service = permission_service
    
    async def execute(
        self,
        document_id: int,
        new_status: WorkflowStatus,
        user_id: int,
        reason: str
    ) -> UploadedDocument:
        """
        Ändere Workflow-Status eines Dokuments.
        
        Args:
            document_id: Dokument ID
            new_status: Neuer Workflow-Status
            user_id: User ID des Änderers
            reason: Grund für die Änderung
            
        Returns:
            Aktualisiertes UploadedDocument
            
        Raises:
            ValueError: Wenn Dokument nicht existiert oder Parameter ungültig
            PermissionError: Wenn User keine Berechtigung hat
        """
        # Validiere Parameter
        if user_id <= 0:
            raise ValueError("user_id must be positive")
        
        if not reason or not reason.strip():
            raise ValueError("reason cannot be empty")
        
        # Lade Dokument
        document = await self.upload_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Prüfe Berechtigung
        can_change = await self.permission_service.can_change_status(
            user_id, document.workflow_status, new_status
        )
        if not can_change:
            raise PermissionError(
                f"User {user_id} cannot change status from "
                f"{document.workflow_status} to {new_status}"
            )
        
        # Ändere Status in Domain Entity
        event = document.change_workflow_status(new_status, user_id, reason)
        
        # Speichere Änderung
        updated_document = await self.upload_repository.save(document)
        
        # Erstelle History-Eintrag
        history_entry = WorkflowStatusChange(
            id=0,  # Wird von DB gesetzt
            document_id=document_id,
            from_status=event.old_status,
            to_status=event.new_status,
            changed_by_user_id=user_id,
            reason=reason
        )
        await self.history_repository.add(history_entry)
        
        return updated_document


class GetWorkflowHistoryUseCase:
    """
    Use Case: Hole Workflow-History eines Dokuments.
    
    Lädt alle Status-Änderungen eines Dokuments chronologisch.
    """
    
    def __init__(self, history_repository: WorkflowHistoryRepository):
        self.history_repository = history_repository
    
    async def execute(self, document_id: int) -> List[WorkflowStatusChange]:
        """
        Hole Workflow-History eines Dokuments.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            Liste der Status-Änderungen (chronologisch sortiert)
        """
        return await self.history_repository.get_by_document_id(document_id)


class GetDocumentsByWorkflowStatusUseCase:
    """
    Use Case: Hole Dokumente nach Workflow-Status.
    
    Lädt alle Dokumente mit einem bestimmten Workflow-Status,
    optional gefiltert nach Interest Groups.
    """
    
    def __init__(self, upload_repository: UploadRepository):
        self.upload_repository = upload_repository
    
    async def execute(
        self,
        status: WorkflowStatus,
        interest_group_ids: Optional[List[int]] = None,
        document_type_id: Optional[int] = None
    ) -> List[UploadedDocument]:
        """
        Hole Dokumente nach Workflow-Status.
        
        Args:
            status: Workflow-Status
            interest_group_ids: Optional filter by Interest Groups
            document_type_id: Optional filter by Document Type
            
        Returns:
            Liste der Dokumente mit dem Status
        """
        return await self.upload_repository.get_by_workflow_status(
            status, interest_group_ids, document_type_id
        )

