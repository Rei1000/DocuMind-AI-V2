"""
Domain Value Objects: DocumentTypes Context

Immutable Value Objects die fachliche Konzepte kapseln.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class FileTypeVO:
    """
    Value Object: Erlaubter Dateityp
    
    Kapselt die Validierung von Dateitypen.
    """
    extension: str  # z.B. ".pdf"
    mime_type: str  # z.B. "application/pdf"
    display_name: str  # z.B. "PDF Dokument"
    
    def __post_init__(self):
        """Validate on creation"""
        if not self.extension.startswith('.'):
            raise ValueError(f"Extension must start with '.': {self.extension}")


# Vordefinierte Dateitypen für QMS
PDF_TYPE = FileTypeVO(".pdf", "application/pdf", "PDF Dokument")
PNG_TYPE = FileTypeVO(".png", "image/png", "PNG Bild")
JPG_TYPE = FileTypeVO(".jpg", "image/jpeg", "JPEG Bild")
JPEG_TYPE = FileTypeVO(".jpeg", "image/jpeg", "JPEG Bild")
GIF_TYPE = FileTypeVO(".gif", "image/gif", "GIF Bild")
WEBP_TYPE = FileTypeVO(".webp", "image/webp", "WebP Bild")

AVAILABLE_FILE_TYPES: List[FileTypeVO] = [
    PDF_TYPE,
    PNG_TYPE,
    JPG_TYPE,
    JPEG_TYPE,
    GIF_TYPE,
    WEBP_TYPE,
]


@dataclass(frozen=True)
class ValidationRule:
    """
    Value Object: Validierungsregel
    
    Definiert eine Regel die auf Dokumente dieses Typs angewendet wird.
    """
    rule_type: str  # z.B. "file_size", "file_type", "resolution"
    constraint: str  # z.B. "max:10MB", "only:.pdf,.png"
    error_message: str


@dataclass(frozen=True)
class ProcessingRequirement:
    """
    Value Object: Verarbeitungsanforderung
    
    Definiert welche AI-Verarbeitung für diesen Dokumenttyp nötig ist.
    """
    requires_ocr: bool
    requires_vision: bool
    requires_text_extraction: bool = True
    preferred_ai_model: str = "gpt-4o-mini"  # Default Modell

