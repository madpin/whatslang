#!/bin/bash
# Quick start script for WhatSlang

set -e

echo "🚀 Starting WhatSlang..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo ""
    echo "Quick fix:"
    echo "  1. Copy the example file:"
    echo "     cp .env.example .env"
    echo ""
    echo "  2. Edit .env with your credentials:"
    echo "     nano .env"
    echo ""
    echo "See .env.example for all available configuration options."
    echo ""
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Start services
echo "📦 Starting Docker containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if backend is healthy
echo "🔍 Checking backend health..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start. Check logs with: docker-compose logs backend"
        exit 1
    fi
    sleep 2
done

echo ""
echo "✨ WhatSlang is running!"
echo ""
echo "📍 Endpoints:"
echo "   - Frontend: http://localhost:3000"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Health Check: http://localhost:8000/health"
echo ""
echo "📝 Useful commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Backend logs: docker-compose logs -f backend"
echo "   - Stop all: docker-compose down"
echo "   - Restart: docker-compose restart"
echo ""
echo "📖 Documentation: See docs/DEPLOYMENT.md for more details"
echo ""

