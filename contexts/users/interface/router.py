"""
DDD FastAPI Router für Benutzerverwaltung

Ersetzt Legacy-/Adapter-Routen bei `RBAC_IMPL=ddd`.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas import (
    User,
    UserCreate,
    UserUpdate,
    UserGroupMembership,
    UserGroupMembershipCreate,
)
from backend.app.legacy_adapter_router import _ensure_legacy_user_shape

from contexts.users.application import (
    UserService,
    CreateUserUseCase,
    UpdateUserUseCase,
    DeactivateUserUseCase,
    ReactivateUserUseCase,
    AssignRoleUseCase,
    RevokeRoleUseCase,
    AddMembershipUseCase,
    RemoveMembershipUseCase,
    GetUserUseCase,
    ListUsersUseCase,
    ListUserMembershipsUseCase,
    CreateUserCommand,
    UpdateUserCommand,
    DeactivateUserCommand,
    ReactivateUserCommand,
    AssignRoleCommand,
    RevokeRoleCommand,
    AddMembershipCommand,
    RemoveMembershipCommand,
)
from contexts.users.infrastructure.repositories import (
    SQLUserRepository,
    SQLRoleRepository,
    SQLMembershipRepository,
    SQLAssignmentRepository,
    SQLPermissionRepository,
)


router = APIRouter(prefix="/api/users", tags=["users-ddd"])


def get_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(
        SQLUserRepository(db),
        SQLRoleRepository(db),
        SQLMembershipRepository(db),
        SQLAssignmentRepository(db),
        SQLPermissionRepository(db),
    )


@router.get("/", response_model=List[User])
def list_users(service: UserService = Depends(get_service)):
    return [
        _map_user_to_schema(user) for user in ListUsersUseCase(service).execute()
    ]


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, service: UserService = Depends(get_service)):
    try:
        command = CreateUserCommand(
            email=payload.email,
            full_name=payload.full_name,
            employee_id=payload.employee_id,
            organizational_unit=payload.organizational_unit,
            approval_level=payload.approval_level,
            is_department_head=payload.is_department_head,
        )
        user = CreateUserUseCase(service).execute(command)
        return _map_user_to_schema(user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{user_id}", response_model=User)
def get_user(user_id: int, service: UserService = Depends(get_service)):
    user = GetUserUseCase(service).execute(user_id)
    return _map_user_to_schema(user)


@router.put("/{user_id}", response_model=User)
def update_user(user_id: int, payload: UserUpdate, service: UserService = Depends(get_service)):
    command = UpdateUserCommand(
        user_id=user_id,
        full_name=payload.full_name,
        organizational_unit=payload.organizational_unit,
        approval_level=payload.approval_level,
        is_department_head=payload.is_department_head,
    )
    user = UpdateUserUseCase(service).execute(command)
    return _map_user_to_schema(user)


@router.post("/{user_id}/deactivate", response_model=User)
def deactivate_user(user_id: int, service: UserService = Depends(get_service)):
    command = DeactivateUserCommand(user_id=user_id)
    user = DeactivateUserUseCase(service).execute(command)
    return _map_user_to_schema(user)


@router.post("/{user_id}/reactivate", response_model=User)
def reactivate_user(user_id: int, service: UserService = Depends(get_service)):
    command = ReactivateUserCommand(user_id=user_id)
    user = ReactivateUserUseCase(service).execute(command)
    return _map_user_to_schema(user)


@router.post("/{user_id}/roles/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
def assign_role(user_id: int, role_name: str, service: UserService = Depends(get_service)):
    try:
        command = AssignRoleCommand(user_id=user_id, role_name=role_name)
        AssignRoleUseCase(service).execute(command)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{user_id}/roles/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_role(user_id: int, role_name: str, service: UserService = Depends(get_service)):
    try:
        command = RevokeRoleCommand(user_id=user_id, role_name=role_name)
        RevokeRoleUseCase(service).execute(command)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{user_id}/memberships", response_model=List[UserGroupMembership])
def list_memberships(user_id: int, service: UserService = Depends(get_service)):
    memberships = ListUserMembershipsUseCase(service).execute(user_id)
    return [_map_membership_to_schema(m) for m in memberships]


@router.post("/{user_id}/memberships", response_model=UserGroupMembership)
def add_membership(
    user_id: int,
    payload: UserGroupMembershipCreate,
    service: UserService = Depends(get_service),
):
    command = AddMembershipCommand(
        user_id=user_id,
        interest_group_id=payload.interest_group_id,
        role_in_group=payload.role_in_group,
        approval_level=payload.approval_level,
        assigned_by=None,
    )
    membership = AddMembershipUseCase(service).execute(command)
    return _map_membership_to_schema(membership)


@router.delete("/{user_id}/memberships/{interest_group_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_membership(user_id: int, interest_group_id: int, service: UserService = Depends(get_service)):
    command = RemoveMembershipCommand(user_id=user_id, interest_group_id=interest_group_id)
    RemoveMembershipUseCase(service).execute(command)


def _map_user_to_schema(user: User) -> User:
    raw_dict = {
        "id": int(user.id),
        "email": str(user.email),
        "full_name": str(user.full_name),
        "employee_id": str(user.employee_id) or None,
        "organizational_unit": str(user.organizational_unit) or None,
        "individual_permissions": [str(p) for p in user.individual_permissions],
        "permissions": [str(p) for p in user.individual_permissions],
        "is_department_head": user.is_department_head,
        "approval_level": int(user.approval_level),
        "is_active": user.is_active,
        "created_at": user.created_at,
        "department": None,
    }
    normalized = _ensure_legacy_user_shape(raw_dict)
    return User(**normalized)


def _map_membership_to_schema(membership: Membership) -> UserGroupMembership:
    membership_dict: Dict[str, Any] = {
        "id": membership.id,
        "user_id": int(membership.user_id),
        "interest_group_id": int(membership.interest_group_id),
        "role_in_group": membership.role_in_group.value if membership.role_in_group.value else None,
        "approval_level": int(membership.approval_level),
        "is_active": membership.is_active,
    }

    interest_group_data: Optional[Dict[str, Any]] = membership.extra.get("interest_group") if hasattr(membership, "extra") else None
    if interest_group_data:
        membership_dict["interest_group"] = interest_group_data

    return UserGroupMembership(**membership_dict)


