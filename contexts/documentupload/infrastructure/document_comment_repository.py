"""
Document Comment Repository Implementation.

SQLAlchemy Implementation für DocumentComment Entities.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import delete

from ..domain.repositories import DocumentCommentRepository
from ..domain.entities import DocumentComment
from backend.app.models import DocumentComment as DocumentCommentModel
from .mappers import DocumentCommentMapper


class SQLAlchemyDocumentCommentRepository(DocumentCommentRepository):
    """
    SQLAlchemy Implementation des DocumentCommentRepository.
    
    Adapter: Implementiert DocumentCommentRepository Port mit SQLAlchemy.
    
    Args:
        db: SQLAlchemy Session
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.mapper = DocumentCommentMapper()
    
    async def add(self, comment: DocumentComment) -> DocumentComment:
        """
        Speichere DocumentComment.
        
        Args:
            comment: DocumentComment Entity
            
        Returns:
            DocumentComment mit ID
        """
        model = self.mapper.to_model(comment)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        
        # Update Entity mit ID
        comment.id = model.id
        return comment
    
    async def get_by_document_id(self, document_id: int) -> List[DocumentComment]:
        """
        Lade alle Kommentare eines Dokuments.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            Liste der Kommentare (chronologisch sortiert)
        """
        models = self.db.query(DocumentCommentModel).filter(
            DocumentCommentModel.upload_document_id == document_id
        ).order_by(DocumentCommentModel.created_at.asc()).all()
        
        return [self.mapper.to_entity(model) for model in models]
    
    async def get_by_document_id_and_type(
        self,
        document_id: int,
        comment_type: str
    ) -> List[DocumentComment]:
        """
        Lade Kommentare eines Dokuments nach Typ.
        
        Args:
            document_id: Dokument ID
            comment_type: Kommentar-Typ (general, review, approval, rejection)
            
        Returns:
            Liste der Kommentare des Typs
        """
        models = self.db.query(DocumentCommentModel).filter(
            DocumentCommentModel.upload_document_id == document_id,
            DocumentCommentModel.comment_type == comment_type
        ).order_by(DocumentCommentModel.created_at.asc()).all()
        
        return [self.mapper.to_entity(model) for model in models]
    
    async def delete(self, comment_id: int) -> bool:
        """
        Lösche DocumentComment.
        
        Args:
            comment_id: Kommentar ID
            
        Returns:
            True wenn erfolgreich gelöscht
        """
        result = self.db.query(DocumentCommentModel).filter(
            DocumentCommentModel.id == comment_id
        ).delete()
        
        self.db.commit()
        
        return result > 0
