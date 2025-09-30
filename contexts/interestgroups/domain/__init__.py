"""
Interest Groups Domain Layer
Enthält Entities, Value Objects, Events und Repository Interfaces
"""

# Entities
from .entities import InterestGroup

# Value Objects
from .value_objects import (
    GroupCode,
    GroupName,
    GroupDescription,
    GroupPermission,
    GroupPermissions
)

# Events
from .events import (
    DomainEvent,
    InterestGroupCreated,
    InterestGroupUpdated,
    InterestGroupDeactivated,
    InterestGroupReactivated,
    InterestGroupPermissionsChanged
)

# Repository Interface
from .repositories import InterestGroupRepository

__all__ = [
    # Entities
    'InterestGroup',
    
    # Value Objects
    'GroupCode',
    'GroupName',
    'GroupDescription',
    'GroupPermission',
    'GroupPermissions',
    
    # Events
    'DomainEvent',
    'InterestGroupCreated',
    'InterestGroupUpdated',
    'InterestGroupDeactivated',
    'InterestGroupReactivated',
    'InterestGroupPermissionsChanged',
    
    # Repository
    'InterestGroupRepository'
]
