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
from contexts.users.domain.value_objects import ApprovalLevel
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
        normalized_email = command.email.strip().lower()
        existing = self.user_repo.find_by_email(normalized_email)
        if existing:
            raise ValueError("User with email already exists")

        user = User.create(
            email=normalized_email,
            full_name=command.full_name,
            employee_id=command.employee_id,
            organizational_unit=command.organizational_unit,
            approval_level=command.approval_level,
            is_department_head=command.is_department_head,
        )
        created = self.user_repo.create(user, password=command.password)  # Passwort an Repository weitergeben
        
        # ENTFERNT: Validierung für Membership-Pflicht entfernt
        # Grund: Memberships werden erst NACH User-Erstellung über Drag & Drop zugewiesen
        # Die ursprüngliche Validierung führte zu einem Henne-Ei-Problem:
        # User konnte nicht erstellt werden, weil keine Memberships existierten,
        # aber Memberships konnten nicht erstellt werden, weil User nicht existierte.
        # 
        # Optional: UI-Warnung anzeigen, wenn User ohne Memberships erstellt wird
        
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
            approval_level=ApprovalLevel(command.approval_level or 1),
            assigned_by=UserId(command.assigned_by) if command.assigned_by else None,
        )
        user.add_membership(membership)
        created = self.membership_repo.add_membership(membership)
        
        # RBAC: Wenn User Level 4 erhält, setze alle anderen Memberships auf Level 4
        if command.approval_level and command.approval_level >= 4:
            self._sync_level_4_to_all_groups(command.user_id)
        
        self.user_repo.update(user)
        return created
    
    def _sync_level_4_to_all_groups(self, user_id: int) -> None:
        """
        Synchronisiert Level 4 für einen User: Wenn User Level 4 in mindestens einer IG hat,
        werden alle anderen Memberships automatisch auf Level 4 gesetzt.
        
        Grund: Level 4 User (QM-Manager) sehen ALLE Dokumente, daher macht es keinen Sinn,
        unterschiedliche Levels pro IG zu haben.
        """
        # Hole alle Memberships des Users
        all_memberships = self.membership_repo.list_for_user(UserId(user_id))
        
        def _level_value(level: object) -> int:
            return int(level) if hasattr(level, "__int__") else int(level)

        # Prüfe ob User bereits Level 4 in mindestens einer IG hat
        has_level_4 = any(_level_value(m.approval_level) >= 4 for m in all_memberships)
        
        if has_level_4:
            # Aktualisiere alle Memberships < Level 4 auf Level 4
            from contexts.users.domain import InterestGroupId
            from backend.app.models import UserGroupMembership as UserGroupMembershipModel
            from backend.app.database import SessionLocal
            from datetime import datetime
            
            db = SessionLocal()
            try:
                for membership in all_memberships:
                    if _level_value(membership.approval_level) < 4:
                        # Aktualisiere über SQLAlchemy Model (direkt, da wir den User-Context nutzen)
                        db_membership = db.query(UserGroupMembershipModel).filter(
                            UserGroupMembershipModel.id == membership.id
                        ).first()
                        
                        if db_membership:
                            db_membership.approval_level = 4
                            db_membership.role_in_group = "QM-Manager"
                            db_membership.updated_at = datetime.utcnow()
                
                db.commit()
            finally:
                db.close()

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




