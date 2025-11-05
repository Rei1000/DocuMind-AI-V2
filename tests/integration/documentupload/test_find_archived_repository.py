"""
Integration Tests für find_archived Repository-Methode.

Test-Driven Development: Tests für Archiv-System Repository.
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from contexts.documentupload.infrastructure.repositories import SQLAlchemyUploadRepository
from contexts.documentupload.domain.entities import UploadedDocument
from contexts.documentupload.domain.value_objects import (
    FileType, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus,
    WorkflowStatus
)
from backend.app.database import SessionLocal
from contexts.documentupload.application.use_cases import SoftDeleteDocumentUseCase


@pytest.fixture
def db_session():
    """Database Session für Tests."""
    session = SessionLocal()
    yield session
    # Cleanup
    try:
        session.rollback()
    except:
        pass
    session.close()


@pytest.mark.asyncio
async def test_find_archived_returns_deleted_documents(db_session: Session):
    """find_archived gibt nur gelöschte Dokumente zurück."""
    # Arrange
    upload_repo = SQLAlchemyUploadRepository(db_session)
    
    # Erstelle aktives Dokument
    active_doc = UploadedDocument(
        id=None,
        file_type=FileType.PDF,
        file_size_bytes=1024,
        document_type_id=1,
        metadata=DocumentMetadata(
            filename="active.pdf",
            original_filename="active.pdf",
            qm_chapter="1.1",
            version="v1.0"
        ),
        file_path=FilePath("data/uploads/active.pdf"),
        processing_method=ProcessingMethod.OCR,
        processing_status=ProcessingStatus.COMPLETED,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        workflow_status=WorkflowStatus.APPROVED
    )
    active_doc = await upload_repo.save(active_doc)
    
    # Erstelle gelöschtes Dokument
    soft_delete_use_case = SoftDeleteDocumentUseCase(upload_repo)
    deleted_doc = await soft_delete_use_case.execute(
        document_id=active_doc.id,
        deleted_by_user_id=1,
        reason="Test deletion"
    )
    
    # Act
    archived_docs = await upload_repo.find_archived(limit=100, offset=0)
    
    # Assert
    assert len(archived_docs) >= 1
    # Prüfe ob gelöschtes Dokument in Liste ist
    deleted_ids = [doc.id for doc in archived_docs]
    assert deleted_doc.id in deleted_ids
    # Prüfe ob aktives Dokument NICHT in Liste ist
    assert active_doc.id not in deleted_ids


@pytest.mark.asyncio
async def test_find_archived_filters_by_document_type(db_session: Session):
    """find_archived filtert nach document_type_id."""
    # Arrange
    upload_repo = SQLAlchemyUploadRepository(db_session)
    
    # Erstelle 2 gelöschte Dokumente mit verschiedenen Typen
    doc1 = UploadedDocument(
        id=None,
        file_type=FileType.PDF,
        file_size_bytes=1024,
        document_type_id=1,
        metadata=DocumentMetadata(
            filename="doc1.pdf",
            original_filename="doc1.pdf",
            qm_chapter="1.1",
            version="v1.0"
        ),
        file_path=FilePath("data/uploads/doc1.pdf"),
        processing_method=ProcessingMethod.OCR,
        processing_status=ProcessingStatus.COMPLETED,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        workflow_status=WorkflowStatus.APPROVED
    )
    doc1 = await upload_repo.save(doc1)
    
    doc2 = UploadedDocument(
        id=None,
        file_type=FileType.PDF,
        file_size_bytes=2048,
        document_type_id=2,
        metadata=DocumentMetadata(
            filename="doc2.pdf",
            original_filename="doc2.pdf",
            qm_chapter="2.1",
            version="v2.0"
        ),
        file_path=FilePath("data/uploads/doc2.pdf"),
        processing_method=ProcessingMethod.VISION,
        processing_status=ProcessingStatus.COMPLETED,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        workflow_status=WorkflowStatus.APPROVED
    )
    doc2 = await upload_repo.save(doc2)
    
    # Lösche beide
    soft_delete_use_case = SoftDeleteDocumentUseCase(upload_repo)
    deleted_doc1 = await soft_delete_use_case.execute(doc1.id, 1, "Test")
    deleted_doc2 = await soft_delete_use_case.execute(doc2.id, 1, "Test")
    
    # Act: Filter nach document_type_id=1
    archived_docs = await upload_repo.find_archived(
        limit=100,
        offset=0,
        document_type_id=1
    )
    
    # Assert
    assert len(archived_docs) >= 1
    # Alle Dokumente sollten document_type_id=1 haben
    for doc in archived_docs:
        assert doc.document_type_id == 1
    # doc2 sollte nicht in Liste sein
    deleted_ids = [doc.id for doc in archived_docs]
    assert deleted_doc2.id not in deleted_ids


@pytest.mark.asyncio
async def test_find_archived_sorted_by_deleted_at_desc(db_session: Session):
    """find_archived sortiert nach deleted_at DESC (neueste zuerst)."""
    # Arrange
    upload_repo = SQLAlchemyUploadRepository(db_session)
    
    # Erstelle 2 Dokumente
    doc1 = UploadedDocument(
        id=None,
        file_type=FileType.PDF,
        file_size_bytes=1024,
        document_type_id=1,
        metadata=DocumentMetadata(
            filename="doc1.pdf",
            original_filename="doc1.pdf",
            qm_chapter="1.1",
            version="v1.0"
        ),
        file_path=FilePath("data/uploads/doc1.pdf"),
        processing_method=ProcessingMethod.OCR,
        processing_status=ProcessingStatus.COMPLETED,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        workflow_status=WorkflowStatus.APPROVED
    )
    doc1 = await upload_repo.save(doc1)
    
    doc2 = UploadedDocument(
        id=None,
        file_type=FileType.PDF,
        file_size_bytes=2048,
        document_type_id=1,
        metadata=DocumentMetadata(
            filename="doc2.pdf",
            original_filename="doc2.pdf",
            qm_chapter="1.2",
            version="v2.0"
        ),
        file_path=FilePath("data/uploads/doc2.pdf"),
        processing_method=ProcessingMethod.VISION,
        processing_status=ProcessingStatus.COMPLETED,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        workflow_status=WorkflowStatus.APPROVED
    )
    doc2 = await upload_repo.save(doc2)
    
    # Lösche beide (doc1 zuerst, dann doc2)
    soft_delete_use_case = SoftDeleteDocumentUseCase(upload_repo)
    deleted_doc1 = await soft_delete_use_case.execute(doc1.id, 1, "Test")
    import time
    time.sleep(0.1)  # Kurze Pause damit deleted_at unterschiedlich ist
    deleted_doc2 = await soft_delete_use_case.execute(doc2.id, 1, "Test")
    
    # Act
    archived_docs = await upload_repo.find_archived(limit=100, offset=0)
    
    # Assert
    assert len(archived_docs) >= 2
    # Erste Dokument sollte neueste deleted_at haben (doc2)
    if archived_docs[0].deleted_at and archived_docs[1].deleted_at:
        assert archived_docs[0].deleted_at >= archived_docs[1].deleted_at


@pytest.mark.asyncio
async def test_find_archived_respects_limit_and_offset(db_session: Session):
    """find_archived respektiert limit und offset."""
    # Arrange
    upload_repo = SQLAlchemyUploadRepository(db_session)
    
    # Erstelle 3 gelöschte Dokumente
    soft_delete_use_case = SoftDeleteDocumentUseCase(upload_repo)
    for i in range(3):
        doc = UploadedDocument(
            id=None,
            file_type=FileType.PDF,
            file_size_bytes=1024,
            document_type_id=1,
            metadata=DocumentMetadata(
                filename=f"doc{i}.pdf",
                original_filename=f"doc{i}.pdf",
                qm_chapter="1.1",
                version="v1.0"
            ),
            file_path=FilePath(f"data/uploads/doc{i}.pdf"),
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.COMPLETED,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            workflow_status=WorkflowStatus.APPROVED
        )
        doc = await upload_repo.save(doc)
        await soft_delete_use_case.execute(doc.id, 1, "Test")
    
    # Act: Limit 2, Offset 0
    archived_docs_page1 = await upload_repo.find_archived(limit=2, offset=0)
    
    # Act: Limit 2, Offset 2
    archived_docs_page2 = await upload_repo.find_archived(limit=2, offset=2)
    
    # Assert
    assert len(archived_docs_page1) <= 2
    assert len(archived_docs_page2) <= 2
    # IDs sollten unterschiedlich sein
    ids_page1 = [doc.id for doc in archived_docs_page1]
    ids_page2 = [doc.id for doc in archived_docs_page2]
    assert len(set(ids_page1 + ids_page2)) == len(ids_page1) + len(ids_page2)  # Keine Duplikate


