-- RAG UX Transparency Phase 1.3: Audit-Trail
-- Migration: Erstelle rag_audit_logs Tabelle für vollständige Transparenz und Compliance

-- 1. Erstelle rag_audit_logs Tabelle
CREATE TABLE IF NOT EXISTS rag_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indexed_document_id INTEGER,
    action VARCHAR(50) NOT NULL,
    user_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    duration_ms INTEGER,
    tokens_used INTEGER,
    cost_usd INTEGER,  -- In Cents gespeichert
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys (SQLite unterstützt ALTER TABLE ADD FOREIGN KEY nicht direkt)
    -- Für PostgreSQL/MySQL:
    -- FOREIGN KEY (user_id) REFERENCES users(id),
    -- FOREIGN KEY (indexed_document_id) REFERENCES indexed_documents(id)
    
    -- Constraints
    CHECK (status IN ('success', 'failed', 'in_progress')),
    CHECK (action IN (
        'chunking_started', 'chunking_completed', 'chunking_failed',
        'chunk_created', 'chunk_edited', 'chunk_deleted',
        'embedding_started', 'embedding_completed', 'embedding_failed',
        'indexing_started', 'indexing_completed', 'indexing_failed',
        'query_executed', 'feedback_submitted'
    ))
);

-- 2. Erstelle Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_rag_audit_logs_indexed_document_id ON rag_audit_logs(indexed_document_id) WHERE indexed_document_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_rag_audit_logs_action ON rag_audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_rag_audit_logs_user_id ON rag_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_rag_audit_logs_timestamp ON rag_audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_rag_audit_logs_status ON rag_audit_logs(status);

-- 3. Kommentare (SQLite unterstützt keine Kommentare, aber für PostgreSQL/MySQL)
-- COMMENT ON TABLE rag_audit_logs IS 'RAG Audit Log für vollständige Transparenz und Compliance';
-- COMMENT ON COLUMN rag_audit_logs.cost_usd IS 'Geschätzte Kosten in USD (Cents)';

