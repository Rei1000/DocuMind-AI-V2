"""
Value Objects für Interest Groups Domain
Unveränderliche Objekte mit Business-Validierung
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Union
import json


@dataclass(frozen=True)
class GroupCode:
    """
    Interest Group Code - muss snake_case sein, 2-50 Zeichen
    """
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Group code cannot be empty")
            
        if not re.match(r'^[a-z0-9_]{2,50}$', self.value):
            raise ValueError(
                f"Group code must be snake_case, 2-50 characters. Got: '{self.value}'"
            )
    
    def __str__(self):
        return self.value


@dataclass(frozen=True)
class GroupName:
    """
    Interest Group Name - 2-100 Zeichen
    """
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Group name cannot be empty")
            
        if not 2 <= len(self.value) <= 100:
            raise ValueError(
                f"Group name must be 2-100 characters. Got: {len(self.value)} characters"
            )
    
    def __str__(self):
        return self.value


@dataclass(frozen=True)
class GroupDescription:
    """
    Interest Group Beschreibung - optional, max 500 Zeichen
    """
    value: Optional[str] = None
    
    def __post_init__(self):
        if self.value and len(self.value) > 500:
            raise ValueError(
                f"Description must be max 500 characters. Got: {len(self.value)}"
            )
    
    def __str__(self):
        return self.value or ""


@dataclass(frozen=True)
class GroupPermission:
    """
    Eine einzelne Permission für eine Interest Group
    """
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Permission cannot be empty")
    
    def __str__(self):
        return self.value


class GroupPermissions:
    """
    Sammlung von Permissions für eine Interest Group
    Unterstützt verschiedene Input-Formate (Legacy-Kompatibilität)
    """
    
    def __init__(self, permissions: Union[List[str], str, dict, None] = None):
        self._permissions: List[GroupPermission] = []
        
        if permissions is None or permissions == "":
            # Leere Permissions sind erlaubt
            return
            
        if isinstance(permissions, list):
            # Liste von Strings
            for perm in permissions:
                if perm and isinstance(perm, str):
                    self._permissions.append(GroupPermission(perm.strip()))
                    
        elif isinstance(permissions, str):
            # JSON-String oder Komma-separiert
            try:
                # Versuche als JSON zu parsen
                parsed = json.loads(permissions)
                if isinstance(parsed, list):
                    for perm in parsed:
                        if perm and isinstance(perm, str):
                            self._permissions.append(GroupPermission(perm.strip()))
            except json.JSONDecodeError:
                # Fallback: Komma-separiert
                for perm in permissions.split(','):
                    cleaned = perm.strip()
                    if cleaned:
                        self._permissions.append(GroupPermission(cleaned))
                        
        elif isinstance(permissions, dict):
            # Dict-Format (Legacy)
            # Konvertiere Keys oder Values zu Permissions
            for key, value in permissions.items():
                if key and isinstance(key, str):
                    self._permissions.append(GroupPermission(key))
    
    def to_list(self) -> List[str]:
        """Gibt Permissions als Liste von Strings zurück"""
        return [str(perm) for perm in self._permissions]
    
    def to_json_string(self) -> str:
        """Serialisiert Permissions als JSON-String für DB-Storage"""
        return json.dumps(self.to_list(), ensure_ascii=False)
    
    def has_permission(self, permission: str) -> bool:
        """Prüft ob eine bestimmte Permission vorhanden ist"""
        return permission in self.to_list()
    
    def add(self, permission: str):
        """Fügt eine neue Permission hinzu"""
        if permission and permission not in self.to_list():
            self._permissions.append(GroupPermission(permission))
    
    def remove(self, permission: str):
        """Entfernt eine Permission"""
        self._permissions = [p for p in self._permissions if str(p) != permission]
    
    def __len__(self):
        return len(self._permissions)
    
    def __iter__(self):
        return iter(self.to_list())
    
    def __str__(self):
        return f"GroupPermissions({self.to_list()})"


# Tolerante Versionen für Legacy-Daten
@dataclass(frozen=True)
class LenientGroupCode:
    """
    Tolerante Version von GroupCode für Legacy-Daten
    Gibt Warnung statt Fehler bei ungültigen Codes
    """
    value: str
    
    def __post_init__(self):
        if not self.value:
            # Leerer Code wird zu "unknown" 
            object.__setattr__(self, 'value', 'unknown')
            
        # Prüfe Format, aber nur warnen
        if not re.match(r'^[a-z0-9_]{2,50}$', self.value):
            import warnings
            warnings.warn(
                f"Legacy group code '{self.value}' does not match snake_case pattern. "
                f"Consider updating to valid format.",
                UserWarning
            )
    
    def __str__(self):
        return self.value


@dataclass(frozen=True) 
class LenientGroupName:
    """
    Tolerante Version von GroupName für Legacy-Daten
    """
    value: str
    
    def __post_init__(self):
        if not self.value:
            object.__setattr__(self, 'value', 'Unnamed Group')
            
        # Nur warnen bei ungültiger Länge
        if not 2 <= len(self.value) <= 100:
            import warnings
            warnings.warn(
                f"Legacy group name has {len(self.value)} characters "
                f"(should be 2-100).",
                UserWarning
            )
    
    def __str__(self):
        return self.value
