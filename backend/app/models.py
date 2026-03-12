"""
📊 DocuMind-AI V2 Data Models (SQLAlchemy ORM)

Minimales DDD-orientiertes Datenmodell fokussiert auf:
- User Management (RBAC)
- Interest Groups (13 Stakeholder-System)
- User Group Memberships (Many-to-Many)
- Document Types (QMS Document Classification)

Version: 2.9.4 (Clean DDD Architecture)
Stand: 2025-12-28
NEU v2.9.1: Chunk-Level Feedback (rag_chunk_feedback) für präziseres RAG-Feedback
NEU v2.9.0: Search Quality Metrics (search_quality_metrics) für Trend-Analyse
NEU v2.7.3: Custom RAG Chat Prompts (CR-P2.2) - strikte Custom-Prompt-Enforcement
NEU v2.7.0: SQLite-Persistenz für ML/SHAP (training_samples, shap_background_data, shap_cache)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
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
    
    # Relationship bewusst nicht definiert (DDD: kein Cross-Context Coupling)
    # Zugriff auf Prompt-Templates erfolgt über Repositories/Use Cases.
    
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
    
    # NEU: File Hash & Duplikat-Erkennung (Document Lifecycle Phase 1.1)
    file_hash = Column(String(64), unique=True, index=True, nullable=True, comment="SHA-256 Hash (64 hex Zeichen) für Duplikat-Prüfung")
    is_duplicate = Column(Boolean, default=False, nullable=False, index=True, comment="Flag: Ist dieses Dokument ein Duplikat?")
    duplicate_of_document_id = Column(Integer, ForeignKey("upload_documents.id"), nullable=True, index=True, comment="Link zum Original-Dokument (wenn Duplikat)")
    
    # NEU Phase 2 - Versionierung (Document Lifecycle Phase 2)
    document_series_id = Column(Integer, ForeignKey("upload_documents.id"), nullable=True, index=True, comment="ID der logischen Dokument-Serie (self-reference zur ersten Version)")
    parent_document_id = Column(Integer, ForeignKey("upload_documents.id"), nullable=True, index=True, comment="Vorgänger-Version (bei neuen Versionen)")
    is_current_version = Column(Boolean, default=True, nullable=False, index=True, comment="Aktuelle Version? (True bei Upload, False bei Archivierung)")
    
    # NEU Phase 1.3 - Soft Delete (Document Lifecycle Phase 1.3)
    deleted_at = Column(DateTime, nullable=True, index=True, comment="Zeitstempel der Löschung (Soft Delete)")
    deleted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True, comment="User ID des Löschers")
    deletion_reason = Column(Text, nullable=True, comment="Grund für Löschung")
    # NEU Phase 1.4 - Archivierung (Document Lifecycle Phase 1.4)
    archived_at = Column(DateTime, nullable=True, index=True, comment="Zeitstempel der Archivierung")
    archived_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True, comment="User ID des Archivierers")
    archive_reason = Column(Text, nullable=True, comment="Grund für Archivierung")
    
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
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
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


# ============================================================================
# RAG AUDIT-TRAIL MODELS (PHASE 1.3)
# ============================================================================

class RAGAuditLogModel(Base):
    """
    RAG Audit Log Model für vollständige Transparenz und Compliance.
    
    Protokolliert alle RAG-Operationen (Chunking, Indexing, Queries) für:
    - Compliance und Audit-Trail
    - Performance-Monitoring
    - Fehler-Tracking
    - ML-Analytics
    
    Features:
    - JSON-Details für flexible Metadaten
    - Kosten-Tracking (tokens_used, cost_usd)
    - Performance-Metriken (duration_ms)
    - Fehler-Logging (error_message bei status='failed')
    
    Relationships:
    - indexed_document: Optional FK (NULL bei Chat-Queries)
    - user: FK zu User der die Aktion ausführte
    """
    __tablename__ = "rag_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    indexed_document_id = Column(Integer, nullable=True, index=True, comment="FK zu indexed_documents (NULL bei Chat-Queries)")
    action = Column(String(50), nullable=False, index=True, comment="Action-Type (z.B. 'chunking_started', 'query_executed')")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="User der die Aktion ausführte")
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True, comment="Zeitstempel der Aktion")
    
    # JSON Details
    details = Column(Text, nullable=False, comment="JSON-String mit allen Parametern")
    
    # Status
    status = Column(String(20), nullable=False, index=True, comment="Status: 'success', 'failed', 'in_progress'")
    error_message = Column(Text, nullable=True, comment="Fehler-Message (nur bei failed)")
    
    # Metadata für ML/Analytics
    duration_ms = Column(Integer, nullable=True, comment="Dauer der Operation in Millisekunden")
    tokens_used = Column(Integer, nullable=True, comment="Anzahl verwendeter Tokens (bei AI-Calls)")
    cost_usd = Column(Integer, nullable=True, comment="Geschätzte Kosten in USD (Cents)")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    # indexed_document = relationship("IndexedDocument", foreign_keys=[indexed_document_id])  # Optional
    
    def __repr__(self):
        return f"<RAGAuditLog(id={self.id}, action='{self.action}', status='{self.status}')>"


# ============================================================================
# RAG FEEDBACK MODEL (PHASE 4.1)
# ============================================================================

class RAGFeedbackModel(Base):
    """
    RAG Feedback Model für User Feedback zu RAG Chat-Antworten.
    
    Ermöglicht es Usern, Feedback zu RAG-Antworten zu geben für:
    - Qualitätsverbesserung
    - ML-Training
    - Analytics
    
    Relationships:
    - chat_message: FK zu ChatMessage (Assistant-Message)
    - user: FK zu User der das Feedback gegeben hat
    """
    __tablename__ = "rag_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_message_id = Column(Integer, ForeignKey("rag_chat_messages.id"), nullable=False, index=True, comment="FK zu ChatMessage (Assistant-Message)")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="User der das Feedback gegeben hat")
    rating = Column(String(20), nullable=False, index=True, comment="Bewertung: 'positive', 'negative', 'neutral'")
    comment = Column(Text, nullable=True, comment="Optionaler Kommentar (max 2000 Zeichen)")
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True, comment="Zeitstempel der Abgabe")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    # chat_message = relationship("ChatMessage", foreign_keys=[chat_message_id])  # Optional


class ChunkFeedbackModel(Base):
    """
    Chunk Feedback Model für User Feedback zu einzelnen Chunks in RAG Chat-Antworten.
    
    Ermöglicht es Usern, Feedback zu einzelnen Chunks zu geben für:
    - Präzise Qualitätsverbesserung (welche Chunks sind relevant/nicht relevant)
    - ML-Training (Chunk-Level Relevanz-Scores)
    - Analytics (Chunk-Level Metriken)
    
    Relationships:
    - chat_message: FK zu ChatMessage (Assistant-Message, für Kontext)
    - document: FK zu Document (für Kontext)
    - user: FK zu User der das Feedback gegeben hat
    """
    __tablename__ = "rag_chunk_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String(255), nullable=False, index=True, comment="Chunk-ID (z.B. 'doc_123_meta_abc123')")
    chat_message_id = Column(Integer, ForeignKey("rag_chat_messages.id"), nullable=False, index=True, comment="FK zu ChatMessage (für Kontext)")
    document_id = Column(Integer, ForeignKey("upload_documents.id"), nullable=False, index=True, comment="Dokument-ID (für Kontext)")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="User der das Feedback gegeben hat")
    rating = Column(String(20), nullable=False, index=True, comment="Bewertung: 'positive', 'negative', 'neutral'")
    comment = Column(Text, nullable=True, comment="Optionaler Kommentar (max 2000 Zeichen)")
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True, comment="Zeitstempel der Abgabe")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    # chat_message = relationship("ChatMessage", foreign_keys=[chat_message_id])  # Optional
    # document = relationship("Document", foreign_keys=[document_id])  # Optional
    
    def __repr__(self):
        return f"<RAGFeedback(id={self.id}, message_id={self.chat_message_id}, rating='{self.rating}')>"


# ============================================================================
# RAG CHAT PROMPT MODELS (PHASE 1)
# ============================================================================

class RAGChatPromptModel(Base):
    """
    RAG Chat Prompt Modell für globale, dokumenttyp-spezifische Prompts.
    
    Level 4+ User können diese Prompts anpassen.
    Ein Prompt pro Dokumenttyp (UNIQUE constraint).
    
    Features:
    - Global gespeichert (für alle User)
    - Audit-Trail (created_by_user_id, created_at, updated_at)
    - Multi-Query Prompt Support (PHASE 2)
    
    Relationships:
    - document_type: Many-to-One zu DocumentType
    - created_by_user: Many-to-One zu User
    """
    __tablename__ = "rag_chat_prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    document_type_id = Column(Integer, ForeignKey("document_types.id"), nullable=True, unique=True, index=True, comment="FK zu DocumentType (UNIQUE - ein Prompt pro Dokumenttyp, NULL = Default-Prompt)")
    prompt_text = Column(Text, nullable=False, comment="RAG Chat Prompt-Text für diesen Dokumenttyp")
    multi_query_prompt_text = Column(Text, nullable=True, comment="Multi-Query Prompt-Text (optional, PHASE 2)")
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="User ID des Erstellers (Audit-Trail)")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Zeitstempel der Erstellung")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="Zeitstempel der letzten Aktualisierung")
    
    # Relationships
    # document_type = relationship("DocumentTypeModel", foreign_keys=[document_type_id])
    # created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    
    def __repr__(self):
        return f"<RAGChatPrompt(id={self.id}, document_type_id={self.document_type_id})>"

# ============================================================================
# TRAINING DATA MODEL (PHASE 2: SHAP Training Data Collection)
# ============================================================================

class TrainingDataModel(Base):
    """
    Training Data Model für ML-Model Training.
    
    Sammelt SHAP-Erklärungen + User-Feedback für Learning-to-Rank Model.
    """
    __tablename__ = "rag_training_data"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False, comment="Die ursprüngliche Query")
    chunk_id = Column(String(255), nullable=False, index=True, comment="Chunk-ID")
    document_id = Column(Integer, nullable=False, index=True, comment="Dokument-ID")
    session_id = Column(Integer, nullable=False, index=True, comment="Chat-Session-ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="User-ID")
    vector_score = Column(String(20), nullable=False, comment="Vektor-Ähnlichkeits-Score (0-1)")
    text_score = Column(String(20), nullable=False, comment="Text-Matching-Score (0-1)")
    hybrid_score = Column(String(20), nullable=False, comment="Kombinierter Score (0-1)")
    document_type = Column(String(100), nullable=False, index=True, comment="Dokumenttyp")
    user_level = Column(Integer, nullable=False, comment="User-Level (1-5)")
    keyword_matches = Column(Integer, nullable=False, comment="Anzahl der Keyword-Matches")
    chunk_length = Column(Integer, nullable=False, comment="Chunk-Länge in Zeichen")
    heading_hierarchy_depth = Column(Integer, nullable=False, comment="Tiefe der Heading-Hierarchie")
    confidence_score = Column(String(20), nullable=False, comment="Confidence-Score (0-1)")
    shap_explanation = Column(Text, nullable=True, comment="SHAP-Erklärung (JSON)")
    user_feedback = Column(String(20), nullable=True, index=True, comment="User-Feedback ('positive', 'negative', 'neutral', NULL)")
    feedback_comment = Column(Text, nullable=True, comment="Optionaler Feedback-Kommentar")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True, comment="Zeitstempel der Erstellung")
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<TrainingData(id={self.id}, query='{self.query[:50]}...', chunk_id='{self.chunk_id}')>"


# ============================================================================
# ML/SHAP SQLITE-PERSISTENZ MODELS (v2.7.0)
# ============================================================================

class TrainingSampleModel(Base):
    """
    Training Sample Model für ML-Training-Daten.
    
    Einfacheres Format als TrainingDataModel, speziell für FileBasedTrainingDataRepository
    Migration zu SQLite. Speichert Training-Samples für Learning-to-Rank Modelle.
    
    Features:
    - JSON-Serialisierung für Features (flexibel)
    - Optional user_id/feedback_id für Tracking
    - Source-Tracking (feedback, system, auto)
    """
    __tablename__ = "training_samples"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False, index=True, comment="Die ursprüngliche Query")
    chunk_id = Column(Text, nullable=False, comment="Chunk-ID")
    features_json = Column(Text, nullable=False, comment="Features als JSON-String")
    relevance_score = Column(Float, nullable=False, comment="Relevance-Score (0.0-1.0)")
    source = Column(Text, nullable=False, comment="Quelle: 'feedback', 'system', 'auto'")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="Optional: User der das Feedback gab")
    feedback_id = Column(Integer, nullable=True, comment="Optional: Reference zu Feedback")
    created_at = Column(Text, nullable=False, index=True, comment="ISO-8601 Timestamp")
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    @property
    def features(self):
        """Deserialisiere features_json zu dict."""
        import json
        return json.loads(self.features_json)
    
    def __repr__(self):
        return f"<TrainingSample(id={self.id}, query='{self.query[:30]}...', relevance={self.relevance_score})>"


class SHAPBackgroundDataModel(Base):
    """
    SHAP Background Data Model für historische Search-Daten.
    
    Speichert historische Search-Records für echte SHAP-Background-Data.
    Verbessert SHAP-Qualität deutlich gegenüber zufälligen Daten.
    
    Features:
    - Rolling Window Support (max 1000 Records)
    - Automatisches Sammeln von Search-Daten
    - Feature-Extraktion für SHAP
    """
    __tablename__ = "shap_background_data"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False, comment="Search-Query")
    vector_score = Column(Float, nullable=True, comment="Vektor-Score (0-1)")
    text_score = Column(Float, nullable=True, comment="Text-Score (0-1)")
    user_level = Column(Integer, nullable=True, comment="User-Level (1-5)")
    keyword_matches = Column(Integer, nullable=True, comment="Anzahl Keyword-Matches")
    chunk_length = Column(Integer, nullable=True, comment="Chunk-Länge")
    heading_hierarchy_depth = Column(Integer, nullable=True, comment="Heading-Hierarchie-Tiefe")
    confidence_score = Column(Float, nullable=True, comment="Confidence-Score (0-1)")
    created_at = Column(Text, nullable=False, index=True, comment="ISO-8601 Timestamp")
    
    def __repr__(self):
        return f"<SHAPBackgroundData(id={self.id}, query='{self.query[:30]}...')>"


class SHAPCacheEntryModel(Base):
    """
    SHAP Cache Entry Model für gecachte SHAP-Erklärungen.
    
    Speichert SHAP-Explanations mit TTL (Time-To-Live) für Performance-Optimierung.
    LRU Cache mit TTL: 1 Stunde.
    
    Features:
    - UNIQUE cache_key (verhindert Duplikate)
    - JSON-Serialisierung für SHAP-Values
    - TTL-Support (expires_at)
    """
    __tablename__ = "shap_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(Text, unique=True, nullable=False, index=True, comment="Eindeutiger Cache-Key")
    shap_values_json = Column(Text, nullable=False, comment="SHAP-Explanation als JSON-String")
    created_at = Column(Text, nullable=False, comment="ISO-8601 Timestamp")
    expires_at = Column(Text, nullable=False, index=True, comment="ISO-8601 Expiry-Timestamp")
    
    @property
    def shap_values(self):
        """Deserialisiere shap_values_json zu dict."""
        import json
        return json.loads(self.shap_values_json)
    
    def __repr__(self):
        return f"<SHAPCacheEntry(id={self.id}, key='{self.cache_key[:30]}...')>"


# ============================================================================
# SEARCH QUALITY METRICS MODEL (v2.9.0)
# ============================================================================

class SearchQualityMetricsModel(Base):
    """
    Search Quality Metrics Model für Tracking von Suchergebnis-Qualität.
    
    Speichert Metriken für jede Query, um Trend-Analyse und kontinuierliche Verbesserung zu ermöglichen.
    
    Features:
    - Precision@k, Recall@k, NDCG@k, MRR für jede Query
    - Hybrid vs ML Ranking Vergleich
    - Metadaten (Session, User, Document Type)
    - Timestamp für Trend-Analyse
    """
    __tablename__ = "search_quality_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False, index=True, comment="Die ursprüngliche Query")
    session_id = Column(Integer, nullable=True, index=True, comment="Chat-Session-ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True, comment="User-ID")
    document_type = Column(String(100), nullable=True, index=True, comment="Document Type")
    
    # Precision & Recall
    precision_at_1 = Column(Float, nullable=False, comment="Precision@1")
    precision_at_3 = Column(Float, nullable=False, comment="Precision@3")
    precision_at_5 = Column(Float, nullable=False, comment="Precision@5")
    precision_at_10 = Column(Float, nullable=False, comment="Precision@10")
    
    recall_at_1 = Column(Float, nullable=False, comment="Recall@1")
    recall_at_3 = Column(Float, nullable=False, comment="Recall@3")
    recall_at_5 = Column(Float, nullable=False, comment="Recall@5")
    recall_at_10 = Column(Float, nullable=False, comment="Recall@10")
    
    # Ranking Metriken
    ndcg_at_1 = Column(Float, nullable=False, comment="NDCG@1")
    ndcg_at_3 = Column(Float, nullable=False, comment="NDCG@3")
    ndcg_at_5 = Column(Float, nullable=False, comment="NDCG@5")
    ndcg_at_10 = Column(Float, nullable=False, comment="NDCG@10")
    
    mrr = Column(Float, nullable=False, comment="Mean Reciprocal Rank")
    
    # Zusätzliche Metriken
    average_relevance_score = Column(Float, nullable=False, comment="Durchschnittlicher Relevance-Score")
    num_relevant_results = Column(Integer, nullable=False, comment="Anzahl relevanter Ergebnisse")
    num_total_results = Column(Integer, nullable=False, comment="Gesamtanzahl Ergebnisse")
    
    # Ranking-Vergleich (Hybrid vs ML)
    hybrid_ndcg_at_10 = Column(Float, nullable=True, comment="NDCG@10 für Hybrid-Ranking")
    ml_ndcg_at_10 = Column(Float, nullable=True, comment="NDCG@10 für ML-Ranking")
    
    # Timestamp
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True, comment="Zeitstempel")
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<SearchQualityMetrics(id={self.id}, query='{self.query[:30]}...', ndcg@10={self.ndcg_at_10:.3f})>"
