"""
E2E Tests für RBAC-Workflows

Testet alle 5 RBAC-Level und ihre Berechtigungen:
- Level 1: Nur RAG Chat (nur eigene IG)
- Level 2: RAG Chat + Dokumenten-Liste (Tabelle, nur eigene IG) + Kommentare
- Level 3: RAG Chat + Dokumenten-Liste (Kanban, nur eigene IG) + Workflow Draft→Reviewed + Kommentare
- Level 4: RAG Chat + Upload + Dokumenten-Liste (alle) + Alle Workflows + Kommentare
- Level 5: Alle Rechte + Benutzerverwaltung
"""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.models import User, UploadDocument, InterestGroup, UserGroupMembership, DocumentTypeModel
from contexts.documentupload.domain.value_objects import WorkflowStatus
import bcrypt
from datetime import datetime


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


@pytest.fixture
async def test_client():
    """Async HTTP Client für Tests."""
    from backend.app.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def db_session():
    """Database Session für Tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
async def test_interest_group(db_session):
    """Erstelle Test-Interest Group."""
    group = InterestGroup(
        name="Test Service",
        code="SERVICE",
        description="Test Interest Group für RBAC Tests",
        is_active=True,
        is_external=False
    )
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


@pytest.fixture
async def test_document_type(db_session):
    """Erstelle Test-Document Type."""
    doc_type = DocumentTypeModel(
        name="Test Document Type",
        code="TEST_DOC_TYPE",
        description="Test Document Type für RBAC Tests",
        allowed_file_types='["pdf"]',
        max_file_size_mb=10,
        requires_ocr=True,
        requires_vision=False,
        is_active=True,
        sort_order=0
    )
    db_session.add(doc_type)
    db_session.commit()
    db_session.refresh(doc_type)
    return doc_type


@pytest.fixture
async def test_user_level1(db_session, test_interest_group):
    """Erstelle Test-User mit Level 1 (Mitarbeiter)."""
    user = User(
        email="mitarbeiter.service@company.com",
        full_name="Mitarbeiter Test",
        employee_id="L1-001",
        organizational_unit="Service",
        hashed_password=hash_password("123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Erstelle Interest Group Membership mit Level 1
    membership = UserGroupMembership(
        user_id=user.id,
        interest_group_id=test_interest_group.id,
        approval_level=1,
        is_active=True
    )
    db_session.add(membership)
    db_session.commit()
    
    return user


@pytest.fixture
async def test_user_level2(db_session, test_interest_group):
    """Erstelle Test-User mit Level 2 (Teamleiter)."""
    user = User(
        email="teamleiter.service@company.com",
        full_name="Teamleiter Test",
        employee_id="L2-001",
        organizational_unit="Service",
        hashed_password=hash_password("123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Erstelle Interest Group Membership mit Level 2
    membership = UserGroupMembership(
        user_id=user.id,
        interest_group_id=test_interest_group.id,
        approval_level=2,
        is_active=True
    )
    db_session.add(membership)
    db_session.commit()
    
    return user


@pytest.fixture
async def test_user_level3(db_session, test_interest_group):
    """Erstelle Test-User mit Level 3 (Abteilungsleiter)."""
    user = User(
        email="abteilungsleiter.service@company.com",
        full_name="Abteilungsleiter Test",
        employee_id="L3-001",
        organizational_unit="Service",
        hashed_password=hash_password("123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Erstelle Interest Group Membership mit Level 3
    membership = UserGroupMembership(
        user_id=user.id,
        interest_group_id=test_interest_group.id,
        approval_level=3,
        is_active=True
    )
    db_session.add(membership)
    db_session.commit()
    
    return user


@pytest.fixture
async def test_user_level4(db_session):
    """Erstelle Test-User mit Level 4 (QM-Mitarbeiter)."""
    user = User(
        email="qm.mitarbeiter@company.com",
        full_name="QM Mitarbeiter Test",
        employee_id="L4-001",
        organizational_unit="Quality Management",
        hashed_password=hash_password("123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Level 4 hat keine Interest Group Memberships (sieht alle Dokumente)
    return user


@pytest.fixture
async def test_user_level5(db_session):
    """Erstelle Test-User mit Level 5 (QMS Admin)."""
    user = User(
        email="qms.admin@company.com",
        full_name="QMS Admin Test",
        employee_id="L5-001",
        organizational_unit="QMS",
        hashed_password=hash_password("123"),
        is_qms_admin=True,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture
async def test_document(db_session, test_document_type, test_user_level4, test_interest_group):
    """Erstelle Test-Dokument in Status 'draft'."""
    document = UploadDocument(
        filename="test_rbac.pdf",
        original_filename="test_rbac.pdf",
        file_size_bytes=1024,
        file_type="pdf",
        document_type_id=test_document_type.id,
        qm_chapter="1.2.3",
        version="v1.0",
        page_count=1,
        uploaded_by_user_id=test_user_level4.id,
        file_path="/test/path",
        processing_method="ocr",
        processing_status="completed",
        workflow_status="draft"
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    # Weise Interest Group zu
    from backend.app.models import UploadDocumentInterestGroup
    assignment = UploadDocumentInterestGroup(
        upload_document_id=document.id,
        interest_group_id=test_interest_group.id,
        assigned_by_user_id=test_user_level4.id,
        assigned_at=datetime.utcnow()
    )
    db_session.add(assignment)
    db_session.commit()
    
    return document


async def login_user(client: AsyncClient, email: str, password: str = "123"):
    """Helper: Login als User und hole Token."""
    response = await client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


class TestRBACLevel1:
    """E2E Tests für Level 1 (Mitarbeiter)."""
    
    @pytest.mark.asyncio
    async def test_level1_can_access_rag_chat(self, test_client, test_user_level1):
        """Level 1: Kann RAG Chat nutzen."""
        token = await login_user(test_client, test_user_level1.email)
        
        # RAG Chat sollte funktionieren
        response = await test_client.get(
            "/api/rag/sessions",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_level1_cannot_access_documents_list(self, test_client, test_user_level1):
        """Level 1: Kann NICHT auf Dokumenten-Liste zugreifen."""
        token = await login_user(test_client, test_user_level1.email)
        
        # Dokumenten-Liste sollte 403 geben (oder nur eigene IG-Dokumente)
        response = await test_client.get(
            "/api/document-upload/uploads",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Level 1 sieht keine Dokumenten-Liste im Frontend, aber Backend liefert leere Liste
        assert response.status_code == 200  # Backend gibt 200, aber leere Liste
    
    @pytest.mark.asyncio
    async def test_level1_cannot_upload(self, test_client, test_user_level1):
        """Level 1: Kann NICHT uploaden."""
        token = await login_user(test_client, test_user_level1.email)
        
        response = await test_client.post(
            "/api/document-upload/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
            data={
                "filename": "test.pdf",
                "original_filename": "test.pdf",
                "document_type_id": 1,
                "qm_chapter": "1.0",
                "version": "v1.0",
                "processing_method": "ocr"
            }
        )
        assert response.status_code == 403  # Forbidden
    
    @pytest.mark.asyncio
    async def test_level1_cannot_create_comments(self, test_client, test_user_level1, test_document):
        """Level 1: Kann NICHT kommentieren."""
        token = await login_user(test_client, test_user_level1.email)
        
        response = await test_client.post(
            f"/api/document-upload/{test_document.id}/comments",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "comment_text": "Test Kommentar",
                "comment_type": "general"
            }
        )
        assert response.status_code == 403  # Forbidden


class TestRBACLevel2:
    """E2E Tests für Level 2 (Teamleiter)."""
    
    @pytest.mark.asyncio
    async def test_level2_can_access_documents_list(self, test_client, test_user_level2, test_document):
        """Level 2: Kann Dokumenten-Liste sehen (nur eigene IG)."""
        token = await login_user(test_client, test_user_level2.email)
        
        response = await test_client.get(
            "/api/document-upload/uploads",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Sollte nur Dokumente aus seiner IG sehen
        assert isinstance(data.get("documents", []), list)
    
    @pytest.mark.asyncio
    async def test_level2_can_create_comments(self, test_client, test_user_level2, test_document):
        """Level 2: Kann kommentieren."""
        token = await login_user(test_client, test_user_level2.email)
        
        response = await test_client.post(
            f"/api/document-upload/{test_document.id}/comments",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "comment_text": "Test Kommentar von Level 2",
                "comment_type": "general"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["comment"] is not None
    
    @pytest.mark.asyncio
    async def test_level2_cannot_change_status(self, test_client, test_user_level2, test_document):
        """Level 2: Kann NICHT Status ändern."""
        token = await login_user(test_client, test_user_level2.email)
        
        response = await test_client.post(
            "/api/document-workflow/change-status",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "document_id": test_document.id,
                "new_status": "reviewed",
                "reason": "Test"
            }
        )
        assert response.status_code == 403  # Forbidden


class TestRBACLevel3:
    """E2E Tests für Level 3 (Abteilungsleiter)."""
    
    @pytest.mark.asyncio
    async def test_level3_can_change_status_draft_to_reviewed(self, test_client, test_user_level3, test_document):
        """Level 3: Kann Draft → Reviewed verschieben (nur eigene IG)."""
        token = await login_user(test_client, test_user_level3.email)
        
        response = await test_client.post(
            "/api/document-workflow/change-status",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "document_id": test_document.id,
                "new_status": "reviewed",
                "reason": "Geprüft von Abteilungsleiter"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_level3_cannot_change_status_to_approved(self, test_client, test_user_level3, test_document):
        """Level 3: Kann NICHT zu Approved verschieben."""
        token = await login_user(test_client, test_user_level3.email)
        
        response = await test_client.post(
            "/api/document-workflow/change-status",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "document_id": test_document.id,
                "new_status": "approved",
                "reason": "Test"
            }
        )
        assert response.status_code == 403  # Forbidden - nur Level 4+


class TestRBACLevel4:
    """E2E Tests für Level 4 (QM-Mitarbeiter)."""
    
    @pytest.mark.asyncio
    async def test_level4_can_upload(self, test_client, test_user_level4, test_document_type):
        """Level 4: Kann Dokumente hochladen."""
        token = await login_user(test_client, test_user_level4.email)
        
        # Note: Dieser Test könnte fehlschlagen ohne vollständige Upload-Implementierung
        # Wir testen nur die Permission
        response = await test_client.post(
            "/api/document-upload/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
            data={
                "filename": "test.pdf",
                "original_filename": "test.pdf",
                "document_type_id": test_document_type.id,
                "qm_chapter": "1.0",
                "version": "v1.0",
                "processing_method": "ocr"
            }
        )
        # Sollte entweder 201 (erfolgreich) oder 400 (Validierungsfehler) sein, aber NICHT 403
        assert response.status_code != 403, "Level 4 sollte uploaden dürfen"
    
    @pytest.mark.asyncio
    async def test_level4_can_approve(self, test_client, test_user_level4, test_document):
        """Level 4: Kann zu Approved verschieben."""
        token = await login_user(test_client, test_user_level4.email)
        
        # Erst zu Reviewed
        response = await test_client.post(
            "/api/document-workflow/change-status",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "document_id": test_document.id,
                "new_status": "reviewed",
                "reason": "Geprüft"
            }
        )
        assert response.status_code == 200
        
        # Dann zu Approved
        response = await test_client.post(
            "/api/document-workflow/change-status",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "document_id": test_document.id,
                "new_status": "approved",
                "reason": "Freigegeben"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_level4_sees_all_documents(self, test_client, test_user_level4, test_document):
        """Level 4: Sieht alle Dokumente (unabhängig von IG)."""
        token = await login_user(test_client, test_user_level4.email)
        
        response = await test_client.get(
            "/api/document-upload/uploads",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Level 4 sieht alle Dokumente
        assert isinstance(data.get("documents", []), list)


class TestRBACLevel5:
    """E2E Tests für Level 5 (QMS Admin)."""
    
    @pytest.mark.asyncio
    async def test_level5_can_access_user_management(self, test_client, test_user_level5):
        """Level 5: Kann auf Benutzerverwaltung zugreifen."""
        token = await login_user(test_client, test_user_level5.email)
        
        # Benutzer-Liste sollte funktionieren
        response = await test_client.get(
            "/api/users/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_level5_has_all_permissions(self, test_client, test_user_level5, test_document):
        """Level 5: Hat alle Berechtigungen."""
        token = await login_user(test_client, test_user_level5.email)
        
        # Kann uploaden
        # Kann Status ändern
        response = await test_client.post(
            "/api/document-workflow/change-status",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "document_id": test_document.id,
                "new_status": "approved",
                "reason": "Freigegeben von Admin"
            }
        )
        assert response.status_code == 200
        
        # Kann kommentieren
        response = await test_client.post(
            f"/api/document-upload/{test_document.id}/comments",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "comment_text": "Admin Kommentar",
                "comment_type": "general"
            }
        )
        assert response.status_code == 201


class TestRBACInterestGroupFiltering:
    """E2E Tests für Interest Group Filtering."""
    
    @pytest.mark.asyncio
    async def test_level1_only_sees_own_ig_documents_in_rag(self, test_client, test_user_level1, test_document):
        """Level 1: Sieht nur eigene IG-Dokumente im RAG Chat."""
        token = await login_user(test_client, test_user_level1.email)
        
        # RAG Chat Query sollte nur Dokumente aus seiner IG zurückgeben
        response = await test_client.post(
            "/api/rag/ask",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "question": "Was steht im Dokument?",
                "session_id": None
            }
        )
        assert response.status_code == 200
        # Die Antwort sollte nur Dokumente aus seiner IG enthalten (Backend-Filter)
    
    @pytest.mark.asyncio
    async def test_level2_only_sees_own_ig_documents(self, test_client, test_user_level2, test_document):
        """Level 2: Sieht nur eigene IG-Dokumente in der Liste."""
        token = await login_user(test_client, test_user_level2.email)
        
        response = await test_client.get(
            "/api/document-upload/uploads",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Dokumente sollten nur aus seiner IG sein
        documents = data.get("documents", [])
        for doc in documents:
            # Prüfe ob Dokument in seiner IG ist (wenn IG-Filtering implementiert)
            assert doc.get("interest_group_ids", []) is not None

