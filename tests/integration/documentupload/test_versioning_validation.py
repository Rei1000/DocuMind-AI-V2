"""
Integration Tests für Dokument-Versionierung.

Testet, dass Versionierung korrekt funktioniert:
- Parent-Child Relationships
- document_series_id wird gesetzt
- is_current_version wird korrekt verwaltet
- Alte Versionen werden archiviert
"""

import pytest
import hashlib
from pathlib import Path
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.models import UploadDocument as UploadDocumentModel
from contexts.documentupload.infrastructure.repositories import SQLAlchemyUploadRepository
from contexts.documentupload.application.use_cases import UploadDocumentUseCase


@pytest.fixture
def db_session():
    """DB Session für Tests."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def upload_repo(db_session):
    """UploadRepository für Tests."""
    return SQLAlchemyUploadRepository(db_session)


@pytest.fixture
def use_case(upload_repo):
    """UploadDocumentUseCase für Tests."""
    return UploadDocumentUseCase(upload_repo)


@pytest.fixture
def test_file_v1(tmp_path):
    """Test-Datei Version 1."""
    content = b"Version 1.0 content"
    file = tmp_path / "doc_v1.pdf"
    file.write_bytes(content)
    return str(file), content


@pytest.fixture
def test_file_v2(tmp_path):
    """Test-Datei Version 2 (anderer Inhalt = anderer Hash)."""
    content = b"Version 2.0 content - updated"
    file = tmp_path / "doc_v2.pdf"
    file.write_bytes(content)
    return str(file), content


@pytest.mark.asyncio
async def test_first_version_creates_document_series(upload_repo, use_case, test_file_v1):
    """
    Test: Erste Version erstellt document_series_id (selbst als Serie).
    
    Erwartung:
    - document_series_id = eigene ID (nach Save)
    - parent_document_id = None
    - is_current_version = True
    """
    file_path, content = test_file_v1
    document_type_id = 1
    user_id = 1
    
    doc = None
    
    try:
        # Act: Erste Version hochladen
        doc = await use_case.execute(
            original_filename="doc_v1.pdf",
            file_size_bytes=len(content),
            document_type_id=document_type_id,
            qm_chapter="1.2",
            version="v1.0",
            file_path=file_path,
            processing_method="ocr",
            uploaded_by_user_id=user_id
        )
        
        # Assert: Version-Felder sind korrekt
        assert doc.id is not None
        assert doc.document_series_id == doc.id  # Nach Save: document_series_id = eigene ID
        assert doc.parent_document_id is None  # Erste Version hat keinen Parent
        assert doc.is_current_version is True
        
        # Verify in DB
        db = upload_repo.db
        db_doc = db.query(UploadDocumentModel).filter(
            UploadDocumentModel.id == doc.id
        ).first()
        
        assert db_doc.document_series_id == doc.id
        assert db_doc.parent_document_id is None
        assert db_doc.is_current_version is True
        
    finally:
        # Cleanup
        if doc and doc.id:
            db = upload_repo.db
            db.query(UploadDocumentModel).filter(UploadDocumentModel.id == doc.id).delete()
            db.commit()


@pytest.mark.asyncio
async def test_new_version_archives_old_version(upload_repo, use_case, test_file_v1, test_file_v2):
    """
    Test: Neue Version archiviert alte Version automatisch.
    
    Erwartung:
    - v1.0: is_current_version = False (nach v2.0 Upload)
    - v2.0: is_current_version = True
    - v2.0: parent_document_id = v1.0.id
    - v2.0: document_series_id = v1.0.document_series_id
    """
    file_v1, content_v1 = test_file_v1
    file_v2, content_v2 = test_file_v2
    
    document_type_id = 1
    user_id = 1
    qm_chapter = "1.2"
    
    doc_v1 = None
    doc_v2 = None
    
    try:
        # Act 1: Erste Version (v1.0)
        doc_v1 = await use_case.execute(
            original_filename="doc_v1.pdf",
            file_size_bytes=len(content_v1),
            document_type_id=document_type_id,
            qm_chapter=qm_chapter,
            version="v1.0",
            file_path=file_v1,
            processing_method="ocr",
            uploaded_by_user_id=user_id
        )
        
        # Verify v1.0 ist aktuell
        assert doc_v1.is_current_version is True
        original_series_id = doc_v1.document_series_id
        
        # Act 2: Neue Version (v2.0) - sollte v1.0 archivieren
        doc_v2 = await use_case.execute(
            original_filename="doc_v2.pdf",
            file_size_bytes=len(content_v2),
            document_type_id=document_type_id,
            qm_chapter=qm_chapter,  # Gleiches QM-Kapitel = gleiche Serie
            version="v2.0",
            file_path=file_v2,
            processing_method="ocr",
            uploaded_by_user_id=user_id
        )
        
        # Assert v2.0: Neue Version ist aktuell
        assert doc_v2.id is not None
        assert doc_v2.is_current_version is True
        assert doc_v2.parent_document_id == doc_v1.id
        assert doc_v2.document_series_id == original_series_id
        
        # Assert v1.0: Alte Version wurde archiviert
        # Lade v1.0 neu aus DB
        doc_v1_updated = await upload_repo.get_by_id(doc_v1.id)
        assert doc_v1_updated.is_current_version is False  # Archiviert!
        
        # Verify in DB
        db = upload_repo.db
        db_v1 = db.query(UploadDocumentModel).filter(
            UploadDocumentModel.id == doc_v1.id
        ).first()
        db_v2 = db.query(UploadDocumentModel).filter(
            UploadDocumentModel.id == doc_v2.id
        ).first()
        
        assert db_v1.is_current_version is False
        assert db_v2.is_current_version is True
        assert db_v2.parent_document_id == doc_v1.id
        assert db_v2.document_series_id == original_series_id
        
    finally:
        # Cleanup
        db = upload_repo.db
        if doc_v1 and doc_v1.id:
            db.query(UploadDocumentModel).filter(UploadDocumentModel.id == doc_v1.id).delete()
        if doc_v2 and doc_v2.id:
            db.query(UploadDocumentModel).filter(UploadDocumentModel.id == doc_v2.id).delete()
        db.commit()


@pytest.mark.asyncio
async def test_multiple_versions_chain_correctly(upload_repo, use_case, tmp_path):
    """
    Test: Mehrere Versionen werden korrekt verkettet.
    
    Erwartung:
    - v1.0: parent = None, series_id = v1.id
    - v2.0: parent = v1.id, series_id = v1.id
    - v3.0: parent = v2.id, series_id = v1.id
    - Nur v3.0: is_current_version = True
    """
    # Erstelle 3 Versionen mit unterschiedlichem Inhalt (für verschiedene Hashes)
    content_v1 = b"Version 1.0"
    content_v2 = b"Version 2.0 - updated"
    content_v3 = b"Version 3.0 - final"
    
    file_v1 = tmp_path / "doc_v1.pdf"
    file_v1.write_bytes(content_v1)
    
    file_v2 = tmp_path / "doc_v2.pdf"
    file_v2.write_bytes(content_v2)
    
    file_v3 = tmp_path / "doc_v3.pdf"
    file_v3.write_bytes(content_v3)
    
    document_type_id = 1
    user_id = 1
    qm_chapter = "1.2"
    
    doc_v1 = None
    doc_v2 = None
    doc_v3 = None
    
    try:
        # Act: Drei Versionen hochladen
        doc_v1 = await use_case.execute(
            original_filename="doc_v1.pdf",
            file_size_bytes=len(content_v1),
            document_type_id=document_type_id,
            qm_chapter=qm_chapter,
            version="v1.0",
            file_path=str(file_v1),
            processing_method="ocr",
            uploaded_by_user_id=user_id
        )
        
        doc_v2 = await use_case.execute(
            original_filename="doc_v2.pdf",
            file_size_bytes=len(content_v2),
            document_type_id=document_type_id,
            qm_chapter=qm_chapter,
            version="v2.0",
            file_path=str(file_v2),
            processing_method="ocr",
            uploaded_by_user_id=user_id
        )
        
        doc_v3 = await use_case.execute(
            original_filename="doc_v3.pdf",
            file_size_bytes=len(content_v3),
            document_type_id=document_type_id,
            qm_chapter=qm_chapter,
            version="v3.0",
            file_path=str(file_v3),
            processing_method="ocr",
            uploaded_by_user_id=user_id
        )
        
        # Assert: Version-Chain ist korrekt
        series_id = doc_v1.document_series_id
        
        # v1.0
        doc_v1_reloaded = await upload_repo.get_by_id(doc_v1.id)
        assert doc_v1_reloaded.parent_document_id is None
        assert doc_v1_reloaded.document_series_id == series_id
        assert doc_v1_reloaded.is_current_version is False  # Archiviert durch v2.0
        
        # v2.0
        doc_v2_reloaded = await upload_repo.get_by_id(doc_v2.id)
        assert doc_v2_reloaded.parent_document_id == doc_v1.id
        assert doc_v2_reloaded.document_series_id == series_id
        assert doc_v2_reloaded.is_current_version is False  # Archiviert durch v3.0
        
        # v3.0
        doc_v3_reloaded = await upload_repo.get_by_id(doc_v3.id)
        assert doc_v3_reloaded.parent_document_id == doc_v2.id
        assert doc_v3_reloaded.document_series_id == series_id
        assert doc_v3_reloaded.is_current_version is True  # Aktuelle Version!
        
    finally:
        # Cleanup
        db = upload_repo.db
        if doc_v1 and doc_v1.id:
            db.query(UploadDocumentModel).filter(UploadDocumentModel.id == doc_v1.id).delete()
        if doc_v2 and doc_v2.id:
            db.query(UploadDocumentModel).filter(UploadDocumentModel.id == doc_v2.id).delete()
        if doc_v3 and doc_v3.id:
            db.query(UploadDocumentModel).filter(UploadDocumentModel.id == doc_v3.id).delete()
        db.commit()


@pytest.mark.asyncio
async def test_different_document_types_create_separate_series(upload_repo, use_case, tmp_path):
    """
    Test: Verschiedene Dokumenttypen erzeugen separate Serien.
    
    Erwartung:
    - document_type_id=1, qm_chapter="1.2" → Serie A
    - document_type_id=2, qm_chapter="1.2" → Serie B (andere Serie, gleicher Chapter)
    """
    content = b"Test content"
    
    file1 = tmp_path / "doc1.pdf"
    file1.write_bytes(content)
    
    file2 = tmp_path / "doc2.pdf"
    file2.write_bytes(content)
    
    user_id = 1
    qm_chapter = "1.2"
    
    doc1 = None
    doc2 = None
    
    try:
        # Act: Zwei Dokumente mit verschiedenen document_type_id
        doc1 = await use_case.execute(
            original_filename="doc1.pdf",
            file_size_bytes=len(content),
            document_type_id=1,
            qm_chapter=qm_chapter,
            version="v1.0",
            file_path=str(file1),
            processing_method="ocr",
            uploaded_by_user_id=user_id
        )
        
        doc2 = await use_case.execute(
            original_filename="doc2.pdf",
            file_size_bytes=len(content),
            document_type_id=2,  # Anderer Dokumenttyp
            qm_chapter=qm_chapter,  # Gleicher Chapter
            version="v1.0",
            file_path=str(file2),
            processing_method="ocr",
            uploaded_by_user_id=user_id
        )
        
        # Assert: Verschiedene Serien (verschiedene document_type_id)
        assert doc1.document_series_id != doc2.document_series_id
        
    finally:
        # Cleanup
        db = upload_repo.db
        if doc1 and doc1.id:
            db.query(UploadDocumentModel).filter(UploadDocumentModel.id == doc1.id).delete()
        if doc2 and doc2.id:
            db.query(UploadDocumentModel).filter(UploadDocumentModel.id == doc2.id).delete()
        db.commit()


@pytest.mark.asyncio
async def test_repository_get_current_version_works(upload_repo, use_case, test_file_v1, test_file_v2):
    """
    Test: Repository get_current_version findet aktuelle Version korrekt.
    """
    file_v1, content_v1 = test_file_v1
    file_v2, content_v2 = test_file_v2
    
    document_type_id = 1
    user_id = 1
    qm_chapter = "1.2"
    
    doc_v1 = None
    doc_v2 = None
    
    try:
        # Act: Zwei Versionen hochladen
        doc_v1 = await use_case.execute(
            original_filename="doc_v1.pdf",
            file_size_bytes=len(content_v1),
            document_type_id=document_type_id,
            qm_chapter=qm_chapter,
            version="v1.0",
            file_path=file_v1,
            processing_method="ocr",
            uploaded_by_user_id=user_id
        )
        
        doc_v2 = await use_case.execute(
            original_filename="doc_v2.pdf",
            file_size_bytes=len(content_v2),
            document_type_id=document_type_id,
            qm_chapter=qm_chapter,
            version="v2.0",
            file_path=file_v2,
            processing_method="ocr",
            uploaded_by_user_id=user_id
        )
        
        # Assert: get_current_version findet v2.0
        current_version = await upload_repo.get_current_version(
            document_type_id=document_type_id,
            qm_chapter=qm_chapter
        )
        
        assert current_version is not None
        assert current_version.id == doc_v2.id
        assert current_version.is_current_version is True
        
    finally:
        # Cleanup
        db = upload_repo.db
        if doc_v1 and doc_v1.id:
            db.query(UploadDocumentModel).filter(UploadDocumentModel.id == doc_v1.id).delete()
        if doc_v2 and doc_v2.id:
            db.query(UploadDocumentModel).filter(UploadDocumentModel.id == doc_v2.id).delete()
        db.commit()

