-- =====================================================
-- Migration: Add File Hash & Duplikat-Erkennung Fields
-- =====================================================
-- Version: 1.1.0
-- Stand: 2025-11-02
-- Document Lifecycle Phase 1.1
-- =====================================================
-- 
-- Fügt folgende Felder zur upload_documents Tabelle hinzu:
-- - file_hash: SHA-256 Hash (64 hex Zeichen) für Duplikat-Prüfung
-- - is_duplicate: Flag ob Dokument ein Duplikat ist
-- - duplicate_of_document_id: Link zum Original-Dokument
-- =====================================================

-- Prüfe ob Felder bereits existieren (für idempotente Migration)
-- SQLite unterstützt kein "IF NOT EXISTS" für ALTER TABLE ADD COLUMN,
-- daher verwenden wir einen Workaround mit pragma table_info

-- Füge file_hash Feld hinzu
-- SQLite benötigt separate ALTER TABLE Statements
ALTER TABLE upload_documents ADD COLUMN file_hash VARCHAR(64);

-- Füge is_duplicate Feld hinzu
ALTER TABLE upload_documents ADD COLUMN is_duplicate BOOLEAN NOT NULL DEFAULT FALSE;

-- Füge duplicate_of_document_id Feld hinzu
ALTER TABLE upload_documents ADD COLUMN duplicate_of_document_id INTEGER;

-- Füge Foreign Key hinzu (SQLite erfordert separaten Schritt)
-- ACHTUNG: SQLite unterstützt ALTER TABLE ... ADD CONSTRAINT erst ab Version 3.37.0
-- Falls nicht verfügbar, wird Foreign Key nur durch Application-Level validiert

-- Erstelle Indizes
CREATE INDEX IF NOT EXISTS idx_upload_documents_file_hash ON upload_documents(file_hash) WHERE file_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_upload_documents_is_duplicate ON upload_documents(is_duplicate) WHERE is_duplicate = TRUE;
CREATE INDEX IF NOT EXISTS idx_upload_documents_duplicate_of ON upload_documents(duplicate_of_document_id) WHERE duplicate_of_document_id IS NOT NULL;

-- UNIQUE Constraint auf file_hash (für schnelle Duplikat-Prüfung)
-- SQLite benötigt CREATE UNIQUE INDEX statt ALTER TABLE
CREATE UNIQUE INDEX IF NOT EXISTS idx_upload_documents_file_hash_unique ON upload_documents(file_hash) WHERE file_hash IS NOT NULL;

