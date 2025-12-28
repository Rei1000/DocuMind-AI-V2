#!/bin/bash

# DocuMind-AI V2 Starter Script
# Supports Docker and Local development modes

set -e  # Exit on error

# ════════════════════════════════════════════════════════════
# 📋 USAGE
# ════════════════════════════════════════════════════════════
# ./start.sh          - Start with Docker (default)
# ./start.sh docker   - Start with Docker
# ./start.sh local    - Start locally (Backend + Frontend)
# ════════════════════════════════════════════════════════════

MODE="${1:-docker}"  # Default: docker

# ════════════════════════════════════════════════════════════
# 🧰 Docker Compose Helper (v1/v2 kompatibel)
# ════════════════════════════════════════════════════════════

compose_cmd() {
    # Docker Desktop nutzt häufig `docker compose` (v2). Manche Systeme haben noch `docker-compose` (v1).
    if docker compose version > /dev/null 2>&1; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

COMPOSE="$(compose_cmd)"

echo "🚀 Starting DocuMind-AI V2..."
echo "   Mode: $MODE"
echo ""

# ════════════════════════════════════════════════════════════
# 🧹 CLEANUP: Stop old processes and free ports
# ════════════════════════════════════════════════════════════

echo "🧹 Cleaning up old processes..."

# 1. Stop Docker containers gracefully
echo "   🐳 Stopping Docker containers..."
$COMPOSE down --remove-orphans > /dev/null 2>&1 || true

# 2. Kill Node.js processes (Frontend)
echo "   🔴 Stopping Node.js processes..."
killall -9 node > /dev/null 2>&1 || true

# 3. Free ports 3000, 8000, 6333
echo "   🔓 Freeing ports 3000, 8000, 6333..."
lsof -ti:3000,8000,6333 | xargs kill -9 > /dev/null 2>&1 || true

# 4. Clear Next.js cache
echo "   🗑️  Clearing Next.js cache..."
rm -rf frontend/.next > /dev/null 2>&1 || true
rm -rf frontend/node_modules/.cache > /dev/null 2>&1 || true

# 5. Clear Python cache
echo "   🗑️  Clearing Python cache..."
find . -type d -name __pycache__ -exec rm -rf {} + > /dev/null 2>&1 || true
find . -type f -name "*.pyc" -delete > /dev/null 2>&1 || true

echo "   ✅ Cleanup complete!"
echo ""

# Wait for ports to be fully released
sleep 2

# ════════════════════════════════════════════════════════════
# 🚀 START SERVICES
# ════════════════════════════════════════════════════════════

if [ "$MODE" == "docker" ]; then
    # ═══════════════════════════════════════════════════════
    # 🐳 DOCKER MODE
    # ═══════════════════════════════════════════════════════
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker first."
        exit 1
    fi
    
    echo "✅ Docker is running"
    echo ""

    # Ensure `.env` exists for container runtime keys (OpenAI/Gemini etc.)
    if [ ! -f ".env" ]; then
        echo "⚠️  Missing .env file in project root."
        echo "   Docker needs runtime environment variables (e.g. OPENAI_API_KEY / OPENAI_GPT5_MINI_API_KEY)."
        echo "   Create a .env file (NOT committed) before starting Docker."
        echo ""
    fi
    
    # Build and start services
    echo "📦 Building and starting Docker services..."
    $COMPOSE up -d --build
    
    # Wait for services to be healthy
    echo ""
    echo "⏳ Waiting for services to be ready..."
    sleep 5
    
    # Check backend
    echo ""
    echo "🔍 Checking Backend..."
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy (http://localhost:8000)"
    else
        echo "⚠️  Backend is starting..."
    fi
    
    # Check frontend
    echo ""
    echo "🔍 Checking Frontend..."
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend is healthy (http://localhost:3000)"
    else
        echo "⚠️  Frontend is starting..."
    fi
    
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "🎉 DocuMind-AI V2 (Docker Mode) is starting!"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "📊 Access Points:"
    echo "   🌐 Frontend:  http://localhost:3000"
    echo "   🔧 Backend:   http://localhost:8000"
    echo "   📚 API Docs:  http://localhost:8000/docs"
    echo ""
    echo "📋 Useful Commands:"
    echo "   🛑 Stop:      $COMPOSE down"
    echo "   📝 Logs:      $COMPOSE logs -f"
    echo "   🔄 Restart:   $COMPOSE restart"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    
    # Offer to show logs (nur interaktiv)
    if [ -t 0 ] && [ "${DOCUMIND_NONINTERACTIVE:-}" != "1" ]; then
        read -p "Show live logs? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            $COMPOSE logs -f
        fi
    fi
    
elif [ "$MODE" == "local" ]; then
    # ═══════════════════════════════════════════════════════
    # 💻 LOCAL MODE
    # ═══════════════════════════════════════════════════════
    
    echo "💻 Starting services locally..."
    echo ""
    
    # 1. Initialize database (only if it doesn't exist)
    DATABASE_PATH="/Users/reiner/Documents/DocuMind-AI-V2/data/qms.db"
    if [ ! -f "$DATABASE_PATH" ]; then
        echo "🌱 Initializing database..."
        python3 backend/init_database.py
        echo ""
    else
        echo "✅ Using existing database: $DATABASE_PATH"
        echo ""
    fi
    
    # 2. Start Qdrant Vector Store
    echo "🔍 Starting Qdrant Vector Store (http://localhost:6333)..."
    ./bin/qdrant --config-path data/qdrant/config.yaml > qdrant.log 2>&1 &
    QDRANT_PID=$!
    echo "   Qdrant PID: $QDRANT_PID"
    
    # Wait for Qdrant
    sleep 3
    
    # 3. Start Backend in background
    echo "🐍 Starting Backend (http://localhost:8000)..."
    python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
    BACKEND_PID=$!
    echo "   Backend PID: $BACKEND_PID"
    
    # Wait for backend
    sleep 3
    
    # 4. Start Frontend in background
    echo "⚛️  Starting Frontend (http://localhost:3000)..."
    cd frontend && PORT=3000 npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "   Frontend PID: $FRONTEND_PID"
    cd ..
    
    # Wait for services
    sleep 5
    
    # Check services
    echo ""
    echo "🔍 Checking services..."
    if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
        echo "✅ Qdrant is healthy (http://localhost:6333)"
    else
        echo "⚠️  Qdrant failed to start. Check qdrant.log"
    fi
    
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy (http://localhost:8000)"
    else
        echo "⚠️  Backend failed to start. Check backend.log"
    fi
    
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend is healthy (http://localhost:3000)"
    else
        echo "⚠️  Frontend failed to start. Check frontend.log"
    fi
    
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "🎉 DocuMind-AI V2 (Local Mode) is running!"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "📊 Access Points:"
    echo "   🌐 Frontend:  http://localhost:3000"
    echo "   🔧 Backend:   http://localhost:8000"
    echo "   📚 API Docs:  http://localhost:8000/docs"
    echo "   🔍 Qdrant:    http://localhost:6333/dashboard"
    echo ""
    echo "📋 Process IDs:"
    echo "   Qdrant:   $QDRANT_PID"
    echo "   Backend:  $BACKEND_PID"
    echo "   Frontend: $FRONTEND_PID"
    echo ""
    echo "📝 Logs:"
    echo "   Qdrant:   tail -f qdrant.log"
    echo "   Backend:  tail -f backend.log"
    echo "   Frontend: tail -f frontend.log"
    echo ""
    echo "🛑 To stop:"
    echo "   kill $QDRANT_PID $BACKEND_PID $FRONTEND_PID"
    echo "   # OR"
    echo "   killall -9 node python3 qdrant"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    
else
    echo "❌ Invalid mode: $MODE"
    echo ""
    echo "Usage:"
    echo "  ./start.sh          - Start with Docker (default)"
    echo "  ./start.sh docker   - Start with Docker"
    echo "  ./start.sh local    - Start locally"
    exit 1
fi
