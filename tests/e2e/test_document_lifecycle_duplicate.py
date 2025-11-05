"""
E2E Tests für Document Lifecycle - Duplikat-Prüfung.

Test-Driven Development: RED Phase für Duplikat-Erkennung im Upload-Endpoint.
"""

import pytest
from httpx import AsyncClient
from backend.app.database import SessionLocal
from backend.app.models import UploadDocument as UploadDocumentModel
import os


@pytest.fixture
async def test_client():
    """Async HTTP Client für Tests."""
    from backend.app.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def qms_admin_token(test_client):
    """Login als QMS Admin und hole Token."""
    async for client in test_client:
        response = await client.post("/api/auth/login", json={
            "email": "qms.admin@company.com",
            "password": "123"
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        yield token


@pytest.mark.asyncio
async def test_upload_includes_file_hash(test_client, qms_admin_token):
    """Upload-Endpoint berechnet und liefert File Hash"""
    # Arrange
    file_content = b"test document content for hash test"
    test_file_path = "data/uploads/test_hash.pdf"
    
    os.makedirs("data/uploads", exist_ok=True)
    with open(test_file_path, "wb") as f:
        f.write(file_content)
    
    import hashlib
    expected_hash = hashlib.sha256(file_content).hexdigest()
    
    doc_id = None
    
    try:
        async for client in test_client:
            async for token in qms_admin_token:
                headers = {"Authorization": f"Bearer {token}"}
                with open(test_file_path, "rb") as file:
                    files = {"file": ("test.pdf", file.read(), "application/pdf")}
                    data = {
                        "filename": "test.pdf",
                        "original_filename": "test.pdf",
                        "document_type_id": 1,
                        "qm_chapter": "1.2",
                        "version": "v1.0"
                    }
                    
                    response = await client.post(
                        "/api/documents/upload",
                        files=files,
                        data=data,
                        headers=headers
                    )
                
                # Assert
                assert response.status_code == 200
                result = response.json()
                doc_id = result["document"]["id"]
                assert "file_hash" in result["document"]
                assert len(result["document"]["file_hash"]) == 64  # SHA-256 = 64 hex chars
                assert result["document"]["file_hash"] == expected_hash
                break
            break
    
    finally:
        # Cleanup
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        
        # Lösche Dokument aus DB
        if doc_id:
            db = SessionLocal()
            try:
                db.query(UploadDocumentModel).filter(UploadDocumentModel.id == doc_id).delete()
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()
