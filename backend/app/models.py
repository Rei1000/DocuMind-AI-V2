"""
📊 DocuMind-AI V2 Data Models (SQLAlchemy ORM)

Minimales DDD-orientiertes Datenmodell fokussiert auf:
- User Management (RBAC)
- Interest Groups (13 Stakeholder-System)
- User Group Memberships (Many-to-Many)
- Document Types (QMS Document Classification)

Version: 2.0.0 (Clean DDD Architecture)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# === KERN-MODELLE: USER & INTEREST GROUPS ===

class InterestGroup(Base):
    """
    Interessensgruppen-Modell für das 13-Stakeholder-System.
    
    Repräsentiert organisatorische Einheiten von internen Teams
    (Einkauf, QM, Entwicklung) bis zu externen Stakeholdern.
    
    Features:
    - Granulare Berechtigungssteuerung über group_permissions
    - Unterscheidung zwischen internen/externen Gruppen
    - Soft-Delete über is_active
    
    Relationships:
    - users: Many-to-Many über UserGroupMembership
    """
    __tablename__ = "interest_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    group_permissions = Column(Text, comment="JSON-String mit Gruppen-Berechtigungen")
    ai_functionality = Column(Text, comment="Verfügbare KI-Funktionen")
    typical_tasks = Column(Text, comment="Typische Aufgaben")
    is_external = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="Erstellt von (QMS Admin)")
    
    # Relationships
    user_memberships = relationship("UserGroupMembership", back_populates="interest_group")
    created_by = relationship("User", foreign_keys=[created_by_id], post_update=True)
    
    def get_group_permissions_list(self):
        """Gruppen-Permissions als Python-Liste"""
        try:
            import json
            if self.group_permissions:
                return json.loads(self.group_permissions)
            return []
        except (json.JSONDecodeError, TypeError, AttributeError):
            return []


class User(Base):
    """
    Benutzer-Modell für Authentifizierung und RBAC.
    
    Features:
    - Verschlüsselte Passwort-Speicherung (bcrypt)
    - Eindeutige Email/Employee-ID
    - Soft-Delete für Audit-Trail
    - Multi-Department Support via UserGroupMembership
    - QMS Admin (Level 5) - Spezielle System-Admin-Rechte
    
    Relationships:
    - interest_groups: Many-to-Many über UserGroupMembership
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(200), nullable=False)
    employee_id = Column(String(50), unique=True)
    organizational_unit = Column(String(100), comment="Primäre Organisationseinheit")
    hashed_password = Column(String(255))
    
    # Berechtigungen (Level 1-4 nur in UserGroupMembership, Level 5 = QMS Admin hier)
    individual_permissions = Column(Text, comment="JSON-String mit individuellen Berechtigungen")
    is_qms_admin = Column(Boolean, default=False, nullable=False, comment="Level 5 - System Admin (User-Management, Group-Management)")
    cannot_be_deleted = Column(Boolean, default=False, nullable=False, comment="Schutz für QMS Admin")
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    group_memberships = relationship("UserGroupMembership", back_populates="user", foreign_keys="UserGroupMembership.user_id")


class UserGroupMembership(Base):
    """
    Many-to-Many Zuordnung User ↔ InterestGroup.
    
    Ermöglicht Multiple Abteilungen pro User mit individuellen Levels (1-4):
    
    Beispiel:
        User: reiner@company.com
        ├── QM-Abteilung (Level 4 - QM-Manager) 
        ├── Service (Level 3 - Abteilungsleiter)
        └── IT (Level 1 - Mitarbeiter)
    
    Permission Levels:
    - Level 1: Mitarbeiter (Lesen, Vorschlagen)
    - Level 2: Teamleiter (Team-Freigabe)
    - Level 3: Abteilungsleiter (Abteilungs-Freigabe)
    - Level 4: QM-Manager (QM-Freigabe in dieser Group)
    - Level 5: Nur QMS Admin (User.is_qms_admin)
    
    Features:
    - Verschiedene Approval-Levels je Gruppe (1-4)
    - Unique Constraint: Ein User kann nur 1x pro Gruppe sein
    - Audit-Trail via joined_at/assigned_by
    - Soft-Delete via is_active
    """
    __tablename__ = "user_group_memberships"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    interest_group_id = Column(Integer, ForeignKey("interest_groups.id"), nullable=False, index=True)
    
    # Rollen & Berechtigungen (1-4, nicht 5!)
    role_in_group = Column(String(50), comment="z.B. 'Teamleiter', 'Fachexperte'")
    approval_level = Column(Integer, default=1, nullable=False, comment="1=Mitarbeiter, 2=Teamleiter, 3=Abteilungsleiter, 4=QM-Manager")
    is_department_head = Column(Boolean, default=False, nullable=False)
    
    # Audit
    is_active = Column(Boolean, default=True, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, comment="Bemerkungen zur Zuordnung")
    
    # Relationships
    user = relationship("User", back_populates="group_memberships", foreign_keys=[user_id])
    interest_group = relationship("InterestGroup", back_populates="user_memberships")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id], post_update=True)
    
    def __repr__(self):
        return f"<UserGroupMembership(user_id={self.user_id}, group_id={self.interest_group_id}, level={self.approval_level})>"


# === DOCUMENT MANAGEMENT MODELS ===

class DocumentTypeModel(Base):
    """
    Dokumenttyp-Modell für QMS-Dokumente.
    
    Definiert Kategorien von QMS-Dokumenten (z.B. SOP, Flussdiagramm, Formular).
    Jeder Typ hat spezifische Validierungsregeln und kann mit Prompt Templates verknüpft werden.
    
    Features:
    - File Type Validation (allowed_file_types als JSON)
    - Max File Size Limit
    - AI Processing Requirements (OCR, Vision)
    - Default Prompt Template Assignment
    - Soft-Delete über is_active
    
    Relationships:
    - prompt_templates: One-to-Many (default_prompt_template_id)
    
    DDD Context: documenttypes
    """
    __tablename__ = "document_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True, comment="Anzeigename (z.B. 'Flussdiagramm')")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="Technischer Code (z.B. 'FLOWCHART')")
    description = Column(Text, nullable=True, comment="Detaillierte Beschreibung")
    
    # File Validation Rules
    allowed_file_types = Column(Text, nullable=False, comment="JSON Array: ['.pdf', '.png', '.jpg']")
    max_file_size_mb = Column(Integer, nullable=False, default=10, comment="Maximale Dateigröße in MB")
    
    # AI Processing Requirements
    requires_ocr = Column(Boolean, default=False, nullable=False, comment="Benötigt OCR-Verarbeitung")
    requires_vision = Column(Boolean, default=False, nullable=False, comment="Benötigt Vision AI")
    
    # Prompt Template Integration
    default_prompt_template_id = Column(Integer, nullable=True, comment="Standard-Template für diesen Typ")
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="Erstellt von User ID")
    is_active = Column(Boolean, default=True, nullable=False, index=True, comment="Ist aktiv?")
    sort_order = Column(Integer, default=0, nullable=False, comment="Sortierung in UI")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Future Relationships (will be added when prompttemplates context is implemented)
    # default_prompt_template = relationship("PromptTemplateModel", foreign_keys=[default_prompt_template_id])
    
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
    version = Column(String(20), nullable=False, default="1.0", comment="Version (Semantic Versioning)")
    
    # Usage Tracking
    tested_successfully = Column(Boolean, default=False, nullable=False, comment="Wurde erfolgreich getestet?")
    success_count = Column(Integer, default=0, nullable=False, comment="Anzahl erfolgreicher Verwendungen")
    last_used_at = Column(DateTime, nullable=True, comment="Wann zuletzt verwendet?")
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="Erstellt von User ID")
    tags = Column(Text, nullable=True, comment="JSON Array: Tags für Kategorisierung")
    
    # Example Data (for documentation)
    example_input = Column(Text, nullable=True, comment="Beispiel Input für Dokumentation")
    example_output = Column(Text, nullable=True, comment="Beispiel Output für Dokumentation")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    # document_type = relationship("DocumentTypeModel", foreign_keys=[document_type_id])
    
    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, name='{self.name}', status='{self.status}')>"


# === DOCUMENT UPLOAD SYSTEM (Phase 1.2) ===

class UploadDocument(Base):
    """
    Hochgeladenes Dokument mit Metadaten.
    
    Context: documentupload
    
    Features:
    - Multi-Format Support (PDF, DOCX, PNG, JPG)
    - Automatisches Page-Splitting
    - Processing Method (OCR oder Vision)
    - Metadaten (QM-Kapitel, Version)
    
    Relationships:
    - pages: One-to-Many zu UploadDocumentPage
    - interest_groups: Many-to-Many über UploadDocumentInterestGroup
    - workflow_document: One-to-One zu WorkflowDocument
    """
    __tablename__ = "upload_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, comment="Interner Dateiname")
    original_filename = Column(String(255), nullable=False, comment="Original Dateiname vom User")
    file_size_bytes = Column(Integer, nullable=False)
    file_type = Column(String(10), nullable=False, comment="pdf, docx, png, jpg")
    document_type_id = Column(Integer, ForeignKey("document_types.id"), nullable=False)
    qm_chapter = Column(String(50), nullable=True, comment="QM-Kapitel (z.B. 5.2)")
    version = Column(String(20), nullable=False, comment="Version (z.B. v1.0.0)")
    page_count = Column(Integer, nullable=True, comment="Anzahl Seiten")
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    file_path = Column(String(500), nullable=False, comment="Pfad zum Original")
    processing_method = Column(String(20), nullable=False, comment="ocr oder vision")
    processing_status = Column(String(20), default="pending", nullable=False, comment="pending, processing, completed, failed")
    
    # Workflow Status (Phase 4)
    workflow_status = Column(String(20), default="draft", nullable=False, comment="draft, reviewed, approved, rejected")
    
    # Relationships
    document_type = relationship("DocumentTypeModel", foreign_keys=[document_type_id])
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_user_id])
    pages = relationship("UploadDocumentPage", back_populates="document", cascade="all, delete-orphan")
    interest_groups = relationship("UploadDocumentInterestGroup", back_populates="document", cascade="all, delete-orphan")
    # Relationship zu RAG-IndexedDocument entfernt (DDD: keine Cross-Context-Relationships)
    # Verwende stattdessen: contexts/ragintegration Repository-Pattern
    # indexed_document wird über indexed_document_repo.get_by_upload_document_id(id) abgerufen
    
    # Workflow Relationships
    workflow_history = relationship("DocumentStatusChange", back_populates="document", cascade="all, delete-orphan")
    comments = relationship("DocumentComment", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UploadDocument(id={self.id}, filename='{self.filename}', status='{self.processing_status}')>"


class UploadDocumentPage(Base):
    """
    Einzelne Seite eines hochgeladenen Dokuments.
    
    Context: documentupload
    
    Features:
    - Preview-Bild (Full-Size)
    - Thumbnail
    - Dimensionen (Breite, Höhe)
    
    Relationships:
    - document: Many-to-One zu UploadDocument
    """
    __tablename__ = "upload_document_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_document_id = Column(Integer, ForeignKey("upload_documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False, comment="1-basiert")
    preview_image_path = Column(String(500), nullable=False, comment="Pfad zum Preview-Bild")
    thumbnail_path = Column(String(500), nullable=True, comment="Pfad zum Thumbnail")
    width = Column(Integer, nullable=True, comment="Breite in Pixel")
    height = Column(Integer, nullable=True, comment="Höhe in Pixel")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("UploadDocument", back_populates="pages")
    
    def __repr__(self):
        return f"<UploadDocumentPage(id={self.id}, document_id={self.upload_document_id}, page={self.page_number})>"


class UploadDocumentInterestGroup(Base):
    """
    Zuweisung eines Dokuments zu einer Interest Group.
    
    Context: documentupload
    
    Many-to-Many Relationship zwischen UploadDocument und InterestGroup.
    
    Relationships:
    - document: Many-to-One zu UploadDocument
    - interest_group: Many-to-One zu InterestGroup
    - assigned_by: Many-to-One zu User
    """
    __tablename__ = "upload_document_interest_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_document_id = Column(Integer, ForeignKey("upload_documents.id"), nullable=False)
    interest_group_id = Column(Integer, ForeignKey("interest_groups.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    document = relationship("UploadDocument", back_populates="interest_groups")
    interest_group = relationship("InterestGroup")
    assigned_by = relationship("User", foreign_keys=[assigned_by_user_id])
    
    def __repr__(self):
        return f"<UploadDocumentInterestGroup(doc_id={self.upload_document_id}, group_id={self.interest_group_id})>"

# RAG Models wurden entfernt - verwende jetzt:
# contexts/ragintegration/infrastructure/models.py
# - IndexedDocumentModel (statt RAGIndexedDocument)
# - DocumentChunkModel (statt RAGDocumentChunk)


# === WORKFLOW MODELS (Phase 4) ===

class DocumentStatusChange(Base):
    """
    Workflow-Status-Änderung für Audit Trail.
    
    Context: documentupload
    
    Features:
    - Vollständiger Audit Trail für alle Status-Änderungen
    - User-Tracking (wer hat was wann geändert)
    - Grund für Änderung (reason)
    - Chronologische Sortierung
    
    Relationships:
    - document: Many-to-One zu UploadDocument
    - changed_by: Many-to-One zu User
    """
    __tablename__ = "document_status_changes"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_document_id = Column(Integer, ForeignKey("upload_documents.id"), nullable=False, index=True)
    from_status = Column(String(20), nullable=False, comment="Vorheriger Status")
    to_status = Column(String(20), nullable=False, comment="Neuer Status")
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Zeitstempel der Änderung")
    change_reason = Column(Text, nullable=False, comment="Grund für die Änderung")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("UploadDocument", foreign_keys=[upload_document_id])
    changed_by = relationship("User", foreign_keys=[changed_by_user_id])
    
    def __repr__(self):
        return f"<DocumentStatusChange(id={self.id}, doc_id={self.upload_document_id}, {self.from_status}→{self.to_status})>"


class DocumentComment(Base):
    """
    Kommentar zu einem Dokument.
    
    Context: documentupload
    
    Features:
    - Verschiedene Kommentar-Typen (general, review, approval, rejection)
    - User-Tracking (wer hat kommentiert)
    - Chronologische Sortierung
    
    Relationships:
    - document: Many-to-One zu UploadDocument
    - user: Many-to-One zu User
    """
    __tablename__ = "document_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_document_id = Column(Integer, ForeignKey("upload_documents.id"), nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment_text = Column(Text, nullable=False, comment="Kommentar-Text")
    comment_type = Column(String(20), nullable=False, comment="general, review, approval, rejection")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("UploadDocument", foreign_keys=[upload_document_id])
    user = relationship("User", foreign_keys=[created_by_user_id])
    
    def __repr__(self):
        return f"<DocumentComment(id={self.id}, doc_id={self.upload_document_id}, type='{self.comment_type}')>"


# ==================== RAG MODELS ENTFERNT ====================
# RAG Models wurden entfernt um SQLAlchemy-Kollisionen zu vermeiden
# Verwende stattdessen:
# - contexts/ragintegration/infrastructure/models.py
#   * IndexedDocumentModel (statt RAGIndexedDocument)
#   * DocumentChunkModel (statt RAGDocumentChunk)
#   * ChatSessionModel (statt RAGChatSession)
#   * ChatMessageModel (statt RAGChatMessage)
#
# Der Fehler "no such column: last_activity" entstand durch doppelte Model-Definitionen
# in app.models.Base und Property-Konflikte


# ==================== DOCUMENT AI RESPONSES ====================

class DocumentAIResponse(Base):
    """
    AI-Verarbeitungs-Ergebnis für eine Dokumentseite.
    
    Context: documentupload (Phase 2.7: AI-Verarbeitung)
    
    Features:
    - 1:1 Beziehung zu UploadDocumentPage
    - Speichert strukturierte JSON-Response vom AI-Modell
    - Verknüpft mit verwendetem Prompt-Template
    - Tracking: Tokens, Response Time, Model-Info
    
    Workflow:
    1. Upload-Dokument wird hochgeladen (UploadDocument)
    2. Seiten werden generiert (UploadDocumentPage)
    3. Pro Seite: AI-Verarbeitung → DocumentAIResponse
    
    Relationships:
    - upload_document: Many-to-One zu UploadDocument
    - upload_document_page: One-to-One zu UploadDocumentPage
    - prompt_template: Many-to-One zu PromptTemplate
    """
    __tablename__ = "document_ai_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_document_id = Column(Integer, ForeignKey("upload_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    upload_document_page_id = Column(Integer, ForeignKey("upload_document_pages.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=False, index=True)
    
    # AI Model Info
    ai_model_id = Column(String(100), nullable=False, comment="AI Model ID (z.B. 'gpt-4o-mini', 'gemini-2.5-flash')")
    model_name = Column(String(100), nullable=False, comment="z.B. 'gpt-4o-mini', 'gemini-2.0-flash-exp'")
    
    # AI Response Data
    json_response = Column(Text, nullable=False, comment="Strukturierte JSON-Antwort vom AI-Modell")
    processing_status = Column(String(20), nullable=False, default="completed", comment="completed, failed, partial")
    
    # Token Tracking
    tokens_sent = Column(Integer, nullable=True)
    tokens_received = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    
    # Performance Tracking
    response_time_ms = Column(Integer, nullable=True, comment="Response Zeit in Millisekunden")
    
    # Error Handling
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    upload_document = relationship("UploadDocument", foreign_keys=[upload_document_id])
    upload_document_page = relationship("UploadDocumentPage", foreign_keys=[upload_document_page_id], uselist=False)
    # prompt_template = relationship("PromptTemplateModel", foreign_keys=[prompt_template_id])  # Optional, nicht critical
    # ai_model = relationship("AIModel", foreign_keys=[ai_model_id])  # Model existiert nicht
    
    def __repr__(self):
        return f"<DocumentAIResponse(id={self.id}, page_id={self.upload_document_page_id}, status='{self.processing_status}')>"
