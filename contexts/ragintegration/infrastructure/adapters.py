"""
Infrastructure Layer: Adapters

Kombiniert alle Infrastructure Services und Adapters.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from contexts.ragintegration.infrastructure.repositories import (
    SQLAlchemyIndexedDocumentRepository,
    SQLAlchemyDocumentChunkRepository,
    SQLAlchemyChatSessionRepository,
    SQLAlchemyChatMessageRepository
)
from contexts.ragintegration.infrastructure.vector_store_adapter import QdrantVectorStoreAdapter
from contexts.ragintegration.infrastructure.embedding_adapter import OpenAIEmbeddingAdapter
from contexts.ragintegration.infrastructure.vision_extractor_adapter import VisionDataExtractorAdapter
from contexts.ragintegration.infrastructure.services import (
    HeadingAwareChunkingServiceImpl,
    MultiQueryServiceImpl,
    StructuredDataExtractorServiceImpl
)
from contexts.ragintegration.infrastructure.hybrid_search_service import HybridSearchService


class RAGInfrastructureAdapter:
    """Haupt-Adapter für alle RAG Infrastructure Services."""
    
    def __init__(
        self,
        db_session: Session,
        openai_api_key: str,
        collection_name: str = "rag_documents"
    ):
        # Repositories
        self.indexed_document_repo = SQLAlchemyIndexedDocumentRepository(db_session)
        self.document_chunk_repo = SQLAlchemyDocumentChunkRepository(db_session)
        self.chat_session_repo = SQLAlchemyChatSessionRepository(db_session)
        self.chat_message_repo = SQLAlchemyChatMessageRepository(db_session)
        
        # Vector Store & Embedding
        self.vector_store = QdrantVectorStoreAdapter(collection_name)
        self.embedding_service = OpenAIEmbeddingAdapter(openai_api_key)
        
        # Vision & Services
        self.vision_extractor = VisionDataExtractorAdapter()
        self.chunking_service = HeadingAwareChunkingServiceImpl(self.vision_extractor)
        
        # Hybrid Search
        self.hybrid_search_service = HybridSearchService(
            self.vector_store, 
            self.embedding_service
        )
    
    def get_repositories(self) -> Dict[str, Any]:
        """Gibt alle Repositories zurück."""
        return {
            'indexed_document_repo': self.indexed_document_repo,
            'document_chunk_repo': self.document_chunk_repo,
            'chat_session_repo': self.chat_session_repo,
            'chat_message_repo': self.chat_message_repo
        }
    
    def get_services(self) -> Dict[str, Any]:
        """Gibt alle Services zurück."""
        return {
            'vector_store': self.vector_store,
            'embedding_service': self.embedding_service,
            'vision_extractor': self.vision_extractor,
            'chunking_service': self.chunking_service,
            'hybrid_search_service': self.hybrid_search_service
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Gibt System-Informationen zurück."""
        try:
            collection_info = self.vector_store.get_collection_info()
            embedding_info = self.embedding_service.get_model_info()
            
            return {
                'vector_store': {
                    'type': 'Qdrant',
                    'mode': 'in-memory',
                    'collection': collection_info.get('name', 'unknown'),
                    'total_chunks': collection_info.get('points_count', 0),
                    'vector_dimension': collection_info.get('vector_size', 0)
                },
                'embedding_service': embedding_info,
                'repositories': {
                    'indexed_documents': 'SQLAlchemy',
                    'document_chunks': 'SQLAlchemy',
                    'chat_sessions': 'SQLAlchemy',
                    'chat_messages': 'SQLAlchemy'
                },
                'services': {
                    'chunking': 'HeadingAwareChunkingService',
                    'search': 'HybridSearchService',
                    'vision_extraction': 'VisionDataExtractorAdapter'
                }
            }
            
        except Exception as e:
            return {'error': f'Fehler beim Abrufen der System-Info: {str(e)}'}
    
    def health_check(self) -> Dict[str, Any]:
        """Führt Health Check für alle Services durch."""
        health_status = {
            'overall_status': 'healthy',
            'services': {},
            'errors': []
        }
        
        try:
            # Teste Vector Store
            collection_info = self.vector_store.get_collection_info()
            health_status['services']['vector_store'] = 'healthy'
            
        except Exception as e:
            health_status['services']['vector_store'] = 'unhealthy'
            health_status['errors'].append(f'Vector Store: {str(e)}')
            health_status['overall_status'] = 'degraded'
        
        try:
            # Teste Embedding Service
            test_embedding = self.embedding_service.generate_embedding("test")
            if self.embedding_service.validate_embedding(test_embedding):
                health_status['services']['embedding_service'] = 'healthy'
            else:
                health_status['services']['embedding_service'] = 'unhealthy'
                health_status['errors'].append('Embedding Service: Invalid embedding generated')
                health_status['overall_status'] = 'degraded'
                
        except Exception as e:
            health_status['services']['embedding_service'] = 'unhealthy'
            health_status['errors'].append(f'Embedding Service: {str(e)}')
            health_status['overall_status'] = 'degraded'
        
        try:
            # Teste Database Connection (über Repository)
            self.indexed_document_repo.find_all()
            health_status['services']['database'] = 'healthy'
            
        except Exception as e:
            health_status['services']['database'] = 'unhealthy'
            health_status['errors'].append(f'Database: {str(e)}')
            health_status['overall_status'] = 'degraded'
        
        return health_status
    
    def cleanup(self):
        """Räumt Ressourcen auf."""
        try:
            # Schließe Database Session
            if hasattr(self.indexed_document_repo, 'db_session'):
                self.indexed_document_repo.db_session.close()
            
            # Qdrant In-Memory wird automatisch aufgeräumt
            # OpenAI Client benötigt kein explizites Cleanup
            
        except Exception as e:
            print(f"Fehler beim Cleanup: {str(e)}")
    
    def reset_vector_store(self) -> bool:
        """Setzt den Vector Store zurück."""
        try:
            self.vector_store.clear_collection()
            return True
        except Exception as e:
            print(f"Fehler beim Reset des Vector Stores: {str(e)}")
            return False
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Gibt Nutzungsstatistiken zurück."""
        try:
            # Database Statistiken
            total_documents = self.indexed_document_repo.count_by_status('indexed')
            total_chunks = self.document_chunk_repo.count_by_document_id(1)  # Placeholder
            
            # Vector Store Statistiken
            collection_info = self.vector_store.get_collection_info()
            
            return {
                'documents': {
                    'total_indexed': total_documents,
                    'by_status': {
                        'indexed': total_documents,
                        'processing': 0,  # Placeholder
                        'failed': 0  # Placeholder
                    }
                },
                'chunks': {
                    'total_in_vector_store': collection_info.get('points_count', 0),
                    'average_per_document': collection_info.get('points_count', 0) / max(total_documents, 1)
                },
                'vector_store': {
                    'collection_size': collection_info.get('points_count', 0),
                    'vector_dimension': collection_info.get('vector_size', 0)
                }
            }
            
        except Exception as e:
            return {'error': f'Fehler beim Abrufen der Statistiken: {str(e)}'}
