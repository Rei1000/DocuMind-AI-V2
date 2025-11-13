"""
🚀 DocuMind-AI V2 - Clean DDD Backend

Minimales FastAPI Backend mit:
- DDD Architecture (Hexagonal/Clean)
- Interest Groups Context
- Users Context (RBAC)
- Access Control Context (Auth/JWT)

Version: 2.5.1
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✅ Loaded environment variables from {env_path}")
else:
    print(f"⚠️ No .env file found at {env_path}")

# Add project root and contexts to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import database
from .database import Base, engine

# Import all models to ensure they're registered before table creation
# This ensures SQLAlchemy registers all table definitions
from . import models  # Core models (User, InterestGroup, etc.)
try:
    from contexts.ragintegration.infrastructure.models import (
        IndexedDocumentModel,
        DocumentChunkModel,
        ChatSessionModel,
        ChatMessageModel
    )
    print("✅ RAG Integration Models imported")
except ImportError as e:
    print(f"⚠️ Could not import RAG Models: {e}")

# Create all tables (after all models are imported)
Base.metadata.create_all(bind=engine)

# Ensure uploads directory exists
uploads_dir = project_root / "data" / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="DocuMind-AI V2 API",
    description="""
    ## Clean DDD Architecture für QMS
    
    **Features:**
    - 🏗️ Domain-Driven Design (Hexagonal Architecture)
    - 👥 User Management (RBAC)
    - 🏢 Interest Groups (13 Stakeholder System)
    - 🔐 JWT Authentication
    - 🤖 AI Playground (OpenAI, Google AI, Model Comparison)
    - 📄 Document Types & Prompt Templates
    - 📤 Document Upload System (PDF, DOCX, PNG, JPG)
    - 📊 ISO 13485 Ready
    
    **Tech Stack:**
    - FastAPI (Python 3.12+)
    - SQLAlchemy ORM
    - Pydantic V2
    - JWT Tokens
    - PIL/Pillow (Image Processing)
    - PyPDF2 (PDF Processing)
    """,
    version="2.5.1",
    contact={
        "name": "DocuMind-AI Team",
        "email": "support@documind-ai.de",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],  # Next.js Frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== DDD CONTEXT ROUTERS =====

# Load Interest Groups Router (DDD Context)
try:
    from contexts.interestgroups.interface.router import router as ig_router
    app.include_router(ig_router, tags=["Interest Groups"])
    print("✅ DDD Interest Groups Router loaded")
except ImportError as e:
    print(f"⚠️ Could not load Interest Groups Router: {e}")

# Load Users Router (DDD Context)
try:
    from contexts.users.interface.router import router as users_router
    app.include_router(users_router, tags=["Users"])
    print("✅ DDD Users Router loaded")
except ImportError as e:
    print(f"⚠️ Could not load Users Router: {e}")

# Load Access Control Router (DDD Context - Auth/JWT)
try:
    from contexts.accesscontrol.interface.guard_router import router as guard_router
    app.include_router(guard_router, tags=["Authentication"])
    print("✅ DDD Access Control (Auth) Router loaded")
except ImportError as e:
    print(f"⚠️ Could not load Access Control Router: {e}")

# Load AI Playground Router (DDD Context - AI Testing)
try:
    from contexts.aiplayground.interface.router import router as playground_router
    app.include_router(playground_router, tags=["AI Playground"])
    print("✅ DDD AI Playground Router loaded")
except ImportError as e:
    print(f"⚠️ Could not load AI Playground Router: {e}")

# Load Document Types Router (DDD Context - Document Management)
try:
    from contexts.documenttypes.interface.router import router as doctypes_router
    app.include_router(doctypes_router, tags=["Document Types"])
    print("✅ DDD Document Types Router loaded")
except ImportError as e:
    print(f"⚠️ Could not load Document Types Router: {e}")

# Load Prompt Templates Router (DDD Context - Prompt Management)
try:
    from contexts.prompttemplates.interface.router import router as prompttemplates_router
    app.include_router(prompttemplates_router, tags=["Prompt Templates"])
    print("✅ DDD Prompt Templates Router loaded")
except ImportError as e:
    print(f"⚠️ Could not load Prompt Templates Router: {e}")

# Load Document Upload Router (DDD Context - Document Upload System)
try:
    from contexts.documentupload.interface.router import router as documentupload_router
    app.include_router(documentupload_router, tags=["Document Upload"])
    print("✅ DDD Document Upload Router loaded")
except ImportError as e:
    print(f"⚠️ Could not load Document Upload Router: {e}")

# Load Document Workflow Router (DDD Context - Document Workflow System)
try:
    from contexts.documentupload.interface.workflow_router import router as workflow_router
    app.include_router(workflow_router, tags=["Document Workflow"])
    print("✅ DDD Document Workflow Router loaded")
except ImportError as e:
    print(f"⚠️ Could not load Document Workflow Router: {e}")

# Load RAG Integration Router
try:
    from contexts.ragintegration.interface.router import router as rag_router
    app.include_router(rag_router, tags=["RAG Integration"])
    print("✅ RAG Integration Router loaded")
except ImportError as e:
    print(f"⚠️ Could not load RAG Integration Router: {e}")

# Load RAG Monitoring Router
try:
    from contexts.ragintegration.interface.monitoring_router import router as rag_monitoring_router
    app.include_router(rag_monitoring_router, tags=["RAG Monitoring"])
    print("✅ RAG Monitoring Router loaded")
except ImportError as e:
    print(f"⚠️ Could not load RAG Monitoring Router: {e}")



# ===== STATIC FILES CONFIGURATION =====

# Mount static files for uploaded documents, previews, and thumbnails
app.mount("/data/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
print(f"✅ Static files mounted: /data/uploads -> {uploads_dir}")


# ===== HEALTH & STATUS ENDPOINTS =====

@app.get("/", tags=["System"])
async def root():
    """API Root - System Information"""
    return {
        "service": "DocuMind-AI V2",
        "version": "2.5.1",
        "architecture": "DDD + Hexagonal",
        "status": "running",
        "endpoints": {
            "api_docs": "/docs",
            "health": "/health",
            "interest_groups": "/api/interest-groups",
            "users": "/api/users",
            "auth": "/api/auth",
            "ai_playground": "/api/ai-playground",
            "document_types": "/api/document-types",
            "prompt_templates": "/api/prompt-templates",
            "document_upload": "/api/document-upload",
            "document_workflow": "/api/document-workflow",
            "rag_integration": "/api/rag",
        }
    }


@app.get("/api/documents", tags=["System"])
async def documents_redirect():
    """Documents Endpoint - Redirect to correct endpoints"""
    return {
        "error": "Endpoint not found",
        "message": "The /api/documents endpoint does not exist. Use the correct endpoints:",
        "correct_endpoints": {
            "document_uploads": "/api/document-upload/",
            "rag_documents": "/api/rag/documents",
            "workflow_status": "/api/document-workflow/status/{status}"
        },
        "documentation": "/docs"
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Health Check Endpoint"""
    return {
        "status": "healthy",
        "service": "DocuMind-AI V2",
        "version": "2.5.1"
    }


# ===== STARTUP EVENT =====

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    print("\n" + "=" * 60)
    print("🚀 DocuMind-AI V2 Backend Starting...")
    print("=" * 60)
    print("📦 Architecture: DDD + Hexagonal")
    print("🗄️  Database: SQLite (Development)")
    print("🔐 Auth: JWT Tokens")
    print("=" * 60 + "\n")
    
    # Future: Initialize default data, check DB connections, etc.


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
