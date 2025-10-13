# 🗺️ Roadmap: Document Upload System

> **Feature Branch:** `feature/document-upload-system`  
> **Start Date:** 2025-10-13  
> **Target:** Vollständiges QMS Document Management mit RAG Integration

---

## 🎯 OVERVIEW

Dieses Feature fügt 3 neue Bounded Contexts hinzu:

1. **documentupload** - File Upload, Preview Generation, Metadata Management
2. **documentworkflow** - Review → Approval Workflow, Audit Trail
3. **ragintegration** - RAG Chat, Vector Store (Qdrant), OCR/Vision Processing

---

## 📋 PHASE 1: FOUNDATION (Woche 1-2)

### 1.1 Context-Struktur erstellen

- [ ] Verzeichnisse anlegen:
  - [ ] `contexts/documentupload/{domain,application,infrastructure,interface}`
  - [ ] `contexts/documentworkflow/{domain,application,infrastructure,interface}`
  - [ ] `contexts/ragintegration/{domain,application,infrastructure,interface}`
- [ ] `__init__.py` Dateien erstellen
- [ ] Context-READMEs schreiben:
  - [ ] `contexts/documentupload/README.md`
  - [ ] `contexts/documentworkflow/README.md`
  - [ ] `contexts/ragintegration/README.md`

### 1.2 Database Schema Design

- [ ] Migration Script erstellen (`backend/migrations/`)
- [ ] Tabellen anlegen:
  - [ ] `upload_documents`
  - [ ] `upload_document_pages`
  - [ ] `upload_document_interest_groups`
  - [ ] `workflow_documents`
  - [ ] `workflow_audit_log`
  - [ ] `rag_indexed_documents`
  - [ ] `rag_document_chunks`
  - [ ] `rag_chat_sessions`
  - [ ] `rag_chat_messages`
- [ ] Seed Data für Tests erstellen
- [ ] Update `docs/database-schema.md`

### 1.3 Dependencies installieren

- [ ] Backend:
  - [ ] `PyPDF2` - PDF Manipulation
  - [ ] `pdf2image` - PDF → Bilder
  - [ ] `Pillow` - Image Processing
  - [ ] `python-docx` - DOCX Support
  - [ ] `pytesseract` - OCR (lokal)
  - [ ] `qdrant-client` - Vector Database
  - [ ] `celery` - Async Task Processing
  - [ ] `redis` - Celery Broker
  - [ ] `sentence-transformers` - Embeddings (optional)
- [ ] Frontend:
  - [ ] `react-dropzone` - Drag & Drop
  - [ ] `react-pdf` - PDF Preview
  - [ ] `react-image-gallery` - Image Preview
  - [ ] `react-beautiful-dnd` - Kanban Drag & Drop
  - [ ] `react-markdown` - Markdown Rendering

### 1.4 Dokumentation

- [ ] Update `PROJECT_RULES.md` (neue Contexts)
- [ ] Update `docs/architecture.md` (neue Contexts)
- [ ] Update `.cursorrules` (neue Contexts)
- [ ] Erstelle `docs/user-manual/` Struktur

---

## 📋 PHASE 2: DOCUMENT UPLOAD (Woche 2-3)

### 2.1 Backend: Domain Layer

- [ ] **Entities** (`domain/entities.py`):
  - [ ] `UploadedDocument`
  - [ ] `DocumentPage`
  - [ ] `InterestGroupAssignment`
- [ ] **Value Objects** (`domain/value_objects.py`):
  - [ ] `ProcessingMethod` (OCR, Vision)
  - [ ] `FileType` (PDF, DOCX, PNG, JPG)
  - [ ] `ProcessingStatus` (pending, processing, completed, failed)
  - [ ] `QMChapter`
  - [ ] `DocumentVersion`
- [ ] **Repository Interfaces** (`domain/repositories.py`):
  - [ ] `UploadRepository`
  - [ ] `DocumentPageRepository`
- [ ] **Domain Events** (`domain/events.py`):
  - [ ] `DocumentUploadedEvent`
  - [ ] `PagesGeneratedEvent`
  - [ ] `InterestGroupsAssignedEvent`
- [ ] **Tests** (`tests/unit/documentupload/test_entities.py`)

### 2.2 Backend: Application Layer

- [ ] **Use Cases** (`application/use_cases.py`):
  - [ ] `UploadDocumentUseCase` (TDD)
  - [ ] `GeneratePreviewUseCase` (TDD)
  - [ ] `AssignInterestGroupsUseCase` (TDD)
  - [ ] `GetUploadDetailsUseCase` (TDD)
- [ ] **Services** (`application/services.py`):
  - [ ] `PageSplitterService`
  - [ ] `PreviewGeneratorService`
  - [ ] `FileValidationService`
- [ ] **Tests** (`tests/unit/documentupload/test_use_cases.py`)

### 2.3 Backend: Infrastructure Layer

- [ ] **Repositories** (`infrastructure/repositories.py`):
  - [ ] `SQLAlchemyUploadRepository`
  - [ ] `SQLAlchemyDocumentPageRepository`
- [ ] **File Storage** (`infrastructure/file_storage.py`):
  - [ ] `LocalFileStorageService`
  - [ ] Verzeichnisstruktur: `/data/uploads/{documents,previews}`
- [ ] **PDF Processing** (`infrastructure/pdf_splitter.py`):
  - [ ] PDF → Einzelseiten (PyPDF2)
  - [ ] PDF → Bilder (pdf2image)
- [ ] **Image Processing** (`infrastructure/image_processor.py`):
  - [ ] Thumbnail-Generierung (Pillow)
  - [ ] Auto-Rotation (Pillow)
  - [ ] Quality Check
- [ ] **DOCX Processing** (`infrastructure/docx_processor.py`):
  - [ ] DOCX → PDF Konvertierung
- [ ] **Mappers** (`infrastructure/mappers.py`):
  - [ ] `UploadDocumentMapper`
  - [ ] `DocumentPageMapper`
- [ ] **Tests** (`tests/integration/documentupload/test_repositories.py`)

### 2.4 Backend: Interface Layer

- [ ] **Schemas** (`interface/schemas.py`):
  - [ ] `UploadDocumentRequest`
  - [ ] `UploadDocumentResponse`
  - [ ] `DocumentPageResponse`
  - [ ] `AssignInterestGroupsRequest`
- [ ] **Router** (`interface/router.py`):
  - [ ] `POST /api/uploads` - Upload + Metadata
  - [ ] `GET /api/uploads` - Liste aller Uploads (mit Filter)
  - [ ] `GET /api/uploads/{id}` - Upload Details
  - [ ] `GET /api/uploads/{id}/preview/{page}` - Preview-Bild
  - [ ] `POST /api/uploads/{id}/interest-groups` - Assign Groups
  - [ ] `DELETE /api/uploads/{id}` - Upload löschen (Soft Delete)
- [ ] **Tests** (`tests/e2e/test_upload_api.py`)
- [ ] Router in `backend/app/main.py` registrieren

### 2.5 Frontend: API Integration

- [ ] **Types** (`frontend/types/documentUpload.ts`):
  - [ ] `UploadedDocument`
  - [ ] `DocumentPage`
  - [ ] `UploadRequest`
- [ ] **API Client** (`frontend/lib/api/documentUpload.ts`):
  - [ ] `uploadDocument()`
  - [ ] `getUploadDetails()`
  - [ ] `getPreviewImage()`
  - [ ] `assignInterestGroups()`

### 2.6 Frontend: Upload Wizard

- [ ] **Page** (`frontend/app/document-upload/page.tsx`):
  - [ ] Step 1: File Upload + Dokumenttyp (Drag & Drop)
    - [ ] Drag & Drop Zone (react-dropzone)
    - [ ] Dokumenttyp-Karten (Drag & Drop)
    - [ ] File Validation (Größe, Typ)
  - [ ] Step 2: Metadaten
    - [ ] Dokumentname Input
    - [ ] QM-Kapitel Dropdown
    - [ ] Version Input (Auto-Increment Vorschlag)
  - [ ] Step 3: Interest Groups
    - [ ] Drag & Drop Interest Group Cards
    - [ ] Zugewiesene Gruppen Liste
  - [ ] Step 4: Preview + Upload
    - [ ] Seiten-Thumbnails
    - [ ] Vollbild-Preview Modal
    - [ ] Upload-Button
    - [ ] Progress Bar
- [ ] **Components**:
  - [ ] `DocumentTypeCard.tsx`
  - [ ] `InterestGroupCard.tsx`
  - [ ] `PagePreview.tsx`
  - [ ] `UploadProgress.tsx`
- [ ] Navigation-Link hinzufügen (`/document-upload`)

---

## 📋 PHASE 3: DOCUMENT WORKFLOW (Woche 3-4)

### 3.1 Backend: Domain Layer

- [ ] **Entities** (`domain/entities.py`):
  - [ ] `WorkflowDocument`
  - [ ] `AuditLogEntry`
  - [ ] `ReviewComment`
- [ ] **Value Objects** (`domain/value_objects.py`):
  - [ ] `DocumentStatus` (uploaded, reviewed, approved, rejected)
  - [ ] `WorkflowAction` (review, approve, reject, comment)
- [ ] **Repository Interfaces** (`domain/repositories.py`):
  - [ ] `WorkflowRepository`
  - [ ] `AuditLogRepository`
- [ ] **Policies** (`domain/policies.py`):
  - [ ] `PermissionPolicy` (wer darf was?)
    - [ ] Level 2: Dokumente ansehen
    - [ ] Level 3: Prüfen + Kommentieren
    - [ ] Level 4: Freigeben
- [ ] **Domain Events** (`domain/events.py`):
  - [ ] `DocumentReviewedEvent`
  - [ ] `DocumentApprovedEvent`
  - [ ] `DocumentRejectedEvent`
  - [ ] `CommentAddedEvent`
- [ ] **Tests** (`tests/unit/documentworkflow/test_entities.py`)

### 3.2 Backend: Application Layer

- [ ] **Use Cases** (`application/use_cases.py`):
  - [ ] `ReviewDocumentUseCase` (Level 3) - TDD
  - [ ] `ApproveDocumentUseCase` (Level 4) - TDD
  - [ ] `RejectDocumentUseCase` - TDD
  - [ ] `AddCommentUseCase` - TDD
  - [ ] `GetWorkflowDocumentsUseCase` (mit Filter) - TDD
  - [ ] `GetAuditLogUseCase` - TDD
- [ ] **Event Handlers** (`application/event_handlers.py`):
  - [ ] `DocumentUploadedEventHandler` (erstellt Workflow-Entry)
- [ ] **Services** (`application/services.py`):
  - [ ] `NotificationService` (Email/Slack bei Status-Änderung)
  - [ ] `AuditLogService`
- [ ] **Tests** (`tests/unit/documentworkflow/test_use_cases.py`)

### 3.3 Backend: Infrastructure Layer

- [ ] **Repositories** (`infrastructure/repositories.py`):
  - [ ] `SQLAlchemyWorkflowRepository`
  - [ ] `SQLAlchemyAuditLogRepository`
- [ ] **Notification Adapter** (`infrastructure/notification_adapter.py`):
  - [ ] Email-Versand (SMTP)
  - [ ] Slack-Integration (optional)
- [ ] **Mappers** (`infrastructure/mappers.py`):
  - [ ] `WorkflowDocumentMapper`
  - [ ] `AuditLogEntryMapper`
- [ ] **Tests** (`tests/integration/documentworkflow/test_repositories.py`)

### 3.4 Backend: Interface Layer

- [ ] **Schemas** (`interface/schemas.py`):
  - [ ] `WorkflowDocumentResponse`
  - [ ] `ReviewRequest`
  - [ ] `ApprovalRequest`
  - [ ] `RejectionRequest`
  - [ ] `CommentRequest`
  - [ ] `AuditLogEntryResponse`
- [ ] **Router** (`interface/router.py`):
  - [ ] `GET /api/workflow/documents` - Liste (Filter: status, interest_group)
  - [ ] `GET /api/workflow/documents/{id}` - Details
  - [ ] `POST /api/workflow/documents/{id}/review` - Prüfen (Level 3)
  - [ ] `POST /api/workflow/documents/{id}/approve` - Freigeben (Level 4)
  - [ ] `POST /api/workflow/documents/{id}/reject` - Ablehnen
  - [ ] `POST /api/workflow/documents/{id}/comment` - Kommentar hinzufügen
  - [ ] `GET /api/workflow/documents/{id}/audit-log` - Audit Trail
- [ ] **Tests** (`tests/e2e/test_workflow_api.py`)
- [ ] Router in `backend/app/main.py` registrieren

### 3.5 Frontend: API Integration

- [ ] **Types** (`frontend/types/documentWorkflow.ts`):
  - [ ] `WorkflowDocument`
  - [ ] `AuditLogEntry`
  - [ ] `ReviewRequest`
- [ ] **API Client** (`frontend/lib/api/documentWorkflow.ts`):
  - [ ] `getWorkflowDocuments()`
  - [ ] `reviewDocument()`
  - [ ] `approveDocument()`
  - [ ] `rejectDocument()`
  - [ ] `addComment()`
  - [ ] `getAuditLog()`

### 3.6 Frontend: Document Management

- [ ] **Page** (`frontend/app/document-management/page.tsx`):
  - [ ] Kanban-Board (3 Spalten):
    - [ ] Spalte 1: Hochgeladen
    - [ ] Spalte 2: Geprüft
    - [ ] Spalte 3: Freigegeben
  - [ ] Filter:
    - [ ] Nach Status
    - [ ] Nach Interest Group
    - [ ] Nach Dokumenttyp
    - [ ] Nach Uploader
  - [ ] Search Bar
- [ ] **Components**:
  - [ ] `DocumentCard.tsx` (Kanban-Karte)
  - [ ] `DocumentViewer.tsx` (Seiten-Navigation)
  - [ ] `ReviewModal.tsx` (Level 3)
  - [ ] `ApprovalModal.tsx` (Level 4)
  - [ ] `RejectionModal.tsx`
  - [ ] `CommentSection.tsx`
  - [ ] `AuditLogViewer.tsx`
- [ ] Navigation-Link hinzufügen (`/document-management`)

---

## 📋 PHASE 4: RAG INTEGRATION (Woche 4-6)

### 4.1 Qdrant Setup

- [ ] Qdrant Docker Container (später)
- [ ] Qdrant Python Client (lokal für Tests)
- [ ] Collection erstellen: `qms_documents`
- [ ] Index-Konfiguration:
  - [ ] Vector Size: 1536 (OpenAI text-embedding-3-small)
  - [ ] Distance Metric: Cosine
  - [ ] Payload Schema (Metadaten)

### 4.2 Backend: Domain Layer

- [ ] **Entities** (`domain/entities.py`):
  - [ ] `IndexedDocument`
  - [ ] `DocumentChunk`
  - [ ] `ChatSession`
  - [ ] `ChatMessage`
- [ ] **Value Objects** (`domain/value_objects.py`):
  - [ ] `EmbeddingVector`
  - [ ] `SearchQuery`
  - [ ] `ChunkMetadata`
- [ ] **Repository Interfaces** (`domain/repositories.py`):
  - [ ] `VectorStoreRepository`
  - [ ] `ChatSessionRepository`
- [ ] **Services** (`domain/services.py`):
  - [ ] `RAGService` (Interface)
  - [ ] `ChunkingService` (Interface)
  - [ ] `EmbeddingService` (Interface)
  - [ ] `OCRService` (Interface)
  - [ ] `VisionService` (Interface)
- [ ] **Domain Events** (`domain/events.py`):
  - [ ] `DocumentIndexedEvent`
  - [ ] `ChunkCreatedEvent`
- [ ] **Tests** (`tests/unit/ragintegration/test_entities.py`)

### 4.3 Backend: Application Layer

- [ ] **Use Cases** (`application/use_cases.py`):
  - [ ] `IndexDocumentUseCase` - TDD
  - [ ] `SearchDocumentsUseCase` - TDD
  - [ ] `AskQuestionUseCase` (RAG Chat) - TDD
  - [ ] `CreateChatSessionUseCase` - TDD
  - [ ] `GetChatHistoryUseCase` - TDD
- [ ] **Event Handlers** (`application/event_handlers.py`):
  - [ ] `DocumentApprovedEventHandler` (startet Indexierung)
- [ ] **Services** (`application/services.py`):
  - [ ] `AuditCompliantChunkingService` (Absatz + Satz-Überlappung)
  - [ ] `HybridSearchService` (Keyword + Semantic)
- [ ] **Tests** (`tests/unit/ragintegration/test_use_cases.py`)

### 4.4 Backend: Infrastructure Layer

- [ ] **Repositories** (`infrastructure/repositories.py`):
  - [ ] `QdrantVectorStoreRepository`
  - [ ] `SQLAlchemyChatSessionRepository`
- [ ] **OCR Adapter** (`infrastructure/ocr_adapter.py`):
  - [ ] Tesseract Integration (lokal)
  - [ ] Google Vision API (optional)
- [ ] **Vision Adapter** (`infrastructure/vision_adapter.py`):
  - [ ] GPT-4o Vision Integration
  - [ ] Gemini Vision Integration
- [ ] **Embedding Adapter** (`infrastructure/embedding_adapter.py`):
  - [ ] OpenAI Embeddings (text-embedding-3-small)
  - [ ] Sentence Transformers (optional, lokal)
- [ ] **Chunking Strategy** (`infrastructure/chunking_strategy.py`):
  - [ ] `AuditCompliantChunkingStrategy`
  - [ ] Absatz-basiert mit Satz-Überlappung
  - [ ] Max 512 Tokens, 2 Sätze Überlappung
- [ ] **Job Queue** (`infrastructure/jobs/`):
  - [ ] Celery Setup (später)
  - [ ] `ProcessDocumentJob` (OCR/Vision)
  - [ ] `IndexDocumentJob` (Chunking + Embedding)
- [ ] **Mappers** (`infrastructure/mappers.py`):
  - [ ] `IndexedDocumentMapper`
  - [ ] `DocumentChunkMapper`
  - [ ] `ChatSessionMapper`
- [ ] **Tests** (`tests/integration/ragintegration/test_repositories.py`)

### 4.5 Backend: Interface Layer

- [ ] **Schemas** (`interface/schemas.py`):
  - [ ] `ChatRequest`
  - [ ] `ChatResponse`
  - [ ] `SearchRequest`
  - [ ] `SearchResult`
  - [ ] `ChatSessionResponse`
  - [ ] `ChatMessageResponse`
- [ ] **Router** (`interface/router.py`):
  - [ ] `POST /api/rag/chat` - Chat-Nachricht senden
  - [ ] `GET /api/rag/sessions` - Chat-Sessions
  - [ ] `GET /api/rag/sessions/{id}` - Chat-History
  - [ ] `POST /api/rag/sessions` - Neue Session
  - [ ] `DELETE /api/rag/sessions/{id}` - Session löschen
  - [ ] `GET /api/rag/search` - Direkte Suche (ohne Chat)
- [ ] **Tests** (`tests/e2e/test_rag_api.py`)
- [ ] Router in `backend/app/main.py` registrieren

### 4.6 Frontend: API Integration

- [ ] **Types** (`frontend/types/ragChat.ts`):
  - [ ] `ChatSession`
  - [ ] `ChatMessage`
  - [ ] `SearchResult`
  - [ ] `DocumentChunk`
- [ ] **API Client** (`frontend/lib/api/ragChat.ts`):
  - [ ] `sendChatMessage()`
  - [ ] `getChatSessions()`
  - [ ] `getChatHistory()`
  - [ ] `createChatSession()`
  - [ ] `searchDocuments()`

### 4.7 Frontend: RAG Chat Interface

- [ ] **Page** (`frontend/app/rag-chat/page.tsx`):
  - [ ] Chat-Fenster:
    - [ ] Nachrichtenverlauf
    - [ ] Input-Feld
    - [ ] Send-Button
    - [ ] Typing Indicator
  - [ ] Sidebar:
    - [ ] Chat-Sessions Liste
    - [ ] Neue Session Button
    - [ ] Filter nach Interest Groups (Level 1)
  - [ ] Source-Links:
    - [ ] Dokument-Titel
    - [ ] Seite + Absatz
    - [ ] Confidence Score
    - [ ] "Dokument öffnen" Button
- [ ] **Components**:
  - [ ] `ChatWindow.tsx`
  - [ ] `ChatMessage.tsx` (User vs. Assistant)
  - [ ] `SourceLink.tsx`
  - [ ] `DocumentViewer.tsx` (Integration aus Workflow)
  - [ ] `SearchBar.tsx` (alternative zu Chat)
- [ ] Navigation-Link hinzufügen (`/rag-chat`)

---

## 📋 PHASE 5: ADVANCED FEATURES (Woche 6+)

### 5.1 Batch Upload

- [ ] Backend:
  - [ ] `POST /api/uploads/batch` - Multi-File Upload
  - [ ] Bulk Metadata Assignment
  - [ ] Progress Tracking
- [ ] Frontend:
  - [ ] Multi-File Drag & Drop
  - [ ] Bulk Metadata Form
  - [ ] Progress Bar mit ETA

### 5.2 Version Management

- [ ] Backend:
  - [ ] `upload_document_versions` Tabelle
  - [ ] `POST /api/uploads/{id}/versions` - Neue Version hochladen
  - [ ] `GET /api/uploads/{id}/versions` - Version History
  - [ ] `GET /api/uploads/{id}/versions/{v1}/diff/{v2}` - Diff
- [ ] Frontend:
  - [ ] Version History Viewer
  - [ ] Diff-View (Side-by-Side)
  - [ ] Rollback-Button

### 5.3 Smart Preview

- [ ] Backend:
  - [ ] AI-powered Thumbnail Highlights
  - [ ] Auto-Rotation für schräge Scans
  - [ ] Quality Check (Warnung bei unlesbaren Seiten)
- [ ] Frontend:
  - [ ] Highlighted Thumbnails
  - [ ] Quality Warnings

### 5.4 RAG Enhancements

- [ ] Hybrid Search (Keyword + Semantic)
- [ ] Multi-Document Answers (aus 3+ Quellen)
- [ ] Confidence Score Tuning
- [ ] Filter nach Interest Groups im Chat
- [ ] Export Chat History (PDF)

### 5.5 Analytics & Monitoring

- [ ] Backend:
  - [ ] Upload-Statistiken (Anzahl, Größe, Typen)
  - [ ] Workflow-Metriken (Durchlaufzeiten)
  - [ ] RAG-Qualitäts-Metriken (Antwort-Relevanz)
  - [ ] `GET /api/analytics/uploads`
  - [ ] `GET /api/analytics/workflow`
  - [ ] `GET /api/analytics/rag`
- [ ] Frontend:
  - [ ] Dashboard mit Charts
  - [ ] Export als CSV/PDF

---

## 📚 DOKUMENTATION

### Während der Entwicklung (kontinuierlich):

- [ ] Update `PROJECT_RULES.md` bei jedem neuen Context
- [ ] Update `docs/architecture.md` bei Architektur-Änderungen
- [ ] Update `docs/database-schema.md` bei neuen Tabellen
- [ ] Update `.cursorrules` bei neuen Regeln
- [ ] Context-READMEs aktuell halten

### Am Ende jeder Phase:

- [ ] Phase 1: Foundation dokumentieren
- [ ] Phase 2: Upload-Workflow dokumentieren
- [ ] Phase 3: Workflow-Prozess dokumentieren
- [ ] Phase 4: RAG-System dokumentieren
- [ ] Phase 5: Advanced Features dokumentieren

### User Manuals:

- [ ] `docs/user-manual/01-upload.md` - Dokument hochladen
- [ ] `docs/user-manual/02-workflow.md` - Prüfen & Freigeben
- [ ] `docs/user-manual/03-rag-chat.md` - RAG Chat nutzen
- [ ] `docs/user-manual/04-search.md` - Dokumente suchen

### Admin Manuals:

- [ ] `docs/admin-manual/01-setup.md` - System-Setup
- [ ] `docs/admin-manual/02-qdrant.md` - Qdrant-Konfiguration
- [ ] `docs/admin-manual/03-celery.md` - Job Queue
- [ ] `docs/admin-manual/04-monitoring.md` - Monitoring & Logs

---

## 🧪 TESTING

### Test Coverage Ziele:

- [ ] Domain Layer: 100% (TDD)
- [ ] Application Layer: 100% (TDD)
- [ ] Infrastructure Layer: 80%
- [ ] Interface Layer: 80%
- [ ] E2E Tests: Kritische Workflows

### Test-Suites:

- [ ] Unit Tests: `tests/unit/`
- [ ] Integration Tests: `tests/integration/`
- [ ] E2E Tests: `tests/e2e/`

---

## 🚀 DEPLOYMENT

### Docker Integration (später):

- [ ] `docker-compose.yml` erweitern:
  - [ ] Qdrant Service
  - [ ] Redis Service
  - [ ] Celery Worker Service
- [ ] Environment Variables:
  - [ ] `QDRANT_URL`
  - [ ] `REDIS_URL`
  - [ ] `OCR_API_KEY` (optional)
  - [ ] `VISION_API_KEY`
- [ ] Volumes:
  - [ ] `/data/uploads`
  - [ ] `/data/qdrant`

---

## ✅ COMPLETION CRITERIA

### Phase 1: Foundation
- [ ] Alle Tabellen erstellt
- [ ] Context-Struktur vollständig
- [ ] Dependencies installiert
- [ ] Dokumentation aktualisiert

### Phase 2: Document Upload
- [ ] Upload funktioniert (PDF, DOCX, PNG, JPG)
- [ ] Preview-Generierung funktioniert
- [ ] Interest Groups Assignment funktioniert
- [ ] Frontend: Upload Wizard vollständig
- [ ] Tests: 100% Coverage (Domain + Application)

### Phase 3: Document Workflow
- [ ] Review-Prozess funktioniert (Level 3)
- [ ] Approval-Prozess funktioniert (Level 4)
- [ ] Audit-Trail vollständig
- [ ] Frontend: Kanban-Board funktioniert
- [ ] Tests: 100% Coverage (Domain + Application)

### Phase 4: RAG Integration
- [ ] OCR/Vision Processing funktioniert
- [ ] Chunking funktioniert (Audit-Compliant)
- [ ] Qdrant Indexierung funktioniert
- [ ] RAG Chat funktioniert
- [ ] Frontend: Chat-Interface vollständig
- [ ] Tests: 100% Coverage (Domain + Application)

### Phase 5: Advanced Features
- [ ] Batch Upload funktioniert
- [ ] Version Management funktioniert
- [ ] Smart Preview funktioniert
- [ ] RAG Enhancements funktionieren
- [ ] Analytics Dashboard funktioniert

---

## 📊 PROGRESS TRACKING

**Gesamtfortschritt:** 0% (0/150+ Tasks)

- **Phase 1:** 0% (0/20 Tasks)
- **Phase 2:** 0% (0/40 Tasks)
- **Phase 3:** 0% (0/35 Tasks)
- **Phase 4:** 0% (0/40 Tasks)
- **Phase 5:** 0% (0/15 Tasks)

---

**Last Updated:** 2025-10-13  
**Branch:** `feature/document-upload-system`  
**Status:** 🚀 Ready to Start Phase 1

