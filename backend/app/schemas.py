"""
📋 DocuMind-AI V2 Pydantic Schemas

Request/Response-Validierung für:
- Interest Groups
- Users (RBAC)
- User Group Memberships

Version: 2.0.0 (Clean DDD Architecture)
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional, List, Union, Dict, Any
from datetime import datetime
import json

# === INTEREST GROUP SCHEMAS ===

class InterestGroupBase(BaseModel):
    """Basis-Schema für Interest Groups."""
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    group_permissions: Optional[str] = None
    ai_functionality: Optional[str] = None
    typical_tasks: Optional[str] = None
    is_external: bool = False


class InterestGroupCreate(InterestGroupBase):
    """Schema für Erstellung neuer Interest Groups."""
    pass


class InterestGroupUpdate(BaseModel):
    """Schema für Updates von Interest Groups."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None
    group_permissions: Optional[str] = None
    ai_functionality: Optional[str] = None
    typical_tasks: Optional[str] = None
    is_external: Optional[bool] = None
    is_active: Optional[bool] = None


class InterestGroup(InterestGroupBase):
    """Vollständiges Interest Group Schema."""
    id: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# === USER SCHEMAS ===

class UserBase(BaseModel):
    """Basis-Schema für Users."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=200)
    employee_id: Optional[str] = Field(None, max_length=50)
    organizational_unit: Optional[str] = Field(None, max_length=100)
    individual_permissions: Optional[List[str]] = Field(default_factory=list)
    is_department_head: Optional[bool] = False
    approval_level: Optional[int] = Field(1, ge=1, le=5)
    
    @field_validator('individual_permissions', mode='before')
    @classmethod
    def parse_individual_permissions(cls, v: Union[str, List[str], None]) -> List[str]:
        """Parse permissions from JSON string or list."""
        if v is None:
            return []
        if isinstance(v, str):
            if not v.strip():
                return []
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else [str(parsed)]
            except (json.JSONDecodeError, TypeError):
                return [item.strip() for item in v.split(',') if item.strip()]
        return v if isinstance(v, list) else []


class UserCreate(UserBase):
    """Schema für User-Erstellung."""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema für User-Updates."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    employee_id: Optional[str] = Field(None, max_length=50)
    organizational_unit: Optional[str] = Field(None, max_length=100)
    individual_permissions: Optional[List[str]] = None
    is_department_head: Optional[bool] = None
    approval_level: Optional[int] = Field(None, ge=1, le=5)
    is_active: Optional[bool] = None
    
    @field_validator('individual_permissions', mode='before')
    @classmethod
    def parse_individual_permissions(cls, v: Union[str, List[str], None]) -> Optional[List[str]]:
        """Parse permissions - None-tolerant for updates."""
        if v is None:
            return None
        if isinstance(v, str):
            if not v.strip():
                return []
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else [str(parsed)]
            except (json.JSONDecodeError, TypeError):
                return [item.strip() for item in v.split(',') if item.strip()]
        return v if isinstance(v, list) else []


class User(UserBase):
    """Vollständiges User Schema."""
    id: int
    is_active: bool
    created_at: datetime
    
    # Legacy-Kompatibilität
    department: Optional[Dict[str, Any]] = None
    permissions: Optional[List[str]] = None
    memberships: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


# === USER GROUP MEMBERSHIP SCHEMAS ===

class UserGroupMembershipBase(BaseModel):
    """Basis-Schema für User-Group-Memberships."""
    user_id: int
    interest_group_id: int
    approval_level: int = Field(1, ge=1, le=5)
    is_active: bool = True


class UserGroupMembershipCreate(UserGroupMembershipBase):
    """Schema für Membership-Erstellung."""
    role_in_group: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class UserGroupMembership(UserGroupMembershipBase):
    """Vollständiges Membership Schema."""
    id: int
    role_in_group: Optional[str] = None
    is_department_head: bool = False
    joined_at: datetime
    notes: Optional[str] = None
    
    # Relationships (optional)
    user: Optional[User] = None
    interest_group: Optional[InterestGroup] = None
    
    model_config = ConfigDict(from_attributes=True)


# === GENERIC RESPONSE SCHEMAS ===

class GenericResponse(BaseModel):
    """Standard Success/Error Response."""
    message: str
    success: bool = True


# === AUTH SCHEMAS ===

class LoginRequest(BaseModel):
    """Login Request Schema."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT Token Response."""
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    """User Info Response for /api/auth/me."""
    id: int
    email: EmailStr
    full_name: str
    organizational_unit: Optional[str] = None
    is_department_head: bool = False
    approval_level: int = 1
    is_active: bool = True
    groups: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class PasswordChangeRequest(BaseModel):
    """Password Change Request."""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
