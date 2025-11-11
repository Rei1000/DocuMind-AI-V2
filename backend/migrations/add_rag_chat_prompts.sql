-- =====================================================
-- Migration: Add RAG Chat Prompts Table
-- =====================================================
-- Version: 1.0.0
-- Stand: 2025-11-11
-- PHASE 1: RAG Chat Prompt Management
-- =====================================================
-- 
-- Erstellt rag_chat_prompts Tabelle für globale, dokumenttyp-spezifische
-- RAG Chat Prompts (Level 4+ können diese anpassen).
-- 
-- Features:
-- - Ein Prompt pro Dokumenttyp (UNIQUE constraint)
-- - Global gespeichert (für alle User)
-- - Audit-Trail (created_by_user_id, created_at, updated_at)
-- =====================================================

-- 1. Erstelle rag_chat_prompts Tabelle
CREATE TABLE IF NOT EXISTS rag_chat_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type_id INTEGER NOT NULL,
    prompt_text TEXT NOT NULL,
    multi_query_prompt_text TEXT,  -- PHASE 2: Multi-Query Prompt (optional)
    created_by_user_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    -- UNIQUE: Ein Prompt pro Dokumenttyp (global)
    UNIQUE(document_type_id),
    
    -- Foreign Keys (SQLite unterstützt ALTER TABLE ADD FOREIGN KEY nicht direkt)
    -- Für PostgreSQL/MySQL:
    -- FOREIGN KEY (document_type_id) REFERENCES document_types(id),
    -- FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    
    -- CHECK Constraints
    CHECK (LENGTH(prompt_text) > 0)  -- Prompt darf nicht leer sein
);

-- 2. Erstelle Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_rag_chat_prompts_document_type_id ON rag_chat_prompts(document_type_id);
CREATE INDEX IF NOT EXISTS idx_rag_chat_prompts_created_by_user_id ON rag_chat_prompts(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_rag_chat_prompts_updated_at ON rag_chat_prompts(updated_at);

-- 3. Kommentare (SQLite unterstützt keine Kommentare, aber für PostgreSQL/MySQL)
-- COMMENT ON TABLE rag_chat_prompts IS 'Globale RAG Chat Prompts pro Dokumenttyp (Level 4+ können anpassen)';
-- COMMENT ON COLUMN rag_chat_prompts.document_type_id IS 'Eindeutiger Dokumenttyp (UNIQUE constraint)';
-- COMMENT ON COLUMN rag_chat_prompts.prompt_text IS 'RAG Chat Prompt-Text für diesen Dokumenttyp';
-- COMMENT ON COLUMN rag_chat_prompts.multi_query_prompt_text IS 'Multi-Query Prompt-Text (optional, PHASE 2)';
-- COMMENT ON COLUMN rag_chat_prompts.created_by_user_id IS 'User ID des Erstellers (Audit-Trail)';

