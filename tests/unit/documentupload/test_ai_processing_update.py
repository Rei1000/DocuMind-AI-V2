"""
Unit Tests: AI Processing Update Logic

Tests für Update-Logik bei wiederholter AI-Verarbeitung derselben Seite.
Folgt TDD-Prinzip: Tests ZUERST, dann Implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from contexts.documentupload.domain.entities import (
    UploadedDocument, DocumentPage, AIProcessingResult, 
    ProcessingStatus, FileType, ProcessingMethod, DocumentMetadata, FilePath
)
from contexts.documentupload.application.use_cases import ProcessDocumentPageUseCase
from contexts.documentupload.domain.repositories import (
    UploadRepository, DocumentPageRepository, AIResponseRepository, PromptTemplateRepository
)


class TestAIProcessingUpdate:
    """Test-Klasse für AI Processing Update-Logik"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Mock alle benötigten Repositories"""
        return {
            'upload_repo': Mock(spec=UploadRepository),
            'page_repo': Mock(spec=DocumentPageRepository),
            'ai_response_repo': Mock(spec=AIResponseRepository),
            'prompt_template_repo': Mock(spec=PromptTemplateRepository),
            'ai_processing_service': Mock()
        }
    
    @pytest.fixture
    def mock_prompt_template(self):
        """Mock PromptTemplate für Tests"""
        template = Mock()
        template.id = 7
        template.name = "Test Prompt"
        template.ai_model = "gemini-2.5-flash"
        template.prompt_text = "Test prompt text"
        template.temperature = 0.0
        template.max_tokens = 128000
        template.top_p = 0.01
        template.detail_level = "high"
        return template
    
    @pytest.fixture
    def sample_document(self):
        """Beispiel-Dokument für Tests"""
        return UploadedDocument(
            id=123,
            file_type=FileType.PDF,
            file_size_bytes=1024000,
            document_type_id=3,
            metadata=DocumentMetadata(
                filename="test_document.pdf",
                original_filename="test_document.pdf",
                qm_chapter="1.0",
                version="v1.0"
            ),
            file_path=FilePath("/uploads/test_document.pdf"),
            processing_method=ProcessingMethod.VISION,
            processing_status=ProcessingStatus.PENDING,
            uploaded_by_user_id=1,
            uploaded_at=datetime.utcnow(),
            pages=[],
            interest_group_ids=[]
        )
    
    @pytest.fixture
    def sample_page(self):
        """Beispiel-Seite für Tests"""
        return DocumentPage(
            id=456,
            upload_document_id=123,
            page_number=1,
            preview_image_path=FilePath("/previews/page_1.jpg"),
            thumbnail_path=FilePath("/thumbnails/page_1.jpg"),
            dimensions=None,
            created_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_ai_result(self):
        """Beispiel AI-Processing-Result"""
        return AIProcessingResult(
            id=789,
            upload_document_id=123,
            upload_document_page_id=456,
            prompt_template_id=7,
            ai_model_id="gemini-2.5-flash",
            model_name="Gemini 2.5 Flash",
            json_response='{"test": "response"}',
            processing_status="completed",
            tokens_sent=100,
            tokens_received=200,
            total_tokens=300,
            response_time_ms=5000,
            processed_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def use_case(self, mock_repositories):
        """ProcessDocumentPageUseCase mit gemockten Repositories"""
        return ProcessDocumentPageUseCase(
            upload_repo=mock_repositories['upload_repo'],
            page_repo=mock_repositories['page_repo'],
            ai_response_repo=mock_repositories['ai_response_repo'],
            prompt_template_repo=mock_repositories['prompt_template_repo'],
            ai_processing_service=mock_repositories['ai_processing_service']
        )

    # ===== RED PHASE: Tests schreiben (sollen fehlschlagen) =====
    
    @pytest.mark.asyncio
    async def test_process_page_first_time_creates_new_result(self, use_case, mock_repositories, 
                                                           sample_document, sample_page, sample_ai_result, mock_prompt_template):
        """Test: Erste Verarbeitung erstellt neues AIProcessingResult"""
        # Arrange
        mock_repositories['upload_repo'].get_by_id = AsyncMock(return_value=sample_document)
        mock_repositories['page_repo'].get_by_document_id = AsyncMock(return_value=[sample_page])
        mock_repositories['ai_response_repo'].get_by_page_id = AsyncMock(return_value=None)  # Kein existierendes Result
        mock_repositories['ai_response_repo'].save = AsyncMock(return_value=sample_ai_result)
        mock_repositories['prompt_template_repo'].get_default_for_document_type = AsyncMock(return_value=mock_prompt_template)
        mock_repositories['ai_processing_service'].process_page = AsyncMock(return_value={
            "json_response": '{"test": "response"}',
            "model_name": "Gemini 2.5 Flash",
            "tokens_sent": 100,
            "tokens_received": 200,
            "response_time_ms": 5000
        })
        
        # Act
        result = await use_case.execute(upload_document_id=123, page_number=1)
        
        # Assert
        assert result is not None
        mock_repositories['ai_response_repo'].save.assert_called_once()
        mock_repositories['ai_response_repo'].update_result.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_page_second_time_updates_existing_result(self, use_case, mock_repositories,
                                                                 sample_document, sample_page, sample_ai_result, mock_prompt_template):
        """Test: Zweite Verarbeitung updated existierendes AIProcessingResult"""
        # Arrange
        existing_result = sample_ai_result
        mock_repositories['upload_repo'].get_by_id = AsyncMock(return_value=sample_document)
        mock_repositories['page_repo'].get_by_document_id = AsyncMock(return_value=[sample_page])
        mock_repositories['ai_response_repo'].get_by_page_id = AsyncMock(return_value=existing_result)
        mock_repositories['ai_response_repo'].update_result = AsyncMock(return_value=existing_result)
        mock_repositories['prompt_template_repo'].get_default_for_document_type = AsyncMock(return_value=mock_prompt_template)
        
        new_ai_data = {
            "json_response": '{"test": "updated_response"}',
            "model_name": "Gemini 2.5 Flash",
            "tokens_sent": 150,
            "tokens_received": 250,
            "response_time_ms": 6000
        }
        mock_repositories['ai_processing_service'].process_page = AsyncMock(return_value=new_ai_data)
        
        # Act
        result = await use_case.execute(upload_document_id=123, page_number=1)
        
        # Assert
        assert result is not None
        mock_repositories['ai_response_repo'].update_result.assert_called_once()
        mock_repositories['ai_response_repo'].save.assert_not_called()
        
        # Verify that the existing result was updated with new data
        updated_result = mock_repositories['ai_response_repo'].update_result.call_args[0][0]
        assert updated_result.json_response == '{"test": "updated_response"}'
        assert updated_result.tokens_sent == 150
        assert updated_result.tokens_received == 250
    
    @pytest.mark.asyncio
    async def test_process_page_handles_ai_processing_error(self, use_case, mock_repositories,
                                                          sample_document, sample_page, mock_prompt_template):
        """Test: AI Processing Fehler wird korrekt behandelt"""
        # Arrange
        mock_repositories['upload_repo'].get_by_id = AsyncMock(return_value=sample_document)
        mock_repositories['page_repo'].get_by_document_id = AsyncMock(return_value=[sample_page])
        mock_repositories['ai_response_repo'].get_by_page_id = AsyncMock(return_value=None)
        mock_repositories['prompt_template_repo'].get_default_for_document_type = AsyncMock(return_value=mock_prompt_template)
        mock_repositories['ai_processing_service'].process_page = AsyncMock(
            side_effect=Exception("AI Processing failed")
        )
        
        # Act & Assert
        with pytest.raises(Exception, match="AI Processing failed"):
            await use_case.execute(upload_document_id=123, page_number=1)
    
    @pytest.mark.asyncio
    async def test_process_page_document_not_found(self, use_case, mock_repositories):
        """Test: Dokument nicht gefunden wirft ValueError"""
        # Arrange
        mock_repositories['upload_repo'].get_by_id = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Document 123 not found"):
            await use_case.execute(upload_document_id=123, page_number=1)
    
    @pytest.mark.asyncio
    async def test_process_page_page_not_found(self, use_case, mock_repositories, sample_document):
        """Test: Seite nicht gefunden wirft ValueError"""
        # Arrange
        mock_repositories['upload_repo'].get_by_id = AsyncMock(return_value=sample_document)
        mock_repositories['page_repo'].get_by_document_id = AsyncMock(return_value=[])  # Keine Seiten
        
        # Act & Assert
        with pytest.raises(ValueError, match="No pages found for document 123"):
            await use_case.execute(upload_document_id=123, page_number=1)


class TestAIProcessingResultUpdate:
    """Test-Klasse für AIProcessingResult Update-Methoden"""
    
    def test_update_with_new_data(self):
        """Test: AIProcessingResult.update_with_new_data() aktualisiert Felder korrekt"""
        # Arrange
        original_result = AIProcessingResult(
            id=789,
            upload_document_id=123,
            upload_document_page_id=456,
            prompt_template_id=7,
            ai_model_id="gemini-2.5-flash",
            model_name="Gemini 2.5 Flash",
            json_response='{"old": "response"}',
            processing_status="completed",
            tokens_sent=100,
            tokens_received=200,
            total_tokens=300,
            response_time_ms=5000,
            processed_at=datetime(2025, 1, 1, 12, 0, 0)
        )
        
        new_ai_data = {
            "json_response": '{"new": "response"}',
            "model_name": "Gemini 2.5 Flash",
            "tokens_sent": 150,
            "tokens_received": 250,
            "response_time_ms": 6000
        }
        
        # Act
        original_result.update_with_new_data(new_ai_data)
        
        # Assert
        assert original_result.json_response == '{"new": "response"}'
        assert original_result.tokens_sent == 150
        assert original_result.tokens_received == 250
        assert original_result.response_time_ms == 6000
        # processed_at sollte aktualisiert werden
        assert original_result.processed_at > datetime(2025, 1, 1, 12, 0, 0)
