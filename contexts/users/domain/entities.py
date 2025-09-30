"""
Domain Entities für Users Context

Kapselt Kernlogik für Benutzer, Rollen, Permissions und Memberships.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

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
    UserCreated,
    UserUpdated,
    UserDeactivated,
    UserReactivated,
    RoleAssigned,
    RoleRevoked,
    MembershipAdded,
    MembershipRemoved,
)


@dataclass
class Membership:
    """Mitgliedschaft eines Benutzers in einer Interessengruppe"""

    user_id: UserId
    interest_group_id: InterestGroupId
    role_in_group: MembershipRole = field(default_factory=MembershipRole)
    approval_level: ApprovalLevel = field(default_factory=ApprovalLevel)
    assigned_by: Optional[UserId] = None
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    id: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def deactivate(self) -> None:
        self.is_active = False


@dataclass
class Role:
    """Systemweite Rolle mit zugehörigen Permissions"""

    name: RoleName
    description: Optional[str] = None
    permissions: List[PermissionCode] = field(default_factory=list)
    is_active: bool = True

    def add_permission(self, permission: PermissionCode) -> None:
        if permission not in self.permissions:
            self.permissions.append(permission)

    def remove_permission(self, permission: PermissionCode) -> None:
        self.permissions = [p for p in self.permissions if p != permission]


@dataclass
class User:
    """Aggregrat-Root für Benutzer"""

    id: Optional[UserId]
    email: EmailAddress | LenientEmailAddress
    full_name: FullName | LenientFullName
    employee_id: EmployeeId = field(default_factory=EmployeeId)
    organizational_unit: OrganizationalUnit = field(default_factory=OrganizationalUnit)
    approval_level: ApprovalLevel = field(default_factory=ApprovalLevel)
    is_active: bool = True
    is_department_head: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    memberships: List[Membership] = field(default_factory=list)
    roles: List[RoleName] = field(default_factory=list)
    individual_permissions: List[PermissionCode] = field(default_factory=list)

    _events: List[Any] = field(default_factory=list, init=False, repr=False)

    # --- Factory Methods -------------------------------------------------
    @classmethod
    def create(
        cls,
        email: str,
        full_name: str,
        employee_id: Optional[str] = None,
        organizational_unit: Optional[str] = None,
        approval_level: int = 1,
        is_department_head: bool = False,
    ) -> "User":
        user = cls(
            id=None,
            email=EmailAddress(email),
            full_name=FullName(full_name),
            employee_id=EmployeeId(employee_id),
            organizational_unit=OrganizationalUnit(organizational_unit),
            approval_level=ApprovalLevel(approval_level),
            is_active=True,
            is_department_head=is_department_head,
        )
        user._events.append(UserCreated(user_id=0, email=str(user.email)))
        return user

    # --- Domain Behaviour ------------------------------------------------
    def update_details(
        self,
        full_name: Optional[str] = None,
        organizational_unit: Optional[str] = None,
        approval_level: Optional[int] = None,
        is_department_head: Optional[bool] = None,
    ) -> None:
        changes: Dict[str, Any] = {}

        if full_name is not None and str(self.full_name) != full_name:
            self.full_name = FullName(full_name)
            changes["full_name"] = full_name

        if organizational_unit is not None and str(self.organizational_unit) != organizational_unit:
            self.organizational_unit = OrganizationalUnit(organizational_unit)
            changes["organizational_unit"] = organizational_unit

        if approval_level is not None and int(self.approval_level) != approval_level:
            self.approval_level = ApprovalLevel(approval_level)
            changes["approval_level"] = approval_level

        if is_department_head is not None and self.is_department_head != is_department_head:
            self.is_department_head = is_department_head
            changes["is_department_head"] = is_department_head

        if changes:
            self.updated_at = datetime.utcnow()
            self._events.append(UserUpdated(user_id=int(self.id or 0), changes=changes))

    def deactivate(self, reason: Optional[str] = None) -> None:
        if not self.is_active:
            return
        self.is_active = False
        self._events.append(UserDeactivated(user_id=int(self.id or 0), reason=reason))

    def reactivate(self) -> None:
        if self.is_active:
            return
        self.is_active = True
        self._events.append(UserReactivated(user_id=int(self.id or 0)))

    def assign_role(self, role: RoleName) -> None:
        if role not in self.roles:
            self.roles.append(role)
            self._events.append(RoleAssigned(user_id=int(self.id or 0), role_name=str(role)))

    def revoke_role(self, role: RoleName) -> None:
        if role in self.roles:
            self.roles = [r for r in self.roles if r != role]
            self._events.append(RoleRevoked(user_id=int(self.id or 0), role_name=str(role)))

    def add_membership(self, membership: Membership) -> None:
        for existing in self.memberships:
            if existing.interest_group_id == membership.interest_group_id and existing.is_active:
                raise ValueError("Membership already exists for this interest group")
        self.memberships.append(membership)
        self._events.append(
            MembershipAdded(
                user_id=int(self.id or 0),
                interest_group_id=int(membership.interest_group_id),
                membership_id=membership.id,
            )
        )

    def remove_membership(self, interest_group_id: InterestGroupId) -> None:
        target = None
        for m in self.memberships:
            if m.interest_group_id == interest_group_id and m.is_active:
                target = m
                break
        if not target:
            raise ValueError("Active membership not found")
        target.deactivate()
        self._events.append(
            MembershipRemoved(
                user_id=int(self.id or 0),
                interest_group_id=int(interest_group_id),
                membership_id=target.id,
            )
        )

    def grant_permission(self, permission: PermissionCode) -> None:
        if permission not in self.individual_permissions:
            self.individual_permissions.append(permission)

    def revoke_permission(self, permission: PermissionCode) -> None:
        self.individual_permissions = [p for p in self.individual_permissions if p != permission]

    # --- Helpers ---------------------------------------------------------
    def has_permission(self, permission_code: PermissionCode) -> bool:
        return permission_code in self.individual_permissions

    def pull_events(self) -> List[Any]:
        events = self._events.copy()
        self._events.clear()
        return events


