"""
Integration Tests für RAG Interest Group Filtering (Phase 2)

Testet, dass RAG Chat Dokumente basierend auf User-Level und Interest Groups filtert:
- Level 1-3: Nur eigene Interest Groups
- Level 4-5: Alle Dokumente (keine Filterung)
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from datetime import datetime

from contexts.ragintegration.application.use_cases import AskQuestionUseCase
from contexts.ragintegration.domain.entities import ChatMessage, ChatSession
from contexts.documentupload.infrastructure.permission_service import SQLAlchemyWorkflowPermissionService


class TestRAGInterestGroupFiltering:
    """Test Suite für Interest Group Filtering im RAG Chat"""
    
    @pytest.fixture
    def mock_permission_service(self):
        """Mock Permission Service"""
        service = MagicMock(spec=SQLAlchemyWorkflowPermissionService)
        return service
    
    @pytest.fixture
    def mock_repositories(self):
        """Mock Repositories"""
        return {
            'chunk_repository': MagicMock(),
            'session_repository': MagicMock(),
            'indexed_document_repository': MagicMock(),
            'message_repository': MagicMock()
        }
    
    @pytest.fixture
    def mock_services(self):
        """Mock Services"""
        return {
            'vector_store': MagicMock(),
            'embedding_service': MagicMock(),
            'multi_query_service': MagicMock(),
            'ai_service': AsyncMock(),
            'event_publisher': MagicMock()
        }
    
    @pytest.fixture
    def ask_question_use_case(self, mock_repositories, mock_services, mock_permission_service):
        """AskQuestionUseCase mit gemockten Dependencies"""
        use_case = AskQuestionUseCase(
            chunk_repository=mock_repositories['chunk_repository'],
            session_repository=mock_repositories['session_repository'],
            indexed_document_repository=mock_repositories['indexed_document_repository'],
            vector_store=mock_services['vector_store'],
            embedding_service=mock_services['embedding_service'],
            multi_query_service=mock_services['multi_query_service'],
            ai_service=mock_services['ai_service'],
            event_publisher=mock_services['event_publisher'],
            message_repository=mock_repositories['message_repository']
        )
        
        # Füge Permission Service hinzu (für Phase 2)
        use_case.permission_service = mock_permission_service
        
        return use_case
    
    @pytest.fixture
    def sample_indexed_docs(self):
        """Sample Indexed Documents"""
        return [
            type('IndexedDocument', (), {
                'id': 1,
                'upload_document_id': 10,
                'collection_name': 'doc_10_collection'
            })(),
            type('IndexedDocument', (), {
                'id': 2,
                'upload_document_id': 20,
                'collection_name': 'doc_20_collection'
            })()
        ]
    
    # ============================================================================
    # Phase 2.1: Level 1-3 User sieht nur eigene Interest Groups
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_rag_chat_level_1_only_sees_own_interest_group(
        self, ask_question_use_case, mock_repositories, mock_services, 
        mock_permission_service, sample_indexed_docs
    ):
        """Test: Level 1 User sieht nur Dokumente aus seiner Interest Group"""
        # Arrange
        user_id = 1
        user_level = 1
        user_interest_groups = [1]  # Nur IG 1
        
        # Mock Permission Service
        mock_permission_service.get_user_level.return_value = user_level
        mock_permission_service.get_user_interest_groups.return_value = user_interest_groups
        
        # Mock Indexed Documents (alle Dokumente)
        mock_repositories['indexed_document_repository'].get_all.return_value = sample_indexed_docs
        
        # Mock Vector Store Search Results
        # Doc 10 gehört zu IG 1, Doc 20 gehört zu IG 2
        results_doc_10 = [
            {
                'chunk_id': 'chunk_1',
                'score': 0.9,
                'metadata': {
                    'document_id': 10,
                    'chunk_text': 'Text from doc 10',
                    'page_numbers': [1]
                }
            }
        ]
        results_doc_20 = [
            {
                'chunk_id': 'chunk_2',
                'score': 0.8,
                'metadata': {
                    'document_id': 20,
                    'chunk_text': 'Text from doc 20',
                    'page_numbers': [1]
                }
            }
        ]
        
        mock_services['vector_store'].search_with_hybrid_scoring.side_effect = [
            results_doc_10,  # Für doc_10_collection
            results_doc_20   # Für doc_20_collection
        ]
        
        # Mock: Dokument 10 gehört zu IG 1, Dokument 20 gehört zu IG 2
        # (Wird in _filter_results_by_interest_group geprüft)
        
        # Mock AI Service
        mock_services['ai_service'].generate_response_async.return_value = {
            'answer': 'Test answer',
            'model_used': 'gpt-4o-mini',
            'tokens_used': 50
        }
        
        # Mock Message Repository
        saved_message = ChatMessage(
            id=1,
            session_id=1,
            role='assistant',
            content='Test answer',
            source_references=[],
            ai_model_used='gpt-4o-mini',
            created_at=datetime.now()
        )
        mock_repositories['message_repository'].save.return_value = saved_message
        
        # Mock Multi Query
        mock_services['multi_query_service'].generate_queries.return_value = ['Test question']
        mock_services['embedding_service'].generate_embedding.return_value = [0.1] * 1536
        
        # Act
        # TODO: Implementiere _filter_results_by_interest_group in AskQuestionUseCase
        # Der Use Case muss die Ergebnisse nach Interest Groups filtern
        
        # Assert
        # Nach Implementierung: Nur Doc 10 sollte in source_references sein
        # (Dieser Test schlägt fehl, bis _filter_results_by_interest_group implementiert ist)
    
    # ============================================================================
    # Phase 2.2: Level 4-5 User sieht alle Dokumente
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_rag_chat_level_4_sees_all_documents(
        self, ask_question_use_case, mock_repositories, mock_services,
        mock_permission_service, sample_indexed_docs
    ):
        """Test: Level 4 User sieht alle Dokumente (keine IG-Filterung)"""
        # Arrange
        user_id = 2
        user_level = 4
        user_interest_groups = []  # Leere Liste = alle IG
        
        # Mock Permission Service
        mock_permission_service.get_user_level.return_value = user_level
        mock_permission_service.get_user_interest_groups.return_value = user_interest_groups
        
        # Mock Indexed Documents
        mock_repositories['indexed_document_repository'].get_all.return_value = sample_indexed_docs
        
        # Mock Vector Store Search Results
        results_doc_10 = [
            {
                'chunk_id': 'chunk_1',
                'score': 0.9,
                'metadata': {
                    'document_id': 10,
                    'chunk_text': 'Text from doc 10',
                    'page_numbers': [1]
                }
            }
        ]
        results_doc_20 = [
            {
                'chunk_id': 'chunk_2',
                'score': 0.8,
                'metadata': {
                    'document_id': 20,
                    'chunk_text': 'Text from doc 20',
                    'page_numbers': [1]
                }
            }
        ]
        
        mock_services['vector_store'].search_with_hybrid_scoring.side_effect = [
            results_doc_10,
            results_doc_20
        ]
        
        # Mock AI Service
        mock_services['ai_service'].generate_response_async.return_value = {
            'answer': 'Test answer',
            'model_used': 'gpt-4o-mini',
            'tokens_used': 50
        }
        
        # Mock Message Repository
        saved_message = ChatMessage(
            id=1,
            session_id=1,
            role='assistant',
            content='Test answer',
            source_references=[],
            ai_model_used='gpt-4o-mini',
            created_at=datetime.now()
        )
        mock_repositories['message_repository'].save.return_value = saved_message
        
        # Mock Multi Query
        mock_services['multi_query_service'].generate_queries.return_value = ['Test question']
        mock_services['embedding_service'].generate_embedding.return_value = [0.1] * 1536
        
        # Act
        # TODO: Implementiere _filter_results_by_interest_group
        # Level 4+ sollte keine Filterung anwenden
        
        # Assert
        # Nach Implementierung: Beide Dokumente sollten in source_references sein
        # (Dieser Test schlägt fehl, bis _filter_results_by_interest_group implementiert ist)

