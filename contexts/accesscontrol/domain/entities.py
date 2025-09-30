"""
AccessControl Domain Entities

Kern-Entitäten für RBAC: User, Role, Permission, Assignment
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class User:
    """User Entity - Kern-Benutzer-Informationen"""
    id: int
    email: str
    full_name: str
    hashed_password: str
    employee_id: Optional[str] = None
    organizational_unit: Optional[str] = None
    is_department_head: bool = False
    approval_level: int = 1
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    def has_approval_level(self, required_level: int) -> bool:
        """Prüft ob User das erforderliche Approval Level hat"""
        return self.approval_level >= required_level
    
    def is_qm_manager(self) -> bool:
        """Prüft ob User QM-Manager ist (Level 4+)"""
        return self.approval_level >= 4
    
    def is_system_admin(self) -> bool:
        """Prüft ob User System-Admin ist (Level 5)"""
        return self.approval_level >= 5


@dataclass
class Role:
    """Role Entity - Rollen-Definition"""
    name: str
    description: Optional[str] = None
    permissions: List[str] = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []
    
    def has_permission(self, permission_code: str) -> bool:
        """Prüft ob Rolle eine bestimmte Permission hat"""
        return permission_code in self.permissions


@dataclass
class Permission:
    """Permission Entity - Berechtigungs-Definition"""
    code: str
    name: str
    description: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    
    def __str__(self) -> str:
        return self.code


@dataclass
class Assignment:
    """Assignment Entity - User-Role-Zuordnung"""
    user_id: int
    role_name: str
    assigned_at: datetime
    assigned_by: Optional[int] = None
    is_active: bool = True
    notes: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Prüft ob Assignment gültig ist"""
        return self.is_active and self.user_id > 0 and bool(self.role_name)


@dataclass
class Membership:
    """Membership Entity - User-Group-Zuordnung"""
    user_id: int
    interest_group_id: int
    role_in_group: Optional[str] = None
    approval_level: int = 1
    is_department_head: bool = False
    is_active: bool = True
    joined_at: Optional[datetime] = None
    assigned_by: Optional[int] = None
    notes: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Prüft ob Membership gültig ist"""
        return self.is_active and self.user_id > 0 and self.interest_group_id > 0


@dataclass
class ApprovalRule:
    """ApprovalRule Entity - Freigabe-Regel (Placeholder)"""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    required_approval_level: int = 1
    required_groups: List[str] = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.required_groups is None:
            self.required_groups = []
    
    def requires_group(self, group_code: str) -> bool:
        """Prüft ob Regel eine bestimmte Gruppe erfordert"""
        return group_code in self.required_groups

