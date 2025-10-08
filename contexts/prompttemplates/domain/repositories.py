"""
Domain Repository Interfaces (Ports): PromptTemplates Context

Definiert abstrakte Interfaces für Persistence.
Infrastructure Layer implementiert diese (Adapters).
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import PromptTemplate, PromptStatus


class IPromptTemplateRepository(ABC):
    """
    Port: Repository Interface für PromptTemplate
    
    Definiert Contract für Persistence-Operationen.
    KEINE Implementierung hier - nur Interface!
    """
    
    @abstractmethod
    def get_by_id(self, template_id: int) -> Optional[PromptTemplate]:
        """
        Hole PromptTemplate by ID
        
        Args:
            template_id: ID des Templates
            
        Returns:
            PromptTemplate Entity oder None
        """
        pass
    
    @abstractmethod
    def get_by_name(self, name: str) -> Optional[PromptTemplate]:
        """
        Hole PromptTemplate by Name
        
        Args:
            name: Name des Templates
            
        Returns:
            PromptTemplate Entity oder None
        """
        pass
    
    @abstractmethod
    def get_all(self, 
                status: Optional[PromptStatus] = None,
                document_type_id: Optional[int] = None) -> List[PromptTemplate]:
        """
        Hole alle PromptTemplates mit optionalen Filtern
        
        Args:
            status: Optional: Filter nach Status
            document_type_id: Optional: Filter nach Dokumenttyp
            
        Returns:
            Liste von PromptTemplate Entities
        """
        pass
    
    @abstractmethod
    def get_active_for_document_type(self, document_type_id: int) -> List[PromptTemplate]:
        """
        Hole alle aktiven Templates für einen Dokumenttyp
        
        Args:
            document_type_id: ID des Dokumenttyps
            
        Returns:
            Liste von aktiven PromptTemplate Entities
        """
        pass
    
    @abstractmethod
    def save(self, template: PromptTemplate) -> PromptTemplate:
        """
        Speichere PromptTemplate (Create oder Update)
        
        Args:
            template: PromptTemplate Entity
            
        Returns:
            Gespeicherte PromptTemplate Entity mit ID
        """
        pass
    
    @abstractmethod
    def delete(self, template_id: int) -> bool:
        """
        Lösche PromptTemplate (Hard Delete)
        
        Args:
            template_id: ID des Templates
            
        Returns:
            True wenn gelöscht, False wenn nicht gefunden
        """
        pass
    
    @abstractmethod
    def exists_by_name(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """
        Prüfe ob Name bereits existiert
        
        Args:
            name: Name des Templates
            exclude_id: Optional: ID die ausgeschlossen werden soll (für Updates)
            
        Returns:
            True wenn Name existiert, sonst False
        """
        pass
    
    @abstractmethod
    def search_by_tags(self, tags: List[str]) -> List[PromptTemplate]:
        """
        Suche Templates nach Tags
        
        Args:
            tags: Liste von Tags (OR-Verknüpfung)
            
        Returns:
            Liste von PromptTemplate Entities die mindestens einen Tag haben
        """
        pass

