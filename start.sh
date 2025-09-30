#!/bin/bash

# DocuMind-AI V2 Starter Script
# Quick start with Docker Compose

echo "🚀 Starting DocuMind-AI V2..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Build and start services
echo "📦 Building and starting services..."
docker-compose up -d --build

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
echo "🎉 DocuMind-AI V2 is starting!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📊 Access Points:"
echo "   🌐 Frontend:  http://localhost:3000"
echo "   🔧 Backend:   http://localhost:8000"
echo "   📚 API Docs:  http://localhost:8000/docs"
echo ""
echo "📋 Useful Commands:"
echo "   🛑 Stop:      docker-compose down"
echo "   📝 Logs:      docker-compose logs -f"
echo "   🔄 Restart:   docker-compose restart"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

# Offer to show logs
read -p "Show live logs? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose logs -f
fi
