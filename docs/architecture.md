# 🏗️ DocuMind-AI V2 Architecture

> Clean Architecture mit Domain-Driven Design

---

## 📐 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  (Next.js 14 + TypeScript + Tailwind CSS)                  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Interest     │  │ Users        │  │ AI           │     │
│  │ Groups Page  │  │ Page         │  │ Playground   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         API Client (lib/api.ts)                      │  │
│  │         - JWT Auth                                    │  │
│  │         - Type-Safe Requests                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Interface Layer                         │
│             (FastAPI Routers - API Gateway)                  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Interest     │  │ Users        │  │ AI           │     │
│  │ Groups       │  │ Router       │  │ Playground   │     │
│  │ Router       │  │              │  │ Router       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│                    (Use Cases / Services)                    │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Create       │  │ Create       │  │ Test AI      │     │
│  │ Interest     │  │ User         │  │ Model        │     │
│  │ Group        │  │ UseCase      │  │ Service      │     │
│  │ UseCase      │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                    │                   │
                    ▼                   ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   Domain Layer           │  │  Infrastructure Layer    │
│   (Business Logic)       │  │  (Technical Impl.)       │
│                          │  │                          │
│  ┌────────────────┐      │  │  ┌────────────────┐     │
│  │ Entities       │      │  │  │ SQLAlchemy     │     │
│  │ - User         │      │  │  │ Repositories   │     │
│  │ - InterestGroup│      │  │  │                │     │
│  │ - TestResult   │      │  │  │ - UserRepo     │     │
│  └────────────────┘      │  │  │ - GroupRepo    │     │
│                          │  │  └────────────────┘     │
│  ┌────────────────┐      │  │                          │
│  │ Value Objects  │      │  │  ┌────────────────┐     │
│  │ - Email        │      │  │  │ AI Providers   │     │
│  │ - Permission   │      │  │  │ - OpenAI       │     │
│  │ - ModelConfig  │      │  │  │ - Google AI    │     │
│  └────────────────┘      │  │  └────────────────┘     │
│                          │  │                          │
│  ┌────────────────┐      │  │  ┌────────────────┐     │
│  │ Repository     │◄─────┼──┼──┤ Implementation │     │
│  │ Interfaces     │      │  │  │ (Adapters)     │     │
│  │ (Ports)        │      │  │  └────────────────┘     │
│  └────────────────┘      │  │                          │
└──────────────────────────┘  └──────────────────────────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │   Database       │
                              │   (SQLite / PG)  │
                              └──────────────────┘
```

---

## 🎯 Bounded Contexts

Jeder **Bounded Context** ist eine eigenständige Domäne:

```
contexts/
│
├── interestgroups/         # Interest Groups Domain
│   ├── domain/
│   │   ├── entities.py           # InterestGroup Entity
│   │   ├── repositories.py       # IInterestGroupRepository (Port)
│   │   └── value_objects.py      # GroupCode, Permissions
│   │
│   ├── application/
│   │   └── use_cases.py          # CreateInterestGroup, etc.
│   │
│   ├── infrastructure/
│   │   ├── repositories.py       # SQLAlchemyInterestGroupRepo
│   │   └── mappers.py            # InterestGroupMapper
│   │
│   └── interface/
│       └── router.py             # FastAPI Routes
│
├── users/                  # Users & RBAC Domain
│   ├── domain/
│   │   ├── entities.py           # User, UserGroupMembership
│   │   ├── repositories.py       # IUserRepository
│   │   └── value_objects.py      # Email, Permission
│   │
│   ├── application/
│   │   ├── use_cases.py          # CreateUser, AssignToGroup
│   │   └── commands.py           # CreateUserCommand
│   │
│   ├── infrastructure/
│   │   ├── repositories.py       # SQLAlchemyUserRepo
│   │   └── mappers.py            # UserMapper
│   │
│   └── interface/
│       └── router.py             # FastAPI Routes
│
├── accesscontrol/          # Auth & Permissions Domain
│   ├── domain/
│   │   ├── entities.py           # Session, Token
│   │   ├── policies.py           # PermissionPolicy
│   │   └── repositories.py       # ISessionRepository
│   │
│   ├── application/
│   │   └── use_cases.py          # LoginUser, ValidateToken
│   │
│   ├── infrastructure/
│   │   ├── jwt_service.py        # JWT Implementation
│   │   └── repositories.py       # SessionRepo
│   │
│   └── interface/
│       └── guard_router.py       # /api/auth/* Routes
│
├── aiplayground/           # AI Model Testing & Comparison & Evaluation
│   ├── domain/
│   │   ├── entities.py           # TestResult, AIModel, EvaluationResult
│   │   └── value_objects.py      # ModelConfig, Provider, ModelDefinition
│   │
│   ├── application/
│   │   └── services.py           # AIPlaygroundService
│   │       # - test_model() - Single Model Test
│   │       # - compare_models() - Multi-Model Comparison (parallel)
│   │       # - evaluate_single_model_result() - Step-by-Step Evaluation (NEW)
│   │       # - evaluate_comparison_results() - Legacy Evaluation
│   │
│   ├── infrastructure/
│   │   └── ai_providers/         # AI Provider Adapters (Ports & Adapters)
│   │       ├── base.py           # AIProviderAdapter (Port)
│   │       ├── openai_adapter.py # OpenAI Implementation (GPT-4o Mini, GPT-5 Mini)
│   │       └── google_adapter.py # Google AI Implementation (Gemini 2.5 Flash)
│   │
│   └── interface/
│       └── router.py             # /api/ai-playground/* Routes
│           # - POST /test - Single Model Test
│           # - POST /compare - Multi-Model Comparison
│           # - POST /evaluate-single - Single Model Evaluation (NEW)
│           # - POST /evaluate - Legacy Comparison Evaluation
│
├── documenttypes/          # Document Type Management
│   ├── domain/
│   │   ├── entities.py           # DocumentType Entity
│   │   ├── value_objects.py      # FileTypeVO, ValidationRule, ProcessingRequirement
│   │   └── repositories.py       # IDocumentTypeRepository (Port)
│   │
│   ├── application/
│   │   ├── use_cases.py          # CRUD Use Cases
│   │   └── services.py           # DocumentTypeService (file validation)
│   │
│   ├── infrastructure/
│   │   ├── repositories.py       # DocumentTypeSQLAlchemyRepository
│   │   └── mappers.py            # Entity ↔ DB Model Mapper
│   │
│   └── interface/
│       └── router.py             # /api/document-types/* Routes
│
├── prompttemplates/        # Prompt Template Management & Versioning
│   ├── domain/
│   │   ├── entities.py           # PromptTemplate Entity
│   │   ├── value_objects.py      # AIModelConfig, PromptVersion, PromptStatus
│   │   └── repositories.py       # IPromptTemplateRepository (Port)
│   │
│   ├── application/
│   │   ├── use_cases.py          # CRUD + Activate/Archive Use Cases
│   │   └── services.py           # PromptTemplateService
│   │
│   ├── infrastructure/
│   │   ├── repositories.py       # PromptTemplateSQLAlchemyRepository
│   │   └── mappers.py            # Entity ↔ DB Model Mapper (float/int conversion)
│   │
│   └── interface/
│       └── router.py             # /api/prompt-templates/* Routes
│                                  # Special: /from-playground endpoint
│
├── documentupload/        # Document Upload & Workflow Context ✅
│   ├── domain/           # UploadedDocument, DocumentPage, WorkflowStatusChange, AIProcessingResult
│   ├── application/      # Upload, Preview, Assign, ProcessPage, Workflow Use Cases
│   ├── infrastructure/   # FileStorage, PDFSplitter, ImageProcessor, AIProcessingService, WorkflowHistory
│   └── interface/        # API Router (11 Endpoints: Upload + Workflow)
│
└── ragintegration/        # RAG Chat & Vector Store Context ✅
    ├── domain/           # IndexedDocument, DocumentChunk, ChatSession, ChatMessage
    ├── application/      # IndexDocument, AskQuestion, CreateSession, GetHistory Use Cases
    ├── infrastructure/   # Qdrant Adapter, OpenAI Embedding, Hybrid Search Service
    └── interface/        # API Router (8 Endpoints: RAG Chat + Search)
```

---

## 🔄 Dependency Flow (Hexagonal Architecture)

```
┌─────────────────────────────────────────────────────────┐
│                   OUTSIDE WORLD                          │
│  (HTTP Requests, Database, External APIs)               │
└─────────────────────────────────────────────────────────┘
                       │ Adapters
                       ▼
┌─────────────────────────────────────────────────────────┐
│                 INTERFACE LAYER                          │
│  - FastAPI Routers (Driving Adapters)                   │
│  - REST API Endpoints                                    │
│  - Request/Response Validation                           │
└─────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              APPLICATION LAYER                           │
│  - Use Cases (Application Logic)                         │
│  - Orchestrates Domain + Infrastructure                  │
│  - NO Business Logic here!                               │
└─────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  DOMAIN LAYER                            │
│  - Entities (Business Objects)                           │
│  - Value Objects (Immutable Values)                      │
│  - Repository Interfaces (Ports)                         │
│  - Domain Events                                         │
│  - Business Rules & Logic                                │
│  ⚠️  NO DEPENDENCIES to outer layers!                   │
└─────────────────────────────────────────────────────────┘
                       ▲
                       │ Implements
                       │
┌─────────────────────────────────────────────────────────┐
│             INFRASTRUCTURE LAYER                         │
│  - Concrete Repositories (Driven Adapters)              │
│  - SQLAlchemy Models                                     │
│  - External API Clients                                  │
│  - Mappers (DTO ↔ Entity)                               │
└─────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              EXTERNAL SYSTEMS                            │
│  - Database (SQLite / PostgreSQL)                        │
│  - External APIs                                         │
│  - File System                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🔐 Authentication Flow

```
┌────────────┐         ┌──────────────┐         ┌──────────────┐
│  Frontend  │         │   Backend    │         │   Database   │
│  (Next.js) │         │  (FastAPI)   │         │   (SQLite)   │
└────────────┘         └──────────────┘         └──────────────┘
      │                       │                        │
      │ POST /api/auth/login  │                        │
      │ { email, password }   │                        │
      │──────────────────────>│                        │
      │                       │                        │
      │                       │ Verify Credentials     │
      │                       │───────────────────────>│
      │                       │                        │
      │                       │ User Found + Valid     │
      │                       │<───────────────────────│
      │                       │                        │
      │                       │ Generate JWT Token     │
      │                       │                        │
      │ { access_token: "..." }                       │
      │<──────────────────────│                        │
      │                       │                        │
      │ Store in localStorage │                        │
      │                       │                        │
      │                       │                        │
      │ GET /api/users        │                        │
      │ Authorization: Bearer <token>                  │
      │──────────────────────>│                        │
      │                       │                        │
      │                       │ Validate JWT           │
      │                       │                        │
      │                       │ Extract User ID        │
      │                       │                        │
      │                       │ Get User Data          │
      │                       │───────────────────────>│
      │                       │                        │
      │                       │ User Data              │
      │                       │<───────────────────────│
      │                       │                        │
      │ { users: [...] }      │                        │
      │<──────────────────────│                        │
      │                       │                        │
```

---

## 📊 Data Flow: RAG Chat Example

```
┌──────────────────────────────────────────────────────────────┐
│  1. INTERFACE LAYER (interface/router.py)                   │
│     POST /api/rag/chat/ask                                   │
│     ┌──────────────────────────────────────────┐           │
│     │ @router.post("/ask")                      │           │
│     │ async def ask_question(                   │           │
│     │     data: AskQuestionRequest,             │           │
│     │     db: Session = Depends(get_db)         │           │
│     │ ):                                        │           │
│     │     # 1. Create Repositories              │           │
│     │     indexed_doc_repo = SQLAlchemyIndexedDocumentRepo(db) │
│     │     chunk_repo = SQLAlchemyDocumentChunkRepo(db)     │
│     │     session_repo = SQLAlchemyChatSessionRepo(db)      │
│     │     # 2. Create Use Case                  │           │
│     │     use_case = AskQuestionUseCase(...)    │           │
│     │     # 3. Execute                          │           │
│     │     response = use_case.execute(data)     │           │
│     │     return response                       │           │
│     └──────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  2. APPLICATION LAYER (application/use_cases.py)            │
│     AskQuestionUseCase                                        │
│     ┌──────────────────────────────────────────┐           │
│     │ def execute(self, data: AskQuestionRequest): │           │
│     │     # 1. Multi-Query Expansion            │           │
│     │     queries = self.multi_query_service.generate_queries(data.question) │
│     │                                           │           │
│     │     # 2. Hybrid Search                    │           │
│     │     chunks = self.hybrid_search_service.search(queries) │
│     │                                           │           │
│     │     # 3. Build Context                    │           │
│     │     context = self._build_context(chunks) │           │
│     │                                           │           │
│     │     # 4. Generate AI Response             │           │
│     │     response = self.ai_service.generate_response(context) │
│     │                                           │           │
│     │     # 5. Extract Structured Data         │           │
│     │     structured_data = self.structured_data_extractor.extract(response) │
│     │                                           │           │
│     │     # 6. Save Messages                   │           │
│     │     self._save_messages(data, response)   │           │
│     │     return response                       │           │
│     └──────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  3. DOMAIN LAYER (domain/entities.py)                       │
│     ChatMessage Entity (Pure Business Object)                │
│     ┌──────────────────────────────────────────┐           │
│     │ @dataclass                                │           │
│     │ class ChatMessage:                        │           │
│     │     id: int                               │           │
│     │     session_id: int                       │           │
│     │     role: str                             │           │
│     │     content: str                          │           │
│     │     source_references: List[SourceReference] │           │
│     │     structured_data: List[dict]           │           │
│     │     ai_model_used: str                   │           │
│     │     created_at: datetime                  │           │
│     └──────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  4. INFRASTRUCTURE LAYER (infrastructure/)                   │
│     QdrantVectorStoreAdapter + HybridSearchService            │
│     ┌──────────────────────────────────────────┐           │
│     │ def search(self, queries: List[str]) -> List[DocumentChunk]: │
│     │     # 1. Generate Embeddings             │           │
│     │     embeddings = self.embedding_service.generate_embeddings(queries) │
│     │                                           │           │
│     │     # 2. Vector Search (Qdrant)          │           │
│     │     vector_results = self.qdrant_client.search(embeddings) │
│     │                                           │           │
│     │     # 3. Text Search (SQLite FTS)         │           │
│     │     text_results = self.text_search_service.search(queries) │
│     │                                           │           │
│     │     # 4. Merge & Re-Rank                  │           │
│     │     merged_results = self._merge_results(vector_results, text_results) │
│     │     return merged_results                 │           │
│     └──────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
                 ┌────────────────┐
                 │   QDRANT       │
                 │   (Vector DB)  │
                 └────────────────┘
```

---

## 🔧 Technology Stack

### Backend
- **Framework:** FastAPI 0.115+
- **ORM:** SQLAlchemy 2.0+
- **Validation:** Pydantic V2
- **Auth:** python-jose (JWT)
- **Database:** SQLite (Dev), PostgreSQL (Prod)
- **Vector Store:** Qdrant (In-Memory)
- **AI:** OpenAI API, Google AI API
- **Embeddings:** OpenAI text-embedding-3-small

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript 5+
- **Styling:** Tailwind CSS 3+
- **UI Components:** shadcn/ui + Radix UI
- **State:** React Hooks (useState, useEffect)

### Infrastructure
- **Containerization:** Docker + Docker Compose
- **Reverse Proxy:** (TODO: nginx/traefik)
- **Monitoring:** (TODO: Prometheus + Grafana)

---

## 📈 Scalability Considerations

### Current (MVP):
- SQLite Database
- Qdrant In-Memory Vector Store
- Single Backend Container
- Single Frontend Container

### Future (Production):
- PostgreSQL with Read Replicas
- Qdrant Cluster (Persistent Vector Store)
- Multiple Backend Instances (Load Balanced)
- Redis for Caching/Sessions
- Message Queue (RabbitMQ/Kafka) für Domain Events
- Kubernetes Deployment

---

## 🔒 Security Architecture

### Authentication:
- JWT Tokens (HS256)
- Token Expiry: 24 hours (1440 minutes)
- Session-Based Storage (sessionStorage) - Token cleared on browser close
- Refresh Token: (TODO)

### Authorization:
- Role-Based Access Control (RBAC)
- Permission Checks in Domain Layer
- Multi-Department Support (User ↔ Groups)
- RAG Chat: Level-based access (Level 1-4)

### Data Protection:
- Password Hashing (bcrypt)
- SQL Injection Prevention (SQLAlchemy ORM)
- XSS Protection (React Auto-Escaping)
- CORS Policy (Whitelist)
- Vector Store: In-Memory (no persistent data)

---

## 📊 Context Relationships

```
┌──────────────────┐
│  accesscontrol   │◄──┐
│  (Auth/JWT)      │   │ Depends on
└──────────────────┘   │
         ▲             │
         │ Uses        │
         │             │
┌──────────────────┐   │
│     users        │───┘
│  (RBAC/Perms)    │
└──────────────────┘
         ▲
         │ Uses
         │
┌──────────────────┐
│ interestgroups   │
│ (13 Stakeholder) │
└──────────────────┘

┌──────────────────┐
│  aiplayground    │───┐
│ (AI Testing)     │   │ Depends on
└──────────────────┘   │
         ▲             │
         │ Uses        │
         └─────────────┘
         (accesscontrol for Admin checks)
         │
         │ Integration
         │
┌──────────────────┐
│ prompttemplates  │◄──┐
│ (Prompt Mgmt)    │   │ Linked to
└──────────────────┘   │
         ▲             │
         │ Linked to   │
         │             │
┌──────────────────┐   │
│ documenttypes    │───┘
│ (Doc Categories) │
└──────────────────┘

┌──────────────────┐
│ documentupload   │──┐ Depends on
│ (Doc Upload)     │  │ documenttypes + prompttemplates
└──────────────────┘  │
         ▲            │
         │            │
┌──────────────────┐  │
│ ragintegration   │──┤
│ (RAG Chat/Index) │  │
└──────────────────┘  │
         ▲            │
         │ Uses       │
         │            │
┌──────────────────┐  │
│ documentupload   │──┘
│ (AI Processing)  │
└──────────────────┘

Note: ragintegration uses documentupload for:
      - Reading approved documents
      - Accessing Vision AI processing results
      - Document chunking and indexing
```

---

## 🎯 RAG System Architecture

### Vector Store Flow:
```
Document Upload → AI Processing → Vision AI Results → Chunking → Embeddings → Qdrant
                                                                                    │
User Question → Multi-Query Expansion → Hybrid Search ←──────────────────────────┘
                    │
                    ▼
AI Response ← Context Building ← Re-Ranking ← Search Results
```

### Chunking Strategy:
1. **Vision-AI-basiert** (Primär): Nutzt strukturierte JSON-Response
2. **Page-Boundary-aware** (Fallback): Respektiert Seiten-Grenzen
3. **Plain-Text** (Notfall): Einfache Text-Aufteilung

### Hybrid Search:
- **Vector Search:** Qdrant (semantic similarity)
- **Text Search:** SQLite FTS (keyword matching)
- **Re-Ranking:** Combiniert beide Ergebnisse

---

**Last Updated:** 2025-10-27  
**Version:** 2.1  
**Latest Changes:** Complete RAG Integration System with Vector Store, Hybrid Search, Multi-Model AI Support, and Frontend Integration