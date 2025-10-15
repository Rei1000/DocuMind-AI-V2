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
    workflow_document = relationship("WorkflowDocument", back_populates="upload_document", uselist=False)
    
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


class WorkflowDocument(Base):
    """
    Dokument im Workflow-Prozess (Review → Approval).
    
    Context: documentworkflow
    
    Features:
    - Status-Workflow: uploaded → reviewed → approved/rejected
    - Permission-basierte Actions (Level 2/3/4)
    - Kommentar-System
    - Vollständiger Audit-Trail
    
    Relationships:
    - upload_document: One-to-One zu UploadDocument
    - audit_logs: One-to-Many zu WorkflowAuditLog
    - indexed_document: One-to-One zu RAGIndexedDocument
    """
    __tablename__ = "workflow_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_document_id = Column(Integer, ForeignKey("upload_documents.id"), unique=True, nullable=False)
    status = Column(String(20), default="uploaded", nullable=False, comment="uploaded, reviewed, approved, rejected")
    current_reviewer_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_comment = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_comment = Column(Text, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejected_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    upload_document = relationship("UploadDocument", back_populates="workflow_document")
    current_reviewer = relationship("User", foreign_keys=[current_reviewer_user_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    rejected_by = relationship("User", foreign_keys=[rejected_by_user_id])
    audit_logs = relationship("WorkflowAuditLog", back_populates="workflow_document", cascade="all, delete-orphan")
    indexed_document = relationship("RAGIndexedDocument", back_populates="workflow_document", uselist=False)
    
    def __repr__(self):
        return f"<WorkflowDocument(id={self.id}, status='{self.status}')>"


class WorkflowAuditLog(Base):
    """
    Audit-Trail Entry für TÜV-Compliance.
    
    Context: documentworkflow
    
    Features:
    - Vollständige Nachverfolgbarkeit aller Aktionen
    - IP-Adresse + User-Agent für Forensik
    - Status-Transitions
    
    Relationships:
    - workflow_document: Many-to-One zu WorkflowDocument
    - performed_by: Many-to-One zu User
    """
    __tablename__ = "workflow_audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_document_id = Column(Integer, ForeignKey("workflow_documents.id"), nullable=False)
    action = Column(String(50), nullable=False, comment="uploaded, reviewed, approved, rejected, comment_added")
    performed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    previous_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=True)
    comment = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True, comment="IPv4 oder IPv6")
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    workflow_document = relationship("WorkflowDocument", back_populates="audit_logs")
    performed_by = relationship("User", foreign_keys=[performed_by_user_id])
    
    def __repr__(self):
        return f"<WorkflowAuditLog(id={self.id}, action='{self.action}', user_id={self.performed_by_user_id})>"


class RAGIndexedDocument(Base):
    """
    Im RAG-System indexiertes Dokument.
    
    Context: ragintegration
    
    Features:
    - Nur freigegebene Dokumente (status=approved)
    - Qdrant Vector Store
    - Chunking mit Metadaten
    
    Relationships:
    - workflow_document: One-to-One zu WorkflowDocument
    - chunks: One-to-Many zu RAGDocumentChunk
    """
    __tablename__ = "rag_indexed_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_document_id = Column(Integer, ForeignKey("workflow_documents.id"), unique=True, nullable=False)
    qdrant_collection_name = Column(String(100), nullable=False, comment="Name der Qdrant Collection")
    total_chunks = Column(Integer, nullable=False, comment="Anzahl Chunks")
    indexed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    embedding_model = Column(String(100), nullable=False, comment="z.B. text-embedding-3-small")
    
    # Relationships
    workflow_document = relationship("WorkflowDocument", back_populates="indexed_document")
    chunks = relationship("RAGDocumentChunk", back_populates="indexed_document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<RAGIndexedDocument(id={self.id}, chunks={self.total_chunks})>"


class RAGDocumentChunk(Base):
    """
    Einzelner Chunk eines Dokuments (TÜV-Audit-tauglich).
    
    Context: ragintegration
    
    Features:
    - Absatz-basiertes Chunking mit Satz-Überlappung
    - Präzise Metadaten (Seite, Absatz, Chunk-ID)
    - Qdrant Point ID für Vector Store
    
    Relationships:
    - indexed_document: Many-to-One zu RAGIndexedDocument
    """
    __tablename__ = "rag_document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    rag_indexed_document_id = Column(Integer, ForeignKey("rag_indexed_documents.id"), nullable=False)
    chunk_id = Column(String(100), unique=True, nullable=False, comment="z.B. 123_p1_c0")
    chunk_text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=False)
    paragraph_index = Column(Integer, nullable=True)
    chunk_index = Column(Integer, nullable=False)
    token_count = Column(Integer, nullable=True)
    sentence_count = Column(Integer, nullable=True)
    has_overlap = Column(Boolean, default=False, nullable=False)
    overlap_sentence_count = Column(Integer, default=0, nullable=False)
    qdrant_point_id = Column(String(100), nullable=True, comment="UUID in Qdrant")
    embedding_vector_preview = Column(Text, nullable=True, comment="Erste 10 Dimensionen (Debug)")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    indexed_document = relationship("RAGIndexedDocument", back_populates="chunks")
    
    def __repr__(self):
        return f"<RAGDocumentChunk(id={self.id}, chunk_id='{self.chunk_id}', page={self.page_number})>"


class RAGChatSession(Base):
    """
    Chat-Session eines Users.
    
    Context: ragintegration
    
    Features:
    - Persistent, pro User
    - Session-Name
    - Active/Inactive Status
    
    Relationships:
    - user: Many-to-One zu User
    - messages: One-to-Many zu RAGChatMessage
    """
    __tablename__ = "rag_chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_name = Column(String(255), nullable=True, comment="Optional: User-definierter Name")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    messages = relationship("RAGChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<RAGChatSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class RAGChatMessage(Base):
    """
    Einzelne Chat-Nachricht.
    
    Context: ragintegration
    
    Features:
    - User oder Assistant Rolle
    - Source-Chunks (JSON Array)
    
    Relationships:
    - session: Many-to-One zu RAGChatSession
    """
    __tablename__ = "rag_chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("rag_chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False, comment="user oder assistant")
    content = Column(Text, nullable=False)
    source_chunks = Column(Text, nullable=True, comment="JSON Array von chunk_ids")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    session = relationship("RAGChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<RAGChatMessage(id={self.id}, role='{self.role}', session_id={self.session_id})>"


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
    ai_model_id = Column(Integer, ForeignKey("ai_models.id"), nullable=False)
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
