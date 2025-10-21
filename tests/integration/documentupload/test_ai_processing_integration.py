"""
Integration Tests: AI Processing Update Logic

Tests für die komplette AI Processing Pipeline mit echter Datenbank.
Folgt TDD-Prinzip: Tests ZUERST, dann Debug.
"""

import pytest
import asyncio
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contexts.documentupload.application.use_cases import ProcessDocumentPageUseCase
from contexts.documentupload.infrastructure.repositories import (
    SQLAlchemyUploadRepository,
    SQLAlchemyDocumentPageRepository, 
    SQLAlchemyAIResponseRepository
)
from contexts.documentupload.domain.entities import (
    UploadedDocument, DocumentPage, AIProcessingResult,
    FileType, ProcessingMethod, ProcessingStatus, DocumentMetadata, FilePath
)
from backend.app.models import Base


class TestAIProcessingIntegration:
    """Integration Tests für AI Processing Update-Logik"""
    
    @pytest.fixture
    def db_session(self):
        """Erstelle Test-Datenbank Session"""
        # In-Memory SQLite für Tests
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        yield session
        
        session.close()
    
    @pytest.fixture
    def repositories(self, db_session):
        """Erstelle Repository-Instanzen"""
        return {
            'upload_repo': SQLAlchemyUploadRepository(db_session),
            'page_repo': SQLAlchemyDocumentPageRepository(db_session),
            'ai_response_repo': SQLAlchemyAIResponseRepository(db_session)
        }
    
    @pytest.fixture
    def sample_document(self):
        """Beispiel-Dokument für Tests"""
        return UploadedDocument(
            id=None,
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
            id=None,
            upload_document_id=None,  # Wird nach Document-Save gesetzt
            page_number=1,
            preview_image_path=FilePath("/previews/page_1.jpg"),
            thumbnail_path=FilePath("/thumbnails/page_1.jpg"),
            dimensions=None,
            created_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def mock_ai_processing_service(self):
        """Mock AI Processing Service"""
        from unittest.mock import Mock, AsyncMock
        
        service = Mock()
        service.process_page = AsyncMock(return_value={
            "json_response": '{"test": "response"}',
            "model_name": "Gemini 2.5 Flash",
            "tokens_sent": 100,
            "tokens_received": 200,
            "response_time_ms": 5000
        })
        return service
    
    @pytest.fixture
    def mock_prompt_template_repo(self):
        """Mock Prompt Template Repository"""
        from unittest.mock import Mock, AsyncMock
        
        repo = Mock()
        template = Mock()
        template.id = 7
        template.name = "Test Prompt"
        template.ai_model = "gemini-2.5-flash"
        template.prompt_text = "Test prompt text"
        template.temperature = 0.0
        template.max_tokens = 128000
        template.top_p = 0.01
        template.detail_level = "high"
        
        repo.get_default_for_document_type = AsyncMock(return_value=template)
        return repo

    # ===== INTEGRATION TESTS =====
    
    @pytest.mark.asyncio
    async def test_first_processing_creates_new_result(self, db_session, repositories, 
                                                     sample_document, sample_page, 
                                                     mock_ai_processing_service, mock_prompt_template_repo):
        """Test: Erste Verarbeitung erstellt neues AIProcessingResult"""
        # Arrange: Erstelle Document und Page
        saved_document = await repositories['upload_repo'].save(sample_document)
        sample_page.upload_document_id = saved_document.id
        saved_page = await repositories['page_repo'].save(sample_page)
        
        # Arrange: Use Case
        use_case = ProcessDocumentPageUseCase(
            upload_repo=repositories['upload_repo'],
            page_repo=repositories['page_repo'],
            ai_response_repo=repositories['ai_response_repo'],
            prompt_template_repo=mock_prompt_template_repo,
            ai_processing_service=mock_ai_processing_service
        )
        
        # Act: Erste Verarbeitung
        result = await use_case.execute(
            upload_document_id=saved_document.id,
            page_number=1
        )
        
        # Assert: Neues Result erstellt
        assert result is not None
        assert result.upload_document_page_id == saved_page.id
        assert result.json_response == '{"test": "response"}'
        
        # Verify: In Datenbank gespeichert
        db_result = await repositories['ai_response_repo'].get_by_page_id(saved_page.id)
        assert db_result is not None
        assert db_result.id == result.id
    
    @pytest.mark.asyncio
    async def test_second_processing_updates_existing_result(self, db_session, repositories,
                                                           sample_document, sample_page,
                                                           mock_ai_processing_service, mock_prompt_template_repo):
        """Test: Zweite Verarbeitung updated existierendes AIProcessingResult"""
        # Arrange: Erstelle Document und Page
        saved_document = await repositories['upload_repo'].save(sample_document)
        sample_page.upload_document_id = saved_document.id
        saved_page = await repositories['page_repo'].save(sample_page)
        
        # Arrange: Erste Verarbeitung
        use_case = ProcessDocumentPageUseCase(
            upload_repo=repositories['upload_repo'],
            page_repo=repositories['page_repo'],
            ai_response_repo=repositories['ai_response_repo'],
            prompt_template_repo=mock_prompt_template_repo,
            ai_processing_service=mock_ai_processing_service
        )
        
        # Act: Erste Verarbeitung
        first_result = await use_case.execute(
            upload_document_id=saved_document.id,
            page_number=1
        )
        
        # Arrange: Ändere AI Service Response für zweite Verarbeitung
        mock_ai_processing_service.process_page.return_value = {
            "json_response": '{"test": "updated_response"}',
            "model_name": "Gemini 2.5 Flash",
            "tokens_sent": 150,
            "tokens_received": 250,
            "response_time_ms": 6000
        }
        
        # Act: Zweite Verarbeitung (sollte UPDATE sein)
        second_result = await use_case.execute(
            upload_document_id=saved_document.id,
            page_number=1
        )
        
        # Assert: Gleiche ID, aber updated Daten
        assert second_result.id == first_result.id  # Gleiche ID = UPDATE
        assert second_result.json_response == '{"test": "updated_response"}'
        assert second_result.tokens_sent == 150
        assert second_result.tokens_received == 250
        
        # Verify: Nur ein Eintrag in Datenbank
        db_results = await repositories['ai_response_repo'].get_by_document_id(saved_document.id)
        assert len(db_results) == 1
        assert db_results[0].id == first_result.id
    
    @pytest.mark.asyncio
    async def test_get_by_page_id_works_correctly(self, db_session, repositories, sample_document, sample_page):
        """Test: get_by_page_id() funktioniert korrekt"""
        # Arrange: Erstelle Document, Page und AI Result
        saved_document = await repositories['upload_repo'].save(sample_document)
        sample_page.upload_document_id = saved_document.id
        saved_page = await repositories['page_repo'].save(sample_page)
        
        # Arrange: Erstelle AI Result direkt
        ai_result = AIProcessingResult(
            id=None,
            upload_document_id=saved_document.id,
            upload_document_page_id=saved_page.id,
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
        
        saved_ai_result = await repositories['ai_response_repo'].save(ai_result)
        
        # Act: Hole Result by page_id
        found_result = await repositories['ai_response_repo'].get_by_page_id(saved_page.id)
        
        # Assert: Result gefunden
        assert found_result is not None
        assert found_result.id == saved_ai_result.id
        assert found_result.upload_document_page_id == saved_page.id
    
    @pytest.mark.asyncio
    async def test_update_result_works_correctly(self, db_session, repositories, sample_document, sample_page):
        """Test: update_result() funktioniert korrekt"""
        # Arrange: Erstelle Document, Page und AI Result
        saved_document = await repositories['upload_repo'].save(sample_document)
        sample_page.upload_document_id = saved_document.id
        saved_page = await repositories['page_repo'].save(sample_page)
        
        # Arrange: Erstelle AI Result
        ai_result = AIProcessingResult(
            id=None,
            upload_document_id=saved_document.id,
            upload_document_page_id=saved_page.id,
            prompt_template_id=7,
            ai_model_id="gemini-2.5-flash",
            model_name="Gemini 2.5 Flash",
            json_response='{"test": "original"}',
            processing_status="completed",
            tokens_sent=100,
            tokens_received=200,
            total_tokens=300,
            response_time_ms=5000,
            processed_at=datetime.utcnow()
        )
        
        saved_ai_result = await repositories['ai_response_repo'].save(ai_result)
        
        # Act: Update Result
        saved_ai_result.json_response = '{"test": "updated"}'
        saved_ai_result.tokens_sent = 150
        saved_ai_result.tokens_received = 250
        
        updated_result = await repositories['ai_response_repo'].update_result(saved_ai_result)
        
        # Assert: Result updated
        assert updated_result.id == saved_ai_result.id
        assert updated_result.json_response == '{"test": "updated"}'
        assert updated_result.tokens_sent == 150
        assert updated_result.tokens_received == 250
        
        # Verify: In Datenbank updated
        db_result = await repositories['ai_response_repo'].get_by_page_id(saved_page.id)
        assert db_result.json_response == '{"test": "updated"}'
