"""
Unit Tests für WorkflowPermissionService Implementation.

Testet die Level-basierte Berechtigung für Workflow-Status-Änderungen.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from contexts.documentupload.infrastructure.permission_service import SQLAlchemyWorkflowPermissionService
from contexts.documentupload.domain.value_objects import WorkflowStatus
from backend.app.models import User, UserGroupMembership


class TestSQLAlchemyWorkflowPermissionService:
    """Test Suite für SQLAlchemyWorkflowPermissionService."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock Database Session."""
        return MagicMock()
    
    @pytest.fixture
    def permission_service(self, mock_db):
        """Permission Service Instance."""
        return SQLAlchemyWorkflowPermissionService(mock_db)
    
    @pytest.fixture
    def qms_admin_user(self):
        """QMS Admin User Model."""
        user = MagicMock(spec=User)
        user.id = 1
        user.is_qms_admin = True
        return user
    
    @pytest.fixture
    def regular_user(self):
        """Regular User Model."""
        user = MagicMock(spec=User)
        user.id = 2
        user.is_qms_admin = False
        return user
    
    @pytest.fixture
    def level3_membership(self):
        """Level 3 UserGroupMembership."""
        membership = MagicMock(spec=UserGroupMembership)
        membership.approval_level = 3
        return membership
    
    @pytest.fixture
    def level4_membership(self):
        """Level 4 UserGroupMembership."""
        membership = MagicMock(spec=UserGroupMembership)
        membership.approval_level = 4
        return membership
    
    def test_get_user_level_qms_admin(self, permission_service, mock_db, qms_admin_user):
        """Test: QMS Admin → Level 5."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = qms_admin_user
        
        # Execute
        level = permission_service.get_user_level(1)
        
        # Assert
        assert level == 5
    
    def test_get_user_level_from_approval_level(self, permission_service, mock_db, regular_user, level3_membership):
        """Test: UserGroupMembership.approval_level → Level 1-4."""
        # Setup
        # First call: get user
        mock_db.query.return_value.filter.return_value.first.return_value = regular_user
        
        # Second call: get membership with order_by
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = level3_membership
        
        # Execute
        level = permission_service.get_user_level(2)
        
        # Assert
        assert level == 3
    
    def test_get_user_level_no_membership(self, permission_service, mock_db, regular_user):
        """Test: User ohne Membership → Level 0."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = regular_user
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        # Execute
        level = permission_service.get_user_level(2)
        
        # Assert
        assert level == 0
    
    def test_get_user_level_user_not_found(self, permission_service, mock_db):
        """Test: User nicht gefunden → Level 0."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        level = permission_service.get_user_level(999)
        
        # Assert
        assert level == 0
    
    def test_can_change_status_level3_draft_to_reviewed(self, permission_service, mock_db, regular_user, level3_membership):
        """Test: Level 3 kann draft → reviewed."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = regular_user
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = level3_membership
        
        # Execute
        can_change = permission_service.can_change_status(
            user_id=2,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED
        )
        
        # Assert
        assert can_change is True
    
    def test_can_change_status_level4_reviewed_to_approved(self, permission_service, mock_db, regular_user, level4_membership):
        """Test: Level 4 kann reviewed → approved."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = regular_user
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = level4_membership
        
        # Execute
        can_change = permission_service.can_change_status(
            user_id=2,
            from_status=WorkflowStatus.REVIEWED,
            to_status=WorkflowStatus.APPROVED
        )
        
        # Assert
        assert can_change is True
    
    def test_can_change_status_level2_cannot_draft_to_reviewed(self, permission_service, mock_db, regular_user):
        """Test: Level 2 kann nicht draft → reviewed."""
        # Setup - Level 2 Membership
        level2_membership = MagicMock(spec=UserGroupMembership)
        level2_membership.approval_level = 2
        
        mock_db.query.return_value.filter.return_value.first.return_value = regular_user
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = level2_membership
        
        # Execute
        can_change = permission_service.can_change_status(
            user_id=2,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.REVIEWED
        )
        
        # Assert
        assert can_change is False
    
    def test_can_change_status_level3_cannot_reviewed_to_approved(self, permission_service, mock_db, regular_user, level3_membership):
        """Test: Level 3 kann nicht reviewed → approved."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = regular_user
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = level3_membership
        
        # Execute
        can_change = permission_service.can_change_status(
            user_id=2,
            from_status=WorkflowStatus.REVIEWED,
            to_status=WorkflowStatus.APPROVED
        )
        
        # Assert
        assert can_change is False
    
    def test_can_change_status_invalid_transition(self, permission_service, mock_db, regular_user, level3_membership):
        """Test: Ungültige Transition → False."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.side_effect = [regular_user, level3_membership]
        
        # Execute
        can_change = permission_service.can_change_status(
            user_id=2,
            from_status=WorkflowStatus.DRAFT,
            to_status=WorkflowStatus.APPROVED  # Ungültig: draft → approved
        )
        
        # Assert
        assert can_change is False
    
    def test_can_change_status_qms_admin_all_transitions(self, permission_service, mock_db, qms_admin_user):
        """Test: QMS Admin kann alle Transitions."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = qms_admin_user
        
        # Test alle erlaubten Transitions
        transitions = [
            (WorkflowStatus.DRAFT, WorkflowStatus.REVIEWED),
            (WorkflowStatus.REVIEWED, WorkflowStatus.APPROVED),
            (WorkflowStatus.REVIEWED, WorkflowStatus.REJECTED),
            (WorkflowStatus.REJECTED, WorkflowStatus.DRAFT),
        ]
        
        for from_status, to_status in transitions:
            can_change = permission_service.can_change_status(
                user_id=1,
                from_status=from_status,
                to_status=to_status
            )
            assert can_change is True, f"QMS Admin sollte {from_status} → {to_status} können"
    
    def test_workflow_rules_defined_correctly(self, permission_service):
        """Test: Workflow Rules sind korrekt definiert."""
        rules = permission_service.WORKFLOW_RULES
        
        # Prüfe alle erwarteten Transitions
        assert WorkflowStatus.DRAFT in rules
        assert WorkflowStatus.REVIEWED in rules
        assert WorkflowStatus.REJECTED in rules
        
        # Prüfe spezifische Rules
        assert rules[WorkflowStatus.DRAFT][WorkflowStatus.REVIEWED] == 3
        assert rules[WorkflowStatus.REVIEWED][WorkflowStatus.APPROVED] == 4
        assert rules[WorkflowStatus.REVIEWED][WorkflowStatus.REJECTED] == 4
        assert rules[WorkflowStatus.REJECTED][WorkflowStatus.DRAFT] == 3
