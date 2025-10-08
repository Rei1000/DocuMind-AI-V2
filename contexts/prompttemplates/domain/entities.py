"""
Domain Entities: PromptTemplates Context

Enthält die Kerngeschäftslogik für Prompt Templates.
KEINE Abhängigkeiten zu Infrastructure oder External Libraries!
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class PromptStatus(Enum):
    """Status eines Prompt Templates"""
    DRAFT = "draft"           # Entwurf, noch nicht freigegeben
    ACTIVE = "active"         # Aktiv und verwendbar
    ARCHIVED = "archived"     # Archiviert, nicht mehr aktiv
    DEPRECATED = "deprecated" # Veraltet, aber noch sichtbar


@dataclass
class PromptTemplate:
    """
    Aggregate Root: Prompt Template
    
    Wiederverwendbares AI-Prompt Template für Dokumentenanalyse.
    Kann aus erfolgreichen AI Playground Tests gespeichert werden.
    
    Attributes:
        id: Eindeutige ID
        name: Anzeigename (z.B. "Flussdiagramm Analyse v2")
        description: Beschreibung des Template-Zwecks
        prompt_text: Der eigentliche Prompt-Text
        system_instructions: Optional: System-Level Instructions
        document_type_id: Verknüpfung mit Dokumenttyp (optional)
        ai_model: Empfohlenes AI-Modell (z.B. "gpt-4o-mini")
        
        # AI Configuration
        temperature: Temperature Setting (0-2)
        max_tokens: Max Output Tokens
        top_p: Nucleus Sampling Parameter
        detail_level: Vision Detail Level ("high" / "low")
        
        # Metadata
        status: Draft, Active, Archived, Deprecated
        version: Versionsnummer (z.B. "1.0", "2.1")
        created_by: User ID des Erstellers
        tested_successfully: Wurde erfolgreich getestet?
        success_count: Wie oft erfolgreich verwendet?
        last_used_at: Wann zuletzt verwendet?
        tags: Kategorisierung (z.B. ["qms", "flowchart"])
        
        created_at: Erstellungszeitpunkt
        updated_at: Letzte Änderung
    
    Business Rules:
        - Name muss eindeutig sein (pro Dokumenttyp)
        - Prompt-Text darf nicht leer sein
        - Nur ACTIVE Templates werden bei Document Upload angeboten
        - Version sollte Semantic Versioning folgen (empfohlen)
    """
    
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    prompt_text: str = ""
    system_instructions: Optional[str] = None
    
    # Document Type Linking
    document_type_id: Optional[int] = None
    
    # AI Configuration
    ai_model: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_tokens: int = 4000
    top_p: float = 1.0
    detail_level: str = "high"  # for vision models
    
    # Metadata
    status: PromptStatus = PromptStatus.DRAFT
    version: str = "1.0"
    created_by: Optional[int] = None
    tested_successfully: bool = False
    success_count: int = 0
    last_used_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    
    # Example Data (for testing/documentation)
    example_input: Optional[str] = None
    example_output: Optional[str] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate entity after creation"""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        
        # Convert string status to enum if needed
        if isinstance(self.status, str):
            self.status = PromptStatus(self.status)
    
    def is_valid(self) -> bool:
        """
        Business Logic: Validiere Template
        
        Returns:
            True wenn valide, sonst False
        """
        return (
            len(self.name.strip()) > 0 and
            len(self.prompt_text.strip()) > 0 and
            self.temperature >= 0 and
            self.temperature <= 2 and
            self.max_tokens > 0
        )
    
    def mark_as_updated(self):
        """Business Logic: Markiere als aktualisiert"""
        self.updated_at = datetime.utcnow()
    
    def activate(self):
        """Business Logic: Aktiviere Template"""
        if not self.is_valid():
            raise ValueError("Template muss valid sein bevor es aktiviert wird")
        self.status = PromptStatus.ACTIVE
        self.mark_as_updated()
    
    def archive(self):
        """Business Logic: Archiviere Template"""
        self.status = PromptStatus.ARCHIVED
        self.mark_as_updated()
    
    def deprecate(self):
        """Business Logic: Markiere als veraltet"""
        self.status = PromptStatus.DEPRECATED
        self.mark_as_updated()
    
    def mark_as_used(self, success: bool = True):
        """
        Business Logic: Markiere als verwendet
        
        Args:
            success: War die Verwendung erfolgreich?
        """
        self.last_used_at = datetime.utcnow()
        if success:
            self.success_count += 1
            if not self.tested_successfully:
                self.tested_successfully = True
        self.mark_as_updated()
    
    def increment_version(self, version_type: str = "minor"):
        """
        Business Logic: Version hochzählen
        
        Args:
            version_type: "major", "minor", oder "patch"
        """
        try:
            parts = self.version.split(".")
            major = int(parts[0]) if len(parts) > 0 else 1
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            
            if version_type == "major":
                major += 1
                minor = 0
                patch = 0
            elif version_type == "minor":
                minor += 1
                patch = 0
            else:  # patch
                patch += 1
            
            self.version = f"{major}.{minor}.{patch}"
        except (ValueError, IndexError):
            # Falls Version nicht im erwarteten Format
            self.version = "1.0.0"
        
        self.mark_as_updated()
    
    def is_usable(self) -> bool:
        """
        Business Logic: Kann Template verwendet werden?
        
        Returns:
            True wenn ACTIVE und valid
        """
        return self.status == PromptStatus.ACTIVE and self.is_valid()
    
    def add_tag(self, tag: str):
        """Business Logic: Tag hinzufügen"""
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.mark_as_updated()
    
    def remove_tag(self, tag: str):
        """Business Logic: Tag entfernen"""
        tag = tag.strip().lower()
        if tag in self.tags:
            self.tags.remove(tag)
            self.mark_as_updated()

