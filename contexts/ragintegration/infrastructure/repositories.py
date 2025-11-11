"""
SQLAlchemy Repository Implementations für RAG Integration Context.

Implementiert die Repository Interfaces mit SQLAlchemy ORM.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, desc, update
import json

from contexts.ragintegration.domain.entities import (
    IndexedDocument, DocumentChunk, ChatSession, ChatMessage, RAGFeedback
)
from contexts.ragintegration.domain.value_objects import ChunkMetadata
from contexts.ragintegration.domain.repositories import (
    IndexedDocumentRepository, DocumentChunkRepository, 
    ChatSessionRepository, ChatMessageRepository, RAGFeedbackRepository
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
                model = ChatMessageModel(
                    session_id=chat_message.session_id,
                    role=chat_message.role,
                    content=chat_message.content,
                    created_at=chat_message.created_at,
                    source_chunks=json.dumps([ref.__dict__ for ref in chat_message.source_references]) if chat_message.source_references else None,
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
                        model.source_chunks = json.dumps([ref.__dict__ for ref in chat_message.source_references])
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
    ) -> dict:
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