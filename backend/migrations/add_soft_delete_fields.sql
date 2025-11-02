-- Migration: Add deleted_at, deleted_by_user_id, deletion_reason to upload_documents
-- Document Lifecycle Phase 1.3: Soft Delete

-- Add deleted_at column
ALTER TABLE upload_documents ADD COLUMN deleted_at DATETIME;

-- Add deleted_by_user_id column
ALTER TABLE upload_documents ADD COLUMN deleted_by_user_id INTEGER;

-- Add deletion_reason column
ALTER TABLE upload_documents ADD COLUMN deletion_reason TEXT;

-- Add foreign key constraint for deleted_by_user_id
-- Note: SQLite does not support ADD FOREIGN KEY to existing tables directly.
-- This would typically require recreating the table or handling in application logic.
-- For simplicity in development, we'll add it here, but be aware of SQLite limitations.
-- In a real production environment with SQLite, this might be handled differently.
-- For other DBs (PostgreSQL, MySQL), this would be:
-- ALTER TABLE upload_documents ADD CONSTRAINT fk_deleted_by_user
-- FOREIGN KEY (deleted_by_user_id) REFERENCES users(id);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_upload_documents_deleted_at ON upload_documents(deleted_at) WHERE deleted_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_upload_documents_deleted_by_user_id ON upload_documents(deleted_by_user_id) WHERE deleted_by_user_id IS NOT NULL;

