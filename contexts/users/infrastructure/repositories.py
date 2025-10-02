"""
SQLAlchemy basierte Repositories für Users Context

Nutzen bestehende Legacy-Tabellen (`users`, `user_group_memberships`) ohne Schemaänderung.
"""

from __future__ import annotations

import json
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models import (
    User as UserModel,
    UserGroupMembership,
    InterestGroup as InterestGroupModel,
)

from contexts.users.domain import (
    User,
    Role,
    Membership,
    RoleName,
    PermissionCode,
    MembershipRole,
    InterestGroupId,
    UserId,
)
from contexts.users.domain.repositories import (
    UserRepository,
    RoleRepository,
    MembershipRepository,
    AssignmentRepository,
    PermissionRepository,
)
from .mappers import UserMapper, MembershipMapper


ROLE_PERMISSION_MAP = {
    "system_admin": ["system_administration", "user_management", "audit_management"],
    "qm_manager": ["final_approval", "gap_analysis", "system_administration"],
    "dev_lead": ["design_approval", "change_management"],
    "team_member": [],
    "external_auditor": ["audit_read", "compliance_check"],
}


class SQLAlchemySessionMixin:
    """Hilfsmix-in zur Verwaltung von Sessions"""

    def __init__(self, session: Optional[Session] = None) -> None:
        self._external_session = session

    def _get_session(self) -> Session:
        if self._external_session is not None:
            return self._external_session
        return SessionLocal()

    def _dispose_session(self, session: Session) -> None:
        if self._external_session is None:
            session.close()


class SQLUserRepository(SQLAlchemySessionMixin, UserRepository):
    def get_by_id(self, user_id: UserId) -> Optional[User]:
        session = self._get_session()
        try:
            model = session.get(UserModel, int(user_id))
            if not model:
                return None
            return UserMapper.to_domain(model)
        finally:
            self._dispose_session(session)

    def find_by_email(self, email: str) -> Optional[User]:
        session = self._get_session()
        try:
            model = session.query(UserModel).filter(UserModel.email == email).first()
            if not model:
                return None
            return UserMapper.to_domain(model)
        finally:
            self._dispose_session(session)

    def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        session = self._get_session()
        try:
            models = (
                session.query(UserModel)
                .order_by(UserModel.id)
                .offset(skip)
                .limit(limit)
                .all()
            )
            return [UserMapper.to_domain(model) for model in models]
        finally:
            self._dispose_session(session)

    def create(self, user: User) -> User:
        session = self._get_session()
        try:
            model = UserMapper.to_model(user)
            session.add(model)
            session.commit()
            session.refresh(model)
            return UserMapper.to_domain(model)
        finally:
            self._dispose_session(session)

    def update(self, user: User) -> User:
        session = self._get_session()
        try:
            existing = session.get(UserModel, int(user.id))
            if not existing:
                raise ValueError("User not found")
            updated_model = UserMapper.to_model(user, existing)
            session.add(updated_model)
            session.commit()
            session.refresh(updated_model)
            return UserMapper.to_domain(updated_model)
        finally:
            self._dispose_session(session)


class SQLRoleRepository(SQLAlchemySessionMixin, RoleRepository):
    def get_by_name(self, role_name: RoleName) -> Optional[Role]:
        permissions = ROLE_PERMISSION_MAP.get(str(role_name))
        if permissions is None:
            return None
        return Role(name=role_name, permissions=[PermissionCode(p) for p in permissions], is_active=True)

    def list_all(self) -> List[Role]:
        return [
            Role(
                name=RoleName(name),
                permissions=[PermissionCode(p) for p in perms],
                is_active=True,
            )
            for name, perms in ROLE_PERMISSION_MAP.items()
        ]

    def list_for_user(self, user_id: UserId) -> List[Role]:
        permissions_repo = SQLPermissionRepository()
        user_permissions = permissions_repo.list_for_user(user_id)
        result = []
        for name, perms in ROLE_PERMISSION_MAP.items():
            if all(PermissionCode(p) in user_permissions for p in perms):
                result.append(self.get_by_name(RoleName(name)))
        return [role for role in result if role]


class SQLMembershipRepository(SQLAlchemySessionMixin, MembershipRepository):
    def list_for_user(self, user_id: UserId) -> List[Membership]:
        session = self._get_session()
        try:
            models = (
                session.query(UserGroupMembership, InterestGroupModel)
                .join(InterestGroupModel, InterestGroupModel.id == UserGroupMembership.interest_group_id)
                .filter(
                    UserGroupMembership.user_id == int(user_id),
                    UserGroupMembership.is_active.is_(True)  # Nur aktive Memberships!
                )
                .all()
            )

            memberships: List[Membership] = []
            for membership_model, group_model in models:
                domain_membership = MembershipMapper.to_domain(
                    membership_model,
                    interest_group=group_model,
                )
                memberships.append(domain_membership)

            return memberships
        finally:
            self._dispose_session(session)

    def add_membership(self, membership: Membership) -> Membership:
        session = self._get_session()
        try:
            model = MembershipMapper.to_models(membership)
            session.add(model)
            session.commit()
            session.refresh(model)
            return MembershipMapper.to_domain(model)
        finally:
            self._dispose_session(session)

    def remove_membership(self, membership_id: int) -> bool:
        session = self._get_session()
        try:
            model = session.get(UserGroupMembership, membership_id)
            if not model:
                return False
            model.is_active = False
            session.add(model)
            session.commit()
            return True
        finally:
            self._dispose_session(session)

    def is_member(self, user_id: UserId, interest_group_id: InterestGroupId) -> bool:
        session = self._get_session()
        try:
            exists = (
                session.query(UserGroupMembership)
                .filter(
                    UserGroupMembership.user_id == int(user_id),
                    UserGroupMembership.interest_group_id == int(interest_group_id),
                    UserGroupMembership.is_active.is_(True),
                )
                .first()
            )
            return exists is not None
        finally:
            self._dispose_session(session)


class SQLAssignmentRepository(SQLAlchemySessionMixin, AssignmentRepository):
    def assign_role(self, user_id: UserId, role_name: RoleName, assigned_by: Optional[UserId] = None) -> None:
        session = self._get_session()
        try:
            user = session.get(UserModel, int(user_id))
            if not user:
                raise ValueError("User not found")
            permissions = ROLE_PERMISSION_MAP.get(str(role_name))
            if permissions is None:
                raise ValueError("Role not defined")
            existing = []
            if user.individual_permissions:
                try:
                    existing = json.loads(user.individual_permissions)
                except (json.JSONDecodeError, TypeError):
                    existing = [user.individual_permissions]
            merged = list({*existing, *permissions})
            user.individual_permissions = json.dumps(merged, ensure_ascii=False)
            session.add(user)
            session.commit()
        finally:
            self._dispose_session(session)

    def revoke_role(self, user_id: UserId, role_name: RoleName, revoked_by: Optional[UserId] = None) -> bool:
        session = self._get_session()
        try:
            user = session.get(UserModel, int(user_id))
            if not user:
                return False
            permissions = ROLE_PERMISSION_MAP.get(str(role_name))
            if permissions is None:
                return False
            if not user.individual_permissions:
                return False
            try:
                current = json.loads(user.individual_permissions)
            except (json.JSONDecodeError, TypeError):
                current = [user.individual_permissions]
            remaining = [perm for perm in current if perm not in permissions]
            user.individual_permissions = json.dumps(remaining, ensure_ascii=False) if remaining else None
            session.add(user)
            session.commit()
            return True
        finally:
            self._dispose_session(session)

    def list_for_user(self, user_id: UserId) -> List[RoleName]:
        permissions_repo = SQLPermissionRepository()
        user_permissions = permissions_repo.list_for_user(user_id)
        role_names = []
        for name, perms in ROLE_PERMISSION_MAP.items():
            if all(PermissionCode(p) in user_permissions for p in perms):
                role_names.append(RoleName(name))
        return role_names


class SQLPermissionRepository(SQLAlchemySessionMixin, PermissionRepository):
    def list_for_user(self, user_id: UserId) -> List[PermissionCode]:
        session = self._get_session()
        try:
            user = session.get(UserModel, int(user_id))
            if not user or not user.individual_permissions:
                return []
            try:
                raw = json.loads(user.individual_permissions)
            except (json.JSONDecodeError, TypeError):
                raw = [user.individual_permissions]
            return [PermissionCode(code) for code in raw]
        finally:
            self._dispose_session(session)

    def list_for_role(self, role_name: RoleName) -> List[PermissionCode]:
        return [PermissionCode(code) for code in ROLE_PERMISSION_MAP.get(str(role_name), [])]


