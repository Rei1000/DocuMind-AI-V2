import pytest
from unittest.mock import AsyncMock
from contexts.documentupload.application.use_cases import GetDocumentsByWorkflowStatusUseCase
from contexts.documentupload.domain.entities import UploadedDocument, DocumentMetadata
from contexts.documentupload.domain.value_objects import WorkflowStatus, FileType, ProcessingMethod, ProcessingStatus, FilePath
from datetime import datetime
from pathlib import Path

@pytest.fixture
def mock_upload_repo():
    return AsyncMock()

@pytest.fixture
def get_documents_use_case(mock_upload_repo):
    return GetDocumentsByWorkflowStatusUseCase(upload_repository=mock_upload_repo)

@pytest.mark.asyncio
async def test_document_includes_interest_group_ids(get_documents_use_case, mock_upload_repo):
    """Test: Dokumente enthalten Interest Group IDs"""
    # GIVEN: Ein Dokument mit Interest Groups [1, 3, 5]
    status = WorkflowStatus.DRAFT
    
    mock_document = UploadedDocument(
            id=1,
            metadata=DocumentMetadata(
                filename="test.pdf", 
                original_filename="test.pdf",
                qm_chapter="AA",
                version="v1.0"
            ),
            file_path=FilePath("/data/uploads/test.pdf"),
            workflow_status=status,
            uploaded_at=datetime.utcnow(),
            file_type=FileType.PDF,
            file_size_bytes=1000,
            document_type_id=1,
            processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.COMPLETED,
            uploaded_by_user_id=1,
            interest_group_ids=[1, 3, 5]  # Interest Groups
        )
    
    mock_upload_repo.get_by_workflow_status.return_value = [mock_document]

    # WHEN: Dokumente für Status "draft" abgerufen werden
    documents = await get_documents_use_case.execute(status=status)

    # THEN: Response enthält interest_group_ids
    assert len(documents) == 1
    assert documents[0].interest_group_ids == [1, 3, 5]
    mock_upload_repo.get_by_workflow_status.assert_called_once_with(status, None, None)

@pytest.mark.asyncio
async def test_document_without_interest_groups(get_documents_use_case, mock_upload_repo):
    """Test: Dokument ohne Interest Groups"""
    status = WorkflowStatus.DRAFT
    
    mock_document = UploadedDocument(
        id=1,
        metadata=DocumentMetadata(
            filename="test.pdf", 
            original_filename="test.pdf",
            qm_chapter="AA",
            version="v1.0"
        ),
            file_path=FilePath("/data/uploads/test.pdf"),
        workflow_status=status,
        uploaded_at=datetime.utcnow(),
        file_type=FileType.PDF,
        file_size_bytes=1000,
        document_type_id=1,
        processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.COMPLETED,
            uploaded_by_user_id=1,
            interest_group_ids=[]  # Keine Interest Groups
        )
    
    mock_upload_repo.get_by_workflow_status.return_value = [mock_document]

    documents = await get_documents_use_case.execute(status=status)

    assert len(documents) == 1
    assert documents[0].interest_group_ids == []

@pytest.mark.asyncio
async def test_filter_documents_by_user_interest_groups(get_documents_use_case, mock_upload_repo):
    """Test: Dokumente nach User Interest Groups filtern"""
    # GIVEN: User gehört zu Interest Groups [1, 3]
    # GIVEN: Dokumente mit verschiedenen Interest Groups
    status = WorkflowStatus.DRAFT
    user_interest_groups = [1, 3]
    
    # Dokument 1: User kann sehen (Interest Groups [1, 3])
    doc1 = UploadedDocument(
        id=1,
        metadata=DocumentMetadata(
            filename="doc1.pdf", 
            original_filename="doc1.pdf",
            qm_chapter="AA",
            version="v1.0"
        ),
            file_path=FilePath("/data/uploads/doc1.pdf"),
        workflow_status=status,
        uploaded_at=datetime.utcnow(),
        file_type=FileType.PDF,
        file_size_bytes=1000,
        document_type_id=1,
        processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.COMPLETED,
            uploaded_by_user_id=1,
            interest_group_ids=[1, 3]  # User kann sehen
        )
    
    # Dokument 2: User kann NICHT sehen (Interest Groups [5, 7])
    doc2 = UploadedDocument(
        id=2,
        metadata=DocumentMetadata(
            filename="doc2.pdf", 
            original_filename="doc2.pdf",
            qm_chapter="BB",
            version="v1.0"
        ),
            file_path=FilePath("/data/uploads/doc2.pdf"),
        workflow_status=status,
        uploaded_at=datetime.utcnow(),
        file_type=FileType.PDF,
        file_size_bytes=2000,
        document_type_id=2,
        processing_method=ProcessingMethod.OCR,
            processing_status=ProcessingStatus.COMPLETED,
            uploaded_by_user_id=1,
            interest_group_ids=[5, 7]  # User kann NICHT sehen
        )
    
    # Repository sollte nur Dokumente zurückgeben, die User sehen kann
    mock_upload_repo.get_by_workflow_status.return_value = [doc1]  # Nur doc1

    # WHEN: Dokumente für User abgerufen werden
    documents = await get_documents_use_case.execute(
        status=status,
        interest_group_ids=user_interest_groups
    )

    # THEN: Nur sichtbare Dokumente werden zurückgegeben
    assert len(documents) == 1
    assert documents[0].id == 1
    assert documents[0].interest_group_ids == [1, 3]
    mock_upload_repo.get_by_workflow_status.assert_called_once_with(
        status, user_interest_groups, None
    )
