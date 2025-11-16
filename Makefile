# Makefile for WhatsApp Bot Service
# Provides convenient commands for development and deployment

.PHONY: help install dev run docker-build docker-run docker-stop clean test lint format backup backup-docker restore

# Default target
help:
	@echo "WhatsApp Bot Service - Available Commands"
	@echo "==========================================="
	@echo ""
	@echo "Setup:"
	@echo "  make venv         Create virtual environment"
	@echo "  make setup-env    Create .env from template"
	@echo ""
	@echo "Development:"
	@echo "  make install       Install dependencies (requires venv)"
	@echo "  make install-dev   Install dev dependencies (requires venv)"
	@echo "  make dev          Run in development mode with auto-reload"
	@echo "  make run          Run in production mode"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  Build Docker image"
	@echo "  make docker-run    Run with Docker Compose"
	@echo "  make docker-stop   Stop Docker containers"
	@echo "  make docker-logs   View Docker logs"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format       Format code with black"
	@echo "  make lint         Run linter (ruff)"
	@echo "  make type-check   Run type checker (mypy)"
	@echo "  make test         Run tests"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        Clean up generated files"
	@echo ""
	@echo "Database:"
	@echo "  make backup        Backup local database"
	@echo "  make backup-docker Backup database from Docker container"
	@echo "  make restore       List and restore backups"
	@echo "  make db-reset      Delete database (with confirmation)"
	@echo ""

# Development setup
venv:
	@if [ -d .venv ]; then \
		echo "✗ Virtual environment already exists at .venv"; \
		echo "  To recreate it, run: rm -rf .venv && make venv"; \
	else \
		echo "Creating virtual environment..."; \
		python3 -m venv .venv; \
		echo ""; \
		echo "✓ Virtual environment created at .venv"; \
		echo ""; \
		echo "Activate it with:"; \
		echo "  source .venv/bin/activate    # On Linux/Mac"; \
		echo "  # or"; \
		echo "  .venv\\Scripts\\activate      # On Windows"; \
		echo ""; \
		echo "Then run: make install"; \
	fi

check-venv:
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo ""; \
		echo "❌ ERROR: No virtual environment detected!"; \
		echo ""; \
		echo "Please create and activate a virtual environment first:"; \
		echo ""; \
		echo "  python -m venv .venv"; \
		echo "  source .venv/bin/activate    # On Linux/Mac"; \
		echo "  # or"; \
		echo "  .venv\\Scripts\\activate      # On Windows"; \
		echo ""; \
		echo "Then run 'make install' or 'make install-dev' again."; \
		echo ""; \
		exit 1; \
	else \
		echo "✓ Virtual environment detected: $$VIRTUAL_ENV"; \
	fi

install: check-venv
	@echo "Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "✓ Dependencies installed successfully"

install-dev: check-venv
	@echo "Installing development dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install black ruff mypy pytest pytest-cov
	@echo "✓ Development dependencies installed successfully"

setup-env:
	@if [ ! -f .env ]; then \
		echo "Creating .env file from template..."; \
		cp env.example .env; \
		echo "✓ Created .env file. Please edit it with your credentials."; \
	else \
		echo "✗ .env file already exists"; \
	fi

# Running
dev:
	@echo "Starting development server with auto-reload..."
	DEV_RELOAD=true python run.py

run:
	@echo "Starting production server..."
	python run.py

# Docker commands
docker-build:
	@echo "Building Docker image..."
	docker build -t whatslang:latest .

docker-run:
	@echo "Starting services with Docker Compose..."
	docker-compose up -d
	@echo "✓ Services started"
	@echo "  Dashboard: http://localhost:8000/static/index.html"
	@echo "  Health: http://localhost:8000/health"

docker-stop:
	@echo "Stopping Docker containers..."
	docker-compose down

docker-logs:
	@echo "Showing Docker logs (Ctrl+C to exit)..."
	docker-compose logs -f

docker-restart:
	@echo "Restarting Docker containers..."
	docker-compose restart

# Code quality
format:
	@echo "Formatting code with black..."
	black .
	@echo "✓ Code formatted"

lint:
	@echo "Running linter..."
	ruff check .
	@echo "✓ Linting complete"

type-check:
	@echo "Running type checker..."
	mypy api/ core/ bots/
	@echo "✓ Type checking complete"

test:
	@echo "Running tests..."
	pytest
	@echo "✓ Tests complete"

test-cov:
	@echo "Running tests with coverage..."
	pytest --cov --cov-report=html --cov-report=term
	@echo "✓ Coverage report generated in htmlcov/"

# Utilities
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "✓ Cleanup complete"

# Database management
backup:
	@echo "Creating database backup..."
	@mkdir -p backups
	@if [ -f data/messages.db ]; then \
		TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
		cp data/messages.db backups/messages_$$TIMESTAMP.db; \
		sqlite3 data/messages.db .dump | gzip > backups/messages_$$TIMESTAMP.sql.gz; \
		echo "✓ Backup created:"; \
		echo "  - backups/messages_$$TIMESTAMP.db"; \
		echo "  - backups/messages_$$TIMESTAMP.sql.gz"; \
	else \
		echo "✗ No database file found at data/messages.db"; \
		exit 1; \
	fi

backup-docker:
	@echo "Creating database backup from Docker container..."
	@mkdir -p backups
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	docker exec whatslang-bot-service sqlite3 /data/messages.db .dump | gzip > backups/messages_$$TIMESTAMP.sql.gz; \
	echo "✓ Backup created: backups/messages_$$TIMESTAMP.sql.gz"

restore:
	@echo "Available backups:"
	@ls -lh backups/*.sql.gz 2>/dev/null || echo "No backups found"
	@echo ""
	@echo "To restore a backup, run:"
	@echo "  zcat backups/messages_TIMESTAMP.sql.gz | sqlite3 data/messages.db"

db-reset:
	@echo "⚠️  This will delete the message database!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -f data/messages.db; \
		echo "✓ Database deleted"; \
	else \
		echo "Cancelled"; \
	fi

# Deployment helpers
check-env:
	@echo "Checking environment configuration..."
	@if [ -f .env ]; then \
		echo "✓ .env file exists"; \
	else \
		echo "✗ .env file missing"; \
		exit 1; \
	fi
	@python -c "from dotenv import load_dotenv; import os; load_dotenv(); \
		required = ['WHATSAPP_BASE_URL', 'WHATSAPP_API_USER', 'WHATSAPP_API_PASSWORD', 'CHAT_JID', 'OPENAI_API_KEY']; \
		missing = [v for v in required if not os.environ.get(v)]; \
		exit(1) if missing else print('✓ All required variables set')" || \
		(echo "✗ Missing required environment variables" && exit 1)

health-check:
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health || (echo "✗ Service not responding" && exit 1)
	@echo ""
	@echo "✓ Service is healthy"

ready-check:
	@echo "Checking service readiness..."
	@curl -f http://localhost:8000/ready || (echo "✗ Service not ready" && exit 1)
	@echo ""
	@echo "✓ Service is ready"

