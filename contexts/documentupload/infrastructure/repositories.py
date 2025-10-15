"""
Repository Implementations (Adapters) für Document Upload Context

Repositories sind die konkrete Implementierung der Repository Interfaces (Ports).
Sie verwenden SQLAlchemy für Persistence.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.app.models import (
    UploadDocument as UploadDocumentModel,
    UploadDocumentPage as UploadDocumentPageModel,
    UploadDocumentInterestGroup as UploadDocumentInterestGroupModel,
    DocumentAIResponse as DocumentAIResponseModel
)
from ..domain.entities import (
    UploadedDocument,
    DocumentPage,
    InterestGroupAssignment,
    AIProcessingResult
)
from ..domain.repositories import (
    UploadRepository,
    DocumentPageRepository,
    InterestGroupAssignmentRepository,
    AIResponseRepository
)
from .mappers import (
    UploadDocumentMapper,
    DocumentPageMapper,
    InterestGroupAssignmentMapper
)


class SQLAlchemyUploadRepository(UploadRepository):
    """
    SQLAlchemy Implementation des UploadRepository.
    
    Adapter: Implementiert UploadRepository Port mit SQLAlchemy.
    
    Args:
        db: SQLAlchemy Session
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.mapper = UploadDocumentMapper()
    
    async def save(self, document: UploadedDocument) -> UploadedDocument:
        """
        Speichere UploadedDocument (Create oder Update).
        
        Args:
            document: UploadedDocument Entity
            
        Returns:
            UploadedDocument mit ID
        """
        if document.id is None:
            # Create
            model = self.mapper.to_model(document)
            self.db.add(model)
            self.db.commit()
            self.db.refresh(model)
            
            # Update Entity mit ID
            document.id = model.id
            return document
        else:
            # Update
            model = self.db.query(UploadDocumentModel).filter(
                UploadDocumentModel.id == document.id
            ).first()
            
            if not model:
                raise ValueError(f"Document {document.id} not found")
            
            self.mapper.update_model(model, document)
            self.db.commit()
            self.db.refresh(model)
            
            return document
    
    async def get_by_id(self, document_id: int) -> Optional[UploadedDocument]:
        """
        Lade UploadedDocument by ID.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            UploadedDocument oder None
        """
        model = self.db.query(UploadDocumentModel).filter(
            UploadDocumentModel.id == document_id
        ).first()
        
        if not model:
            return None
        
        return self.mapper.to_entity(model)
    
    async def get_all(
        self,
        user_id: Optional[int] = None,
        document_type_id: Optional[int] = None,
        processing_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[UploadedDocument]:
        """
        Lade alle UploadedDocuments mit optionalen Filtern.
        
        Args:
            user_id: Filter nach Uploader
            document_type_id: Filter nach Dokumenttyp
            processing_status: Filter nach Status
            limit: Max Anzahl Ergebnisse
            offset: Offset für Pagination
            
        Returns:
            Liste von UploadedDocuments
        """
        query = self.db.query(UploadDocumentModel)
        
        # Filter anwenden
        if user_id is not None:
            query = query.filter(UploadDocumentModel.uploaded_by_user_id == user_id)
        
        if document_type_id is not None:
            query = query.filter(UploadDocumentModel.document_type_id == document_type_id)
        
        if processing_status is not None:
            query = query.filter(UploadDocumentModel.processing_status == processing_status)
        
        # Order by uploaded_at DESC (BEFORE pagination!)
        query = query.order_by(UploadDocumentModel.uploaded_at.desc())
        
        # Pagination
        query = query.offset(offset).limit(limit)
        
        models = query.all()
        
        return [self.mapper.to_entity(model) for model in models]
    
    async def delete(self, document_id: int) -> bool:
        """
        Lösche UploadedDocument (Hard Delete).
        
        Args:
            document_id: Dokument ID
            
        Returns:
            True wenn erfolgreich, False wenn nicht gefunden
        """
        model = self.db.query(UploadDocumentModel).filter(
            UploadDocumentModel.id == document_id
        ).first()
        
        if not model:
            return False
        
        self.db.delete(model)
        self.db.commit()
        
        return True
    
    async def exists(self, document_id: int) -> bool:
        """
        Prüfe ob UploadedDocument existiert.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            True wenn existiert
        """
        count = self.db.query(UploadDocumentModel).filter(
            UploadDocumentModel.id == document_id
        ).count()
        
        return count > 0


class SQLAlchemyDocumentPageRepository(DocumentPageRepository):
    """
    SQLAlchemy Implementation des DocumentPageRepository.
    
    Adapter: Implementiert DocumentPageRepository Port mit SQLAlchemy.
    
    Args:
        db: SQLAlchemy Session
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.mapper = DocumentPageMapper()
    
    async def save(self, page: DocumentPage) -> DocumentPage:
        """
        Speichere DocumentPage (Create oder Update).
        
        Args:
            page: DocumentPage Entity
            
        Returns:
            DocumentPage mit ID
        """
        if page.id is None:
            # Create
            model = self.mapper.to_model(page)
            self.db.add(model)
            self.db.commit()
            self.db.refresh(model)
            
            # Update Entity mit ID
            page.id = model.id
            return page
        else:
            # Update
            model = self.db.query(UploadDocumentPageModel).filter(
                UploadDocumentPageModel.id == page.id
            ).first()
            
            if not model:
                raise ValueError(f"Page {page.id} not found")
            
            # Update Model
            model.page_number = page.page_number
            model.preview_image_path = str(page.preview_image_path)
            model.thumbnail_path = str(page.thumbnail_path) if page.thumbnail_path else None
            model.width = page.dimensions.width if page.dimensions else None
            model.height = page.dimensions.height if page.dimensions else None
            
            self.db.commit()
            self.db.refresh(model)
            
            return page
    
    async def get_by_document_id(self, document_id: int) -> List[DocumentPage]:
        """
        Lade alle Pages eines Dokuments.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            Liste von DocumentPages (sortiert nach page_number)
        """
        models = self.db.query(UploadDocumentPageModel).filter(
            UploadDocumentPageModel.upload_document_id == document_id
        ).order_by(UploadDocumentPageModel.page_number).all()
        
        return [self.mapper.to_entity(model) for model in models]
    
    async def get_by_id(self, page_id: int) -> Optional[DocumentPage]:
        """
        Lade DocumentPage by ID.
        
        Args:
            page_id: Page ID
            
        Returns:
            DocumentPage oder None
        """
        model = self.db.query(UploadDocumentPageModel).filter(
            UploadDocumentPageModel.id == page_id
        ).first()
        
        if not model:
            return None
        
        return self.mapper.to_entity(model)
    
    async def delete_by_document_id(self, document_id: int) -> int:
        """
        Lösche alle Pages eines Dokuments.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            Anzahl gelöschter Pages
        """
        count = self.db.query(UploadDocumentPageModel).filter(
            UploadDocumentPageModel.upload_document_id == document_id
        ).delete()
        
        self.db.commit()
        
        return count


class SQLAlchemyInterestGroupAssignmentRepository(InterestGroupAssignmentRepository):
    """
    SQLAlchemy Implementation des InterestGroupAssignmentRepository.
    
    Adapter: Implementiert InterestGroupAssignmentRepository Port mit SQLAlchemy.
    
    Args:
        db: SQLAlchemy Session
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.mapper = InterestGroupAssignmentMapper()
    
    async def save(self, assignment: InterestGroupAssignment) -> InterestGroupAssignment:
        """
        Speichere InterestGroupAssignment.
        
        Args:
            assignment: InterestGroupAssignment Entity
            
        Returns:
            InterestGroupAssignment mit ID
        """
        if assignment.id is None:
            # Create
            model = self.mapper.to_model(assignment)
            self.db.add(model)
            self.db.commit()
            self.db.refresh(model)
            
            # Update Entity mit ID
            assignment.id = model.id
            return assignment
        else:
            # Update (normalerweise nicht nötig, da Assignments unveränderlich sind)
            model = self.db.query(UploadDocumentInterestGroupModel).filter(
                UploadDocumentInterestGroupModel.id == assignment.id
            ).first()
            
            if not model:
                raise ValueError(f"Assignment {assignment.id} not found")
            
            self.db.commit()
            self.db.refresh(model)
            
            return assignment
    
    async def get_by_document_id(self, document_id: int) -> List[InterestGroupAssignment]:
        """
        Lade alle Assignments eines Dokuments.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            Liste von InterestGroupAssignments
        """
        models = self.db.query(UploadDocumentInterestGroupModel).filter(
            UploadDocumentInterestGroupModel.upload_document_id == document_id
        ).all()
        
        return [self.mapper.to_entity(model) for model in models]
    
    async def delete_by_document_id(self, document_id: int) -> int:
        """
        Lösche alle Assignments eines Dokuments.
        
        Args:
            document_id: Dokument ID
            
        Returns:
            Anzahl gelöschter Assignments
        """
        count = self.db.query(UploadDocumentInterestGroupModel).filter(
            UploadDocumentInterestGroupModel.upload_document_id == document_id
        ).delete()
        
        self.db.commit()
        
        return count
    
    async def exists(self, document_id: int, interest_group_id: int) -> bool:
        """
        Prüfe ob Assignment existiert.
        
        Args:
            document_id: Dokument ID
            interest_group_id: Interest Group ID
            
        Returns:
            True wenn existiert
        """
        count = self.db.query(UploadDocumentInterestGroupModel).filter(
            and_(
                UploadDocumentInterestGroupModel.upload_document_id == document_id,
                UploadDocumentInterestGroupModel.interest_group_id == interest_group_id
            )
        ).count()
        
        return count > 0


class SQLAlchemyAIResponseRepository(AIResponseRepository):
    """
    SQLAlchemy Implementation des AIResponseRepository.
    
    Adapter: Implementiert AIResponseRepository Port mit SQLAlchemy.
    
    Args:
        db: SQLAlchemy Session
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def save(self, ai_response: AIProcessingResult) -> AIProcessingResult:
        """
        Speichere AIProcessingResult (Create oder Update).
        
        Args:
            ai_response: AIProcessingResult Entity
            
        Returns:
            AIProcessingResult mit ID (falls neu)
        """
        if ai_response.id:
            # Update
            model = self.db.query(DocumentAIResponseModel).filter(
                DocumentAIResponseModel.id == ai_response.id
            ).first()
            
            if not model:
                raise ValueError(f"AIResponse {ai_response.id} not found")
            
            # Update Felder
            model.json_response = ai_response.json_response
            model.processing_status = ai_response.processing_status
            model.tokens_sent = ai_response.tokens_sent
            model.tokens_received = ai_response.tokens_received
            model.total_tokens = ai_response.total_tokens
            model.response_time_ms = ai_response.response_time_ms
            model.error_message = ai_response.error_message
            
        else:
            # Create
            model = DocumentAIResponseModel(
                upload_document_id=ai_response.upload_document_id,
                upload_document_page_id=ai_response.upload_document_page_id,
                prompt_template_id=ai_response.prompt_template_id,
                ai_model_id=ai_response.ai_model_id,
                model_name=ai_response.model_name,
                json_response=ai_response.json_response,
                processing_status=ai_response.processing_status,
                tokens_sent=ai_response.tokens_sent,
                tokens_received=ai_response.tokens_received,
                total_tokens=ai_response.total_tokens,
                response_time_ms=ai_response.response_time_ms,
                error_message=ai_response.error_message,
                processed_at=ai_response.processed_at
            )
            self.db.add(model)
        
        self.db.commit()
        self.db.refresh(model)
        
        # Convert zurück zu Entity
        return self._model_to_entity(model)
    
    async def get_by_page_id(self, page_id: int) -> Optional[AIProcessingResult]:
        """
        Lade AIProcessingResult für eine Seite.
        
        Args:
            page_id: DocumentPage ID
            
        Returns:
            AIProcessingResult oder None
        """
        model = self.db.query(DocumentAIResponseModel).filter(
            DocumentAIResponseModel.upload_document_page_id == page_id
        ).first()
        
        if not model:
            return None
        
        return self._model_to_entity(model)
    
    async def get_by_document_id(self, document_id: int) -> List[AIProcessingResult]:
        """
        Lade alle AIProcessingResults eines Dokuments.
        
        Args:
            document_id: UploadDocument ID
            
        Returns:
            Liste von AIProcessingResults (sortiert nach page_number)
        """
        models = self.db.query(DocumentAIResponseModel).filter(
            DocumentAIResponseModel.upload_document_id == document_id
        ).all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def exists_for_page(self, page_id: int) -> bool:
        """
        Prüfe ob AIProcessingResult für Seite existiert.
        
        Args:
            page_id: DocumentPage ID
            
        Returns:
            True wenn existiert
        """
        count = self.db.query(DocumentAIResponseModel).filter(
            DocumentAIResponseModel.upload_document_page_id == page_id
        ).count()
        
        return count > 0
    
    async def delete_by_document_id(self, document_id: int) -> int:
        """
        Lösche alle AIProcessingResults eines Dokuments.
        
        Args:
            document_id: UploadDocument ID
            
        Returns:
            Anzahl gelöschter Responses
        """
        deleted = self.db.query(DocumentAIResponseModel).filter(
            DocumentAIResponseModel.upload_document_id == document_id
        ).delete()
        
        self.db.commit()
        
        return deleted
    
    def _model_to_entity(self, model: DocumentAIResponseModel) -> AIProcessingResult:
        """
        Konvertiere SQLAlchemy Model zu Domain Entity.
        
        Args:
            model: DocumentAIResponseModel
            
        Returns:
            AIProcessingResult Entity
        """
        return AIProcessingResult(
            id=model.id,
            upload_document_id=model.upload_document_id,
            upload_document_page_id=model.upload_document_page_id,
            prompt_template_id=model.prompt_template_id,
            ai_model_id=model.ai_model_id,
            model_name=model.model_name,
            json_response=model.json_response,
            processing_status=model.processing_status,
            tokens_sent=model.tokens_sent,
            tokens_received=model.tokens_received,
            total_tokens=model.total_tokens,
            response_time_ms=model.response_time_ms,
            error_message=model.error_message,
            processed_at=model.processed_at
        )

