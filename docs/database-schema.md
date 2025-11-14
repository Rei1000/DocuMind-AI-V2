# 📊 DocuMind-AI V2 - Datenbank Schema

**Stand:** 2025-11-14  
**Version:** 2.7.0  
**Engine:** SQLite (Dev) / PostgreSQL (Prod)  
**Tabellen:** 21 (Core: 5 + Document Upload: 6 + RAG: 7 + ML/SHAP: 3)

**NEU (v2.7.0 - 2025-11-14):**
- ✅ **ML/SHAP SQLite-Persistenz:** 3 neue Tabellen für Training-Daten und SHAP-Cache
  - `training_samples` - Training-Daten für ML-Modelle (Features, Relevance-Scores)
  - `shap_background_data` - Historische Search-Daten für SHAP-Background (Rolling Window)
  - `shap_cache` - Gecachte SHAP-Erklärungen (LRU Cache mit TTL)
  - Migration: `backend/app/migrations/add_ml_shap_tables.py` (mit automatischem Backup)

**Hinweis (v2.6.0):** Keine DB-Änderungen. SHAP-Integration nutzt bestehende Tabellen.

**NEU (v2.5.1):**
- ✅ **RAG Chat Prompts:** `rag_chat_prompts` Tabelle (PHASE 1: RAG Chat Prompt Management)
- ✅ **RAG Feedback:** `rag_feedback` Tabelle (PHASE 4.1: User Feedback System)
- ✅ **RAG Audit Logs:** `rag_audit_logs` Tabelle (PHASE 1.3: Audit-Trail für Compliance)
- ✅ **Message Metadata:** `message_metadata` in `rag_chat_messages` (JSON für Prompt-Text, Tokens, Query-Params, generated_queries)

**NEU (v2.5.0):**
- ✅ **Chunk-Editor Overlap:** `has_overlap` und `overlap_sentence_count` in `rag_document_chunks`
  - **Split-Modal:** Visuelles Modal zum Splitten nach Sätzen (statt Buchstaben)
  - **Korrekte Overlap-Logik:** Nur der zweite Chunk beginnt mit den letzten N Sätzen des ersten Chunks
- ✅ **Strukturiertes Chunking:** JSON wird in lesbaren Text konvertiert (Fachartikel)
- ✅ **Diagramm-Beschreibung:** Figuren und Tabellen werden in Chunks integriert

**NEU (v2.3.0):**
- ✅ File Hash & Duplikat-Erkennung (SHA-256)
- ✅ Dokument-Versionierung (Series + Parent-Child)
- ✅ Soft Delete (Audit-tauglich)
- ✅ Archivierung (Automatisch + Manuell)
- ✅ **Archiv-System:** Wiederherstellung, Hard Delete, Archiv-Ansicht (Level 4+)

---

## 🎯 Entity Relationship Diagram

```mermaid
erDiagram
    %% Core System
    USERS ||--o{ USER_GROUP_MEMBERSHIPS : "has many"
    INTEREST_GROUPS ||--o{ USER_GROUP_MEMBERSHIPS : "has many"
    USERS ||--o{ DOCUMENT_TYPES : "created_by"
    USERS ||--o{ PROMPT_TEMPLATES : "created_by"
    DOCUMENT_TYPES ||--o{ PROMPT_TEMPLATES : "has many"
    
    %% Document Upload System
    USERS ||--o{ UPLOAD_DOCUMENTS : "uploaded_by"
    DOCUMENT_TYPES ||--o{ UPLOAD_DOCUMENTS : "has many"
    UPLOAD_DOCUMENTS ||--o{ UPLOAD_DOCUMENT_PAGES : "has many"
    UPLOAD_DOCUMENTS ||--o{ UPLOAD_DOCUMENT_INTEREST_GROUPS : "assigned to"
    INTEREST_GROUPS ||--o{ UPLOAD_DOCUMENT_INTEREST_GROUPS : "assigned to"
    UPLOAD_DOCUMENTS ||--o{ DOCUMENT_STATUS_CHANGES : "has history"
    UPLOAD_DOCUMENTS ||--o{ DOCUMENT_COMMENTS : "has comments"
    UPLOAD_DOCUMENTS ||--o{ DOCUMENT_AI_RESPONSES : "has AI results"
    UPLOAD_DOCUMENT_PAGES ||--o{ DOCUMENT_AI_RESPONSES : "processed by"
    PROMPT_TEMPLATES ||--o{ DOCUMENT_AI_RESPONSES : "used by"
    
    %% RAG System
    UPLOAD_DOCUMENTS ||--o{ RAG_INDEXED_DOCUMENTS : "indexed as"
    RAG_INDEXED_DOCUMENTS ||--o{ RAG_DOCUMENT_CHUNKS : "has chunks"
    RAG_INDEXED_DOCUMENTS ||--o{ RAG_AUDIT_LOGS : "has logs"
    USERS ||--o{ RAG_CHAT_SESSIONS : "has sessions"
    RAG_CHAT_SESSIONS ||--o{ RAG_CHAT_MESSAGES : "has messages"
    RAG_CHAT_MESSAGES ||--o{ RAG_FEEDBACK : "has feedback"
    DOCUMENT_TYPES ||--o| RAG_CHAT_PROMPTS : "has prompt"
    USERS ||--o{ RAG_CHAT_PROMPTS : "created by"
    USERS ||--o{ RAG_FEEDBACK : "submitted by"
    USERS ||--o{ RAG_AUDIT_LOGS : "performed by"
    
    %% ML/SHAP System (NEU v2.7.0)
    USERS ||--o{ TRAINING_SAMPLES : "feedback by"
    RAG_CHAT_MESSAGES ||--o{ TRAINING_SAMPLES : "generates"
    RAG_FEEDBACK ||--o{ TRAINING_SAMPLES : "creates"
    
    USERS {
        int id PK
        string email UK
        string full_name
        string employee_id UK
        string organizational_unit
        string hashed_password
        text individual_permissions
        boolean is_qms_admin
        boolean cannot_be_deleted
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    INTEREST_GROUPS {
        int id PK
        string name UK
        string code UK
        text description
        text group_permissions
        text ai_functionality
        text typical_tasks
        boolean is_external
        boolean is_active
        datetime created_at
        datetime updated_at
        int created_by_id FK
    }
    
    USER_GROUP_MEMBERSHIPS {
        int id PK
        int user_id FK
        int interest_group_id FK
        string role_in_group
        int approval_level
        boolean is_department_head
        boolean is_active
        datetime joined_at
        datetime updated_at
        int assigned_by_id FK
        text notes
    }
    
    DOCUMENT_TYPES {
        int id PK
        string name
        string code UK
        text description
        text allowed_file_types
        int max_file_size_mb
        boolean requires_ocr
        boolean requires_vision
        int default_prompt_template_id FK
        int created_by FK
        boolean is_active
        int sort_order
        datetime created_at
        datetime updated_at
    }
    
    PROMPT_TEMPLATES {
        int id PK
        string name UK
        text description
        text prompt_text
        text system_instructions
        int document_type_id FK
        string ai_model
        int temperature
        int max_tokens
        int top_p
        string detail_level
        string status
        string version
        boolean tested_successfully
        int success_count
        datetime last_used_at
        int created_by FK
        text tags
        text example_input
        text example_output
        datetime created_at
        datetime updated_at
    }
    
    UPLOAD_DOCUMENTS {
        int id PK
        string filename
        string original_filename
        int file_size_bytes
        string file_type
        int document_type_id FK
        string qm_chapter
        string version
        int page_count
        int uploaded_by_user_id FK
        datetime uploaded_at
        string file_path
        string processing_method
        string processing_status
        string workflow_status
        string file_hash UK "SHA-256 Hash (64 hex) - NEU v2.3"
        boolean is_duplicate "Flag: Duplikat? - NEU v2.3"
        int duplicate_of_document_id FK "Link zum Original - NEU v2.3"
        int document_series_id FK "Dokument-Serie ID - NEU v2.3"
        int parent_document_id FK "Vorgänger-Version - NEU v2.3"
        boolean is_current_version "Aktuelle Version? - NEU v2.3"
        datetime deleted_at "Soft Delete Zeitstempel - NEU v2.3"
        int deleted_by_user_id FK "User der gelöscht hat - NEU v2.3"
        text deletion_reason "Grund für Löschung - NEU v2.3"
        datetime archived_at "Archivierungs-Zeitstempel - NEU v2.3"
        int archived_by_user_id FK "User der archiviert hat - NEU v2.3"
        text archive_reason "Grund für Archivierung - NEU v2.3"
    }
    
    UPLOAD_DOCUMENT_PAGES {
        int id PK
        int upload_document_id FK
        int page_number
        string preview_image_path
        string thumbnail_path
        int width
        int height
        datetime created_at
    }
    
    RAG_INDEXED_DOCUMENTS {
        int id PK
        int upload_document_id FK
        string qdrant_collection_name
        int total_chunks
        datetime indexed_at
        datetime last_updated_at
        string embedding_model
    }
    
    RAG_DOCUMENT_CHUNKS {
        int id PK
        int rag_indexed_document_id FK
        string chunk_id UK
        text chunk_text
        int page_number
        int paragraph_index
        int chunk_index
        int token_count
        int sentence_count
        boolean has_overlap
        int overlap_sentence_count
        string qdrant_point_id
        text embedding_vector_preview
        datetime created_at
    }
    
    RAG_CHAT_SESSIONS {
        int id PK
        int user_id FK
        string session_name
        datetime created_at
        datetime last_message_at
        boolean is_active
    }
    
    RAG_CHAT_MESSAGES {
        int id PK
        int session_id FK
        string role
        text content
        text source_chunks
        string ai_model_used
        text message_metadata "NEU v2.5.0"
        datetime created_at
    }
    
    RAG_CHAT_PROMPTS {
        int id PK
        int document_type_id FK UK "NEU v2.5.1"
        text prompt_text
        text multi_query_prompt_text "NEU v2.5.1"
        int created_by_user_id FK
        datetime created_at
        datetime updated_at
    }
    
    RAG_FEEDBACK {
        int id PK
        int chat_message_id FK "NEU v2.5.1"
        int user_id FK
        string rating
        text comment
        datetime submitted_at
        datetime created_at
    }
    
    RAG_AUDIT_LOGS {
        int id PK
        int indexed_document_id FK "NEU v2.5.1"
        string action
        int user_id FK
        datetime timestamp
        text details
        string status
        text error_message
        int duration_ms
        int tokens_used
        int cost_usd
        datetime created_at
    }
    
    TRAINING_SAMPLES {
        int id PK "NEU v2.7.0"
        text query
        text chunk_id
        text features_json
        real relevance_score
        text source
        int user_id FK
        int feedback_id
        text created_at
    }
    
    SHAP_BACKGROUND_DATA {
        int id PK "NEU v2.7.0"
        text query
        real vector_score
        real text_score
        int user_level
        int keyword_matches
        int chunk_length
        int heading_hierarchy_depth
        real confidence_score
        text created_at
    }
    
    SHAP_CACHE {
        int id PK "NEU v2.7.0"
        text cache_key UK
        text shap_values_json
        text created_at
        text expires_at
    }
```

---

## 📋 Tabellen-Details

### **Core System (5 Tabellen)**

#### **1. `users` - Benutzer**
Zentrale User-Tabelle für Authentifizierung und RBAC.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `email` | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | Email-Adresse (Login) |
| `full_name` | VARCHAR(200) | NOT NULL | Vollständiger Name |
| `employee_id` | VARCHAR(50) | UNIQUE | Mitarbeiter-ID |
| `organizational_unit` | VARCHAR(100) | - | Primäre Organisationseinheit |
| `hashed_password` | VARCHAR(255) | - | bcrypt-Hash |
| `individual_permissions` | TEXT | - | JSON-String mit Permissions |
| `is_qms_admin` | BOOLEAN | NOT NULL, DEFAULT FALSE | QMS-Administrator Flag |
| `cannot_be_deleted` | BOOLEAN | NOT NULL, DEFAULT FALSE | Schutz vor Löschung |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Soft-Delete Flag |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW | Erstellungsdatum |
| `updated_at` | DATETIME | NOT NULL, DEFAULT NOW | Letzte Änderung |

#### **2. `interest_groups` - Interessensgruppen**
13-Stakeholder-System für organisatorische Einheiten.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `name` | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | Name (z.B. "Team") |
| `code` | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Code (z.B. "team") |
| `description` | TEXT | - | Beschreibung |
| `group_permissions` | TEXT | - | JSON-String mit Permissions |
| `ai_functionality` | TEXT | - | Verfügbare KI-Funktionen |
| `typical_tasks` | TEXT | - | Typische Aufgaben |
| `is_external` | BOOLEAN | NOT NULL, DEFAULT FALSE | Intern/Extern |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Soft-Delete Flag |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW | Erstellungsdatum |
| `updated_at` | DATETIME | NOT NULL, DEFAULT NOW | Letzte Änderung |
| `created_by_id` | INTEGER | FK → users.id | Ersteller |

#### **3. `user_group_memberships` - Zuordnungen**
Many-to-Many Beziehung zwischen Users und Interest Groups.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `user_id` | INTEGER | FK → users.id, NOT NULL, INDEX | User-Referenz |
| `interest_group_id` | INTEGER | FK → interest_groups.id, NOT NULL, INDEX | Group-Referenz |
| `role_in_group` | VARCHAR(50) | - | Rolle (z.B. "Teamleiter") |
| `approval_level` | INTEGER | NOT NULL, DEFAULT 1 | **1-5** Permission Level |
| `is_department_head` | BOOLEAN | NOT NULL, DEFAULT FALSE | Abteilungsleiter-Flag |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Soft-Delete Flag |
| `joined_at` | DATETIME | NOT NULL, DEFAULT NOW | Beitrittsdatum |
| `updated_at` | DATETIME | NOT NULL, DEFAULT NOW | Letzte Änderung |
| `assigned_by_id` | INTEGER | FK → users.id | Wer hat zugeordnet |
| `notes` | TEXT | - | Bemerkungen |

#### **4. `document_types` - Dokumenttypen**
Verwaltung von Dokumenttypen mit AI-Anforderungen.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `name` | VARCHAR(100) | NOT NULL, INDEX | Name (z.B. "SOP") |
| `code` | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Code (z.B. "sop") |
| `description` | TEXT | - | Beschreibung |
| `allowed_file_types` | TEXT | NOT NULL | JSON-Array: ["pdf", "docx"] |
| `max_file_size_mb` | INTEGER | NOT NULL | Max. Dateigröße in MB |
| `requires_ocr` | BOOLEAN | NOT NULL, DEFAULT FALSE | OCR-Verarbeitung erforderlich |
| `requires_vision` | BOOLEAN | NOT NULL, DEFAULT FALSE | Vision-Analyse erforderlich |
| `default_prompt_template_id` | INTEGER | FK → prompt_templates.id | Standard-Prompt |
| `created_by` | INTEGER | FK → users.id | Ersteller |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Aktiv/Inaktiv |
| `sort_order` | INTEGER | NOT NULL, DEFAULT 0 | Sortierreihenfolge |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW | Erstellungsdatum |
| `updated_at` | DATETIME | NOT NULL, DEFAULT NOW | Letzte Änderung |

#### **5. `prompt_templates` - Prompt-Vorlagen**
AI-Prompt-Templates mit Versionierung und Status-Management.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `name` | VARCHAR(200) | UNIQUE, NOT NULL, INDEX | Template-Name |
| `description` | TEXT | - | Beschreibung |
| `prompt_text` | TEXT | NOT NULL | Der eigentliche Prompt |
| `system_instructions` | TEXT | - | System-Instruktionen |
| `document_type_id` | INTEGER | FK → document_types.id | Zugeordneter Dokumenttyp |
| `ai_model` | VARCHAR(100) | NOT NULL | AI-Model (gpt-4o-mini, gemini-2.5-flash) |
| `temperature` | INTEGER | NOT NULL | 0-100 (0.0-1.0 als Integer) |
| `max_tokens` | INTEGER | NOT NULL | Max. Token-Limit |
| `top_p` | INTEGER | NOT NULL | 0-100 (0.0-1.0 als Integer) |
| `detail_level` | VARCHAR(10) | NOT NULL | "low", "high" (für Vision-Models) |
| `status` | VARCHAR(20) | NOT NULL, INDEX | "draft", "active", "archived" |
| `version` | VARCHAR(20) | NOT NULL | Versionsnummer (v1.0, v1.1) |
| `tested_successfully` | BOOLEAN | NOT NULL, DEFAULT FALSE | Erfolgreich getestet |
| `success_count` | INTEGER | NOT NULL, DEFAULT 0 | Anzahl erfolgreicher Tests |
| `last_used_at` | DATETIME | - | Letzte Verwendung |
| `created_by` | INTEGER | FK → users.id | Ersteller |
| `tags` | TEXT | - | JSON-Array: ["ocr", "vision"] |
| `example_input` | TEXT | - | Beispiel-Eingabe |
| `example_output` | TEXT | - | Beispiel-Ausgabe |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW | Erstellungsdatum |
| `updated_at` | DATETIME | NOT NULL, DEFAULT NOW | Letzte Änderung |

---

### **Document Upload System (6 Tabellen)**

#### **6. `upload_documents` - Hochgeladene Dokumente**
Zentrale Tabelle für alle hochgeladenen Dokumente mit Workflow-Status.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `filename` | VARCHAR(255) | NOT NULL | System-Dateiname |
| `original_filename` | VARCHAR(255) | NOT NULL | Original-Dateiname |
| `file_size_bytes` | INTEGER | NOT NULL | Dateigröße in Bytes |
| `file_type` | VARCHAR(10) | NOT NULL | Dateityp (pdf, docx, png, jpg) |
| `document_type_id` | INTEGER | FK → document_types.id, NOT NULL | Dokumenttyp |
| `qm_chapter` | VARCHAR(50) | - | QM-Kapitel |
| `version` | VARCHAR(20) | NOT NULL | Dokumentversion |
| `page_count` | INTEGER | - | Anzahl Seiten |
| `uploaded_by_user_id` | INTEGER | FK → users.id, NOT NULL | Uploader |
| `uploaded_at` | DATETIME | NOT NULL | Upload-Zeitpunkt |
| `file_path` | VARCHAR(500) | NOT NULL | Pfad zur Datei |
| `processing_method` | VARCHAR(20) | NOT NULL | "ocr" oder "vision" |
| `processing_status` | VARCHAR(20) | NOT NULL | "pending", "processing", "completed", "failed" |
| `workflow_status` | VARCHAR(20) | NOT NULL | "draft", "reviewed", "approved", "rejected", "archived", "deleted" |
| `file_hash` | VARCHAR(64) | UNIQUE, INDEX, NULLABLE | **SHA-256 Hash (64 hex) für Duplikat-Prüfung - NEU v2.3** |
| `is_duplicate` | BOOLEAN | NOT NULL, DEFAULT FALSE, INDEX | **Flag: Ist Duplikat? - NEU v2.3** |
| `duplicate_of_document_id` | INTEGER | FK → upload_documents.id, NULLABLE, INDEX | **Link zum Original-Dokument - NEU v2.3** |
| `document_series_id` | INTEGER | FK → upload_documents.id, NULLABLE, INDEX | **ID der logischen Dokument-Serie - NEU v2.3** |
| `parent_document_id` | INTEGER | FK → upload_documents.id, NULLABLE, INDEX | **Vorgänger-Version (bei neuen Versionen) - NEU v2.3** |
| `is_current_version` | BOOLEAN | NOT NULL, DEFAULT TRUE, INDEX | **Aktuelle Version? (True bei Upload) - NEU v2.3** |
| `deleted_at` | DATETIME | NULLABLE, INDEX | **Zeitstempel der Soft Delete - NEU v2.3** |
| `deleted_by_user_id` | INTEGER | FK → users.id, NULLABLE, INDEX | **User ID des Löschers - NEU v2.3** |
| `deletion_reason` | TEXT | NULLABLE | **Grund für Löschung - NEU v2.3** |
| `archived_at` | DATETIME | NULLABLE, INDEX | **Zeitstempel der Archivierung - NEU v2.3** |
| `archived_by_user_id` | INTEGER | FK → users.id, NULLABLE, INDEX | **User ID des Archivierers - NEU v2.3** |
| `archive_reason` | TEXT | NULLABLE | **Grund für Archivierung - NEU v2.3** |

#### **7. `upload_document_pages` - Dokument-Seiten**
Einzelne Seiten eines Dokuments mit Preview-Bildern.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `upload_document_id` | INTEGER | FK → upload_documents.id, NOT NULL | Dokument-Referenz |
| `page_number` | INTEGER | NOT NULL | Seitennummer (1-basiert) |
| `preview_image_path` | VARCHAR(500) | NOT NULL | Pfad zum Preview-Bild |
| `thumbnail_path` | VARCHAR(500) | - | Pfad zum Thumbnail |
| `width` | INTEGER | - | Bildbreite in Pixel |
| `height` | INTEGER | - | Bildhöhe in Pixel |
| `created_at` | DATETIME | NOT NULL | Erstellungsdatum |

#### **8. `upload_document_interest_groups` - Dokument-Zuordnungen**
Zuordnung von Dokumenten zu Interest Groups.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `upload_document_id` | INTEGER | FK → upload_documents.id, NOT NULL | Dokument-Referenz |
| `interest_group_id` | INTEGER | FK → interest_groups.id, NOT NULL | Group-Referenz |
| `assigned_at` | DATETIME | NOT NULL | Zuordnungs-Zeitpunkt |
| `assigned_by_user_id` | INTEGER | FK → users.id, NOT NULL | Wer hat zugeordnet |

#### **9. `document_status_changes` - Workflow-Historie**
Audit-Trail für alle Workflow-Status-Änderungen.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `upload_document_id` | INTEGER | FK → upload_documents.id, NOT NULL | Dokument-Referenz |
| `from_status` | VARCHAR(20) | - | Vorheriger Status |
| `to_status` | VARCHAR(20) | NOT NULL | Neuer Status |
| `changed_by_user_id` | INTEGER | FK → users.id, NOT NULL | Wer hat geändert |
| `changed_at` | DATETIME | NOT NULL | Änderungs-Zeitpunkt |
| `change_reason` | TEXT | NOT NULL | Grund für Änderung |
| `comment` | TEXT | - | Zusätzlicher Kommentar |
| `created_at` | DATETIME | NOT NULL | Erstellungsdatum |

#### **10. `document_comments` - Dokument-Kommentare**
Kommentare zu Dokumenten oder spezifischen Seiten.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `upload_document_id` | INTEGER | FK → upload_documents.id, NOT NULL | Dokument-Referenz |
| `comment_text` | TEXT | NOT NULL | Kommentar-Text |
| `comment_type` | VARCHAR(20) | NOT NULL | "general", "review", "approval" |
| `page_number` | INTEGER | - | Seitennummer (falls seiten-spezifisch) |
| `created_by_user_id` | INTEGER | FK → users.id, NOT NULL | Kommentar-Ersteller |
| `created_at` | DATETIME | NOT NULL | Erstellungsdatum |
| `status_change_id` | INTEGER | FK → document_status_changes.id | Verknüpfung zu Status-Änderung |
| `updated_at` | DATETIME | NOT NULL | Letzte Änderung |

#### **11. `document_ai_responses` - AI-Verarbeitungsergebnisse**
Ergebnisse der AI-Verarbeitung von Dokument-Seiten.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `upload_document_id` | INTEGER | FK → upload_documents.id, NOT NULL | Dokument-Referenz |
| `upload_document_page_id` | INTEGER | FK → upload_document_pages.id, NOT NULL | Seiten-Referenz |
| `prompt_template_id` | INTEGER | FK → prompt_templates.id, NOT NULL | Verwendetes Template |
| `ai_model_id` | VARCHAR(100) | NOT NULL | AI-Model ID |
| `model_name` | VARCHAR(100) | NOT NULL | AI-Model Name |
| `json_response` | TEXT | NOT NULL | Strukturierte JSON-Antwort |
| `processing_status` | VARCHAR(20) | NOT NULL | "success", "failed", "pending" |
| `tokens_sent` | INTEGER | - | Verwendete Input-Tokens |
| `tokens_received` | INTEGER | - | Verwendete Output-Tokens |
| `total_tokens` | INTEGER | - | Gesamt-Tokens |
| `response_time_ms` | INTEGER | - | Antwortzeit in Millisekunden |
| `error_message` | TEXT | - | Fehlermeldung (falls fehlgeschlagen) |
| `processed_at` | DATETIME | NOT NULL | Verarbeitungs-Zeitpunkt |
| `created_at` | DATETIME | NOT NULL | Erstellungsdatum |
| `updated_at` | DATETIME | NOT NULL | Letzte Änderung |

---

### **RAG System (7 Tabellen)**

#### **12. `rag_indexed_documents` - Indexierte Dokumente**
Dokumente, die für das RAG-System indexiert wurden.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `upload_document_id` | INTEGER | FK → upload_documents.id, NOT NULL, UNIQUE | Dokument-Referenz |
| `qdrant_collection_name` | VARCHAR(100) | NOT NULL | Qdrant Collection Name |
| `total_chunks` | INTEGER | NOT NULL | Anzahl erstellter Chunks |
| `indexed_at` | DATETIME | NOT NULL | Indexierungs-Zeitpunkt |
| `last_updated_at` | DATETIME | NOT NULL | Letzte Aktualisierung |
| `embedding_model` | VARCHAR(100) | NOT NULL | Verwendetes Embedding-Model |

#### **13. `rag_document_chunks` - Dokument-Chunks**
Einzelne Text-Chunks für Vektor-Suche.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `rag_indexed_document_id` | INTEGER | FK → rag_indexed_documents.id, NOT NULL | Indexiertes Dokument |
| `chunk_id` | VARCHAR(100) | UNIQUE, NOT NULL | Eindeutige Chunk-ID |
| `chunk_text` | TEXT | NOT NULL | Text-Inhalt des Chunks |
| `page_number` | INTEGER | NOT NULL | Quell-Seitennummer |
| `paragraph_index` | INTEGER | - | Absatz-Index |
| `chunk_index` | INTEGER | NOT NULL | Chunk-Index innerhalb der Seite |
| `token_count` | INTEGER | - | Anzahl Tokens |
| `sentence_count` | INTEGER | - | Anzahl Sätze |
| `has_overlap` | BOOLEAN | NOT NULL, DEFAULT FALSE | Hat Überlappung (nur bei gesplitteten Chunks) |
| `overlap_sentence_count` | INTEGER | NOT NULL, DEFAULT 0 | Anzahl überlappender Sätze (0-10) |
| `qdrant_point_id` | VARCHAR(100) | - | Qdrant Point ID |
| `embedding_vector_preview` | TEXT | - | Preview der ersten 50 Dimensionen |
| `created_at` | DATETIME | NOT NULL | Erstellungsdatum |

#### **14. `rag_chat_sessions` - Chat-Sessions**
RAG-Chat-Sessions pro User.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `user_id` | INTEGER | FK → users.id, NOT NULL | User-Referenz |
| `session_name` | VARCHAR(255) | - | Session-Name |
| `created_at` | DATETIME | NOT NULL | Erstellungsdatum |
| `last_message_at` | DATETIME | - | Letzte Nachricht |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Session aktiv |

#### **15. `rag_chat_messages` - Chat-Nachrichten**
Einzelne Nachrichten in RAG-Chat-Sessions.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `session_id` | INTEGER | FK → rag_chat_sessions.id, NOT NULL | Session-Referenz |
| `role` | VARCHAR(20) | NOT NULL | "user" oder "assistant" |
| `content` | TEXT | NOT NULL | Nachrichten-Inhalt |
| `source_chunks` | TEXT | - | JSON-Array mit Quell-Chunk-IDs (SourceReferences) |
| `ai_model_used` | VARCHAR(100) | - | AI Model das für diese Nachricht verwendet wurde (z.B. 'gpt-4o-mini', 'gpt-5-mini', 'gemini-2.5-flash') |
| `message_metadata` | TEXT | - | JSON-Metadaten (prompt_text, tokens_used, query_params, processing_time_ms, embedding_provider, embedding_dimensions, generated_queries) - NEU v2.5.0 |
| `created_at` | DATETIME | NOT NULL | Erstellungsdatum |

#### **16. `rag_chat_prompts` - RAG Chat Prompts (NEU v2.5.1)**
Globale, dokumenttyp-spezifische RAG Chat Prompts. Level 4+ können diese anpassen.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `document_type_id` | INTEGER | FK → document_types.id, UNIQUE, NOT NULL | Dokumenttyp-Referenz (ein Prompt pro Dokumenttyp) |
| `prompt_text` | TEXT | NOT NULL, CHECK(LENGTH > 0) | RAG Chat Prompt-Text für diesen Dokumenttyp |
| `multi_query_prompt_text` | TEXT | - | Multi-Query Prompt-Text (optional, PHASE 2) |
| `created_by_user_id` | INTEGER | FK → users.id, NOT NULL | User ID des Erstellers (Audit-Trail) |
| `created_at` | DATETIME | NOT NULL | Erstellungsdatum |
| `updated_at` | DATETIME | NOT NULL | Letzte Änderung |

#### **17. `rag_feedback` - RAG Feedback (NEU v2.5.1)**
User Feedback zu RAG Chat-Antworten für Qualitätsverbesserung und Analytics.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `chat_message_id` | INTEGER | FK → rag_chat_messages.id, NOT NULL | Chat-Message-Referenz (Assistant-Message) |
| `user_id` | INTEGER | FK → users.id, NOT NULL | User der das Feedback gegeben hat |
| `rating` | VARCHAR(20) | NOT NULL, CHECK(rating IN ('positive', 'negative', 'neutral')) | Bewertung: 'positive', 'negative', 'neutral' |
| `comment` | TEXT | CHECK(LENGTH <= 2000) | Optionaler Kommentar (max 2000 Zeichen) |
| `submitted_at` | DATETIME | NOT NULL | Zeitstempel der Abgabe |
| `created_at` | DATETIME | NOT NULL | Erstellungsdatum |
| **Unique Constraint:** `(chat_message_id, user_id)` - Ein User kann nur einmal pro Message Feedback geben |

#### **18. `rag_audit_logs` - RAG Audit Logs (NEU v2.5.1)**
Vollständiger Audit-Trail für RAG-Operationen (Compliance und Transparenz).

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `indexed_document_id` | INTEGER | FK → rag_indexed_documents.id | Optional: Indexed Document-Referenz |
| `action` | VARCHAR(50) | NOT NULL | Aktion: 'chunking_started', 'indexing_completed', 'query_executed', 'feedback_submitted', etc. |
| `user_id` | INTEGER | FK → users.id, NOT NULL | User der die Aktion ausgeführt hat |
| `timestamp` | DATETIME | NOT NULL | Zeitstempel der Aktion |
| `details` | TEXT | NOT NULL | JSON-Details der Aktion |
| `status` | VARCHAR(20) | NOT NULL, CHECK(status IN ('success', 'failed', 'in_progress')) | Status: 'success', 'failed', 'in_progress' |
| `error_message` | TEXT | - | Fehlermeldung (falls status = 'failed') |
| `duration_ms` | INTEGER | - | Dauer der Aktion in Millisekunden |
| `tokens_used` | INTEGER | - | Anzahl verwendeter Tokens |
| `cost_usd` | INTEGER | - | Geschätzte Kosten in USD (Cents) |
| `created_at` | DATETIME | NOT NULL | Erstellungsdatum |

---

### **ML/SHAP System (3 Tabellen) - NEU v2.7.0**

#### **19. `training_samples` - ML Training-Daten (NEU v2.7.0)**
Training-Samples für ML-Modelle (Learning-to-Rank). Wird automatisch aus User-Feedback erstellt.

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `query` | TEXT | NOT NULL, INDEX | Die ursprüngliche Query |
| `chunk_id` | TEXT | NOT NULL | Chunk-ID (z.B. "doc_14_page_1_text") |
| `features_json` | TEXT | NOT NULL | Features als JSON-String (vector_score, text_score, bm25_score, jaccard_score, keyword_matches, chunk_length, document_type_encoded, heading_hierarchy_depth, confidence_score, user_level, hybrid_score) |
| `relevance_score` | REAL | NOT NULL | Relevance-Score (0.0-1.0) aus Feedback |
| `source` | TEXT | NOT NULL | Quelle: 'feedback', 'system', 'auto' |
| `user_id` | INTEGER | FK → users.id | Optional: User der das Feedback gab |
| `feedback_id` | INTEGER | - | Optional: Reference zu Feedback |
| `created_at` | TEXT | NOT NULL, INDEX | ISO-8601 Timestamp |

**Indizes:**
- `ix_training_samples_query` auf `query`
- `ix_training_samples_created_at` auf `created_at`

#### **20. `shap_background_data` - SHAP Background-Daten (NEU v2.7.0)**
Historische Search-Daten für SHAP-Background (Rolling Window, max 1000 Records).

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `query` | TEXT | NOT NULL | Search-Query |
| `vector_score` | REAL | - | Vektor-Score (0-1) |
| `text_score` | REAL | - | Text-Score (0-1) |
| `user_level` | INTEGER | - | User-Level (1-5) |
| `keyword_matches` | INTEGER | - | Anzahl Keyword-Matches |
| `chunk_length` | INTEGER | - | Chunk-Länge |
| `heading_hierarchy_depth` | INTEGER | - | Heading-Hierarchie-Tiefe |
| `confidence_score` | REAL | - | Confidence-Score (0-1) |
| `created_at` | TEXT | NOT NULL, INDEX | ISO-8601 Timestamp |

**Indizes:**
- `ix_shap_background_data_created_at` auf `created_at`

**Rolling Window:** Wenn > 1000 Records, werden älteste automatisch gelöscht.

#### **21. `shap_cache` - SHAP Cache (NEU v2.7.0)**
Gecachte SHAP-Erklärungen für Performance-Optimierung (LRU Cache mit TTL).

| Feld | Typ | Constraints | Beschreibung |
|------|-----|-------------|--------------|
| `id` | INTEGER | PK, AUTO | Primary Key |
| `cache_key` | TEXT | UNIQUE, NOT NULL | MD5 Hash von (query, features) |
| `shap_values_json` | TEXT | NOT NULL | SHAP-Erklärung als JSON-String |
| `created_at` | TEXT | NOT NULL | ISO-8601 Timestamp |
| `expires_at` | TEXT | NOT NULL, INDEX | ISO-8601 Timestamp (TTL: 1 Stunde) |

**Indizes:**
- `ix_shap_cache_cache_key` UNIQUE auf `cache_key`
- `ix_shap_cache_expires_at` auf `expires_at`

**LRU Cache:** Max 100 Einträge, älteste werden bei Überschreitung gelöscht.

---

## 🎯 Permission Levels (1-5)

Basierend auf dem QMS-System:

| Level | Name | Rechte | Beispiel |
|-------|------|--------|----------|
| **L1** | Mitarbeiter | Lesen, Vorschlagen | Normaler Mitarbeiter |
| **L2** | Teamleiter | L1 + Team-Freigabe | Team Lead |
| **L3** | Abteilungsleiter | L2 + Abteilungs-Freigabe | Department Head |
| **L4** | QM-Manager | L3 + QM-Freigabe | QM-Bereich Verantwortlicher |
| **L5** | System-Admin / QM-Leitung | Alles | QMS-Admin, Vollzugriff |

---

## 🔄 Workflow-Status

### **Document Upload Workflow:**
1. **`draft`** → Dokument hochgeladen, noch nicht bearbeitet
2. **`reviewed`** → Dokument wurde geprüft (Level 2-3)
3. **`approved`** → Dokument wurde freigegeben (Level 4-5)
4. **`rejected`** → Dokument wurde abgelehnt
5. **`deleted`** → Dokument wurde soft-deleted (Archiv) - NEU v2.3

### **Processing Status:**
1. **`pending`** → Wartet auf Verarbeitung
2. **`processing`** → Wird gerade verarbeitet
3. **`completed`** → Verarbeitung abgeschlossen
4. **`failed`** → Verarbeitung fehlgeschlagen

---

## 📊 Aktuelle Statistiken

**Tabellen:** 18 (Core: 5 + Document Upload: 6 + RAG: 7)  
**Relationships:** 30+  
**Indexes:** 60+  
**Foreign Keys:** 25+  
**Triggers:** 8  
**Views:** 2  
**Standard-Daten:** 13 Interest Groups, 7 Document Types, 1 QMS Admin User, 3 Prompt Templates

**System-Status:**
- ✅ **Core System:** Vollständig implementiert
- ✅ **Document Upload:** Vollständig implementiert mit Workflow
- ✅ **RAG Integration:** Vollständig implementiert
- ✅ **AI Processing:** Vollständig implementiert
- ✅ **Permission System:** Vollständig implementiert

**Letzte Änderung:** 2025-11-11 (RAG Chat Prompts, Feedback, Audit Logs, Message Metadata - v2.5.1)

---

## 🔄 **SCHEMA-SYNC UPDATE (2025-10-28)**

**Wichtige Änderungen:** Backend-Code wurde an das tatsächliche DB-Schema angepasst:

### **rag_chat_sessions**
- ✅ `session_name` ist jetzt `nullable=True` (VARCHAR(255))
- ✅ `last_activity` → `last_message_at` (nullable=True)
- ✅ `message_count` wird als Property berechnet
- ✅ `is_active` Spalte hinzugefügt

### **rag_chat_messages**
- ✅ `chat_session_id` → `session_id`
- ✅ `source_references` JSON → `source_chunks` TEXT
- ✅ `ai_model_used` VARCHAR(100) hinzugefügt (Trackt welches AI-Model verwendet wurde: gpt-4o-mini, gpt-5-mini, gemini-2.5-flash)
- ✅ `message_metadata` TEXT hinzugefügt (v2.5.0) - JSON mit prompt_text, tokens_used, query_params, processing_time_ms, embedding_provider, embedding_dimensions
- ✅ `structured_data` wird als Property berechnet

### **rag_indexed_documents**
- ✅ `document_title`, `document_type`, `status` werden als Properties berechnet
- ✅ `qdrant_collection_name` und `embedding_model` hinzugefügt

### **rag_document_chunks**
- ✅ `indexed_document_id` → `rag_indexed_document_id`
- ✅ `page_numbers` JSON → `page_number` INTEGER
- ✅ Zusätzliche Spalten: `sentence_count`, `has_overlap`, `overlap_sentence_count`, `qdrant_point_id`
- ✅ **Overlap-Felder (v2.5.0):** `has_overlap` BOOLEAN, `overlap_sentence_count` INTEGER (für Chunk-Split mit Overlap)

**Status:** ✅ **SCHEMA-SYNC ABGESCHLOSSEN** - Backend und DB sind jetzt synchron!

---

## 🎯 Datenbank-Pfad und Initialisierung

**Wichtiger Hinweis:** Die Datenbank befindet sich unter:
```
/Users/reiner/Documents/DocuMind-AI-V2/data/qms.db
```

Dieser Pfad ist fest in der Konfiguration definiert und sollte nicht geändert werden.

### **Initialisierung der Datenbank**

**NEU:** Ab Version 2.1.0 gibt es ein komplettes Initialisierungs-Script, das alle Migration-Scripts ersetzt:

```bash
# Komplette Datenbank-Initialisierung
cd backend
python3 init_database.py

# Mit Force-Flag (ohne Bestätigung)
python3 init_database.py --force
```

**Das Script erstellt:**
- ✅ Alle 18 Tabellen (Core: 5 + Document Upload: 6 + RAG: 7)

**Hinweis:** Die 3 ML/SHAP-Tabellen (v2.7.0) werden separat mit `backend/app/migrations/add_ml_shap_tables.py` erstellt.
- ✅ 30+ Indizes für optimale Performance
- ✅ 20+ Foreign Key Constraints
- ✅ 6 Trigger für automatische Updates
- ✅ 2 Views für komplexe Queries
- ✅ Standard-Seed-Daten (13 Interest Groups, 7 Document Types, 1 QMS Admin)
- ✅ SQLite-Optimierungen
- ✅ Automatisches Backup der bestehenden Datenbank

**Migration-Scripts:** Die alten Migration-Scripts in `backend/migrations/` sind nicht mehr notwendig und können entfernt werden.