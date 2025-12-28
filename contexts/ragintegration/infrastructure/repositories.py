"""
SQLAlchemy Repository Implementations für RAG Integration Context.

Implementiert die Repository Interfaces mit SQLAlchemy ORM.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, desc, update, Float
import json

from contexts.ragintegration.domain.entities import (
    IndexedDocument, DocumentChunk, ChatSession, ChatMessage, RAGFeedback, RAGChatPrompt, TrainingData
)
from contexts.ragintegration.domain.value_objects import ChunkMetadata
from contexts.ragintegration.domain.repositories import (
    IndexedDocumentRepository, DocumentChunkRepository, 
    ChatSessionRepository, ChatMessageRepository, RAGFeedbackRepository,
    ChunkFeedbackRepository,
    RAGChatPromptRepository, TrainingDataRepository, SearchQualityMetricsRepository
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
                    embedding_model=document.embedding_model  # NEU: Verwende embedding_model aus Entity
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
                    model.embedding_model = document.embedding_model  # NEU: Update embedding_model
            
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
    
    def count_by_document_type(
        self, 
        document_type_id: int,
        interest_group_ids: Optional[List[int]] = None
    ) -> int:
        """Zähle IndexedDocuments für einen DocumentType.
        
        JOIN: rag_indexed_documents → upload_documents → document_types
        
        Args:
            document_type_id: Document Type ID
            interest_group_ids: Optional - Filter nach Interest Groups (RBAC)
                              None/Leere Liste = alle Dokumente
                              Liste mit IDs = nur Dokumente in diesen IGs
        
        Returns:
            Anzahl indexierter Dokumente
        """
        from backend.app.models import UploadDocument, UploadDocumentInterestGroup
        
        query = self.db_session.query(IndexedDocumentModel).join(
            UploadDocument,
            IndexedDocumentModel.upload_document_id == UploadDocument.id
        ).filter(
            UploadDocument.document_type_id == document_type_id
        )
        
        # RBAC Multi-Level: Filter nach Interest Groups falls angegeben
        if interest_group_ids:
            query = query.join(
                UploadDocumentInterestGroup,
                UploadDocument.id == UploadDocumentInterestGroup.upload_document_id
            ).filter(
                UploadDocumentInterestGroup.interest_group_id.in_(interest_group_ids)
            ).distinct()  # WICHTIG: distinct() verhindert Duplikate bei mehreren IG-Zuordnungen
        
        count = query.count()
        return count
    
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
            last_updated_at=model.last_updated_at,
            embedding_model=model.embedding_model  # NEU: Embedding-Modell
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
                page_num = chunk.metadata.page_numbers[0] if chunk.metadata.page_numbers and len(chunk.metadata.page_numbers) > 0 else 1
                
                paragraph_idx = 0
                if hasattr(chunk.metadata, 'paragraph_index') and chunk.metadata.paragraph_index is not None:
                    try:
                        paragraph_idx = int(chunk.metadata.paragraph_index)
                    except (ValueError, TypeError):
                        paragraph_idx = 0
                
                # chunk_index ist 0 für einzelne Chunks (wird bei save_batch überschrieben)
                chunk_idx = 0
                
                token_cnt = chunk.metadata.token_count if chunk.metadata.token_count is not None else 0
                sentence_cnt = chunk.metadata.sentence_count if chunk.metadata.sentence_count is not None else 1
                has_ovlp = chunk.metadata.has_overlap if hasattr(chunk.metadata, 'has_overlap') and chunk.metadata.has_overlap is not None else False
                overlap_cnt = chunk.metadata.overlap_sentence_count if hasattr(chunk.metadata, 'overlap_sentence_count') and chunk.metadata.overlap_sentence_count is not None else 0
                
                # Erstelle Model - WICHTIG: embedding_vector_preview="" statt None (SQLite NOT NULL Constraint)
                model = DocumentChunkModel(
                    rag_indexed_document_id=chunk.indexed_document_id,
                    chunk_id=chunk.chunk_id,
                    chunk_text=chunk.chunk_text,
                    page_number=page_num,
                    paragraph_index=paragraph_idx if paragraph_idx is not None else None,
                    chunk_index=chunk_idx,
                    token_count=token_cnt if token_cnt is not None else None,
                    sentence_count=sentence_cnt if sentence_cnt is not None else None,
                    has_overlap=has_ovlp,
                    overlap_sentence_count=overlap_cnt,
                    qdrant_point_id=chunk.qdrant_point_id,
                    embedding_vector_preview="",  # Leerer String statt None (SQLite erfordert das)
                    created_at=chunk.created_at or datetime.utcnow()
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
                    # WICHTIG: Aktualisiere auch Overlap-Felder
                    if hasattr(chunk.metadata, 'has_overlap'):
                        model.has_overlap = chunk.metadata.has_overlap if chunk.metadata.has_overlap is not None else False
                    if hasattr(chunk.metadata, 'overlap_sentence_count'):
                        model.overlap_sentence_count = chunk.metadata.overlap_sentence_count if chunk.metadata.overlap_sentence_count is not None else 0
                    # WICHTIG: page_numbers und heading_hierarchy sind JSON-Felder im Model
                    # Sie werden in _model_to_entity konvertiert
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
            for i, chunk in enumerate(chunks):
                if chunk.id is None:
                    # Extrahiere page_number sicher
                    page_num = chunk.metadata.page_numbers[0] if chunk.metadata.page_numbers and len(chunk.metadata.page_numbers) > 0 else 1
                    
                    # Stelle sicher dass alle Werte die richtigen Typen haben
                    paragraph_idx = 0
                    if hasattr(chunk.metadata, 'paragraph_index') and chunk.metadata.paragraph_index is not None:
                        try:
                            paragraph_idx = int(chunk.metadata.paragraph_index)
                        except (ValueError, TypeError):
                            paragraph_idx = 0
                    
                    # chunk_index ist der sequenzielle Index in der Liste (Integer!)
                    chunk_idx = int(i)
                    
                    token_cnt = chunk.metadata.token_count if chunk.metadata.token_count is not None else 0
                    sentence_cnt = chunk.metadata.sentence_count if chunk.metadata.sentence_count is not None else 1
                    has_ovlp = chunk.metadata.has_overlap if hasattr(chunk.metadata, 'has_overlap') and chunk.metadata.has_overlap is not None else False
                    overlap_cnt = chunk.metadata.overlap_sentence_count if hasattr(chunk.metadata, 'overlap_sentence_count') and chunk.metadata.overlap_sentence_count is not None else 0
                    
                    # Erstelle Model - WICHTIG: embedding_vector_preview="" statt None (SQLite NOT NULL Constraint)
                    model = DocumentChunkModel(
                        rag_indexed_document_id=chunk.indexed_document_id,
                        chunk_id=chunk.chunk_id,
                        chunk_text=chunk.chunk_text,
                        page_number=page_num,
                        paragraph_index=paragraph_idx if paragraph_idx is not None else None,
                        chunk_index=chunk_idx,
                        token_count=token_cnt if token_cnt is not None else None,
                        sentence_count=sentence_cnt if sentence_cnt is not None else None,
                        has_overlap=has_ovlp,
                        overlap_sentence_count=overlap_cnt,
                        qdrant_point_id=chunk.qdrant_point_id,
                        embedding_vector_preview="",  # Leerer String statt None (SQLite erfordert das)
                        created_at=chunk.created_at or datetime.utcnow()
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
            DocumentChunkModel.rag_indexed_document_id == indexed_document_id
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
        """Findet alle Chunks eines Dokuments, sortiert nach Seitenzahl."""
        models = self.db_session.query(DocumentChunkModel).filter(
            DocumentChunkModel.rag_indexed_document_id == indexed_document_id
        ).order_by(DocumentChunkModel.page_number.asc(), DocumentChunkModel.chunk_id.asc()).all()
        
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
        # WICHTIG: Model hat nur page_number (singular), aber ChunkMetadata erwartet page_numbers (plural)
        # WICHTIG: heading_hierarchy und chunk_type sind nicht im Model gespeichert
        # Verwende Standardwerte für fehlende Metadaten
        # WICHTIG: SQLite speichert Boolean als Integer (1/0), daher explizite Konvertierung
        has_overlap_value = False
        if hasattr(model, 'has_overlap'):
            if model.has_overlap is not None:
                has_overlap_value = bool(model.has_overlap)
        
        overlap_count_value = 0
        if hasattr(model, 'overlap_sentence_count'):
            if model.overlap_sentence_count is not None:
                overlap_count_value = int(model.overlap_sentence_count)
        
        metadata = ChunkMetadata(
            page_numbers=[model.page_number] if model.page_number else [1],
            heading_hierarchy=[],  # Nicht im Model gespeichert
            chunk_type='text',  # Nicht im Model gespeichert, Standardwert
            token_count=model.token_count,
            sentence_count=model.sentence_count,
            has_overlap=has_overlap_value,
            overlap_sentence_count=overlap_count_value
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
        """Löscht eine ChatSession.
        
        WICHTIG: Löscht zuerst alle Messages der Session um Foreign Key Constraints zu vermeiden.
        """
        # Prüfe ob Session existiert
        model = self.db_session.query(ChatSessionModel).filter(
            ChatSessionModel.id == session_id
        ).first()
        
        if not model:
            return False
        
        try:
            # 1. Lösche zuerst alle Messages der Session (Foreign Key Constraint!)
            # Verwende direkten SQL-Delete für Performance
            deleted_messages = self.db_session.query(ChatMessageModel).filter(
                ChatMessageModel.session_id == session_id
            ).delete(synchronize_session=False)
            
            # 2. Dann lösche die Session selbst
            self.db_session.delete(model)
            self.db_session.commit()
            
            return True
            
        except Exception as e:
            self.db_session.rollback()
            raise ValueError(f"Fehler beim Löschen der Session {session_id}: {str(e)}")
    
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
                # WICHTIG: Verwende asdict() für dataclass SourceReference, nicht __dict__
                from dataclasses import asdict
                source_chunks_data = None
                if chat_message.source_references:
                    source_chunks_list = []
                    for ref in chat_message.source_references:
                        # Konvertiere dataclass zu dict
                        ref_dict = asdict(ref)
                        # Füge _extended_metadata hinzu falls vorhanden
                        if hasattr(ref, '_extended_metadata') and ref._extended_metadata:
                            ref_dict['_extended_metadata'] = ref._extended_metadata
                        source_chunks_list.append(ref_dict)
                    source_chunks_data = json.dumps(source_chunks_list)
                
                model = ChatMessageModel(
                    session_id=chat_message.session_id,
                    role=chat_message.role,
                    content=chat_message.content,
                    created_at=chat_message.created_at,
                    source_chunks=source_chunks_data,
                    ai_model_used=chat_message.ai_model_used if chat_message.role == "assistant" else None,
                    message_metadata=json.dumps(chat_message.metadata) if chat_message.metadata else None
                )
                self.db_session.add(model)
                self.db_session.flush()  # Um ID zu bekommen
                chat_message.id = model.id
                
                # Aktualisiere Session last_message_at
                # WICHTIG: Verwende direkten SQL-Update, nicht SQLAlchemy Relationship
                # um automatische Updates zu vermeiden, die last_activity Fehler verursachen
                self.db_session.execute(
                    update(ChatSessionModel)
                    .where(ChatSessionModel.id == chat_message.session_id)
                    .values(last_message_at=datetime.utcnow())
                )
            else:
                # Update existierender Message (z.B. für Metadaten-Updates)
                model = self.db_session.query(ChatMessageModel).filter(
                    ChatMessageModel.id == chat_message.id
                ).first()
                if model:
                    # Aktualisiere nur Metadaten (andere Felder sollten nicht geändert werden)
                    if chat_message.metadata:
                        model.message_metadata = json.dumps(chat_message.metadata)
                    # Optional: Auch source_chunks und ai_model_used aktualisieren falls nötig
                    if chat_message.source_references:
                        from dataclasses import asdict
                        source_chunks_list = []
                        for ref in chat_message.source_references:
                            ref_dict = asdict(ref)
                            if hasattr(ref, '_extended_metadata') and ref._extended_metadata:
                                ref_dict['_extended_metadata'] = ref._extended_metadata
                            source_chunks_list.append(ref_dict)
                        model.source_chunks = json.dumps(source_chunks_list)
                    if chat_message.role == "assistant" and chat_message.ai_model_used:
                        model.ai_model_used = chat_message.ai_model_used
                
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

    async def get_all(self) -> List[ChatMessage]:
        """Hole alle ChatMessages (für Analytics)."""
        models = self.db_session.query(ChatMessageModel).order_by(ChatMessageModel.created_at).all()
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
                        # Erstelle SourceReference (ohne _extended_metadata)
                        source_ref = SourceReference(
                            document_id=ref_data["document_id"],
                            document_title=ref_data["document_title"],
                            page_number=ref_data["page_number"],
                            chunk_id=ref_data["chunk_id"],
                            preview_image_path=ref_data.get("preview_image_path"),
                            relevance_score=ref_data["relevance_score"],
                            text_excerpt=ref_data.get("text_excerpt")
                        )
                        # Stelle _extended_metadata wieder her falls vorhanden
                        if "_extended_metadata" in ref_data:
                            source_ref._extended_metadata = ref_data["_extended_metadata"]
                        source_refs.append(source_ref)
            except (json.JSONDecodeError, TypeError, KeyError):
                # Fallback: leere Liste wenn Parsing fehlschlägt
                source_refs = []
        
        # Konvertiere message_metadata JSON zu Dict
        metadata = {}
        if model.message_metadata:
            try:
                import json
                metadata = json.loads(model.message_metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        
        return ChatMessage(
            id=model.id,
            session_id=model.session_id,
            role=model.role,
            content=model.content,
            created_at=model.created_at,
            source_references=source_refs,
            ai_model_used=model.ai_model_used,
            metadata=metadata
        )


# ============================================================================
# RAG AUDIT LOG REPOSITORY (PHASE 1.3)
# ============================================================================

class SQLAlchemyRAGAuditLogRepository:
    """
    SQLAlchemy Implementation des RAGAuditLogRepository.
    
    Persists Audit Logs in relationaler DB für Compliance und Transparenz.
    """
    
    def __init__(self, db: Session):
        """Init mit DB Session."""
        self.db = db
    
    async def save(self, audit_log):
        """Speichere RAGAuditLog."""
        from backend.app.models import RAGAuditLogModel
        from contexts.ragintegration.domain.entities import RAGAuditLog
        import json
        
        model = RAGAuditLogModel(
            indexed_document_id=audit_log.indexed_document_id,
            action=audit_log.action,
            user_id=audit_log.user_id,
            timestamp=audit_log.timestamp,
            details=json.dumps(audit_log.details),
            status=audit_log.status,
            error_message=audit_log.error_message,
            duration_ms=audit_log.duration_ms,
            tokens_used=audit_log.tokens_used,
            cost_usd=int(audit_log.cost_usd * 100) if audit_log.cost_usd else None  # USD → Cents
        )
        
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        
        # Convert back to Entity
        return RAGAuditLog(
            id=model.id,
            indexed_document_id=model.indexed_document_id,
            action=model.action,
            user_id=model.user_id,
            timestamp=model.timestamp,
            details=json.loads(model.details),
            status=model.status,
            error_message=model.error_message,
            duration_ms=model.duration_ms,
            tokens_used=model.tokens_used,
            cost_usd=model.cost_usd / 100.0 if model.cost_usd else None
        )
    
    async def get_by_document_id(self, indexed_document_id: int, limit: int = 100):
        """Hole Logs für Dokument."""
        from backend.app.models import RAGAuditLogModel
        from contexts.ragintegration.domain.entities import RAGAuditLog
        import json
        
        models = self.db.query(RAGAuditLogModel)\
            .filter(RAGAuditLogModel.indexed_document_id == indexed_document_id)\
            .order_by(RAGAuditLogModel.timestamp.desc())\
            .limit(limit)\
            .all()
        
        return [RAGAuditLog(
            id=m.id,
            indexed_document_id=m.indexed_document_id,
            action=m.action,
            user_id=m.user_id,
            timestamp=m.timestamp,
            details=json.loads(m.details),
            status=m.status,
            error_message=m.error_message,
            duration_ms=m.duration_ms,
            tokens_used=m.tokens_used,
            cost_usd=m.cost_usd / 100.0 if m.cost_usd else None
        ) for m in models]
    
    async def get_by_user_id(self, user_id: int, limit: int = 100):
        """Hole Logs für User."""
        from backend.app.models import RAGAuditLogModel
        from contexts.ragintegration.domain.entities import RAGAuditLog
        import json
        
        models = self.db.query(RAGAuditLogModel)\
            .filter(RAGAuditLogModel.user_id == user_id)\
            .order_by(RAGAuditLogModel.timestamp.desc())\
            .limit(limit)\
            .all()
        
        return [RAGAuditLog(
            id=m.id,
            indexed_document_id=m.indexed_document_id,
            action=m.action,
            user_id=m.user_id,
            timestamp=m.timestamp,
            details=json.loads(m.details),
            status=m.status,
            error_message=m.error_message,
            duration_ms=m.duration_ms,
            tokens_used=m.tokens_used,
            cost_usd=m.cost_usd / 100.0 if m.cost_usd else None
        ) for m in models]


# ============================================================================
# RAG FEEDBACK REPOSITORY (PHASE 4.1)
# ============================================================================

class SQLAlchemyRAGFeedbackRepository(RAGFeedbackRepository):
    """
    SQLAlchemy Implementation des RAGFeedbackRepository.

    Persists User Feedback in relationaler DB für Qualitätsverbesserung und ML-Training.
    """

    def __init__(self, db: Session):
        """Init mit DB Session."""
        self.db = db

    async def save(self, feedback: RAGFeedback) -> RAGFeedback:
        """Speichere RAGFeedback."""
        from backend.app.models import RAGFeedbackModel

        model = RAGFeedbackModel(
            chat_message_id=feedback.chat_message_id,
            user_id=feedback.user_id,
            rating=feedback.rating,
            comment=feedback.comment,
            submitted_at=feedback.submitted_at
        )

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        # Convert back to Entity
        return RAGFeedback(
            id=model.id,
            chat_message_id=model.chat_message_id,
            user_id=model.user_id,
            rating=model.rating,
            comment=model.comment,
            submitted_at=model.submitted_at
        )

    async def get_by_id(self, feedback_id: int) -> Optional[RAGFeedback]:
        """Hole Feedback nach ID."""
        from backend.app.models import RAGFeedbackModel

        model = self.db.query(RAGFeedbackModel).filter(
            RAGFeedbackModel.id == feedback_id
        ).first()

        if not model:
            return None

        return RAGFeedback(
            id=model.id,
            chat_message_id=model.chat_message_id,
            user_id=model.user_id,
            rating=model.rating,
            comment=model.comment,
            submitted_at=model.submitted_at
        )

    async def get_by_message_id(
        self,
        chat_message_id: int,
        user_id: Optional[int] = None
    ) -> Optional[RAGFeedback]:
        """Hole Feedback für Chat-Message."""
        from backend.app.models import RAGFeedbackModel

        query = self.db.query(RAGFeedbackModel).filter(
            RAGFeedbackModel.chat_message_id == chat_message_id
        )

        if user_id:
            query = query.filter(RAGFeedbackModel.user_id == user_id)

        model = query.first()

        if not model:
            return None

        return RAGFeedback(
            id=model.id,
            chat_message_id=model.chat_message_id,
            user_id=model.user_id,
            rating=model.rating,
            comment=model.comment,
            submitted_at=model.submitted_at
        )

    async def get_by_user_id(self, user_id: int, limit: int = 100) -> List[RAGFeedback]:
        """Hole alle Feedbacks eines Users."""
        from backend.app.models import RAGFeedbackModel

        models = self.db.query(RAGFeedbackModel)\
            .filter(RAGFeedbackModel.user_id == user_id)\
            .order_by(desc(RAGFeedbackModel.submitted_at))\
            .limit(limit)\
            .all()

        return [RAGFeedback(
            id=m.id,
            chat_message_id=m.chat_message_id,
            user_id=m.user_id,
            rating=m.rating,
            comment=m.comment,
            submitted_at=m.submitted_at
        ) for m in models]

    async def get_statistics(
        self,
        chat_message_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Hole Feedback-Statistiken."""
        from backend.app.models import RAGFeedbackModel

        query = self.db.query(RAGFeedbackModel)

        if chat_message_id:
            query = query.filter(RAGFeedbackModel.chat_message_id == chat_message_id)
        if user_id:
            query = query.filter(RAGFeedbackModel.user_id == user_id)

        # Zähle nach Rating
        total = query.count()
        positive = query.filter(RAGFeedbackModel.rating == "positive").count()
        negative = query.filter(RAGFeedbackModel.rating == "negative").count()
        neutral = query.filter(RAGFeedbackModel.rating == "neutral").count()

        # Berechne Average Rating (1.0 = positive, 0.0 = negative, 0.5 = neutral)
        if total > 0:
            average_rating = (positive * 1.0 + neutral * 0.5 + negative * 0.0) / total
        else:
            average_rating = 0.0

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "average_rating": round(average_rating, 2)
        }


# ============================================================================
# CHUNK FEEDBACK REPOSITORY (v2.9.0: Chunk-Level Feedback)
# ============================================================================

class SQLAlchemyChunkFeedbackRepository(ChunkFeedbackRepository):
    """
    SQLAlchemy Implementation des ChunkFeedbackRepository.
    
    Persists Chunk-Level Feedback in relationaler DB für präzise Qualitätsverbesserung.
    """
    
    def __init__(self, db: Session):
        """Init mit DB Session."""
        self.db = db
    
    async def save(self, feedback: 'ChunkFeedback') -> 'ChunkFeedback':
        """Speichere ChunkFeedback."""
        from backend.app.models import ChunkFeedbackModel
        from contexts.ragintegration.domain.entities import ChunkFeedback
        
        model = ChunkFeedbackModel(
            chunk_id=feedback.chunk_id,
            chat_message_id=feedback.chat_message_id,
            document_id=feedback.document_id,
            user_id=feedback.user_id,
            rating=feedback.rating,
            comment=feedback.comment,
            submitted_at=feedback.submitted_at
        )
        
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        
        # Convert back to Entity
        return ChunkFeedback(
            id=model.id,
            chunk_id=model.chunk_id,
            chat_message_id=model.chat_message_id,
            document_id=model.document_id,
            user_id=model.user_id,
            rating=model.rating,
            comment=model.comment,
            submitted_at=model.submitted_at
        )
    
    async def get_by_id(self, feedback_id: int) -> Optional['ChunkFeedback']:
        """Hole ChunkFeedback nach ID."""
        from backend.app.models import ChunkFeedbackModel
        from contexts.ragintegration.domain.entities import ChunkFeedback
        
        model = self.db.query(ChunkFeedbackModel).filter(
            ChunkFeedbackModel.id == feedback_id
        ).first()
        
        if not model:
            return None
        
        return ChunkFeedback(
            id=model.id,
            chunk_id=model.chunk_id,
            chat_message_id=model.chat_message_id,
            document_id=model.document_id,
            user_id=model.user_id,
            rating=model.rating,
            comment=model.comment,
            submitted_at=model.submitted_at
        )
    
    async def get_by_chunk_id(
        self,
        chunk_id: str,
        chat_message_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> List['ChunkFeedback']:
        """Hole Feedbacks für einen Chunk."""
        from backend.app.models import ChunkFeedbackModel
        from contexts.ragintegration.domain.entities import ChunkFeedback
        from sqlalchemy import desc
        
        query = self.db.query(ChunkFeedbackModel).filter(
            ChunkFeedbackModel.chunk_id == chunk_id
        )
        
        if chat_message_id:
            query = query.filter(ChunkFeedbackModel.chat_message_id == chat_message_id)
        
        if user_id:
            query = query.filter(ChunkFeedbackModel.user_id == user_id)
        
        models = query.order_by(desc(ChunkFeedbackModel.submitted_at)).all()
        
        return [ChunkFeedback(
            id=m.id,
            chunk_id=m.chunk_id,
            chat_message_id=m.chat_message_id,
            document_id=m.document_id,
            user_id=m.user_id,
            rating=m.rating,
            comment=m.comment,
            submitted_at=m.submitted_at
        ) for m in models]
    
    async def get_by_message_id(
        self,
        chat_message_id: int,
        user_id: Optional[int] = None
    ) -> List['ChunkFeedback']:
        """Hole alle Feedbacks für Chunks einer Chat-Message."""
        from backend.app.models import ChunkFeedbackModel
        from contexts.ragintegration.domain.entities import ChunkFeedback
        from sqlalchemy import desc
        
        query = self.db.query(ChunkFeedbackModel).filter(
            ChunkFeedbackModel.chat_message_id == chat_message_id
        )
        
        if user_id:
            query = query.filter(ChunkFeedbackModel.user_id == user_id)
        
        models = query.order_by(desc(ChunkFeedbackModel.submitted_at)).all()
        
        return [ChunkFeedback(
            id=m.id,
            chunk_id=m.chunk_id,
            chat_message_id=m.chat_message_id,
            document_id=m.document_id,
            user_id=m.user_id,
            rating=m.rating,
            comment=m.comment,
            submitted_at=m.submitted_at
        ) for m in models]
    
    async def get_by_user_id(self, user_id: int, limit: int = 100) -> List['ChunkFeedback']:
        """Hole alle Feedbacks eines Users."""
        from backend.app.models import ChunkFeedbackModel
        from contexts.ragintegration.domain.entities import ChunkFeedback
        from sqlalchemy import desc
        
        models = self.db.query(ChunkFeedbackModel)\
            .filter(ChunkFeedbackModel.user_id == user_id)\
            .order_by(desc(ChunkFeedbackModel.submitted_at))\
            .limit(limit)\
            .all()
        
        return [ChunkFeedback(
            id=m.id,
            chunk_id=m.chunk_id,
            chat_message_id=m.chat_message_id,
            document_id=m.document_id,
            user_id=m.user_id,
            rating=m.rating,
            comment=m.comment,
            submitted_at=m.submitted_at
        ) for m in models]
    
    async def get_statistics(
        self,
        chunk_id: Optional[str] = None,
        chat_message_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Hole Feedback-Statistiken."""
        from backend.app.models import ChunkFeedbackModel
        from sqlalchemy import func
        
        query = self.db.query(ChunkFeedbackModel)
        
        if chunk_id:
            query = query.filter(ChunkFeedbackModel.chunk_id == chunk_id)
        
        if chat_message_id:
            query = query.filter(ChunkFeedbackModel.chat_message_id == chat_message_id)
        
        if user_id:
            query = query.filter(ChunkFeedbackModel.user_id == user_id)
        
        total = query.count()
        
        if total == 0:
            return {
                'total': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'average_rating': 0.0
            }
        
        positive = query.filter(ChunkFeedbackModel.rating == 'positive').count()
        negative = query.filter(ChunkFeedbackModel.rating == 'negative').count()
        neutral = query.filter(ChunkFeedbackModel.rating == 'neutral').count()
        
        # Berechne durchschnittlichen Rating (positive=1.0, neutral=0.5, negative=0.0)
        average_rating = (positive * 1.0 + neutral * 0.5 + negative * 0.0) / total
        
        return {
            'total': total,
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'average_rating': average_rating
        }


# ============================================================================
# RAG CHAT PROMPT REPOSITORY (PHASE 1)
# ============================================================================

class SQLAlchemyRAGChatPromptRepository(RAGChatPromptRepository):
    """
    SQLAlchemy Implementation des RAGChatPromptRepository.
    
    Persists globale RAG Chat Prompts in relationaler DB.
    """
    
    def __init__(self, db_session: Session):
        """Init mit DB Session."""
        self.db_session = db_session
    
    def get_by_document_type_id(self, document_type_id: Optional[int]) -> Optional[RAGChatPrompt]:
        """Hole RAG Chat Prompt für einen Dokumenttyp (None = Default-Prompt)."""
        from backend.app.models import RAGChatPromptModel
        
        # Wenn document_type_id None ist, suche nach NULL in der DB
        if document_type_id is None:
            model = self.db_session.query(RAGChatPromptModel).filter(
                RAGChatPromptModel.document_type_id.is_(None)
            ).first()
        else:
            model = self.db_session.query(RAGChatPromptModel).filter(
                RAGChatPromptModel.document_type_id == document_type_id
            ).first()
        
        if not model:
            return None
        
        return self._model_to_entity(model)
    
    def save(self, prompt: RAGChatPrompt) -> RAGChatPrompt:
        """Speichere RAG Chat Prompt (Create oder Update)."""
        from backend.app.models import RAGChatPromptModel
        
        try:
            if prompt.id is None:
                # Neues Prompt
                model = RAGChatPromptModel(
                    document_type_id=prompt.document_type_id,
                    prompt_text=prompt.prompt_text,
                    multi_query_prompt_text=prompt.multi_query_prompt_text,
                    created_by_user_id=prompt.created_by_user_id,
                    created_at=prompt.created_at,
                    updated_at=prompt.updated_at
                )
                self.db_session.add(model)
                self.db_session.flush()  # Um ID zu bekommen
                prompt.id = model.id
            else:
                # Update existierendes Prompt
                model = self.db_session.query(RAGChatPromptModel).filter(
                    RAGChatPromptModel.id == prompt.id
                ).first()
                if model:
                    model.prompt_text = prompt.prompt_text
                    model.multi_query_prompt_text = prompt.multi_query_prompt_text
                    model.updated_at = prompt.updated_at
            
            self.db_session.commit()
            return prompt
            
        except IntegrityError as e:
            self.db_session.rollback()
            raise ValueError(f"Fehler beim Speichern des Prompts: {str(e)}")
    
    def delete(self, document_type_id: int) -> bool:
        """Lösche RAG Chat Prompt (zurücksetzen auf Standard)."""
        from backend.app.models import RAGChatPromptModel
        
        model = self.db_session.query(RAGChatPromptModel).filter(
            RAGChatPromptModel.document_type_id == document_type_id
        ).first()
        
        if not model:
            return False
        
        self.db_session.delete(model)
        self.db_session.commit()
        return True
    
    def get_all(self) -> List[RAGChatPrompt]:
        """Hole alle RAG Chat Prompts."""
        from backend.app.models import RAGChatPromptModel
        
        models = self.db_session.query(RAGChatPromptModel).all()
        return [self._model_to_entity(model) for model in models]
    
    def _model_to_entity(self, model) -> RAGChatPrompt:
        """Konvertiert SQLAlchemy Model zu Domain Entity."""
        return RAGChatPrompt(
            id=model.id,
            document_type_id=model.document_type_id,
            prompt_text=model.prompt_text,
            created_by_user_id=model.created_by_user_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            multi_query_prompt_text=model.multi_query_prompt_text  # PHASE 2: Multi-Query Prompt (muss am Ende sein)
        )
# ============================================================================
# TRAINING DATA REPOSITORY (PHASE 2: SHAP Training Data Collection)
# ============================================================================

class SQLAlchemyTrainingDataRepository(TrainingDataRepository):
    """
    SQLAlchemy Implementation des TrainingDataRepository.
    
    Persists Training Data in relationaler DB für ML-Model Training.
    """
    
    def __init__(self, db: Session):
        """Init mit DB Session."""
        self.db = db
    
    def save(self, training_data: TrainingData) -> TrainingData:
        """Speichere Training Data."""
        from backend.app.models import TrainingDataModel
        import json
        
        model = TrainingDataModel(
            query=training_data.query,
            chunk_id=training_data.chunk_id,
            document_id=training_data.document_id,
            session_id=training_data.session_id,
            user_id=training_data.user_id,
            vector_score=str(training_data.vector_score),
            text_score=str(training_data.text_score),
            hybrid_score=str(training_data.hybrid_score),
            document_type=training_data.document_type,
            user_level=training_data.user_level,
            keyword_matches=training_data.keyword_matches,
            chunk_length=training_data.chunk_length,
            heading_hierarchy_depth=training_data.heading_hierarchy_depth,
            confidence_score=str(training_data.confidence_score),
            shap_explanation=json.dumps(training_data.shap_explanation) if training_data.shap_explanation else None,
            user_feedback=training_data.user_feedback,
            feedback_comment=training_data.feedback_comment,
            created_at=training_data.created_at
        )
        
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        
        # Convert back to Entity
        return self._model_to_entity(model)
    
    def get_training_data(
        self,
        with_feedback: Optional[bool] = None,
        with_shap: Optional[bool] = None,
        query_text: Optional[str] = None,
        chunk_id: Optional[str] = None,
        user_id: Optional[int] = None,
        document_type: Optional[str] = None,
        limit: int = 100
    ) -> List[TrainingData]:
        """Hole Training Data mit Filtern."""
        from backend.app.models import TrainingDataModel
        from sqlalchemy import desc
        from sqlalchemy import func
        
        query = self.db.query(TrainingDataModel)
        
        if with_feedback is True:
            query = query.filter(TrainingDataModel.user_feedback.isnot(None))
        elif with_feedback is False:
            query = query.filter(TrainingDataModel.user_feedback.is_(None))
        
        if with_shap is True:
            query = query.filter(TrainingDataModel.shap_explanation.isnot(None))
        elif with_shap is False:
            query = query.filter(TrainingDataModel.shap_explanation.is_(None))

        # Optional: Filter nach Query (case-insensitive, trim)
        if query_text:
            normalized = query_text.strip().lower()
            query = query.filter(func.lower(func.trim(TrainingDataModel.query)) == normalized)

        # Optional: Filter nach Chunk ID
        if chunk_id:
            query = query.filter(TrainingDataModel.chunk_id == chunk_id)
        
        if user_id:
            query = query.filter(TrainingDataModel.user_id == user_id)
        
        if document_type:
            query = query.filter(TrainingDataModel.document_type == document_type)
        
        models = query.order_by(desc(TrainingDataModel.created_at)).limit(limit).all()
        
        return [self._model_to_entity(m) for m in models]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Hole Training Data Statistiken."""
        from backend.app.models import TrainingDataModel
        from sqlalchemy import func
        
        total_count = self.db.query(func.count(TrainingDataModel.id)).scalar() or 0
        with_feedback_count = self.db.query(func.count(TrainingDataModel.id)).filter(
            TrainingDataModel.user_feedback.isnot(None)
        ).scalar() or 0
        with_shap_count = self.db.query(func.count(TrainingDataModel.id)).filter(
            TrainingDataModel.shap_explanation.isnot(None)
        ).scalar() or 0
        
        avg_score = self.db.query(func.avg(func.cast(TrainingDataModel.hybrid_score, Float))).scalar()
        average_hybrid_score = float(avg_score) if avg_score else 0.0
        
        return {
            'total_count': total_count,
            'with_feedback_count': with_feedback_count,
            'with_shap_count': with_shap_count,
            'average_hybrid_score': average_hybrid_score
        }
    
    def update_feedback(
        self,
        training_data_id: int,
        feedback: str,
        comment: Optional[str] = None
    ) -> Optional[TrainingData]:
        """Aktualisiere Feedback für Training Data."""
        from backend.app.models import TrainingDataModel
        
        model = self.db.query(TrainingDataModel).filter(
            TrainingDataModel.id == training_data_id
        ).first()
        
        if not model:
            return None
        
        model.user_feedback = feedback
        model.feedback_comment = comment
        self.db.commit()
        self.db.refresh(model)
        
        return self._model_to_entity(model)
    
    def _model_to_entity(self, model: 'TrainingDataModel') -> TrainingData:
        """Konvertiere Model zu Entity."""
        import json
        
        return TrainingData(
            id=model.id,
            query=model.query,
            chunk_id=model.chunk_id,
            document_id=model.document_id,
            session_id=model.session_id,
            user_id=model.user_id,
            vector_score=float(model.vector_score),
            text_score=float(model.text_score),
            hybrid_score=float(model.hybrid_score),
            document_type=model.document_type,
            user_level=model.user_level,
            keyword_matches=model.keyword_matches,
            chunk_length=model.chunk_length,
            heading_hierarchy_depth=model.heading_hierarchy_depth,
            confidence_score=float(model.confidence_score),
            shap_explanation=json.loads(model.shap_explanation) if model.shap_explanation else None,
            user_feedback=model.user_feedback,
            feedback_comment=model.feedback_comment,
            created_at=model.created_at
        )


# ============================================================================
# SEARCH QUALITY METRICS REPOSITORY (v2.9.0)
# ============================================================================

class SQLAlchemySearchQualityMetricsRepository(SearchQualityMetricsRepository):
    """
    SQLAlchemy Implementation des SearchQualityMetricsRepository.
    
    Speichert Search Quality Metrics in SQLite (search_quality_metrics Tabelle).
    """
    
    def __init__(self, db_session: Session):
        """
        Initialisiere Repository.
        
        Args:
            db_session: SQLAlchemy Session
        """
        self.db = db_session
    
    def save(self, metrics) -> 'SearchQualityMetrics':
        """
        Speichere Search Quality Metrics.
        
        Args:
            metrics: SearchQualityMetrics Dataclass
            
        Returns:
            Gespeicherte Metrics (mit ID)
        """
        try:
            from backend.app.models import SearchQualityMetricsModel
            from contexts.ragintegration.infrastructure.search_quality_metrics import SearchQualityMetrics
            
            # Erstelle Model
            model = SearchQualityMetricsModel(
                query=metrics.query,
                session_id=metrics.session_id,
                user_id=metrics.user_id,
                document_type=metrics.document_type,
                
                # Precision & Recall
                precision_at_1=metrics.precision_at_1,
                precision_at_3=metrics.precision_at_3,
                precision_at_5=metrics.precision_at_5,
                precision_at_10=metrics.precision_at_10,
                
                recall_at_1=metrics.recall_at_1,
                recall_at_3=metrics.recall_at_3,
                recall_at_5=metrics.recall_at_5,
                recall_at_10=metrics.recall_at_10,
                
                # Ranking Metriken
                ndcg_at_1=metrics.ndcg_at_1,
                ndcg_at_3=metrics.ndcg_at_3,
                ndcg_at_5=metrics.ndcg_at_5,
                ndcg_at_10=metrics.ndcg_at_10,
                
                mrr=metrics.mrr,
                
                # Zusätzliche Metriken
                average_relevance_score=metrics.average_relevance_score,
                num_relevant_results=metrics.num_relevant_results,
                num_total_results=metrics.num_total_results,
                
                # Ranking-Vergleich
                hybrid_ndcg_at_10=metrics.hybrid_ndcg_at_10,
                ml_ndcg_at_10=metrics.ml_ndcg_at_10,
                
                created_at=metrics.timestamp
            )
            
            # Speichere
            self.db.add(model)
            self.db.commit()
            self.db.refresh(model)
            
            # Konvertiere zurück zu Dataclass (mit ID)
            return SearchQualityMetrics(
                query=model.query,
                timestamp=model.created_at,
                precision_at_1=model.precision_at_1,
                precision_at_3=model.precision_at_3,
                precision_at_5=model.precision_at_5,
                precision_at_10=model.precision_at_10,
                recall_at_1=model.recall_at_1,
                recall_at_3=model.recall_at_3,
                recall_at_5=model.recall_at_5,
                recall_at_10=model.recall_at_10,
                ndcg_at_1=model.ndcg_at_1,
                ndcg_at_3=model.ndcg_at_3,
                ndcg_at_5=model.ndcg_at_5,
                ndcg_at_10=model.ndcg_at_10,
                mrr=model.mrr,
                average_relevance_score=model.average_relevance_score,
                num_relevant_results=model.num_relevant_results,
                num_total_results=model.num_total_results,
                hybrid_ndcg_at_10=model.hybrid_ndcg_at_10,
                ml_ndcg_at_10=model.ml_ndcg_at_10,
                session_id=model.session_id,
                user_id=model.user_id,
                document_type=model.document_type
            )
            
        except Exception as e:
            print(f"Fehler beim Speichern von Search Quality Metrics: {e}")
            self.db.rollback()
            raise
    
    def get_by_query(
        self,
        query: str,
        session_id: Optional[int] = None,
        limit: int = 10
    ) -> List['SearchQualityMetrics']:
        """
        Hole Metrics für eine Query.
        
        Args:
            query: Die ursprüngliche Query
            session_id: Optional Session-ID Filter
            limit: Maximale Anzahl Einträge
            
        Returns:
            Liste von SearchQualityMetrics (sortiert nach timestamp DESC)
        """
        try:
            from backend.app.models import SearchQualityMetricsModel
            from contexts.ragintegration.infrastructure.search_quality_metrics import SearchQualityMetrics
            
            # Base Query
            db_query = self.db.query(SearchQualityMetricsModel).filter(
                SearchQualityMetricsModel.query == query
            )
            
            # Session Filter
            if session_id is not None:
                db_query = db_query.filter(
                    SearchQualityMetricsModel.session_id == session_id
                )
            
            # Sortierung und Limit
            models = db_query.order_by(desc(SearchQualityMetricsModel.created_at)).limit(limit).all()
            
            # Konvertiere zu Dataclass
            return [self._model_to_metrics(m) for m in models]
            
        except Exception as e:
            print(f"Fehler beim Laden von Search Quality Metrics: {e}")
            return []
    
    def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        document_type: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List['SearchQualityMetrics']:
        """
        Hole Metrics für einen Zeitraum.
        
        Args:
            start_date: Start-Datum
            end_date: End-Datum
            document_type: Optional Document Type Filter
            user_id: Optional User-ID Filter
            
        Returns:
            Liste von SearchQualityMetrics
        """
        try:
            from backend.app.models import SearchQualityMetricsModel
            from contexts.ragintegration.infrastructure.search_quality_metrics import SearchQualityMetrics
            
            # Base Query
            db_query = self.db.query(SearchQualityMetricsModel).filter(
                and_(
                    SearchQualityMetricsModel.created_at >= start_date,
                    SearchQualityMetricsModel.created_at <= end_date
                )
            )
            
            # Filter
            if document_type:
                db_query = db_query.filter(
                    SearchQualityMetricsModel.document_type == document_type
                )
            
            if user_id:
                db_query = db_query.filter(
                    SearchQualityMetricsModel.user_id == user_id
                )
            
            # Sortierung
            models = db_query.order_by(desc(SearchQualityMetricsModel.created_at)).all()
            
            # Konvertiere zu Dataclass
            return [self._model_to_metrics(m) for m in models]
            
        except Exception as e:
            print(f"Fehler beim Laden von Search Quality Metrics: {e}")
            return []
    
    def get_aggregated_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        document_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Hole aggregierte Metriken über mehrere Queries.
        
        Args:
            start_date: Optional Start-Datum
            end_date: Optional End-Datum
            document_type: Optional Document Type Filter
            
        Returns:
            Dict mit aggregierten Metriken (Durchschnittswerte)
        """
        try:
            from backend.app.models import SearchQualityMetricsModel
            from sqlalchemy import func
            
            # Base Query
            db_query = self.db.query(SearchQualityMetricsModel)
            
            # Datum-Filter
            if start_date:
                db_query = db_query.filter(
                    SearchQualityMetricsModel.created_at >= start_date
                )
            if end_date:
                db_query = db_query.filter(
                    SearchQualityMetricsModel.created_at <= end_date
                )
            
            # Document Type Filter
            if document_type:
                db_query = db_query.filter(
                    SearchQualityMetricsModel.document_type == document_type
                )
            
            # Aggregation
            result = db_query.with_entities(
                func.avg(SearchQualityMetricsModel.precision_at_10).label('avg_precision_at_10'),
                func.avg(SearchQualityMetricsModel.recall_at_10).label('avg_recall_at_10'),
                func.avg(SearchQualityMetricsModel.ndcg_at_10).label('avg_ndcg_at_10'),
                func.avg(SearchQualityMetricsModel.mrr).label('avg_mrr'),
                func.avg(SearchQualityMetricsModel.hybrid_ndcg_at_10).label('avg_hybrid_ndcg_at_10'),
                func.avg(SearchQualityMetricsModel.ml_ndcg_at_10).label('avg_ml_ndcg_at_10'),
                func.count(SearchQualityMetricsModel.id).label('total_queries')
            ).first()
            
            if result and result.total_queries > 0:
                return {
                    'precision_at_10': float(result.avg_precision_at_10) if result.avg_precision_at_10 else 0.0,
                    'recall_at_10': float(result.avg_recall_at_10) if result.avg_recall_at_10 else 0.0,
                    'ndcg_at_10': float(result.avg_ndcg_at_10) if result.avg_ndcg_at_10 else 0.0,
                    'mrr': float(result.avg_mrr) if result.avg_mrr else 0.0,
                    'hybrid_ndcg_at_10': float(result.avg_hybrid_ndcg_at_10) if result.avg_hybrid_ndcg_at_10 else None,
                    'ml_ndcg_at_10': float(result.avg_ml_ndcg_at_10) if result.avg_ml_ndcg_at_10 else None,
                    'total_queries': int(result.total_queries)
                }
            else:
                return {
                    'precision_at_10': 0.0,
                    'recall_at_10': 0.0,
                    'ndcg_at_10': 0.0,
                    'mrr': 0.0,
                    'hybrid_ndcg_at_10': None,
                    'ml_ndcg_at_10': None,
                    'total_queries': 0
                }
            
        except Exception as e:
            print(f"Fehler beim Laden von aggregierten Metriken: {e}")
            return {
                'precision_at_10': 0.0,
                'recall_at_10': 0.0,
                'ndcg_at_10': 0.0,
                'mrr': 0.0,
                'hybrid_ndcg_at_10': None,
                'ml_ndcg_at_10': None,
                'total_queries': 0
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Hole Statistiken über gespeicherte Metrics.
        
        Returns:
            Dict mit Statistiken
        """
        try:
            from backend.app.models import SearchQualityMetricsModel
            from sqlalchemy import func
            
            # Total Count
            total_count = self.db.query(func.count(SearchQualityMetricsModel.id)).scalar() or 0
            
            if total_count == 0:
                return {
                    'total_count': 0,
                    'oldest_date': None,
                    'newest_date': None,
                    'unique_queries': 0
                }
            
            # Oldest/Newest
            oldest = self.db.query(SearchQualityMetricsModel).order_by(
                SearchQualityMetricsModel.created_at.asc()
            ).first()
            
            newest = self.db.query(SearchQualityMetricsModel).order_by(
                SearchQualityMetricsModel.created_at.desc()
            ).first()
            
            # Unique Queries
            unique_queries = self.db.query(SearchQualityMetricsModel.query).distinct().count()
            
            return {
                'total_count': total_count,
                'oldest_date': oldest.created_at.isoformat() if oldest else None,
                'newest_date': newest.created_at.isoformat() if newest else None,
                'unique_queries': unique_queries
            }
            
        except Exception as e:
            print(f"Fehler beim Laden von Statistiken: {e}")
            return {
                'total_count': 0,
                'oldest_date': None,
                'newest_date': None,
                'unique_queries': 0
            }
    
    def _model_to_metrics(self, model) -> 'SearchQualityMetrics':
        """
        Konvertiere Model zu SearchQualityMetrics Dataclass.
        
        Args:
            model: SearchQualityMetricsModel
            
        Returns:
            SearchQualityMetrics Dataclass
        """
        from contexts.ragintegration.infrastructure.search_quality_metrics import SearchQualityMetrics
        
        return SearchQualityMetrics(
            query=model.query,
            timestamp=model.created_at,
            precision_at_1=model.precision_at_1,
            precision_at_3=model.precision_at_3,
            precision_at_5=model.precision_at_5,
            precision_at_10=model.precision_at_10,
            recall_at_1=model.recall_at_1,
            recall_at_3=model.recall_at_3,
            recall_at_5=model.recall_at_5,
            recall_at_10=model.recall_at_10,
            ndcg_at_1=model.ndcg_at_1,
            ndcg_at_3=model.ndcg_at_3,
            ndcg_at_5=model.ndcg_at_5,
            ndcg_at_10=model.ndcg_at_10,
            mrr=model.mrr,
            average_relevance_score=model.average_relevance_score,
            num_relevant_results=model.num_relevant_results,
            num_total_results=model.num_total_results,
            hybrid_ndcg_at_10=model.hybrid_ndcg_at_10,
            ml_ndcg_at_10=model.ml_ndcg_at_10,
            session_id=model.session_id,
            user_id=model.user_id,
            document_type=model.document_type
        )
