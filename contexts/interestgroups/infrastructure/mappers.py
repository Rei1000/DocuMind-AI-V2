"""
Mapper zwischen Domain Entities und SQLAlchemy Models
Konvertiert in beide Richtungen ohne die Legacy-Models zu ändern
"""

from typing import Optional
from datetime import datetime
from backend.app.models import InterestGroup as InterestGroupModel
from contexts.interestgroups.domain import (
    InterestGroup,
    GroupCode,
    GroupName,
    GroupDescription,
    GroupPermissions
)
from contexts.interestgroups.domain.value_objects import LenientGroupCode, LenientGroupName
import json


class InterestGroupMapper:
    """
    Mapper zwischen Domain Entity und SQLAlchemy Model
    Stellt sicher dass Legacy-Models unverändert bleiben
    """
    
    @staticmethod
    def to_domain(model: InterestGroupModel) -> InterestGroup:
        """
        Konvertiert SQLAlchemy Model zu Domain Entity
        Verwendet tolerante Value Objects für Legacy-Daten
        
        Args:
            model: SQLAlchemy InterestGroup Model
            
        Returns:
            Domain InterestGroup Entity
        """
        if not model:
            return None
            
        # Erstelle Domain Entity mit toleranten Value Objects für Legacy-Daten
        entity = InterestGroup(
            id=model.id,
            name=LenientGroupName(model.name),  # Tolerant für Legacy
            code=LenientGroupCode(model.code),  # Tolerant für Legacy
            description=GroupDescription(model.description),
            permissions=GroupPermissions(model.group_permissions),
            ai_functionality=model.ai_functionality,
            typical_tasks=model.typical_tasks,
            is_external=model.is_external,
            is_active=model.is_active,
            created_at=model.created_at if hasattr(model, 'created_at') else None,
            updated_at=model.updated_at if hasattr(model, 'updated_at') else None
        )
        
        return entity
    
    @staticmethod
    def to_model(entity: InterestGroup, existing_model: Optional[InterestGroupModel] = None) -> InterestGroupModel:
        """
        Konvertiert Domain Entity zu SQLAlchemy Model
        
        Args:
            entity: Domain InterestGroup Entity
            existing_model: Optional existierendes Model für Updates
            
        Returns:
            SQLAlchemy InterestGroup Model
        """
        if not entity:
            return None
            
        # Bei Update verwende existierendes Model
        if existing_model:
            model = existing_model
        else:
            # Neues Model erstellen
            model = InterestGroupModel()
            
        # Setze Attribute
        model.name = str(entity.name)
        model.code = str(entity.code)
        model.description = str(entity.description) if entity.description else None
        
        # Permissions serialisieren (Legacy-kompatibel)
        if entity.permissions:
            # Legacy erwartet JSON-String
            model.group_permissions = entity.permissions.to_json_string()
        else:
            model.group_permissions = None
            
        model.ai_functionality = entity.ai_functionality
        model.typical_tasks = entity.typical_tasks
        model.is_external = entity.is_external
        model.is_active = entity.is_active
        
        # ID nur setzen wenn vorhanden (nicht bei neuen Entities)
        if entity.id:
            model.id = entity.id
            
        # Timestamps werden von SQLAlchemy verwaltet
        
        return model
    
    @staticmethod
    def to_schema_dict(entity: InterestGroup) -> dict:
        """
        Konvertiert Domain Entity zu Schema-kompatiblem Dictionary
        Für Response Models
        
        Args:
            entity: Domain InterestGroup Entity
            
        Returns:
            Dictionary kompatibel mit InterestGroup Schema
        """
        return {
            'id': entity.id,
            'name': str(entity.name),
            'code': str(entity.code),
            'description': str(entity.description) if entity.description else None,
            'group_permissions': entity.permissions.to_json_string() if entity.permissions else None,
            'ai_functionality': entity.ai_functionality,
            'typical_tasks': entity.typical_tasks,
            'is_external': entity.is_external,
            'is_active': entity.is_active,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at
        }