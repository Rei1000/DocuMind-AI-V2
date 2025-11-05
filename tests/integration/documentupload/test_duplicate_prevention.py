"""
Integration Tests für Duplikat-Prävention.

Testet, dass keine Dokumente doppelt hochgeladen werden können.
"""

import pytest
import hashlib
import os
from pathlib import Path
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal, engine
from backend.app.models import UploadDocument as UploadDocumentModel
from contexts.documentupload.infrastructure.repositories import SQLAlchemyUploadRepository
from contexts.documentupload.application.use_cases import UploadDocumentUseCase
from contexts.documentupload.domain.value_objects import FileHash


@pytest.fixture
def db_session():
    """DB Session für Tests."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_file_content():
    """Test-Datei-Inhalt für Hash-Berechnung."""
    return b"This is a test document content for duplicate testing"


@pytest.fixture
def test_file_path(tmp_path, test_file_content):
    """Erstelle temporäre Test-Datei."""
    test_file = tmp_path / "test_duplicate.pdf"
    test_file.write_bytes(test_file_content)
    return str(test_file)


@pytest.fixture
def expected_hash(test_file_content):
    """Erwarteter SHA-256 Hash."""
    return hashlib.sha256(test_file_content).hexdigest()


@pytest.fixture
def upload_repo(db_session):
    """UploadRepository für Tests."""
    return SQLAlchemyUploadRepository(db_session)


@pytest.fixture
def use_case(upload_repo):
    """UploadDocumentUseCase für Tests."""
    return UploadDocumentUseCase(upload_repo)


@pytest.mark.asyncio
async def test_duplicate_document_prevented(upload_repo, use_case, test_file_path, expected_hash, test_file_content):
    """
    Test: Gleiches Dokument kann nicht zweimal hochgeladen werden.
    
    Erwartung:
    - Erster Upload: Erfolgreich, is_duplicate=False, file_hash gesetzt
    - Zweiter Upload: Wird als Duplikat erkannt, is_duplicate=True, duplicate_of_document_id gesetzt
    """
    # Arrange
    document_type_id = 1
    user_id = 1
    
    original_doc = None
    duplicate_doc = None
    
    try:
        # Act 1: Erster Upload (Original)
        original_doc = await use_case.execute(
            original_filename="test.pdf",
            file_size_bytes=len(test_file_content),
            document_type_id=document_type_id,
            qm_chapter="1.2",
            version="v1.0",
            file_path=test_file_path,
            processing_method="ocr",
            uploaded_by_user_id=user_id
        )
        
        # Assert 1: Original ist kein Duplikat
        assert original_doc.id is not None
        assert original_doc.is_duplicate is False
        assert original_doc.duplicate_of_document_id is None
        assert original_doc.file_hash is not None
        assert original_doc.file_hash.value == expected_hash
        
        # Act 2: Zweiter Upload (gleiche Datei = Duplikat)
        duplicate_doc = await use_case.execute(
            original_filename="test_copy.pdf",  # Anderer Name, aber gleicher Inhalt
            file_size_bytes=len(test_file_content),
            document_type_id=document_type_id,
            qm_chapter="1.2",
            version="v1.0",
            file_path=test_file_path,  # Gleicher Pfad = gleicher Hash
            processing_method="ocr",
            uploaded_by_user_id=user_id
        )
        
        # Assert 2: Duplikat wurde erkannt
        assert duplicate_doc.id is not None
        assert duplicate_doc.id != original_doc.id  # Neue ID (Upload wurde nicht blockiert, nur markiert)
        assert duplicate_doc.is_duplicate is True
        assert duplicate_doc.duplicate_of_document_id == original_doc.id
        # WICHTIG: Duplikat hat file_hash=None (verhindert UNIQUE Constraint)
        assert duplicate_doc.file_hash is None
        
        # Verify in DB
        db = upload_repo.db
        original_db = db.query(UploadDocumentModel).filter(
            UploadDocumentModel.id == original_doc.id
        ).first()
        duplicate_db = db.query(UploadDocumentModel).filter(
            UploadDocumentModel.id == duplicate_doc.id
        ).first()
        
        assert original_db.is_duplicate is False
        assert original_db.file_hash == expected_hash
        assert duplicate_db.is_duplicate is True
        assert duplicate_db.duplicate_of_document_id == original_doc.id
        assert duplicate_db.file_hash is None  # Duplikat hat keinen Hash (UNIQUE Constraint)
        
    finally:
        # Cleanup
        db = upload_repo.db
        if original_doc and original_doc.id:
            db.query(UploadDocumentModel).filter(UploadDocumentModel.id == original_doc.id).delete()
        if duplicate_doc and duplicate_doc.id:
            db.query(UploadDocumentModel).filter(UploadDocumentModel.id == duplicate_doc.id).delete()
        db.commit()


@pytest.mark.asyncio
async def test_different_documents_not_marked_as_duplicate(upload_repo, use_case, tmp_path):
    """
    Test: Verschiedene Dokumente werden nicht als Duplikate markiert.
    
    Erwartung:
    - Beide Uploads: Erfolgreich, is_duplicate=False
    - Verschiedene file_hash Werte
    """
    # Arrange
    content1 = b"First document content"
    content2 = b"Second different document content"
    
    file1 = tmp_path / "doc1.pdf"
    file1.write_bytes(content1)
    
    file2 = tmp_path / "doc2.pdf"
    file2.write_bytes(content2)
    
    hash1 = hashlib.sha256(content1).hexdigest()
    hash2 = hashlib.sha256(content2).hexdigest()
    
    document_type_id = 1
    user_id = 1
    
    doc1 = None
    doc2 = None
    
    try:
        # Act: Zwei verschiedene Dokumente hochladen
        doc1 = await use_case.execute(
            original_filename="doc1.pdf",
            file_size_bytes=len(content1),
            document_type_id=document_type_id,
            qm_chapter="1.2",
            version="v1.0",
            file_path=str(file1),
            processing_method="ocr",
            uploaded_by_user_id=user_id
        )
        
        doc2 = await use_case.execute(
            original_filename="doc2.pdf",
            file_size_bytes=len(content2),
            document_type_id=document_type_id,
            qm_chapter="1.3",
            version="v1.0",
            file_path=str(file2),
            processing_method="ocr",
            uploaded_by_user_id=user_id
        )
        
        # Assert: Beide sind keine Duplikate
        assert doc1.is_duplicate is False
        assert doc1.duplicate_of_document_id is None
        assert doc1.file_hash.value == hash1
        
        assert doc2.is_duplicate is False
        assert doc2.duplicate_of_document_id is None
        assert doc2.file_hash.value == hash2
        
        assert doc1.file_hash.value != doc2.file_hash.value
        
    finally:
        # Cleanup
        db = upload_repo.db
        if doc1 and doc1.id:
            db.query(UploadDocumentModel).filter(UploadDocumentModel.id == doc1.id).delete()
        if doc2 and doc2.id:
            db.query(UploadDocumentModel).filter(UploadDocumentModel.id == doc2.id).delete()
        db.commit()


@pytest.mark.asyncio
async def test_repository_find_by_hash_works(upload_repo, test_file_path, expected_hash, test_file_content):
    """
    Test: Repository find_by_hash findet Dokumente korrekt.
    """
    use_case = UploadDocumentUseCase(upload_repo)
    document_type_id = 1
    user_id = 1
    
    doc = None
    
    try:
        # Act: Dokument hochladen
        doc = await use_case.execute(
            original_filename="test.pdf",
            file_size_bytes=len(test_file_content),
            document_type_id=document_type_id,
            qm_chapter="1.2",
            version="v1.0",
            file_path=test_file_path,
            processing_method="ocr",
            uploaded_by_user_id=user_id
        )
        
        # Assert: find_by_hash findet das Dokument
        file_hash = FileHash(expected_hash)
        found_doc = await upload_repo.find_by_hash(file_hash)
        
        assert found_doc is not None
        assert found_doc.id == doc.id
        assert found_doc.file_hash.value == expected_hash
        
    finally:
        # Cleanup
        if doc and doc.id:
            db = upload_repo.db
            db.query(UploadDocumentModel).filter(UploadDocumentModel.id == doc.id).delete()
            db.commit()


@pytest.mark.asyncio
async def test_hash_calculation_is_consistent(upload_repo, use_case, test_file_path, expected_hash, test_file_content):
    """
    Test: Hash-Berechnung ist konsistent (gleicher Inhalt = gleicher Hash).
    """
    document_type_id = 1
    user_id = 1
    
    doc = None
    
    try:
        # Act: Dokument hochladen
        doc = await use_case.execute(
            original_filename="test.pdf",
            file_size_bytes=len(test_file_content),
            document_type_id=document_type_id,
            qm_chapter="1.2",
            version="v1.0",
            file_path=test_file_path,
            processing_method="ocr",
            uploaded_by_user_id=user_id
        )
        
        # Assert: Hash ist korrekt (SHA-256 von Datei-Inhalt)
        assert doc.file_hash is not None
        assert doc.file_hash.value == expected_hash
        assert len(doc.file_hash.value) == 64  # SHA-256 = 64 hex Zeichen
        
    finally:
        # Cleanup
        if doc and doc.id:
            db = upload_repo.db
            db.query(UploadDocumentModel).filter(UploadDocumentModel.id == doc.id).delete()
            db.commit()

