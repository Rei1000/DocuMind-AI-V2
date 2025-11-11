-- Reset RAG Analytics Data
-- Löscht alle Analytics-Daten für Testzwecke
-- WICHTIG: Dies löscht alle Feedback, Chat-Messages und Audit-Logs!

-- 1. Lösche alle Feedback-Einträge
DELETE FROM rag_feedback;

-- 2. Lösche alle Chat-Messages (inkl. message_metadata)
DELETE FROM rag_chat_messages;

-- 3. Lösche alle Chat-Sessions
DELETE FROM rag_chat_sessions;

-- 4. Lösche alle Audit-Logs
DELETE FROM rag_audit_logs;

-- 5. Reset SQLite Sequenzen (falls verwendet)
-- SQLite verwendet AUTOINCREMENT, daher nicht nötig

-- Bestätigung
SELECT 'RAG Analytics Daten wurden zurückgesetzt!' AS status;

