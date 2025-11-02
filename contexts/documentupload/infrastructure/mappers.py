"""
Mappers für Document Upload Context

Mappers konvertieren zwischen SQLAlchemy Models (DTOs) und Domain Entities.
"""

from typing import List, Optional
from datetime import datetime
from backend.app.models import (
    UploadDocument as UploadDocumentModel,
    UploadDocumentPage as UploadDocumentPageModel,
    UploadDocumentInterestGroup as UploadDocumentInterestGroupModel,
    DocumentStatusChange as DocumentStatusChangeModel,
    DocumentComment as DocumentCommentModel
)
from ..domain.entities import (
    UploadedDocument,
    DocumentPage,
    InterestGroupAssignment,
    WorkflowStatusChange,
    DocumentComment
)
from ..domain.value_objects import (
    FileType,
    ProcessingMethod,
    ProcessingStatus,
    DocumentMetadata,
    PageDimensions,
    FilePath,
    WorkflowStatus,
    FileHash
)


class UploadDocumentMapper:
    """
    Mapper für UploadedDocument Entity ↔ UploadDocument Model.
    """
    
    @staticmethod
    def to_entity(model: UploadDocumentModel) -> UploadedDocument:
        """
        Konvertiere SQLAlchemy Model zu Domain Entity.
        
        Args:
            model: UploadDocument SQLAlchemy Model
            
        Returns:
            UploadedDocument Entity
        """
        metadata = DocumentMetadata(
            filename=model.filename,
            original_filename=model.original_filename,
            qm_chapter=model.qm_chapter,
            version=model.version
        )
        
        file_path = FilePath(model.file_path)
        
        # Load interest group IDs from relationship (via junction table)
        interest_group_ids = []
        if hasattr(model, 'interest_groups') and model.interest_groups:
            interest_group_ids = [ig.interest_group_id for ig in model.interest_groups]
        
        # FileHash (optional, falls DB-Feld existiert)
        file_hash = None
        if hasattr(model, 'file_hash') and model.file_hash:
            file_hash = FileHash(model.file_hash)
        
        # Duplikat-Felder (optional, falls DB-Felder existieren)
        is_duplicate = getattr(model, 'is_duplicate', False)
        duplicate_of_document_id = getattr(model, 'duplicate_of_document_id', None)
        
        # NEU Phase 2: Version-Felder (optional, falls DB-Felder existieren)
        document_series_id = getattr(model, 'document_series_id', None)
        parent_document_id = getattr(model, 'parent_document_id', None)
        is_current_version = getattr(model, 'is_current_version', True)  # Default: True für Rückwärtskompatibilität
        
        # NEU Phase 1.3: Soft Delete Felder (optional, falls DB-Felder existieren)
        deleted_at = getattr(model, 'deleted_at', None)
        deleted_by_user_id = getattr(model, 'deleted_by_user_id', None)
        deletion_reason = getattr(model, 'deletion_reason', None)
        
        return UploadedDocument(
            id=model.id,
            file_type=FileType(model.file_type),
            file_size_bytes=model.file_size_bytes,
            document_type_id=model.document_type_id,
            metadata=metadata,
            file_path=file_path,
            processing_method=ProcessingMethod(model.processing_method),
            processing_status=ProcessingStatus(model.processing_status),
            uploaded_by_user_id=model.uploaded_by_user_id,
            uploaded_at=model.uploaded_at,
            workflow_status=WorkflowStatus(model.workflow_status) if model.workflow_status else WorkflowStatus.DRAFT,
            pages=[],  # Werden separat geladen
            interest_group_ids=interest_group_ids,
            file_hash=file_hash,  # Phase 1.1
            is_duplicate=is_duplicate,  # Phase 1.1
            duplicate_of_document_id=duplicate_of_document_id,  # Phase 1.1
            # Phase 2 - Versionierung
            document_series_id=document_series_id,  # NEU
            parent_document_id=parent_document_id,  # NEU
            is_current_version=is_current_version,  # NEU
            # Phase 1.3 - Soft Delete
            deleted_at=deleted_at,  # NEU
            deleted_by_user_id=deleted_by_user_id,  # NEU
            deletion_reason=deletion_reason  # NEU
        )
    
    @staticmethod
    def to_model(entity: UploadedDocument) -> UploadDocumentModel:
        """
        Konvertiere Domain Entity zu SQLAlchemy Model.
        
        Args:
            entity: UploadedDocument Entity
            
        Returns:
            UploadDocument SQLAlchemy Model
        """
        model = UploadDocumentModel(
            id=entity.id,
            filename=entity.metadata.filename,
            original_filename=entity.metadata.original_filename,
            file_size_bytes=entity.file_size_bytes,
            file_type=entity.file_type.value,
            document_type_id=entity.document_type_id,
            qm_chapter=entity.metadata.qm_chapter,
            version=entity.metadata.version,
            page_count=entity.page_count,
            uploaded_by_user_id=entity.uploaded_by_user_id,
            uploaded_at=entity.uploaded_at,
            file_path=str(entity.file_path),
            processing_method=entity.processing_method.value,
            processing_status=entity.processing_status.value,
            workflow_status=entity.workflow_status.value
        )
        
        # NEU: FileHash und Duplikat-Felder (falls DB-Felder existieren)
        if hasattr(model, 'file_hash') and entity.file_hash:
            model.file_hash = entity.file_hash.value
        if hasattr(model, 'is_duplicate'):
            model.is_duplicate = entity.is_duplicate
        if hasattr(model, 'duplicate_of_document_id'):
            model.duplicate_of_document_id = entity.duplicate_of_document_id
        
        # NEU Phase 2: Version-Felder (falls DB-Felder existieren)
        if hasattr(model, 'document_series_id'):
            model.document_series_id = entity.document_series_id
        if hasattr(model, 'parent_document_id'):
            model.parent_document_id = entity.parent_document_id
        if hasattr(model, 'is_current_version'):
            model.is_current_version = entity.is_current_version
        
        return model
    
    @staticmethod
    def update_model(model: UploadDocumentModel, entity: UploadedDocument) -> None:
        """
        Update SQLAlchemy Model mit Entity-Daten (für Updates).
        
        Args:
            model: Existierendes UploadDocument Model
            entity: UploadedDocument Entity mit neuen Daten
        """
        model.filename = entity.metadata.filename
        model.original_filename = entity.metadata.original_filename
        model.file_size_bytes = entity.file_size_bytes
        model.file_type = entity.file_type.value
        model.document_type_id = entity.document_type_id
        model.qm_chapter = entity.metadata.qm_chapter
        model.version = entity.metadata.version
        model.page_count = entity.page_count
        model.uploaded_by_user_id = entity.uploaded_by_user_id
        model.uploaded_at = entity.uploaded_at
        model.file_path = str(entity.file_path)
        model.processing_method = entity.processing_method.value
        model.processing_status = entity.processing_status.value
        model.workflow_status = entity.workflow_status.value
        
        # NEU: FileHash und Duplikat-Felder (falls DB-Felder existieren)
        if hasattr(model, 'file_hash') and entity.file_hash:
            model.file_hash = entity.file_hash.value
        if hasattr(model, 'is_duplicate'):
            model.is_duplicate = entity.is_duplicate
        if hasattr(model, 'duplicate_of_document_id'):
            model.duplicate_of_document_id = entity.duplicate_of_document_id
        
        # NEU Phase 2: Version-Felder (falls DB-Felder existieren)
        if hasattr(model, 'document_series_id'):
            model.document_series_id = entity.document_series_id
        if hasattr(model, 'parent_document_id'):
            model.parent_document_id = entity.parent_document_id
        if hasattr(model, 'is_current_version'):
            model.is_current_version = entity.is_current_version
        
        # NEU Phase 1.3: Soft Delete Felder (falls DB-Felder existieren)
        if hasattr(model, 'deleted_at'):
            model.deleted_at = entity.deleted_at
        if hasattr(model, 'deleted_by_user_id'):
            model.deleted_by_user_id = entity.deleted_by_user_id
        if hasattr(model, 'deletion_reason'):
            model.deletion_reason = entity.deletion_reason


class DocumentPageMapper:
    """
    Mapper für DocumentPage Entity ↔ UploadDocumentPage Model.
    """
    
    @staticmethod
    def to_entity(model: UploadDocumentPageModel) -> DocumentPage:
        """
        Konvertiere SQLAlchemy Model zu Domain Entity.
        
        Args:
            model: UploadDocumentPage SQLAlchemy Model
            
        Returns:
            DocumentPage Entity
        """
        dimensions = None
        if model.width and model.height:
            dimensions = PageDimensions(
                width=model.width,
                height=model.height
            )
        
        thumbnail_path = None
        if model.thumbnail_path:
            thumbnail_path = FilePath(model.thumbnail_path)
        
        return DocumentPage(
            id=model.id,
            upload_document_id=model.upload_document_id,
            page_number=model.page_number,
            preview_image_path=FilePath(model.preview_image_path),
            thumbnail_path=thumbnail_path,
            dimensions=dimensions,
            created_at=model.created_at
        )
    
    @staticmethod
    def to_model(entity: DocumentPage) -> UploadDocumentPageModel:
        """
        Konvertiere Domain Entity zu SQLAlchemy Model.
        
        Args:
            entity: DocumentPage Entity
            
        Returns:
            UploadDocumentPage SQLAlchemy Model
        """
        return UploadDocumentPageModel(
            id=entity.id,
            upload_document_id=entity.upload_document_id,
            page_number=entity.page_number,
            preview_image_path=str(entity.preview_image_path),
            thumbnail_path=str(entity.thumbnail_path) if entity.thumbnail_path else None,
            width=entity.dimensions.width if entity.dimensions else None,
            height=entity.dimensions.height if entity.dimensions else None,
            created_at=entity.created_at
        )


class InterestGroupAssignmentMapper:
    """
    Mapper für InterestGroupAssignment Entity ↔ UploadDocumentInterestGroup Model.
    """
    
    @staticmethod
    def to_entity(model: UploadDocumentInterestGroupModel) -> InterestGroupAssignment:
        """
        Konvertiere SQLAlchemy Model zu Domain Entity.
        
        Args:
            model: UploadDocumentInterestGroup SQLAlchemy Model
            
        Returns:
            InterestGroupAssignment Entity
        """
        return InterestGroupAssignment(
            id=model.id,
            upload_document_id=model.upload_document_id,
            interest_group_id=model.interest_group_id,
            assigned_by_user_id=model.assigned_by_user_id,
            assigned_at=model.assigned_at
        )
    
    @staticmethod
    def to_model(entity: InterestGroupAssignment) -> UploadDocumentInterestGroupModel:
        """
        Konvertiere Domain Entity zu SQLAlchemy Model.
        
        Args:
            entity: InterestGroupAssignment Entity
            
        Returns:
            UploadDocumentInterestGroup SQLAlchemy Model
        """
        return UploadDocumentInterestGroupModel(
            id=entity.id,
            upload_document_id=entity.upload_document_id,
            interest_group_id=entity.interest_group_id,
            assigned_by_user_id=entity.assigned_by_user_id,
            assigned_at=entity.assigned_at
        )


class WorkflowHistoryMapper:
    """
    Mapper für WorkflowStatusChange Entity ↔ DocumentStatusChange Model.
    """
    
    @staticmethod
    def to_entity(model: DocumentStatusChangeModel) -> WorkflowStatusChange:
        """
        Konvertiere SQLAlchemy Model zu Domain Entity.
        
        Args:
            model: DocumentStatusChange SQLAlchemy Model
            
        Returns:
            WorkflowStatusChange Entity
        """
        return WorkflowStatusChange(
            id=model.id,
            document_id=model.upload_document_id,  # Fix: upload_document_id statt document_id
            from_status=WorkflowStatus(model.from_status),
            to_status=WorkflowStatus(model.to_status),
            changed_by_user_id=model.changed_by_user_id,
            reason=model.change_reason,
            created_at=model.created_at
        )
    
    @staticmethod
    def to_model(entity: WorkflowStatusChange) -> DocumentStatusChangeModel:
        """
        Konvertiere Domain Entity zu SQLAlchemy Model.
        
        Args:
            entity: WorkflowStatusChange Entity
            
        Returns:
            DocumentStatusChange SQLAlchemy Model
        """
        return DocumentStatusChangeModel(
            id=entity.id if entity.id > 0 else None,
            upload_document_id=entity.document_id,  # Fix: upload_document_id statt document_id
            from_status=entity.from_status.value,
            to_status=entity.to_status.value,
            changed_by_user_id=entity.changed_by_user_id,
            change_reason=entity.reason,
            created_at=entity.created_at
        )


class DocumentCommentMapper:
    """
    Mapper für DocumentComment Entity ↔ DocumentComment Model.
    """
    
    @staticmethod
    def to_entity(model: DocumentCommentModel) -> DocumentComment:
        """
        Konvertiere SQLAlchemy Model zu Domain Entity.
        
        Args:
            model: DocumentComment SQLAlchemy Model
            
        Returns:
            DocumentComment Entity
        """
        return DocumentComment(
            id=model.id,
            document_id=model.upload_document_id,  # Fix: upload_document_id → document_id
            user_id=model.created_by_user_id,  # Fix: created_by_user_id → user_id
            comment_text=model.comment_text,
            comment_type=model.comment_type,
            created_at=model.created_at
        )
    
    @staticmethod
    def to_model(entity: DocumentComment) -> DocumentCommentModel:
        """
        Konvertiere Domain Entity zu SQLAlchemy Model.
        
        Args:
            entity: DocumentComment Entity
            
        Returns:
            DocumentComment SQLAlchemy Model
        """
        from datetime import datetime
        
        return DocumentCommentModel(
            id=entity.id if entity.id > 0 else None,
            upload_document_id=entity.document_id,  # Fix: document_id → upload_document_id
            created_by_user_id=entity.user_id,  # Fix: user_id → created_by_user_id
            comment_text=entity.comment_text,
            comment_type=entity.comment_type,
            created_at=entity.created_at,
            updated_at=entity.created_at if entity.created_at else datetime.utcnow()  # Fix: updated_at setzen
        )

