"""
🚀 DocuMind-AI V2 - Clean DDD Backend

Minimales FastAPI Backend mit:
- DDD Architecture (Hexagonal/Clean)
- Interest Groups Context
- Users Context (RBAC)
- Access Control Context (Auth/JWT)

Version: 2.0.0
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

# Add project root and contexts to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import database
from .database import Base, engine

# Create all tables
Base.metadata.create_all(bind=engine)

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
    - 📊 ISO 13485 Ready
    
    **Tech Stack:**
    - FastAPI (Python 3.12+)
    - SQLAlchemy ORM
    - Pydantic V2
    - JWT Tokens
    """,
    version="2.0.0",
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


# ===== HEALTH & STATUS ENDPOINTS =====

@app.get("/", tags=["System"])
async def root():
    """API Root - System Information"""
    return {
        "service": "DocuMind-AI V2",
        "version": "2.0.0",
        "architecture": "DDD + Hexagonal",
        "status": "running",
        "endpoints": {
            "api_docs": "/docs",
            "health": "/health",
            "interest_groups": "/api/interest-groups",
            "users": "/api/users",
            "auth": "/api/auth",
        }
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Health Check Endpoint"""
    return {
        "status": "healthy",
        "service": "DocuMind-AI V2",
        "version": "2.0.0"
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
