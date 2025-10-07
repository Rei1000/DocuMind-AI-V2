"""
AccessControl Infrastructure Adapters

Repository-Implementierungen mit Legacy-Integration
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..domain.entities import User, Role, Permission, Assignment, Membership
from ..application.ports import (
    UserRepository, RoleRepository, PermissionRepository,
    AssignmentRepository, MembershipRepository, PolicyPort, AuditPort
)
from .acl_gateways import (
    LegacyUserACLGateway, LegacyMembershipACLGateway, LegacyPermissionACLGateway
)


class LegacyUserRepository:
    """User Repository mit Legacy-Integration"""
    
    def __init__(self, legacy_gateway: LegacyUserACLGateway):
        self.legacy_gateway = legacy_gateway
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """User by ID abrufen"""
        legacy_user = self.legacy_gateway.get_user_by_id(user_id)
        if not legacy_user:
            return None
        
        return self._map_legacy_to_domain(legacy_user)
    
    def find_by_email(self, email: str) -> Optional[User]:
        """User by Email finden"""
        legacy_user = self.legacy_gateway.get_user_by_email(email)
        if not legacy_user:
            return None
        
        return self._map_legacy_to_domain(legacy_user)
    
    def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Alle User auflisten"""
        legacy_users = self.legacy_gateway.list_users(skip, limit)
        return [self._map_legacy_to_domain(user_data) for user_data in legacy_users]
    
    def create(self, user: User) -> User:
        """User erstellen - TODO: Legacy-Integration"""
        # TODO: Implementierung für User-Erstellung
        raise NotImplementedError("User creation not yet implemented in Legacy adapter")
    
    def update(self, user: User) -> User:
        """User aktualisieren - TODO: Legacy-Integration"""
        # TODO: Implementierung für User-Update
        raise NotImplementedError("User update not yet implemented in Legacy adapter")
    
    def delete(self, user_id: int) -> bool:
        """User löschen - TODO: Legacy-Integration"""
        # TODO: Implementierung für User-Delete
        raise NotImplementedError("User deletion not yet implemented in Legacy adapter")
    
    def _map_legacy_to_domain(self, legacy_user: dict) -> User:
        """Legacy User-Daten zu Domain Entity mappen"""
        return User(
            id=legacy_user['id'],
            email=legacy_user['email'],
            full_name=legacy_user['full_name'],
            employee_id=legacy_user.get('employee_id'),
            organizational_unit=legacy_user.get('organizational_unit'),
            is_department_head=bool(legacy_user.get('is_department_head', False)),
            approval_level=legacy_user.get('approval_level', 1),
            is_active=bool(legacy_user.get('is_active', True)),
            created_at=self._parse_datetime(legacy_user.get('created_at'))
        )
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Datetime-String parsen"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None


class LegacyRoleRepository:
    """Role Repository mit Legacy-Integration"""
    
    def __init__(self, legacy_gateway: LegacyUserACLGateway):
        self.legacy_gateway = legacy_gateway
    
    def get_by_id(self, role_id: int) -> Optional[Role]:
        """Role by ID abrufen - TODO: Legacy-Integration"""
        # TODO: Implementierung für Role-Abruf (keine Role-Tabelle in Legacy)
        raise NotImplementedError("Role repository not yet implemented")
    
    def get_by_name(self, role_name: str) -> Optional[Role]:
        """Role by Name abrufen - Legacy-Integration über User-Permissions"""
        # Legacy hat keine explizite Role-Tabelle, verwende Permission-basierte Rollen
        role_permissions = self._get_role_permissions(role_name)
        if role_permissions:
            return Role(
                name=role_name,
                description=f"Role: {role_name}",
                permissions=role_permissions,
                is_active=True
            )
        return None
    
    def list_all(self) -> List[Role]:
        """Alle Rollen auflisten - Legacy-Integration"""
        # Definiere Standard-Rollen basierend auf Legacy-Permissions
        standard_roles = [
            "system_admin",
            "qm_manager", 
            "dev_lead",
            "team_member",
            "external_auditor"
        ]
        
        roles = []
        for role_name in standard_roles:
            role = self.get_by_name(role_name)
            if role:
                roles.append(role)
        
        return roles
    
    def list_for_user(self, user_id: int) -> List[Role]:
        """Rollen für User auflisten - Legacy-Integration"""
        # Hole User-Permissions und leite Rollen ab
        user = self.legacy_gateway.get_user_by_id(user_id)
        if not user:
            return []
        
        user_permissions = []
        if user.get('individual_permissions'):
            import json
            try:
                user_permissions = json.loads(user['individual_permissions'])
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Leite Rollen aus Permissions ab
        roles = []
        if 'system_administration' in user_permissions:
            roles.append(self.get_by_name('system_admin'))
        if 'final_approval' in user_permissions:
            roles.append(self.get_by_name('qm_manager'))
        if 'design_approval' in user_permissions:
            roles.append(self.get_by_name('dev_lead'))
        if 'audit_read' in user_permissions:
            roles.append(self.get_by_name('external_auditor'))
        
        # Standard-Rolle für alle User
        if not roles:
            roles.append(self.get_by_name('team_member'))
        
        return [role for role in roles if role is not None]


# DDD Guard Adapter Functions
def get_user_by_id(user_id: int) -> Optional[User]:
    """DDD Guard: User by ID abrufen für JWT-basierte Authentifizierung"""
    from contexts.accesscontrol.infrastructure.repositories import UserRepositoryImpl
    from backend.app.database import SessionLocal
    
    # Create fresh DB session
    db = SessionLocal()
    try:
        user_repo = UserRepositoryImpl(db)
        user = user_repo.find_by_id(user_id)
        return user
    finally:
        db.close()


def get_user_by_email(email: str) -> Optional[User]:
    """DDD Guard: User by Email abrufen für JWT-basierte Authentifizierung"""
    from contexts.accesscontrol.infrastructure.repositories import UserRepositoryImpl
    from backend.app.database import SessionLocal
    
    # Create fresh DB session
    db = SessionLocal()
    try:
        user_repo = UserRepositoryImpl(db)
        user = user_repo.find_by_email(email)
        return user
    finally:
        db.close()
    
    def create(self, role: Role) -> Role:
        """Role erstellen - TODO: Legacy-Integration"""
        raise NotImplementedError("Role creation not yet implemented")
    
    def update(self, role: Role) -> Role:
        """Role aktualisieren - TODO: Legacy-Integration"""
        raise NotImplementedError("Role update not yet implemented")
    
    def _get_role_permissions(self, role_name: str) -> List[str]:
        """Permissions für Role abrufen"""
        role_permissions = {
            "system_admin": ["system_administration", "user_management", "audit_management"],
            "qm_manager": ["final_approval", "gap_analysis", "system_administration"],
            "dev_lead": ["design_approval", "change_management"],
            "team_member": [],
            "external_auditor": ["audit_read", "compliance_check"]
        }
        return role_permissions.get(role_name, [])


class LegacyPermissionRepository:
    """Permission Repository mit Legacy-Integration"""
    
    def __init__(self, legacy_gateway: LegacyPermissionACLGateway):
        self.legacy_gateway = legacy_gateway
    
    def get_by_code(self, permission_code: str) -> Optional[Permission]:
        """Permission by Code abrufen"""
        # TODO: Implementierung für Permission-Abruf
        # Für jetzt: Fake Permission erstellen
        return Permission(
            code=permission_code,
            name=permission_code.replace('_', ' ').title(),
            description=f"Permission: {permission_code}"
        )
    
    def list_all(self) -> List[Permission]:
        """Alle Permissions auflisten - TODO: Legacy-Integration"""
        # TODO: Implementierung für Permission-Liste
        return []
    
    def list_for_role(self, role_name: str) -> List[Permission]:
        """Permissions für Role auflisten - TODO: Legacy-Integration"""
        # TODO: Implementierung für Role-Permissions
        return []
    
    def list_for_user(self, user_id: int) -> List[Permission]:
        """Permissions für User auflisten (aggregiert)"""
        permission_codes = self.legacy_gateway.get_user_permissions(user_id)
        return [
            Permission(code=code, name=code.replace('_', ' ').title())
            for code in permission_codes
        ]
    
    def create(self, permission: Permission) -> Permission:
        """Permission erstellen - TODO: Legacy-Integration"""
        raise NotImplementedError("Permission creation not yet implemented")


class LegacyAssignmentRepository:
    """Assignment Repository mit Legacy-Integration"""
    
    def __init__(self, legacy_gateway: LegacyUserACLGateway):
        self.legacy_gateway = legacy_gateway
    
    def assign_role(self, user_id: int, role_name: str, assigned_by: Optional[int] = None) -> Assignment:
        """Role zuweisen - Legacy-Integration über User-Permissions"""
        # Prüfe ob User existiert
        user = self.legacy_gateway.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Prüfe ob Role bereits zugewiesen
        if self.is_assigned(user_id, role_name):
            raise ValueError(f"User {user_id} already has role '{role_name}'")
        
        # Hole aktuelle Permissions
        current_permissions = []
        if user.get('individual_permissions'):
            import json
            try:
                current_permissions = json.loads(user['individual_permissions'])
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Füge Role-Permissions hinzu
        role_permissions = self._get_role_permissions(role_name)
        new_permissions = list(set(current_permissions + role_permissions))
        
        # Update User-Permissions in DB
        self._update_user_permissions(user_id, new_permissions)
        
        # Erstelle Assignment-Entity
        return Assignment(
            user_id=user_id,
            role_name=role_name,
            assigned_at=datetime.utcnow(),
            assigned_by=assigned_by,
            is_active=True
        )
    
    def revoke_role(self, user_id: int, role_name: str, revoked_by: Optional[int] = None) -> bool:
        """Role entziehen - Legacy-Integration über User-Permissions"""
        # Prüfe ob User existiert
        user = self.legacy_gateway.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Prüfe ob Role zugewiesen ist
        if not self.is_assigned(user_id, role_name):
            raise ValueError(f"User {user_id} does not have role '{role_name}'")
        
        # Hole aktuelle Permissions
        current_permissions = []
        if user.get('individual_permissions'):
            import json
            try:
                current_permissions = json.loads(user['individual_permissions'])
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Entferne Role-Permissions
        role_permissions = self._get_role_permissions(role_name)
        new_permissions = [p for p in current_permissions if p not in role_permissions]
        
        # Update User-Permissions in DB
        self._update_user_permissions(user_id, new_permissions)
        
        return True
    
    def list_for_user(self, user_id: int) -> List[Assignment]:
        """Assignments für User auflisten - Legacy-Integration"""
        # Hole User-Permissions und leite Rollen ab
        user = self.legacy_gateway.get_user_by_id(user_id)
        if not user:
            return []
        
        user_permissions = []
        if user.get('individual_permissions'):
            import json
            try:
                user_permissions = json.loads(user['individual_permissions'])
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Leite Rollen aus Permissions ab
        assignments = []
        role_names = ["system_admin", "qm_manager", "dev_lead", "external_auditor"]
        
        for role_name in role_names:
            if self.is_assigned(user_id, role_name):
                assignments.append(Assignment(
                    user_id=user_id,
                    role_name=role_name,
                    assigned_at=datetime.utcnow(),  # TODO: Echte Timestamps
                    is_active=True
                ))
        
        return assignments
    
    def list_for_role(self, role_name: str) -> List[Assignment]:
        """Assignments für Role auflisten - Legacy-Integration"""
        # Hole alle User und prüfe Rollen
        users = self.legacy_gateway.list_users(limit=1000)
        assignments = []
        
        for user_data in users:
            user_id = user_data['id']
            if self.is_assigned(user_id, role_name):
                assignments.append(Assignment(
                    user_id=user_id,
                    role_name=role_name,
                    assigned_at=datetime.utcnow(),  # TODO: Echte Timestamps
                    is_active=True
                ))
        
        return assignments
    
    def is_assigned(self, user_id: int, role_name: str) -> bool:
        """Prüfen ob Role zugewiesen ist - Legacy-Integration"""
        user = self.legacy_gateway.get_user_by_id(user_id)
        if not user:
            return False
        
        user_permissions = []
        if user.get('individual_permissions'):
            import json
            try:
                user_permissions = json.loads(user['individual_permissions'])
            except (json.JSONDecodeError, TypeError):
                pass
        
        role_permissions = self._get_role_permissions(role_name)
        return all(perm in user_permissions for perm in role_permissions)
    
    def _get_role_permissions(self, role_name: str) -> List[str]:
        """Permissions für Role abrufen"""
        role_permissions = {
            "system_admin": ["system_administration", "user_management", "audit_management"],
            "qm_manager": ["final_approval", "gap_analysis", "system_administration"],
            "dev_lead": ["design_approval", "change_management"],
            "team_member": [],
            "external_auditor": ["audit_read", "compliance_check"]
        }
        return role_permissions.get(role_name, [])
    
    def _update_user_permissions(self, user_id: int, permissions: List[str]) -> None:
        """User-Permissions in DB aktualisieren"""
        import json
        permissions_json = json.dumps(permissions, ensure_ascii=False)
        
        # Direkter DB-Update über Engine
        from sqlalchemy import create_engine, text
        database_url = os.environ.get("DATABASE_URL", "sqlite:///.tmp/test_qms_mvp.db")
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            conn.execute(
                text("UPDATE users SET individual_permissions = :permissions WHERE id = :user_id"),
                {"permissions": permissions_json, "user_id": user_id}
            )
            conn.commit()


class LegacyMembershipRepository:
    """Membership Repository mit Legacy-Integration"""
    
    def __init__(self, legacy_gateway: LegacyMembershipACLGateway):
        self.legacy_gateway = legacy_gateway
    
    def list_groups_for_user(self, user_id: int) -> List[Membership]:
        """Groups für User auflisten"""
        legacy_memberships = self.legacy_gateway.get_memberships_for_user(user_id)
        return [self._map_legacy_to_domain(membership_data) for membership_data in legacy_memberships]
    
    def add_membership(self, membership: Membership) -> Membership:
        """Membership hinzufügen"""
        membership_data = {
            'user_id': membership.user_id,
            'interest_group_id': membership.interest_group_id,
            'role_in_group': membership.role_in_group,
            'approval_level': membership.approval_level,
            'is_department_head': membership.is_department_head,
            'is_active': membership.is_active,
            'assigned_by_id': membership.assigned_by,
            'notes': membership.notes
        }
        
        legacy_membership = self.legacy_gateway.create_membership(membership_data)
        return self._map_legacy_to_domain(legacy_membership)
    
    def remove_membership(self, user_id: int, group_id: int) -> bool:
        """Membership entfernen - TODO: Legacy-Integration"""
        # TODO: Implementierung für Membership-Removal
        raise NotImplementedError("Membership removal not yet implemented")
    
    def update_membership(self, membership: Membership) -> Membership:
        """Membership aktualisieren - TODO: Legacy-Integration"""
        # TODO: Implementierung für Membership-Update
        raise NotImplementedError("Membership update not yet implemented")
    
    def is_member(self, user_id: int, group_id: int) -> bool:
        """Prüfen ob User Mitglied ist"""
        memberships = self.list_groups_for_user(user_id)
        return any(m.interest_group_id == group_id and m.is_active for m in memberships)
    
    def _map_legacy_to_domain(self, legacy_membership: dict) -> Membership:
        """Legacy Membership-Daten zu Domain Entity mappen"""
        return Membership(
            user_id=legacy_membership['user_id'],
            interest_group_id=legacy_membership['interest_group_id'],
            role_in_group=legacy_membership.get('role_in_group'),
            approval_level=legacy_membership.get('approval_level', 1),
            is_department_head=bool(legacy_membership.get('is_department_head', False)),
            is_active=bool(legacy_membership.get('is_active', True)),
            joined_at=self._parse_datetime(legacy_membership.get('joined_at')),
            assigned_by=legacy_membership.get('assigned_by_id'),
            notes=legacy_membership.get('notes')
        )
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Datetime-String parsen"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None


class LegacyPolicyPort:
    """Policy Port mit Legacy-Integration"""
    
    def __init__(self, 
                 user_repo: LegacyUserRepository,
                 permission_repo: LegacyPermissionRepository,
                 membership_repo: LegacyMembershipRepository,
                 legacy_permission_gateway: LegacyPermissionACLGateway):
        self.user_repo = user_repo
        self.permission_repo = permission_repo
        self.membership_repo = membership_repo
        self.legacy_permission_gateway = legacy_permission_gateway
    
    def check_access(self, user_id: int, permission_code: str, resource: Optional[str] = None) -> bool:
        """Zugriff prüfen"""
        return self.legacy_permission_gateway.check_user_access(user_id, permission_code)
    
    def can_approve(self, user_id: int, required_level: int) -> bool:
        """Freigabe-Berechtigung prüfen"""
        user_approval_level = self.legacy_permission_gateway.get_user_approval_level(user_id)
        return user_approval_level >= required_level
    
    def can_manage_users(self, user_id: int) -> bool:
        """User-Management-Berechtigung prüfen"""
        user_approval_level = self.legacy_permission_gateway.get_user_approval_level(user_id)
        is_dept_head = self.legacy_permission_gateway.is_user_department_head(user_id)
        return user_approval_level >= 4 or is_dept_head
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """User-Permissions abrufen (aggregiert)"""
        return self.legacy_permission_gateway.get_user_permissions(user_id)


class FakeAuditPort:
    """Fake Audit Port für Tests"""
    
    def record(self, event_type: str, user_id: int, details: dict) -> None:
        """Event aufzeichnen - Fake Implementation"""
        print(f"[AUDIT] {event_type}: user={user_id}, details={details}")
    
    def record_access_check(self, user_id: int, permission_code: str, granted: bool) -> None:
        """Access-Check aufzeichnen - Fake Implementation"""
        print(f"[AUDIT] access_check: user={user_id}, permission={permission_code}, granted={granted}")
    
    def record_role_assignment(self, user_id: int, role_name: str, assigned_by: int) -> None:
        """Role-Assignment aufzeichnen - Fake Implementation"""
        print(f"[AUDIT] role_assignment: user={user_id}, role={role_name}, assigned_by={assigned_by}")


# Factory für Adapter

class AdapterFactory:
    """Factory für Repository Adapter"""
    
    @staticmethod
    def create_adapters(database_url: str):
        """Alle Adapter erstellen"""
        from .acl_gateways import ACLGatewayFactory
        
        # ACL Gateways erstellen
        user_gateway = ACLGatewayFactory.create_user_gateway(database_url)
        membership_gateway = ACLGatewayFactory.create_membership_gateway(database_url)
        permission_gateway = ACLGatewayFactory.create_permission_gateway(database_url)
        
        # Repository Adapter erstellen
        user_repo = LegacyUserRepository(user_gateway)
        role_repo = LegacyRoleRepository(user_gateway)  # Legacy-Integration implementiert
        permission_repo = LegacyPermissionRepository(permission_gateway)
        assignment_repo = LegacyAssignmentRepository(user_gateway)  # Legacy-Integration implementiert
        membership_repo = LegacyMembershipRepository(membership_gateway)
        
        # Policy Port erstellen
        policy_port = LegacyPolicyPort(user_repo, permission_repo, membership_repo, permission_gateway)
        
        # Audit Port erstellen
        audit_port = FakeAuditPort()
        
        return {
            'user_repo': user_repo,
            'role_repo': role_repo,
            'permission_repo': permission_repo,
            'assignment_repo': assignment_repo,
            'membership_repo': membership_repo,
            'policy_port': policy_port,
            'audit_port': audit_port
        }
