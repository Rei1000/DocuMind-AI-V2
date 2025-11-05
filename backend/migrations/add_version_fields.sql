-- Migration: Add document_series_id, parent_document_id, is_current_version to upload_documents
-- Document Lifecycle Phase 2: Versionierung

-- Add document_series_id column
ALTER TABLE upload_documents ADD COLUMN document_series_id INTEGER;

-- Add parent_document_id column
ALTER TABLE upload_documents ADD COLUMN parent_document_id INTEGER;

-- Add is_current_version column
ALTER TABLE upload_documents ADD COLUMN is_current_version BOOLEAN NOT NULL DEFAULT TRUE;

-- Add foreign key constraints for document_series_id and parent_document_id
-- Note: SQLite does not support ADD FOREIGN KEY to existing tables directly.
-- This would typically require recreating the table or handling in application logic.
-- For simplicity in development, we'll add it here, but be aware of SQLite limitations.
-- In a real production environment with SQLite, this might be handled differently.
-- For other DBs (PostgreSQL, MySQL), this would be:
-- ALTER TABLE upload_documents ADD CONSTRAINT fk_document_series
-- FOREIGN KEY (document_series_id) REFERENCES upload_documents(id);
-- ALTER TABLE upload_documents ADD CONSTRAINT fk_parent_document
-- FOREIGN KEY (parent_document_id) REFERENCES upload_documents(id);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_upload_documents_document_series_id ON upload_documents(document_series_id) WHERE document_series_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_upload_documents_parent_document_id ON upload_documents(parent_document_id) WHERE parent_document_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_upload_documents_is_current_version ON upload_documents(is_current_version) WHERE is_current_version = TRUE;

-- Set is_current_version = TRUE for all existing documents (Migration: Alle existierenden Dokumente sind aktuell)
UPDATE upload_documents SET is_current_version = TRUE WHERE is_current_version IS NULL;

