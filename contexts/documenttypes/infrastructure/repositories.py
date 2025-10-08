"""
Infrastructure Repositories: DocumentTypes Context

Konkrete Implementierung der Repository Interfaces (Adapters).
Verwendet SQLAlchemy für Persistence.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.models import DocumentTypeModel
from ..domain.entities import DocumentType
from ..domain.repositories import IDocumentTypeRepository
from .mappers import DocumentTypeMapper


class SQLAlchemyDocumentTypeRepository(IDocumentTypeRepository):
    """
    Adapter: SQLAlchemy Implementation of IDocumentTypeRepository
    
    Implementiert das Repository Interface mit SQLAlchemy.
    """
    
    def __init__(self, db: Session):
        """
        Args:
            db: SQLAlchemy Session (Dependency Injection)
        """
        self.db = db
        self.mapper = DocumentTypeMapper()
    
    def get_by_id(self, document_type_id: int) -> Optional[DocumentType]:
        """
        Hole DocumentType by ID
        
        Args:
            document_type_id: ID des Dokumenttyps
            
        Returns:
            DocumentType Entity oder None
        """
        db_model = self.db.query(DocumentTypeModel).filter(
            DocumentTypeModel.id == document_type_id
        ).first()
        
        return self.mapper.to_entity(db_model)
    
    def get_by_code(self, code: str) -> Optional[DocumentType]:
        """
        Hole DocumentType by Code (eindeutig)
        
        Args:
            code: Technischer Code
            
        Returns:
            DocumentType Entity oder None
        """
        db_model = self.db.query(DocumentTypeModel).filter(
            DocumentTypeModel.code == code.upper()
        ).first()
        
        return self.mapper.to_entity(db_model)
    
    def get_all(self, active_only: bool = True) -> List[DocumentType]:
        """
        Hole alle DocumentTypes
        
        Args:
            active_only: Nur aktive Typen?
            
        Returns:
            Liste von DocumentType Entities
        """
        query = self.db.query(DocumentTypeModel)
        
        if active_only:
            query = query.filter(DocumentTypeModel.is_active == True)
        
        db_models = query.all()
        return [self.mapper.to_entity(model) for model in db_models if model]
    
    def save(self, document_type: DocumentType) -> DocumentType:
        """
        Speichere DocumentType (Create oder Update)
        
        Args:
            document_type: DocumentType Entity
            
        Returns:
            Gespeicherte DocumentType Entity mit ID
        """
        # Check if this is an update (entity has ID)
        if document_type.id:
            # Update: Load existing model
            db_model = self.db.query(DocumentTypeModel).filter(
                DocumentTypeModel.id == document_type.id
            ).first()
            
            if not db_model:
                raise ValueError(f"DocumentType mit ID {document_type.id} nicht gefunden")
            
            # Update existing model
            db_model = self.mapper.to_model(document_type, db_model)
        else:
            # Create: New model
            db_model = self.mapper.to_model(document_type)
            self.db.add(db_model)
        
        # Commit
        self.db.commit()
        self.db.refresh(db_model)
        
        # Return updated entity
        return self.mapper.to_entity(db_model)
    
    def delete(self, document_type_id: int) -> bool:
        """
        Lösche DocumentType (Hard Delete)
        
        Args:
            document_type_id: ID des Dokumenttyps
            
        Returns:
            True wenn gelöscht, False wenn nicht gefunden
        """
        db_model = self.db.query(DocumentTypeModel).filter(
            DocumentTypeModel.id == document_type_id
        ).first()
        
        if not db_model:
            return False
        
        self.db.delete(db_model)
        self.db.commit()
        return True
    
    def exists_by_code(self, code: str, exclude_id: Optional[int] = None) -> bool:
        """
        Prüfe ob Code bereits existiert
        
        Args:
            code: Technischer Code
            exclude_id: Optional: ID die ausgeschlossen werden soll (für Updates)
            
        Returns:
            True wenn Code existiert, sonst False
        """
        query = self.db.query(DocumentTypeModel).filter(
            DocumentTypeModel.code == code.upper()
        )
        
        if exclude_id:
            query = query.filter(DocumentTypeModel.id != exclude_id)
        
        return query.first() is not None

