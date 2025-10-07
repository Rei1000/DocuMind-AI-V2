# DocuMind-AI V2

> **Clean DDD Architecture** for Quality Management Systems (QMS)

Modern, Domain-Driven Design implementation of DocuMind-AI with focus on:
- 🏗️ **Hexagonal Architecture** (Ports & Adapters)
- 👥 **RBAC** (Role-Based Access Control)
- 🏢 **13 Interest Groups** (Stakeholder System)
- 🤖 **AI Playground** (Multi-Model Testing with Vision Support)
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
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Access:**
- 🌐 Frontend: http://localhost:3000
- 🔧 Backend API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs

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
│   └── aiplayground/          # AI Model Testing Context
│       ├── domain/           # TestResult, ModelConfig
│       ├── application/      # AIPlaygroundService
│       ├── infrastructure/   # AI Provider Adapters (OpenAI, Google)
│       └── interface/        # API Router
│
├── frontend/                   # Next.js Frontend
│   ├── app/                   # Next.js 14 App Router
│   │   ├── interest-groups/
│   │   ├── users/
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

### Default Users
- **QMS Admin:** `qms.admin@company.com` / `Admin!234` (Full Access + AI Playground)
- **Admin:** `admin@documind.ai` / `admin123`
- **QM Manager:** `qm@documind.ai` / `qm123`

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
pytest
```

---

## 📦 Core Features

### ✅ Implemented (V2.0)

- [x] Interest Groups CRUD
- [x] User Management (RBAC)
- [x] User-Group Memberships (Multi-Department)
- [x] JWT Authentication (Session-Based, 24h Expiry)
- [x] AI Playground (Multi-Model Testing, Vision Support)
  - [x] OpenAI Support (GPT-4o Mini, GPT-5 Mini)
  - [x] Google AI Support (Gemini 2.5 Flash)
  - [x] Parallel Model Comparison
  - [x] Image/Document Upload (Drag & Drop, 10MB)
  - [x] Token Breakdown & Metrics
- [x] DDD Contexts (4)
- [x] Docker Deployment
- [x] Next.js Frontend

### 🔜 Roadmap (Later)

- [ ] Document Management (DDD Context)
- [ ] Upload Methods (OCR, Batch Processing)
- [ ] QM Workflow (Review → Approval)
- [ ] AI Document Analysis (Integration with AI Playground)
- [ ] PostgreSQL Support
- [ ] Kubernetes Deployment

---

## 🐳 Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart service
docker-compose restart backend

# Stop all
docker-compose down

# Remove volumes (reset DB)
docker-compose down -v
```

---

## 📝 API Documentation

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
- **Email:** support@documind-ai.de

---

**Built with ❤️ using DDD, FastAPI, and Next.js**
