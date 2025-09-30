"""
AccessControl Use Cases

Business-Logic für RBAC-Operationen
"""

from typing import List, Optional
from ..domain.entities import User, Role, Assignment, Membership
from ..domain.value_objects import UserId, PermissionCode, RoleName
from ..domain.events import RoleAssigned, RoleRevoked, AccessChecked
from .ports import (
    UserRepository, RoleRepository, PermissionRepository, 
    AssignmentRepository, MembershipRepository, PolicyPort, AuditPort
)


class AssignRoleUseCase:
    """Use Case: Role zuweisen"""
    
    def __init__(self, 
                 user_repo: UserRepository,
                 role_repo: RoleRepository,
                 assignment_repo: AssignmentRepository,
                 audit_port: Optional[AuditPort] = None):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.assignment_repo = assignment_repo
        self.audit_port = audit_port
    
    def execute(self, user_id: int, role_name: str, assigned_by: Optional[int] = None) -> Assignment:
        """
        Role einem User zuweisen
        
        Args:
            user_id: User ID
            role_name: Role Name
            assigned_by: ID des zuweisenden Users
            
        Returns:
            Assignment: Erstellte Assignment
            
        Raises:
            ValueError: Wenn User oder Role nicht existieren
        """
        # User prüfen
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        if not user.is_active:
            raise ValueError(f"User {user_id} is not active")
        
        # Role prüfen
        role = self.role_repo.get_by_name(role_name)
        if not role:
            raise ValueError(f"Role '{role_name}' not found")
        
        if not role.is_active:
            raise ValueError(f"Role '{role_name}' is not active")
        
        # Prüfen ob bereits zugewiesen
        if self.assignment_repo.is_assigned(user_id, role_name):
            raise ValueError(f"User {user_id} already has role '{role_name}'")
        
        # Assignment erstellen
        assignment = self.assignment_repo.assign_role(user_id, role_name, assigned_by)
        
        # Audit
        if self.audit_port:
            self.audit_port.record_role_assignment(user_id, role_name, assigned_by or 0)
        
        return assignment


class RevokeRoleUseCase:
    """Use Case: Role entziehen"""
    
    def __init__(self,
                 user_repo: UserRepository,
                 role_repo: RoleRepository,
                 assignment_repo: AssignmentRepository,
                 audit_port: Optional[AuditPort] = None):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.assignment_repo = assignment_repo
        self.audit_port = audit_port
    
    def execute(self, user_id: int, role_name: str, revoked_by: Optional[int] = None) -> bool:
        """
        Role von User entziehen
        
        Args:
            user_id: User ID
            role_name: Role Name
            revoked_by: ID des entziehenden Users
            
        Returns:
            bool: True wenn erfolgreich entzogen
            
        Raises:
            ValueError: Wenn User nicht existiert oder Role nicht zugewiesen
        """
        # User prüfen
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Prüfen ob zugewiesen
        if not self.assignment_repo.is_assigned(user_id, role_name):
            raise ValueError(f"User {user_id} does not have role '{role_name}'")
        
        # Role entziehen
        success = self.assignment_repo.revoke_role(user_id, role_name, revoked_by)
        
        # Audit
        if self.audit_port and success:
            self.audit_port.record("role_revoked", user_id, {
                "role_name": role_name,
                "revoked_by": revoked_by
            })
        
        return success


class CheckAccessUseCase:
    """Use Case: Zugriff prüfen"""
    
    def __init__(self,
                 user_repo: UserRepository,
                 permission_repo: PermissionRepository,
                 policy_port: PolicyPort,
                 audit_port: Optional[AuditPort] = None):
        self.user_repo = user_repo
        self.permission_repo = permission_repo
        self.policy_port = policy_port
        self.audit_port = audit_port
    
    def execute(self, user_id: int, permission_code: str, resource: Optional[str] = None) -> bool:
        """
        Zugriff für User prüfen
        
        Args:
            user_id: User ID
            permission_code: Permission Code
            resource: Optional Resource
            
        Returns:
            bool: True wenn Zugriff erlaubt
        """
        # User prüfen
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            return False
        
        # Permission prüfen
        permission = self.permission_repo.get_by_code(permission_code)
        if not permission:
            return False
        
        # Policy-Check
        granted = self.policy_port.check_access(user_id, permission_code, resource)
        
        # Audit
        if self.audit_port:
            self.audit_port.record_access_check(user_id, permission_code, granted)
        
        return granted


class GetUserPermissionsUseCase:
    """Use Case: User-Permissions abrufen"""
    
    def __init__(self,
                 user_repo: UserRepository,
                 permission_repo: PermissionRepository,
                 policy_port: PolicyPort):
        self.user_repo = user_repo
        self.permission_repo = permission_repo
        self.policy_port = policy_port
    
    def execute(self, user_id: int) -> List[str]:
        """
        Alle Permissions für User abrufen
        
        Args:
            user_id: User ID
            
        Returns:
            List[str]: Liste der Permission Codes
        """
        # User prüfen
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            return []
        
        # Permissions abrufen
        return self.policy_port.get_user_permissions(user_id)


class CreateUserUseCase:
    """Use Case: User erstellen"""
    
    def __init__(self,
                 user_repo: UserRepository,
                 audit_port: Optional[AuditPort] = None):
        self.user_repo = user_repo
        self.audit_port = audit_port
    
    def execute(self, email: str, full_name: str, employee_id: Optional[str] = None,
                organizational_unit: Optional[str] = None, approval_level: int = 1) -> User:
        """
        Neuen User erstellen
        
        Args:
            email: Email-Adresse
            full_name: Vollständiger Name
            employee_id: Optional Employee ID
            organizational_unit: Optional Organizational Unit
            approval_level: Approval Level
            
        Returns:
            User: Erstellter User
            
        Raises:
            ValueError: Wenn Email bereits existiert
        """
        # Prüfen ob Email bereits existiert
        existing_user = self.user_repo.find_by_email(email)
        if existing_user:
            raise ValueError(f"User with email '{email}' already exists")
        
        # User erstellen
        user = User(
            id=0,  # Wird von Repository gesetzt
            email=email,
            full_name=full_name,
            employee_id=employee_id,
            organizational_unit=organizational_unit,
            approval_level=approval_level,
            is_active=True
        )
        
        created_user = self.user_repo.create(user)
        
        # Audit
        if self.audit_port:
            self.audit_port.record("user_created", created_user.id, {
                "email": email,
                "full_name": full_name,
                "approval_level": approval_level
            })
        
        return created_user


class AddMembershipUseCase:
    """Use Case: Group-Membership hinzufügen"""
    
    def __init__(self,
                 user_repo: UserRepository,
                 membership_repo: MembershipRepository,
                 audit_port: Optional[AuditPort] = None):
        self.user_repo = user_repo
        self.membership_repo = membership_repo
        self.audit_port = audit_port
    
    def execute(self, user_id: int, group_id: int, role_in_group: Optional[str] = None,
                approval_level: int = 1, assigned_by: Optional[int] = None) -> Membership:
        """
        User zu Group hinzufügen
        
        Args:
            user_id: User ID
            group_id: Group ID
            role_in_group: Optional Role in Group
            approval_level: Approval Level in Group
            assigned_by: ID des zuweisenden Users
            
        Returns:
            Membership: Erstellte Membership
            
        Raises:
            ValueError: Wenn User nicht existiert oder bereits Mitglied
        """
        # User prüfen
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        if not user.is_active:
            raise ValueError(f"User {user_id} is not active")
        
        # Prüfen ob bereits Mitglied
        if self.membership_repo.is_member(user_id, group_id):
            raise ValueError(f"User {user_id} is already member of group {group_id}")
        
        # Membership erstellen
        membership = Membership(
            user_id=user_id,
            interest_group_id=group_id,
            role_in_group=role_in_group,
            approval_level=approval_level,
            assigned_by=assigned_by,
            is_active=True
        )
        
        created_membership = self.membership_repo.add_membership(membership)
        
        # Audit
        if self.audit_port:
            self.audit_port.record("membership_created", user_id, {
                "group_id": group_id,
                "role_in_group": role_in_group,
                "approval_level": approval_level,
                "assigned_by": assigned_by
            })
        
        return created_membership

