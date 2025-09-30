"""
Domain Events für Users Context

Events dokumentieren wichtige Zustandsänderungen im Benutzer- und RBAC-Modell.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class DomainEvent(ABC):
    """Basis-Klasse für Domain-Events"""

    @abstractmethod
    def occurred_on(self) -> datetime:
        ...

    @abstractmethod
    def event_name(self) -> str:
        ...

    def to_dict(self) -> Dict[str, Any]:  # pragma: no cover - Default serialisierung
        return {
            "event": self.event_name(),
            "occurred_on": self.occurred_on().isoformat(),
        }


@dataclass
class UserCreated(DomainEvent):
    user_id: int
    email: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    def occurred_on(self) -> datetime:
        return self.occurred_at

    def event_name(self) -> str:
        return "user.created"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "user_id": self.user_id,
            "email": self.email,
        })
        return base


@dataclass
class UserUpdated(DomainEvent):
    user_id: int
    changes: Dict[str, Any]
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    def occurred_on(self) -> datetime:
        return self.occurred_at

    def event_name(self) -> str:
        return "user.updated"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "user_id": self.user_id,
            "changes": self.changes,
        })
        return base


@dataclass
class UserDeactivated(DomainEvent):
    user_id: int
    reason: Optional[str] = None
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    def occurred_on(self) -> datetime:
        return self.occurred_at

    def event_name(self) -> str:
        return "user.deactivated"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "user_id": self.user_id,
            "reason": self.reason,
        })
        return base


@dataclass
class UserReactivated(DomainEvent):
    user_id: int
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    def occurred_on(self) -> datetime:
        return self.occurred_at

    def event_name(self) -> str:
        return "user.reactivated"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"user_id": self.user_id})
        return base


@dataclass
class RoleAssigned(DomainEvent):
    user_id: int
    role_name: str
    assigned_by: Optional[int] = None
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    def occurred_on(self) -> datetime:
        return self.occurred_at

    def event_name(self) -> str:
        return "user.role_assigned"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "user_id": self.user_id,
            "role_name": self.role_name,
            "assigned_by": self.assigned_by,
        })
        return base


@dataclass
class RoleRevoked(DomainEvent):
    user_id: int
    role_name: str
    revoked_by: Optional[int] = None
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    def occurred_on(self) -> datetime:
        return self.occurred_at

    def event_name(self) -> str:
        return "user.role_revoked"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "user_id": self.user_id,
            "role_name": self.role_name,
            "revoked_by": self.revoked_by,
        })
        return base


@dataclass
class MembershipAdded(DomainEvent):
    user_id: int
    interest_group_id: int
    membership_id: Optional[int] = None
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    def occurred_on(self) -> datetime:
        return self.occurred_at

    def event_name(self) -> str:
        return "user.membership_added"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "user_id": self.user_id,
            "interest_group_id": self.interest_group_id,
            "membership_id": self.membership_id,
        })
        return base


@dataclass
class MembershipRemoved(DomainEvent):
    user_id: int
    interest_group_id: int
    membership_id: Optional[int] = None
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    def occurred_on(self) -> datetime:
        return self.occurred_at

    def event_name(self) -> str:
        return "user.membership_removed"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "user_id": self.user_id,
            "interest_group_id": self.interest_group_id,
            "membership_id": self.membership_id,
        })
        return base


@dataclass
class PermissionGranted(DomainEvent):
    user_id: int
    permission_code: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    def occurred_on(self) -> datetime:
        return self.occurred_at

    def event_name(self) -> str:
        return "user.permission_granted"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "user_id": self.user_id,
            "permission_code": self.permission_code,
        })
        return base


@dataclass
class PermissionRevoked(DomainEvent):
    user_id: int
    permission_code: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    def occurred_on(self) -> datetime:
        return self.occurred_at

    def event_name(self) -> str:
        return "user.permission_revoked"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "user_id": self.user_id,
            "permission_code": self.permission_code,
        })
        return base




