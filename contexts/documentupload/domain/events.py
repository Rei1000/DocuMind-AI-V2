"""
Domain Events für Document Upload Context

Domain Events repräsentieren Ereignisse, die im System passiert sind.
Sie werden von anderen Contexts konsumiert (Event-Driven Architecture).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from .value_objects import WorkflowStatus


@dataclass(frozen=True)
class DocumentUploadedEvent:
    """
    Event: Dokument wurde hochgeladen.
    
    Wird publiziert nach erfolgreichem Upload.
    
    Subscribers:
    - documentworkflow.DocumentUploadedEventHandler → Erstellt Workflow-Entry
    
    Attributes:
        document_id: ID des hochgeladenen Dokuments
        filename: Dateiname
        document_type_id: Dokumenttyp ID
        uploaded_by_user_id: Uploader User ID
        page_count: Anzahl Seiten
        interest_group_ids: Zugewiesene Interest Groups
        timestamp: Event-Zeitstempel
    """
    document_id: int
    filename: str
    document_type_id: int
    uploaded_by_user_id: int
    page_count: int
    interest_group_ids: List[int]
    timestamp: datetime


@dataclass(frozen=True)
class PagesGeneratedEvent:
    """
    Event: Seiten wurden generiert (Preview + Thumbnails).
    
    Wird publiziert nach erfolgreicher Preview-Generierung.
    
    Attributes:
        document_id: ID des Dokuments
        page_count: Anzahl generierter Seiten
        timestamp: Event-Zeitstempel
    """
    document_id: int
    page_count: int
    timestamp: datetime


@dataclass(frozen=True)
class InterestGroupsAssignedEvent:
    """
    Event: Interest Groups wurden zugewiesen.
    
    Wird publiziert nach erfolgreicher Zuweisung.
    
    Attributes:
        document_id: ID des Dokuments
        interest_group_ids: Zugewiesene Interest Groups
        assigned_by_user_id: User ID des Zuweisers
        timestamp: Event-Zeitstempel
    """
    document_id: int
    interest_group_ids: List[int]
    assigned_by_user_id: int
    timestamp: datetime


@dataclass(frozen=True)
class ProcessingStartedEvent:
    """
    Event: Verarbeitung (OCR/Vision) wurde gestartet.
    
    Wird publiziert wenn Processing beginnt.
    
    Attributes:
        document_id: ID des Dokuments
        processing_method: OCR oder Vision
        timestamp: Event-Zeitstempel
    """
    document_id: int
    processing_method: str
    timestamp: datetime


@dataclass(frozen=True)
class ProcessingCompletedEvent:
    """
    Event: Verarbeitung (OCR/Vision) wurde abgeschlossen.
    
    Wird publiziert nach erfolgreicher Verarbeitung.
    
    Attributes:
        document_id: ID des Dokuments
        processing_method: OCR oder Vision
        timestamp: Event-Zeitstempel
    """
    document_id: int
    processing_method: str
    timestamp: datetime


@dataclass(frozen=True)
class ProcessingFailedEvent:
    """
    Event: Verarbeitung (OCR/Vision) ist fehlgeschlagen.
    
    Wird publiziert bei Verarbeitungs-Fehler.
    
    Attributes:
        document_id: ID des Dokuments
        processing_method: OCR oder Vision
        error_message: Fehlermeldung
        timestamp: Event-Zeitstempel
    """
    document_id: int
    processing_method: str
    error_message: str
    timestamp: datetime


@dataclass(frozen=True)
class DocumentWorkflowChangedEvent:
    """
    Event: Dokument-Workflow-Status wurde geändert.
    
    Wird publiziert nach erfolgreicher Status-Änderung.
    
    Subscribers:
    - Notifications: Benachrichtige betroffene User
    - Audit: Logge Status-Änderung
    - RAG: Bei APPROVED → Indexiere für RAG
    
    Attributes:
        document_id: ID des Dokuments
        old_status: Vorheriger Status
        new_status: Neuer Status
        changed_by_user_id: User ID des Änderers
        reason: Grund für die Änderung
        timestamp: Event-Zeitstempel
    """
    document_id: int
    old_status: WorkflowStatus
    new_status: WorkflowStatus
    changed_by_user_id: int
    reason: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validiere DocumentWorkflowChangedEvent nach Initialisierung."""
        if self.document_id <= 0:
            raise ValueError("document_id must be positive")
        
        if self.changed_by_user_id <= 0:
            raise ValueError("changed_by_user_id must be positive")
        
        if not self.reason or not self.reason.strip():
            raise ValueError("reason cannot be empty")
        
        if self.old_status == self.new_status:
            raise ValueError("old_status and new_status must be different")


@dataclass(frozen=True)
class DocumentRejectedEvent:
    """
    Event: Dokument wurde zurückgewiesen.
    
    NEU Phase 3 & 5: Wird publiziert wenn Dokument rejected wird.
    
    Subscribers:
    - ragintegration.DocumentRejectedEventHandler → Entferne aus RAG Index
    
    Attributes:
        document_id: ID des Dokuments
        rejected_by_user_id: User ID des Zurückweisenden
        rejection_reason: Grund für Zurückweisung
        timestamp: Event-Zeitstempel
    """
    document_id: int
    rejected_by_user_id: int
    rejection_reason: str
    timestamp: datetime


@dataclass(frozen=True)
class DocumentDeletedEvent:
    """
    Event: Dokument wurde soft-deleted.
    
    NEU Phase 1.3 & 5: Wird publiziert wenn Dokument soft-deleted wird.
    
    Subscribers:
    - ragintegration.DocumentDeletedEventHandler → Entferne aus RAG Index
    
    Attributes:
        document_id: ID des Dokuments
        deleted_by_user_id: User ID des Löschers
        deletion_reason: Grund für Löschung
        timestamp: Event-Zeitstempel
    """
    document_id: int
    deleted_by_user_id: int
    deletion_reason: str
    timestamp: datetime


@dataclass(frozen=True)
class DocumentArchivedEvent:
    """
    Event: Dokument wurde archiviert.
    
    NEU Phase 1.4 & 5: Wird publiziert wenn Dokument archived wird.
    
    Subscribers:
    - ragintegration.DocumentArchivedEventHandler → Entferne aus RAG Index
    
    Attributes:
        document_id: ID des Dokuments
        archived_by_user_id: User ID des Archivierers
        archive_reason: Grund für Archivierung
        timestamp: Event-Zeitstempel
    """
    document_id: int
    archived_by_user_id: int
    archive_reason: Optional[str]
    timestamp: datetime


@dataclass(frozen=True)
class DocumentVersionArchivedEvent:
    """
    Event: Dokument-Version wurde archiviert (neue Version hochgeladen).
    
    NEU Phase 2 & 5: Wird publiziert wenn neue Version hochgeladen wird und alte Version archiviert wird.
    
    Subscribers:
    - ragintegration.DocumentVersionArchivedEventHandler → Entferne alte Version aus RAG Index
    
    Attributes:
        old_version_id: ID der alten (archivierten) Version
        new_version_id: ID der neuen Version
        document_series_id: ID der Dokument-Serie
        archived_by_user_id: User ID des Uploaders (der neuen Version)
        timestamp: Event-Zeitstempel
    """
    old_version_id: int
    new_version_id: int
    document_series_id: int
    archived_by_user_id: int
    timestamp: datetime


@dataclass(frozen=True)
class DocumentHardDeletedEvent:
    """
    Event: Dokument wurde endgültig gelöscht (Hard Delete).
    
    NEU Archiv-System: Wird publiziert wenn Dokument hard-deleted wird.
    
    Wird von:
    - documentupload.HardDeleteDocumentUseCase
    
    Wird verarbeitet von:
    - Optional: Audit-System (für Compliance-Logging)
    - Optional: Backup-System (für Retention-Management)
    
    Attributes:
        document_id: ID des gelöschten Dokuments
        deleted_by_user_id: User ID der Löschung durchführt
        deletion_reason: Grund für Löschung (aus Soft Delete)
        files_deleted: Liste der gelöschten Dateien
        timestamp: Event-Zeitstempel
    """
    document_id: int
    deleted_by_user_id: int
    deletion_reason: Optional[str]
    files_deleted: List[str]
    timestamp: datetime

