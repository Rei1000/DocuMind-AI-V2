"""
Unit Tests für AuthLoginService - Phase 1.1-1.2

Testet die Erweiterung des JWT Tokens um:
- user_level
- is_qms_admin
- interest_group_ids
"""

import pytest
from unittest.mock import MagicMock, Mock
from jose import jwt
import os
from datetime import datetime, timedelta

from contexts.accesscontrol.application.auth_login_service import AuthLoginService, LoginResult
from contexts.accesscontrol.domain.entities import User
from contexts.documentupload.infrastructure.permission_service import SQLAlchemyWorkflowPermissionService


class TestAuthLoginServiceTokenExtension:
    """Test Suite für JWT Token Erweiterung (Phase 1.1-1.2)"""
    
    @pytest.fixture
    def mock_user_repository(self):
        """Mock User Repository"""
        repo = MagicMock()
        return repo
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock Database Session"""
        return MagicMock()
    
    @pytest.fixture
    def mock_permission_service(self, mock_db_session):
        """Mock Permission Service"""
        service = SQLAlchemyWorkflowPermissionService(mock_db_session)
        service.get_user_level = MagicMock()
        service.get_user_interest_groups = MagicMock()
        return service
    
    @pytest.fixture
    def auth_service(self, mock_user_repository, mock_permission_service):
        """AuthLoginService mit Permission Service"""
        service = AuthLoginService(mock_user_repository, mock_permission_service)
        return service
    
    @pytest.fixture
    def qms_admin_user(self):
        """QMS Admin User Entity"""
        user = User(
            id=1,
            email="qms.admin@company.com",
            full_name="QMS Admin",
            hashed_password="hashed_pw",
            is_active=True,
            approval_level=5  # QMS Admin hat Level 5
        )
        return user
    
    @pytest.fixture
    def level_3_user(self):
        """Level 3 User Entity"""
        user = User(
            id=2,
            email="abteilungsleiter.service@company.com",
            full_name="Abteilungsleiter Service",
            hashed_password="hashed_pw",
            is_active=True,
            approval_level=3  # Abteilungsleiter hat Level 3
        )
        return user
    
    @pytest.fixture
    def level_4_user(self):
        """Level 4 User Entity"""
        user = User(
            id=3,
            email="qm.mitarbeiter@company.com",
            full_name="QM Mitarbeiter",
            hashed_password="hashed_pw",
            is_active=True,
            approval_level=4  # QM Mitarbeiter hat Level 4
        )
        return user
    
    def _decode_token(self, token: str, secret_key: str) -> dict:
        """Hilfsmethode: JWT Token dekodieren"""
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    
    # ============================================================================
    # Phase 1.1: user_level im Token
    # ============================================================================
    
    def test_token_contains_user_level_5_for_qms_admin(self, auth_service, mock_user_repository, mock_permission_service, qms_admin_user):
        """Test: QMS Admin (Level 5) hat user_level=5 im Token"""
        # Arrange
        mock_user_repository.find_by_email.return_value = qms_admin_user
        mock_permission_service.get_user_level.return_value = 5
        mock_permission_service.get_user_interest_groups.return_value = []
        
        # Mock password verification
        auth_service._verify_password = MagicMock(return_value=True)
        
        # Act
        result = auth_service.login("qms.admin@company.com", "password")
        
        # Assert
        assert result.success is True
        token_data = self._decode_token(result.data["access_token"], auth_service.secret_key)
        assert token_data["user_level"] == 5
    
    def test_token_contains_user_level_3_for_department_head(self, auth_service, mock_user_repository, mock_permission_service, level_3_user):
        """Test: Level 3 User hat user_level=3 im Token"""
        # Arrange
        mock_user_repository.find_by_email.return_value = level_3_user
        mock_permission_service.get_user_level.return_value = 3
        mock_permission_service.get_user_interest_groups.return_value = [1, 2]
        
        auth_service._verify_password = MagicMock(return_value=True)
        
        # Act
        result = auth_service.login("abteilungsleiter.service@company.com", "password")
        
        # Assert
        assert result.success is True
        token_data = self._decode_token(result.data["access_token"], auth_service.secret_key)
        assert token_data["user_level"] == 3
    
    def test_token_contains_user_level_4_for_qm_employee(self, auth_service, mock_user_repository, mock_permission_service, level_4_user):
        """Test: Level 4 User hat user_level=4 im Token"""
        # Arrange
        mock_user_repository.find_by_email.return_value = level_4_user
        mock_permission_service.get_user_level.return_value = 4
        mock_permission_service.get_user_interest_groups.return_value = []
        
        auth_service._verify_password = MagicMock(return_value=True)
        
        # Act
        result = auth_service.login("qm.mitarbeiter@company.com", "password")
        
        # Assert
        assert result.success is True
        token_data = self._decode_token(result.data["access_token"], auth_service.secret_key)
        assert token_data["user_level"] == 4
    
    # ============================================================================
    # Phase 1.1: is_qms_admin im Token
    # ============================================================================
    
    def test_token_contains_is_qms_admin_true_for_admin(self, auth_service, mock_user_repository, mock_permission_service, qms_admin_user):
        """Test: QMS Admin hat is_qms_admin=True im Token"""
        # Arrange
        mock_user_repository.find_by_email.return_value = qms_admin_user
        mock_permission_service.get_user_level.return_value = 5
        mock_permission_service.get_user_interest_groups.return_value = []
        
        auth_service._verify_password = MagicMock(return_value=True)
        
        # Act
        result = auth_service.login("qms.admin@company.com", "password")
        
        # Assert
        assert result.success is True
        token_data = self._decode_token(result.data["access_token"], auth_service.secret_key)
        assert token_data["is_qms_admin"] is True
    
    def test_token_contains_is_qms_admin_false_for_regular_user(self, auth_service, mock_user_repository, mock_permission_service, level_3_user):
        """Test: Normaler User hat is_qms_admin=False im Token"""
        # Arrange
        mock_user_repository.find_by_email.return_value = level_3_user
        mock_permission_service.get_user_level.return_value = 3
        mock_permission_service.get_user_interest_groups.return_value = [1]
        
        auth_service._verify_password = MagicMock(return_value=True)
        
        # Act
        result = auth_service.login("abteilungsleiter.service@company.com", "password")
        
        # Assert
        assert result.success is True
        token_data = self._decode_token(result.data["access_token"], auth_service.secret_key)
        assert token_data["is_qms_admin"] is False  # Level 3 ist nicht QMS Admin
    
    # ============================================================================
    # Phase 1.2: interest_group_ids im Token
    # ============================================================================
    
    def test_token_contains_empty_interest_groups_for_level_4(self, auth_service, mock_user_repository, mock_permission_service, level_4_user):
        """Test: Level 4+ User hat leere interest_group_ids Liste (alle IG)"""
        # Arrange
        mock_user_repository.find_by_email.return_value = level_4_user
        mock_permission_service.get_user_level.return_value = 4
        mock_permission_service.get_user_interest_groups.return_value = []  # Leere Liste = alle IG
        
        auth_service._verify_password = MagicMock(return_value=True)
        
        # Act
        result = auth_service.login("qm.mitarbeiter@company.com", "password")
        
        # Assert
        assert result.success is True
        token_data = self._decode_token(result.data["access_token"], auth_service.secret_key)
        assert token_data["interest_group_ids"] == []
    
    def test_token_contains_interest_groups_for_level_3(self, auth_service, mock_user_repository, mock_permission_service, level_3_user):
        """Test: Level 3 User hat seine Interest Groups im Token"""
        # Arrange
        mock_user_repository.find_by_email.return_value = level_3_user
        mock_permission_service.get_user_level.return_value = 3
        mock_permission_service.get_user_interest_groups.return_value = [1, 2]  # Zwei IG
        
        auth_service._verify_password = MagicMock(return_value=True)
        
        # Act
        result = auth_service.login("abteilungsleiter.service@company.com", "password")
        
        # Assert
        assert result.success is True
        token_data = self._decode_token(result.data["access_token"], auth_service.secret_key)
        assert token_data["interest_group_ids"] == [1, 2]
    
    def test_token_contains_interest_groups_for_level_1(self, auth_service, mock_user_repository, mock_permission_service):
        """Test: Level 1 User hat seine Interest Groups im Token"""
        # Arrange
        level_1_user = User(
            id=4,
            email="mitarbeiter.service@company.com",
            full_name="Mitarbeiter Service",
            hashed_password="hashed_pw",
            is_active=True,
            approval_level=1  # Level 1 Mitarbeiter
        )
        
        mock_user_repository.find_by_email.return_value = level_1_user
        mock_permission_service.get_user_level.return_value = 1
        mock_permission_service.get_user_interest_groups.return_value = [1]  # Eine IG
        
        auth_service._verify_password = MagicMock(return_value=True)
        
        # Act
        result = auth_service.login("mitarbeiter.service@company.com", "password")
        
        # Assert
        assert result.success is True
        token_data = self._decode_token(result.data["access_token"], auth_service.secret_key)
        assert token_data["interest_group_ids"] == [1]
    
    # ============================================================================
    # Integration: Alle neuen Felder zusammen
    # ============================================================================
    
    def test_token_contains_all_rbac_fields(self, auth_service, mock_user_repository, mock_permission_service, qms_admin_user):
        """Test: Token enthält alle neuen RBAC-Felder"""
        # Arrange
        mock_user_repository.find_by_email.return_value = qms_admin_user
        mock_permission_service.get_user_level.return_value = 5
        mock_permission_service.get_user_interest_groups.return_value = []
        
        auth_service._verify_password = MagicMock(return_value=True)
        
        # Act
        result = auth_service.login("qms.admin@company.com", "password")
        
        # Assert
        assert result.success is True
        token_data = self._decode_token(result.data["access_token"], auth_service.secret_key)
        
        # Alle neuen Felder müssen vorhanden sein
        assert "user_level" in token_data
        assert "is_qms_admin" in token_data
        assert "interest_group_ids" in token_data
        
        # Werte prüfen
        assert token_data["user_level"] == 5
        assert token_data["is_qms_admin"] is True
        assert token_data["interest_group_ids"] == []
    
    def test_token_contains_all_rbac_fields_level_3(self, auth_service, mock_user_repository, mock_permission_service, level_3_user):
        """Test: Level 3 Token enthält alle neuen RBAC-Felder"""
        # Arrange
        mock_user_repository.find_by_email.return_value = level_3_user
        mock_permission_service.get_user_level.return_value = 3
        mock_permission_service.get_user_interest_groups.return_value = [1, 2, 3]
        
        auth_service._verify_password = MagicMock(return_value=True)
        
        # Act
        result = auth_service.login("abteilungsleiter.service@company.com", "password")
        
        # Assert
        assert result.success is True
        token_data = self._decode_token(result.data["access_token"], auth_service.secret_key)
        
        # Alle neuen Felder müssen vorhanden sein
        assert "user_level" in token_data
        assert "is_qms_admin" in token_data
        assert "interest_group_ids" in token_data
        
        # Werte prüfen
        assert token_data["user_level"] == 3
        assert token_data["is_qms_admin"] is False
        assert token_data["interest_group_ids"] == [1, 2, 3]

