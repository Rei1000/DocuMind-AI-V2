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
    FileHash,
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
    
    def __init__(self, upload_repo: UploadRepository, event_publisher=None):
        self.upload_repo = upload_repo
        self.event_publisher = event_publisher
    
    async def execute(
        self,
        original_filename: str,
        file_size_bytes: int,
        document_type_id: int,
        qm_chapter: Optional[str],
        file_path: str,
        processing_method: str,
        uploaded_by_user_id: int,
        version: Optional[str] = None  # NEU: Optional für Phase 2 (am Ende wegen Default)
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
        
        # 2. Berechne File Hash (SHA-256) - Optimiert für große Dateien (Chunk-basiert)
        import hashlib
        import os
        file_hash = None
        try:
            # Optimiert: Chunk-basiertes Lesen für große Dateien (spart RAM)
            sha256_hash = hashlib.sha256()
            chunk_size = 8192  # 8 KB Chunks (optimal für I/O)
            
            # Prüfe ob Datei existiert
            if not os.path.exists(file_path):
                raise ValueError(f"File not found: {file_path}")
            
            with open(file_path, 'rb') as f:
                # Lese Datei in Chunks (speichereffizient)
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    sha256_hash.update(chunk)
            
            hash_value = sha256_hash.hexdigest()
            file_hash = FileHash(hash_value)
        except FileNotFoundError:
            raise ValueError(f"File not found: {file_path}")
        except PermissionError:
            raise ValueError(f"Permission denied: {file_path}")
        except Exception as e:
            raise ValueError(f"Failed to calculate file hash: {str(e)}")
        
        # 3. Prüfe auf Duplikat - Optimiert mit früher Rückgabe
        existing_doc = None
        is_duplicate = False
        duplicate_of_document_id = None
        
        # Prüfe nur wenn Repository-Methode existiert und Hash berechnet wurde
        if file_hash and hasattr(self.upload_repo, 'find_by_hash'):
            try:
                existing_doc = await self.upload_repo.find_by_hash(file_hash)
                if existing_doc:
                    is_duplicate = True
                    duplicate_of_document_id = existing_doc.id
                    # NEU: Für Duplikate setze file_hash auf None, um UNIQUE Constraint zu vermeiden
                    # Nur das Original-Dokument behält den Hash
                    file_hash = None
            except Exception as e:
                # Bei Repository-Fehler: Logge Warnung, aber breche Upload nicht ab
                # (Duplikat-Prüfung ist "nice-to-have", Upload sollte funktionieren)
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to check for duplicate: {str(e)}")
                # Setze Werte auf Default (kein Duplikat erkannt)
                is_duplicate = False
                duplicate_of_document_id = None
        
        # 4. NEU: Prüfe auf existierende Version (Phase 2 - Versionierung)
        # Suche nach Dokumenten mit gleichem document_type_id + qm_chapter
        # Warnung wird später im Router angezeigt (nicht hier, da Use Case keine UI-Logik)
        existing_versions = []
        current_version = None  # NEU: Initialisiere current_version
        
        if version and qm_chapter and hasattr(self.upload_repo, 'find_by_document_type_and_chapter'):
            try:
                existing_docs = await self.upload_repo.find_by_document_type_and_chapter(
                    document_type_id=document_type_id,
                    qm_chapter=qm_chapter
                )
                # Filtere nach gleicher Version (für Warnung)
                existing_versions = [
                    doc for doc in existing_docs
                    if doc.metadata.version == version
                ]
                
                # NEU: Hole aktuelle Version (für Parent-Child Relationship)
                if hasattr(self.upload_repo, 'get_current_version'):
                    current_version = await self.upload_repo.get_current_version(
                        document_type_id=document_type_id,
                        qm_chapter=qm_chapter
                    )
                # Warnung wird später im Router angezeigt (wenn existing_versions nicht leer)
            except Exception as e:
                # Bei Repository-Fehler: Logge Warnung, aber breche Upload nicht ab
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to check for existing version: {str(e)}")
                existing_versions = []
                current_version = None
        
        # 6. Erstelle UploadedDocument Entity
        # NEU Phase 2: Setze Version-Felder basierend auf current_version
        parent_document_id = None
        document_series_id = None
        
        if current_version:
            # Existierende aktuelle Version → Neue Version (Parent-Child Relationship)
            parent_document_id = current_version.id
            document_series_id = current_version.document_series_id or current_version.id  # Falls keine Serie existiert, nutze ID als Serie
        else:
            # Keine aktuelle Version → Erste Version (kein Parent)
            parent_document_id = None
            document_series_id = None  # Wird nach Save gesetzt (benötigt ID)
        
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
            interest_group_ids=[],
            file_hash=file_hash,  # Phase 1.1
            is_duplicate=is_duplicate,  # Phase 1.1
            duplicate_of_document_id=duplicate_of_document_id,  # Phase 1.1
            # Phase 2 - Versionierung
            parent_document_id=parent_document_id,  # NEU: Gesetzt wenn current_version existiert
            document_series_id=document_series_id,  # NEU: Gesetzt wenn current_version existiert
            is_current_version=True  # NEU: Neue Version ist immer aktuell
        )
        
        # 7. Speichere in Repository
        saved_document = await self.upload_repo.save(document)
        
        # 8. NEU: Setze document_series_id nach Save (benötigt ID) und archiviere alte Version
        if not saved_document.document_series_id:
            # Erste Version → Nutze eigene ID als Serie
            saved_document.document_series_id = saved_document.id
            saved_document = await self.upload_repo.save(saved_document)
        elif current_version:
            # Neue Version → Archiviere alte Version (is_current_version=False)
            current_version.is_current_version = False
            archived_version = await self.upload_repo.save(current_version)
            
            # NEU Phase 5: Publiziere DocumentVersionArchivedEvent für RAG Cleanup
            if hasattr(self, 'event_publisher') and self.event_publisher:
                from ..domain.events import DocumentVersionArchivedEvent
                event = DocumentVersionArchivedEvent(
                    old_version_id=archived_version.id,
                    new_version_id=saved_document.id,
                    document_series_id=saved_document.document_series_id,
                    archived_by_user_id=uploaded_by_user_id,
                    timestamp=datetime.utcnow()
                )
                await self.event_publisher.publish(event)
        
        # 9. Publiziere Event (TODO: Event Bus implementieren)
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
        
        # RBAC Multi-Level: Context-specific Permission Check
        # Hole Dokument-Interest-Group-IDs
        document_ig_ids = document.interest_group_ids if hasattr(document, 'interest_group_ids') else []
        
        # Bestimme required_level für diese Transition aus Permission Service
        from_status_value = document.workflow_status.value
        to_status_value = new_status.value
        
        # Hole required_level aus Permission Service WORKFLOW_RULES (falls verfügbar)
        required_level = None
        if hasattr(self.permission_service, 'WORKFLOW_RULES'):
            workflow_rules = self.permission_service.WORKFLOW_RULES
            required_level = workflow_rules.get(document.workflow_status, {}).get(new_status, None)
        
        # Fallback: Bestimme required_level basierend auf Workflow-Rules
        if required_level is None:
            # Standard Workflow Rules:
            # draft → reviewed: Level 3
            # draft → approved: Level 4
            # reviewed → approved: Level 4
            # reviewed → rejected: Level 4
            # approved → rejected: Level 4 (NEU: Auch Approved-Dokumente können zurückgewiesen werden)
            # rejected → draft: Level 3
            if document.workflow_status.value == 'draft' and new_status.value == 'reviewed':
                required_level = 3
            elif document.workflow_status.value == 'draft' and new_status.value == 'approved':
                required_level = 4
            elif document.workflow_status.value == 'reviewed' and new_status.value in ('approved', 'rejected'):
                required_level = 4
            elif document.workflow_status.value == 'approved' and new_status.value == 'rejected':
                required_level = 4  # NEU: Approved → Rejected erlaubt (z.B. für Validierung)
            elif document.workflow_status.value == 'rejected' and new_status.value == 'draft':
                required_level = 3
            else:
                required_level = 5  # Ungültige Transition
        
        # Prüfe Context-specific Permission (falls Permission Service die Methode hat)
        if required_level is not None and hasattr(self.permission_service, 'can_perform_action_on_document'):
            can_perform = self.permission_service.can_perform_action_on_document(
                user_id=user_id,
                document_interest_group_ids=document_ig_ids,
                action=f"change_status_{from_status_value}_to_{to_status_value}",
                required_level=required_level
            )
            if not can_perform:
                raise PermissionError(
                    f"User {user_id} hat keine Berechtigung, dieses Dokument von "
                    f"{from_status_value} nach {to_status_value} zu ändern. "
                    f"Benötigt Level {required_level} für die Interest Group(s) dieses Dokuments."
                )
        
        # Prüfe globale Berechtigung (Fallback für Legacy oder wenn Context-Check nicht verfügbar)
        can_change = self.permission_service.can_change_status(
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


class RejectDocumentUseCase:
    """
    Use Case: Dokument zurückweisen (Rejection mit Kommentar-Pflicht).
    
    Verantwortlichkeiten:
    - Validiere dass Dokument zurückgewiesen werden kann (Status REVIEWED)
    - Prüfe dass Rejection-Kommentar vorhanden ist (MUSS)
    - Setze Status auf REJECTED
    - Publiziere DocumentRejectedEvent (NEU Phase 5)
    - Dokument verschwindet aus Kanban (via Filter)
    - Dokument bleibt in Dokumenten-Tabelle sichtbar
    
    Args:
        upload_repository: UploadRepository Interface
        comment_repository: DocumentCommentRepository Interface
        event_publisher: Optional EventPublisher Interface (für Cross-Context Events)
    """
    
    def __init__(
        self,
        upload_repository: UploadRepository,
        comment_repository: DocumentCommentRepository,
        event_publisher=None  # Optional, keine Cross-Context Import
    ):
        self.upload_repository = upload_repository
        self.comment_repository = comment_repository
        self.event_publisher = event_publisher
    
    async def execute(
        self,
        document_id: int,
        rejected_by_user_id: int,
        rejection_reason: str
    ) -> UploadedDocument:
        """
        Weise Dokument zurück (Rejection).
        
        Args:
            document_id: Dokument ID
            rejected_by_user_id: User ID des Zurückweisenden
            rejection_reason: Grund für Zurückweisung (MUSS nicht leer sein)
            
        Returns:
            Aktualisiertes UploadedDocument mit Status REJECTED
            
        Raises:
            ValueError: Wenn Dokument nicht existiert oder kein Kommentar vorhanden
        """
        from ..domain.value_objects import WorkflowStatus
        
        # Validiere Parameter
        if rejected_by_user_id <= 0:
            raise ValueError("rejected_by_user_id must be positive")
        
        # Lade Dokument
        document = await self.upload_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Validiere Status: Nur REVIEWED kann zurückgewiesen werden
        if document.workflow_status != WorkflowStatus.REVIEWED:
            raise ValueError(
                f"Cannot reject document with status {document.workflow_status.value}. "
                f"Only documents with status 'reviewed' can be rejected."
            )
        
        # NEU Phase 3: Prüfe dass Rejection-Kommentar vorhanden ist (MUSS)
        # Kommentar kann vor oder nach Status-Änderung erstellt werden
        # Wir prüfen ob bereits ein Rejection-Kommentar existiert
        rejection_comments = await self.comment_repository.get_by_document_id_and_type(
            document_id=document_id,
            comment_type="rejection"
        )
        
        # NEU Phase 3: Rejection erfordert Kommentar (MUSS)
        # Wenn kein Kommentar vorhanden UND rejection_reason leer/None → Fehler
        if not rejection_comments:
            if not rejection_reason or not rejection_reason.strip():
                raise ValueError(
                    "Rejection requires a comment. Please provide a rejection_reason "
                    "or create a rejection comment before rejecting the document."
                )
        
        # Wenn rejection_reason angegeben, erstelle Kommentar (falls noch keiner existiert)
        if rejection_reason.strip() and not rejection_comments:
            from datetime import datetime
            from ..domain.entities import DocumentComment
            
            # Erstelle Rejection-Kommentar
            rejection_comment = DocumentComment(
                id=0,  # Wird vom Repository gesetzt
                document_id=document_id,
                user_id=rejected_by_user_id,
                comment_text=rejection_reason.strip(),
                comment_type="rejection",
                created_at=datetime.utcnow()
            )
            
            await self.comment_repository.add(rejection_comment)
        
        # Setze Status auf REJECTED
        event = document.change_workflow_status(
            new_status=WorkflowStatus.REJECTED,
            user_id=rejected_by_user_id,
            reason=rejection_reason
        )
        
        # Speichere Änderung
        updated_document = await self.upload_repository.save(document)
        
        # NEU Phase 5: Publiziere DocumentRejectedEvent für RAG Cleanup
        if self.event_publisher:
            from ..domain.events import DocumentRejectedEvent
            from datetime import datetime
            event = DocumentRejectedEvent(
                document_id=updated_document.id,
                rejected_by_user_id=rejected_by_user_id,
                rejection_reason=rejection_reason,
                timestamp=datetime.utcnow()
            )
            await self.event_publisher.publish(event)
        
        return updated_document


class ArchiveDocumentUseCase:
    """
    Use Case: Dokument archivieren.
    
    Verantwortlichkeiten:
    - Validiere dass Dokument existiert
    - Setze workflow_status auf ARCHIVED
    - Setze archived_at, archived_by_user_id, archive_reason
    - Publiziere DocumentArchivedEvent (NEU Phase 5)
    - Speichere Änderung
    
    Args:
        upload_repository: UploadRepository Interface
        event_publisher: Optional EventPublisher Interface (für Cross-Context Events)
    """
    
    def __init__(
        self,
        upload_repository: UploadRepository,
        event_publisher=None  # Optional, keine Cross-Context Import
    ):
        self.upload_repository = upload_repository
        self.event_publisher = event_publisher
    
    async def execute(
        self,
        document_id: int,
        archived_by_user_id: int,
        reason: Optional[str] = None
    ) -> UploadedDocument:
        """
        Archiviere Dokument.
        
        Args:
            document_id: Dokument ID
            archived_by_user_id: User ID des Archivierers
            reason: Optionaler Grund für Archivierung
            
        Returns:
            Aktualisiertes UploadedDocument mit Status ARCHIVED
            
        Raises:
            ValueError: Wenn Dokument nicht existiert oder Parameter ungültig
        """
        from datetime import datetime
        from ..domain.value_objects import WorkflowStatus
        
        # Validiere Parameter
        if archived_by_user_id <= 0:
            raise ValueError("archived_by_user_id must be positive")
        
        # Lade Dokument
        document = await self.upload_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Archive: Setze Status und Felder
        document.workflow_status = WorkflowStatus.ARCHIVED
        document.archived_at = datetime.utcnow()
        document.archived_by_user_id = archived_by_user_id
        document.archive_reason = reason.strip() if reason and reason.strip() else None
        
        # Speichere Änderung
        updated_document = await self.upload_repository.save(document)
        
        # NEU Phase 5: Publiziere DocumentArchivedEvent für RAG Cleanup
        if self.event_publisher:
            from ..domain.events import DocumentArchivedEvent
            event = DocumentArchivedEvent(
                document_id=updated_document.id,
                archived_by_user_id=archived_by_user_id,
                archive_reason=reason,
                timestamp=datetime.utcnow()
            )
            await self.event_publisher.publish(event)
        
        return updated_document


class SoftDeleteDocumentUseCase:
    """
    Use Case: Dokument Soft Delete.
    
    Verantwortlichkeiten:
    - Validiere dass Dokument existiert
    - Setze workflow_status auf DELETED
    - Setze deleted_at, deleted_by_user_id, deletion_reason
    - Publiziere DocumentDeletedEvent (NEU Phase 5)
    - Speichere Änderung
    
    Args:
        upload_repository: UploadRepository Interface
        event_publisher: Optional EventPublisher Interface (für Cross-Context Events)
    """
    
    def __init__(
        self,
        upload_repository: UploadRepository,
        event_publisher=None  # Optional, keine Cross-Context Import
    ):
        self.upload_repository = upload_repository
        self.event_publisher = event_publisher
    
    async def execute(
        self,
        document_id: int,
        deleted_by_user_id: int,
        reason: str
    ) -> UploadedDocument:
        """
        Lösche Dokument (Soft Delete).
        
        Args:
            document_id: Dokument ID
            deleted_by_user_id: User ID des Löschers
            reason: Grund für Löschung
            
        Returns:
            Aktualisiertes UploadedDocument mit Status DELETED
            
        Raises:
            ValueError: Wenn Dokument nicht existiert oder Parameter ungültig
        """
        from datetime import datetime
        from ..domain.value_objects import WorkflowStatus
        
        # Validiere Parameter
        if deleted_by_user_id <= 0:
            raise ValueError("deleted_by_user_id must be positive")
        
        if not reason or not reason.strip():
            raise ValueError("reason cannot be empty")
        
        # Lade Dokument
        document = await self.upload_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Soft Delete: Setze Status und Felder
        document.workflow_status = WorkflowStatus.DELETED
        document.deleted_at = datetime.utcnow()
        document.deleted_by_user_id = deleted_by_user_id
        document.deletion_reason = reason.strip()
        
        # Speichere Änderung
        updated_document = await self.upload_repository.save(document)
        
        # NEU Phase 5: Publiziere DocumentDeletedEvent für RAG Cleanup
        if self.event_publisher:
            from ..domain.events import DocumentDeletedEvent
            event = DocumentDeletedEvent(
                document_id=updated_document.id,
                deleted_by_user_id=deleted_by_user_id,
                deletion_reason=reason,
                timestamp=datetime.utcnow()
            )
            await self.event_publisher.publish(event)
        
        return updated_document


class GetArchivedDocumentsUseCase:
    """
    Use Case: Hole archivierte Dokumente.
    
    Verantwortlichkeiten:
    - Lade gelöschte Dokumente aus Repository
    - Filtere nach optionalen Parametern
    - Sortiere nach deleted_at DESC (neueste zuerst)
    """
    
    def __init__(self, upload_repository: "UploadRepository"):
        self.upload_repository = upload_repository
    
    async def execute(
        self,
        limit: int = 100,
        offset: int = 0,
        document_type_id: Optional[int] = None,
        deleted_before: Optional[datetime] = None,
        deleted_after: Optional[datetime] = None
    ) -> List[UploadedDocument]:
        """
        Hole archivierte Dokumente.
        
        Args:
            limit: Maximale Anzahl Ergebnisse
            offset: Offset für Pagination
            document_type_id: Optional - Filter nach Dokumenttyp
            deleted_before: Optional - Filter: gelöscht vor diesem Datum
            deleted_after: Optional - Filter: gelöscht nach diesem Datum
            
        Returns:
            Liste von gelöschten UploadedDocuments
        """
        return await self.upload_repository.find_archived(
            limit=limit,
            offset=offset,
            document_type_id=document_type_id,
            deleted_before=deleted_before,
            deleted_after=deleted_after
        )


class HardDeleteDocumentUseCase:
    """
    Use Case: Endgültige Löschung (nur Level 5).
    
    Verantwortlichkeiten:
    - Prüfe confirmation == "LÖSCHEN"
    - Lösche physische Dateien (file_path)
    - Lösche Preview-Bilder
    - RAG ist bereits gelöscht (bei Soft Delete passiert)
    - Lösche DB-Eintrag (oder setze hard_deleted Flag)
    - Publiziere DocumentHardDeletedEvent (EDD: für Audit/Backup)
    """
    
    def __init__(
        self,
        upload_repository: "UploadRepository",
        page_repository: Optional["DocumentPageRepository"] = None,
        event_publisher: Optional[Any] = None
    ):
        self.upload_repository = upload_repository
        self.page_repository = page_repository
        self.event_publisher = event_publisher
    
    async def execute(
        self,
        document_id: int,
        deleted_by_user_id: int,
        confirmation: str
    ) -> Dict[str, Any]:
        """
        Endgültige Löschung.
        
        Args:
            document_id: Dokument ID
            deleted_by_user_id: User ID der Löschung durchführt
            confirmation: Muss "LÖSCHEN" sein (Sicherheits-Bestätigung)
            
        Returns:
            Dict mit success, message
            
        Raises:
            ValueError: Wenn confirmation nicht "LÖSCHEN" ist
            ValueError: Wenn Dokument nicht gefunden
        """
        import os
        
        # Prüfe confirmation
        if confirmation.strip().upper() != "LÖSCHEN":
            raise ValueError("Bestätigung fehlgeschlagen. Bitte geben Sie 'LÖSCHEN' ein.")
        
        # Lade Dokument
        document = await self.upload_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Dokument {document_id} nicht gefunden")
        
        # Lösche physische Datei
        files_deleted = []
        if document.file_path:
            # FilePath hat 'path' Attribut, nicht 'value'
            file_path = document.file_path.path if hasattr(document.file_path, 'path') else str(document.file_path)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    files_deleted.append(f"Datei: {file_path}")
                except Exception as e:
                    print(f"WARNING: Konnte Datei nicht löschen: {file_path}, Error: {e}")
        
        # Lösche Preview-Bilder (von Pages)
        if self.page_repository:
            pages = await self.page_repository.get_by_document_id(document_id)
            for page in pages:
                if page.preview_image_path:
                    # FilePath hat 'path' Attribut, nicht 'value'
                    preview_path = page.preview_image_path.path if hasattr(page.preview_image_path, 'path') else str(page.preview_image_path)
                    if os.path.exists(preview_path):
                        try:
                            os.remove(preview_path)
                            files_deleted.append(f"Preview: {preview_path}")
                        except Exception as e:
                            print(f"WARNING: Konnte Preview nicht löschen: {preview_path}, Error: {e}")
        
        # Lösche DB-Eintrag (oder setze hard_deleted Flag)
        # OPTION 1: Hard Delete (komplett entfernen)
        # await self.upload_repository.delete(document_id)
        
        # OPTION 2: Hard Delete Flag (für Audit-Trail)
        # document.hard_deleted = True
        # document.hard_deleted_at = datetime.utcnow()
        # document.hard_deleted_by_user_id = deleted_by_user_id
        # await self.upload_repository.save(document)
        
        # Aktuell: OPTION 1 (komplett entfernen)
        # TODO: Optional: Hard Delete Flag für Audit-Trail implementieren
        deleted = await self.upload_repository.delete(document_id)
        
        # EDD: Publiziere DocumentHardDeletedEvent (für Audit/Backup)
        if self.event_publisher:
            from ..domain.events import DocumentHardDeletedEvent
            event = DocumentHardDeletedEvent(
                document_id=document_id,
                deleted_by_user_id=deleted_by_user_id,
                deletion_reason=document.deletion_reason if hasattr(document, 'deletion_reason') else None,
                files_deleted=files_deleted,
                timestamp=datetime.utcnow()
            )
            await self.event_publisher.publish(event)
        
        return {
            "success": deleted,
            "message": f"Dokument {document_id} endgültig gelöscht. {len(files_deleted)} Dateien entfernt.",
            "files_deleted": files_deleted
        }


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
        document_type_id: Optional[int] = None,
        exclude_rag_indexed: bool = True,  # NEU: Für Kanban-Workflow indexierte Dokumente ausschließen
        exclude_rejected: bool = True  # NEU Phase 3: Rejected Dokumente für Kanban ausschließen
    ) -> List[UploadedDocument]:
        """
        Hole Dokumente nach Workflow-Status.
        
        Args:
            status: Workflow-Status
            interest_group_ids: Optional filter by Interest Groups
            document_type_id: Optional filter by Document Type
            exclude_rag_indexed: Wenn True, werden RAG-indexierte Dokumente ausgeschlossen (für Kanban-Workflow)
            
        Returns:
            Liste der Dokumente mit dem Status
        """
        documents = await self.upload_repository.get_by_workflow_status(
            status=status,
            interest_group_ids=interest_group_ids,
            document_type_id=document_type_id,
            exclude_rag_indexed=exclude_rag_indexed,
            exclude_rejected=exclude_rejected  # NEU Phase 3: Rejected für Kanban ausschließen
        )
        
        # NEU Phase 3: Filtere rejected Dokumente aus (für Kanban-Workflow)
        # Wenn exclude_rejected=True, dann sollten rejected Dokumente nicht zurückgegeben werden
        if exclude_rejected:
            from ..domain.value_objects import WorkflowStatus
            documents = [
                doc for doc in documents 
                if doc.workflow_status != WorkflowStatus.REJECTED
            ]
        
        return documents

