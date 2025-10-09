"""
Domain Entities für Interest Groups
Aggregat-Root mit Business-Logik und Domain Events
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from .value_objects import (
    GroupCode, GroupName, GroupDescription, GroupPermissions,
    LenientGroupCode, LenientGroupName
)
from typing import Union
from .events import (
    InterestGroupCreated,
    InterestGroupUpdated,
    InterestGroupDeactivated,
    InterestGroupReactivated
)


@dataclass
class InterestGroup:
    """
    Interest Group Aggregat-Root
    Repräsentiert eine Interessengruppe/Stakeholder im QMS
    """
    
    # Identity
    id: Optional[int] = None
    
    # Attributes
    name: Union[GroupName, LenientGroupName] = None
    code: Union[GroupCode, LenientGroupCode] = None
    description: GroupDescription = field(default_factory=lambda: GroupDescription())
    permissions: GroupPermissions = field(default_factory=GroupPermissions)
    
    # QMS-spezifische Felder
    ai_functionality: Optional[str] = None
    typical_tasks: Optional[str] = None
    
    # Status
    is_external: bool = False
    is_active: bool = True
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Domain Events
    _events: List = field(default_factory=list)
    
    def __post_init__(self):
        """Validierung nach Initialisierung"""
        if not self.name:
            raise ValueError("Interest Group must have a name")
        if not self.code:
            raise ValueError("Interest Group must have a code")
    
    @classmethod
    def create(
        cls,
        name: str,
        code: str,
        description: Optional[str] = None,
        permissions: Optional[any] = None,
        ai_functionality: Optional[str] = None,
        typical_tasks: Optional[str] = None,
        is_external: bool = False
    ) -> 'InterestGroup':
        """
        Factory-Methode zum Erstellen einer neuen Interest Group
        """
        group = cls(
            name=GroupName(name),
            code=GroupCode(code),
            description=GroupDescription(description),
            permissions=GroupPermissions(permissions),
            ai_functionality=ai_functionality,
            typical_tasks=typical_tasks,
            is_external=is_external,
            is_active=True
        )
        
        # Domain Event auslösen
        group._events.append(InterestGroupCreated(
            group_id=None,  # ID wird erst nach DB-Save gesetzt
            name=name,
            code=code,
            is_external=is_external
        ))
        
        return group
    
    def update(
        self,
        name: Optional[str] = None,
        code: Optional[str] = None,
        description: Optional[str] = None,
        permissions: Optional[any] = None,
        ai_functionality: Optional[str] = None,
        typical_tasks: Optional[str] = None,
        is_external: Optional[bool] = None,
        is_active: Optional[bool] = None
    ):
        """
        Aktualisiert die Interest Group mit neuen Werten
        """
        changes = {}
        
        if name is not None and str(self.name) != name:
            self.name = GroupName(name)
            changes['name'] = name
            
        if code is not None and str(self.code) != code:
            self.code = GroupCode(code)
            changes['code'] = code
            
        if description is not None:
            self.description = GroupDescription(description)
            changes['description'] = description
            
        if permissions is not None:
            self.permissions = GroupPermissions(permissions)
            changes['permissions'] = self.permissions.to_list()
            
        if ai_functionality is not None:
            self.ai_functionality = ai_functionality
            changes['ai_functionality'] = ai_functionality
            
        if typical_tasks is not None:
            self.typical_tasks = typical_tasks
            changes['typical_tasks'] = typical_tasks
            
        if is_external is not None:
            self.is_external = is_external
            changes['is_external'] = is_external
            
        if is_active is not None and self.is_active != is_active:
            self.is_active = is_active
            changes['is_active'] = is_active
        
        if changes:
            self._events.append(InterestGroupUpdated(
                group_id=self.id,
                changes=changes
            ))
    
    def deactivate(self):
        """
        Deaktiviert die Interest Group (Soft Delete)
        """
        if not self.is_active:
            raise ValueError("Interest Group is already inactive")
            
        self.is_active = False
        self._events.append(InterestGroupDeactivated(
            group_id=self.id,
            name=str(self.name),
            code=str(self.code)
        ))
    
    def reactivate(self):
        """
        Reaktiviert eine deaktivierte Interest Group
        """
        if self.is_active:
            raise ValueError("Interest Group is already active")
            
        self.is_active = True
        self._events.append(InterestGroupReactivated(
            group_id=self.id,
            name=str(self.name),
            code=str(self.code)
        ))
    
    def add_permission(self, permission: str):
        """
        Fügt eine neue Permission hinzu
        """
        old_permissions = self.permissions.to_list()
        self.permissions.add(permission)
        
        if self.permissions.to_list() != old_permissions:
            self._events.append(InterestGroupUpdated(
                group_id=self.id,
                changes={'permissions': self.permissions.to_list()}
            ))
    
    def remove_permission(self, permission: str):
        """
        Entfernt eine Permission
        """
        old_permissions = self.permissions.to_list()
        self.permissions.remove(permission)
        
        if self.permissions.to_list() != old_permissions:
            self._events.append(InterestGroupUpdated(
                group_id=self.id,
                changes={'permissions': self.permissions.to_list()}
            ))
    
    def has_permission(self, permission: str) -> bool:
        """
        Prüft ob die Group eine bestimmte Permission hat
        """
        return self.permissions.has_permission(permission)
    
    def pull_domain_events(self) -> List:
        """
        Gibt alle Domain Events zurück und leert den Event-Buffer
        """
        events = self._events.copy()
        self._events.clear()
        return events
    
    def to_dict(self) -> dict:
        """
        Konvertiert Entity zu Dictionary für Serialisierung
        """
        return {
            'id': self.id,
            'name': str(self.name),
            'code': str(self.code),
            'description': str(self.description),
            'group_permissions': self.permissions.to_list(),
            'ai_functionality': self.ai_functionality,
            'typical_tasks': self.typical_tasks,
            'is_external': self.is_external,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __str__(self):
        return f"InterestGroup(id={self.id}, name='{self.name}', code='{self.code}', active={self.is_active})"
