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
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="Erstellt von (QMS Admin)")
    
    # Relationships
    user_memberships = relationship("UserGroupMembership", back_populates="interest_group")
    created_by = relationship("User", foreign_keys=[created_by_id], post_update=True)
    
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
    - QMS Admin (Level 5) - Spezielle System-Admin-Rechte
    
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
    
    # Berechtigungen (Level 1-4 nur in UserGroupMembership, Level 5 = QMS Admin hier)
    individual_permissions = Column(Text, comment="JSON-String mit individuellen Berechtigungen")
    is_qms_admin = Column(Boolean, default=False, nullable=False, comment="Level 5 - System Admin (User-Management, Group-Management)")
    cannot_be_deleted = Column(Boolean, default=False, nullable=False, comment="Schutz für QMS Admin")
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    group_memberships = relationship("UserGroupMembership", back_populates="user", foreign_keys="UserGroupMembership.user_id")


class UserGroupMembership(Base):
    """
    Many-to-Many Zuordnung User ↔ InterestGroup.
    
    Ermöglicht Multiple Abteilungen pro User mit individuellen Levels (1-4):
    
    Beispiel:
        User: reiner@company.com
        ├── QM-Abteilung (Level 4 - QM-Manager) 
        ├── Service (Level 3 - Abteilungsleiter)
        └── IT (Level 1 - Mitarbeiter)
    
    Permission Levels:
    - Level 1: Mitarbeiter (Lesen, Vorschlagen)
    - Level 2: Teamleiter (Team-Freigabe)
    - Level 3: Abteilungsleiter (Abteilungs-Freigabe)
    - Level 4: QM-Manager (QM-Freigabe in dieser Group)
    - Level 5: Nur QMS Admin (User.is_qms_admin)
    
    Features:
    - Verschiedene Approval-Levels je Gruppe (1-4)
    - Unique Constraint: Ein User kann nur 1x pro Gruppe sein
    - Audit-Trail via joined_at/assigned_by
    - Soft-Delete via is_active
    """
    __tablename__ = "user_group_memberships"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    interest_group_id = Column(Integer, ForeignKey("interest_groups.id"), nullable=False, index=True)
    
    # Rollen & Berechtigungen (1-4, nicht 5!)
    role_in_group = Column(String(50), comment="z.B. 'Teamleiter', 'Fachexperte'")
    approval_level = Column(Integer, default=1, nullable=False, comment="1=Mitarbeiter, 2=Teamleiter, 3=Abteilungsleiter, 4=QM-Manager")
    is_department_head = Column(Boolean, default=False, nullable=False)
    
    # Audit
    is_active = Column(Boolean, default=True, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, comment="Bemerkungen zur Zuordnung")
    
    # Relationships
    user = relationship("User", back_populates="group_memberships", foreign_keys=[user_id])
    interest_group = relationship("InterestGroup", back_populates="user_memberships")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id], post_update=True)
    
    def __repr__(self):
        return f"<UserGroupMembership(user_id={self.user_id}, group_id={self.interest_group_id}, level={self.approval_level})>"
