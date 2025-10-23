"""
Unit Tests für Workflow Permission Service

Testet Permission-Logic für verschiedene User-Levels.
"""

import pytest
from contexts.documentupload.application.ports import WorkflowPermissionService
from contexts.documentupload.domain.entities import UploadedDocument, WorkflowStatusChange
from contexts.documentupload.domain.value_objects import (
    WorkflowStatus, 
    FileType, 
    ProcessingMethod, 
    ProcessingStatus,
    DocumentMetadata,
    FilePath
)
from datetime import datetime


class TestWorkflowPermissionService:
    """Tests für WorkflowPermissionService."""
    
    def test_level_2_read_only_access(self):
        """Test: Level 2 kann nur Dokumente seiner Interest Groups sehen (read-only)."""
        # Mock Permission Service
        class MockPermissionService(WorkflowPermissionService):
            def can_view_document(self, user_id: int, document) -> bool:
                return user_id == 2 and 1 in document.interest_group_ids
            
            def can_change_status(self, user_id: int, from_status: WorkflowStatus, to_status: WorkflowStatus) -> bool:
                return False  # Level 2 kann keine Status ändern
            
            def get_allowed_transitions(self, user_id: int, current_status: WorkflowStatus) -> list[WorkflowStatus]:
                return []  # Level 2 hat keine Transitions
            
            def get_user_level(self, user_id: int) -> int:
                return 2
            
            def get_user_interest_groups(self, user_id: int) -> list[int]:
                return [1, 2]
        
        service = MockPermissionService()
        
        # Test-Dokument
        metadata = DocumentMetadata(
            filename="test.pdf",
            original_filename="Test Document.pdf",
            qm_chapter="5.2",
            version="v1.0"
        )
        
        document = UploadedDocument(
            id=1,
            file_type=FileType.PDF,
            file_size_bytes=1024,
            document_type_id=1,
            metadata=metadata,
            file_path=FilePath("uploads/test.pdf"),
            processing_method=ProcessingMethod.VISION,
            processing_status=ProcessingStatus.COMPLETED,
            uploaded_by_user_id=456,
            uploaded_at=datetime.utcnow(),
            pages=[],
            interest_group_ids=[1, 2]
        )
        
        # Level 2 kann sein Dokument sehen
        assert service.can_view_document(2, document) == True
        
        # Level 2 kann keine Status ändern
        assert service.can_change_status(2, WorkflowStatus.DRAFT, WorkflowStatus.REVIEWED) == False
        assert service.get_allowed_transitions(2, WorkflowStatus.DRAFT) == []
    
    def test_level_3_team_leader_permissions(self):
        """Test: Level 3 kann nur Dokumente seiner Interest Groups sehen UND draft → reviewed verschieben."""
        class MockPermissionService(WorkflowPermissionService):
            def can_view_document(self, user_id: int, document) -> bool:
                return user_id == 3 and 1 in document.interest_group_ids
            
            def can_change_status(self, user_id: int, from_status: WorkflowStatus, to_status: WorkflowStatus) -> bool:
                if user_id != 3:
                    return False
                return from_status == WorkflowStatus.DRAFT and to_status == WorkflowStatus.REVIEWED
            
            def get_allowed_transitions(self, user_id: int, current_status: WorkflowStatus) -> list[WorkflowStatus]:
                if user_id != 3:
                    return []
                if current_status == WorkflowStatus.DRAFT:
                    return [WorkflowStatus.REVIEWED]
                return []
            
            def get_user_level(self, user_id: int) -> int:
                return 3
            
            def get_user_interest_groups(self, user_id: int) -> list[int]:
                return [1, 2]
        
        service = MockPermissionService()
        
        # Level 3 kann draft → reviewed
        assert service.can_change_status(3, WorkflowStatus.DRAFT, WorkflowStatus.REVIEWED) == True
        
        # Level 3 kann nicht reviewed → approved
        assert service.can_change_status(3, WorkflowStatus.REVIEWED, WorkflowStatus.APPROVED) == False
        
        # Level 3 kann nicht draft → approved (direkt)
        assert service.can_change_status(3, WorkflowStatus.DRAFT, WorkflowStatus.APPROVED) == False
        
        # Erlaubte Transitions
        assert service.get_allowed_transitions(3, WorkflowStatus.DRAFT) == [WorkflowStatus.REVIEWED]
        assert service.get_allowed_transitions(3, WorkflowStatus.REVIEWED) == []
    
    def test_level_4_qm_manager_permissions(self):
        """Test: Level 4 kann alle Dokumente sehen und reviewed → approved, any → rejected verschieben."""
        class MockPermissionService(WorkflowPermissionService):
            def can_view_document(self, user_id: int, document) -> bool:
                return user_id == 4  # Level 4 sieht alle Dokumente
            
            def can_change_status(self, user_id: int, from_status: WorkflowStatus, to_status: WorkflowStatus) -> bool:
                if user_id != 4:
                    return False
                return (
                    (from_status == WorkflowStatus.REVIEWED and to_status == WorkflowStatus.APPROVED) or
                    to_status == WorkflowStatus.REJECTED
                )
            
            def get_allowed_transitions(self, user_id: int, current_status: WorkflowStatus) -> list[WorkflowStatus]:
                if user_id != 4:
                    return []
                if current_status == WorkflowStatus.REVIEWED:
                    return [WorkflowStatus.APPROVED, WorkflowStatus.REJECTED]
                return [WorkflowStatus.REJECTED]  # any → rejected
            
            def get_user_level(self, user_id: int) -> int:
                return 4
            
            def get_user_interest_groups(self, user_id: int) -> list[int]:
                return [1, 2, 3, 4]  # Alle Interest Groups
        
        service = MockPermissionService()
        
        # Level 4 kann reviewed → approved
        assert service.can_change_status(4, WorkflowStatus.REVIEWED, WorkflowStatus.APPROVED) == True
        
        # Level 4 kann any → rejected
        assert service.can_change_status(4, WorkflowStatus.DRAFT, WorkflowStatus.REJECTED) == True
        assert service.can_change_status(4, WorkflowStatus.REVIEWED, WorkflowStatus.REJECTED) == True
        assert service.can_change_status(4, WorkflowStatus.APPROVED, WorkflowStatus.REJECTED) == True
        
        # Level 4 kann nicht draft → approved (direkt)
        assert service.can_change_status(4, WorkflowStatus.DRAFT, WorkflowStatus.APPROVED) == False
        
        # Erlaubte Transitions
        assert service.get_allowed_transitions(4, WorkflowStatus.REVIEWED) == [WorkflowStatus.APPROVED, WorkflowStatus.REJECTED]
        assert service.get_allowed_transitions(4, WorkflowStatus.DRAFT) == [WorkflowStatus.REJECTED]
    
    def test_level_5_qms_admin_permissions(self):
        """Test: Level 5 (QMS Admin) hat vollen Zugriff auf alles."""
        class MockPermissionService(WorkflowPermissionService):
            def can_view_document(self, user_id: int, document) -> bool:
                return user_id == 5  # Level 5 sieht alle Dokumente
            
            def can_change_status(self, user_id: int, from_status: WorkflowStatus, to_status: WorkflowStatus) -> bool:
                if user_id != 5:
                    return False
                return from_status != to_status  # Alle Transitions außer same-status
            
            def get_allowed_transitions(self, user_id: int, current_status: WorkflowStatus) -> list[WorkflowStatus]:
                if user_id != 5:
                    return []
                return [status for status in WorkflowStatus if status != current_status]
            
            def get_user_level(self, user_id: int) -> int:
                return 5
            
            def get_user_interest_groups(self, user_id: int) -> list[int]:
                return [1, 2, 3, 4, 5]  # Alle Interest Groups
        
        service = MockPermissionService()
        
        # Level 5 kann alle Transitions
        assert service.can_change_status(5, WorkflowStatus.DRAFT, WorkflowStatus.REVIEWED) == True
        assert service.can_change_status(5, WorkflowStatus.REVIEWED, WorkflowStatus.APPROVED) == True
        assert service.can_change_status(5, WorkflowStatus.DRAFT, WorkflowStatus.APPROVED) == True
        assert service.can_change_status(5, WorkflowStatus.APPROVED, WorkflowStatus.REJECTED) == True
        
        # Level 5 kann nicht same-status
        assert service.can_change_status(5, WorkflowStatus.DRAFT, WorkflowStatus.DRAFT) == False
        
        # Erlaubte Transitions
        draft_transitions = service.get_allowed_transitions(5, WorkflowStatus.DRAFT)
        assert WorkflowStatus.REVIEWED in draft_transitions
        assert WorkflowStatus.APPROVED in draft_transitions
        assert WorkflowStatus.REJECTED in draft_transitions
        assert WorkflowStatus.DRAFT not in draft_transitions
    
    def test_invalid_user_levels(self):
        """Test: Ungültige User-Levels werden abgelehnt."""
        class MockPermissionService(WorkflowPermissionService):
            def can_view_document(self, user_id: int, document) -> bool:
                return False
            
            def can_change_status(self, user_id: int, from_status: WorkflowStatus, to_status: WorkflowStatus) -> bool:
                return False
            
            def get_allowed_transitions(self, user_id: int, current_status: WorkflowStatus) -> list[WorkflowStatus]:
                return []
            
            def get_user_level(self, user_id: int) -> int:
                if user_id == 1:
                    raise ValueError("Invalid user level: 1")
                return 2
            
            def get_user_interest_groups(self, user_id: int) -> list[int]:
                return []
        
        service = MockPermissionService()
        
        # Level 1 ist ungültig
        with pytest.raises(ValueError):
            service.get_user_level(1)
    
    def test_user_interest_groups(self):
        """Test: get_user_interest_groups gibt korrekte Groups zurück."""
        class MockPermissionService(WorkflowPermissionService):
            def can_view_document(self, user_id: int, document) -> bool:
                return False
            
            def can_change_status(self, user_id: int, from_status: WorkflowStatus, to_status: WorkflowStatus) -> bool:
                return False
            
            def get_allowed_transitions(self, user_id: int, current_status: WorkflowStatus) -> list[WorkflowStatus]:
                return []
            
            def get_user_level(self, user_id: int) -> int:
                return 2
            
            def get_user_interest_groups(self, user_id: int) -> list[int]:
                if user_id == 2:
                    return [1, 2]
                elif user_id == 3:
                    return [1, 2, 3]
                elif user_id == 4:
                    return [1, 2, 3, 4]
                elif user_id == 5:
                    return [1, 2, 3, 4, 5]
                return []
        
        service = MockPermissionService()
        
        assert service.get_user_interest_groups(2) == [1, 2]
        assert service.get_user_interest_groups(3) == [1, 2, 3]
        assert service.get_user_interest_groups(4) == [1, 2, 3, 4]
        assert service.get_user_interest_groups(5) == [1, 2, 3, 4, 5]
