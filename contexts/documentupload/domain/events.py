"""
Domain Events für Document Upload Context

Domain Events repräsentieren Ereignisse, die im System passiert sind.
Sie werden von anderen Contexts konsumiert (Event-Driven Architecture).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List


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

