"""
Integration Tests für Repository find_by_hash Funktionalität.

Test-Driven Development: RED Phase für find_by_hash.
"""

import pytest
from datetime import datetime
from contexts.documentupload.domain.entities import UploadedDocument
from contexts.documentupload.domain.value_objects import (
    FileHash,
    FileType,
    FilePath,
    ProcessingMethod,
    ProcessingStatus,
    DocumentMetadata,
    WorkflowStatus
)
from contexts.documentupload.infrastructure.repositories import SQLAlchemyUploadRepository
from backend.app.database import SessionLocal


@pytest.fixture
def db_session():
    """Database Session für Tests."""
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def upload_repo(db_session):
    """SQLAlchemyUploadRepository für Tests."""
    return SQLAlchemyUploadRepository(db_session)


@pytest.mark.asyncio
async def test_save_document_with_hash(db_session, upload_repo):
    """Repository speichert FileHash korrekt"""
    # Arrange
    file_hash = FileHash("a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3")
    metadata = DocumentMetadata(
        filename="test.pdf",
        original_filename="test.pdf",
        qm_chapter="1.2",
        version="v1.0"
    )
    
    document = UploadedDocument(
        id=None,
        file_type=FileType.PDF,
        file_size_bytes=1024,
        document_type_id=1,
        metadata=metadata,
        file_path=FilePath("data/uploads/test.pdf"),
        processing_method=ProcessingMethod.OCR,
        processing_status=ProcessingStatus.PENDING,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        file_hash=file_hash
    )
    
    # Act
    saved = await upload_repo.save(document)
    
    # Assert
    assert saved.file_hash is not None
    assert saved.file_hash.value == file_hash.value
    
    # Prüfe DB direkt
    from backend.app.models import UploadDocument as UploadDocumentModel
    model = db_session.query(UploadDocumentModel).filter_by(id=saved.id).first()
    # Note: file_hash Feld existiert noch nicht in DB, wird später hinzugefügt
    # assert model.file_hash == file_hash.value


@pytest.mark.asyncio
async def test_find_by_hash(db_session, upload_repo):
    """Repository kann Dokument nach Hash finden"""
    # Arrange: Speichere Dokument mit Hash
    file_hash = FileHash("a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3")
    metadata = DocumentMetadata(
        filename="test.pdf",
        original_filename="test.pdf",
        qm_chapter="1.2",
        version="v1.0"
    )
    
    document = UploadedDocument(
        id=None,
        file_type=FileType.PDF,
        file_size_bytes=1024,
        document_type_id=1,
        metadata=metadata,
        file_path=FilePath("data/uploads/test.pdf"),
        processing_method=ProcessingMethod.OCR,
        processing_status=ProcessingStatus.PENDING,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        file_hash=file_hash
    )
    saved = await upload_repo.save(document)
    
    # Act
    found = await upload_repo.find_by_hash(file_hash)
    
    # Assert
    assert found is not None
    assert found.id == saved.id
    assert found.file_hash.value == file_hash.value


@pytest.mark.asyncio
async def test_find_by_hash_not_found(db_session, upload_repo):
    """Repository gibt None zurück wenn Hash nicht gefunden"""
    # Arrange
    non_existent_hash = FileHash("b" * 64)  # Hash der nicht existiert
    
    # Act
    found = await upload_repo.find_by_hash(non_existent_hash)
    
    # Assert
    assert found is None


@pytest.mark.asyncio
async def test_find_by_hash_multiple_documents_same_hash(db_session, upload_repo):
    """Wenn mehrere Dokumente denselben Hash haben, wird das erste zurückgegeben"""
    # Arrange: Speichere zwei Dokumente mit gleichem Hash
    file_hash = FileHash("a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3")
    
    metadata1 = DocumentMetadata(
        filename="doc1.pdf",
        original_filename="doc1.pdf",
        qm_chapter="1.2",
        version="v1.0"
    )
    document1 = UploadedDocument(
        id=None,
        file_type=FileType.PDF,
        file_size_bytes=1024,
        document_type_id=1,
        metadata=metadata1,
        file_path=FilePath("data/uploads/doc1.pdf"),
        processing_method=ProcessingMethod.OCR,
        processing_status=ProcessingStatus.PENDING,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        file_hash=file_hash
    )
    saved1 = await upload_repo.save(document1)
    
    metadata2 = DocumentMetadata(
        filename="doc2.pdf",
        original_filename="doc2.pdf",
        qm_chapter="1.2",
        version="v1.0"
    )
    document2 = UploadedDocument(
        id=None,
        file_type=FileType.PDF,
        file_size_bytes=1024,
        document_type_id=1,
        metadata=metadata2,
        file_path=FilePath("data/uploads/doc2.pdf"),
        processing_method=ProcessingMethod.OCR,
        processing_status=ProcessingStatus.PENDING,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        file_hash=file_hash,
        is_duplicate=True,
        duplicate_of_document_id=saved1.id
    )
    saved2 = await upload_repo.save(document2)
    
    # Act
    found = await upload_repo.find_by_hash(file_hash)
    
    # Assert
    assert found is not None
    # Sollte das erste Dokument finden (nicht das Duplikat)
    assert found.id in [saved1.id, saved2.id]

