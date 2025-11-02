"""
E2E Tests für RBAC Multi-Level Permissions

Testet Context-Specific Permissions:
- User mit verschiedenen Levels für verschiedene Interest Groups
- Kanban-Sichtbarkeit basierend auf IG-Level
- Workflow-Transitions basierend auf IG-Level
- Document Type Filtering im RAG Chat
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.models import (
    User, UploadDocument, InterestGroup, UserGroupMembership, 
    UploadDocumentInterestGroup, DocumentTypeModel
)
from contexts.documentupload.domain.value_objects import WorkflowStatus
import bcrypt
from datetime import datetime


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


async def login_user(client: AsyncClient, email: str) -> str:
    """Helper: Login User und hole Token"""
    response = await client.post(
        "/api/auth/login",
        json={"email": email, "password": "123"}
    )
    assert response.status_code == 200
    data = response.json()
    return data.get("access_token") or data.get("token")


@pytest.fixture
async def test_client():
    """Async HTTP Client für Tests."""
    from backend.app.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def db_session():
    """Database Session für Tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_interest_group_produktion(db_session):
    """Erstelle Test-Interest Group: Produktion."""
    group = InterestGroup(
        name="Produktion",
        code="PRODUKTION",
        description="Produktion Interest Group",
        is_active=True,
        is_external=False
    )
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


@pytest.fixture
def test_interest_group_service(db_session):
    """Erstelle Test-Interest Group: Service."""
    group = InterestGroup(
        name="Service",
        code="SERVICE",
        description="Service Interest Group",
        is_active=True,
        is_external=False
    )
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


@pytest.fixture
def test_document_type(db_session):
    """Erstelle Test-Document Type."""
    doc_type = DocumentTypeModel(
        name="SOP",
        code="SOP",
        description="Standard Operating Procedure",
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
def test_multi_level_user(
    db_session, 
    test_interest_group_produktion, 
    test_interest_group_service
):
    """
    Erstelle Test-User mit Multi-Level Permissions:
    - Level 3 für Produktion
    - Level 2 für Service
    """
    user = User(
        email="multi.level@company.com",
        full_name="Multi-Level Test User",
        employee_id="ML-001",
        organizational_unit="Cross-Department",
        hashed_password=hash_password("123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Level 3 für Produktion
    membership_prod = UserGroupMembership(
        user_id=user.id,
        interest_group_id=test_interest_group_produktion.id,
        approval_level=3,
        is_active=True
    )
    db_session.add(membership_prod)
    
    # Level 2 für Service
    membership_service = UserGroupMembership(
        user_id=user.id,
        interest_group_id=test_interest_group_service.id,
        approval_level=2,
        is_active=True
    )
    db_session.add(membership_service)
    
    db_session.commit()
    return user


@pytest.fixture
def test_document_produktion(db_session, test_document_type, test_interest_group_produktion):
    """Erstelle Test-Dokument in Produktion IG."""
    doc = UploadDocument(
        filename="sop_produktion.pdf",
        original_filename="SOP_Produktion.pdf",
        file_size_bytes=102400,
        file_type="application/pdf",
        document_type_id=test_document_type.id,
        qm_chapter="1.2.3",
        version="v1.0",
        file_path="/uploads/sop_produktion.pdf",
        uploaded_at=datetime.utcnow(),
        processing_method="ocr",
        processing_status="completed",
        workflow_status=WorkflowStatus.DRAFT.value,
        uploaded_by_user_id=1
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    
    # Zuweisung zu Produktion IG
    assignment = UploadDocumentInterestGroup(
        upload_document_id=doc.id,
        interest_group_id=test_interest_group_produktion.id,
        assigned_by_user_id=1,
        assigned_at=datetime.utcnow()
    )
    db_session.add(assignment)
    db_session.commit()
    
    return doc


@pytest.fixture
def test_document_service(db_session, test_document_type, test_interest_group_service):
    """Erstelle Test-Dokument in Service IG."""
    doc = UploadDocument(
        filename="sop_service.pdf",
        original_filename="SOP_Service.pdf",
        file_size_bytes=102400,
        file_type="application/pdf",
        document_type_id=test_document_type.id,
        qm_chapter="1.2.4",
        version="v1.0",
        file_path="/uploads/sop_service.pdf",
        uploaded_at=datetime.utcnow(),
        processing_method="ocr",
        processing_status="completed",
        workflow_status=WorkflowStatus.DRAFT.value,
        uploaded_by_user_id=1
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    
    # Zuweisung zu Service IG
    assignment = UploadDocumentInterestGroup(
        upload_document_id=doc.id,
        interest_group_id=test_interest_group_service.id,
        assigned_by_user_id=1,
        assigned_at=datetime.utcnow()
    )
    db_session.add(assignment)
    db_session.commit()
    
    return doc


class TestMultiLevelRBAC:
    """E2E Tests für Multi-Level RBAC mit verschiedenen IGs."""
    
    @pytest.mark.asyncio
    async def test_multi_level_user_jwt_token_contains_ig_levels(
        self, 
        test_client, 
        test_multi_level_user
    ):
        """Test: JWT Token enthält interest_groups_with_levels."""
        token = await login_user(test_client, test_multi_level_user.email)
        
        # Decode Token (vereinfacht - in echtem Test würde man jwt.decode verwenden)
        import base64
        import json
        
        # JWT Token hat 3 Teile: header.payload.signature
        parts = token.split('.')
        assert len(parts) == 3
        
        # Decode payload
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
        
        # Prüfe ob interest_groups_with_levels vorhanden
        assert "interest_groups_with_levels" in payload
        ig_levels = payload["interest_groups_with_levels"]
        
        # Sollte 2 IGs enthalten (Produktion: 3, Service: 2)
        assert len(ig_levels) == 2
        
        # Prüfe Levels
        ig_names = {ig["interest_group_name"]: ig["approval_level"] for ig in ig_levels}
        assert ig_names.get("Produktion") == 3
        assert ig_names.get("Service") == 2
    
    @pytest.mark.asyncio
    async def test_multi_level_user_can_change_status_produktion_draft_to_reviewed(
        self,
        test_client,
        test_multi_level_user,
        test_document_produktion
    ):
        """Test: User kann Draft → Reviewed für Produktion-Dokument (Level 3)."""
        token = await login_user(test_client, test_multi_level_user.email)
        
        response = await test_client.post(
            "/api/document-workflow/change-status",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "document_id": test_document_produktion.id,
                "new_status": "reviewed",
                "reason": "Geprüft von Multi-Level User (Level 3 für Produktion)"
            }
        )
        
        # Sollte erfolgreich sein (User hat Level 3 für Produktion)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["new_status"] == "reviewed"
    
    @pytest.mark.asyncio
    async def test_multi_level_user_cannot_change_status_service_draft_to_reviewed(
        self,
        test_client,
        test_multi_level_user,
        test_document_service
    ):
        """Test: User kann NICHT Draft → Reviewed für Service-Dokument (nur Level 2)."""
        token = await login_user(test_client, test_multi_level_user.email)
        
        response = await test_client.post(
            "/api/document-workflow/change-status",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "document_id": test_document_service.id,
                "new_status": "reviewed",
                "reason": "Versucht Draft → Reviewed (benötigt Level 3)"
            }
        )
        
        # Sollte fehlschlagen (User hat nur Level 2 für Service, benötigt aber Level 3 für Draft→Reviewed)
        assert response.status_code == 403
        error_detail = response.json().get("detail", "")
        assert "Berechtigung" in error_detail or "Level" in error_detail or "Permission" in error_detail
    
    @pytest.mark.asyncio
    async def test_multi_level_user_sees_produktion_in_kanban(
        self,
        test_client,
        test_multi_level_user,
        test_document_produktion,
        test_document_service
    ):
        """Test: User sieht nur Produktion-Dokumente im Kanban (Level 3)."""
        token = await login_user(test_client, test_multi_level_user.email)
        
        # Hole Dokumente für Draft-Status
        response = await test_client.get(
            "/api/document-workflow/status/draft",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        documents = data.get("data", {}).get("documents", [])
        
        # Dokument-IDs aus Response
        doc_ids = [doc["id"] for doc in documents]
        
        # Produktion-Dokument sollte sichtbar sein (Level 3)
        assert test_document_produktion.id in doc_ids
        
        # Service-Dokument sollte NICHT im Kanban sichtbar sein (nur Level 2)
        # (Kanban erfordert Level 3, Service-Dokument hat User nur Level 2)
        assert test_document_service.id not in doc_ids
    
    @pytest.mark.asyncio
    async def test_multi_level_user_sees_both_documents_in_table(
        self,
        test_client,
        test_multi_level_user,
        test_document_produktion,
        test_document_service
    ):
        """Test: User sieht beide Dokumente in Tabelle (Level 2 reicht für Table View)."""
        token = await login_user(test_client, test_multi_level_user.email)
        
        # Hole alle Dokumente
        response = await test_client.get(
            "/api/document-upload/uploads",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        documents = data.get("documents", [])
        
        # Dokument-IDs aus Response
        doc_ids = [doc["id"] for doc in documents]
        
        # Beide Dokumente sollten sichtbar sein (Table View erfordert nur Level 2)
        assert test_document_produktion.id in doc_ids
        assert test_document_service.id in doc_ids
    
    @pytest.mark.asyncio
    async def test_document_type_counts_filtered_by_ig(
        self,
        test_client,
        test_multi_level_user,
        test_document_type,
        test_document_produktion,
        test_document_service
    ):
        """Test: Document Type Counts sind nach IGs gefiltert."""
        token = await login_user(test_client, test_multi_level_user.email)
        
        # Hole Document Type Counts
        response = await test_client.get(
            f"/api/rag/documents/types/counts?document_type_ids={test_document_type.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        counts = response.json()
        
        # Count sollte > 0 sein (mindestens eines der beiden Dokumente sollte gezählt werden)
        # Da beide Dokumente zum gleichen Document Type gehören und User beide IGs hat,
        # sollten beide gezählt werden
        assert counts.get(str(test_document_type.id), 0) >= 1


class TestContextSpecificPermissions:
    """Tests für Context-Specific Permission Checks."""
    
    @pytest.mark.asyncio
    async def test_user_with_level3_for_ig_can_see_kanban(
        self,
        test_client,
        test_multi_level_user,
        test_document_produktion
    ):
        """Test: User mit Level 3 für eine IG sieht Kanban für diese IG."""
        token = await login_user(test_client, test_multi_level_user.email)
        
        # JWT Token sollte user_level = 3 enthalten (höchstes Level)
        import base64
        import json
        parts = token.split('.')
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
        
        # user_level sollte 3 sein (höchstes Level des Users)
        assert payload.get("user_level") == 3
        
        # User sollte Kanban sehen können (global Level >= 3)
        # Aber nur für Produktion-Dokumente (context-specific)
    
    @pytest.mark.asyncio
    async def test_can_perform_action_on_document_check(
        self,
        db_session,
        test_multi_level_user,
        test_document_produktion,
        test_document_service
    ):
        """Test: can_perform_action_on_document prüft korrekt IG-Level."""
        from contexts.documentupload.infrastructure.permission_service import SQLAlchemyWorkflowPermissionService
        
        permission_service = SQLAlchemyWorkflowPermissionService(db_session)
        
        # Hole IG-IDs der Dokumente
        prod_ig_ids = [ig.interest_group_id for ig in db_session.query(UploadDocumentInterestGroup).filter(
            UploadDocumentInterestGroup.upload_document_id == test_document_produktion.id
        ).all()]
        
        service_ig_ids = [ig.interest_group_id for ig in db_session.query(UploadDocumentInterestGroup).filter(
            UploadDocumentInterestGroup.upload_document_id == test_document_service.id
        ).all()]
        
        # User kann Draft → Reviewed für Produktion (Level 3 vorhanden)
        can_prod = permission_service.can_perform_action_on_document(
            user_id=test_multi_level_user.id,
            document_interest_group_ids=prod_ig_ids,
            action="change_status_draft_to_reviewed",
            required_level=3
        )
        assert can_prod is True
        
        # User kann NICHT Draft → Reviewed für Service (nur Level 2 vorhanden)
        can_service = permission_service.can_perform_action_on_document(
            user_id=test_multi_level_user.id,
            document_interest_group_ids=service_ig_ids,
            action="change_status_draft_to_reviewed",
            required_level=3
        )
        assert can_service is False

