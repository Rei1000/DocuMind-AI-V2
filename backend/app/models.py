"""
📊 DocuMind-AI V2 Data Models (SQLAlchemy ORM)

Minimales DDD-orientiertes Datenmodell fokussiert auf:
- User Management (RBAC)
- Interest Groups (13 Stakeholder-System)
- User Group Memberships (Many-to-Many)

Version: 2.0.0 (Clean DDD Architecture)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# === KERN-MODELLE: USER & INTEREST GROUPS ===

class InterestGroup(Base):
    """
    Interessensgruppen-Modell für das 13-Stakeholder-System.
    
    Repräsentiert organisatorische Einheiten von internen Teams
    (Einkauf, QM, Entwicklung) bis zu externen Stakeholdern.
    
    Features:
    - Granulare Berechtigungssteuerung über group_permissions
    - Unterscheidung zwischen internen/externen Gruppen
    - Soft-Delete über is_active
    
    Relationships:
    - users: Many-to-Many über UserGroupMembership
    """
    __tablename__ = "interest_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    group_permissions = Column(Text, comment="JSON-String mit Gruppen-Berechtigungen")
    ai_functionality = Column(Text, comment="Verfügbare KI-Funktionen")
    typical_tasks = Column(Text, comment="Typische Aufgaben")
    is_external = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user_memberships = relationship("UserGroupMembership", back_populates="interest_group")
    
    def get_group_permissions_list(self):
        """Gruppen-Permissions als Python-Liste"""
        try:
            import json
            if self.group_permissions:
                return json.loads(self.group_permissions)
            return []
        except (json.JSONDecodeError, TypeError, AttributeError):
            return []


class User(Base):
    """
    Benutzer-Modell für Authentifizierung und RBAC.
    
    Features:
    - Verschlüsselte Passwort-Speicherung (bcrypt)
    - Eindeutige Email/Employee-ID
    - Soft-Delete für Audit-Trail
    - Multi-Department Support via UserGroupMembership
    
    Relationships:
    - interest_groups: Many-to-Many über UserGroupMembership
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(200), nullable=False)
    employee_id = Column(String(50), unique=True)
    organizational_unit = Column(String(100), comment="Primäre Organisationseinheit")
    hashed_password = Column(String(255))
    
    # Berechtigungen
    individual_permissions = Column(Text, comment="JSON-String mit individuellen Berechtigungen")
    is_department_head = Column(Boolean, default=False, nullable=False)
    approval_level = Column(Integer, default=1, comment="1=Standard, 2=Teamleiter, 3=Abteilungsleiter, 4=QM-Manager, 5=System-Admin")
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    group_memberships = relationship("UserGroupMembership", back_populates="user", foreign_keys="UserGroupMembership.user_id")


class UserGroupMembership(Base):
    """
    Many-to-Many Zuordnung User ↔ InterestGroup.
    
    Ermöglicht Multiple Abteilungen pro User mit individuellen Levels:
    
    Beispiel:
        User: reiner@company.com
        ├── QM-Abteilung (Level 2 - Teamleiter) 
        ├── Service (Level 3 - Abteilungsleiter)
        └── Entwicklung (Level 1 - Mitarbeiter)
    
    Features:
    - Verschiedene Approval-Levels je Gruppe
    - Audit-Trail via joined_at/assigned_by
    - Soft-Delete via is_active
    """
    __tablename__ = "user_group_memberships"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    interest_group_id = Column(Integer, ForeignKey("interest_groups.id"), nullable=False, index=True)
    
    # Rollen & Berechtigungen
    role_in_group = Column(String(50), comment="z.B. 'Teamleiter', 'Fachexperte'")
    approval_level = Column(Integer, default=1, nullable=False, comment="1=Mitarbeiter, 2=Teamleiter, 3=Abteilungsleiter, 4=QM-Manager")
    is_department_head = Column(Boolean, default=False, nullable=False)
    
    # Audit
    is_active = Column(Boolean, default=True, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, comment="Bemerkungen zur Zuordnung")
    
    # Relationships
    user = relationship("User", back_populates="group_memberships", foreign_keys=[user_id])
    interest_group = relationship("InterestGroup", back_populates="user_memberships")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id], post_update=True)
    
    def __repr__(self):
        return f"<UserGroupMembership(user_id={self.user_id}, group_id={self.interest_group_id}, level={self.approval_level})>"
