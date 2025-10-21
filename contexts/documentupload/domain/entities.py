"""
Domain Entities für Document Upload Context

Entities sind Objekte mit einer eindeutigen Identität, die sich über die Zeit ändern können.
Sie repräsentieren die Kerngeschäftslogik des Systems.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
from .value_objects import (
    FileType,
    ProcessingMethod,
    ProcessingStatus,
    DocumentMetadata,
    PageDimensions,
    FilePath,
    AIResponse
)


@dataclass
class UploadedDocument:
    """
    Hochgeladenes Dokument - Aggregate Root.
    
    Ein UploadedDocument ist ein Aggregate Root im DDD-Sinne.
    Es verwaltet DocumentPages und InterestGroupAssignments.
    
    Attributes:
        id: Eindeutige ID (None bei neuen Entities)
        file_type: Dateityp (PDF, DOCX, PNG, JPG)
        file_size_bytes: Dateigröße in Bytes
        document_type_id: FK zu DocumentType
        metadata: Dokumenten-Metadaten (Value Object)
        file_path: Pfad zum Original (Value Object)
        processing_method: OCR oder Vision
        processing_status: Status der Verarbeitung
        uploaded_by_user_id: User ID des Uploaders
        uploaded_at: Upload-Zeitstempel
        pages: Liste der Seiten (Aggregate)
        interest_group_ids: Zugewiesene Interest Groups
    """
    id: Optional[int]
    file_type: FileType
    file_size_bytes: int
    document_type_id: int
    metadata: DocumentMetadata
    file_path: FilePath
    processing_method: ProcessingMethod
    processing_status: ProcessingStatus
    uploaded_by_user_id: int
    uploaded_at: datetime
    pages: List["DocumentPage"] = field(default_factory=list)
    interest_group_ids: List[int] = field(default_factory=list)
    
    def __post_init__(self):
        """Validiere Entity nach Initialisierung."""
        if self.file_size_bytes <= 0:
            raise ValueError("File size must be positive")
        if self.file_size_bytes > 50 * 1024 * 1024:  # 50 MB
            raise ValueError("File size exceeds maximum (50 MB)")
        if self.uploaded_by_user_id <= 0:
            raise ValueError("Invalid user ID")
        if self.document_type_id <= 0:
            raise ValueError("Invalid document type ID")
    
    @property
    def page_count(self) -> int:
        """Returniere Anzahl Seiten."""
        return len(self.pages)
    
    @property
    def is_multi_page(self) -> bool:
        """Prüfe ob mehrseitig."""
        return self.page_count > 1
    
    @property
    def is_processing_complete(self) -> bool:
        """Prüfe ob Verarbeitung abgeschlossen."""
        return self.processing_status == ProcessingStatus.COMPLETED
    
    @property
    def is_processing_failed(self) -> bool:
        """Prüfe ob Verarbeitung fehlgeschlagen."""
        return self.processing_status == ProcessingStatus.FAILED
    
    def add_page(self, page: "DocumentPage") -> None:
        """
        Füge Seite hinzu (Aggregate-Logik).
        
        Args:
            page: DocumentPage Entity
            
        Raises:
            ValueError: Wenn Seite bereits existiert
        """
        if any(p.page_number == page.page_number for p in self.pages):
            raise ValueError(f"Page {page.page_number} already exists")
        
        self.pages.append(page)
        self.pages.sort(key=lambda p: p.page_number)
    
    def assign_interest_group(self, interest_group_id: int) -> None:
        """
        Weise Interest Group zu (Aggregate-Logik).
        
        Args:
            interest_group_id: ID der Interest Group
            
        Raises:
            ValueError: Wenn bereits zugewiesen
        """
        if interest_group_id in self.interest_group_ids:
            raise ValueError(f"Interest group {interest_group_id} already assigned")
        
        self.interest_group_ids.append(interest_group_id)
    
    def start_processing(self) -> None:
        """Setze Status auf PROCESSING (Business Logic)."""
        if self.processing_status != ProcessingStatus.PENDING:
            raise ValueError(f"Cannot start processing from status {self.processing_status}")
        
        self.processing_status = ProcessingStatus.PROCESSING
    
    def complete_processing(self) -> None:
        """Setze Status auf COMPLETED (Business Logic)."""
        if self.processing_status != ProcessingStatus.PROCESSING:
            raise ValueError(f"Cannot complete processing from status {self.processing_status}")
        
        self.processing_status = ProcessingStatus.COMPLETED
    
    def fail_processing(self, error: str) -> None:
        """
        Setze Status auf FAILED (Business Logic).
        
        Args:
            error: Fehlermeldung
        """
        if self.processing_status not in [ProcessingStatus.PENDING, ProcessingStatus.PROCESSING]:
            raise ValueError(f"Cannot fail processing from status {self.processing_status}")
        
        self.processing_status = ProcessingStatus.FAILED
        # TODO: Store error message (needs additional field)


@dataclass
class DocumentPage:
    """
    Einzelne Seite eines Dokuments.
    
    Teil des UploadedDocument Aggregates.
    
    Attributes:
        id: Eindeutige ID (None bei neuen Entities)
        upload_document_id: FK zu UploadedDocument
        page_number: Seitennummer (1-basiert)
        preview_image_path: Pfad zum Preview-Bild
        thumbnail_path: Pfad zum Thumbnail
        dimensions: Seiten-Dimensionen (Value Object)
        created_at: Erstellungs-Zeitstempel
    """
    id: Optional[int]
    upload_document_id: Optional[int]
    page_number: int
    preview_image_path: FilePath
    thumbnail_path: Optional[FilePath]
    dimensions: Optional[PageDimensions]
    created_at: datetime
    
    def __post_init__(self):
        """Validiere Entity nach Initialisierung."""
        if self.page_number <= 0:
            raise ValueError("Page number must be positive (1-based)")
    
    @property
    def has_thumbnail(self) -> bool:
        """Prüfe ob Thumbnail vorhanden."""
        return self.thumbnail_path is not None
    
    @property
    def has_dimensions(self) -> bool:
        """Prüfe ob Dimensionen vorhanden."""
        return self.dimensions is not None


@dataclass
class InterestGroupAssignment:
    """
    Zuweisung eines Dokuments zu einer Interest Group.
    
    Teil des UploadedDocument Aggregates.
    
    Attributes:
        id: Eindeutige ID (None bei neuen Entities)
        upload_document_id: FK zu UploadedDocument
        interest_group_id: FK zu InterestGroup
        assigned_by_user_id: User ID des Zuweisers
        assigned_at: Zuweisungs-Zeitstempel
    """
    id: Optional[int]
    upload_document_id: Optional[int]
    interest_group_id: int
    assigned_by_user_id: int
    assigned_at: datetime
    
    def __post_init__(self):
        """Validiere Entity nach Initialisierung."""
        if self.interest_group_id <= 0:
            raise ValueError("Invalid interest group ID")
        if self.assigned_by_user_id <= 0:
            raise ValueError("Invalid user ID")


@dataclass
class AIProcessingResult:
    """
    AI-Verarbeitungs-Ergebnis für eine Dokumentseite.
    
    Speichert die strukturierte JSON-Response vom AI-Modell für eine einzelne Seite.
    1:1 Beziehung zu DocumentPage.
    
    Attributes:
        id: Eindeutige ID (None bei neuen Entities)
        upload_document_id: FK zu UploadedDocument
        upload_document_page_id: FK zu DocumentPage (unique)
        prompt_template_id: FK zu PromptTemplate
        ai_model_id: FK zu AIModel
        model_name: Name des AI-Modells (z.B. 'gpt-4o-mini')
        json_response: Strukturierte JSON-Antwort (String)
        processing_status: completed, failed, partial
        tokens_sent: Anzahl gesendeter Tokens
        tokens_received: Anzahl empfangener Tokens
        total_tokens: Gesamtzahl Tokens
        response_time_ms: Response-Zeit in Millisekunden
        error_message: Fehler-Nachricht (falls failed)
        processed_at: Verarbeitungs-Zeitstempel
    """
    id: Optional[int]
    upload_document_id: int
    upload_document_page_id: int
    prompt_template_id: int
    ai_model_id: str  # Changed to str (model identifier like 'gemini-2.5-flash')
    model_name: str
    json_response: str
    processing_status: str  # "completed", "failed", "partial"
    tokens_sent: Optional[int] = None
    tokens_received: Optional[int] = None
    total_tokens: Optional[int] = None
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    processed_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validiere Entity nach Initialisierung."""
        if self.upload_document_id <= 0:
            raise ValueError("Invalid upload_document_id")
        if self.upload_document_page_id <= 0:
            raise ValueError("Invalid upload_document_page_id")
        if self.prompt_template_id <= 0:
            raise ValueError("Invalid prompt_template_id")
        if not self.ai_model_id:  # Changed: check for empty string instead of <= 0
            raise ValueError("Invalid ai_model_id")
        if not self.model_name:
            raise ValueError("model_name cannot be empty")
        if not self.json_response:
            raise ValueError("json_response cannot be empty")
        
        # Validiere processing_status
        valid_statuses = ["completed", "failed", "partial"]
        if self.processing_status not in valid_statuses:
            raise ValueError(f"Invalid processing_status. Must be one of: {valid_statuses}")
        
        # Berechne total_tokens falls nicht gesetzt
        if self.total_tokens is None and self.tokens_sent is not None and self.tokens_received is not None:
            object.__setattr__(self, 'total_tokens', self.tokens_sent + self.tokens_received)
    
    def is_completed(self) -> bool:
        """Prüfe ob Verarbeitung erfolgreich abgeschlossen."""
        return self.processing_status == "completed"
    
    def is_failed(self) -> bool:
        """Prüfe ob Verarbeitung fehlgeschlagen."""
        return self.processing_status == "failed"
    
    def is_partial(self) -> bool:
        """Prüfe ob Verarbeitung teilweise erfolgreich."""
        return self.processing_status == "partial"
    
    def get_parsed_json(self) -> Dict[str, Any]:
        """
        Parse JSON-Response zu Dictionary.
        
        Returns:
            Parsed JSON als Dictionary
            
        Raises:
            json.JSONDecodeError: Falls JSON ungültig
        """
        return json.loads(self.json_response)
    
    def update_with_new_data(self, new_ai_data: Dict[str, Any]) -> None:
        """
        Update AIProcessingResult mit neuen AI-Daten.
        
        Args:
            new_ai_data: Dictionary mit neuen AI-Verarbeitungsdaten
        """
        # Update JSON Response
        if "json_response" in new_ai_data:
            object.__setattr__(self, 'json_response', new_ai_data["json_response"])
        
        # Update Token-Informationen
        if "tokens_sent" in new_ai_data:
            object.__setattr__(self, 'tokens_sent', new_ai_data["tokens_sent"])
        if "tokens_received" in new_ai_data:
            object.__setattr__(self, 'tokens_received', new_ai_data["tokens_received"])
        if "response_time_ms" in new_ai_data:
            object.__setattr__(self, 'response_time_ms', new_ai_data["response_time_ms"])
        
        # Update Model Name falls geändert
        if "model_name" in new_ai_data:
            object.__setattr__(self, 'model_name', new_ai_data["model_name"])
        
        # Update processed_at timestamp
        object.__setattr__(self, 'processed_at', datetime.utcnow())
        
        # Recalculate total_tokens
        if self.tokens_sent is not None and self.tokens_received is not None:
            object.__setattr__(self, 'total_tokens', self.tokens_sent + self.tokens_received)
    
    def get_ai_response_vo(self) -> AIResponse:
        """
        Konvertiere zu AIResponse Value Object.
        
        Returns:
            AIResponse Value Object
        """
        return AIResponse(
            json_data=self.json_response,
            tokens_sent=self.tokens_sent or 0,
            tokens_received=self.tokens_received or 0,
            response_time_ms=self.response_time_ms or 0
        )

