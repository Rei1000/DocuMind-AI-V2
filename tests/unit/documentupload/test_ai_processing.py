"""
Unit Tests für AI-Verarbeitung (TDD)

Context: documentupload (Phase 2.7: AI-Verarbeitung)

Test-Strategie:
1. Domain Layer: AIProcessingResult Entity
2. Application Layer: ProcessDocumentPageUseCase
3. Infrastructure Layer: AIProcessingService
"""

import pytest
from datetime import datetime
from typing import Dict, Any


# ==================== DOMAIN LAYER TESTS ====================

class TestAIProcessingResultEntity:
    """Tests für AIProcessingResult Domain Entity"""
    
    def test_create_valid_ai_processing_result(self):
        """Test: Erstelle valides AI-Verarbeitungsergebnis"""
        from contexts.documentupload.domain.entities import AIProcessingResult
        
        result = AIProcessingResult(
            id=1,
            upload_document_id=100,
            upload_document_page_id=200,
            prompt_template_id=10,
            ai_model_id=5,
            model_name="gpt-4o-mini",
            json_response='{"material": "Kunststoff", "critical_rules": []}',
            processing_status="completed",
            tokens_sent=1500,
            tokens_received=800,
            total_tokens=2300,
            response_time_ms=2500,
            processed_at=datetime.utcnow()
        )
        
        assert result.id == 1
        assert result.upload_document_id == 100
        assert result.processing_status == "completed"
        assert result.total_tokens == 2300
        assert result.is_completed()
    
    def test_ai_processing_result_failed_status(self):
        """Test: AI-Verarbeitung mit Failed-Status"""
        from contexts.documentupload.domain.entities import AIProcessingResult
        
        result = AIProcessingResult(
            id=2,
            upload_document_id=101,
            upload_document_page_id=201,
            prompt_template_id=10,
            ai_model_id=5,
            model_name="gemini-2.0-flash",
            json_response="{}",
            processing_status="failed",
            error_message="API Rate Limit exceeded",
            tokens_sent=0,
            tokens_received=0,
            total_tokens=0,
            response_time_ms=0,
            processed_at=datetime.utcnow()
        )
        
        assert result.processing_status == "failed"
        assert result.is_failed()
        assert result.error_message == "API Rate Limit exceeded"
    
    def test_parse_json_response(self):
        """Test: JSON-Response parsen"""
        from contexts.documentupload.domain.entities import AIProcessingResult
        
        result = AIProcessingResult(
            id=3,
            upload_document_id=102,
            upload_document_page_id=202,
            prompt_template_id=10,
            ai_model_id=5,
            model_name="gpt-5-mini",
            json_response='{"material": "Stahl", "thickness": "2mm"}',
            processing_status="completed",
            tokens_sent=1000,
            tokens_received=500,
            total_tokens=1500,
            response_time_ms=3000,
            processed_at=datetime.utcnow()
        )
        
        parsed = result.get_parsed_json()
        assert parsed["material"] == "Stahl"
        assert parsed["thickness"] == "2mm"


# ==================== VALUE OBJECTS TESTS ====================

class TestProcessingStatusVO:
    """Tests für ProcessingStatus Value Object"""
    
    def test_valid_processing_statuses(self):
        """Test: Alle gültigen Status"""
        from contexts.documentupload.domain.value_objects import ProcessingStatus
        
        completed = ProcessingStatus("completed")
        failed = ProcessingStatus("failed")
        partial = ProcessingStatus("partial")
        
        assert completed.value == "completed"
        assert failed.value == "failed"
        assert partial.value == "partial"
    
    def test_invalid_processing_status_raises_error(self):
        """Test: Ungültiger Status wirft Fehler"""
        from contexts.documentupload.domain.value_objects import ProcessingStatus
        
        with pytest.raises(ValueError, match="is not a valid ProcessingStatus"):
            ProcessingStatus("invalid_status")


class TestAIResponseVO:
    """Tests für AIResponse Value Object"""
    
    def test_create_valid_ai_response(self):
        """Test: Valide AI-Response erstellen"""
        from contexts.documentupload.domain.value_objects import AIResponse
        
        response = AIResponse(
            json_data='{"key": "value"}',
            tokens_sent=1000,
            tokens_received=500,
            response_time_ms=2000
        )
        
        assert response.json_data == '{"key": "value"}'
        assert response.tokens_sent == 1000
        assert response.tokens_received == 500
        assert response.total_tokens == 1500
        assert response.response_time_ms == 2000
    
    def test_ai_response_with_invalid_json(self):
        """Test: Ungültiges JSON wirft Fehler"""
        from contexts.documentupload.domain.value_objects import AIResponse
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            AIResponse(
                json_data="not a json",
                tokens_sent=100,
                tokens_received=50,
                response_time_ms=1000
            )


# ==================== USE CASE TESTS ====================

class TestProcessDocumentPageUseCase:
    """Tests für ProcessDocumentPageUseCase"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Mock Repositories für Tests"""
        from unittest.mock import Mock
        
        upload_repo = Mock()
        page_repo = Mock()
        ai_response_repo = Mock()
        prompt_template_repo = Mock()
        
        return {
            "upload_repo": upload_repo,
            "page_repo": page_repo,
            "ai_response_repo": ai_response_repo,
            "prompt_template_repo": prompt_template_repo
        }
    
    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI Processing Service"""
        from unittest.mock import Mock, AsyncMock
        
        service = Mock()
        service.process_page = AsyncMock(return_value={
            "json_response": '{"material": "Kunststoff"}',
            "model_name": "gpt-4o-mini",
            "tokens_sent": 1500,
            "tokens_received": 800,
            "total_tokens": 2300,
            "response_time_ms": 2500
        })
        return service
    
    @pytest.mark.asyncio
    async def test_process_single_page_success(self, mock_repositories, mock_ai_service):
        """Test: Erfolgreiche Verarbeitung einer Seite"""
        from contexts.documentupload.application.use_cases import ProcessDocumentPageUseCase
        from unittest.mock import Mock, AsyncMock
        
        # Arrange
        use_case = ProcessDocumentPageUseCase(
            upload_repo=mock_repositories["upload_repo"],
            page_repo=mock_repositories["page_repo"],
            ai_response_repo=mock_repositories["ai_response_repo"],
            prompt_template_repo=mock_repositories["prompt_template_repo"],
            ai_processing_service=mock_ai_service
        )
        
        # Mock Daten
        mock_page = Mock()
        mock_page.id = 200
        mock_page.upload_document_id = 100
        mock_page.page_number = 1
        mock_page.preview_image_path = "/path/to/preview.png"
        
        mock_upload = Mock()
        mock_upload.id = 100
        mock_upload.document_type_id = 10
        
        mock_prompt_template = Mock()
        mock_prompt_template.id = 5
        mock_prompt_template.prompt_text = "Analyze this document..."
        mock_prompt_template.ai_model_id = 3
        mock_prompt_template.temperature = 0.3
        mock_prompt_template.max_tokens = 4000
        mock_prompt_template.top_p = 0.9
        mock_prompt_template.detail_level = "high"
        
        # Setup async mocks
        mock_repositories["page_repo"].get_by_document_id = AsyncMock(return_value=[mock_page])
        mock_repositories["upload_repo"].get_by_id = AsyncMock(return_value=mock_upload)
        mock_repositories["prompt_template_repo"].get_default_for_document_type = AsyncMock(return_value=mock_prompt_template)
        mock_repositories["ai_response_repo"].get_by_page_id = AsyncMock(return_value=None)  # No existing result
        mock_repositories["ai_response_repo"].save = AsyncMock(return_value=Mock(
            processing_status="completed",
            tokens_sent=1500,
            tokens_received=800,
            total_tokens=2300
        ))
        
        # Act
        result = await use_case.execute(
            upload_document_id=100,
            page_number=1
        )
        
        # Assert
        assert result.processing_status == "completed"
        assert result.tokens_sent == 1500
        assert result.tokens_received == 800
        assert result.total_tokens == 2300
        mock_ai_service.process_page.assert_called_once()
        mock_repositories["ai_response_repo"].save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_page_with_no_default_prompt(self, mock_repositories, mock_ai_service):
        """Test: Fehler wenn kein Standard-Prompt existiert"""
        from contexts.documentupload.application.use_cases import ProcessDocumentPageUseCase
        from unittest.mock import Mock, AsyncMock
        
        # Arrange
        use_case = ProcessDocumentPageUseCase(
            upload_repo=mock_repositories["upload_repo"],
            page_repo=mock_repositories["page_repo"],
            ai_response_repo=mock_repositories["ai_response_repo"],
            prompt_template_repo=mock_repositories["prompt_template_repo"],
            ai_processing_service=mock_ai_service
        )
        
        mock_page = Mock()
        mock_page.id = 200
        mock_page.upload_document_id = 100
        mock_page.page_number = 1
        
        mock_upload = Mock()
        mock_upload.id = 100
        mock_upload.document_type_id = 10
        
        # Setup async mocks
        mock_repositories["page_repo"].get_by_document_id = AsyncMock(return_value=[mock_page])
        mock_repositories["upload_repo"].get_by_id = AsyncMock(return_value=mock_upload)
        mock_repositories["prompt_template_repo"].get_default_for_document_type = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(ValueError, match="No default prompt template"):
            await use_case.execute(upload_document_id=100, page_number=1)


# ==================== REPOSITORY INTERFACE TESTS ====================

class TestAIResponseRepository:
    """Tests für AIResponseRepository Interface"""
    
    def test_repository_interface_exists(self):
        """Test: Repository Interface ist definiert"""
        from contexts.documentupload.domain.repositories import AIResponseRepository
        
        assert hasattr(AIResponseRepository, "save")
        assert hasattr(AIResponseRepository, "get_by_page_id")
        assert hasattr(AIResponseRepository, "get_by_document_id")

