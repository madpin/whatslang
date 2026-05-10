# syntax=docker/dockerfile:1.6

# ---- Frontend build (Vite/React/TS) ---------------------------------------
FROM node:22-alpine AS web_build
WORKDIR /web

COPY web/package.json web/package-lock.json* ./
RUN npm ci --no-audit --no-fund

COPY web/ ./
RUN npm run build

# ---- Python dependencies --------------------------------------------------
FROM python:3.11-slim AS pybuilder
WORKDIR /build

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update -o Acquire::Retries=3 \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# ---- Runtime image --------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DB_PATH=/data/messages.db \
    HOST=0.0.0.0 \
    PORT=8000

# OS packages (its own layer so it caches independently of code).
RUN apt-get update -o Acquire::Retries=3 \
 && apt-get install -y --no-install-recommends \
        curl \
        ffmpeg \
        ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Non-root user + persistent data dir.
RUN useradd -m -u 1000 appuser \
 && mkdir -p /data \
 && chown -R appuser:appuser /data

WORKDIR /app

# Python dependencies from the builder stage.
COPY --from=pybuilder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=pybuilder /usr/local/bin /usr/local/bin

# Application code + frontend bundle.
COPY --chown=appuser:appuser app/ /app/app/
COPY --chown=appuser:appuser README.md /app/README.md
COPY --from=web_build --chown=appuser:appuser /web/dist /app/web/dist

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:${PORT:-8000}/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
