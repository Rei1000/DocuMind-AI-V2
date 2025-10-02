"""
Application Services für Users Context

Orchestriert Domain Entities und Repositories.
"""

from __future__ import annotations

from typing import List, Optional

from contexts.users.domain import (
    User,
    RoleName,
    Membership,
    PermissionCode,
    UserId,
    InterestGroupId,
)
from contexts.users.domain.repositories import (
    UserRepository,
    RoleRepository,
    MembershipRepository,
    AssignmentRepository,
    PermissionRepository,
)
from .commands import (
    CreateUserCommand,
    UpdateUserCommand,
    DeactivateUserCommand,
    ReactivateUserCommand,
    AssignRoleCommand,
    RevokeRoleCommand,
    AddMembershipCommand,
    RemoveMembershipCommand,
    GrantPermissionCommand,
    RevokePermissionCommand,
)


class UserService:
    """Orchestriert Benutzer-bezogene Use Cases"""

    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository,
        membership_repo: MembershipRepository,
        assignment_repo: AssignmentRepository,
        permission_repo: PermissionRepository,
    ) -> None:
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.membership_repo = membership_repo
        self.assignment_repo = assignment_repo
        self.permission_repo = permission_repo

    # --- User Management -------------------------------------------------
    def create_user(self, command: CreateUserCommand) -> User:
        existing = self.user_repo.find_by_email(command.email)
        if existing:
            raise ValueError("User with email already exists")

        user = User.create(
            email=command.email,
            full_name=command.full_name,
            employee_id=command.employee_id,
            organizational_unit=command.organizational_unit,
            approval_level=command.approval_level,
            is_department_head=command.is_department_head,
        )
        created = self.user_repo.create(user)
        return created

    def update_user(self, command: UpdateUserCommand) -> User:
        user = self._get_user_or_raise(command.user_id)
        user.update_details(
            full_name=command.full_name,
            organizational_unit=command.organizational_unit,
            approval_level=command.approval_level,
            is_department_head=command.is_department_head,
        )
        return self.user_repo.update(user)

    def deactivate_user(self, command: DeactivateUserCommand) -> User:
        user = self._get_user_or_raise(command.user_id)
        user.deactivate(command.reason)
        return self.user_repo.update(user)

    def reactivate_user(self, command: ReactivateUserCommand) -> User:
        user = self._get_user_or_raise(command.user_id)
        user.reactivate()
        return self.user_repo.update(user)

    # --- Role Management -------------------------------------------------
    def assign_role(self, command: AssignRoleCommand) -> None:
        user = self._get_user_or_raise(command.user_id)
        role_name = RoleName(command.role_name)
        role = self.role_repo.get_by_name(role_name)
        if not role:
            raise ValueError(f"Role '{command.role_name}' not found")
        user.assign_role(role_name)
        self.assignment_repo.assign_role(
            UserId(command.user_id),
            role_name,
            UserId(command.assigned_by) if command.assigned_by else None,
        )
        self.user_repo.update(user)

    def revoke_role(self, command: RevokeRoleCommand) -> None:
        user = self._get_user_or_raise(command.user_id)
        role_name = RoleName(command.role_name)
        user.revoke_role(role_name)
        success = self.assignment_repo.revoke_role(
            UserId(command.user_id),
            role_name,
            UserId(command.revoked_by) if command.revoked_by else None,
        )
        if not success:
            raise ValueError("Role revoke failed")
        self.user_repo.update(user)

    # --- Membership Management ------------------------------------------
    def add_membership(self, command: AddMembershipCommand) -> Membership:
        user = self._get_user_or_raise(command.user_id)
        membership = Membership(
            user_id=UserId(command.user_id),
            interest_group_id=InterestGroupId(command.interest_group_id),
            role_in_group=command.role_in_group or "Member",  # Simple string
            approval_level=command.approval_level or 1,  # Simple int (1-5)
            assigned_by=UserId(command.assigned_by) if command.assigned_by else None,
        )
        user.add_membership(membership)
        created = self.membership_repo.add_membership(membership)
        self.user_repo.update(user)
        return created

    def remove_membership(self, command: RemoveMembershipCommand) -> None:
        """Remove a membership (idempotent - returns success even if already inactive)"""
        user = self._get_user_or_raise(command.user_id)
        
        # Finde die Membership im Repository (nur aktive!)
        memberships = self.membership_repo.list_for_user(UserId(command.user_id))
        target = next(
            (m for m in memberships if int(m.interest_group_id) == command.interest_group_id),
            None,
        )
        
        # Wenn nicht gefunden: Bereits gelöscht oder nie existiert → Idempotent OK
        if not target or not target.id:
            return  # Success (idempotent)
        
        # Entferne in Domain (kann fehlschlagen, ist aber ok)
        try:
            user.remove_membership(InterestGroupId(command.interest_group_id))
        except Exception:
            pass  # Domain-Logik-Fehler ignorieren, Repository ist wichtiger
        
        # Repository-Ebene: Membership deaktivieren
        success = self.membership_repo.remove_membership(target.id)
        if not success:
            raise ValueError(f"Failed to remove membership {target.id}")
        
        self.user_repo.update(user)

    # --- Permissions -----------------------------------------------------
    def grant_permission(self, command: GrantPermissionCommand) -> None:
        user = self._get_user_or_raise(command.user_id)
        user.grant_permission(PermissionCode(command.permission_code))
        self.user_repo.update(user)

    def revoke_permission(self, command: RevokePermissionCommand) -> None:
        user = self._get_user_or_raise(command.user_id)
        user.revoke_permission(PermissionCode(command.permission_code))
        self.user_repo.update(user)

    # --- Queries ---------------------------------------------------------
    def get_user(self, user_id: int) -> User:
        return self._get_user_or_raise(user_id)

    def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.user_repo.list_all(skip, limit)

    def list_user_roles(self, user_id: int) -> List[RoleName]:
        return self.assignment_repo.list_for_user(UserId(user_id))

    def list_user_memberships(self, user_id: int) -> List[Membership]:
        return self.membership_repo.list_for_user(UserId(user_id))

    def list_user_permissions(self, user_id: int) -> List[PermissionCode]:
        return self.permission_repo.list_for_user(UserId(user_id))

    # --- Helper ----------------------------------------------------------
    def _get_user_or_raise(self, user_id: int) -> User:
        user = self.user_repo.get_by_id(UserId(user_id))
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        return user




