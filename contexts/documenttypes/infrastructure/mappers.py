"""
Infrastructure Mappers: DocumentTypes Context

Mapped zwischen Domain Entities und DB Models (SQLAlchemy).
Anti-Corruption Layer zwischen Domain und Persistence.
"""

import json
from typing import Optional

from backend.app.models import DocumentTypeModel
from ..domain.entities import DocumentType


class DocumentTypeMapper:
    """
    Mapper: DocumentType Entity ↔ SQLAlchemy Model
    
    Konvertiert zwischen sauberer Domain Entity und DB Model.
    """
    
    @staticmethod
    def to_entity(db_model: Optional[DocumentTypeModel]) -> Optional[DocumentType]:
        """
        Map SQLAlchemy Model → Domain Entity
        
        Args:
            db_model: SQLAlchemy DocumentTypeModel
            
        Returns:
            DocumentType Entity oder None
        """
        if db_model is None:
            return None
        
        # Parse JSON fields
        allowed_file_types = json.loads(db_model.allowed_file_types) if db_model.allowed_file_types else []
        
        return DocumentType(
            id=db_model.id,
            name=db_model.name,
            code=db_model.code,
            description=db_model.description or "",
            allowed_file_types=allowed_file_types,
            max_file_size_mb=db_model.max_file_size_mb,
            requires_ocr=db_model.requires_ocr,
            requires_vision=db_model.requires_vision,
            default_prompt_template_id=db_model.default_prompt_template_id,
            created_by=db_model.created_by,
            is_active=db_model.is_active,
            sort_order=db_model.sort_order,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at
        )
    
    @staticmethod
    def to_model(entity: DocumentType, db_model: Optional[DocumentTypeModel] = None) -> DocumentTypeModel:
        """
        Map Domain Entity → SQLAlchemy Model
        
        Args:
            entity: DocumentType Entity
            db_model: Optional existing model (für Updates)
            
        Returns:
            SQLAlchemy DocumentTypeModel
        """
        if db_model is None:
            db_model = DocumentTypeModel()
        
        # Map fields
        db_model.name = entity.name
        db_model.code = entity.code
        db_model.description = entity.description
        db_model.allowed_file_types = json.dumps(entity.allowed_file_types)
        db_model.max_file_size_mb = entity.max_file_size_mb
        db_model.requires_ocr = entity.requires_ocr
        db_model.requires_vision = entity.requires_vision
        db_model.default_prompt_template_id = entity.default_prompt_template_id
        db_model.created_by = entity.created_by
        db_model.is_active = entity.is_active
        db_model.sort_order = entity.sort_order
        db_model.created_at = entity.created_at
        db_model.updated_at = entity.updated_at
        
        return db_model

