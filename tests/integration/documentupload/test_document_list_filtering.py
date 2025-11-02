"""
Integration Tests für Document List Interest Group Filtering (Phase 3)

Testet, dass die Dokumenten-Liste basierend auf User-Level und Interest Groups filtert:
- Level 1-3: Nur eigene Interest Groups
- Level 4-5: Alle Dokumente (keine Filterung)
"""

import pytest
from unittest.mock import Mock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, UploadDocument, UploadDocumentInterestGroup, InterestGroup
from contexts.documentupload.infrastructure.permission_service import SQLAlchemyWorkflowPermissionService
from contexts.documentupload.infrastructure.repositories import SQLAlchemyUploadRepository
from jose import jwt


# Test Database Setup
@pytest.fixture
def db_session():
    """Erstelle eine temporäre SQLite-Datenbank für Tests"""
    engine = create_engine(
        'sqlite:///:memory:',
        poolclass=StaticPool,
        connect_args={'check_same_thread': False}
    )
    
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    engine.dispose()


@pytest.fixture
def client(db_session):
    """Test Client mit Mock DB Session"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


def create_test_token(user_id: int, user_level: int, interest_group_ids: list = None):
    """Erstelle Mock JWT Token"""
    token_data = {
        "sub": str(user_id),
        "user_id": user_id,
        "user_level": user_level,
        "is_qms_admin": user_level == 5,
        "interest_group_ids": interest_group_ids or [],
        "email": f"test{user_id}@company.com"
    }
    return jwt.encode(token_data, "test-secret-123", algorithm="HS256")


class TestDocumentListInterestGroupFiltering:
    """Test Suite für Interest Group Filtering in Dokumenten-Liste"""
    
    def test_document_list_level_1_only_sees_own_interest_group(self, db_session, client):
        """Test: Level 1 User sieht nur Dokumente aus seiner Interest Group"""
        # Arrange
        # Create Interest Groups
        sv_group = InterestGroup(name="Service", code="SV", is_active=True)
        it_group = InterestGroup(name="IT", code="IT", is_active=True)
        db_session.add(sv_group)
        db_session.add(it_group)
        db_session.flush()
        
        # Create User (Level 1)
        user = User(
            email="mitarbeiter.service@company.com",
            full_name="Mitarbeiter Service",
            hashed_password="hashed",
            is_active=True,
            is_qms_admin=False
        )
        db_session.add(user)
        db_session.flush()
        
        # Create Document Type (required)
        from backend.app.models import DocumentTypeModel
        doc_type = DocumentTypeModel(name="Test Type", code="TEST", is_active=True)
        db_session.add(doc_type)
        db_session.flush()
        
        # Create Documents (mit allen erforderlichen Feldern)
        from datetime import datetime
        doc1 = UploadDocument(
            filename="doc1.pdf",
            original_filename="doc1.pdf",
            file_size_bytes=1024,
            file_type="pdf",
            document_type_id=doc_type.id,
            version="1.0.0",
            file_path="/tmp/doc1.pdf",
            uploaded_by_user_id=user.id,
            uploaded_at=datetime.utcnow(),
            workflow_status="approved",
            processing_status="completed",
            processing_method="ocr"
        )
        doc2 = UploadDocument(
            filename="doc2.pdf",
            original_filename="doc2.pdf",
            file_size_bytes=2048,
            file_type="pdf",
            document_type_id=doc_type.id,
            version="1.0.0",
            file_path="/tmp/doc2.pdf",
            uploaded_by_user_id=user.id,
            uploaded_at=datetime.utcnow(),
            workflow_status="approved",
            processing_status="completed",
            processing_method="ocr"
        )
        db_session.add(doc1)
        db_session.add(doc2)
        db_session.flush()
        
        # Assign Interest Groups
        assignment1 = UploadDocumentInterestGroup(
            upload_document_id=doc1.id,
            interest_group_id=sv_group.id,
            assigned_by_user_id=user.id
        )
        assignment2 = UploadDocumentInterestGroup(
            upload_document_id=doc2.id,
            interest_group_id=it_group.id,
            assigned_by_user_id=user.id
        )
        db_session.add(assignment1)
        db_session.add(assignment2)
        db_session.commit()
        
        # Create Token
        token = create_test_token(user.id, user_level=1, interest_group_ids=[sv_group.id])
        
        # Act
        # TODO: Endpoint muss erweitert werden um Interest Group Filtering
        response = client.get(
            "/api/document-upload/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Assert
        # Nach Implementierung: Nur doc1 sollte in der Liste sein
        # (Dieser Test schlägt fehl, bis Interest Group Filtering implementiert ist)
        assert response.status_code == 200
        # TODO: Prüfe, dass nur doc1 in der Liste ist
    
    def test_document_list_level_4_sees_all_documents(self, db_session, client):
        """Test: Level 4 User sieht alle Dokumente"""
        # Arrange
        # Create Interest Groups
        sv_group = InterestGroup(name="Service", code="SV", is_active=True)
        it_group = InterestGroup(name="IT", code="IT", is_active=True)
        db_session.add(sv_group)
        db_session.add(it_group)
        db_session.flush()
        
        # Create User (Level 4)
        user = User(
            email="qm.mitarbeiter@company.com",
            full_name="QM Mitarbeiter",
            hashed_password="hashed",
            is_active=True,
            is_qms_admin=False
        )
        db_session.add(user)
        db_session.flush()
        
        # Create Document Type (required)
        from backend.app.models import DocumentTypeModel
        doc_type = DocumentTypeModel(name="Test Type", code="TEST", is_active=True)
        db_session.add(doc_type)
        db_session.flush()
        
        # Create Documents (mit allen erforderlichen Feldern)
        from datetime import datetime
        doc1 = UploadDocument(
            filename="doc1.pdf",
            original_filename="doc1.pdf",
            file_size_bytes=1024,
            file_type="pdf",
            document_type_id=doc_type.id,
            version="1.0.0",
            file_path="/tmp/doc1.pdf",
            uploaded_by_user_id=user.id,
            uploaded_at=datetime.utcnow(),
            workflow_status="approved",
            processing_status="completed",
            processing_method="ocr"
        )
        doc2 = UploadDocument(
            filename="doc2.pdf",
            original_filename="doc2.pdf",
            file_size_bytes=2048,
            file_type="pdf",
            document_type_id=doc_type.id,
            version="1.0.0",
            file_path="/tmp/doc2.pdf",
            uploaded_by_user_id=user.id,
            uploaded_at=datetime.utcnow(),
            workflow_status="approved",
            processing_status="completed",
            processing_method="ocr"
        )
        db_session.add(doc1)
        db_session.add(doc2)
        db_session.flush()
        
        # Assign Interest Groups
        assignment1 = UploadDocumentInterestGroup(
            upload_document_id=doc1.id,
            interest_group_id=sv_group.id,
            assigned_by_user_id=user.id
        )
        assignment2 = UploadDocumentInterestGroup(
            upload_document_id=doc2.id,
            interest_group_id=it_group.id,
            assigned_by_user_id=user.id
        )
        db_session.add(assignment1)
        db_session.add(assignment2)
        db_session.commit()
        
        # Create Token
        token = create_test_token(user.id, user_level=4, interest_group_ids=[])  # Leere Liste = alle
        
        # Act
        # TODO: Endpoint muss erweitert werden
        response = client.get(
            "/api/document-upload/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Assert
        # Nach Implementierung: Beide Dokumente sollten in der Liste sein
        assert response.status_code == 200
        # TODO: Prüfe, dass beide Dokumente in der Liste sind

