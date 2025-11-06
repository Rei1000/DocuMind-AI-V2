-- RAG UX Transparency Phase 4.1: User Feedback System
-- Migration: Erstelle rag_feedback Tabelle für User Feedback zu RAG Chat-Antworten

-- 1. Erstelle rag_feedback Tabelle
CREATE TABLE IF NOT EXISTS rag_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_message_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    rating VARCHAR(20) NOT NULL,
    comment TEXT,
    submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys (SQLite unterstützt ALTER TABLE ADD FOREIGN KEY nicht direkt)
    -- Für PostgreSQL/MySQL:
    -- FOREIGN KEY (chat_message_id) REFERENCES chat_messages(id),
    -- FOREIGN KEY (user_id) REFERENCES users(id)
    
    -- Constraints
    CHECK (rating IN ('positive', 'negative', 'neutral')),
    CHECK (LENGTH(comment) <= 2000)
);

-- 2. Erstelle Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_rag_feedback_chat_message_id ON rag_feedback(chat_message_id);
CREATE INDEX IF NOT EXISTS idx_rag_feedback_user_id ON rag_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_rag_feedback_rating ON rag_feedback(rating);
CREATE INDEX IF NOT EXISTS idx_rag_feedback_submitted_at ON rag_feedback(submitted_at);

-- 3. Unique Constraint: Ein User kann nur einmal pro Message Feedback geben
CREATE UNIQUE INDEX IF NOT EXISTS idx_rag_feedback_unique_user_message 
ON rag_feedback(chat_message_id, user_id);

-- 4. Kommentare (SQLite unterstützt keine Kommentare, aber für PostgreSQL/MySQL)
-- COMMENT ON TABLE rag_feedback IS 'User Feedback für RAG Chat-Antworten';

