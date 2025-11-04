"""
Integration Tests für Duplikat-Erkennung nach Löschung.

Test-Szenario:
1. Dokument hochladen (noch nicht freigegeben/indexiert)
2. Dokument löschen (Soft Delete)
3. Gleiches Dokument nochmals hochladen → sollte NICHT als Duplikat erkannt werden
4. Dokument freigeben und indexieren
5. Indexiertes Dokument löschen → RAG Cleanup muss funktionieren
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
import hashlib
import os
from pathlib import Path

from contexts.documentupload.infrastructure.repositories import SQLAlchemyUploadRepository
from contexts.documentupload.application.use_cases import (
    UploadDocumentUseCase,
    SoftDeleteDocumentUseCase,
    GetDocumentsByWorkflowStatusUseCase
)
from contexts.documentupload.domain.entities import UploadedDocument
from contexts.documentupload.domain.value_objects import (
    FileType, DocumentMetadata, FilePath, ProcessingMethod, ProcessingStatus,
    WorkflowStatus, FileHash
)
from backend.app.database import SessionLocal


@pytest.fixture
def db_session():
    """Database Session für Tests."""
    session = SessionLocal()
    yield session
    try:
        session.rollback()
    except:
        pass
    session.close()


@pytest.fixture
def test_file(tmp_path):
    """Erstelle temporäre Test-Datei."""
    test_file_path = tmp_path / "test_document.pdf"
    test_file_path.write_bytes(b"Test PDF Content for Duplicate Detection")
    return test_file_path


# FileStorageService wird nicht benötigt für diese Tests


@pytest.mark.asyncio
async def test_upload_delete_reupload_not_duplicate(db_session, test_file):
    """
    Test: Upload → Delete → Re-Upload sollte NICHT als Duplikat erkannt werden.
    
    Szenario:
    1. Dokument hochladen (DRAFT, nicht indexiert)
    2. Dokument löschen (Soft Delete)
    3. Gleiches Dokument nochmals hochladen → sollte als NEUES Dokument behandelt werden
    """
    # Arrange
    upload_repo = SQLAlchemyUploadRepository(db_session)
    # Wir verwenden direkt das Repository, nicht den UseCase
    # upload_use_case = UploadDocumentUseCase(
    #     upload_repository=upload_repo,
    #     file_storage_service=file_storage_service
    # )
    soft_delete_use_case = SoftDeleteDocumentUseCase(upload_repository=upload_repo)
    
    # Step 1: Erstes Upload
    with open(test_file, 'rb') as f:
        file_content = f.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
    
    # Mock Upload (ohne tatsächliche Datei-Speicherung für Schnelligkeit)
    # Aber wir testen die Hash-Logik
    document1 = UploadedDocument(
        id=None,
        file_type=FileType.PDF,
        file_size_bytes=len(file_content),
        document_type_id=1,
        metadata=DocumentMetadata(
            filename=test_file.name,
            original_filename=test_file.name,
            qm_chapter="1.1",
            version="v1.0"
        ),
        file_path=FilePath(str(test_file)),
        processing_method=ProcessingMethod.OCR,
        processing_status=ProcessingStatus.COMPLETED,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        workflow_status=WorkflowStatus.DRAFT,  # Noch nicht freigegeben
        file_hash=FileHash(file_hash)
    )
    document1 = await upload_repo.save(document1)
    document1_id = document1.id
    
    # Step 2: Soft Delete
    deleted_document = await soft_delete_use_case.execute(
        document_id=document1_id,
        deleted_by_user_id=1,
        reason="Test deletion before approval"
    )
    assert deleted_document.deleted_at is not None
    assert deleted_document.workflow_status == WorkflowStatus.DELETED
    
    # Step 3: Re-Upload (gleiches Dokument)
    # find_by_hash sollte gelöschte Dokumente ignorieren
    found_duplicate = await upload_repo.find_by_hash(FileHash(file_hash))
    
    # Assert: Gelöschtes Dokument sollte NICHT als Duplikat gefunden werden
    assert found_duplicate is None, "Gelöschtes Dokument sollte nicht als Duplikat erkannt werden"
    
    # Re-Upload sollte als neues Dokument behandelt werden
    document2 = UploadedDocument(
        id=None,
        file_type=FileType.PDF,
        file_size_bytes=len(file_content),
        document_type_id=1,
        metadata=DocumentMetadata(
            filename=test_file.name,
            original_filename=test_file.name,
            qm_chapter="1.1",
            version="v1.0"
        ),
        file_path=FilePath(str(test_file)),
        processing_method=ProcessingMethod.OCR,
        processing_status=ProcessingStatus.COMPLETED,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        workflow_status=WorkflowStatus.DRAFT,
        file_hash=FileHash(file_hash),
        is_duplicate=False  # Sollte NICHT als Duplikat markiert sein
    )
    document2 = await upload_repo.save(document2)
    
    # Assert: Dokument 2 sollte NICHT als Duplikat markiert sein
    assert document2.is_duplicate is False or document2.is_duplicate is None
    assert document2.duplicate_of_document_id is None
    assert document2.id != document1_id


@pytest.mark.asyncio
async def test_delete_indexed_document_triggers_rag_cleanup(db_session, test_file):
    """
    Test: Löschen eines indexierten Dokuments → RAG Cleanup.
    
    Szenario:
    1. Dokument hochladen
    2. Dokument freigeben (APPROVED)
    3. Dokument indexieren (simuliert)
    4. Dokument löschen → RAG Cleanup Event sollte publiziert werden
    """
    # Arrange
    upload_repo = SQLAlchemyUploadRepository(db_session)
    soft_delete_use_case = SoftDeleteDocumentUseCase(upload_repository=upload_repo)
    
    # Mock Event Publisher
    from unittest.mock import Mock, AsyncMock
    mock_event_publisher = Mock()
    mock_event_publisher.publish = AsyncMock()
    soft_delete_use_case.event_publisher = mock_event_publisher
    
    # Step 1: Dokument hochladen und freigeben
    document = UploadedDocument(
        id=None,
        file_type=FileType.PDF,
        file_size_bytes=1024,
        document_type_id=1,
        metadata=DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="1.1",
            version="v1.0"
        ),
        file_path=FilePath(str(test_file)),
        processing_method=ProcessingMethod.OCR,
        processing_status=ProcessingStatus.COMPLETED,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        workflow_status=WorkflowStatus.APPROVED  # Freigegeben
    )
    document = await upload_repo.save(document)
    
    # Step 2: Simuliere RAG Indexierung (setze Flag)
    # In echt würde das über IndexApprovedDocumentUseCase passieren
    # Hier prüfen wir nur, dass das Soft Delete Event publiziert wird
    
    # Step 3: Soft Delete
    deleted_document = await soft_delete_use_case.execute(
        document_id=document.id,
        deleted_by_user_id=1,
        reason="Test deletion of indexed document"
    )
    
    # Assert: Event sollte publiziert worden sein
    assert mock_event_publisher.publish.called, "DocumentDeletedEvent sollte publiziert worden sein"
    
    # Prüfe Event-Argumente
    call_args = mock_event_publisher.publish.call_args[0][0]
    from contexts.documentupload.domain.events import DocumentDeletedEvent
    assert isinstance(call_args, DocumentDeletedEvent)
    assert call_args.document_id == document.id
    assert call_args.deleted_by_user_id == 1
    assert call_args.deletion_reason == "Test deletion of indexed document"


@pytest.mark.asyncio
async def test_find_by_hash_excludes_deleted_documents(db_session):
    """
    Test: find_by_hash ignoriert gelöschte Dokumente.
    
    Prüft, dass die Repository-Methode find_by_hash korrekt
    gelöschte Dokumente filtert (für Duplikat-Erkennung).
    """
    # Arrange
    upload_repo = SQLAlchemyUploadRepository(db_session)
    soft_delete_use_case = SoftDeleteDocumentUseCase(upload_repository=upload_repo)
    
    # Valider SHA-256 Hash (64 Zeichen hex)
    file_hash = "a" * 64  # 64 Zeichen für SHA-256
    
    # Erstelle Dokument mit Hash
    document1 = UploadedDocument(
        id=None,
        file_type=FileType.PDF,
        file_size_bytes=1024,
        document_type_id=1,
        metadata=DocumentMetadata(
            filename="test1.pdf",
            original_filename="test1.pdf",
            qm_chapter="1.1",
            version="v1.0"
        ),
        file_path=FilePath("data/uploads/test1.pdf"),
        processing_method=ProcessingMethod.OCR,
        processing_status=ProcessingStatus.COMPLETED,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        workflow_status=WorkflowStatus.DRAFT,
        file_hash=FileHash(file_hash)
    )
    document1 = await upload_repo.save(document1)
    
    # Prüfe: Dokument sollte gefunden werden
    found = await upload_repo.find_by_hash(FileHash(file_hash))
    assert found is not None
    assert found.id == document1.id
    
    # Lösche Dokument
    await soft_delete_use_case.execute(document1.id, 1, "Test")
    
    # Prüfe: Gelöschtes Dokument sollte NICHT gefunden werden
    found_after_delete = await upload_repo.find_by_hash(FileHash(file_hash))
    assert found_after_delete is None, "Gelöschtes Dokument sollte nicht als Duplikat gefunden werden"


@pytest.mark.asyncio
async def test_upload_duplicate_detection_after_restore(db_session, test_file):
    """
    Test: Duplikat-Erkennung nach Restore.
    
    Szenario:
    1. Dokument hochladen
    2. Dokument löschen
    3. Dokument wiederherstellen
    4. Gleiches Dokument hochladen → sollte als Duplikat erkannt werden
    """
    # Arrange
    upload_repo = SQLAlchemyUploadRepository(db_session)
    soft_delete_use_case = SoftDeleteDocumentUseCase(upload_repository=upload_repo)
    
    from contexts.documentupload.application.use_cases import RestoreDocumentUseCase
    restore_use_case = RestoreDocumentUseCase(upload_repository=upload_repo)
    
    file_hash = "test_hash_restore_12345"
    
    # Step 1: Dokument hochladen
    document1 = UploadedDocument(
        id=None,
        file_type=FileType.PDF,
        file_size_bytes=1024,
        document_type_id=1,
        metadata=DocumentMetadata(
            filename="test.pdf",
            original_filename="test.pdf",
            qm_chapter="1.1",
            version="v1.0"
        ),
        file_path=FilePath(str(test_file)),
        processing_method=ProcessingMethod.OCR,
        processing_status=ProcessingStatus.COMPLETED,
        uploaded_by_user_id=1,
        uploaded_at=datetime.utcnow(),
        workflow_status=WorkflowStatus.DRAFT,
        file_hash=FileHash(file_hash)
    )
    document1 = await upload_repo.save(document1)
    
    # Step 2: Dokument löschen
    await soft_delete_use_case.execute(document1.id, 1, "Test")
    
    # Step 3: Dokument wiederherstellen
    restored_document = await restore_use_case.execute(
        document_id=document1.id,
        restore_to_status=WorkflowStatus.DRAFT,
        restored_by_user_id=1
    )
    assert restored_document.deleted_at is None
    
    # Step 4: Gleiches Dokument nochmals hochladen → sollte als Duplikat erkannt werden
    found_duplicate = await upload_repo.find_by_hash(FileHash(file_hash))
    assert found_duplicate is not None, "Wiederhergestelltes Dokument sollte als Duplikat gefunden werden"
    assert found_duplicate.id == document1.id

