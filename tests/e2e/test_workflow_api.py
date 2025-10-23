"""
E2E Tests für Document Workflow API

Testet den vollständigen Workflow von Upload bis Approval.
"""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import UploadDocument, DocumentStatusChange, DocumentComment
from contexts.documentupload.domain.value_objects import WorkflowStatus


class TestDocumentWorkflowE2E:
    """E2E Tests für den kompletten Document Workflow."""

    @pytest.fixture
    def client(self):
        """HTTP Client für API-Tests."""
        from backend.app.main import app
        return AsyncClient(app=app, base_url="http://test")

    @pytest.fixture
    def test_user_token(self):
        """Test User JWT Token."""
        # Mock JWT Token für Test-User (Level 4 - QM Manager)
        return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6InFtc0Bjb21wYW55LmNvbSIsImxldmVsIjo0fQ.test"

    @pytest.fixture
    def test_document_data(self):
        """Test-Dokument Daten."""
        return {
            "document_type_id": 1,
            "qm_chapter": "5.2",
            "version": "v1.0",
            "interest_group_ids": [1, 2]
        }

    @pytest.mark.asyncio
    async def test_complete_workflow_draft_to_approved(self, client, test_user_token, test_document_data):
        """Test: Vollständiger Workflow von Draft zu Approved."""
        
        # 1. Erstelle ein Test-Dokument direkt in der DB (für E2E-Tests)
        # In einem echten E2E-Test würde man den Upload-Prozess verwenden
        # Hier simulieren wir ein bereits hochgeladenes Dokument
        document_id = 999  # Mock Document ID für Test
        
        # 2. Prüfe, dass Dokument in "draft" Status ist
        status_response = await client.get(
            f"/api/document-workflow/status/draft",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert status_response.status_code == 200
        documents = status_response.json()
        assert len(documents) >= 1
        assert any(doc["id"] == document_id for doc in documents)
        
        # 3. Ändere Status zu "reviewed"
        change_response = await client.post(
            "/api/document-workflow/change-status",
            json={
                "document_id": document_id,
                "new_status": "reviewed",
                "user_id": 1,
                "reason": "Teamleiter-Freigabe",
                "comment": "Alle Prüfpunkte OK"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert change_response.status_code == 200
        
        # 4. Prüfe, dass Dokument jetzt in "reviewed" Status ist
        reviewed_response = await client.get(
            f"/api/document-workflow/status/reviewed",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert reviewed_response.status_code == 200
        reviewed_documents = reviewed_response.json()
        assert any(doc["id"] == document_id for doc in reviewed_documents)
        
        # 5. Ändere Status zu "approved"
        approve_response = await client.post(
            "/api/document-workflow/change-status",
            json={
                "document_id": document_id,
                "new_status": "approved",
                "user_id": 1,
                "reason": "QM-Freigabe",
                "comment": "Dokument genehmigt"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert approve_response.status_code == 200
        
        # 6. Prüfe, dass Dokument jetzt in "approved" Status ist
        approved_response = await client.get(
            f"/api/document-workflow/status/approved",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert approved_response.status_code == 200
        approved_documents = approved_response.json()
        assert any(doc["id"] == document_id for doc in approved_documents)

    @pytest.mark.asyncio
    async def test_workflow_rejection(self, client, test_user_token, test_document_data):
        """Test: Workflow mit Zurückweisung."""
        
        # 1. Upload Dokument
        upload_response = await client.post(
            "/api/document-upload/upload",
            json=test_document_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        document_id = upload_data["document_id"]
        
        # 2. Ändere Status zu "reviewed"
        change_response = await client.post(
            "/api/document-workflow/change-status",
            json={
                "document_id": document_id,
                "new_status": "reviewed",
                "user_id": 1,
                "reason": "Teamleiter-Freigabe"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert change_response.status_code == 200
        
        # 3. Zurückweisen (reviewed → rejected)
        reject_response = await client.post(
            "/api/document-workflow/change-status",
            json={
                "document_id": document_id,
                "new_status": "rejected",
                "user_id": 1,
                "reason": "QM-Zurückweisung",
                "comment": "Dokument unvollständig, bitte überarbeiten"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert reject_response.status_code == 200
        
        # 4. Prüfe, dass Dokument jetzt in "rejected" Status ist
        rejected_response = await client.get(
            f"/api/document-workflow/status/rejected",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert rejected_response.status_code == 200
        rejected_documents = rejected_response.json()
        assert any(doc["id"] == document_id for doc in rejected_documents)

    @pytest.mark.asyncio
    async def test_workflow_history(self, client, test_user_token, test_document_data):
        """Test: Workflow-Historie wird korrekt gespeichert."""
        
        # 1. Upload Dokument
        upload_response = await client.post(
            "/api/document-upload/upload",
            json=test_document_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        document_id = upload_data["document_id"]
        
        # 2. Ändere Status zu "reviewed"
        change_response = await client.post(
            "/api/document-workflow/change-status",
            json={
                "document_id": document_id,
                "new_status": "reviewed",
                "user_id": 1,
                "reason": "Teamleiter-Freigabe",
                "comment": "Erste Prüfung OK"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert change_response.status_code == 200
        
        # 3. Ändere Status zu "approved"
        approve_response = await client.post(
            "/api/document-workflow/change-status",
            json={
                "document_id": document_id,
                "new_status": "approved",
                "user_id": 1,
                "reason": "QM-Freigabe",
                "comment": "Finale Genehmigung"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert approve_response.status_code == 200
        
        # 4. Hole Workflow-Historie
        history_response = await client.get(
            f"/api/document-workflow/history/{document_id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert history_response.status_code == 200
        history = history_response.json()
        
        # 5. Prüfe Historie
        assert len(history) == 2  # 2 Status-Änderungen
        
        # Erste Änderung: draft → reviewed
        first_change = history[0]
        assert first_change["from_status"] == "draft"
        assert first_change["to_status"] == "reviewed"
        assert first_change["change_reason"] == "Teamleiter-Freigabe"
        assert first_change["comment"] == "Erste Prüfung OK"
        
        # Zweite Änderung: reviewed → approved
        second_change = history[1]
        assert second_change["from_status"] == "reviewed"
        assert second_change["to_status"] == "approved"
        assert second_change["change_reason"] == "QM-Freigabe"
        assert second_change["comment"] == "Finale Genehmigung"

    @pytest.mark.asyncio
    async def test_permission_denied_for_level_2(self, client, test_document_data):
        """Test: Level 2 User kann keine Status-Änderungen vornehmen."""
        
        # Level 2 User Token (nur Lesen)
        level2_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoyLCJlbWFpbCI6ImVtcGxveWVlQGNvbXBhbnkuY29tIiwibGV2ZWwiOjJ9.test"
        
        # 1. Upload Dokument (Level 4 User)
        qm_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6InFtc0Bjb21wYW55LmNvbSIsImxldmVsIjo0fQ.test"
        
        upload_response = await client.post(
            "/api/document-upload/upload",
            json=test_document_data,
            headers={"Authorization": f"Bearer {qm_token}"}
        )
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        document_id = upload_data["document_id"]
        
        # 2. Level 2 User versucht Status zu ändern (sollte fehlschlagen)
        change_response = await client.post(
            "/api/document-workflow/change-status",
            json={
                "document_id": document_id,
                "new_status": "reviewed",
                "user_id": 2,
                "reason": "Versuche Status zu ändern"
            },
            headers={"Authorization": f"Bearer {level2_token}"}
        )
        assert change_response.status_code == 403  # Permission Denied

    @pytest.mark.asyncio
    async def test_allowed_transitions(self, client, test_user_token, test_document_data):
        """Test: Erlaubte Transitions werden korrekt zurückgegeben."""
        
        # 1. Upload Dokument
        upload_response = await client.post(
            "/api/document-upload/upload",
            json=test_document_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        document_id = upload_data["document_id"]
        
        # 2. Hole erlaubte Transitions für Draft-Status
        transitions_response = await client.get(
            f"/api/document-workflow/allowed-transitions/{document_id}",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert transitions_response.status_code == 200
        transitions = transitions_response.json()
        
        # 3. Prüfe erlaubte Transitions (Level 4 kann alles)
        assert "reviewed" in transitions
        assert "approved" in transitions
        assert "rejected" in transitions

    @pytest.mark.asyncio
    async def test_invalid_status_transition(self, client, test_user_token, test_document_data):
        """Test: Ungültige Status-Transitions werden blockiert."""
        
        # 1. Upload Dokument
        upload_response = await client.post(
            "/api/document-upload/upload",
            json=test_document_data,
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        document_id = upload_data["document_id"]
        
        # 2. Versuche ungültige Transition: draft → approved (sollte fehlschlagen)
        invalid_response = await client.post(
            "/api/document-workflow/change-status",
            json={
                "document_id": document_id,
                "new_status": "approved",
                "user_id": 1,
                "reason": "Ungültige Transition"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert invalid_response.status_code == 400  # Bad Request

    @pytest.mark.asyncio
    async def test_interest_groups_filter(self, client, test_user_token):
        """Test: Interest Groups Filter funktioniert."""
        
        # 1. Hole Dokumente mit Interest Group Filter
        filtered_response = await client.get(
            "/api/document-workflow/status/draft?interest_group_ids=1,2",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert filtered_response.status_code == 200
        documents = filtered_response.json()
        
        # 2. Prüfe, dass alle Dokumente die richtigen Interest Groups haben
        for doc in documents:
            assert any(group_id in [1, 2] for group_id in doc["interest_group_ids"])

    @pytest.mark.asyncio
    async def test_document_not_found(self, client, test_user_token):
        """Test: Fehlerbehandlung bei nicht existierendem Dokument."""
        
        # 1. Versuche Status-Änderung für nicht existierendes Dokument
        response = await client.post(
            "/api/document-workflow/change-status",
            json={
                "document_id": 99999,
                "new_status": "reviewed",
                "user_id": 1,
                "reason": "Test"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 404  # Not Found

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client, test_user_token):
        """Test: Fehlerbehandlung bei fehlenden Pflichtfeldern."""
        
        # 1. Versuche Status-Änderung ohne reason
        response = await client.post(
            "/api/document-workflow/change-status",
            json={
                "document_id": 1,
                "new_status": "reviewed",
                "user_id": 1
                # reason fehlt
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 422  # Validation Error

    @pytest.mark.asyncio
    async def test_invalid_workflow_status(self, client, test_user_token):
        """Test: Fehlerbehandlung bei ungültigem Workflow-Status."""
        
        # 1. Versuche Status-Änderung mit ungültigem Status
        response = await client.post(
            "/api/document-workflow/change-status",
            json={
                "document_id": 1,
                "new_status": "invalid_status",
                "user_id": 1,
                "reason": "Test"
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 400  # Bad Request


@pytest.mark.asyncio
class TestWorkflowPerformance:
    """Performance Tests für Workflow-API."""

    @pytest.mark.asyncio
    async def test_bulk_document_loading(self, client, test_user_token):
        """Test: Performance beim Laden vieler Dokumente."""
        
        # 1. Hole alle Dokumente nach Status
        start_time = asyncio.get_event_loop().time()
        
        response = await client.get(
            "/api/document-workflow/status/draft",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        end_time = asyncio.get_event_loop().time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Sollte unter 1 Sekunde sein
        
        documents = response.json()
        print(f"Loaded {len(documents)} documents in {response_time:.3f}s")

    @pytest.mark.asyncio
    async def test_concurrent_status_changes(self, client, test_user_token, test_document_data):
        """Test: Gleichzeitige Status-Änderungen."""
        
        # 1. Upload mehrere Dokumente
        document_ids = []
        for i in range(3):
            upload_response = await client.post(
                "/api/document-upload/upload",
                json={**test_document_data, "version": f"v{i+1}.0"},
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            assert upload_response.status_code == 200
            document_ids.append(upload_response.json()["document_id"])
        
        # 2. Ändere Status aller Dokumente gleichzeitig
        tasks = []
        for doc_id in document_ids:
            task = client.post(
                "/api/document-workflow/change-status",
                json={
                    "document_id": doc_id,
                    "new_status": "reviewed",
                    "user_id": 1,
                    "reason": f"Concurrent change for doc {doc_id}"
                },
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            tasks.append(task)
        
        # 3. Führe alle Änderungen gleichzeitig aus
        start_time = asyncio.get_event_loop().time()
        responses = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()
        
        # 4. Prüfe Ergebnisse
        for response in responses:
            assert response.status_code == 200
        
        response_time = end_time - start_time
        print(f"Concurrent status changes completed in {response_time:.3f}s")
        assert response_time < 2.0  # Sollte unter 2 Sekunden sein
