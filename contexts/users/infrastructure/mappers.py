"""
Mapper für Users Context

Konvertiert zwischen SQLAlchemy Modellen und Domain Entities.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional, List

from backend.app.models import User as UserModel, UserGroupMembership, InterestGroup as InterestGroupModel
from contexts.users.domain import (
    User,
    Membership,
    RoleName,
    PermissionCode,
    MembershipRole,
    InterestGroupId,
    UserId,
)
from contexts.users.domain.value_objects import (
    LenientEmailAddress,
    LenientFullName,
    EmployeeId,
    OrganizationalUnit,
    ApprovalLevel,
)


class UserMapper:
    """Konvertiert User-Modelle"""

    @staticmethod
    def to_domain(model: UserModel) -> User:
        individual_permissions = []
        raw_permissions = getattr(model, "individual_permissions", None)
        if raw_permissions:
            try:
                individual_permissions = [
                    PermissionCode(code) for code in json.loads(raw_permissions)
                ]
            except (json.JSONDecodeError, TypeError):
                individual_permissions = [PermissionCode(raw_permissions)]

        user = User(
            id=UserId(model.id),
            email=LenientEmailAddress(model.email),
            full_name=LenientFullName(model.full_name),
            employee_id=EmployeeId(model.employee_id),
            organizational_unit=OrganizationalUnit(model.organizational_unit),
            approval_level=ApprovalLevel(5 if getattr(model, "is_qms_admin", False) else 1),  # Level 5 für QMS Admin, sonst aus Membership
            is_active=model.is_active,
            is_department_head=False,  # Kommt jetzt aus Membership, nicht mehr aus User
            created_at=getattr(model, "created_at", datetime.utcnow()),
            updated_at=getattr(model, "updated_at", None),
            memberships=[],
            roles=[],
            individual_permissions=individual_permissions,
        )

        # Memberships mappen
        if hasattr(model, "group_memberships"):
            for membership in model.group_memberships:
                user.memberships.append(
                    MembershipMapper.to_domain(
                        membership,
                        interest_group=getattr(membership, "interest_group", None),
                    )
                )

        # Roles approximieren aus individuellen Permissions (Legacy-Logik)
        # TODO: Sobald Role-Assignments Tabelle existiert, hier anpassen
        return user

    @staticmethod
    def to_model(entity: User, model: Optional[UserModel] = None) -> UserModel:
        if model is None:
            model = UserModel()

        model.email = str(entity.email)
        model.full_name = str(entity.full_name)
        model.employee_id = str(entity.employee_id) or None
        model.organizational_unit = str(entity.organizational_unit) or None
        model.approval_level = int(entity.approval_level)
        model.is_active = entity.is_active
        model.is_department_head = entity.is_department_head

        if entity.individual_permissions:
            model.individual_permissions = json.dumps(
                [str(code) for code in entity.individual_permissions], ensure_ascii=False
            )
        else:
            model.individual_permissions = None

        if entity.id:
            model.id = int(entity.id)

        return model


class MembershipMapper:
    @staticmethod
    def to_domain(
        model: UserGroupMembership,
        interest_group: Optional[InterestGroupModel] = None,
    ) -> Membership:
        membership = Membership(
            id=model.id,
            user_id=UserId(model.user_id),
            interest_group_id=InterestGroupId(model.interest_group_id),
            role_in_group=MembershipRole(model.role_in_group),
            approval_level=ApprovalLevel(model.approval_level or 1),
            assigned_by=UserId(model.assigned_by_id) if model.assigned_by_id else None,
            assigned_at=getattr(model, "joined_at", datetime.utcnow()),
            is_active=model.is_active,
        )

        if interest_group is None:
            ig = getattr(model, "interest_group", None)
        else:
            ig = interest_group

        if ig is not None:
            group_permissions_raw = getattr(ig, "group_permissions", None)
            if isinstance(group_permissions_raw, str) and group_permissions_raw:
                try:
                    group_permissions = json.loads(group_permissions_raw)
                except (json.JSONDecodeError, TypeError):
                    group_permissions = [group_permissions_raw]
            elif isinstance(group_permissions_raw, list):
                group_permissions = group_permissions_raw
            else:
                group_permissions = []

            membership.extra = {
                "interest_group": {
                    "id": getattr(ig, "id", None),
                    "name": getattr(ig, "name", "Unbekannt"),
                    "code": getattr(ig, "code", f"IG-{getattr(ig, 'id', '0')}") or f"IG-{getattr(ig, 'id', '0')}",
                    "description": getattr(ig, "description", None),
                    "group_permissions": group_permissions,
                    "ai_functionality": getattr(ig, "ai_functionality", None),
                    "typical_tasks": getattr(ig, "typical_tasks", None),
                    "is_external": getattr(ig, "is_external", False),
                    "is_active": getattr(ig, "is_active", True),
                    "created_at": getattr(ig, "created_at", datetime.utcnow()),
                }
            }
        else:
            membership.extra = {
                "interest_group": {
                    "id": int(membership.interest_group_id),
                    "name": "Unbekannt",
                    "code": f"IG-{int(membership.interest_group_id)}",
                    "group_permissions": [],
                    "is_external": False,
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                }
            }

        return membership

    @staticmethod
    def to_models(entity: Membership) -> UserGroupMembership:
        model = UserGroupMembership()
        model.user_id = int(entity.user_id)
        model.interest_group_id = int(entity.interest_group_id)
        model.role_in_group = str(entity.role_in_group) or None
        model.approval_level = int(entity.approval_level)
        model.is_active = entity.is_active
        model.assigned_by_id = int(entity.assigned_by) if entity.assigned_by else None
        model.joined_at = entity.assigned_at
        return model


def permissions_to_codes(raw: List[str]) -> List[PermissionCode]:
    return [PermissionCode(code) for code in raw]


