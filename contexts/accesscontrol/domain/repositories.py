"""
Domain Repositories für Access Control
"""

from abc import ABC, abstractmethod
from typing import Optional
from .entities import User


class UserRepository(ABC):
    """Repository Interface für User-Entitäten"""
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        """Findet einen User anhand der E-Mail-Adresse"""
        pass
    
    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Findet einen User anhand der ID"""
        pass
    
    @abstractmethod
    def save(self, user: User) -> User:
        """Speichert einen User"""
        pass
