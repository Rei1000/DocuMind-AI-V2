"""
Domain Entities: DocumentTypes Context

Enthält die Kerngeschäftslogik für Dokumenttypen.
KEINE Abhängigkeiten zu Infrastructure oder External Libraries!
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class DocumentType:
    """
    Aggregate Root: Dokumenttyp
    
    Definiert eine Kategorie von QMS-Dokumenten (z.B. SOP, Flussdiagramm, Formular).
    Jeder Dokumenttyp hat spezifische Validierungsregeln und kann mit
    Prompt Templates verknüpft werden.
    
    Attributes:
        id: Eindeutige ID
        name: Anzeigename (z.B. "Flussdiagramm")
        code: Technischer Code (z.B. "FLOWCHART")
        description: Detaillierte Beschreibung
        allowed_file_types: Liste erlaubter Dateitypen [".pdf", ".png", ".jpg"]
        max_file_size_mb: Maximale Dateigröße in MB
        requires_ocr: Benötigt OCR-Verarbeitung
        requires_vision: Benötigt Vision AI
        default_prompt_template_id: Standard-Template ID
        created_by: User ID des Erstellers
        is_active: Ist dieser Typ aktiv?
        sort_order: Sortierung in UI
        created_at: Erstellungszeitpunkt
        updated_at: Letzte Änderung
    
    Business Rules:
        - Code muss eindeutig sein (UPPERCASE, NO SPACES)
        - Mindestens ein Dateityp muss erlaubt sein
        - max_file_size_mb muss > 0 sein
    """
    
    id: Optional[int] = None
    name: str = ""
    code: str = ""
    description: str = ""
    allowed_file_types: List[str] = field(default_factory=lambda: [".pdf"])
    max_file_size_mb: int = 10
    requires_ocr: bool = False
    requires_vision: bool = False
    default_prompt_template_id: Optional[int] = None
    created_by: Optional[int] = None
    is_active: bool = True
    sort_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate entity after creation"""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def validate_file_type(self, file_extension: str) -> bool:
        """
        Business Logic: Prüfe ob Dateityp erlaubt ist
        
        Args:
            file_extension: Dateiendung (z.B. ".pdf")
            
        Returns:
            True wenn erlaubt, sonst False
        """
        return file_extension.lower() in [ft.lower() for ft in self.allowed_file_types]
    
    def validate_file_size(self, file_size_mb: float) -> bool:
        """
        Business Logic: Prüfe ob Dateigröße im Limit
        
        Args:
            file_size_mb: Dateigröße in MB
            
        Returns:
            True wenn im Limit, sonst False
        """
        return file_size_mb <= self.max_file_size_mb
    
    def is_valid(self) -> bool:
        """
        Business Logic: Validiere Entity
        
        Returns:
            True wenn valide, sonst False
        """
        return (
            len(self.name.strip()) > 0 and
            len(self.code.strip()) > 0 and
            len(self.allowed_file_types) > 0 and
            self.max_file_size_mb > 0
        )
    
    def mark_as_updated(self):
        """Business Logic: Markiere als aktualisiert"""
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Business Logic: Deaktiviere Dokumenttyp"""
        self.is_active = False
        self.mark_as_updated()
    
    def activate(self):
        """Business Logic: Aktiviere Dokumenttyp"""
        self.is_active = True
        self.mark_as_updated()

