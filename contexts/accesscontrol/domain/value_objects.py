"""
AccessControl Domain Value Objects

Wert-Objekte für RBAC: PermissionCode, RoleName, UserId
"""

from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class UserId:
    """User ID Value Object"""
    value: int
    
    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("User ID must be positive")
    
    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class PermissionCode:
    """Permission Code Value Object"""
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Permission code cannot be empty")
        if len(self.value) > 100:
            raise ValueError("Permission code too long")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class RoleName:
    """Role Name Value Object"""
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Role name cannot be empty")
        if len(self.value) > 50:
            raise ValueError("Role name too long")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Email:
    """Email Value Object"""
    value: str
    
    def __post_init__(self):
        if not self.value or "@" not in self.value:
            raise ValueError("Invalid email format")
        if len(self.value) > 100:
            raise ValueError("Email too long")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ApprovalLevel:
    """Approval Level Value Object"""
    value: int
    
    def __post_init__(self):
        if not (1 <= self.value <= 5):
            raise ValueError("Approval level must be between 1 and 5")
    
    def __str__(self) -> str:
        return str(self.value)
    
    def is_qm_level(self) -> bool:
        """Prüft ob Level QM-Berechtigung hat"""
        return self.value >= 4
    
    def is_admin_level(self) -> bool:
        """Prüft ob Level Admin-Berechtigung hat"""
        return self.value >= 5

