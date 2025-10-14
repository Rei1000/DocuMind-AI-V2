"""
SQLAlchemy Models für Document Workflow Context.

Diese Models sind spezifisch für den Workflow-Context und erweitern
die bestehenden Upload-Models um Workflow-Funktionalität.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from backend.app.database import Base


class DocumentWorkflowStatus(enum.Enum):
    """Workflow-Status für Dokumente"""
    DRAFT = "draft"           # Initial nach Upload
    IN_REVIEW = "in_review"   # Zur Prüfung (veraltet - nicht mehr verwendet)
    REVIEWED = "reviewed"     # Geprüft (Abteilungsleiter)
    APPROVED = "approved"     # Freigegeben (QM)
    REJECTED = "rejected"     # Zurückgewiesen


class DocumentStatusChange(Base):
    """
    Audit Trail für Status-Änderungen.
    
    Protokolliert jede Status-Änderung eines Dokuments
    für lückenlose Nachvollziehbarkeit.
    """
    __tablename__ = "document_status_changes"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_document_id = Column(Integer, ForeignKey("upload_documents.id"), nullable=False, index=True)
    
    # Status Change
    from_status = Column(String(20), nullable=True, comment="Vorheriger Status")
    to_status = Column(String(20), nullable=False, comment="Neuer Status")
    
    # Change Information
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    change_reason = Column(Text, nullable=True, comment="Grund für Änderung")
    comment = Column(Text, nullable=True, comment="Kommentar zur Änderung")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<DocumentStatusChange(id={self.id}, doc_id={self.upload_document_id}, {self.from_status}→{self.to_status})>"


class DocumentComment(Base):
    """
    Kommentare zu Dokumenten.
    
    Erlaubt strukturierte Kommunikation über Dokumente
    zwischen verschiedenen Rollen.
    """
    __tablename__ = "document_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_document_id = Column(Integer, ForeignKey("upload_documents.id"), nullable=False, index=True)
    
    # Comment Content
    comment_text = Column(Text, nullable=False, comment="Kommentar-Text")
    comment_type = Column(String(20), nullable=False, default="general",
                         comment="general, review, rejection, approval")
    
    # Related to specific page?
    page_number = Column(Integer, nullable=True, comment="Bezieht sich auf bestimmte Seite?")
    
    # Comment Metadata
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Is this comment part of a status change?
    status_change_id = Column(Integer, ForeignKey("document_status_changes.id"), nullable=True)
    
    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<DocumentComment(id={self.id}, doc_id={self.upload_document_id}, type='{self.comment_type}')>"
