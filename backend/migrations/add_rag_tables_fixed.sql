-- Database Migration: RAG Integration Tables (SQLite Compatible)
-- Erstellt die Tabellen für das RAG System

-- Tabelle für indexierte Dokumente
CREATE TABLE IF NOT EXISTS rag_indexed_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_document_id INTEGER NOT NULL UNIQUE,
    collection_name VARCHAR(200) NOT NULL,
    indexed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_chunks INTEGER NOT NULL DEFAULT 0,
    last_updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indizes für rag_indexed_documents
CREATE INDEX IF NOT EXISTS idx_rag_indexed_documents_upload_id ON rag_indexed_documents(upload_document_id);
CREATE INDEX IF NOT EXISTS idx_rag_indexed_documents_collection ON rag_indexed_documents(collection_name);
CREATE INDEX IF NOT EXISTS idx_rag_indexed_documents_indexed_at ON rag_indexed_documents(indexed_at);

-- Tabelle für Dokument-Chunks
CREATE TABLE IF NOT EXISTS rag_document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indexed_document_id INTEGER NOT NULL,
    chunk_id VARCHAR(100) NOT NULL UNIQUE,
    chunk_text TEXT NOT NULL,
    qdrant_point_id VARCHAR(100) NOT NULL UNIQUE,
    page_numbers TEXT NOT NULL, -- JSON als TEXT
    heading_hierarchy TEXT, -- JSON als TEXT
    document_type_id INTEGER NOT NULL,
    confidence_score REAL NOT NULL DEFAULT 1.0,
    chunk_type VARCHAR(50) NOT NULL DEFAULT 'text',
    token_count INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (indexed_document_id) REFERENCES rag_indexed_documents(id) ON DELETE CASCADE
);

-- Indizes für rag_document_chunks
CREATE INDEX IF NOT EXISTS idx_rag_document_chunks_document_id ON rag_document_chunks(indexed_document_id);
CREATE INDEX IF NOT EXISTS idx_rag_document_chunks_chunk_id ON rag_document_chunks(chunk_id);
CREATE INDEX IF NOT EXISTS idx_rag_document_chunks_qdrant_id ON rag_document_chunks(qdrant_point_id);
CREATE INDEX IF NOT EXISTS idx_rag_document_chunks_type ON rag_document_chunks(document_type_id);
CREATE INDEX IF NOT EXISTS idx_rag_document_chunks_chunk_type ON rag_document_chunks(chunk_type);
CREATE INDEX IF NOT EXISTS idx_rag_document_chunks_confidence ON rag_document_chunks(confidence_score);
CREATE INDEX IF NOT EXISTS idx_rag_document_chunks_created_at ON rag_document_chunks(created_at);

-- Tabelle für Chat-Sessions
CREATE TABLE IF NOT EXISTS rag_chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_name VARCHAR(200) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT 1
);

-- Indizes für rag_chat_sessions
CREATE INDEX IF NOT EXISTS idx_rag_chat_sessions_user_id ON rag_chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_rag_chat_sessions_last_activity ON rag_chat_sessions(last_activity);
CREATE INDEX IF NOT EXISTS idx_rag_chat_sessions_created_at ON rag_chat_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_rag_chat_sessions_is_active ON rag_chat_sessions(is_active);

-- Tabelle für Chat-Messages
CREATE TABLE IF NOT EXISTS rag_chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL, -- 'user' oder 'assistant'
    content TEXT NOT NULL,
    source_references TEXT, -- JSON als TEXT
    source_chunk_ids TEXT, -- JSON als TEXT
    confidence_scores TEXT, -- JSON als TEXT
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES rag_chat_sessions(id) ON DELETE CASCADE
);

-- Indizes für rag_chat_messages
CREATE INDEX IF NOT EXISTS idx_rag_chat_messages_session_id ON rag_chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_rag_chat_messages_role ON rag_chat_messages(role);
CREATE INDEX IF NOT EXISTS idx_rag_chat_messages_created_at ON rag_chat_messages(created_at);

-- Trigger für automatische Updates
CREATE TRIGGER IF NOT EXISTS update_rag_indexed_documents_timestamp
    AFTER UPDATE ON rag_indexed_documents
    FOR EACH ROW
    BEGIN
        UPDATE rag_indexed_documents 
        SET last_updated_at = CURRENT_TIMESTAMP 
        WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_rag_chat_sessions_activity
    AFTER INSERT ON rag_chat_messages
    FOR EACH ROW
    BEGIN
        UPDATE rag_chat_sessions 
        SET last_activity = CURRENT_TIMESTAMP,
            message_count = message_count + 1
        WHERE id = NEW.session_id;
    END;
