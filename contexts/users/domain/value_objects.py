"""
Value Objects für Users Domain

Stellt geprüfte, unveränderliche Typen für Benutzer- und RBAC-Attribute bereit.

Hinweis: Legacy-kompatible Varianten (Lenient*) ermöglichen sanften Übergang,
ohne bestehende Daten sofort korrigieren zu müssen.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class UserId:
    """Eindeutige Benutzer-ID"""

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or self.value < 0:
            raise ValueError("UserId must be a non-negative integer")

    def __int__(self) -> int:  # pragma: no cover - convenience helper
        return self.value


@dataclass(frozen=True)
class EmailAddress:
    """Validierte E-Mail-Adresse"""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not EMAIL_REGEX.match(self.value):
            raise ValueError(f"Invalid email address: {self.value}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class LenientEmailAddress:
    """Legacy-kompatible E-Mail: erlaubt ungültige Werte, warnt aber"""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            object.__setattr__(self, "value", "unknown@example.com")
        if not EMAIL_REGEX.match(self.value):
            import warnings

            warnings.warn(
                f"Legacy email '{self.value}' is not RFC-compliant. Consider cleaning data.",
                UserWarning,
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class FullName:
    """Vollständiger Name eines Benutzers"""

    value: str

    def __post_init__(self) -> None:
        if not self.value or len(self.value.strip()) < 2:
            raise ValueError("Full name must contain at least 2 characters")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class LenientFullName:
    """Legacy-kompatibler Name"""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            object.__setattr__(self, "value", "Unnamed User")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class EmployeeId:
    """Mitarbeiter-ID (optional)"""

    value: Optional[str] = None

    def __post_init__(self) -> None:
        if self.value is None:
            return
        if not re.match(r"^[A-Za-z0-9\-_]{2,32}$", self.value):
            raise ValueError("EmployeeId must be 2-32 characters, alphanumeric/_-")

    def __str__(self) -> str:
        return self.value or ""


@dataclass(frozen=True)
class OrganizationalUnit:
    """Organisations-Einheit eines Benutzers"""

    value: Optional[str] = None

    def __post_init__(self) -> None:
        if self.value is None:
            return
        if len(self.value.strip()) < 2:
            raise ValueError("Organizational unit must have at least 2 characters")

    def __str__(self) -> str:
        return self.value or ""


@dataclass(frozen=True)
class ApprovalLevel:
    """Freigabe-Level (1-10)"""

    value: int = 1

    def __post_init__(self) -> None:
        if not 1 <= self.value <= 10:
            raise ValueError("Approval level must be between 1 and 10")

    def __int__(self) -> int:  # pragma: no cover - convenience helper
        return self.value


@dataclass(frozen=True)
class RoleName:
    """Name einer Rolle"""

    value: str

    def __post_init__(self) -> None:
        if not re.match(r"^[a-z0-9_]{2,50}$", self.value):
            raise ValueError("Role name must be snake_case, 2-50 chars")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PermissionCode:
    """Permission-Code (snake_case)"""

    value: str

    def __post_init__(self) -> None:
        if not re.match(r"^[a-z0-9:_\-]{2,100}$", self.value):
            raise ValueError("Permission code must be 2-100 chars, allowed _: - :")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class MembershipRole:
    """Rolle innerhalb einer Interessengruppe"""

    value: Optional[str] = None

    def __post_init__(self) -> None:
        if self.value is None:
            return
        cleaned = self.value.strip()
        if cleaned and len(cleaned) < 2:
            raise ValueError("Membership role must be at least 2 characters if provided")
        object.__setattr__(self, "value", cleaned or None)

    def __str__(self) -> str:
        return self.value or ""


@dataclass(frozen=True)
class InterestGroupId:
    """ID einer Interessengruppe"""

    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError("InterestGroupId must be positive")

    def __int__(self) -> int:  # pragma: no cover - convenience helper
        return self.value


@dataclass(frozen=True)
class InterestGroupCode:
    """Code einer Interessengruppe (snake_case)"""

    value: Optional[str] = None

    def __post_init__(self) -> None:
        if self.value is None:
            return
        if not re.match(r"^[a-z0-9_]{2,50}$", self.value):
            raise ValueError("Interest group code must be snake_case, 2-50 chars")

    def __str__(self) -> str:
        return self.value or ""




