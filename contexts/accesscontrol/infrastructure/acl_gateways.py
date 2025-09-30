"""
AccessControl Anti-Corruption Layer Gateways

Legacy-Integration ohne Legacy-Code-Änderungen
"""

import sqlite3
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from ..application.ports import (
    LegacyUserGateway, LegacyMembershipGateway, LegacyPermissionGateway
)


class LegacyUserACLGateway:
    """Anti-Corruption Layer für Legacy User-System"""
    
    def __init__(self, database_url: str):
        """
        Initialisiert ACL Gateway mit Legacy-DB
        
        Args:
            database_url: SQLite/PostgreSQL URL zur Legacy-DB
        """
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """User aus Legacy-System abrufen"""
        with self.SessionLocal() as session:
            result = session.execute(
                text("SELECT * FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            ).fetchone()
            
            if result:
                return dict(result._mapping)
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """User by Email aus Legacy-System abrufen"""
        with self.SessionLocal() as session:
            result = session.execute(
                text("SELECT * FROM users WHERE email = :email"),
                {"email": email}
            ).fetchone()
            
            if result:
                return dict(result._mapping)
            return None
    
    def list_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """User-Liste aus Legacy-System abrufen"""
        with self.SessionLocal() as session:
            results = session.execute(
                text("SELECT * FROM users ORDER BY created_at DESC LIMIT :limit OFFSET :skip"),
                {"limit": limit, "skip": skip}
            ).fetchall()
            
            return [dict(row._mapping) for row in results]


class LegacyMembershipACLGateway:
    """Anti-Corruption Layer für Legacy Membership-System"""
    
    def __init__(self, database_url: str):
        """
        Initialisiert ACL Gateway mit Legacy-DB
        
        Args:
            database_url: SQLite/PostgreSQL URL zur Legacy-DB
        """
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_memberships_for_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Memberships aus Legacy-System abrufen"""
        with self.SessionLocal() as session:
            results = session.execute(
                text("""
                    SELECT ugm.*, ig.name as group_name, ig.code as group_code
                    FROM user_group_memberships ugm
                    JOIN interest_groups ig ON ugm.interest_group_id = ig.id
                    WHERE ugm.user_id = :user_id AND ugm.is_active = 1
                """),
                {"user_id": user_id}
            ).fetchall()
            
            return [dict(row._mapping) for row in results]
    
    def get_memberships_for_group(self, group_id: int) -> List[Dict[str, Any]]:
        """Memberships für Group aus Legacy-System abrufen"""
        with self.SessionLocal() as session:
            results = session.execute(
                text("""
                    SELECT ugm.*, u.email, u.full_name
                    FROM user_group_memberships ugm
                    JOIN users u ON ugm.user_id = u.id
                    WHERE ugm.interest_group_id = :group_id AND ugm.is_active = 1
                """),
                {"group_id": group_id}
            ).fetchall()
            
            return [dict(row._mapping) for row in results]
    
    def create_membership(self, membership_data: Dict[str, Any]) -> Dict[str, Any]:
        """Membership in Legacy-System erstellen"""
        with self.SessionLocal() as session:
            # Insert membership
            result = session.execute(
                text("""
                    INSERT INTO user_group_memberships 
                    (user_id, interest_group_id, role_in_group, approval_level, 
                     is_department_head, is_active, assigned_by_id, notes)
                    VALUES (:user_id, :interest_group_id, :role_in_group, :approval_level,
                            :is_department_head, :is_active, :assigned_by_id, :notes)
                """),
                membership_data
            )
            session.commit()
            
            # Return created membership
            created_id = result.lastrowid
            return self.get_membership_by_id(created_id)
    
    def get_membership_by_id(self, membership_id: int) -> Optional[Dict[str, Any]]:
        """Membership by ID abrufen"""
        with self.SessionLocal() as session:
            result = session.execute(
                text("SELECT * FROM user_group_memberships WHERE id = :id"),
                {"id": membership_id}
            ).fetchone()
            
            if result:
                return dict(result._mapping)
            return None


class LegacyPermissionACLGateway:
    """Anti-Corruption Layer für Legacy Permission-System"""
    
    def __init__(self, database_url: str):
        """
        Initialisiert ACL Gateway mit Legacy-DB
        
        Args:
            database_url: SQLite/PostgreSQL URL zur Legacy-DB
        """
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """User-Permissions aus Legacy-System abrufen"""
        with self.SessionLocal() as session:
            # Individuelle Permissions
            individual_result = session.execute(
                text("SELECT individual_permissions FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            ).fetchone()
            
            permissions = set()
            
            # Individuelle Permissions parsen
            if individual_result and individual_result[0]:
                import json
                try:
                    individual_perms = json.loads(individual_result[0])
                    if isinstance(individual_perms, list):
                        permissions.update(individual_perms)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Group-Permissions
            group_results = session.execute(
                text("""
                    SELECT ig.group_permissions
                    FROM user_group_memberships ugm
                    JOIN interest_groups ig ON ugm.interest_group_id = ig.id
                    WHERE ugm.user_id = :user_id AND ugm.is_active = 1 AND ig.is_active = 1
                """),
                {"user_id": user_id}
            ).fetchall()
            
            for row in group_results:
                if row[0]:
                    import json
                    try:
                        group_perms = json.loads(row[0])
                        if isinstance(group_perms, list):
                            permissions.update(group_perms)
                    except (json.JSONDecodeError, TypeError):
                        pass
            
            return list(permissions)
    
    def get_group_permissions(self, group_id: int) -> List[str]:
        """Group-Permissions aus Legacy-System abrufen"""
        with self.SessionLocal() as session:
            result = session.execute(
                text("SELECT group_permissions FROM interest_groups WHERE id = :group_id"),
                {"group_id": group_id}
            ).fetchone()
            
            if result and result[0]:
                import json
                try:
                    permissions = json.loads(result[0])
                    if isinstance(permissions, list):
                        return permissions
                except (json.JSONDecodeError, TypeError):
                    pass
            
            return []
    
    def check_user_access(self, user_id: int, permission_code: str) -> bool:
        """Access-Check im Legacy-System"""
        user_permissions = self.get_user_permissions(user_id)
        return permission_code in user_permissions
    
    def get_user_approval_level(self, user_id: int) -> int:
        """User Approval Level aus Legacy-System abrufen"""
        with self.SessionLocal() as session:
            result = session.execute(
                text("SELECT approval_level FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            ).fetchone()
            
            if result:
                return result[0] or 1
            return 1
    
    def is_user_department_head(self, user_id: int) -> bool:
        """Prüfen ob User Department Head ist"""
        with self.SessionLocal() as session:
            result = session.execute(
                text("SELECT is_department_head FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            ).fetchone()
            
            if result:
                return bool(result[0])
            return False


# Factory für ACL Gateways

class ACLGatewayFactory:
    """Factory für ACL Gateways"""
    
    @staticmethod
    def create_user_gateway(database_url: str) -> LegacyUserGateway:
        """User Gateway erstellen"""
        return LegacyUserACLGateway(database_url)
    
    @staticmethod
    def create_membership_gateway(database_url: str) -> LegacyMembershipGateway:
        """Membership Gateway erstellen"""
        return LegacyMembershipACLGateway(database_url)
    
    @staticmethod
    def create_permission_gateway(database_url: str) -> LegacyPermissionGateway:
        """Permission Gateway erstellen"""
        return LegacyPermissionACLGateway(database_url)

