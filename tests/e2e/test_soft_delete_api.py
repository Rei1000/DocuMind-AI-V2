"""
E2E Tests für Soft Delete API Endpoint.

Test-Driven Development: RED Phase für Soft Delete API.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.models import UploadDocument as UploadDocumentModel, User


@pytest.fixture
async def test_client():
    """Async HTTP Client für Tests."""
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def qms_admin_token(test_client: AsyncClient):
    """Token für QMS Admin User."""
    # Login als QMS Admin
    response = await test_client.post(
        "/api/auth/login",
        json={
            "email": "qms.admin@company.com",
            "password": "123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return token


@pytest.fixture
async def authenticated_client(test_client: AsyncClient, qms_admin_token):
    """Client mit Authentication Header."""
    test_client.headers.update({"Authorization": f"Bearer {qms_admin_token}"})
    return test_client


@pytest.mark.asyncio
async def test_soft_delete_document_endpoint(authenticated_client: AsyncClient):
    """API Endpoint für Soft Delete"""
    # Arrange: Erstelle Test-Dokument (vereinfacht - ohne vollständigen Upload)
    db = SessionLocal()
    try:
        # Hole QMS Admin User
        user = db.query(User).filter(User.email == "qms.admin@company.com").first()
        if not user:
            pytest.skip("QMS Admin User nicht gefunden")
        
        # Erstelle Test-Dokument direkt in DB
        test_document = UploadDocumentModel(
            filename="test_soft_delete.pdf",
            original_filename="test_soft_delete.pdf",
            file_size_bytes=1024,
            file_type="pdf",
            document_type_id=1,
            qm_chapter="1.2",
            version="v1.0",
            page_count=1,
            uploaded_by_user_id=user.id,
            file_path="data/uploads/test_soft_delete.pdf",
            processing_method="ocr",
            processing_status="completed",
            workflow_status="approved"
        )
        db.add(test_document)
        db.commit()
        db.refresh(test_document)
        document_id = test_document.id
    finally:
        db.close()
    
    # Act: Soft Delete
    response = await authenticated_client.post(
        "/api/document-workflow/soft-delete",
        json={
            "document_id": document_id,
            "deletion_reason": "Test deletion via API"
        }
    )
    
    # Assert
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["document"]["workflow_status"] == "deleted"
    assert result["document"]["deleted_at"] is not None
    assert result["document"]["deleted_by_user_id"] == user.id
    assert result["document"]["deletion_reason"] == "Test deletion via API"
    
    # Cleanup: Lösche Test-Dokument aus DB
    db = SessionLocal()
    try:
        db.query(UploadDocumentModel).filter(UploadDocumentModel.id == document_id).delete()
        db.commit()
    finally:
        db.close()


@pytest.mark.asyncio
async def test_soft_delete_document_not_found(authenticated_client: AsyncClient):
    """Soft Delete wirft 404 wenn Dokument nicht gefunden"""
    # Act
    response = await authenticated_client.post(
        "/api/document-workflow/soft-delete",
        json={
            "document_id": 999999,  # Nicht existierende ID
            "deletion_reason": "Test deletion"
        }
    )
    
    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_soft_delete_document_empty_reason(authenticated_client: AsyncClient):
    """Soft Delete wirft 400 wenn reason leer ist"""
    # Arrange: Erstelle Test-Dokument
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "qms.admin@company.com").first()
        if not user:
            pytest.skip("QMS Admin User nicht gefunden")
        
        test_document = UploadDocumentModel(
            filename="test.pdf",
            original_filename="test.pdf",
            file_size_bytes=1024,
            file_type="pdf",
            document_type_id=1,
            qm_chapter="1.2",
            version="v1.0",
            page_count=1,
            uploaded_by_user_id=user.id,
            file_path="data/uploads/test.pdf",
            processing_method="ocr",
            processing_status="completed",
            workflow_status="approved"
        )
        db.add(test_document)
        db.commit()
        db.refresh(test_document)
        document_id = test_document.id
    finally:
        db.close()
    
    # Act
    response = await authenticated_client.post(
        "/api/document-workflow/soft-delete",
        json={
            "document_id": document_id,
            "deletion_reason": ""  # Leer
        }
    )
    
    # Assert
    assert response.status_code == 400
    
    # Cleanup
    db = SessionLocal()
    try:
        db.query(UploadDocumentModel).filter(UploadDocumentModel.id == document_id).delete()
        db.commit()
    finally:
        db.close()

