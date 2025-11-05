-- Document Lifecycle Phase 1.4: Archivierung
-- Migration: Füge Archive-Felder zur upload_documents Tabelle hinzu

-- 1. Füge Spalten hinzu
ALTER TABLE upload_documents ADD COLUMN archived_at DATETIME;
ALTER TABLE upload_documents ADD COLUMN archived_by_user_id INTEGER;
ALTER TABLE upload_documents ADD COLUMN archive_reason TEXT;

-- 2. Füge Foreign Key hinzu (SQLite unterstützt ALTER TABLE ADD FOREIGN KEY nicht direkt)
-- Für SQLite: Foreign Key wird beim nächsten CREATE TABLE mit CHECK Constraint validiert
-- Für PostgreSQL/MySQL: 
-- ALTER TABLE upload_documents ADD CONSTRAINT fk_archived_by_user 
--     FOREIGN KEY (archived_by_user_id) REFERENCES users(id);

-- 3. Erstelle Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_upload_documents_archived_at ON upload_documents(archived_at) WHERE archived_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_upload_documents_archived_by_user_id ON upload_documents(archived_by_user_id) WHERE archived_by_user_id IS NOT NULL;

