# DocuMind-AI V2

> **Clean DDD Architecture** for Quality Management Systems (QMS)  
> **Version:** 2.5.1  
> **Status:** ✅ **PRODUCTION READY** (2025-11-12)

Modern, Domain-Driven Design implementation of DocuMind-AI with focus on:
- 🏗️ **Hexagonal Architecture** (Ports & Adapters)
- 👥 **RBAC Multi-Level** (Role-Based Access Control mit Interest Group-spezifischen Berechtigungen)
  - ⭐ **5-Stufen-System:** Level 1 (Mitarbeiter) bis Level 5 (QMS Admin)
  - ⭐ **Context-Specific Permissions:** Dokument-Aktionen basierend auf IG-Level
  - ⭐ **Interest Group Filtering:** Level 1-3 sehen nur relevante Dokumente
  - ⭐ **Multi-Level Support:** User mit unterschiedlichen Levels pro Interest Group
- 🏢 **Interest Groups** (Stakeholder System)
- 🤖 **AI Playground** (Multi-Model Testing with Vision Support)
- 📤 **Document Upload** (PDF, DOCX, PNG, JPG with Preview Generation)
  - ⭐ **QM Requirement:** QM Interest Group wird automatisch zugewiesen und ist erforderlich (kann nicht entfernt werden)
  - 🔐 **SHA-256 Hash Duplikat-Prüfung:** Automatische Erkennung doppelter Dokumente (64 Zeichen Hash)
  - 📑 **Versionierung:** Dokument-Serien mit Parent-Child-Beziehungen, automatische Archivierung alter Versionen
  - 🗑️ **Soft Delete:** Audit-taugliche Löschung mit Grund und Zeitstempel
  - 📦 **Archiv-System:** Vollständiges Lifecycle-Management für gelöschte Dokumente
    - **Archiv-Ansicht:** Gelöschte Dokumente für Level 4+ (QM-Mitarbeiter) und QMS Admins
    - **Read-Only Archiv:** Gelöschte Dokumente nur zur Anzeige (keine Wiederherstellung)
    - **Hard Delete:** Endgültige Löschung (nur Level 5 - für Tests/Cleanup)
    - **RAG Cleanup:** Automatisches Entfernen aus Vector-DB bei Soft Delete
    - **Event-Driven:** DocumentDeletedEvent, DocumentHardDeletedEvent
  - 🔄 **Event-Driven RAG Cleanup:** Automatisches Löschen aus Vector-DB bei Reject/Delete/Archive (verhindert doppelte Vektoren)
- 🔄 **4-Status Workflow** (Draft → Reviewed → Approved/Rejected)
  - ⭐ **Approved → Rejected:** Auch freigegebene Dokumente können zurückgewiesen werden (für Validierung/Fehlerkorrektur)
- 📋 **Audit Trail** (Complete Change History)
- 🎯 **Prompt Management** (Template Versioning & Evaluation)
- 💬 **RAG Chat System** (Intelligent Document Q&A with Vector Search)
  - ⭐ **Prompt-Integration Workflow** (Game Changer): Dokumenttyp-spezifische Chunking basierend auf Standard-Prompts
  - ⭐ **Labels-Mapping** für präzise Bild-zu-Text-Verknüpfung (Buchstaben- + Ziffernlabels)
  - ⭐ **Consumables in Chunks**: Chemikalien/Kleber für optimale RAG-Suche nach Sicherheitshinweisen
  - 🔍 **Hybrid Search** (Qdrant Vector Store + SQLite FTS)
  - 📊 **Source References** mit in-text Links zu Original-Dokumenten
  - 🎯 **Dokumenttyp-spezifische AI-Prompts** für präzisere Chat-Antworten
  - 🧹 **Automatischer RAG Cleanup:** Doppelte Vektoren werden automatisch entfernt bei:
    - Dokument-Rückweisung (Rejected)
    - Soft Delete
    - Archivierung
    - Version-Archivierung (alte Versionen werden aus RAG entfernt)
  - 📊 **RAG Index Status:** Sichtbar in Dokument-Liste, Detail-Seite und Tabellen-Ansicht
  - ✂️ **Chunk-Editor** (Level 4+): Chunks bearbeiten, splitten, mergen, löschen
    - ⭐ **Split-Modal:** Visuelles Modal zum Splitten nach Sätzen (statt Buchstaben)
    - ⭐ **Overlap-Funktion:** Beim Split können 0-10 Overlap-Sätze zwischen Chunks erstellt werden
      - **Korrekte Logik:** Nur der zweite Chunk beginnt mit den letzten N Sätzen des ersten Chunks
      - **Live-Vorschau:** Beide Chunks werden vor dem Split angezeigt
      - **Overlap-Highlighting:** Overlap-Sätze werden grün markiert
    - ⭐ **Seitenweise AI-Verarbeitung:** Einzelne Seiten können neu verarbeitet werden
    - ⭐ **Re-Indexierung:** Dokumente können nach AI-Verarbeitung neu indexiert werden
    - ⭐ **Strukturiertes Chunking:** JSON wird in lesbaren Text konvertiert (Fachartikel)
    - ⭐ **Diagramm-Beschreibung:** Figuren und Tabellen werden in Chunks integriert
- 🤖 **Multi-Model AI** (GPT-4o Mini, GPT-5 Mini, Gemini 2.5 Flash)
  - 📄 **PDF Support in AI Playground**: Native für Gemini, PNG-Conversion für OpenAI
  - 🎯 **Prompt v2.9 für Arbeitsanweisungen**: Excellence Level (9.0/10) mit systematischem Labels-Mapping
- 🐳 **Docker-First** Deployment
- ⚡ **Next.js** Frontend (TypeScript)

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.12+ (for local backend dev)

### Run with Docker (Recommended)

```bash
# Start all services (Backend, Frontend, Qdrant)
docker-compose up -d

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f qdrant

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

**Services:**
- 🐳 **Qdrant**: Vector Store (Port 6333, 6334)
- 🐍 **Backend**: FastAPI (Port 8000)
- ⚛️ **Frontend**: Next.js (Port 3000)

**Access:**
- 🌐 Frontend: http://localhost:3000
- 🔧 Backend API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs
- 🔍 Qdrant Dashboard: http://localhost:6333/dashboard

**Features:**
- ✅ Health Checks für alle Services
- ✅ Automatische Service-Abhängigkeiten (Backend wartet auf Qdrant)
- ✅ Persistente Datenbank (SQLite in `./data/qms.db`)
- ✅ Persistente Vector Store (Qdrant in `./data/qdrant`)
- ✅ Relative Pfade (portabel, keine absoluten Pfade)

---

## 📁 Project Structure

```
DocuMind-AI-V2/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── main.py            # FastAPI app (DDD routers only)
│   │   ├── database.py        # SQLAlchemy setup
│   │   ├── models.py          # DB models (User, InterestGroup)
│   │   └── schemas.py         # Pydantic schemas
│   ├── Dockerfile
│   └── requirements.txt
│
├── contexts/                   # DDD Bounded Contexts
│   ├── interestgroups/        # Interest Groups Context
│   │   ├── domain/           # Entities, VOs, Repositories
│   │   ├── application/      # Use Cases, Services
│   │   ├── infrastructure/   # Concrete Repositories
│   │   └── interface/        # API Router
│   │
│   ├── users/                 # Users & RBAC Context
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── interface/
│   │
│   ├── accesscontrol/         # Auth & Permissions Context
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── interface/
│   │
│   ├── aiplayground/          # AI Model Testing Context
│   │   ├── domain/           # TestResult, ModelConfig
│   │   ├── application/      # AIPlaygroundService
│   │   ├── infrastructure/   # AI Provider Adapters (OpenAI, Google)
│   │   └── interface/        # API Router
│   │
│   ├── documenttypes/         # Document Type Management Context
│   │   ├── domain/           # DocumentType Entity, VOs
│   │   ├── application/      # CRUD Use Cases
│   │   ├── infrastructure/   # SQLAlchemy Repository
│   │   └── interface/        # API Router
│   │
│   ├── prompttemplates/       # Prompt Template Context
│   │   ├── domain/           # PromptTemplate Entity, VOs
│   │   ├── application/      # Template Use Cases
│   │   ├── infrastructure/   # SQLAlchemy Repository
│   │   └── interface/        # API Router
│   │
│   ├── documentupload/        # Document Upload & Workflow Context ✅
│   │   ├── domain/           # UploadedDocument, DocumentPage, WorkflowStatusChange, AIProcessingResult
│   │   ├── application/      # Upload, Preview, Assign, ProcessPage, Workflow Use Cases
│   │   ├── infrastructure/   # FileStorage, PDFSplitter, ImageProcessor, AIProcessingService, WorkflowHistory
│   │   └── interface/        # API Router (11 Endpoints: Upload + Workflow)
│   │
│   └── ragintegration/        # RAG Chat & Vector Store Context ✅
│       ├── domain/           # IndexedDocument, DocumentChunk, ChatSession, ChatMessage
│       ├── application/      # IndexDocument, AskQuestion, CreateSession, GetHistory Use Cases
│       ├── infrastructure/   # Qdrant Adapter, OpenAI Embedding, Hybrid Search Service
│       └── interface/        # API Router (8 Endpoints: RAG Chat + Search)
│
├── frontend/                   # Next.js Frontend
│   ├── app/                   # Next.js 14 App Router
│   │   ├── interest-groups/
│   │   ├── users/
│   │   ├── document-upload/  # Document Upload Page ✅
│   │   ├── documents/        # Document List & Detail (Kanban + Workflow) ✅
│   │   ├── prompt-management/ # Prompt Management Page
│   │   ├── models/           # AI Playground (Admin only)
│   │   └── login/
│   ├── components/            # React components
│   ├── lib/                   # API client, utilities
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.yml          # Docker orchestration
└── README.md                   # This file
```

---

## 🏗️ Architecture

### Domain-Driven Design (DDD)

Each **Bounded Context** follows Clean Architecture:

```
Context (e.g., users/)
├── domain/              # Business Logic (Pure)
│   ├── entities.py     # Domain Entities
│   ├── value_objects.py
│   ├── repositories.py # Repository Interfaces
│   └── events.py       # Domain Events
│
├── application/         # Use Cases
│   ├── use_cases.py    # Application Logic
│   └── services.py     # Application Services
│
├── infrastructure/      # Technical Implementation
│   ├── repositories.py # SQLAlchemy Repos
│   └── mappers.py      # DTO ↔ Entity
│
└── interface/           # External Interface
    └── router.py        # FastAPI Routes
```

### Dependencies Rule
```
interface → application → domain
          ↘ infrastructure ↗
```
**Core principle:** Domain has NO dependencies on outer layers!

---

## 🔐 Authentication

### JWT-Based Auth

```bash
# Login
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "secure123"
}

# Response
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}

# Use token in headers
Authorization: Bearer eyJ...
```

### Default Users (RBAC Multi-Level)

| Benutzer | E-Mail | Passwort | Level | Berechtigung |
|----------|--------|----------|-------|--------------|
| **QMS Admin** | `qms.admin@company.com` | `123` | L5 | Vollzugriff + AI Playground |
| **QM Mitarbeiter** | `qm.mitarbeiter@company.com` | `123` | L4 | Dokument Upload, Workflow, RAG Chat |
| **Abteilungsleiter** | `abteilungsleiter.*@company.com` | `123` | L3 | Workflow (nur eigene IG) |
| **Teamleiter** | `teamleiter.*@company.com` | `123` | L2 | Dokumenten-Tabelle (nur eigene IG) |
| **Mitarbeiter** | `mitarbeiter.*@company.com` | `123` | L1 | RAG Chat (nur eigene IG) |

> **Hinweis:** Alle Test-User-Passwörter sind auf `123` gesetzt. Siehe `docs/RBAC_TEST_USERS.md` für Details.

---

## 🧪 Development

### Backend (Local)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set Python path
export PYTHONPATH=$PWD:$PWD/../contexts

# Run server
uvicorn app.main:app --reload --port 8000
```

### Frontend (Local)

```bash
cd frontend
npm install
npm run dev
```

### Run Tests

```bash
cd backend
pytest                    # Alle Tests
pytest tests/unit/        # Unit Tests (Domain + Application)
pytest tests/integration/ # Integration Tests (Infrastructure)
pytest tests/e2e/         # E2E Tests (API)
pytest -v                 # Verbose Output
pytest --cov              # Coverage Report
```

### Setup Test-User (RBAC)

Für Entwicklung und Tests können Test-User mit verschiedenen RBAC-Leveln erstellt werden:

```bash
cd backend
python3 setup_test_users.py
```

**Erstellt Test-User für alle Level (1-5):**
- Level 5: `qms.admin@company.com` (bereits in init_database.sql)
- Level 4: `qm.mitarbeiter@company.com`
- Level 3: `abteilungsleiter.service@company.com`, `abteilungsleiter.produktion@company.com`
- Level 2: `teamleiter.service@company.com`, `teamleiter.it@company.com`
- Level 1: `mitarbeiter.service@company.com`, `mitarbeiter.it@company.com`

**Alle Passwörter:** `123`

> **Details:** Siehe `docs/RBAC_TEST_USERS.md` für vollständige Dokumentation aller Test-User und deren Berechtigungen.

### Test-Driven Development (TDD)

Dieses Projekt folgt strikt dem **TDD-Ansatz**:

```
1. RED:   Schreibe Tests ZUERST (sie schlagen fehl)
2. GREEN: Implementiere Code bis Tests GRÜN sind
3. REFACTOR: Optimiere Code (Tests bleiben GRÜN)
```

**Test Coverage Ziele:**
- **Domain Layer:** 100% (TDD)
- **Application Layer:** 100% (TDD)
- **Infrastructure Layer:** 80%
- **Interface Layer:** 80%

**Beispiel:** Phase 2.7 (AI-Verarbeitung) - **10/10 Tests GRÜN! 🟢**

---

## 📦 Core Features

### ✅ Implemented (V2.3) - PRODUCTION READY

- [x] **Interest Groups CRUD** (Stakeholder Groups)
- [x] **User Management** (RBAC, Multi-Department)
- [x] **User-Group Memberships** (Dynamic Assignment mit Approval Levels)
- [x] **RBAC Multi-Level System** (5 Levels, Context-Specific Permissions, IG-Level Filtering)
- [x] **JWT Authentication** (Session-Based, 24h Expiry, Logout, RBAC Fields im Token)
- [x] **AI Playground** (Multi-Model Testing, Vision Support, Model Evaluation)
  - [x] OpenAI Support (GPT-4o Mini, GPT-5 Mini - separate API keys)
  - [x] Google AI Support (Gemini 2.5 Flash)
  - [x] Parallel Model Comparison (Thread-Pool Processing)
  - [x] **Step-by-Step Model Evaluation** (Schrittweise Bewertung)
    - Frei editierbarer Evaluator-Prompt (4600+ Zeichen, 10 Kriterien)
    - Auswahl des Evaluator-Modells (GPT-5 Mini, Gemini, GPT-4o Mini)
    - Max Tokens auf Model-Maximum (keine Truncation)
    - Einzelbewertung: "Evaluate First Model" → "Evaluate Second Model"
    - Finale Vergleichstabelle mit Gewinner-Markierung
    - JSON-Output: `category_scores`, `strengths`, `weaknesses`, `summary`
    - Debug-Anzeige: Input JSON Preview + Komplette Evaluation Response
  - [x] Image/Document Upload (Drag & Drop, 10MB, Multimodal)
  - [x] Token Breakdown & Metrics (Text vs. Image Tokens)
  - [x] High/Low Detail Mode (OpenAI Vision)
  - [x] Dynamic Max Tokens (adaptiert an kleinste Modell-Limit)
  - [x] Streaming Support (Live-Content für GPT-4o Mini, Progress für GPT-5/Gemini)
  - [x] Model Verification Badges (zeigt echte API Model-IDs)
  - [x] Progress Indicators & Abort Functionality
- [x] **Document Type Management** (DDD Context: `documenttypes`)
  - [x] CRUD für QMS-Dokumentkategorien (SOP, Flussdiagramm, etc.)
  - [x] File Type Validation & Size Limits
  - [x] AI Processing Requirements (OCR, Vision)
  - [x] Search & Filter (OCR/Vision)
  - [x] Activate/Deactivate Toggle
  - [x] 7 Standard-Typen vorkonfiguriert
- [x] **Prompt Template Management** (DDD Context: `prompttemplates`)
  - [x] CRUD für wiederverwendbare AI Prompts
  - [x] Status Management (Draft, Active, Archived)
  - [x] Semantic Versioning
  - [x] Document Type Linking
  - [x] Usage Tracking & Test Metrics
  - [x] "Save from AI Playground" Workflow
  - [x] **Prompt-Verwaltung Page** (Split-View mit Gestapelten Karten)
  - [x] Drag & Drop für Standard-Prompt Zuweisung
  - [x] Edit-Integration (öffnet AI Playground mit vorausgefüllten Daten)
- [x] **Document Upload & Workflow System** (DDD Context: `documentupload`) **✨ COMPLETE**
  - [x] **Backend (Clean DDD):**
    - [x] Domain Layer (8 Value Objects, 4 Entities, 4 Repository Interfaces, 6 Events)
    - [x] Application Layer (5 Use Cases + 2 Service Ports)
    - [x] Infrastructure Layer (FileStorage, PDFSplitter, ImageProcessor, AIProcessingService, 4 Repositories)
    - [x] Interface Layer (11 FastAPI Endpoints, Pydantic Schemas, Permission Checks Level 4)
  - [x] **Phase 2.7: AI-Verarbeitung (TDD - 10/10 Tests GRÜN)** **🎯 COMPLETE**
    - [x] `AIProcessingResult` Entity (JSON-Parsing, Status-Management, Token-Tracking)
    - [x] `ProcessDocumentPageUseCase` (vollständig getestet, 100% Coverage)
    - [x] `AIPlaygroundProcessingService` (Cross-Context Integration mit aiplayground)
    - [x] `SQLAlchemyAIResponseRepository` (Vollständiges CRUD)
    - [x] `POST /api/document-upload/{id}/process-page/{page}` (mit Error Handling)
    - [x] **TDD-Approach:** RED → GREEN → REFACTOR (10/10 Unit Tests GRÜN)
  - [x] **AI Processing Update-Logik & Prompt Management** **🔄 COMPLETE**
    - [x] **Update-Logik:** Dokumente können mehrfach verarbeitet werden (Update statt Insert)
    - [x] **UNIQUE constraint Fehler behoben:** Keine Fehler mehr bei wiederholter Verarbeitung
    - [x] **Modell-spezifische Token-Limits:** Gemini (5,600), GPT-5 (15,000), GPT-4o (16,384)
    - [x] **Temperature 0.0:** Deterministische Ergebnisse für alle Modelle
    - [x] **Prompt Management:** Drag & Drop und "Als Standard setzen" funktioniert korrekt
    - [x] **AI Playground Integration:** Einstellungen werden 1:1 übertragen
    - [x] **Integration Tests:** 4 Tests für komplette Pipeline
    - [x] **Code Cleanup:** documentworkflow Context entfernt (redundant)
  - [x] **Phase 3: Document Workflow System** **🔄 COMPLETE**
    - [x] **4-Status Workflow:** Draft → Reviewed → Approved/Rejected
    - [x] **Permission Matrix:** Level 2-5 (View, Review, Approve, Admin)
    - [x] **Audit Trail:** Complete History mit User Names, Timestamps, Reasons
    - [x] **Kanban Board:** Drag & Drop Status Management
    - [x] **Interest Groups Filter:** User sieht nur relevante Dokumente
    - [x] **Document Type Filter:** Advanced Search Options
    - [x] **Status Change Modal:** Comment Input, Permission Validation
    - [x] **Real-time Updates:** Status Changes reflected immediately
  - [x] **Frontend (React/Next.js 14):**
    - [x] Upload Page (`/document-upload`) - Drag & Drop, Metadata, Interest Groups
    - [x] Document List (`/documents`) - Kanban Board, Search, Filters, Table View
    - [x] Document Detail (`/documents/:id`) - Preview, Metadata, Page Navigation
    - [x] Status Change Modal - Comment Input, Audit Trail Display
  - [x] **Features:**
    - [x] Multi-Page Document Upload (PDF, DOCX, PNG, JPG, max 50MB)
    - [x] Automatic Page Splitting (PDF → Individual Pages)
    - [x] Preview & Thumbnail Generation (200x200, JPEG 85, DPI 200)
    - [x] Document Type Assignment
    - [x] Interest Group Assignment (Multi-Select)
    - [x] QM Chapter & Version Metadata
    - [x] Upload Progress Indicator (10% → 30% → 50% → 70% → 100%)
    - [x] Date-Based File Storage (`YYYY/MM/DD`)
    - [x] Processing Status (pending → processing → completed / failed)
    - [x] Filter & Search (User, Document Type, Status)
    - [x] Page-by-Page Preview Navigation
    - [x] Delete Document (Cascade: Files + DB)
    - [x] **Workflow Features:**
      - [x] Kanban Board mit 4 Spalten (Draft, Reviewed, Approved, Rejected)
      - [x] Drag & Drop Status Changes mit Permission Checks (Context-Specific RBAC)
      - [x] Interest Groups Badges auf Dokumenten-Karten
      - [x] Document Type Filter Dropdown (RBAC-gefiltert für Level 2-3)
      - [x] Status Change Modal mit Kommentar-Eingabe
      - [x] Audit Trail mit User Names, Timestamps, Reasons
      - [x] Real-time Status Updates
      - [x] **RBAC Multi-Level:** Kanban nur für Level 3+ (mit IG-Level Checks), Tabelle für Level 2+
  - [x] **Dependencies:** PyPDF2, pdf2image, python-docx, pytesseract, Pillow
- [x] **RAG Chat System** (DDD Context: `ragintegration`) **✨ COMPLETE**
  - [x] **Backend (Clean DDD):**
    - [x] Domain Layer (4 Entities, 4 Value Objects, 4 Repository Interfaces, 3 Events)
    - [x] Application Layer (5 Use Cases + 3 Services)
    - [x] Infrastructure Layer (Qdrant Adapter, OpenAI Embedding, Hybrid Search Service, 4 Repositories)
    - [x] Interface Layer (8 FastAPI Endpoints, Pydantic Schemas, Permission Checks)
  - [x] **Vector Store & Embeddings:**
    - [x] Qdrant In-Memory Vector Store (1536-Dimension Embeddings)
    - [x] OpenAI text-embedding-3-small Integration
    - [x] Hybrid Search (Qdrant + SQLite FTS) mit Re-Ranking
    - [x] Multi-Query Expansion für bessere Suche
  - [x] **Intelligent Chunking:**
    - [x] Vision-AI-basiert (strukturierte JSON-Response)
    - [x] Page-Boundary-aware Fallback
    - [x] Plain-Text Fallback
    - [x] Max 1000 Zeichen pro Chunk
    - [x] Metadaten: Page-Numbers, Heading-Hierarchy, Confidence-Score
  - [x] **RAG Chat Features:**
    - [x] Multi-Model Support (GPT-4o Mini, GPT-5 Mini, Gemini 2.5 Flash)
    - [x] Chat Sessions mit Historie
    - [x] Source References mit Relevanz-Score
    - [x] Structured Data Extraction (Tabellen, Listen, Sicherheitshinweise)
    - [x] Suggested Questions für UX-Optimierung
  - [x] **Frontend Integration:**
    - [x] RAG Chat Dashboard (zentraler Chat, 60% Viewport)
    - [x] Session Sidebar (Session-Management, 20% Viewport)
    - [x] Filter Panel (erweiterte Suche, 20% Viewport)
    - [x] Source Preview Modal (Vollbild-Preview mit Zoom)
    - [x] RAG Indexierung Panel (Document Detail Integration)
  - [x] **Database:**
    - [x] 4 neue Tabellen: rag_indexed_documents, rag_document_chunks, rag_chat_sessions, rag_chat_messages
    - [x] Indizes für optimale Performance
    - [x] Trigger für automatische Updates
  - [x] **TDD Testing:** Domain + Application Layer Tests (100% Coverage)
  - [x] **RBAC Integration:**
    - [x] Interest Group Filtering für Level 1-3 (Backend + Frontend)
    - [x] Document Type Filtering für Level 2-3 (nur Document Types mit Dokumenten in eigenen IGs)
    - [x] Context-Specific Permission Checks für Kanban und Workflow-Transitions
- [x] **DDD Contexts (8)** - Vollständig implementiert
- [x] **Docker Deployment** (Docker Compose)
- [x] **Next.js Frontend** (TypeScript, Tailwind CSS)

### 🔜 Roadmap (Phases 5-6)

> **Siehe:** `docs/ROADMAP_DOCUMENT_UPLOAD.md` für detaillierte Task-Liste

- [ ] **QM Workflow Engine** (Review → Approval Flow)
- [ ] **AI Document Analysis** (Prompt Templates auf Dokumente anwenden)
- [ ] **Document Versioning & History**
- [ ] **Advanced Reporting & Analytics**
- [ ] **PostgreSQL Support** (Migration von SQLite)
- [ ] **Kubernetes Deployment**

---

## 🐳 Docker Commands

### Build

```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build backend
docker-compose build frontend
```

### Start

```bash
# Start all services in background
docker-compose up -d

# Start with logs
docker-compose up

# Start specific service
docker-compose up -d qdrant
docker-compose up -d backend
docker-compose up -d frontend
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f qdrant
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Health Checks

```bash
# Check service health
docker-compose ps

# Inspect service
docker inspect documind-backend | grep -A 10 Health
```

### Restart

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
```

### Stop

```bash
# Stop services (keeps containers)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes
docker-compose down -v
```

### Clean

```bash
# Remove all containers, networks, volumes
docker-compose down -v --rmi all

# Remove unused images
docker image prune -a
```

---

## 📚 Wichtige Dateien

### **Dokumentation**
- **`docs/PROJECT_RULES.md`** - Architektur-Regeln und Agent-Guidelines
- **`docs/ONBOARDING_PROMPT.md`** - AI-Agent Onboarding
- **`docs/architecture.md`** - System-Architektur und DDD-Prinzipien
- **`docs/database-schema.md`** - Datenbank-Schema und Tabellen
- **`docs/VERSIONING.md`** - Versionierungs-Best Practices
- **`docs/ROADMAP_DOCUMENT_UPLOAD.md`** - Feature-Roadmap
- **`docs/RBAC_SPECIFICATION.md`** - RBAC Multi-Level Spezifikation
- **`docs/RBAC_MULTI_LEVEL_IMPLEMENTATION.md`** - RBAC Multi-Level Implementierung
- **`docs/RBAC_TEST_USERS.md`** - Test-User Setup und RBAC-Level Übersicht

### **Technische Dokumentation**

**Aktuelle technische Dokumentation** (`docs/technical/`):
- **`docs/technical/EVENT_DRIVEN_ARCHITECTURE.md`** - Event-Driven Architecture: Cross-Context Communication mit Domain Events
- **`docs/technical/DELETE_RAG_CLEANUP.md`** - RAG Cleanup bei Dokument-Löschung: Automatisches Entfernen aus Vector-DB
- **`docs/technical/DUPLICATE_BEHAVIOR_DOCUMENTATION.md`** - Duplikat-Erkennung und -Verhalten: SHA-256 Hash, UX-Warnungen, Indexierungs-Blockierung
- **`docs/technical/MULTIQUERY_SERVICE.md`** - Multi-Query Service Dokumentation
- **`docs/technical/CHUNK_OVERLAP_AND_REINDEX_GUIDE.md`** - Chunk Overlap & Re-Indexierung: Chunk-Splitting mit Overlap, Re-Indexierung
- **`docs/technical/RAG_ANALYSE_UND_FIXES.md`** - RAG System Analyse & Fixes: Identifizierte Probleme und Lösungen

**Abgearbeitete Dokumentation** (`docs/archive/`):
- **`docs/archive/test-reports/`** - Test-Berichte (13 Dateien)
- **`docs/archive/implementation-reports/`** - Implementierungs-Berichte (4 Dateien)
- **`docs/archive/proposals/`** - Abgearbeitete Proposals/Pläne (4 Dateien)

> **Hinweis:** Die Dokumentation ist strukturiert in `docs/technical/` (aktuell) und `docs/archive/` (abgearbeitet). Siehe `docs/PROJECT_RULES.md` für Details zur Dokumentations-Struktur.

### **User Manual**
- **`docs/user-manual/README.md`** - Haupt-Benutzerhandbuch
- **`docs/user-manual/01-upload.md`** - Document Upload Anleitung
- **`docs/user-manual/02-workflow.md`** - Workflow System mit RAG Integration
- **`docs/user-manual/03-rag-chat.md`** - RAG Chat System Handbuch

### **Datenbank**
- **`data/qms.db`** - SQLite-Datenbank (absoluter Pfad: `/Users/reiner/Documents/DocuMind-AI-V2/data/qms.db`)
- **`data/qms_backup_*.db`** - Automatische Backups

---

Interactive API docs available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Key Endpoints

#### Interest Groups
```
GET    /api/interest-groups
GET    /api/interest-groups/{id}
POST   /api/interest-groups
PUT    /api/interest-groups/{id}
DELETE /api/interest-groups/{id}
```

#### Users
```
GET    /api/users
GET    /api/users/{id}
POST   /api/users
PUT    /api/users/{id}
DELETE /api/users/{id}
```

#### Memberships
```
GET    /api/users/{user_id}/memberships
POST   /api/user-group-memberships
PUT    /api/user-group-memberships/{id}
DELETE /api/user-group-memberships/{id}
```

#### Document Upload & Workflow
```
POST   /api/document-upload/upload                    # Upload document
POST   /api/document-upload/{id}/generate-preview    # Generate previews
POST   /api/document-upload/{id}/assign-interest-groups # Assign groups
POST   /api/document-upload/{id}/process-page/{page}  # AI processing
GET    /api/document-upload/{id}                      # Get details
GET    /api/document-upload/                         # List uploads
DELETE /api/document-upload/{id}                      # Delete upload

POST   /api/document-workflow/change-status          # Change status
GET    /api/document-workflow/status/{status}        # Get by status
GET    /api/document-workflow/history/{document_id}  # Audit trail
GET    /api/document-workflow/{id}/allowed-transitions # Allowed transitions
POST   /api/document-workflow/soft-delete           # Soft delete (Archiv)
GET    /api/document-workflow/archive                # Get archived documents (Level 4+)
DELETE /api/document-workflow/hard-delete/{document_id} # Hard delete (Level 5 only)
```

#### Document Types
```
GET    /api/document-types
GET    /api/document-types/{id}
POST   /api/document-types
PUT    /api/document-types/{id}
DELETE /api/document-types/{id}
```

#### Prompt Templates
```
GET    /api/prompt-templates
GET    /api/prompt-templates/{id}
POST   /api/prompt-templates
POST   /api/prompt-templates/from-playground
PUT    /api/prompt-templates/{id}
POST   /api/prompt-templates/{id}/activate
POST   /api/prompt-templates/{id}/archive
DELETE /api/prompt-templates/{id}
```

#### AI Playground
```
GET    /api/ai-playground/models                     # Available models
POST   /api/ai-playground/test                       # Single model test
POST   /api/ai-playground/compare                    # Model comparison
POST   /api/ai-playground/test-model-stream          # Streaming test
POST   /api/ai-playground/evaluate-single            # Single evaluation
```

---

## 🤝 Contributing

### Coding Standards

- **Python:** PEP 8, Type hints, Docstrings
- **TypeScript:** ESLint, Prettier
- **Commits:** Conventional Commits

### Pull Request Process

1. Fork the repo
2. Create feature branch (`feature/my-feature`)
3. Commit changes (`feat: add awesome feature`)
4. Push to branch
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/DocuMind-AI-V2/issues)
- **Email:** mail@rtjaeger.de
Reiner Jaeger
Buchenweg 25
72475 Bitz

---


