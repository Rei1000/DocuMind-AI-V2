"""
Command-Objekte für Users Application Layer.

Diese einfachen Dataklassen tragen Eingabedaten für Use Cases.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CreateUserCommand:
    email: str
    full_name: str
    employee_id: Optional[str] = None
    organizational_unit: Optional[str] = None
    approval_level: int = 1
    is_department_head: bool = False


@dataclass(frozen=True)
class UpdateUserCommand:
    user_id: int
    full_name: Optional[str] = None
    organizational_unit: Optional[str] = None
    approval_level: Optional[int] = None
    is_department_head: Optional[bool] = None


@dataclass(frozen=True)
class DeactivateUserCommand:
    user_id: int
    reason: Optional[str] = None


@dataclass(frozen=True)
class ReactivateUserCommand:
    user_id: int


@dataclass(frozen=True)
class AssignRoleCommand:
    user_id: int
    role_name: str
    assigned_by: Optional[int] = None


@dataclass(frozen=True)
class RevokeRoleCommand:
    user_id: int
    role_name: str
    revoked_by: Optional[int] = None


@dataclass(frozen=True)
class AddMembershipCommand:
    user_id: int
    interest_group_id: int
    role_in_group: Optional[str] = None
    approval_level: int = 1
    assigned_by: Optional[int] = None


@dataclass(frozen=True)
class RemoveMembershipCommand:
    user_id: int
    interest_group_id: int


@dataclass(frozen=True)
class GrantPermissionCommand:
    user_id: int
    permission_code: str


@dataclass(frozen=True)
class RevokePermissionCommand:
    user_id: int
    permission_code: str




