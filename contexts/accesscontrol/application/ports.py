"""
AccessControl Application Ports

Interface-Definitionen für RBAC-Use-Cases
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Protocol, runtime_checkable
from ..domain.entities import User, Role, Permission, Assignment, Membership
from ..domain.value_objects import UserId, PermissionCode, RoleName


@runtime_checkable
class UserRepository(Protocol):
    """User Repository Port"""
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """User by ID abrufen"""
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        """User by Email finden"""
        pass
    
    @abstractmethod
    def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Alle User auflisten"""
        pass
    
    @abstractmethod
    def create(self, user: User) -> User:
        """User erstellen"""
        pass
    
    @abstractmethod
    def update(self, user: User) -> User:
        """User aktualisieren"""
        pass
    
    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """User löschen (Soft Delete)"""
        pass


@runtime_checkable
class RoleRepository(Protocol):
    """Role Repository Port"""
    
    @abstractmethod
    def get_by_id(self, role_id: int) -> Optional[Role]:
        """Role by ID abrufen"""
        pass
    
    @abstractmethod
    def get_by_name(self, role_name: str) -> Optional[Role]:
        """Role by Name abrufen"""
        pass
    
    @abstractmethod
    def list_all(self) -> List[Role]:
        """Alle Rollen auflisten"""
        pass
    
    @abstractmethod
    def list_for_user(self, user_id: int) -> List[Role]:
        """Rollen für User auflisten"""
        pass
    
    @abstractmethod
    def create(self, role: Role) -> Role:
        """Role erstellen"""
        pass
    
    @abstractmethod
    def update(self, role: Role) -> Role:
        """Role aktualisieren"""
        pass


@runtime_checkable
class PermissionRepository(Protocol):
    """Permission Repository Port"""
    
    @abstractmethod
    def get_by_code(self, permission_code: str) -> Optional[Permission]:
        """Permission by Code abrufen"""
        pass
    
    @abstractmethod
    def list_all(self) -> List[Permission]:
        """Alle Permissions auflisten"""
        pass
    
    @abstractmethod
    def list_for_role(self, role_name: str) -> List[Permission]:
        """Permissions für Role auflisten"""
        pass
    
    @abstractmethod
    def list_for_user(self, user_id: int) -> List[Permission]:
        """Permissions für User auflisten (aggregiert)"""
        pass
    
    @abstractmethod
    def create(self, permission: Permission) -> Permission:
        """Permission erstellen"""
        pass


@runtime_checkable
class AssignmentRepository(Protocol):
    """Assignment Repository Port"""
    
    @abstractmethod
    def assign_role(self, user_id: int, role_name: str, assigned_by: Optional[int] = None) -> Assignment:
        """Role zuweisen"""
        pass
    
    @abstractmethod
    def revoke_role(self, user_id: int, role_name: str, revoked_by: Optional[int] = None) -> bool:
        """Role entziehen"""
        pass
    
    @abstractmethod
    def list_for_user(self, user_id: int) -> List[Assignment]:
        """Assignments für User auflisten"""
        pass
    
    @abstractmethod
    def list_for_role(self, role_name: str) -> List[Assignment]:
        """Assignments für Role auflisten"""
        pass
    
    @abstractmethod
    def is_assigned(self, user_id: int, role_name: str) -> bool:
        """Prüfen ob Role zugewiesen ist"""
        pass


@runtime_checkable
class MembershipRepository(Protocol):
    """Membership Repository Port"""
    
    @abstractmethod
    def list_groups_for_user(self, user_id: int) -> List[Membership]:
        """Groups für User auflisten"""
        pass
    
    @abstractmethod
    def add_membership(self, membership: Membership) -> Membership:
        """Membership hinzufügen"""
        pass
    
    @abstractmethod
    def remove_membership(self, user_id: int, group_id: int) -> bool:
        """Membership entfernen"""
        pass
    
    @abstractmethod
    def update_membership(self, membership: Membership) -> Membership:
        """Membership aktualisieren"""
        pass
    
    @abstractmethod
    def is_member(self, user_id: int, group_id: int) -> bool:
        """Prüfen ob User Mitglied ist"""
        pass


@runtime_checkable
class PolicyPort(Protocol):
    """Policy Decision Port"""
    
    @abstractmethod
    def check_access(self, user_id: int, permission_code: str, resource: Optional[str] = None) -> bool:
        """Zugriff prüfen"""
        pass
    
    @abstractmethod
    def can_approve(self, user_id: int, required_level: int) -> bool:
        """Freigabe-Berechtigung prüfen"""
        pass
    
    @abstractmethod
    def can_manage_users(self, user_id: int) -> bool:
        """User-Management-Berechtigung prüfen"""
        pass
    
    @abstractmethod
    def get_user_permissions(self, user_id: int) -> List[str]:
        """User-Permissions abrufen (aggregiert)"""
        pass


@runtime_checkable
class AuditPort(Protocol):
    """Audit Port (optional)"""
    
    @abstractmethod
    def record(self, event_type: str, user_id: int, details: dict) -> None:
        """Event aufzeichnen"""
        pass
    
    @abstractmethod
    def record_access_check(self, user_id: int, permission_code: str, granted: bool) -> None:
        """Access-Check aufzeichnen"""
        pass
    
    @abstractmethod
    def record_role_assignment(self, user_id: int, role_name: str, assigned_by: int) -> None:
        """Role-Assignment aufzeichnen"""
        pass


# Legacy Integration Ports

@runtime_checkable
class LegacyUserGateway(Protocol):
    """Legacy User Gateway Port"""
    
    @abstractmethod
    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """User aus Legacy-System abrufen"""
        pass
    
    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[dict]:
        """User by Email aus Legacy-System abrufen"""
        pass
    
    @abstractmethod
    def list_users(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """User-Liste aus Legacy-System abrufen"""
        pass


@runtime_checkable
class LegacyMembershipGateway(Protocol):
    """Legacy Membership Gateway Port"""
    
    @abstractmethod
    def get_memberships_for_user(self, user_id: int) -> List[dict]:
        """Memberships aus Legacy-System abrufen"""
        pass
    
    @abstractmethod
    def get_memberships_for_group(self, group_id: int) -> List[dict]:
        """Memberships für Group aus Legacy-System abrufen"""
        pass
    
    @abstractmethod
    def create_membership(self, membership_data: dict) -> dict:
        """Membership in Legacy-System erstellen"""
        pass


@runtime_checkable
class LegacyPermissionGateway(Protocol):
    """Legacy Permission Gateway Port"""
    
    @abstractmethod
    def get_user_permissions(self, user_id: int) -> List[str]:
        """User-Permissions aus Legacy-System abrufen"""
        pass
    
    @abstractmethod
    def get_group_permissions(self, group_id: int) -> List[str]:
        """Group-Permissions aus Legacy-System abrufen"""
        pass
    
    @abstractmethod
    def check_user_access(self, user_id: int, permission_code: str) -> bool:
        """Access-Check im Legacy-System"""
        pass

