"""
Infrastructure Mappers: PromptTemplates Context

Mapped zwischen Domain Entities und DB Models (SQLAlchemy).
Anti-Corruption Layer zwischen Domain und Persistence.
"""

import json
from typing import Optional

from backend.app.models import PromptTemplateModel
from ..domain.entities import PromptTemplate, PromptStatus


class PromptTemplateMapper:
    """
    Mapper: PromptTemplate Entity ↔ SQLAlchemy Model
    
    Konvertiert zwischen sauberer Domain Entity und DB Model.
    """
    
    @staticmethod
    def to_entity(db_model: Optional[PromptTemplateModel]) -> Optional[PromptTemplate]:
        """
        Map SQLAlchemy Model → Domain Entity
        
        Args:
            db_model: SQLAlchemy PromptTemplateModel
            
        Returns:
            PromptTemplate Entity oder None
        """
        if db_model is None:
            return None
        
        # Parse JSON fields
        tags = json.loads(db_model.tags) if db_model.tags else []
        
        # Parse status enum
        status = PromptStatus(db_model.status) if db_model.status else PromptStatus.DRAFT
        
        return PromptTemplate(
            id=db_model.id,
            name=db_model.name,
            description=db_model.description or "",
            prompt_text=db_model.prompt_text,
            system_instructions=db_model.system_instructions,
            document_type_id=db_model.document_type_id,
            ai_model=db_model.ai_model,
            temperature=db_model.temperature / 100.0,  # Convert from int (0-200) to float (0.0-2.0)
            max_tokens=db_model.max_tokens,
            top_p=db_model.top_p / 100.0,  # Convert from int (0-100) to float (0.0-1.0)
            detail_level=db_model.detail_level,
            status=status,
            version=db_model.version,
            created_by=db_model.created_by,
            tested_successfully=db_model.tested_successfully,
            success_count=db_model.success_count,
            last_used_at=db_model.last_used_at,
            tags=tags,
            example_input=db_model.example_input,
            example_output=db_model.example_output,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at
        )
    
    @staticmethod
    def to_model(entity: PromptTemplate, db_model: Optional[PromptTemplateModel] = None) -> PromptTemplateModel:
        """
        Map Domain Entity → SQLAlchemy Model
        
        Args:
            entity: PromptTemplate Entity
            db_model: Optional existing model (für Updates)
            
        Returns:
            SQLAlchemy PromptTemplateModel
        """
        if db_model is None:
            db_model = PromptTemplateModel()
        
        # Map fields
        db_model.name = entity.name
        db_model.description = entity.description
        db_model.prompt_text = entity.prompt_text
        db_model.system_instructions = entity.system_instructions
        db_model.document_type_id = entity.document_type_id
        db_model.ai_model = entity.ai_model
        db_model.temperature = int(entity.temperature * 100)  # Convert from float (0.0-2.0) to int (0-200)
        db_model.max_tokens = entity.max_tokens
        db_model.top_p = int(entity.top_p * 100)  # Convert from float (0.0-1.0) to int (0-100)
        db_model.detail_level = entity.detail_level
        db_model.status = entity.status.value if isinstance(entity.status, PromptStatus) else entity.status
        db_model.version = entity.version
        db_model.created_by = entity.created_by
        db_model.tested_successfully = entity.tested_successfully
        db_model.success_count = entity.success_count
        db_model.last_used_at = entity.last_used_at
        db_model.tags = json.dumps(entity.tags)
        db_model.example_input = entity.example_input
        db_model.example_output = entity.example_output
        db_model.created_at = entity.created_at
        db_model.updated_at = entity.updated_at
        
        return db_model

