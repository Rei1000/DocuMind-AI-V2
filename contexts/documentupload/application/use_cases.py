"""
Use Cases für Document Upload Context

Use Cases orchestrieren die Business Logic und koordinieren zwischen
Domain Entities, Repositories und Services.
"""

from datetime import datetime
from typing import List, Optional
from ..domain.entities import (
    UploadedDocument,
    DocumentPage,
    InterestGroupAssignment
)
from ..domain.value_objects import (
    FileType,
    ProcessingMethod,
    ProcessingStatus,
    DocumentMetadata,
    PageDimensions,
    FilePath
)
from ..domain.repositories import (
    UploadRepository,
    DocumentPageRepository,
    InterestGroupAssignmentRepository
)
from ..domain.events import (
    DocumentUploadedEvent,
    PagesGeneratedEvent,
    InterestGroupsAssignedEvent
)


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

