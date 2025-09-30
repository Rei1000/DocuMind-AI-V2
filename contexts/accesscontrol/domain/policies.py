"""
AccessControl Domain Policies

Business Rules und Policies für RBAC
"""

from typing import List, Set
from .entities import User, Role, Permission, Assignment
from .value_objects import PermissionCode, ApprovalLevel


class RBACPolicy:
    """RBAC Policy - Kern-Business-Rules"""
    
    @staticmethod
    def has_permission(user: User, permission_code: str, 
                      user_permissions: List[str] = None,
                      role_permissions: List[str] = None,
                      group_permissions: List[str] = None) -> bool:
        """
        Prüft ob User eine Permission hat
        
        Args:
            user: User Entity
            permission_code: Permission Code
            user_permissions: Individuelle User-Permissions
            role_permissions: Role-basierte Permissions
            group_permissions: Group-basierte Permissions
            
        Returns:
            bool: True wenn Permission vorhanden
        """
        if not user.is_active:
            return False
        
        # Superuser Shortcut: qms.admin hat immer Zugriff
        if user.email == "qms.admin" or getattr(user, 'is_superuser', False):
            return True
        
        # Admin-Rolle Shortcut: User mit admin-Rolle hat Zugriff
        if user_permissions and "admin" in user_permissions:
            return True
        
        # System-Admin hat alle Permissions
        if user.is_system_admin():
            return True
        
        # Sammle alle Permissions
        all_permissions = set()
        
        if user_permissions:
            all_permissions.update(user_permissions)
        
        if role_permissions:
            all_permissions.update(role_permissions)
        
        if group_permissions:
            all_permissions.update(group_permissions)
        
        return permission_code in all_permissions
    
    @staticmethod
    def can_approve(user: User, required_level: int) -> bool:
        """
        Prüft ob User auf einem bestimmten Level freigeben kann
        
        Args:
            user: User Entity
            required_level: Erforderliches Approval Level
            
        Returns:
            bool: True wenn User freigeben kann
        """
        if not user.is_active:
            return False
        
        return user.has_approval_level(required_level)
    
    @staticmethod
    def can_manage_users(user: User) -> bool:
        """
        Prüft ob User andere User verwalten kann
        
        Args:
            user: User Entity
            
        Returns:
            bool: True wenn User-Management erlaubt
        """
        if not user.is_active:
            return False
        
        # QM-Manager oder System-Admin
        return user.is_qm_manager() or user.is_system_admin()
    
    @staticmethod
    def can_access_resource(user: User, resource: str, 
                           user_permissions: List[str] = None) -> bool:
        """
        Prüft ob User auf eine Ressource zugreifen kann
        
        Args:
            user: User Entity
            resource: Ressourcen-Name
            user_permissions: User-Permissions
            
        Returns:
            bool: True wenn Zugriff erlaubt
        """
        if not user.is_active:
            return False
        
        # System-Admin hat Zugriff auf alles
        if user.is_system_admin():
            return True
        
        if not user_permissions:
            return False
        
        # Prüfe spezifische Resource-Permissions
        resource_permissions = [
            f"{resource}_read",
            f"{resource}_write", 
            f"{resource}_admin",
            f"admin_{resource}",
            "system_administration"
        ]
        
        return any(perm in user_permissions for perm in resource_permissions)


class ApprovalPolicy:
    """Approval Policy - Freigabe-Business-Rules"""
    
    @staticmethod
    def can_approve_document(user: User, document_type: str) -> bool:
        """
        Prüft ob User ein Dokument freigeben kann
        
        Args:
            user: User Entity
            document_type: Dokument-Typ
            
        Returns:
            bool: True wenn Freigabe erlaubt
        """
        if not user.is_active:
            return False
        
        # QM-Manager kann alle Dokumente freigeben
        if user.is_qm_manager():
            return True
        
        # Spezifische Dokument-Typ-Regeln
        if document_type in ["quality_manual", "procedures", "work_instructions"]:
            return user.has_approval_level(3)  # Abteilungsleiter
        
        if document_type in ["forms", "templates"]:
            return user.has_approval_level(2)  # Teamleiter
        
        return False
    
    @staticmethod
    def get_required_approval_level(document_type: str) -> int:
        """
        Gibt das erforderliche Approval Level für einen Dokument-Typ zurück
        
        Args:
            document_type: Dokument-Typ
            
        Returns:
            int: Erforderliches Approval Level
        """
        approval_levels = {
            "quality_manual": 4,  # QM-Manager
            "procedures": 3,      # Abteilungsleiter
            "work_instructions": 3,  # Abteilungsleiter
            "forms": 2,           # Teamleiter
            "templates": 2,       # Teamleiter
            "records": 1          # Standard
        }
        
        return approval_levels.get(document_type, 1)


class MembershipPolicy:
    """Membership Policy - Group-Membership-Business-Rules"""
    
    @staticmethod
    def can_join_group(user: User, group_code: str) -> bool:
        """
        Prüft ob User einer Gruppe beitreten kann
        
        Args:
            user: User Entity
            group_code: Group Code
            
        Returns:
            bool: True wenn Beitritt erlaubt
        """
        if not user.is_active:
            return False
        
        # Externe Gruppen haben spezielle Regeln
        if group_code == "external_auditors":
            return user.organizational_unit == "External"
        
        # Interne Gruppen: Standard-Regeln
        return True
    
    @staticmethod
    def get_max_approval_level_in_group(user: User, group_code: str) -> int:
        """
        Gibt das maximale Approval Level zurück, das User in einer Gruppe haben kann
        
        Args:
            user: User Entity
            group_code: Group Code
            
        Returns:
            int: Maximales Approval Level
        """
        if not user.is_active:
            return 1
        
        # QM-Gruppe: Höhere Levels möglich
        if group_code == "quality_management":
            return min(user.approval_level, 4)
        
        # Standard-Gruppen: Begrenzte Levels
        return min(user.approval_level, 3)
