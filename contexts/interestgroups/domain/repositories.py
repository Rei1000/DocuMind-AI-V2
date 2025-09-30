"""
Repository Interface für Interest Groups Domain
Definiert die Schnittstelle für Datenzugriff (ohne Implementierungsdetails)
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import InterestGroup


class InterestGroupRepository(ABC):
    """
    Repository Interface für Interest Group Aggregat
    Definiert Methoden für Persistierung ohne Implementierungsdetails
    """
    
    @abstractmethod
    def find_by_id(self, group_id: int) -> Optional[InterestGroup]:
        """
        Findet eine Interest Group anhand ihrer ID
        
        Args:
            group_id: Die ID der gesuchten Interest Group
            
        Returns:
            InterestGroup oder None wenn nicht gefunden
        """
        pass
    
    @abstractmethod
    def find_by_code(self, code: str) -> Optional[InterestGroup]:
        """
        Findet eine Interest Group anhand ihres Codes
        
        Args:
            code: Der eindeutige Code der Interest Group
            
        Returns:
            InterestGroup oder None wenn nicht gefunden
        """
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[InterestGroup]:
        """
        Findet eine Interest Group anhand ihres Namens
        
        Args:
            name: Der Name der Interest Group
            
        Returns:
            InterestGroup oder None wenn nicht gefunden
        """
        pass
    
    @abstractmethod
    def find_all_active(self) -> List[InterestGroup]:
        """
        Gibt alle aktiven Interest Groups zurück
        
        Returns:
            Liste aller aktiven Interest Groups
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[InterestGroup]:
        """
        Gibt alle Interest Groups zurück (aktive und inaktive)
        
        Returns:
            Liste aller Interest Groups
        """
        pass
    
    @abstractmethod
    def save(self, interest_group: InterestGroup) -> InterestGroup:
        """
        Speichert eine Interest Group (create oder update)
        
        Args:
            interest_group: Die zu speichernde Interest Group
            
        Returns:
            Die gespeicherte Interest Group mit ID
        """
        pass
    
    @abstractmethod
    def exists_with_code(self, code: str, exclude_id: Optional[int] = None) -> bool:
        """
        Prüft ob eine Interest Group mit dem Code bereits existiert
        
        Args:
            code: Der zu prüfende Code
            exclude_id: Optional ID die bei der Prüfung ausgeschlossen werden soll
            
        Returns:
            True wenn Code bereits existiert
        """
        pass
    
    @abstractmethod
    def exists_with_name(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """
        Prüft ob eine Interest Group mit dem Namen bereits existiert
        
        Args:
            name: Der zu prüfende Name
            exclude_id: Optional ID die bei der Prüfung ausgeschlossen werden soll
            
        Returns:
            True wenn Name bereits existiert
        """
        pass
    
    @abstractmethod
    def count_active(self) -> int:
        """
        Zählt alle aktiven Interest Groups
        
        Returns:
            Anzahl der aktiven Interest Groups
        """
        pass
    
    @abstractmethod
    def find_by_permission(self, permission: str) -> List[InterestGroup]:
        """
        Findet alle Interest Groups die eine bestimmte Permission haben
        
        Args:
            permission: Die gesuchte Permission
            
        Returns:
            Liste von Interest Groups mit dieser Permission
        """
        pass
