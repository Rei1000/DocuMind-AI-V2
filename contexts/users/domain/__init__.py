"""
Users Domain Layer

Enthält Entities, Value Objects, Events und Repository-Interfaces.
"""

from .entities import User, Role, Membership
from .value_objects import (
    UserId,
    EmailAddress,
    LenientEmailAddress,
    FullName,
    LenientFullName,
    EmployeeId,
    OrganizationalUnit,
    ApprovalLevel,
    RoleName,
    PermissionCode,
    MembershipRole,
    InterestGroupId,
)
from .events import (
    DomainEvent,
    UserCreated,
    UserUpdated,
    UserDeactivated,
    UserReactivated,
    RoleAssigned,
    RoleRevoked,
    MembershipAdded,
    MembershipRemoved,
    PermissionGranted,
    PermissionRevoked,
)
from .repositories import (
    UserRepository,
    RoleRepository,
    MembershipRepository,
    AssignmentRepository,
    PermissionRepository,
)

__all__ = [
    "User",
    "Role",
    "Membership",
    "UserId",
    "EmailAddress",
    "LenientEmailAddress",
    "FullName",
    "LenientFullName",
    "EmployeeId",
    "OrganizationalUnit",
    "ApprovalLevel",
    "RoleName",
    "PermissionCode",
    "MembershipRole",
    "InterestGroupId",
    "DomainEvent",
    "UserCreated",
    "UserUpdated",
    "UserDeactivated",
    "UserReactivated",
    "RoleAssigned",
    "RoleRevoked",
    "MembershipAdded",
    "MembershipRemoved",
    "PermissionGranted",
    "PermissionRevoked",
    "UserRepository",
    "RoleRepository",
    "MembershipRepository",
    "AssignmentRepository",
    "PermissionRepository",
]




