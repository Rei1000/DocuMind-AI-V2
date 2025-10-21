"""
Infrastructure Repositories: PromptTemplates Context

Konkrete Implementierung der Repository Interfaces (Adapters).
Verwendet SQLAlchemy für Persistence.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.models import PromptTemplateModel
from ..domain.entities import PromptTemplate, PromptStatus
from ..domain.repositories import IPromptTemplateRepository
from .mappers import PromptTemplateMapper


class SQLAlchemyPromptTemplateRepository(IPromptTemplateRepository):
    """
    Adapter: SQLAlchemy Implementation of IPromptTemplateRepository
    
    Implementiert das Repository Interface mit SQLAlchemy.
    """
    
    def __init__(self, db: Session):
        """
        Args:
            db: SQLAlchemy Session (Dependency Injection)
        """
        self.db = db
        self.mapper = PromptTemplateMapper()
    
    def get_by_id(self, template_id: int) -> Optional[PromptTemplate]:
        """Hole PromptTemplate by ID"""
        db_model = self.db.query(PromptTemplateModel).filter(
            PromptTemplateModel.id == template_id
        ).first()
        
        return self.mapper.to_entity(db_model)
    
    def get_by_name(self, name: str) -> Optional[PromptTemplate]:
        """Hole PromptTemplate by Name"""
        db_model = self.db.query(PromptTemplateModel).filter(
            PromptTemplateModel.name == name
        ).first()
        
        return self.mapper.to_entity(db_model)
    
    def get_all(self, 
                status: Optional[PromptStatus] = None,
                document_type_id: Optional[int] = None) -> List[PromptTemplate]:
        """Hole alle PromptTemplates mit optionalen Filtern"""
        query = self.db.query(PromptTemplateModel)
        
        if status:
            query = query.filter(PromptTemplateModel.status == status.value)
        
        if document_type_id:
            query = query.filter(PromptTemplateModel.document_type_id == document_type_id)
        
        # Sort by name
        query = query.order_by(PromptTemplateModel.name)
        
        db_models = query.all()
        return [self.mapper.to_entity(model) for model in db_models if model]
    
    def get_active_for_document_type(self, document_type_id: int) -> List[PromptTemplate]:
        """Hole alle aktiven Templates für einen Dokumenttyp"""
        db_models = self.db.query(PromptTemplateModel).filter(
            PromptTemplateModel.document_type_id == document_type_id,
            PromptTemplateModel.status == PromptStatus.ACTIVE.value
        ).order_by(PromptTemplateModel.name).all()
        
        return [self.mapper.to_entity(model) for model in db_models if model]
    
    def save(self, template: PromptTemplate) -> PromptTemplate:
        """Speichere PromptTemplate (Create oder Update)"""
        # Check if this is an update (entity has ID)
        if template.id:
            # Update: Load existing model
            db_model = self.db.query(PromptTemplateModel).filter(
                PromptTemplateModel.id == template.id
            ).first()
            
            if not db_model:
                raise ValueError(f"Template mit ID {template.id} nicht gefunden")
            
            # Update existing model
            db_model = self.mapper.to_model(template, db_model)
        else:
            # Create: New model
            db_model = self.mapper.to_model(template)
            self.db.add(db_model)
        
        # Commit
        self.db.commit()
        self.db.refresh(db_model)
        
        # Return updated entity
        return self.mapper.to_entity(db_model)
    
    def delete(self, template_id: int) -> bool:
        """Lösche PromptTemplate (Hard Delete)"""
        db_model = self.db.query(PromptTemplateModel).filter(
            PromptTemplateModel.id == template_id
        ).first()
        
        if not db_model:
            return False
        
        self.db.delete(db_model)
        self.db.commit()
        return True
    
    def exists_by_name(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """Prüfe ob Name bereits existiert"""
        query = self.db.query(PromptTemplateModel).filter(
            PromptTemplateModel.name == name
        )
        
        if exclude_id:
            query = query.filter(PromptTemplateModel.id != exclude_id)
        
        return query.first() is not None
    
    def search_by_tags(self, tags: List[str]) -> List[PromptTemplate]:
        """
        Suche Templates nach Tags
        
        Note: SQLite doesn't have native JSON array search,
        so we use LIKE for simple text matching.
        For production, consider PostgreSQL with JSON operators.
        """
        if not tags:
            return []
        
        # Build OR conditions for each tag
        conditions = [PromptTemplateModel.tags.like(f'%"{tag}"%') for tag in tags]
        
        db_models = self.db.query(PromptTemplateModel).filter(
            or_(*conditions)
        ).order_by(PromptTemplateModel.name).all()
        
        return [self.mapper.to_entity(model) for model in db_models if model]
    
    async def get_default_for_document_type(self, document_type_id: int) -> Optional[PromptTemplate]:
        """
        Hole Standard-Prompt-Template für einen Dokumenttyp.
        
        Logik:
        1. Prüfe ob DocumentType.default_prompt_template_id gesetzt und aktiv
        2. Falls nicht: Hole das zuletzt aktualisierte aktive Template für den Dokumenttyp
        
        Args:
            document_type_id: ID des Dokumenttyps
            
        Returns:
            Standard PromptTemplate Entity oder None
        """
        from backend.app.models import DocumentTypeModel
        
        # 1. Hole DocumentType
        doc_type = self.db.query(DocumentTypeModel).filter(
            DocumentTypeModel.id == document_type_id
        ).first()
        
        if not doc_type:
            return None
        
        # 2. Prüfe ob Standard-Template gesetzt und aktiv
        if doc_type.default_prompt_template_id:
            default_template = self.db.query(PromptTemplateModel).filter(
                PromptTemplateModel.id == doc_type.default_prompt_template_id,
                PromptTemplateModel.status == "active"
            ).first()
            
            if default_template:
                return self.mapper.to_entity(default_template)
        
        # 3. Falls kein Standard: Hole das neueste aktive Template für den Dokumenttyp
        fallback_template = self.db.query(PromptTemplateModel).filter(
            PromptTemplateModel.document_type_id == document_type_id,
            PromptTemplateModel.status == "active"
        ).order_by(PromptTemplateModel.updated_at.desc()).first()
        
        if fallback_template:
            return self.mapper.to_entity(fallback_template)
        
        return None

