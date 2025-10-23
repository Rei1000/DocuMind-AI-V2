"""
Test für DELETE Document Funktionalität.

TDD Approach: Schreibe zuerst den Test, dann die Implementierung.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from contexts.documentupload.domain.entities import UploadedDocument, WorkflowStatus
from contexts.documentupload.domain.value_objects import DocumentMetadata


class TestDeleteDocument:
    """Test-Klasse für DELETE Document Endpoint."""
    
    def test_delete_document_success(self):
        """Test: Dokument erfolgreich löschen."""
        client = TestClient(app)
        
        # Mock authentication
        with patch('contexts.documentupload.interface.router.get_current_user') as mock_auth:
            mock_auth.return_value = {
                'id': 1,
                'email': 'qms.admin@company.com',
                'permission_level': 5
            }
            
            # Mock repository
            with patch('contexts.documentupload.interface.router.SQLAlchemyUploadRepository') as mock_repo_class:
                mock_repo = Mock()
                mock_repo_class.return_value = mock_repo
                
                # Mock document exists
                mock_document = Mock()
                mock_document.id = 1
                mock_document.metadata = Mock()
                mock_document.metadata.filename = "test.pdf"
                mock_repo.get_by_id.return_value = mock_document
                mock_repo.delete.return_value = True
                
                # Test DELETE request
                response = client.delete("/api/document-upload/1")
                
                # Assertions
                assert response.status_code == 200
                assert response.json()["success"] is True
                mock_repo.delete.assert_called_once_with(1)
    
    def test_delete_document_not_found(self):
        """Test: Dokument nicht gefunden."""
        client = TestClient(app)
        
        with patch('contexts.documentupload.interface.router.get_current_user') as mock_auth:
            mock_auth.return_value = {
                'id': 1,
                'email': 'qms.admin@company.com',
                'permission_level': 5
            }
            
            with patch('contexts.documentupload.interface.router.SQLAlchemyUploadRepository') as mock_repo_class:
                mock_repo = Mock()
                mock_repo_class.return_value = mock_repo
                mock_repo.get_by_id.return_value = None
                
                response = client.delete("/api/document-upload/999")
                
                assert response.status_code == 404
                assert "not found" in response.json()["detail"].lower()
    
    def test_delete_document_insufficient_permissions(self):
        """Test: Unzureichende Berechtigungen."""
        client = TestClient(app)
        
        with patch('contexts.documentupload.interface.router.get_current_user') as mock_auth:
            mock_auth.return_value = {
                'id': 2,
                'email': 'user@company.com',
                'permission_level': 2  # Zu niedrig
            }
            
            response = client.delete("/api/document-upload/1")
            
            assert response.status_code == 403
            assert "permission" in response.json()["detail"].lower()
    
    def test_delete_document_qms_admin_bypass(self):
        """Test: QMS Admin kann trotz niedrigem Level löschen."""
        client = TestClient(app)
        
        with patch('contexts.documentupload.interface.router.get_current_user') as mock_auth:
            mock_auth.return_value = {
                'id': 1,
                'email': 'qms.admin@company.com',
                'permission_level': 2  # Niedrig, aber QMS Admin
            }
            
            with patch('contexts.documentupload.interface.router.SQLAlchemyUploadRepository') as mock_repo_class:
                mock_repo = Mock()
                mock_repo_class.return_value = mock_repo
                mock_document = Mock()
                mock_document.id = 1
                mock_repo.get_by_id.return_value = mock_document
                mock_repo.delete.return_value = True
                
                response = client.delete("/api/document-upload/1")
                
                assert response.status_code == 200
                assert response.json()["success"] is True
