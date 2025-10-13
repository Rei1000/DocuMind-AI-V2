"""
Value Objects für Document Upload Context

Value Objects sind unveränderliche Objekte, die durch ihre Attribute definiert sind.
Sie haben keine Identität und werden nur durch ihre Werte verglichen.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FileType(str, Enum):
    """
    Unterstützte Dateitypen für Upload.
    
    Attributes:
        PDF: Portable Document Format
        DOCX: Microsoft Word Document
        PNG: Portable Network Graphics
        JPG: JPEG Image
    """
    PDF = "pdf"
    DOCX = "docx"
    PNG = "png"
    JPG = "jpg"
    
    @classmethod
    def from_filename(cls, filename: str) -> "FileType":
        """
        Extrahiere FileType aus Dateiname.
        
        Args:
            filename: Dateiname mit Extension
            
        Returns:
            FileType Enum
            
        Raises:
            ValueError: Wenn Extension nicht unterstützt
        """
        extension = filename.lower().split('.')[-1]
        
        if extension == 'jpeg':
            extension = 'jpg'
        
        try:
            return cls(extension)
        except ValueError:
            raise ValueError(f"Unsupported file type: {extension}")
    
    @property
    def mime_type(self) -> str:
        """Returniere MIME-Type für HTTP-Header."""
        mime_types = {
            FileType.PDF: "application/pdf",
            FileType.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            FileType.PNG: "image/png",
            FileType.JPG: "image/jpeg"
        }
        return mime_types[self]


class ProcessingMethod(str, Enum):
    """
    Verarbeitungsmethode für Dokumente.
    
    Attributes:
        OCR: Text-Extraktion via OCR (Tesseract)
        VISION: Multimodal AI (GPT-4o Vision, Gemini)
    """
    OCR = "ocr"
    VISION = "vision"


class ProcessingStatus(str, Enum):
    """
    Status der Dokumenten-Verarbeitung.
    
    Attributes:
        PENDING: Wartet auf Verarbeitung
        PROCESSING: Wird gerade verarbeitet
        COMPLETED: Erfolgreich verarbeitet
        FAILED: Verarbeitung fehlgeschlagen
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class DocumentMetadata:
    """
    Metadaten eines hochgeladenen Dokuments.
    
    Value Object für Dokumenten-Metadaten (unveränderlich).
    
    Attributes:
        filename: Interner Dateiname
        original_filename: Original Dateiname vom User
        qm_chapter: QM-Kapitel (z.B. "5.2")
        version: Versionsnummer (z.B. "v1.0.0")
    """
    filename: str
    original_filename: str
    qm_chapter: Optional[str]
    version: str
    
    def __post_init__(self):
        """Validiere Metadaten nach Initialisierung."""
        if not self.filename:
            raise ValueError("Filename cannot be empty")
        if not self.original_filename:
            raise ValueError("Original filename cannot be empty")
        if not self.version:
            raise ValueError("Version cannot be empty")
        
        # Validiere Version-Format (vX.Y.Z)
        if not self.version.startswith('v'):
            raise ValueError("Version must start with 'v' (e.g. v1.0.0)")


@dataclass(frozen=True)
class PageDimensions:
    """
    Dimensionen einer Dokumenten-Seite.
    
    Value Object für Seiten-Dimensionen (unveränderlich).
    
    Attributes:
        width: Breite in Pixel
        height: Höhe in Pixel
    """
    width: int
    height: int
    
    def __post_init__(self):
        """Validiere Dimensionen nach Initialisierung."""
        if self.width <= 0:
            raise ValueError("Width must be positive")
        if self.height <= 0:
            raise ValueError("Height must be positive")
    
    @property
    def aspect_ratio(self) -> float:
        """Berechne Seitenverhältnis."""
        return self.width / self.height
    
    def is_landscape(self) -> bool:
        """Prüfe ob Querformat."""
        return self.width > self.height
    
    def is_portrait(self) -> bool:
        """Prüfe ob Hochformat."""
        return self.height > self.width


@dataclass(frozen=True)
class FilePath:
    """
    Dateipfad mit Validierung.
    
    Value Object für Dateipfade (unveränderlich).
    
    Attributes:
        path: Relativer oder absoluter Pfad
    """
    path: str
    
    def __post_init__(self):
        """Validiere Pfad nach Initialisierung."""
        if not self.path:
            raise ValueError("Path cannot be empty")
        
        # Verhindere Path Traversal Attacks
        if '..' in self.path:
            raise ValueError("Path traversal not allowed")
    
    def __str__(self) -> str:
        """String-Repräsentation."""
        return self.path

