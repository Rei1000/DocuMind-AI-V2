"""
Document Workflow Repository Implementations.

SQLAlchemy-basierte Implementierungen der Repository Interfaces.
"""

from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from ..domain.entities import (
    DocumentWorkflow,
    StatusChange,
    DocumentComment,
    WorkflowStatus,
    CommentType
)
from ..domain.repositories import (
    IDocumentWorkflowRepository,
    IStatusChangeRepository,
    IDocumentCommentRepository
)

# Import der SQLAlchemy Models
from backend.app.models import UploadDocument
from .models import (
    DocumentStatusChange as StatusChangeModel,
    DocumentComment as CommentModel
)


class SQLAlchemyDocumentWorkflowRepository(IDocumentWorkflowRepository):
    """SQLAlchemy Implementation des Document Workflow Repository."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_by_document_id(self, document_id: int) -> Optional[DocumentWorkflow]:
        """Hole Workflow für ein Dokument."""
        document = self.db.query(UploadDocument).filter(
            UploadDocument.id == document_id
        ).first()
        
        if not document:
            return None
        
        # Konvertiere zu Domain Entity
        return DocumentWorkflow(
            id=document.id,
            document_id=document.id,
            current_status=WorkflowStatus(document.workflow_status),
            created_at=document.created_at,
            updated_at=document.updated_at
        )
    
    async def save(self, workflow: DocumentWorkflow) -> DocumentWorkflow:
        """Speichere oder update Workflow."""
        document = self.db.query(UploadDocument).filter(
            UploadDocument.id == workflow.document_id
        ).first()
        
        if not document:
            raise ValueError(f"Document {workflow.document_id} not found")
        
        # Update Status
        document.workflow_status = workflow.current_status
        document.updated_at = workflow.updated_at
        
        self.db.commit()
        self.db.refresh(document)
        
        # Return updated entity
        workflow.updated_at = document.updated_at
        return workflow
    
    async def update_status(
        self, 
        document_id: int, 
        new_status: WorkflowStatus,
        user_id: int,
        reason: Optional[str] = None,
        comment: Optional[str] = None
    ) -> DocumentWorkflow:
        """Update Workflow Status mit Audit Trail."""
        document = self.db.query(UploadDocument).filter(
            UploadDocument.id == document_id
        ).first()
        
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        old_status = document.workflow_status
        document.workflow_status = new_status
        document.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(document)
        
        return DocumentWorkflow(
            id=document.id,
            document_id=document.id,
            current_status=WorkflowStatus(document.workflow_status),
            created_at=document.created_at,
            updated_at=document.updated_at
        )
    
    async def get_documents_by_status(
        self, 
        status: WorkflowStatus,
        interest_group_ids: Optional[List[int]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """Hole Dokumente nach Status, optional gefiltert nach Interest Groups."""
        query = self.db.query(UploadDocument).filter(
            UploadDocument.workflow_status == status.value
        )
        
        # Filter nach Interest Groups wenn angegeben
        if interest_group_ids:
            from backend.app.models import UploadDocumentInterestGroup
            query = query.join(UploadDocumentInterestGroup).filter(
                UploadDocumentInterestGroup.interest_group_id.in_(interest_group_ids)
            )
        
        # Paginierung
        documents = query.order_by(desc(UploadDocument.uploaded_at)).offset(offset).limit(limit).all()
        
        # Konvertiere zu Dict für API Response
        result = []
        for doc in documents:
            result.append({
                "id": doc.id,
                "filename": doc.filename,
                "original_filename": doc.original_filename,
                "document_type_id": doc.document_type_id,
                "qm_chapter": doc.qm_chapter,
                "version": doc.version,
                "workflow_status": doc.workflow_status,
                "uploaded_by_user_id": doc.uploaded_by_user_id,
                "uploaded_at": doc.uploaded_at.isoformat(),
                "page_count": doc.page_count,
                "file_size_bytes": doc.file_size_bytes,
                "file_type": doc.file_type
            })
        
        return result


class SQLAlchemyStatusChangeRepository(IStatusChangeRepository):
    """SQLAlchemy Implementation des Status Change Repository."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, status_change: StatusChange) -> StatusChange:
        """Erstelle neuen Status Change Eintrag."""
        db_change = StatusChangeModel(
            upload_document_id=status_change.document_id,
            from_status=status_change.from_status.value if status_change.from_status else None,
            to_status=status_change.to_status.value,
            changed_by_user_id=status_change.changed_by_user_id,
            changed_at=status_change.changed_at,
            change_reason=status_change.change_reason,
            comment=status_change.comment
        )
        
        self.db.add(db_change)
        self.db.commit()
        self.db.refresh(db_change)
        
        # Return Domain Entity
        return StatusChange(
            id=db_change.id,
            document_id=db_change.upload_document_id,
            from_status=WorkflowStatus(db_change.from_status) if db_change.from_status else None,
            to_status=WorkflowStatus(db_change.to_status),
            changed_by_user_id=db_change.changed_by_user_id,
            changed_at=db_change.changed_at,
            change_reason=db_change.change_reason,
            comment=db_change.comment
        )
    
    async def get_by_document_id(
        self, 
        document_id: int,
        limit: int = 100
    ) -> List[StatusChange]:
        """Hole Status Change History für ein Dokument."""
        changes = self.db.query(StatusChangeModel).filter(
            StatusChangeModel.upload_document_id == document_id
        ).order_by(desc(StatusChangeModel.changed_at)).limit(limit).all()
        
        result = []
        for change in changes:
            result.append(StatusChange(
                id=change.id,
                document_id=change.upload_document_id,
                from_status=WorkflowStatus(change.from_status) if change.from_status else None,
                to_status=WorkflowStatus(change.to_status),
                changed_by_user_id=change.changed_by_user_id,
                changed_at=change.changed_at,
                change_reason=change.change_reason,
                comment=change.comment
            ))
        
        return result
    
    async def get_by_user_id(
        self,
        user_id: int,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[StatusChange]:
        """Hole alle Status Changes eines Users."""
        query = self.db.query(StatusChangeModel).filter(
            StatusChangeModel.changed_by_user_id == user_id
        )
        
        if from_date:
            query = query.filter(StatusChangeModel.changed_at >= from_date)
        
        if to_date:
            query = query.filter(StatusChangeModel.changed_at <= to_date)
        
        changes = query.order_by(desc(StatusChangeModel.changed_at)).limit(limit).all()
        
        result = []
        for change in changes:
            result.append(StatusChange(
                id=change.id,
                document_id=change.upload_document_id,
                from_status=WorkflowStatus(change.from_status) if change.from_status else None,
                to_status=WorkflowStatus(change.to_status),
                changed_by_user_id=change.changed_by_user_id,
                changed_at=change.changed_at,
                change_reason=change.change_reason,
                comment=change.comment
            ))
        
        return result


class SQLAlchemyDocumentCommentRepository(IDocumentCommentRepository):
    """SQLAlchemy Implementation des Document Comment Repository."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, comment: DocumentComment) -> DocumentComment:
        """Erstelle neuen Kommentar."""
        db_comment = CommentModel(
            upload_document_id=comment.document_id,
            comment_text=comment.comment_text,
            comment_type=comment.comment_type.value,
            page_number=comment.page_number,
            created_by_user_id=comment.created_by_user_id,
            created_at=comment.created_at,
            status_change_id=comment.status_change_id
        )
        
        self.db.add(db_comment)
        self.db.commit()
        self.db.refresh(db_comment)
        
        # Return Domain Entity
        return DocumentComment(
            id=db_comment.id,
            document_id=db_comment.upload_document_id,
            comment_text=db_comment.comment_text,
            comment_type=CommentType(db_comment.comment_type),
            page_number=db_comment.page_number,
            created_by_user_id=db_comment.created_by_user_id,
            created_at=db_comment.created_at,
            status_change_id=db_comment.status_change_id
        )
    
    async def get_by_document_id(
        self,
        document_id: int,
        page_number: Optional[int] = None,
        comment_type: Optional[CommentType] = None,
        limit: int = 100
    ) -> List[DocumentComment]:
        """Hole Kommentare für ein Dokument."""
        query = self.db.query(CommentModel).filter(
            CommentModel.upload_document_id == document_id
        )
        
        if page_number is not None:
            query = query.filter(CommentModel.page_number == page_number)
        
        if comment_type is not None:
            query = query.filter(CommentModel.comment_type == comment_type.value)
        
        comments = query.order_by(desc(CommentModel.created_at)).limit(limit).all()
        
        result = []
        for comment in comments:
            result.append(DocumentComment(
                id=comment.id,
                document_id=comment.upload_document_id,
                comment_text=comment.comment_text,
                comment_type=CommentType(comment.comment_type),
                page_number=comment.page_number,
                created_by_user_id=comment.created_by_user_id,
                created_at=comment.created_at,
                status_change_id=comment.status_change_id
            ))
        
        return result
    
    async def get_by_id(self, comment_id: int) -> Optional[DocumentComment]:
        """Hole einzelnen Kommentar."""
        comment = self.db.query(CommentModel).filter(
            CommentModel.id == comment_id
        ).first()
        
        if not comment:
            return None
        
        return DocumentComment(
            id=comment.id,
            document_id=comment.upload_document_id,
            comment_text=comment.comment_text,
            comment_type=CommentType(comment.comment_type),
            page_number=comment.page_number,
            created_by_user_id=comment.created_by_user_id,
            created_at=comment.created_at,
            status_change_id=comment.status_change_id
        )
    
    async def update(self, comment: DocumentComment) -> DocumentComment:
        """Update existierenden Kommentar."""
        db_comment = self.db.query(CommentModel).filter(
            CommentModel.id == comment.id
        ).first()
        
        if not db_comment:
            raise ValueError(f"Comment {comment.id} not found")
        
        db_comment.comment_text = comment.comment_text
        db_comment.comment_type = comment.comment_type.value
        db_comment.page_number = comment.page_number
        db_comment.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_comment)
        
        return comment
    
    async def delete(self, comment_id: int) -> bool:
        """Lösche Kommentar."""
        comment = self.db.query(CommentModel).filter(
            CommentModel.id == comment_id
        ).first()
        
        if not comment:
            return False
        
        self.db.delete(comment)
        self.db.commit()
        
        return True
