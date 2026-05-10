# Whatslang — convenience targets

.PHONY: help venv install install-dev dev run web-install web-dev web-build \
        docker-build docker-up docker-down docker-logs docker-restart \
        format lint typecheck check clean backup health

help:
	@echo "Whatslang"
	@echo "========="
	@echo ""
	@echo "Setup"
	@echo "  make venv          Create .venv if missing"
	@echo "  make install       Install Python deps into the active venv"
	@echo "  make install-dev   Install Python deps + dev tooling"
	@echo "  make web-install   npm install in web/"
	@echo ""
	@echo "Run"
	@echo "  make dev           Run uvicorn with reload (backend)"
	@echo "  make run           Run uvicorn (production-style, backend)"
	@echo "  make web-dev       Vite dev server (proxies to backend)"
	@echo "  make web-build     Build the SPA (web/dist served by FastAPI)"
	@echo ""
	@echo "Docker"
	@echo "  make docker-build  docker compose build"
	@echo "  make docker-up     docker compose up -d"
	@echo "  make docker-down   docker compose down"
	@echo "  make docker-logs   tail compose logs"
	@echo "  make docker-restart"
	@echo ""
	@echo "Quality"
	@echo "  make format        ruff format"
	@echo "  make lint          ruff check"
	@echo "  make typecheck     web typecheck (tsc -b --noEmit)"
	@echo "  make check         lint + typecheck"
	@echo ""
	@echo "Misc"
	@echo "  make clean         Remove caches"
	@echo "  make backup        Snapshot data/messages.db"
	@echo "  make health        curl /health"

venv:
	@if [ -d .venv ]; then \
		echo ".venv already exists"; \
	else \
		python3 -m venv .venv && echo "Created .venv. Activate with: source .venv/bin/activate"; \
	fi

check-venv:
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "ERROR: activate a virtualenv first (source .venv/bin/activate)"; \
		exit 1; \
	fi

install: check-venv
	pip install --upgrade pip
	pip install -r requirements.txt

install-dev: check-venv
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install ruff pytest pytest-cov

dev:
	@if [ -z "$$VIRTUAL_ENV" ]; then echo "Activate .venv first"; exit 1; fi
	uvicorn app.main:app --reload --host 0.0.0.0 --port $${PORT:-8000}

run:
	@if [ -z "$$VIRTUAL_ENV" ]; then echo "Activate .venv first"; exit 1; fi
	python -m app

web-install:
	cd web && npm install --no-audit --no-fund

web-dev:
	cd web && npm run dev

web-build:
	cd web && npm run build

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-restart:
	docker compose restart

format:
	ruff format app

lint:
	ruff check app

typecheck:
	cd web && npm run typecheck

check: lint typecheck

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf web/node_modules web/dist 2>/dev/null || true

backup:
	@mkdir -p backups
	@TS=$$(date +%Y%m%d_%H%M%S); \
	if [ -f data/messages.db ]; then \
		cp data/messages.db backups/messages_$$TS.db && \
		echo "backups/messages_$$TS.db"; \
	else \
		echo "data/messages.db not found"; exit 1; \
	fi

health:
	@curl -fsSL http://localhost:8000/health || (echo "service not responding" && exit 1)
	@echo
