-- =====================================================
-- DocuMind-AI V2 - Komplettes Datenbank-Initialisierungs-Script
-- =====================================================
-- Version: 2.1.0
-- Stand: 2025-10-28
-- Datenbank: SQLite
-- Pfad: /Users/reiner/Documents/DocuMind-AI-V2/data/qms.db
-- =====================================================

-- WICHTIG: Dieses Script erstellt die komplette Datenbank von Grund auf
-- Es ersetzt alle Migration-Scripts und ist die Single Source of Truth

-- =====================================================
-- 1. CORE SYSTEM TABLES (5 Tabellen)
-- =====================================================

-- 1.1 Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    employee_id VARCHAR(50) UNIQUE,
    organizational_unit VARCHAR(100),
    hashed_password VARCHAR(255),
    individual_permissions TEXT,
    is_qms_admin BOOLEAN NOT NULL DEFAULT FALSE,
    cannot_be_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 1.2 Interest Groups Table
CREATE TABLE IF NOT EXISTS interest_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    group_permissions TEXT,
    ai_functionality TEXT,
    typical_tasks TEXT,
    is_external BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER,
    FOREIGN KEY (created_by_id) REFERENCES users(id)
);

-- 1.3 User Group Memberships Table
CREATE TABLE IF NOT EXISTS user_group_memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    interest_group_id INTEGER NOT NULL,
    role_in_group VARCHAR(50),
    approval_level INTEGER NOT NULL DEFAULT 1,
    is_department_head BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assigned_by_id INTEGER,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (interest_group_id) REFERENCES interest_groups(id),
    FOREIGN KEY (assigned_by_id) REFERENCES users(id)
);

-- 1.4 Document Types Table
CREATE TABLE IF NOT EXISTS document_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    allowed_file_types TEXT NOT NULL,
    max_file_size_mb INTEGER NOT NULL,
    requires_ocr BOOLEAN NOT NULL DEFAULT FALSE,
    requires_vision BOOLEAN NOT NULL DEFAULT FALSE,
    default_prompt_template_id INTEGER,
    created_by INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- 1.5 Prompt Templates Table
CREATE TABLE IF NOT EXISTS prompt_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    prompt_text TEXT NOT NULL,
    system_instructions TEXT,
    document_type_id INTEGER,
    ai_model VARCHAR(100) NOT NULL,
    temperature INTEGER NOT NULL,
    max_tokens INTEGER NOT NULL,
    top_p INTEGER NOT NULL,
    detail_level VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    version VARCHAR(20) NOT NULL,
    tested_successfully BOOLEAN NOT NULL DEFAULT FALSE,
    success_count INTEGER NOT NULL DEFAULT 0,
    last_used_at DATETIME,
    created_by INTEGER,
    tags TEXT,
    example_input TEXT,
    example_output TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_type_id) REFERENCES document_types(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- =====================================================
-- 2. DOCUMENT UPLOAD SYSTEM TABLES (6 Tabellen)
-- =====================================================

-- 2.1 Upload Documents Table
CREATE TABLE IF NOT EXISTS upload_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    document_type_id INTEGER NOT NULL,
    qm_chapter VARCHAR(50),
    version VARCHAR(20) NOT NULL,
    page_count INTEGER,
    uploaded_by_user_id INTEGER NOT NULL,
    uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    file_path VARCHAR(500) NOT NULL,
    processing_method VARCHAR(20) NOT NULL,
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    workflow_status VARCHAR(20) NOT NULL DEFAULT 'draft',
    FOREIGN KEY (document_type_id) REFERENCES document_types(id),
    FOREIGN KEY (uploaded_by_user_id) REFERENCES users(id)
);

-- 2.2 Upload Document Pages Table
CREATE TABLE IF NOT EXISTS upload_document_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_document_id INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    preview_image_path VARCHAR(500) NOT NULL,
    thumbnail_path VARCHAR(500),
    width INTEGER,
    height INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_document_id) REFERENCES upload_documents(id)
);

-- 2.3 Upload Document Interest Groups Table
CREATE TABLE IF NOT EXISTS upload_document_interest_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_document_id INTEGER NOT NULL,
    interest_group_id INTEGER NOT NULL,
    assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assigned_by_user_id INTEGER NOT NULL,
    FOREIGN KEY (upload_document_id) REFERENCES upload_documents(id),
    FOREIGN KEY (interest_group_id) REFERENCES interest_groups(id),
    FOREIGN KEY (assigned_by_user_id) REFERENCES users(id)
);

-- 2.4 Document Status Changes Table
CREATE TABLE IF NOT EXISTS document_status_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_document_id INTEGER NOT NULL,
    from_status VARCHAR(20),
    to_status VARCHAR(20) NOT NULL,
    changed_by_user_id INTEGER NOT NULL,
    changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    change_reason TEXT NOT NULL,
    comment TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_document_id) REFERENCES upload_documents(id),
    FOREIGN KEY (changed_by_user_id) REFERENCES users(id)
);

-- 2.5 Document Comments Table
CREATE TABLE IF NOT EXISTS document_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_document_id INTEGER NOT NULL,
    comment_text TEXT NOT NULL,
    comment_type VARCHAR(20) NOT NULL,
    page_number INTEGER,
    created_by_user_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status_change_id INTEGER,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_document_id) REFERENCES upload_documents(id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id),
    FOREIGN KEY (status_change_id) REFERENCES document_status_changes(id)
);

-- 2.6 Document AI Responses Table
CREATE TABLE IF NOT EXISTS document_ai_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_document_id INTEGER NOT NULL,
    upload_document_page_id INTEGER NOT NULL,
    prompt_template_id INTEGER NOT NULL,
    ai_model_id VARCHAR(100) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    json_response TEXT NOT NULL,
    processing_status VARCHAR(20) NOT NULL,
    tokens_sent INTEGER,
    tokens_received INTEGER,
    total_tokens INTEGER,
    response_time_ms INTEGER,
    error_message TEXT,
    processed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_document_id) REFERENCES upload_documents(id),
    FOREIGN KEY (upload_document_page_id) REFERENCES upload_document_pages(id),
    FOREIGN KEY (prompt_template_id) REFERENCES prompt_templates(id)
);

-- =====================================================
-- 3. RAG SYSTEM TABLES (4 Tabellen)
-- =====================================================

-- 3.1 RAG Indexed Documents Table
CREATE TABLE IF NOT EXISTS rag_indexed_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_document_id INTEGER NOT NULL UNIQUE,
    qdrant_collection_name VARCHAR(100) NOT NULL,
    total_chunks INTEGER NOT NULL DEFAULT 0,
    indexed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    embedding_model VARCHAR(100) NOT NULL,
    FOREIGN KEY (upload_document_id) REFERENCES upload_documents(id)
);

-- 3.2 RAG Document Chunks Table
CREATE TABLE IF NOT EXISTS rag_document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rag_indexed_document_id INTEGER NOT NULL,
    chunk_id VARCHAR(100) UNIQUE NOT NULL,
    chunk_text TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    paragraph_index INTEGER,
    chunk_index INTEGER NOT NULL,
    token_count INTEGER,
    sentence_count INTEGER,
    has_overlap BOOLEAN NOT NULL DEFAULT FALSE,
    overlap_sentence_count INTEGER NOT NULL DEFAULT 0,
    qdrant_point_id VARCHAR(100),
    embedding_vector_preview TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rag_indexed_document_id) REFERENCES rag_indexed_documents(id)
);

-- 3.3 RAG Chat Sessions Table
CREATE TABLE IF NOT EXISTS rag_chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_name VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_message_at DATETIME,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 3.4 RAG Chat Messages Table
CREATE TABLE IF NOT EXISTS rag_chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    source_chunks TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES rag_chat_sessions(id)
);

-- =====================================================
-- 4. INDIZES FÜR PERFORMANCE
-- =====================================================

-- Core System Indizes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_employee_id ON users(employee_id);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

CREATE INDEX IF NOT EXISTS idx_interest_groups_name ON interest_groups(name);
CREATE INDEX IF NOT EXISTS idx_interest_groups_code ON interest_groups(code);
CREATE INDEX IF NOT EXISTS idx_interest_groups_is_active ON interest_groups(is_active);

CREATE INDEX IF NOT EXISTS idx_user_group_memberships_user_id ON user_group_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_user_group_memberships_group_id ON user_group_memberships(interest_group_id);
CREATE INDEX IF NOT EXISTS idx_user_group_memberships_approval_level ON user_group_memberships(approval_level);

CREATE INDEX IF NOT EXISTS idx_document_types_code ON document_types(code);
CREATE INDEX IF NOT EXISTS idx_document_types_is_active ON document_types(is_active);

CREATE INDEX IF NOT EXISTS idx_prompt_templates_name ON prompt_templates(name);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_status ON prompt_templates(status);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_document_type ON prompt_templates(document_type_id);

-- Document Upload System Indizes
CREATE INDEX IF NOT EXISTS idx_upload_documents_type ON upload_documents(document_type_id);
CREATE INDEX IF NOT EXISTS idx_upload_documents_uploader ON upload_documents(uploaded_by_user_id);
CREATE INDEX IF NOT EXISTS idx_upload_documents_status ON upload_documents(workflow_status);
CREATE INDEX IF NOT EXISTS idx_upload_documents_processing ON upload_documents(processing_status);

CREATE INDEX IF NOT EXISTS idx_upload_document_pages_document ON upload_document_pages(upload_document_id);
CREATE INDEX IF NOT EXISTS idx_upload_document_pages_number ON upload_document_pages(page_number);

CREATE INDEX IF NOT EXISTS idx_upload_document_interest_groups_document ON upload_document_interest_groups(upload_document_id);
CREATE INDEX IF NOT EXISTS idx_upload_document_interest_groups_group ON upload_document_interest_groups(interest_group_id);

CREATE INDEX IF NOT EXISTS idx_document_status_changes_document ON document_status_changes(upload_document_id);
CREATE INDEX IF NOT EXISTS idx_document_status_changes_changed_by ON document_status_changes(changed_by_user_id);
CREATE INDEX IF NOT EXISTS idx_document_status_changes_changed_at ON document_status_changes(changed_at);

CREATE INDEX IF NOT EXISTS idx_document_comments_document ON document_comments(upload_document_id);
CREATE INDEX IF NOT EXISTS idx_document_comments_created_by ON document_comments(created_by_user_id);

CREATE INDEX IF NOT EXISTS idx_document_ai_responses_document ON document_ai_responses(upload_document_id);
CREATE INDEX IF NOT EXISTS idx_document_ai_responses_page ON document_ai_responses(upload_document_page_id);
CREATE INDEX IF NOT EXISTS idx_document_ai_responses_template ON document_ai_responses(prompt_template_id);

-- RAG System Indizes
CREATE INDEX IF NOT EXISTS idx_rag_indexed_documents_upload_id ON rag_indexed_documents(upload_document_id);
CREATE INDEX IF NOT EXISTS idx_rag_indexed_documents_collection ON rag_indexed_documents(qdrant_collection_name);
CREATE INDEX IF NOT EXISTS idx_rag_indexed_documents_indexed_at ON rag_indexed_documents(indexed_at);

CREATE INDEX IF NOT EXISTS idx_rag_document_chunks_document ON rag_document_chunks(rag_indexed_document_id);
CREATE INDEX IF NOT EXISTS idx_rag_document_chunks_chunk_id ON rag_document_chunks(chunk_id);
CREATE INDEX IF NOT EXISTS idx_rag_document_chunks_page ON rag_document_chunks(page_number);

CREATE INDEX IF NOT EXISTS idx_rag_chat_sessions_user ON rag_chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_rag_chat_sessions_active ON rag_chat_sessions(is_active);

CREATE INDEX IF NOT EXISTS idx_rag_chat_messages_session ON rag_chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_rag_chat_messages_created_at ON rag_chat_messages(created_at);

-- =====================================================
-- 5. SEED DATA - STANDARD-DATEN
-- =====================================================

-- 5.1 Standard Interest Groups (13 Stakeholder Groups)
INSERT OR IGNORE INTO interest_groups (id, name, code, description, group_permissions, ai_functionality, typical_tasks, is_external, is_active, created_at, updated_at) VALUES
(1, 'Geschäftsführung', 'geschaeftsfuehrung', 'Geschäftsführung und Unternehmensleitung', '["read_all", "approve_all", "system_admin"]', '["ai_playground", "rag_chat", "document_management"]', '["strategische_planung", "entscheidungen", "freigaben"]', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2, 'Qualitätsmanagement', 'qm', 'Qualitätsmanagement und QM-System', '["read_all", "approve_documents", "manage_workflow"]', '["ai_playground", "rag_chat", "document_management", "prompt_management"]', '["dokumentenfreigabe", "prozessoptimierung", "audits"]', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(3, 'Produktion', 'produktion', 'Produktionsbereich und Fertigung', '["read_production", "upload_documents"]', '["rag_chat", "document_upload"]', '["arbeitsanweisungen", "prozessdokumentation", "qualitaetskontrolle"]', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(4, 'Entwicklung', 'entwicklung', 'Produktentwicklung und Konstruktion', '["read_development", "upload_documents"]', '["ai_playground", "rag_chat", "document_upload"]', '["technische_dokumentation", "entwicklungsprozesse", "testspezifikationen"]', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(5, 'Einkauf', 'einkauf', 'Einkauf und Beschaffung', '["read_procurement", "upload_documents"]', '["rag_chat", "document_upload"]', '["lieferantenbewertung", "bestellprozesse", "qualitaetsanforderungen"]', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(6, 'Vertrieb', 'vertrieb', 'Vertrieb und Kundenbetreuung', '["read_sales", "upload_documents"]', '["rag_chat", "document_upload"]', '["kundenanforderungen", "angebotsprozesse", "vertragsmanagement"]', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(7, 'Personal', 'personal', 'Personalwesen und HR', '["read_hr", "upload_documents"]', '["rag_chat", "document_upload"]', '["personalprozesse", "schulungen", "compliance"]', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(8, 'IT', 'it', 'Informationstechnologie', '["read_it", "system_admin", "upload_documents"]', '["ai_playground", "rag_chat", "document_upload", "system_management"]', '["systemwartung", "datenmanagement", "sicherheit"]', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(9, 'Finanzen', 'finanzen', 'Finanzwesen und Controlling', '["read_finance", "upload_documents"]', '["rag_chat", "document_upload"]', '["finanzprozesse", "controlling", "compliance"]', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(10, 'Recht', 'recht', 'Rechtsabteilung und Compliance', '["read_legal", "upload_documents"]', '["rag_chat", "document_upload"]', '["rechtliche_pruefung", "compliance", "vertraege"]', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(11, 'Marketing', 'marketing', 'Marketing und Kommunikation', '["read_marketing", "upload_documents"]', '["ai_playground", "rag_chat", "document_upload"]', '["marketingprozesse", "kommunikation", "branding"]', FALSE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(12, 'Kunden', 'kunden', 'Externe Kunden und Partner', '["read_customer"]', '["rag_chat"]', '["dokumenteneinsicht", "anfragen", "feedback"]', TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(13, 'Lieferanten', 'lieferanten', 'Externe Lieferanten und Dienstleister', '["read_supplier"]', '["rag_chat"]', '["dokumenteneinsicht", "anfragen", "compliance"]', TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- 5.2 Standard Document Types (7 Typen)
INSERT OR IGNORE INTO document_types (id, name, code, description, allowed_file_types, max_file_size_mb, requires_ocr, requires_vision, is_active, sort_order, created_at, updated_at) VALUES
(1, 'Standard Operating Procedure', 'SOP', 'Standard Operating Procedures - Arbeitsanweisungen und Prozessbeschreibungen', '["pdf", "docx"]', 50, FALSE, TRUE, TRUE, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2, 'Arbeitsanweisung', 'ARBEITSANWEISUNG', 'Detaillierte Arbeitsanweisungen für spezifische Tätigkeiten', '["pdf", "docx", "png", "jpg"]', 25, TRUE, TRUE, TRUE, 2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(3, 'Flussdiagramm', 'FLUSSDIAGRAMM', 'Prozess-Flussdiagramme und Workflow-Darstellungen', '["pdf", "png", "jpg"]', 10, FALSE, TRUE, TRUE, 3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(4, 'Formular', 'FORMULAR', 'Formulare und Checklisten', '["pdf", "docx", "png", "jpg"]', 5, TRUE, TRUE, TRUE, 4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(5, 'Prozess', 'PROZESS', 'Prozessbeschreibungen und Verfahrensanweisungen', '["pdf", "docx"]', 30, FALSE, TRUE, TRUE, 5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(6, 'Qualitätsmanagement', 'QUALITAETSMANAGEMENT', 'QM-Dokumente und Qualitätsrichtlinien', '["pdf", "docx"]', 40, FALSE, TRUE, TRUE, 6, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(7, 'Compliance', 'COMPLIANCE', 'Compliance-Dokumente und rechtliche Vorgaben', '["pdf", "docx"]', 35, FALSE, TRUE, TRUE, 7, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- 5.3 QMS Admin User
INSERT OR IGNORE INTO users (id, email, full_name, employee_id, organizational_unit, hashed_password, individual_permissions, is_qms_admin, cannot_be_deleted, is_active, created_at, updated_at) VALUES
(1, 'qms.admin@company.com', 'QMS Administrator', 'QMS001', 'Qualitätsmanagement', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4/LewdBPj4', '["system_admin", "read_all", "write_all", "approve_all", "delete_all"]', TRUE, TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- 5.4 QMS Admin Membership
INSERT OR IGNORE INTO user_group_memberships (id, user_id, interest_group_id, role_in_group, approval_level, is_department_head, is_active, joined_at, updated_at, assigned_by_id) VALUES
(1, 1, 2, 'QMS Administrator', 5, TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1);

-- =====================================================
-- 6. TRIGGER FÜR AUTOMATISCHE UPDATES
-- =====================================================

-- Trigger für updated_at in users
CREATE TRIGGER IF NOT EXISTS update_users_updated_at 
    AFTER UPDATE ON users
    FOR EACH ROW
    BEGIN
        UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Trigger für updated_at in interest_groups
CREATE TRIGGER IF NOT EXISTS update_interest_groups_updated_at 
    AFTER UPDATE ON interest_groups
    FOR EACH ROW
    BEGIN
        UPDATE interest_groups SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Trigger für updated_at in user_group_memberships
CREATE TRIGGER IF NOT EXISTS update_user_group_memberships_updated_at 
    AFTER UPDATE ON user_group_memberships
    FOR EACH ROW
    BEGIN
        UPDATE user_group_memberships SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Trigger für updated_at in document_types
CREATE TRIGGER IF NOT EXISTS update_document_types_updated_at 
    AFTER UPDATE ON document_types
    FOR EACH ROW
    BEGIN
        UPDATE document_types SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Trigger für updated_at in prompt_templates
CREATE TRIGGER IF NOT EXISTS update_prompt_templates_updated_at 
    AFTER UPDATE ON prompt_templates
    FOR EACH ROW
    BEGIN
        UPDATE prompt_templates SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Trigger für updated_at in document_comments
CREATE TRIGGER IF NOT EXISTS update_document_comments_updated_at 
    AFTER UPDATE ON document_comments
    FOR EACH ROW
    BEGIN
        UPDATE document_comments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Trigger für updated_at in document_ai_responses
CREATE TRIGGER IF NOT EXISTS update_document_ai_responses_updated_at 
    AFTER UPDATE ON document_ai_responses
    FOR EACH ROW
    BEGIN
        UPDATE document_ai_responses SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- =====================================================
-- 7. VIEWS FÜR KOMPLEXE QUERIES
-- =====================================================

-- View für aktive User mit ihren Gruppen
CREATE VIEW IF NOT EXISTS active_users_with_groups AS
SELECT 
    u.id,
    u.email,
    u.full_name,
    u.employee_id,
    u.organizational_unit,
    u.is_qms_admin,
    GROUP_CONCAT(ig.name, ', ') as interest_groups,
    MAX(ugm.approval_level) as max_approval_level
FROM users u
LEFT JOIN user_group_memberships ugm ON u.id = ugm.user_id AND ugm.is_active = TRUE
LEFT JOIN interest_groups ig ON ugm.interest_group_id = ig.id AND ig.is_active = TRUE
WHERE u.is_active = TRUE
GROUP BY u.id, u.email, u.full_name, u.employee_id, u.organizational_unit, u.is_qms_admin;

-- View für Dokumente mit Status-Informationen
CREATE VIEW IF NOT EXISTS documents_with_status AS
SELECT 
    ud.id,
    ud.filename,
    ud.original_filename,
    ud.file_type,
    dt.name as document_type_name,
    ud.qm_chapter,
    ud.version,
    ud.workflow_status,
    ud.processing_status,
    u.full_name as uploaded_by,
    ud.uploaded_at,
    COUNT(udp.id) as page_count,
    COUNT(udig.id) as assigned_groups_count
FROM upload_documents ud
LEFT JOIN document_types dt ON ud.document_type_id = dt.id
LEFT JOIN users u ON ud.uploaded_by_user_id = u.id
LEFT JOIN upload_document_pages udp ON ud.id = udp.upload_document_id
LEFT JOIN upload_document_interest_groups udig ON ud.id = udig.upload_document_id
GROUP BY ud.id, ud.filename, ud.original_filename, ud.file_type, dt.name, ud.qm_chapter, ud.version, ud.workflow_status, ud.processing_status, u.full_name, ud.uploaded_at;

-- =====================================================
-- 8. PRAGMA SETTINGS FÜR SQLITE OPTIMIERUNG
-- =====================================================

-- SQLite-spezifische Optimierungen
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 268435456;

-- =====================================================
-- SCRIPT ERFOLGREICH ABGESCHLOSSEN
-- =====================================================
-- 
-- Dieses Script erstellt:
-- - 15 Tabellen (Core: 5 + Document Upload: 6 + RAG: 4)
-- - 30+ Indizes für optimale Performance
-- - 20+ Foreign Key Constraints
-- - 6 Trigger für automatische Updates
-- - 2 Views für komplexe Queries
-- - Standard-Seed-Daten (13 Interest Groups, 7 Document Types, 1 QMS Admin)
-- - SQLite-Optimierungen
--
-- Datenbank-Pfad: /Users/reiner/Documents/DocuMind-AI-V2/data/qms.db
-- Version: 2.1.0
-- Stand: 2025-10-28
-- =====================================================
