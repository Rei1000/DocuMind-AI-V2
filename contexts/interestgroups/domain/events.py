"""
Domain Events für Interest Groups
Events die bei wichtigen Geschäftsereignissen ausgelöst werden
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class DomainEvent(ABC):
    """
    Basis-Klasse für alle Domain Events
    """
    
    @abstractmethod
    def occurred_on(self) -> datetime:
        """Zeitpunkt wann das Event aufgetreten ist"""
        pass
    
    @abstractmethod
    def event_name(self) -> str:
        """Name des Events für Logging/Monitoring"""
        pass


@dataclass
class InterestGroupCreated(DomainEvent):
    """
    Event wenn eine neue Interest Group erstellt wurde
    """
    group_id: Optional[int]
    name: str
    code: str
    is_external: bool
    timestamp: datetime = field(default_factory=datetime.now)
    
    def occurred_on(self) -> datetime:
        return self.timestamp
    
    def event_name(self) -> str:
        return "interest_group.created"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event': self.event_name(),
            'group_id': self.group_id,
            'name': self.name,
            'code': self.code,
            'is_external': self.is_external,
            'occurred_on': self.timestamp.isoformat()
        }


@dataclass
class InterestGroupUpdated(DomainEvent):
    """
    Event wenn eine Interest Group aktualisiert wurde
    """
    group_id: int
    changes: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def occurred_on(self) -> datetime:
        return self.timestamp
    
    def event_name(self) -> str:
        return "interest_group.updated"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event': self.event_name(),
            'group_id': self.group_id,
            'changes': self.changes,
            'occurred_on': self.timestamp.isoformat()
        }


@dataclass
class InterestGroupDeactivated(DomainEvent):
    """
    Event wenn eine Interest Group deaktiviert wurde (Soft Delete)
    """
    group_id: int
    name: str
    code: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def occurred_on(self) -> datetime:
        return self.timestamp
    
    def event_name(self) -> str:
        return "interest_group.deactivated"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event': self.event_name(),
            'group_id': self.group_id,
            'name': self.name,
            'code': self.code,
            'occurred_on': self.timestamp.isoformat()
        }


@dataclass
class InterestGroupReactivated(DomainEvent):
    """
    Event wenn eine deaktivierte Interest Group reaktiviert wurde
    """
    group_id: int
    name: str
    code: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def occurred_on(self) -> datetime:
        return self.timestamp
    
    def event_name(self) -> str:
        return "interest_group.reactivated"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event': self.event_name(),
            'group_id': self.group_id,
            'name': self.name,
            'code': self.code,
            'occurred_on': self.timestamp.isoformat()
        }


@dataclass
class InterestGroupPermissionsChanged(DomainEvent):
    """
    Event wenn Permissions einer Interest Group geändert wurden
    """
    group_id: int
    old_permissions: list
    new_permissions: list
    timestamp: datetime = field(default_factory=datetime.now)
    
    def occurred_on(self) -> datetime:
        return self.timestamp
    
    def event_name(self) -> str:
        return "interest_group.permissions_changed"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event': self.event_name(),
            'group_id': self.group_id,
            'old_permissions': self.old_permissions,
            'new_permissions': self.new_permissions,
            'occurred_on': self.timestamp.isoformat()
        }
