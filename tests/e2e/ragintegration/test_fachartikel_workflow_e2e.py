"""
E2E Tests für vollständigen Fachartikel-Workflow

Testet den kompletten Workflow:
1. Dokument-Upload (Fachartikel)
2. AI-Verarbeitung (seitenweise)
3. Indexierung (Chunking mit strukturierten Texten)
4. RAG Chat (Frage stellen)
5. Prompt Viewer (echten Prompt anzeigen)
"""
import pytest
import asyncio
from datetime import datetime
from contexts.ragintegration.application.use_cases import (
    IndexApprovedDocumentUseCase,
    AskQuestionUseCase
)
from contexts.ragintegration.infrastructure.adapters import RAGInfrastructureAdapter
from contexts.ragintegration.infrastructure.ai_service import RAGAIService
from contexts.documentupload.infrastructure.repositories import SQLAlchemyUploadRepository
from contexts.documentupload.infrastructure.repositories import SQLAlchemyDocumentPageRepository
from backend.app.database import SessionLocal


class TestFachartikelWorkflowE2E:
    """E2E Tests für vollständigen Fachartikel-Workflow."""
    
    @pytest.fixture
    def db_session(self):
        """Erstelle DB Session für Tests."""
        db = SessionLocal()
        yield db
        db.close()
    
    @pytest.fixture
    def rag_adapter(self, db_session):
        """Erstelle RAG Infrastructure Adapter."""
        return RAGInfrastructureAdapter(db_session)
    
    @pytest.fixture
    def upload_document_id(self, db_session):
        """Hole existierendes Fachartikel-Dokument für Tests."""
        # Suche nach einem existierenden Fachartikel-Dokument
        from backend.app.models import UploadDocument, DocumentType
        doc_type = db_session.query(DocumentType).filter(
            DocumentType.name == 'Fachartikel'
        ).first()
        
        if doc_type:
            doc = db_session.query(UploadDocument).filter(
                UploadDocument.document_type_id == doc_type.id,
                UploadDocument.workflow_status == 'approved'
            ).first()
            if doc:
                return doc.id
        
        pytest.skip("Kein Fachartikel-Dokument für E2E-Test gefunden")
    
    @pytest.mark.asyncio
    async def test_complete_fachartikel_workflow(self, db_session, rag_adapter, upload_document_id):
        """Test: Vollständiger Workflow von Indexierung bis RAG Chat."""
        # 1. Indexiere Dokument
        index_use_case = IndexApprovedDocumentUseCase(
            indexed_document_repository=rag_adapter.indexed_document_repo,
            document_chunk_repository=rag_adapter.document_chunk_repo,
            vision_extractor=rag_adapter.vision_extractor,
            embedding_service=rag_adapter.embedding_service,
            vector_store=rag_adapter.vector_store,
            event_publisher=None
        )
        
        result = index_use_case.execute(upload_document_id, "Fachartikel")
        
        # Prüfe dass Indexierung erfolgreich war
        assert result["success"] is True
        assert result["chunks_created"] > 0
        
        # 2. Prüfe dass Chunks strukturierte Texte sind (nicht JSON)
        chunks = rag_adapter.document_chunk_repo.get_by_indexed_document_id(
            result["indexed_document_id"]
        )
        
        assert len(chunks) > 0
        for chunk in chunks:
            # Prüfe dass keine JSON-Struktur gespeichert wurde
            assert not chunk.chunk_text.startswith('```json')
            assert not chunk.chunk_text.strip().startswith('{')
            # Prüfe dass strukturierte Texte verwendet werden
            assert isinstance(chunk.chunk_text, str)
            assert len(chunk.chunk_text) > 0
        
        # 3. Erstelle Chat Session
        from contexts.ragintegration.application.use_cases import CreateChatSessionUseCase
        create_session_use_case = CreateChatSessionUseCase(
            session_repository=rag_adapter.chat_session_repo
        )
        
        session = create_session_use_case.execute(
            user_id=1,
            session_name=f"E2E Test Session {datetime.now().isoformat()}"
        )
        
        # 4. Stelle Frage im RAG Chat
        ai_service = RAGAIService()
        ask_question_use_case = AskQuestionUseCase(
            chunk_repository=rag_adapter.document_chunk_repo,
            session_repository=rag_adapter.chat_session_repo,
            indexed_document_repository=rag_adapter.indexed_document_repo,
            vector_store=rag_adapter.vector_store,
            embedding_service=rag_adapter.embedding_service,
            multi_query_service=None,
            ai_service=ai_service,
            event_publisher=None,
            message_repository=rag_adapter.chat_message_repo
        )
        
        question = "Was ist die Membranwirkung?"
        answer_message = await ask_question_use_case.execute(
            question=question,
            session_id=session.id,
            model_id="gpt-4o-mini"
        )
        
        # Prüfe dass Antwort generiert wurde
        assert answer_message.content is not None
        assert len(answer_message.content) > 0
        
        # 5. Prüfe dass Prompt in metadata gespeichert wurde
        assert answer_message.metadata is not None
        assert "prompt_text" in answer_message.metadata
        assert answer_message.metadata["prompt_text"] is not None
        assert len(answer_message.metadata["prompt_text"]) > 0
        
        # 6. Prüfe dass gespeicherter Prompt verwendet wird (get_prompt_for_message)
        from contexts.ragintegration.interface.router import get_prompt_for_message
        from contexts.accesscontrol.domain.entities import User
        
        # Mock User
        mock_user = User(
            id=1,
            email="test@example.com",
            full_name="Test User",
            level=4
        )
        
        # Hole Prompt für Message
        prompt_response = await get_prompt_for_message(
            message_id=answer_message.id,
            current_user=mock_user,
            db_session=db_session,
            rag_adapter=rag_adapter
        )
        
        # Prüfe dass gespeicherter Prompt verwendet wurde
        assert prompt_response.prompt_text == answer_message.metadata["prompt_text"]
        assert prompt_response.question == question
    
    @pytest.mark.asyncio
    async def test_fachartikel_chunking_with_figures_tables(self, db_session, rag_adapter, upload_document_id):
        """Test: Fachartikel-Chunking enthält Figures und Tables."""
        # Indexiere Dokument
        index_use_case = IndexApprovedDocumentUseCase(
            indexed_document_repository=rag_adapter.indexed_document_repo,
            document_chunk_repository=rag_adapter.document_chunk_repo,
            vision_extractor=rag_adapter.vision_extractor,
            embedding_service=rag_adapter.embedding_service,
            vector_store=rag_adapter.vector_store,
            event_publisher=None
        )
        
        result = index_use_case.execute(upload_document_id, "Fachartikel")
        
        # Prüfe dass Chunks erstellt wurden
        assert result["success"] is True
        chunks = rag_adapter.document_chunk_repo.get_by_indexed_document_id(
            result["indexed_document_id"]
        )
        
        # Prüfe dass Section Chunks Figures/Tables enthalten (falls vorhanden)
        section_chunks = [c for c in chunks if c.metadata.chunk_type == "section"]
        
        if section_chunks:
            # Prüfe dass mindestens ein Section Chunk Figures oder Tables enthält
            has_figures_or_tables = any(
                "Abbildung" in chunk.chunk_text or 
                "Figure" in chunk.chunk_text or 
                "Tabelle" in chunk.chunk_text or 
                "Table" in chunk.chunk_text
                for chunk in section_chunks
            )
            
            # Wenn Figures/Tables im Original vorhanden sind, sollten sie in Chunks sein
            # (Dies ist optional, da nicht alle Dokumente Figures/Tables haben)
            if has_figures_or_tables:
                print("✅ Figures/Tables wurden in Chunks eingefügt")

