"""
E2E Tests für Archive API Endpoint.

Test-Driven Development: RED Phase für Archive API-Tests.
"""

import pytest
import httpx
from datetime import datetime

from backend.app.main import app
from backend.app.database import SessionLocal, engine
from backend.app import models as db_models
from contexts.accesscontrol.infrastructure.repositories import SQLAlchemyUserRepository
from contexts.accesscontrol.domain.services import PasswordService


@pytest.fixture(scope="function")
def db_session():
    """Database Session für Tests."""
    # Erstelle Tabellen
    db_models.Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    # Cleanup
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Erstelle Test-User für Authentifizierung."""
    user_repo = SQLAlchemyUserRepository(db_session)
    password_service = PasswordService()
    
    # Erstelle User
    user = db_models.User(
        email="test.archive@company.com",
        password_hash=password_service.hash_password("test123"),
        full_name="Test Archive User",
        department="IT"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
def test_document_type(db_session):
    """Erstelle Test Document Type."""
    doc_type = db_models.DocumentTypeModel(
        name="Test Type",
        qm_chapter="1.2"
    )
    db_session.add(doc_type)
    db_session.commit()
    db_session.refresh(doc_type)
    return doc_type


@pytest.fixture(scope="function")
def test_document(db_session, test_user, test_document_type):
    """Erstelle Test-Dokument für Archive-Tests."""
    doc = db_models.UploadDocument(
        file_type="pdf",
        file_size_bytes=1024,
        document_type_id=test_document_type.id,
        filename="test.pdf",
        original_filename="test.pdf",
        qm_chapter="1.2",
        version="v1.0",
        file_path="data/uploads/test.pdf",
        processing_method="ocr",
        processing_status="completed",
        uploaded_by_user_id=test_user.id,
        uploaded_at=datetime.utcnow(),
        workflow_status="approved"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc


@pytest.fixture(scope="function")
def test_client(db_session, test_user):
    """Test-Client mit Authentifizierung."""
    from contexts.accesscontrol.application.auth_login_service import AuthLoginService
    from contexts.accesscontrol.infrastructure.repositories import SQLAlchemyUserRepository
    
    # Login um Token zu erhalten
    user_repo = SQLAlchemyUserRepository(db_session)
    auth_service = AuthLoginService(user_repository=user_repo)
    token = auth_service.login("test.archive@company.com", "test123")
    
    # Client mit Token
    client = httpx.AsyncClient(app=app, base_url="http://test")
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.mark.asyncio
async def test_archive_document_success(test_client, test_document):
    """Archive Endpoint erfolgreich archiviert Dokument"""
    # Arrange
    request_data = {
        "document_id": test_document.id,
        "archive_reason": "Old version"
    }
    
    # Act
    response = await test_client.post("/api/document-workflow/archive", json=request_data)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Document archived successfully"
    assert data["document_id"] == test_document.id
    assert data["new_status"] == "archived"
    assert data["archived_by"] is not None
    assert data["archived_at"] is not None


@pytest.mark.asyncio
async def test_archive_document_not_found(test_client):
    """Archive Endpoint wirft Fehler wenn Dokument nicht existiert"""
    # Arrange
    request_data = {
        "document_id": 99999,
        "archive_reason": "Old version"
    }
    
    # Act
    response = await test_client.post("/api/document-workflow/archive", json=request_data)
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_archive_document_empty_reason_allowed(test_client, test_document):
    """Archive Endpoint erlaubt leeren reason (optional im Gegensatz zu Soft Delete)"""
    # Arrange
    request_data = {
        "document_id": test_document.id,
        "archive_reason": ""  # Leer erlaubt
    }
    
    # Act
    response = await test_client.post("/api/document-workflow/archive", json=request_data)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

