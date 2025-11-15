#!/bin/bash
# Local development start script (uses SQLite)

set -e

echo "🚀 Starting WhatSlang (Local Development with SQLite)..."
echo ""

# Find the best Python version to use
PYTHON_CMD=""

# Try to find Python 3.11 or 3.12 first (preferred)
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo "✅ Found Python 3.11"
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo "✅ Found Python 3.12"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MINOR" -ge 14 ]; then
        echo "⚠️  WARNING: Default python3 is version $PYTHON_VERSION"
        echo "   Python 3.14+ is too new and may not be compatible."
    echo ""
    echo "   ❌ Aborting. Please use Python 3.11 or 3.12"
    echo ""
    echo "   Quick fix:"
    echo "   1. Install Python 3.11 or 3.12"
    echo "   2. Delete old venv: rm -rf backend/.venv"
    echo "   3. Run this script again (it will use python3.11 automatically)"
    echo ""
    exit 1
    fi
    echo "✅ Using Python $PYTHON_VERSION"
else
    echo "❌ Error: No Python 3 installation found"
    exit 1
fi

echo "🐍 Using: $PYTHON_CMD"
echo ""

# Check if we're in the backend directory
if [ ! -f "app/main.py" ]; then
    if [ -d "backend" ]; then
        echo "📂 Changing to backend directory..."
        cd backend
    else
        echo "❌ Error: Cannot find backend directory or app/main.py"
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment with $PYTHON_CMD..."
    $PYTHON_CMD -m venv .venv
else
    # Check if existing venv is using the wrong Python version
    if [ -d ".venv" ]; then
        VENV_PYTHON_VERSION=$(.venv/bin/python --version 2>&1 | awk '{print $2}')
        VENV_PYTHON_MINOR=$(echo $VENV_PYTHON_VERSION | cut -d. -f2)
        
        if [ "$VENV_PYTHON_MINOR" -ge 14 ]; then
            echo "⚠️  WARNING: Existing .venv uses Python $VENV_PYTHON_VERSION (too new!)"
            echo "   Recreating with $PYTHON_CMD..."
            rm -rf .venv
            $PYTHON_CMD -m venv .venv
        fi
    fi
fi

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "🔌 Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "🔌 Activating virtual environment (venv)..."
    source venv/bin/activate
fi

# Check if requirements are installed
echo "📋 Checking dependencies..."
if ! $PYTHON_CMD -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies (SQLite version - no PostgreSQL needed)..."
    pip install --upgrade pip
    pip install -r requirements-local.txt
fi

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "📄 Loading environment variables from .env file..."
    set -a  # automatically export all variables
    source .env
    set +a
    echo "✅ Environment loaded"
elif [ ! -z "$WHATSAPP_BASE_URL" ] && [ ! -z "$OPENAI_API_KEY" ]; then
    echo "✅ Environment variables found in shell"
else
    echo ""
    echo "⚠️  ERROR: Missing required environment variables!"
    echo ""
    echo "   Required:"
    echo "   - WHATSAPP_BASE_URL"
    echo "   - OPENAI_API_KEY"
    echo ""
    echo "   Quick fix:"
    echo "   1. Copy .env.example to backend/.env"
    echo "      cp .env.example backend/.env"
    echo ""
    echo "   2. Edit backend/.env with your credentials"
    echo "      nano backend/.env"
    echo ""
    echo "   See .env.example for all available options"
    echo ""
    exit 1
fi

# Check if database exists, if not initialize it
if [ ! -f "whatslang.db" ]; then
    echo "🗄️  Initializing SQLite database..."
    python run_migrations.py
fi

echo ""
echo "✨ Starting WhatSlang with SQLite..."
echo ""
echo "📍 Endpoints:"
echo "   - API: http://localhost:8000"
echo "   - Docs: http://localhost:8000/docs"
echo "   - Health: http://localhost:8000/health"
echo ""
echo "💾 Database: whatslang.db (SQLite)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

