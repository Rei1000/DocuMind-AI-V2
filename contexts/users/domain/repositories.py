"""
Repository Interfaces für Users Context

Definiert Ports für Speicherung/Abfrage ohne konkrete Implementierung.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import User, Role, Membership
from .value_objects import UserId, RoleName, InterestGroupId, PermissionCode


class UserRepository(ABC):
    """Abstraktes Repository für Benutzer"""

    @abstractmethod
    def get_by_id(self, user_id: UserId) -> Optional[User]:
        ...

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        ...

    @abstractmethod
    def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        ...

    @abstractmethod
    def create(self, user: User) -> User:
        ...

    @abstractmethod
    def update(self, user: User) -> User:
        ...


class RoleRepository(ABC):
    """Repository für Rollen"""

    @abstractmethod
    def get_by_name(self, role_name: RoleName) -> Optional[Role]:
        ...

    @abstractmethod
    def list_all(self) -> List[Role]:
        ...

    @abstractmethod
    def list_for_user(self, user_id: UserId) -> List[Role]:
        ...


class MembershipRepository(ABC):
    """Repository für Memberships"""

    @abstractmethod
    def list_for_user(self, user_id: UserId) -> List[Membership]:
        ...

    @abstractmethod
    def add_membership(self, membership: Membership) -> Membership:
        ...

    @abstractmethod
    def remove_membership(self, membership_id: int) -> bool:
        ...

    @abstractmethod
    def is_member(self, user_id: UserId, interest_group_id: InterestGroupId) -> bool:
        ...


class AssignmentRepository(ABC):
    """Repository für Rollen-Zuordnungen (Assignments)"""

    @abstractmethod
    def assign_role(self, user_id: UserId, role_name: RoleName, assigned_by: Optional[UserId] = None) -> None:
        ...

    @abstractmethod
    def revoke_role(self, user_id: UserId, role_name: RoleName, revoked_by: Optional[UserId] = None) -> bool:
        ...

    @abstractmethod
    def list_for_user(self, user_id: UserId) -> List[RoleName]:
        ...


class PermissionRepository(ABC):
    """Repository für Permissions"""

    @abstractmethod
    def list_for_user(self, user_id: UserId) -> List[PermissionCode]:
        ...

    @abstractmethod
    def list_for_role(self, role_name: RoleName) -> List[PermissionCode]:
        ...




