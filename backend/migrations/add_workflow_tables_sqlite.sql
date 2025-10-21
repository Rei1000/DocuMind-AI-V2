-- Migration: Add Workflow Tables for Document Management
-- Date: 2025-10-14
-- Purpose: Phase 4 - Document Workflow with Audit Trail

-- 1. Add workflow_status to upload_documents
ALTER TABLE upload_documents 
ADD COLUMN workflow_status VARCHAR(20) NOT NULL DEFAULT 'draft';

-- 2. Create document_status_changes table (Audit Trail)
CREATE TABLE IF NOT EXISTS document_status_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_document_id INTEGER NOT NULL,
    from_status VARCHAR(20),
    to_status VARCHAR(20) NOT NULL,
    changed_by_user_id INTEGER NOT NULL,
    changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    change_reason TEXT,
    comment TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_document_id) REFERENCES upload_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by_user_id) REFERENCES users(id)
);

CREATE INDEX idx_status_changes_document ON document_status_changes(upload_document_id);
CREATE INDEX idx_status_changes_user ON document_status_changes(changed_by_user_id);
CREATE INDEX idx_status_changes_date ON document_status_changes(changed_at);

-- 3. Create document_comments table
CREATE TABLE IF NOT EXISTS document_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_document_id INTEGER NOT NULL,
    comment_text TEXT NOT NULL,
    comment_type VARCHAR(20) NOT NULL DEFAULT 'general',
    page_number INTEGER,
    created_by_user_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status_change_id INTEGER,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_document_id) REFERENCES upload_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id),
    FOREIGN KEY (status_change_id) REFERENCES document_status_changes(id)
);

CREATE INDEX idx_comments_document ON document_comments(upload_document_id);
CREATE INDEX idx_comments_user ON document_comments(created_by_user_id);
CREATE INDEX idx_comments_date ON document_comments(created_at);

-- 4. Insert initial status change for existing documents
INSERT INTO document_status_changes (
    upload_document_id,
    from_status,
    to_status,
    changed_by_user_id,
    change_reason
)
SELECT 
    id,
    NULL,
    'draft',
    uploaded_by_user_id,
    'Initial upload'
FROM upload_documents
WHERE NOT EXISTS (
    SELECT 1 FROM document_status_changes 
    WHERE upload_document_id = upload_documents.id
);
