-- Database Migration: RAG Integration Tables
-- Erstellt die Tabellen für das RAG System

-- Tabelle für indexierte Dokumente
CREATE TABLE IF NOT EXISTS rag_indexed_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_document_id INTEGER NOT NULL UNIQUE,
    document_title VARCHAR(500) NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'indexed',
    indexed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_chunks INTEGER NOT NULL DEFAULT 0,
    last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Indizes
    INDEX idx_rag_indexed_documents_upload_id (upload_document_id),
    INDEX idx_rag_indexed_documents_status (status),
    INDEX idx_rag_indexed_documents_type (document_type),
    INDEX idx_rag_indexed_documents_indexed_at (indexed_at)
);

-- Tabelle für Dokument-Chunks
CREATE TABLE IF NOT EXISTS rag_document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indexed_document_id INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    page_numbers JSON NOT NULL, -- List[int]
    heading_hierarchy JSON, -- List[str]
    document_type VARCHAR(100) NOT NULL,
    confidence_score REAL NOT NULL DEFAULT 1.0,
    chunk_type VARCHAR(50) NOT NULL DEFAULT 'text',
    token_count INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key
    FOREIGN KEY (indexed_document_id) REFERENCES rag_indexed_documents(id) ON DELETE CASCADE,
    
    -- Indizes
    INDEX idx_rag_document_chunks_document_id (indexed_document_id),
    INDEX idx_rag_document_chunks_type (document_type),
    INDEX idx_rag_document_chunks_chunk_type (chunk_type),
    INDEX idx_rag_document_chunks_confidence (confidence_score),
    INDEX idx_rag_document_chunks_created_at (created_at)
);

-- Tabelle für Chat-Sessions
CREATE TABLE IF NOT EXISTS rag_chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_name VARCHAR(200) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER NOT NULL DEFAULT 0,
    
    -- Indizes
    INDEX idx_rag_chat_sessions_user_id (user_id),
    INDEX idx_rag_chat_sessions_last_activity (last_activity),
    INDEX idx_rag_chat_sessions_created_at (created_at)
);

-- Tabelle für Chat-Messages
CREATE TABLE IF NOT EXISTS rag_chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_session_id INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL, -- 'user' oder 'assistant'
    content TEXT NOT NULL,
    source_references JSON, -- List[Dict] mit SourceReference Daten
    structured_data JSON, -- Dict mit strukturierten Daten
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key
    FOREIGN KEY (chat_session_id) REFERENCES rag_chat_sessions(id) ON DELETE CASCADE,
    
    -- Indizes
    INDEX idx_rag_chat_messages_session_id (chat_session_id),
    INDEX idx_rag_chat_messages_role (role),
    INDEX idx_rag_chat_messages_created_at (created_at)
);

-- Trigger für automatische Updates
CREATE TRIGGER IF NOT EXISTS update_rag_indexed_documents_timestamp
    AFTER UPDATE ON rag_indexed_documents
    FOR EACH ROW
    BEGIN
        UPDATE rag_indexed_documents 
        SET last_updated = CURRENT_TIMESTAMP 
        WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_rag_chat_sessions_activity
    AFTER INSERT ON rag_chat_messages
    FOR EACH ROW
    BEGIN
        UPDATE rag_chat_sessions 
        SET last_activity = CURRENT_TIMESTAMP,
            message_count = message_count + 1
        WHERE id = NEW.chat_session_id;
    END;

-- Views für häufig verwendete Queries
CREATE VIEW IF NOT EXISTS rag_document_summary AS
SELECT 
    d.id,
    d.upload_document_id,
    d.document_title,
    d.document_type,
    d.status,
    d.indexed_at,
    d.total_chunks,
    d.last_updated,
    COUNT(c.id) as actual_chunks,
    AVG(c.confidence_score) as avg_confidence,
    SUM(c.token_count) as total_tokens
FROM rag_indexed_documents d
LEFT JOIN rag_document_chunks c ON d.id = c.indexed_document_id
GROUP BY d.id;

CREATE VIEW IF NOT EXISTS rag_session_summary AS
SELECT 
    s.id,
    s.user_id,
    s.session_name,
    s.created_at,
    s.last_activity,
    s.message_count,
    COUNT(m.id) as actual_messages,
    MAX(m.created_at) as last_message_at
FROM rag_chat_sessions s
LEFT JOIN rag_chat_messages m ON s.id = m.chat_session_id
GROUP BY s.id;

-- Initiale Daten (falls benötigt)
INSERT OR IGNORE INTO rag_indexed_documents (
    upload_document_id, 
    document_title, 
    document_type, 
    status, 
    total_chunks
) VALUES (
    0, 
    'System Placeholder', 
    'system', 
    'indexed', 
    0
);

-- Kommentare für Dokumentation
-- Diese Migration erstellt die komplette Datenbankstruktur für das RAG System
-- Alle Tabellen sind optimiert für die Anforderungen des RAG Systems
-- Indizes sind für häufige Suchoperationen optimiert
-- Trigger sorgen für automatische Updates von Timestamps und Zählern
-- Views bieten vereinfachte Zugriffe auf komplexe Daten
