-- Migration: Add Workflow Tables for Document Management
-- Date: 2025-10-14
-- Purpose: Phase 4 - Document Workflow with Audit Trail

-- 1. Add workflow_status to upload_documents (if not exists)
ALTER TABLE upload_documents 
ADD COLUMN IF NOT EXISTS workflow_status VARCHAR(20) NOT NULL DEFAULT 'draft' 
CHECK (workflow_status IN ('draft', 'in_review', 'reviewed', 'approved', 'rejected'));

CREATE INDEX IF NOT EXISTS idx_upload_documents_workflow_status ON upload_documents(workflow_status);

-- 2. Create document_status_changes table (Audit Trail)
CREATE TABLE IF NOT EXISTS document_status_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_document_id INTEGER NOT NULL,
    
    -- Status Change
    from_status VARCHAR(20),
    to_status VARCHAR(20) NOT NULL,
    
    -- Change Information
    changed_by_user_id INTEGER NOT NULL,
    changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    change_reason TEXT,
    comment TEXT,
    
    -- Timestamps
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    FOREIGN KEY (upload_document_id) REFERENCES upload_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by_user_id) REFERENCES users(id),
    
    -- Indexes
    CHECK (from_status IN ('draft', 'in_review', 'reviewed', 'approved', 'rejected') OR from_status IS NULL),
    CHECK (to_status IN ('draft', 'in_review', 'reviewed', 'approved', 'rejected'))
);

CREATE INDEX idx_status_changes_document ON document_status_changes(upload_document_id);
CREATE INDEX idx_status_changes_user ON document_status_changes(changed_by_user_id);
CREATE INDEX idx_status_changes_date ON document_status_changes(changed_at);

-- 3. Create document_comments table
CREATE TABLE IF NOT EXISTS document_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_document_id INTEGER NOT NULL,
    
    -- Comment Content
    comment_text TEXT NOT NULL,
    comment_type VARCHAR(20) NOT NULL DEFAULT 'general' 
        CHECK (comment_type IN ('general', 'review', 'rejection', 'approval')),
    
    -- Related to specific page?
    page_number INTEGER,
    
    -- Comment Metadata
    created_by_user_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Link to status change?
    status_change_id INTEGER,
    
    -- Timestamps
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    FOREIGN KEY (upload_document_id) REFERENCES upload_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id),
    FOREIGN KEY (status_change_id) REFERENCES document_status_changes(id),
    
    CHECK (page_number IS NULL OR page_number > 0)
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
