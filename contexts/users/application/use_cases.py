"""
Use Case Layer für Users Context

Enthält orchestrierende Funktionen, welche Commands entgegennehmen und Services nutzen.
"""

from __future__ import annotations

from typing import List

from .services import UserService
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
from contexts.users.domain import User, RoleName, Membership, PermissionCode


class CreateUserUseCase:
    def __init__(self, service: UserService) -> None:
        self.service = service

    def execute(self, command: CreateUserCommand) -> User:
        return self.service.create_user(command)


class UpdateUserUseCase:
    def __init__(self, service: UserService) -> None:
        self.service = service

    def execute(self, command: UpdateUserCommand) -> User:
        return self.service.update_user(command)


class DeactivateUserUseCase:
    def __init__(self, service: UserService) -> None:
        self.service = service

    def execute(self, command: DeactivateUserCommand) -> User:
        return self.service.deactivate_user(command)


class ReactivateUserUseCase:
    def __init__(self, service: UserService) -> None:
        self.service = service

    def execute(self, command: ReactivateUserCommand) -> User:
        return self.service.reactivate_user(command)


class AssignRoleUseCase:
    def __init__(self, service: UserService) -> None:
        self.service = service

    def execute(self, command: AssignRoleCommand) -> None:
        self.service.assign_role(command)


class RevokeRoleUseCase:
    def __init__(self, service: UserService) -> None:
        self.service = service

    def execute(self, command: RevokeRoleCommand) -> None:
        self.service.revoke_role(command)


class AddMembershipUseCase:
    def __init__(self, service: UserService) -> None:
        self.service = service

    def execute(self, command: AddMembershipCommand) -> Membership:
        return self.service.add_membership(command)


class RemoveMembershipUseCase:
    def __init__(self, service: UserService) -> None:
        self.service = service

    def execute(self, command: RemoveMembershipCommand) -> None:
        self.service.remove_membership(command)


class GrantPermissionUseCase:
    def __init__(self, service: UserService) -> None:
        self.service = service

    def execute(self, command: GrantPermissionCommand) -> None:
        self.service.grant_permission(command)


class RevokePermissionUseCase:
    def __init__(self, service: UserService) -> None:
        self.service = service

    def execute(self, command: RevokePermissionCommand) -> None:
        self.service.revoke_permission(command)


class GetUserUseCase:
    def __init__(self, service: UserService) -> None:
        self.service = service

    def execute(self, user_id: int) -> User:
        return self.service.get_user(user_id)


class ListUsersUseCase:
    def __init__(self, service: UserService) -> None:
        self.service = service

    def execute(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.service.list_users(skip, limit)


class ListUserRolesUseCase:
    def __init__(self, service: UserService) -> None:
        self.service = service

    def execute(self, user_id: int) -> List[RoleName]:
        return self.service.list_user_roles(user_id)


class ListUserMembershipsUseCase:
    def __init__(self, service: UserService) -> None:
        self.service = service

    def execute(self, user_id: int) -> List[Membership]:
        return self.service.list_user_memberships(user_id)


class ListUserPermissionsUseCase:
    def __init__(self, service: UserService) -> None:
        self.service = service

    def execute(self, user_id: int) -> List[PermissionCode]:
        return self.service.list_user_permissions(user_id)




