"""
Integration Tests für UploadDocumentMapper - Version-Felder.

Test-Driven Development: Tests für Mapper mit Version-Feldern.
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.models import UploadDocument as UploadDocumentModel
from contexts.documentupload.infrastructure.mappers import UploadDocumentMapper
from contexts.documentupload.domain.entities import UploadedDocument
from contexts.documentupload.domain.value_objects import (
    FileType, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus, WorkflowStatus
)


@pytest.fixture
def db_session():
    """Database Session für Tests."""
    from backend.app.database import SessionLocal
    session = SessionLocal()
    yield session
    session.close()


@pytest.mark.asyncio
async def test_mapper_to_entity_includes_version_fields(db_session: Session):
    """Mapper konvertiert Model zu Entity mit Version-Feldern"""
    # Arrange: Erstelle Model mit Version-Feldern
    model = UploadDocumentModel(
        filename="test_v1.0.pdf",
        original_filename="test.pdf",
        file_size_bytes=1024,
        file_type="pdf",
        document_type_id=1,
        qm_chapter="1.2",
        version="v1.0",
        page_count=0,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        file_path="data/uploads/test.pdf",
        processing_method="ocr",
        processing_status="pending",
        workflow_status="draft",
        document_series_id=100,  # NEU
        parent_document_id=None,  # NEU
        is_current_version=True  # NEU
    )
    
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)
    
    try:
        # Act
        entity = UploadDocumentMapper.to_entity(model)
        
        # Assert
        assert entity.document_series_id == 100
        assert entity.parent_document_id is None
        assert entity.is_current_version is True
    finally:
        db_session.delete(model)
        db_session.commit()


@pytest.mark.asyncio
async def test_mapper_to_model_includes_version_fields(db_session: Session):
    """Mapper konvertiert Entity zu Model mit Version-Feldern"""
    # Arrange
    entity = UploadedDocument(
        id=None,
        file_type=FileType.PDF,
        file_size_bytes=1024,
        document_type_id=1,
        metadata=DocumentMetadata(
            filename="test_v2.0.pdf",
            original_filename="test.pdf",
            qm_chapter="1.2",
            version="v2.0"
        ),
        file_path=FilePath("data/uploads/test.pdf"),
        processing_method=ProcessingMethod.OCR,
        processing_status=ProcessingStatus.PENDING,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        document_series_id=100,  # NEU
        parent_document_id=1,  # NEU
        is_current_version=True  # NEU
    )
    
    # Act
    model = UploadDocumentMapper.to_model(entity)
    
    # Assert
    assert model.document_series_id == 100
    assert model.parent_document_id == 1
    assert model.is_current_version is True

