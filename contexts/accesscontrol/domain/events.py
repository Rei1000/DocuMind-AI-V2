"""
AccessControl Domain Events

Domain Events für RBAC: RoleAssigned, RoleRevoked, PermissionGranted
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RoleAssigned:
    """Event: Rolle wurde zugewiesen"""
    user_id: int
    role_name: str
    assigned_by: Optional[int] = None
    assigned_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        if self.assigned_at is None:
            self.assigned_at = datetime.utcnow()


@dataclass
class RoleRevoked:
    """Event: Rolle wurde entzogen"""
    user_id: int
    role_name: str
    revoked_by: Optional[int] = None
    revoked_at: Optional[datetime] = None
    reason: Optional[str] = None
    
    def __post_init__(self):
        if self.revoked_at is None:
            self.revoked_at = datetime.utcnow()


@dataclass
class PermissionGranted:
    """Event: Berechtigung wurde erteilt"""
    user_id: int
    permission_code: str
    granted_by: Optional[int] = None
    granted_at: Optional[datetime] = None
    source: str = "individual"  # "individual", "role", "group"
    
    def __post_init__(self):
        if self.granted_at is None:
            self.granted_at = datetime.utcnow()


@dataclass
class PermissionRevoked:
    """Event: Berechtigung wurde entzogen"""
    user_id: int
    permission_code: str
    revoked_by: Optional[int] = None
    revoked_at: Optional[datetime] = None
    reason: Optional[str] = None
    
    def __post_init__(self):
        if self.revoked_at is None:
            self.revoked_at = datetime.utcnow()


@dataclass
class UserCreated:
    """Event: User wurde erstellt"""
    user_id: int
    email: str
    full_name: str
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class MembershipCreated:
    """Event: Group-Membership wurde erstellt"""
    user_id: int
    interest_group_id: int
    role_in_group: Optional[str] = None
    approval_level: int = 1
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class AccessChecked:
    """Event: Zugriff wurde geprüft"""
    user_id: int
    permission_code: str
    resource: Optional[str] = None
    granted: bool = False
    checked_at: Optional[datetime] = None
    reason: Optional[str] = None
    
    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.utcnow()

