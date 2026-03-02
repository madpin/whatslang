# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-11-16

### Added

#### Production Features
- **Health Check Endpoints**: `/health` (liveness) and `/ready` (readiness) for container orchestration
- **Structured Logging**: JSON logs in production, human-readable in development
- **Graceful Shutdown**: Proper cleanup of running bots on shutdown
- **Environment-based Configuration**: Support for `.env` files with `python-dotenv`
- **Request Logging Middleware**: Automatic HTTP request/response logging with duration tracking

#### Deployment
- **Docker Support**: Multi-stage Dockerfile with non-root user for security
- **Docker Compose**: Production-ready compose configuration with health checks
- **Nixpacks Configuration**: `nixpacks.toml` for dokploy deployment
- **Kubernetes Ready**: Health checks and resource limits compatible with K8s

#### Documentation
- **Comprehensive README**: Production deployment guide with examples
- **Quick Start Guide**: Updated with Docker and Dokploy instructions
- **Deployment Guide**: Detailed deployment scenarios (Dokploy, Docker, K8s, VPS)
- **Contributing Guide**: Guidelines for contributors
- **License**: MIT license added

#### Configuration
- **Config Validation**: Validates required environment variables at startup
- **Config Flexibility**: `config.yaml` now optional, environment variables take precedence
- **CORS Configuration**: Configurable via `ALLOWED_ORIGINS` environment variable

#### Project Structure
- **pyproject.toml**: Modern Python project configuration
- **.dockerignore**: Optimized Docker builds
- **env.example**: Template for environment configuration

### Changed

- **FastAPI Lifespan**: Migrated from deprecated `@app.on_event` to modern lifespan context manager
- **Logging System**: Complete overhaul with structured logging and configurable levels
- **API Responses**: Enhanced with proper HTTP status codes and error handling
- **Documentation Visibility**: API docs (`/docs`, `/redoc`) disabled in production mode for security

### Improved

- **Error Messages**: More descriptive error messages with context
- **Startup Sequence**: Better initialization logging and error handling
- **Dependencies**: Pinned versions with production dependencies added
- **Security**: Non-root Docker user, no hardcoded secrets, validated inputs

### Fixed

- **Configuration Loading**: Handles missing `config.yaml` gracefully
- **Bot Manager**: Proper cleanup on shutdown prevents zombie processes
- **CORS Issues**: Configurable origins for proper CORS handling

## [1.0.0] - Previous Version

### Features

- Multiple concurrent WhatsApp bots
- Web dashboard for bot management
- Real-time log viewing
- Modular bot architecture
- Translation bot (Portuguese ↔ English)
- Joke bot
- SQLite message tracking
- FastAPI backend
- Static frontend

---

## Version History

- **2.0.0** - Production-ready release with Docker, Nixpacks, and comprehensive deployment support
- **1.0.0** - Initial functional release with core features

---

[2.0.0]: https://github.com/yourusername/whatslang/releases/tag/v2.0.0
[1.0.0]: https://github.com/yourusername/whatslang/releases/tag/v1.0.0

