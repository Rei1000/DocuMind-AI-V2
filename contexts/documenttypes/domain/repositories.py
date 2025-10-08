"""
Domain Repository Interfaces (Ports): DocumentTypes Context

Definiert abstrakte Interfaces für Persistence.
Infrastructure Layer implementiert diese (Adapters).
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import DocumentType


class IDocumentTypeRepository(ABC):
    """
    Port: Repository Interface für DocumentType
    
    Definiert Contract für Persistence-Operationen.
    KEINE Implementierung hier - nur Interface!
    """
    
    @abstractmethod
    def get_by_id(self, document_type_id: int) -> Optional[DocumentType]:
        """
        Hole DocumentType by ID
        
        Args:
            document_type_id: ID des Dokumenttyps
            
        Returns:
            DocumentType Entity oder None
        """
        pass
    
    @abstractmethod
    def get_by_code(self, code: str) -> Optional[DocumentType]:
        """
        Hole DocumentType by Code (eindeutig)
        
        Args:
            code: Technischer Code (z.B. "FLOWCHART")
            
        Returns:
            DocumentType Entity oder None
        """
        pass
    
    @abstractmethod
    def get_all(self, active_only: bool = True) -> List[DocumentType]:
        """
        Hole alle DocumentTypes
        
        Args:
            active_only: Nur aktive Typen?
            
        Returns:
            Liste von DocumentType Entities
        """
        pass
    
    @abstractmethod
    def save(self, document_type: DocumentType) -> DocumentType:
        """
        Speichere DocumentType (Create oder Update)
        
        Args:
            document_type: DocumentType Entity
            
        Returns:
            Gespeicherte DocumentType Entity mit ID
        """
        pass
    
    @abstractmethod
    def delete(self, document_type_id: int) -> bool:
        """
        Lösche DocumentType
        
        Args:
            document_type_id: ID des Dokumenttyps
            
        Returns:
            True wenn gelöscht, False wenn nicht gefunden
        """
        pass
    
    @abstractmethod
    def exists_by_code(self, code: str, exclude_id: Optional[int] = None) -> bool:
        """
        Prüfe ob Code bereits existiert
        
        Args:
            code: Technischer Code
            exclude_id: Optional: ID die ausgeschlossen werden soll (für Updates)
            
        Returns:
            True wenn Code existiert, sonst False
        """
        pass

