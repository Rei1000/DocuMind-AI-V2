"""
Workflow History Repository Implementation.

SQLAlchemy Implementation für WorkflowStatusChange Entities.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from ..domain.repositories import WorkflowHistoryRepository
from ..domain.entities import WorkflowStatusChange
from backend.app.models import DocumentStatusChange as DocumentStatusChangeModel
from .mappers import WorkflowHistoryMapper


class SQLAlchemyWorkflowHistoryRepository(WorkflowHistoryRepository):
    """
    SQLAlchemy Implementation des WorkflowHistoryRepository.
    
    Adapter: Implementiert WorkflowHistoryRepository Port mit SQLAlchemy.
    
    Args:
        db: SQLAlchemy Session
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.mapper = WorkflowHistoryMapper()
    
    async def add(self, change: WorkflowStatusChange) -> WorkflowStatusChange:
        """
        Speichere WorkflowStatusChange.
        
        Args:
            change: WorkflowStatusChange Entity
            
        Returns:
            WorkflowStatusChange mit ID
        """
        model = self.mapper.to_model(change)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        
        # Update Entity mit ID
        change.id = model.id
        return change
    
    async def get_by_document_id(self, document_id: int) -> List[WorkflowStatusChange]:
        """
        Lade alle Status-Änderungen eines Dokuments.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            Liste der Status-Änderungen (chronologisch sortiert)
        """
        models = self.db.query(DocumentStatusChangeModel).filter(
            DocumentStatusChangeModel.upload_document_id == document_id
        ).order_by(DocumentStatusChangeModel.created_at.asc()).all()
        
        return [self.mapper.to_entity(model) for model in models]
    
    async def get_latest_by_document_id(self, document_id: int) -> Optional[WorkflowStatusChange]:
        """
        Lade letzte Status-Änderung eines Dokuments.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            Letzte WorkflowStatusChange oder None
        """
        model = self.db.query(DocumentStatusChangeModel).filter(
            DocumentStatusChangeModel.upload_document_id == document_id
        ).order_by(DocumentStatusChangeModel.created_at.desc()).first()
        
        if not model:
            return None
        
        return self.mapper.to_entity(model)
