"""
SQLAlchemy ORM Models für DocuMind-AI V2.

Diese Datei enthält alle Datenbank-Modelle für die Anwendung.
Die Modelle sind nach DDD-Contexts organisiert.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, JSON, Enum, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import json

from app.database import Base


# ================== ENUMS ==================

class UserLevel(enum.Enum):
    """User Berechtigungsstufen im QMS"""
    LEVEL_1 = 1  # Mitarbeiter - Keine Dokumente
    LEVEL_2 = 2  # Teamleiter - Lesen (eigene IGs)
    LEVEL_3 = 3  # Abteilungsleiter - Lesen + Prüfen (eigene IGs)
    LEVEL_4 = 4  # QM Manager - Alle Rechte

class ProcessingMethod(enum.Enum):
    """Verarbeitungsmethode für Dokumente"""
    OCR = "ocr"
    VISION = "vision"

class DocumentWorkflowStatus(enum.Enum):
    """Workflow-Status für Dokumente"""
    DRAFT = "draft"           # Initial nach Upload
    IN_REVIEW = "in_review"   # Zur Prüfung (Abteilungsleiter)
    REVIEWED = "reviewed"     # Geprüft
    APPROVED = "approved"     # Freigegeben (QM)
    REJECTED = "rejected"     # Zurückgewiesen

# ================== USERS CONTEXT ==================

class User(Base):
    """User Model - Zentrale Benutzerverwaltung"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    interest_group_assignments = relationship("UserInterestGroup", back_populates="user", cascade="all, delete-orphan")
    created_templates = relationship("PromptTemplateModel", back_populates="created_by_user", foreign_keys="PromptTemplateModel.created_by")
    uploaded_documents = relationship("UploadDocument", back_populates="uploaded_by_user", foreign_keys="UploadDocument.uploaded_by_user_id")
    
    # Workflow Relationships
    status_changes = relationship("DocumentStatusChange", back_populates="changed_by_user", foreign_keys="DocumentStatusChange.changed_by_user_id")
    comments = relationship("DocumentComment", back_populates="created_by_user", foreign_keys="DocumentComment.created_by_user_id")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"


# ================== INTEREST GROUPS CONTEXT ==================

class InterestGroup(Base):
    """Interest Group Model - Fachbereiche/Abteilungen"""
    __tablename__ = "interest_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False, comment="Eindeutiger Code (z.B. 'PROD', 'QA')")
    name = Column(String(200), nullable=False, comment="Anzeigename")
    description = Column(Text, nullable=True, comment="Beschreibung der Interest Group")
    color = Column(String(7), nullable=False, default="#6B7280", comment="Hex-Farbe für UI")
    icon = Column(String(50), nullable=True, comment="Icon-Name für UI (z.B. 'factory', 'clipboard')")
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, comment="Ob die Interest Group aktiv ist")
    
    # Metadata
    sort_order = Column(Integer, default=0, nullable=False, comment="Sortierreihenfolge in UI")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user_assignments = relationship("UserInterestGroup", back_populates="interest_group", cascade="all, delete-orphan")
    document_assignments = relationship("UploadDocumentInterestGroup", back_populates="interest_group", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<InterestGroup(id={self.id}, code='{self.code}', name='{self.name}')>"


class UserInterestGroup(Base):
    """User-InterestGroup Zuordnung mit Level"""
    __tablename__ = "user_interest_groups"
    __table_args__ = (
        UniqueConstraint('user_id', 'interest_group_id', name='_user_interest_group_uc'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    interest_group_id = Column(Integer, ForeignKey("interest_groups.id"), nullable=False, index=True)
    
    # Berechtigungslevel (1-4)
    level = Column(Integer, nullable=False, default=1, comment="Berechtigungslevel: 1=Lesen, 2=Bearbeiten, 3=Prüfen, 4=Freigeben")
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="interest_group_assignments", foreign_keys=[user_id])
    interest_group = relationship("InterestGroup", back_populates="user_assignments")
    
    def __repr__(self):
        return f"<UserInterestGroup(user_id={self.user_id}, group_id={self.interest_group_id}, level={self.level})>"


# ================== DOCUMENT TYPES CONTEXT ==================

class DocumentTypeModel(Base):
    """
    Document Type Modell für verschiedene QMS-Dokumenttypen.
    
    Definiert die erlaubten Dokumenttypen im System mit ihren
    spezifischen Eigenschaften und Verarbeitungsregeln.
    
    Beispiele:
    - SOP (Standard Operating Procedure)
    - Arbeitsanweisung (Work Instruction)  
    - Prüfplan (Test Plan)
    - etc.
    
    DDD Context: documenttypes
    """
    __tablename__ = "document_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True, comment="Anzeigename (z.B. 'Arbeitsanweisung')")
    code = Column(String(50), nullable=False, unique=True, index=True, comment="Interner Code (z.B. 'WORK_INSTRUCTION')")
    description = Column(Text, nullable=True, comment="Beschreibung des Dokumenttyps")
    
    # File Settings
    allowed_file_types = Column(Text, nullable=False, default='[".pdf"]', comment="JSON Array erlaubter Dateitypen")
    max_file_size_mb = Column(Integer, nullable=False, default=10, comment="Max. Dateigröße in MB")
    
    # Processing Settings
    requires_ocr = Column(Boolean, nullable=False, default=False, comment="OCR erforderlich?")
    requires_vision = Column(Boolean, nullable=False, default=False, comment="Vision AI erforderlich?")
    processing_method = Column(Enum(ProcessingMethod), nullable=False, default=ProcessingMethod.OCR, 
                             comment="Standard-Verarbeitungsmethode")
    
    # AI Settings (Link zu Prompt Template)
    default_prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=True,
                                      comment="Standard Prompt Template für diesen Dokumenttyp")
    
    # Status & Display
    is_active = Column(Boolean, nullable=False, default=True, index=True, comment="Aktiv für neue Uploads?")
    sort_order = Column(Integer, nullable=False, default=0, comment="Anzeigereihenfolge")
    color = Column(String(7), nullable=True, comment="Hex-Farbe für UI")
    icon = Column(String(50), nullable=True, comment="Icon-Name für UI")
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    prompt_templates = relationship("PromptTemplateModel", back_populates="document_type", 
                                  foreign_keys="PromptTemplateModel.document_type_id")
    default_prompt_template = relationship("PromptTemplateModel", 
                                         foreign_keys=[default_prompt_template_id],
                                         post_update=True)
    uploaded_documents = relationship("UploadDocument", back_populates="document_type")
    
    @property
    def allowed_file_types_list(self):
        """Gibt allowed_file_types als Python Liste zurück"""
        try:
            return json.loads(self.allowed_file_types)
        except:
            return [".pdf"]
    
    def __repr__(self):
        return f"<DocumentType(id={self.id}, code='{self.code}', name='{self.name}')>"


class PromptTemplateModel(Base):
    """
    Prompt Template Modell für wiederverwendbare AI Prompts.
    
    Speichert erfolgreiche Prompt-Konfigurationen aus dem AI Playground,
    die dann bei Document Upload wiederverwendet werden können.
    
    Features:
    - AI Model Configuration (temperature, max_tokens, etc.)
    - Document Type Linking (optional)
    - Status Management (draft, active, archived, deprecated)
    - Versioning (Semantic Versioning)
    - Usage Tracking (success_count, last_used_at)
    - Tag-based Categorization (JSON)
    - Example Input/Output for Documentation
    
    Relationships:
    - document_type: Many-to-One (optional)
    
    DDD Context: prompttemplates
    """
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True, comment="Template-Name (eindeutig)")
    description = Column(Text, nullable=True, comment="Beschreibung des Template-Zwecks")
    prompt_text = Column(Text, nullable=False, comment="Der eigentliche Prompt-Text")
    system_instructions = Column(Text, nullable=True, comment="Optional: System-Level Instructions")
    
    # Document Type Linking
    document_type_id = Column(Integer, ForeignKey("document_types.id"), nullable=True, index=True, 
                             comment="Verknüpfung mit Dokumenttyp")
    
    # AI Configuration
    ai_model = Column(String(100), nullable=False, default="gpt-4o-mini", comment="Empfohlenes AI-Modell")
    temperature = Column(Integer, nullable=False, default=0, comment="Temperature * 100 (0-200)")  # Store as int: 0-200 (0.0-2.0)
    max_tokens = Column(Integer, nullable=False, default=4000, comment="Max Output Tokens")
    top_p = Column(Integer, nullable=False, default=100, comment="Top P * 100 (0-100)")  # Store as int: 0-100 (0.0-1.0)
    detail_level = Column(String(10), nullable=False, default="high", comment="Vision Detail Level (high/low)")
    
    # Status & Version
    status = Column(String(20), nullable=False, default="draft", index=True, 
                   comment="Status: draft, active, archived, deprecated")
    version = Column(String(20), nullable=False, default="1.0", comment="Versionsnummer")
    
    # Usage Tracking
    tested_successfully = Column(Boolean, nullable=False, default=False, 
                               comment="Wurde erfolgreich getestet?")
    success_count = Column(Integer, nullable=False, default=0, comment="Anzahl erfolgreicher Verwendungen")
    last_used_at = Column(DateTime, nullable=True, comment="Letzte Verwendung")
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    tags = Column(Text, nullable=True, comment="JSON Array von Tags")
    example_input = Column(Text, nullable=True, comment="Beispiel-Input für Dokumentation")
    example_output = Column(Text, nullable=True, comment="Beispiel-Output für Dokumentation")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    document_type = relationship("DocumentTypeModel", back_populates="prompt_templates", 
                               foreign_keys=[document_type_id])
    created_by_user = relationship("User", back_populates="created_templates", foreign_keys=[created_by])
    
    @property
    def tags_list(self):
        """Gibt Tags als Python Liste zurück"""
        try:
            return json.loads(self.tags) if self.tags else []
        except:
            return []
    
    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, name='{self.name}', status='{self.status}')>"


# ================== DOCUMENT UPLOAD CONTEXT ==================

class UploadDocument(Base):
    """
    Uploaded Document Model.
    
    Repräsentiert ein hochgeladenes Dokument mit allen Metadaten.
    Ein Dokument kann mehrere Seiten haben (UploadDocumentPage).
    
    DDD Context: documentupload
    """
    __tablename__ = "upload_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # File Information
    filename = Column(String(255), nullable=False, comment="Gespeicherter Dateiname")
    original_filename = Column(String(255), nullable=False, comment="Original Dateiname vom User")
    file_path = Column(String(500), nullable=False, comment="Relativer Pfad im Storage")
    file_size_bytes = Column(Integer, nullable=False, comment="Dateigröße in Bytes")
    file_type = Column(String(10), nullable=False, comment="Dateityp (.pdf, .docx, etc.)")
    mime_type = Column(String(100), nullable=True, comment="MIME Type")
    
    # Document Metadata
    document_type_id = Column(Integer, ForeignKey("document_types.id"), nullable=False, index=True)
    qm_chapter = Column(String(50), nullable=True, comment="QM Handbuch Kapitel")
    version = Column(String(20), nullable=False, comment="Dokumentversion (z.B. v1.0.0)")
    
    # Processing Information
    page_count = Column(Integer, nullable=False, default=0, comment="Anzahl der Seiten")
    processing_method = Column(Enum(ProcessingMethod), nullable=False, default=ProcessingMethod.OCR)
    processing_status = Column(String(20), nullable=False, default="pending", 
                             comment="pending, processing, completed, failed")
    processing_error = Column(Text, nullable=True, comment="Fehlermeldung bei Processing")
    
    # Workflow Status
    workflow_status = Column(Enum(DocumentWorkflowStatus), nullable=False, default=DocumentWorkflowStatus.DRAFT,
                           index=True, comment="Aktueller Workflow-Status")
    
    # Upload Information
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    document_type = relationship("DocumentTypeModel", back_populates="uploaded_documents")
    uploaded_by_user = relationship("User", back_populates="uploaded_documents", foreign_keys=[uploaded_by_user_id])
    pages = relationship("UploadDocumentPage", back_populates="document", cascade="all, delete-orphan",
                        order_by="UploadDocumentPage.page_number")
    interest_group_assignments = relationship("UploadDocumentInterestGroup", back_populates="document", 
                                            cascade="all, delete-orphan")
    ai_responses = relationship("DocumentAIResponse", back_populates="upload_document", cascade="all, delete-orphan")
    
    # Workflow Relationships
    status_changes = relationship("DocumentStatusChange", back_populates="document", cascade="all, delete-orphan",
                                order_by="desc(DocumentStatusChange.changed_at)")
    comments = relationship("DocumentComment", back_populates="document", cascade="all, delete-orphan",
                          order_by="desc(DocumentComment.created_at)")
    
    def __repr__(self):
        return f"<UploadDocument(id={self.id}, filename='{self.filename}', status='{self.workflow_status.value}')>"


class UploadDocumentPage(Base):
    """
    Document Page Model.
    
    Repräsentiert eine einzelne Seite eines Dokuments.
    Jede Seite kann separat mit AI verarbeitet werden.
    
    DDD Context: documentupload
    """
    __tablename__ = "upload_document_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_document_id = Column(Integer, ForeignKey("upload_documents.id"), nullable=False, index=True)
    
    # Page Information
    page_number = Column(Integer, nullable=False, comment="Seitennummer (1-basiert)")
    preview_path = Column(String(500), nullable=True, comment="Pfad zum Preview-Bild")
    thumbnail_path = Column(String(500), nullable=True, comment="Pfad zum Thumbnail")
    
    # Processing Status
    is_processed = Column(Boolean, nullable=False, default=False, comment="Wurde mit AI verarbeitet?")
    processed_at = Column(DateTime, nullable=True, comment="Wann wurde verarbeitet?")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("UploadDocument", back_populates="pages")
    ai_response = relationship("DocumentAIResponse", uselist=False, back_populates="upload_document_page")
    
    def __repr__(self):
        return f"<UploadDocumentPage(id={self.id}, doc_id={self.upload_document_id}, page={self.page_number})>"


class UploadDocumentInterestGroup(Base):
    """
    Document-InterestGroup Assignment.
    
    Verknüpft Dokumente mit Interest Groups für Zugriffskontrolle.
    
    DDD Context: documentupload
    """
    __tablename__ = "upload_document_interest_groups"
    __table_args__ = (
        UniqueConstraint('upload_document_id', 'interest_group_id', name='_doc_interest_group_uc'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    upload_document_id = Column(Integer, ForeignKey("upload_documents.id"), nullable=False, index=True)
    interest_group_id = Column(Integer, ForeignKey("interest_groups.id"), nullable=False, index=True)
    
    # Assignment Metadata
    assigned_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("UploadDocument", back_populates="interest_group_assignments")
    interest_group = relationship("InterestGroup", back_populates="document_assignments")
    
    def __repr__(self):
        return f"<UploadDocumentInterestGroup(doc_id={self.upload_document_id}, group_id={self.interest_group_id})>"


# ================== AI PROCESSING CONTEXT ==================

class DocumentAIResponse(Base):
    """
    AI Processing Result für Document Pages.
    
    Speichert die strukturierten JSON-Responses der AI-Analyse
    für jede Dokumentseite.
    
    DDD Context: documentupload (AI Processing Sub-Domain)
    """
    __tablename__ = "document_ai_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Document References
    upload_document_id = Column(Integer, ForeignKey("upload_documents.id"), nullable=False, index=True)
    upload_document_page_id = Column(Integer, ForeignKey("upload_document_pages.id"), nullable=False, 
                                   unique=True, index=True)
    
    # Prompt Information
    prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=True)
    prompt_text = Column(Text, nullable=False, comment="Verwendeter Prompt (für Audit)")
    
    # AI Model Info (keine FK, da AIModel-Tabelle nicht existiert)
    ai_model_id = Column(Integer, nullable=False)
    model_name = Column(String(100), nullable=False, comment="Model Name für Anzeige")
    
    # Response Data
    json_response = Column(Text, nullable=False, comment="Strukturierte JSON Response")
    processing_status = Column(String(20), nullable=False, default="pending",
                             comment="pending, processing, completed, failed")
    error_message = Column(Text, nullable=True)
    
    # Performance Metrics
    processing_time_ms = Column(Float, nullable=True, comment="Verarbeitungszeit in ms")
    tokens_sent = Column(Integer, nullable=True, comment="Anzahl gesendeter Tokens")
    tokens_received = Column(Integer, nullable=True, comment="Anzahl empfangener Tokens")
    
    # Timestamps
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    upload_document = relationship("UploadDocument", foreign_keys=[upload_document_id])
    upload_document_page = relationship("UploadDocumentPage", foreign_keys=[upload_document_page_id], uselist=False)
    prompt_template = relationship("PromptTemplateModel", foreign_keys=[prompt_template_id])
    
    def __repr__(self):
        return f"<DocumentAIResponse(id={self.id}, page_id={self.upload_document_page_id}, status='{self.processing_status}')>"


# ================== WORKFLOW CONTEXT ==================

class DocumentStatusChange(Base):
    """
    Audit Trail für Status-Änderungen.
    
    Protokolliert jede Status-Änderung eines Dokuments
    für lückenlose Nachvollziehbarkeit.
    
    DDD Context: documentworkflow
    """
    __tablename__ = "document_status_changes"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_document_id = Column(Integer, ForeignKey("upload_documents.id"), nullable=False, index=True)
    
    # Status Change
    from_status = Column(Enum(DocumentWorkflowStatus), nullable=True, comment="Vorheriger Status")
    to_status = Column(Enum(DocumentWorkflowStatus), nullable=False, comment="Neuer Status")
    
    # Change Information
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    change_reason = Column(Text, nullable=True, comment="Grund für Änderung")
    comment = Column(Text, nullable=True, comment="Kommentar zur Änderung")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("UploadDocument", back_populates="status_changes")
    changed_by_user = relationship("User", back_populates="status_changes", foreign_keys=[changed_by_user_id])
    
    def __repr__(self):
        return f"<DocumentStatusChange(id={self.id}, doc_id={self.upload_document_id}, {self.from_status}→{self.to_status})>"


class DocumentComment(Base):
    """
    Kommentare zu Dokumenten.
    
    Erlaubt strukturierte Kommunikation über Dokumente
    zwischen verschiedenen Rollen.
    
    DDD Context: documentworkflow
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
    
    # Relationships
    document = relationship("UploadDocument", back_populates="comments")
    created_by_user = relationship("User", back_populates="comments", foreign_keys=[created_by_user_id])
    
    def __repr__(self):
        return f"<DocumentComment(id={self.id}, doc_id={self.upload_document_id}, type='{self.comment_type}')>"