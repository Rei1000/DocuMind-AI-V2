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
└── prompttemplates/        # Prompt Template Management & Versioning
    ├── domain/
    │   ├── entities.py           # PromptTemplate Entity
    │   ├── value_objects.py      # AIModelConfig, PromptVersion, PromptStatus
    │   └── repositories.py       # IPromptTemplateRepository (Port)
    │
    ├── application/
    │   ├── use_cases.py          # CRUD + Activate/Archive Use Cases
    │   └── services.py           # PromptTemplateService
    │
    ├── infrastructure/
    │   ├── repositories.py       # PromptTemplateSQLAlchemyRepository
    │   └── mappers.py            # Entity ↔ DB Model Mapper (float/int conversion)
    │
    └── interface/
        └── router.py             # /api/prompt-templates/* Routes
                                  # Special: /from-playground endpoint
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

## 📊 Data Flow: Create User Example

```
┌──────────────────────────────────────────────────────────────┐
│  1. INTERFACE LAYER (interface/router.py)                   │
│     POST /api/users                                          │
│     ┌──────────────────────────────────────────┐           │
│     │ @router.post("/")                         │           │
│     │ async def create_user(                    │           │
│     │     data: UserCreate,                     │           │
│     │     db: Session = Depends(get_db)         │           │
│     │ ):                                        │           │
│     │     # 1. Create Repository                │           │
│     │     repo = SQLAlchemyUserRepo(db)         │           │
│     │     # 2. Create Use Case                  │           │
│     │     use_case = CreateUserUseCase(repo)    │           │
│     │     # 3. Execute                          │           │
│     │     user = use_case.execute(data)         │           │
│     │     return user                           │           │
│     └──────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  2. APPLICATION LAYER (application/use_cases.py)            │
│     CreateUserUseCase                                        │
│     ┌──────────────────────────────────────────┐           │
│     │ def execute(self, data: UserCreate):     │           │
│     │     # 1. Validate (Business Rules)       │           │
│     │     self._validate_email(data.email)     │           │
│     │                                           │           │
│     │     # 2. Create Domain Entity             │           │
│     │     user = User(                          │           │
│     │         email=Email(data.email),          │           │
│     │         permissions=[...]                 │           │
│     │     )                                     │           │
│     │                                           │           │
│     │     # 3. Save via Repository (Port)       │           │
│     │     saved_user = self.repo.save(user)     │           │
│     │     return saved_user                     │           │
│     └──────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  3. DOMAIN LAYER (domain/entities.py)                       │
│     User Entity (Pure Business Object)                      │
│     ┌──────────────────────────────────────────┐           │
│     │ @dataclass                                │           │
│     │ class User:                               │           │
│     │     id: int                               │           │
│     │     email: Email                          │           │
│     │     permissions: List[Permission]         │           │
│     │                                           │           │
│     │     def has_permission(self, perm):       │           │
│     │         return perm in self.permissions   │           │
│     └──────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  4. INFRASTRUCTURE LAYER (infrastructure/repositories.py)   │
│     SQLAlchemyUserRepository (Adapter)                       │
│     ┌──────────────────────────────────────────┐           │
│     │ def save(self, user: User) -> User:      │           │
│     │     # 1. Map Entity → DB Model           │           │
│     │     db_user = self.mapper.to_model(user) │           │
│     │                                           │           │
│     │     # 2. Persist to Database              │           │
│     │     self.db.add(db_user)                  │           │
│     │     self.db.commit()                      │           │
│     │     self.db.refresh(db_user)              │           │
│     │                                           │           │
│     │     # 3. Map DB Model → Entity            │           │
│     │     return self.mapper.to_entity(db_user) │           │
│     └──────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
                 ┌────────────────┐
                 │   DATABASE     │
                 │   (SQLite)     │
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
- Single Backend Container
- Single Frontend Container

### Future (Production):
- PostgreSQL with Read Replicas
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

### Data Protection:
- Password Hashing (bcrypt)
- SQL Injection Prevention (SQLAlchemy ORM)
- XSS Protection (React Auto-Escaping)
- CORS Policy (Whitelist)

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

Note: prompttemplates + documenttypes = "Prompt-Verwaltung" Page
      Both contexts use aiplayground for "Save as Template" workflow

Future:
┌──────────────────┐
│   documents      │──┐ Depends on
│  (QMS Docs)      │  │ documenttypes + prompttemplates
└──────────────────┘  │
         ▲            │
         │            │
┌──────────────────┐  │
│    uploads       │──┤
│ (OCR/Vision AI)  │  │
└──────────────────┘  │
         ▲            │
         │            │
┌──────────────────┐  │
│   qmworkflow     │──┘
│ (Review/Approve) │
└──────────────────┘
```

---

**Last Updated:** 2025-10-11  
**Version:** 2.1  
**Latest Changes:** Enhanced AI Playground with Step-by-Step Model Evaluation System (evaluate-single endpoint, max_tokens = model maximum, category_scores/strengths/weaknesses/summary output)
