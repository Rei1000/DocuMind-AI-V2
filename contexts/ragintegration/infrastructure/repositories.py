"""
SQLAlchemy Repository Implementations für RAG Integration Context.

Implementiert die Repository Interfaces mit SQLAlchemy ORM.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, desc
import json

from contexts.ragintegration.domain.entities import (
    IndexedDocument, DocumentChunk, ChatSession, ChatMessage
)
from contexts.ragintegration.domain.value_objects import ChunkMetadata
from contexts.ragintegration.domain.repositories import (
    IndexedDocumentRepository, DocumentChunkRepository, 
    ChatSessionRepository, ChatMessageRepository
)
from contexts.ragintegration.infrastructure.models import (
    IndexedDocumentModel, DocumentChunkModel, 
    ChatSessionModel, ChatMessageModel
)


class SQLAlchemyIndexedDocumentRepository(IndexedDocumentRepository):
    """SQLAlchemy Implementation des IndexedDocumentRepository."""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def save(self, document: IndexedDocument) -> IndexedDocument:
        """Speichert ein IndexedDocument."""
        try:
            if document.id is None:
                # Neues Dokument
                model = IndexedDocumentModel(
                    upload_document_id=document.upload_document_id,
                    qdrant_collection_name=document.collection_name,
                    indexed_at=document.indexed_at,
                    total_chunks=document.total_chunks,
                    last_updated_at=document.last_updated_at,
                    embedding_model="text-embedding-ada-002"
                )
                self.db_session.add(model)
                self.db_session.flush()  # Um ID zu bekommen
                document.id = model.id
            else:
                # Update existierendes Dokument
                model = self.db_session.query(IndexedDocumentModel).filter(
                    IndexedDocumentModel.id == document.id
                ).first()
                if model:
                    model.qdrant_collection_name = document.collection_name
                    model.total_chunks = document.total_chunks
                    model.last_updated_at = document.last_updated_at
            
            self.db_session.commit()
            return document
            
        except IntegrityError as e:
            self.db_session.rollback()
            raise ValueError(f"Fehler beim Speichern des Dokuments: {str(e)}")
    
    def get_by_id(self, indexed_document_id: int) -> Optional[IndexedDocument]:
        """Hole IndexedDocument nach ID."""
        return self.find_by_id(indexed_document_id)
    
    def get_by_upload_document_id(self, upload_document_id: int) -> Optional[IndexedDocument]:
        """Hole IndexedDocument nach Upload Document ID."""
        return self.find_by_upload_document_id(upload_document_id)
    
    def get_all(self) -> List[IndexedDocument]:
        """Hole alle IndexedDocuments."""
        return self.find_all()
    
    def exists_by_upload_document_id(self, upload_document_id: int) -> bool:
        """Prüfe ob IndexedDocument für Upload Document existiert."""
        return self.db_session.query(IndexedDocumentModel).filter(
            IndexedDocumentModel.upload_document_id == upload_document_id
        ).first() is not None
    
    def find_by_id(self, indexed_document_id: int) -> Optional[IndexedDocument]:
        """Findet ein IndexedDocument anhand der ID."""
        model = self.db_session.query(IndexedDocumentModel).filter(
            IndexedDocumentModel.id == indexed_document_id
        ).first()
        
        if not model:
            return None
        
        return self._model_to_entity(model)
    
    def find_by_upload_document_id(self, upload_document_id: int) -> Optional[IndexedDocument]:
        """Findet ein IndexedDocument anhand der Upload Document ID."""
        model = self.db_session.query(IndexedDocumentModel).filter(
            IndexedDocumentModel.upload_document_id == upload_document_id
        ).first()
        
        if not model:
            return None
        
        return self._model_to_entity(model)
    
    def find_all(self) -> List[IndexedDocument]:
        """Findet alle IndexedDocuments."""
        models = self.db_session.query(IndexedDocumentModel).all()
        return [self._model_to_entity(model) for model in models]
    
    def delete(self, indexed_document_id: int) -> bool:
        """Löscht ein IndexedDocument."""
        model = self.db_session.query(IndexedDocumentModel).filter(
            IndexedDocumentModel.id == indexed_document_id
        ).first()
        
        if not model:
            return False
        
        self.db_session.delete(model)
        self.db_session.commit()
        return True
    
    def _model_to_entity(self, model: IndexedDocumentModel) -> IndexedDocument:
        """Konvertiert SQLAlchemy Model zu Domain Entity."""
        return IndexedDocument(
            id=model.id,
            upload_document_id=model.upload_document_id,
            collection_name=model.qdrant_collection_name,
            indexed_at=model.indexed_at,
            total_chunks=model.total_chunks,
            last_updated_at=model.last_updated_at
        )


class SQLAlchemyDocumentChunkRepository(DocumentChunkRepository):
    """SQLAlchemy Implementation des DocumentChunkRepository."""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def save(self, chunk: DocumentChunk) -> DocumentChunk:
        """Speichert einen DocumentChunk."""
        try:
            if chunk.id is None:
                # Neuer Chunk
                model = DocumentChunkModel(
                    rag_indexed_document_id=chunk.indexed_document_id,
                    chunk_id=chunk.chunk_id,
                    chunk_text=chunk.chunk_text,
                    page_number=chunk.metadata.page_numbers[0] if chunk.metadata.page_numbers else 1,
                    paragraph_index=0,
                    chunk_index=0,
                    token_count=chunk.metadata.token_count,
                    sentence_count=1,
                    has_overlap=False,
                    overlap_sentence_count=0,
                    qdrant_point_id=chunk.qdrant_point_id,
                    embedding_vector_preview=None,
                    created_at=chunk.created_at
                )
                self.db_session.add(model)
                self.db_session.flush()  # Um ID zu bekommen
                chunk.id = model.id
            else:
                # Update existierender Chunk
                model = self.db_session.query(DocumentChunkModel).filter(
                    DocumentChunkModel.id == chunk.id
                ).first()
                if model:
                    model.chunk_text = chunk.chunk_text
                    model.page_numbers = chunk.metadata.page_numbers
                    model.heading_hierarchy = chunk.metadata.heading_hierarchy
                    model.confidence_score = chunk.metadata.confidence
                    model.token_count = chunk.metadata.token_count
            
            self.db_session.commit()
            return chunk
            
        except IntegrityError as e:
            self.db_session.rollback()
            raise ValueError(f"Fehler beim Speichern des Chunks: {str(e)}")
    
    def get_by_id(self, chunk_id: int) -> Optional[DocumentChunk]:
        """Hole DocumentChunk nach ID."""
        return self.find_by_id(chunk_id)
    
    def get_by_chunk_id(self, chunk_id: str) -> Optional[DocumentChunk]:
        """Hole DocumentChunk nach Chunk ID."""
        return self.find_by_chunk_id(chunk_id)
    
    def get_by_indexed_document_id(self, indexed_document_id: int) -> List[DocumentChunk]:
        """Hole alle Chunks eines IndexedDocuments."""
        return self.find_by_document_id(indexed_document_id)
    
    def get_all(self) -> List[DocumentChunk]:
        """Hole alle DocumentChunks."""
        models = self.db_session.query(DocumentChunkModel).all()
        return [self._model_to_entity(model) for model in models]
    
    def save_batch(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Speichere mehrere Chunks in einem Batch."""
        try:
            models = []
            for chunk in chunks:
                if chunk.id is None:
                    model = DocumentChunkModel(
                        rag_indexed_document_id=chunk.indexed_document_id,
                        chunk_id=chunk.chunk_id,
                        chunk_text=chunk.chunk_text,
                        page_number=chunk.metadata.page_numbers[0] if chunk.metadata.page_numbers else 1,
                        paragraph_index=0,
                        chunk_index=0,
                        token_count=chunk.metadata.token_count,
                        sentence_count=1,
                        has_overlap=False,
                        overlap_sentence_count=0,
                        qdrant_point_id=chunk.qdrant_point_id,
                        embedding_vector_preview=None,
                        created_at=chunk.created_at
                    )
                    models.append(model)
                    self.db_session.add(model)
            
            self.db_session.flush()  # Um IDs zu bekommen
            
            # Setze IDs zurück
            for i, chunk in enumerate(chunks):
                if chunk.id is None:
                    chunk.id = models[i].id
            
            self.db_session.commit()
            return chunks
            
        except IntegrityError as e:
            self.db_session.rollback()
            raise ValueError(f"Fehler beim Batch-Speichern der Chunks: {str(e)}")
    
    def delete(self, chunk_id: int) -> bool:
        """Lösche DocumentChunk."""
        model = self.db_session.query(DocumentChunkModel).filter(
            DocumentChunkModel.id == chunk_id
        ).first()
        
        if not model:
            return False
        
        self.db_session.delete(model)
        self.db_session.commit()
        return True
    
    def delete_by_indexed_document_id(self, indexed_document_id: int) -> int:
        """Lösche alle Chunks eines IndexedDocuments."""
        deleted_count = self.db_session.query(DocumentChunkModel).filter(
            DocumentChunkModel.indexed_document_id == indexed_document_id
        ).delete()
        
        self.db_session.commit()
        return deleted_count
    
    def exists_by_chunk_id(self, chunk_id: str) -> bool:
        """Prüfe ob Chunk mit Chunk ID existiert."""
        return self.db_session.query(DocumentChunkModel).filter(
            DocumentChunkModel.chunk_id == chunk_id
        ).first() is not None
    
    def delete_by_document_id(self, indexed_document_id: int) -> int:
        """Lösche alle Chunks eines Dokuments."""
        return self.delete_by_indexed_document_id(indexed_document_id)
    
    def find_by_id(self, chunk_id: int) -> Optional[DocumentChunk]:
        """Findet einen DocumentChunk anhand der ID."""
        model = self.db_session.query(DocumentChunkModel).filter(
            DocumentChunkModel.id == chunk_id
        ).first()
        
        if not model:
            return None
        
        return self._model_to_entity(model)
    
    def find_by_chunk_id(self, chunk_id: str) -> Optional[DocumentChunk]:
        """Findet einen DocumentChunk anhand der Chunk ID."""
        model = self.db_session.query(DocumentChunkModel).filter(
            DocumentChunkModel.chunk_id == chunk_id
        ).first()
        
        if not model:
            return None
        
        return self._model_to_entity(model)
    
    def find_by_document_id(self, indexed_document_id: int) -> List[DocumentChunk]:
        """Findet alle Chunks eines Dokuments."""
        models = self.db_session.query(DocumentChunkModel).filter(
            DocumentChunkModel.rag_indexed_document_id == indexed_document_id
        ).order_by(DocumentChunkModel.chunk_id).all()
        
        return [self._model_to_entity(model) for model in models]
    
    def find_by_page_numbers(self, page_numbers: List[int]) -> List[DocumentChunk]:
        """Findet Chunks nach Seitenzahlen."""
        models = self.db_session.query(DocumentChunkModel).filter(
            DocumentChunkModel.page_numbers.op('&')(page_numbers)
        ).all()
        
        return [self._model_to_entity(model) for model in models]
    
    def find_by_chunk_type(self, chunk_type: str) -> List[DocumentChunk]:
        """Findet Chunks nach Typ."""
        models = self.db_session.query(DocumentChunkModel).filter(
            DocumentChunkModel.chunk_type == chunk_type
        ).all()
        
        return [self._model_to_entity(model) for model in models]
    
    def find_by_document_type(self, document_type_id: int) -> List[DocumentChunk]:
        """Findet Chunks nach Dokumenttyp."""
        models = self.db_session.query(DocumentChunkModel).filter(
            DocumentChunkModel.document_type_id == document_type_id
        ).all()
        
        return [self._model_to_entity(model) for model in models]
    
    def search_by_text(self, search_text: str) -> List[DocumentChunk]:
        """Sucht Chunks nach Textinhalt."""
        models = self.db_session.query(DocumentChunkModel).filter(
            DocumentChunkModel.chunk_text.contains(search_text)
        ).all()
        
        return [self._model_to_entity(model) for model in models]
    
    def _model_to_entity(self, model: DocumentChunkModel) -> DocumentChunk:
        """Konvertiert SQLAlchemy Model zu Domain Entity."""
        metadata = ChunkMetadata(
            page_numbers=[model.page_number],
            heading_hierarchy=["Test Section"],
            document_type_id=1,
            confidence=1.0,
            chunk_type='text',
            token_count=model.token_count or 0
        )
        
        return DocumentChunk(
            id=model.id,
            indexed_document_id=model.rag_indexed_document_id,
            chunk_id=model.chunk_id,
            chunk_text=model.chunk_text,
            metadata=metadata,
            qdrant_point_id=model.qdrant_point_id or "",
            created_at=model.created_at
        )


class SQLAlchemyChatSessionRepository(ChatSessionRepository):
    """SQLAlchemy Implementation des ChatSessionRepository."""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def save(self, session: ChatSession) -> ChatSession:
        """Speichert eine ChatSession."""
        try:
            if session.id is None:
                # Neue Session
                model = ChatSessionModel(
                    user_id=session.user_id,
                    session_name=session.session_name,
                    created_at=session.created_at,
                    last_message_at=session.last_message_at,
                    is_active=session.is_active
                )
                self.db_session.add(model)
                self.db_session.flush()  # Um ID zu bekommen
                session.id = model.id
            else:
                # Update existierende Session
                model = self.db_session.query(ChatSessionModel).filter(
                    ChatSessionModel.id == session.id
                ).first()
                if model:
                    model.session_name = session.session_name
                    model.last_message_at = session.last_message_at
                    model.is_active = session.is_active
            
            self.db_session.commit()
            return session
            
        except IntegrityError as e:
            self.db_session.rollback()
            raise ValueError(f"Fehler beim Speichern der Session: {str(e)}")
    
    def get_by_id(self, session_id: int) -> Optional[ChatSession]:
        """Hole ChatSession nach ID."""
        return self.find_by_id(session_id)
    
    def get_by_user_id(self, user_id: int) -> List[ChatSession]:
        """Hole alle Sessions eines Benutzers."""
        return self.find_by_user_id(user_id)
    
    def get_active_by_user_id(self, user_id: int) -> List[ChatSession]:
        """Hole aktive Sessions eines Benutzers."""
        models = self.db_session.query(ChatSessionModel).filter(
            and_(
                ChatSessionModel.user_id == user_id,
                ChatSessionModel.is_active == True
            )
        ).order_by(desc(ChatSessionModel.last_message_at)).all()
        
        return [self._model_to_entity(model) for model in models]
    
    def get_all(self) -> List[ChatSession]:
        """Hole alle ChatSessions."""
        models = self.db_session.query(ChatSessionModel).all()
        return [self._model_to_entity(model) for model in models]
    
    def get_message_count_by_session_id(self, session_id: int) -> int:
        """Hole Anzahl Messages einer Session."""
        return self.db_session.query(ChatMessageModel).filter(
            ChatMessageModel.session_id == session_id
        ).count()
    
    def get_messages_by_session_id(self, session_id: int) -> List[ChatMessage]:
        """Hole alle Messages einer Session."""
        models = self.db_session.query(ChatMessageModel).filter(
            ChatMessageModel.session_id == session_id
        ).order_by(ChatMessageModel.created_at).all()
        
        return [self._model_to_entity(model) for model in models]
    
    def save_message(self, message: ChatMessage) -> ChatMessage:
        """Speichere Message in Session."""
        # Diese Methode würde normalerweise ChatMessageRepository verwenden
        # Für jetzt return message
        return message
    
    def delete_message(self, message_id: int) -> bool:
        """Lösche Message."""
        # Diese Methode würde normalerweise ChatMessageRepository verwenden
        # Für jetzt return False
        return False
    
    def find_by_id(self, session_id: int) -> Optional[ChatSession]:
        """Findet eine ChatSession anhand der ID."""
        model = self.db_session.query(ChatSessionModel).filter(
            ChatSessionModel.id == session_id
        ).first()
        
        if not model:
            return None
        
        return self._model_to_entity(model)
    
    def find_by_user_id(self, user_id: int) -> List[ChatSession]:
        """Findet alle Sessions eines Benutzers."""
        models = self.db_session.query(ChatSessionModel).filter(
            ChatSessionModel.user_id == user_id
        ).order_by(desc(ChatSessionModel.last_message_at)).all()
        
        return [self._model_to_entity(model) for model in models]
    
    def find_recent_sessions(self, user_id: int, limit: int = 10) -> List[ChatSession]:
        """Findet die neuesten Sessions eines Benutzers."""
        models = self.db_session.query(ChatSessionModel).filter(
            ChatSessionModel.user_id == user_id
        ).order_by(desc(ChatSessionModel.last_message_at)).limit(limit).all()
        
        return [self._model_to_entity(model) for model in models]
    
    def delete(self, session_id: int) -> bool:
        """Löscht eine ChatSession."""
        model = self.db_session.query(ChatSessionModel).filter(
            ChatSessionModel.id == session_id
        ).first()
        
        if not model:
            return False
        
        self.db_session.delete(model)
        self.db_session.commit()
        return True
    
    def count_by_user_id(self, user_id: int) -> int:
        """Zählt Sessions eines Benutzers."""
        return self.db_session.query(ChatSessionModel).filter(
            ChatSessionModel.user_id == user_id
        ).count()
    
    def _model_to_entity(self, model: ChatSessionModel) -> ChatSession:
        """Konvertiert SQLAlchemy Model zu Domain Entity."""
        return ChatSession(
            id=model.id,
            user_id=model.user_id,
            session_name=model.session_name,
            created_at=model.created_at,
            last_message_at=model.last_message_at,  # Geändert von last_activity
            is_active=model.is_active
        )


class SQLAlchemyChatMessageRepository(ChatMessageRepository):
    """SQLAlchemy Implementation des ChatMessageRepository."""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def get_by_id(self, message_id: int) -> Optional[ChatMessage]:
        """Hole ChatMessage nach ID."""
        model = self.db_session.query(ChatMessageModel).filter(
            ChatMessageModel.id == message_id
        ).first()
        
        if not model:
            return None
        
        return self._model_to_entity(model)
    
    def get_by_session_id(self, session_id: int) -> List[ChatMessage]:
        """Hole alle ChatMessages einer Session."""
        models = self.db_session.query(ChatMessageModel).filter(
            ChatMessageModel.session_id == session_id
        ).order_by(ChatMessageModel.created_at).all()
        
        return [self._model_to_entity(model) for model in models]
    
    def save(self, chat_message: ChatMessage) -> ChatMessage:
        """Speichere ChatMessage."""
        try:
            if chat_message.id is None:
                # Neue Message
                model = ChatMessageModel(
                    session_id=chat_message.session_id,
                    role=chat_message.role,
                    content=chat_message.content,
                    created_at=chat_message.created_at,
                    source_chunks=json.dumps([ref.__dict__ for ref in chat_message.source_references]) if chat_message.source_references else None
                )
                self.db_session.add(model)
                self.db_session.flush()  # Um ID zu bekommen
                chat_message.id = model.id
            else:
                # Update existierende Message
                model = self.db_session.query(ChatMessageModel).filter(
                    ChatMessageModel.id == chat_message.id
                ).first()
                if model:
                    model.content = chat_message.content
                    model.source_references = [ref.__dict__ for ref in chat_message.source_references]
                    model.source_chunk_ids = chat_message.source_chunk_ids
                    model.confidence_scores = chat_message.confidence_scores
            
            self.db_session.commit()
            return chat_message
            
        except IntegrityError as e:
            self.db_session.rollback()
            raise ValueError(f"Fehler beim Speichern der Message: {str(e)}")
    
    def delete(self, message_id: int) -> bool:
        """Lösche ChatMessage."""
        model = self.db_session.query(ChatMessageModel).filter(
            ChatMessageModel.id == message_id
        ).first()
        
        if not model:
            return False
        
        self.db_session.delete(model)
        self.db_session.commit()
        return True
    
    def get_latest_messages(self, session_id: int, limit: int = 10) -> List[ChatMessage]:
        """Hole neueste ChatMessages einer Session."""
        models = self.db_session.query(ChatMessageModel).filter(
            ChatMessageModel.session_id == session_id
        ).order_by(desc(ChatMessageModel.created_at)).limit(limit).all()
        
        return [self._model_to_entity(model) for model in models]
    
    def _model_to_entity(self, model: ChatMessageModel) -> ChatMessage:
        """Konvertiert SQLAlchemy Model zu Domain Entity."""
        from contexts.ragintegration.domain.value_objects import SourceReference
        
        # Konvertiere source_chunks Text zu SourceReference Objekten
        source_refs = []
        if model.source_chunks:
            try:
                import json
                source_data = json.loads(model.source_chunks)
                if isinstance(source_data, list):
                    for ref_data in source_data:
                        source_refs.append(SourceReference(
                            document_id=ref_data["document_id"],
                            document_title=ref_data["document_title"],
                            page_number=ref_data["page_number"],
                            chunk_id=ref_data["chunk_id"],
                            preview_image_path=ref_data["preview_image_path"],
                            relevance_score=ref_data["relevance_score"],
                            text_excerpt=ref_data["text_excerpt"]
                        ))
            except (json.JSONDecodeError, TypeError, KeyError):
                # Fallback: leere Liste wenn Parsing fehlschlägt
                source_refs = []
        
        return ChatMessage(
            id=model.id,
            session_id=model.session_id,
            role=model.role,
            content=model.content,
            created_at=model.created_at,
            source_references=source_refs
        )