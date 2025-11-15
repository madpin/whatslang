# WhatSlang Deployment Guide

This guide covers deploying WhatSlang to production, with specific instructions for Dokploy and other platforms.

## Table of Contents

- [Quick Start with Dokploy](#quick-start-with-dokploy)
- [Database Options](#database-options)
- [Environment Configuration](#environment-configuration)
- [Docker Deployment](#docker-deployment)
- [Health Checks & Monitoring](#health-checks--monitoring)
- [Troubleshooting](#troubleshooting)

---

## Quick Start with Dokploy

Dokploy makes it easy to deploy WhatSlang using Docker Compose.

### Prerequisites

- Dokploy instance running
- Git repository with your WhatSlang code
- WhatsApp API instance (go-whatsapp-web-multidevice)
- OpenAI API key or compatible LLM endpoint

### Step 1: Create a New Service in Dokploy

1. Log in to your Dokploy dashboard
2. Click **"Create Service"** or **"New Application"**
3. Select **"Docker Compose"** as the deployment type
4. Connect your Git repository

### Step 2: Configure Environment Variables

In Dokploy's environment variables section, add the following:

#### Required Variables

```bash
# WhatsApp API
WHATSAPP_BASE_URL=https://your-whatsapp-api.example.com
WHATSAPP_API_USER=your_username
WHATSAPP_API_PASSWORD=your_password

# OpenAI/LLM
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Database (if using PostgreSQL container)
DB_PASSWORD=your_secure_database_password
```

#### Optional Variables

```bash
# Custom LLM endpoint (e.g., LiteLLM, Azure OpenAI)
OPENAI_BASE_URL=https://your-litellm-endpoint.com

# Bot behavior tuning
POLL_INTERVAL_SECONDS=5
MESSAGE_LIMIT_PER_POLL=20

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

### Step 3: Choose Your Docker Compose File

Dokploy will automatically detect `docker-compose.yml` in your repository root.

**For production deployment**, you can use the production override:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Or configure Dokploy to use both files in the deployment settings.

### Step 4: Deploy

1. Click **"Deploy"** in Dokploy
2. Wait for the build and deployment to complete (2-5 minutes)
3. Check the logs to ensure all services started successfully

### Step 5: Verify Deployment

Once deployed, verify the services are running:

1. **Backend Health Check**: `https://your-domain.com/health`
   - Should return: `{"status":"healthy"}`

2. **Frontend**: `https://your-domain.com`
   - Should load the WhatSlang dashboard

3. **API Documentation**: `https://your-domain.com/docs`
   - Should show the interactive API documentation

### Step 6: Configure Domain & SSL

In Dokploy:

1. Go to your service settings
2. Add your custom domain
3. Enable SSL/TLS (Dokploy handles Let's Encrypt automatically)
4. Update your DNS records to point to your Dokploy server

---

## Database Options

WhatSlang supports two database configurations for production:

### Option A: PostgreSQL Container (Recommended for Dokploy)

**Advantages:**
- ✅ Simple setup - included in `docker-compose.yml`
- ✅ Automatic backups via Docker volumes
- ✅ No external dependencies
- ✅ Works out-of-the-box with Dokploy

**Configuration:**

The default `docker-compose.yml` includes a PostgreSQL container. Just set the `DB_PASSWORD` environment variable:

```bash
DB_PASSWORD=your_secure_password_here
```

The database URL is automatically configured:
```bash
DATABASE_URL=postgresql://whatslang:${DB_PASSWORD}@postgres:5432/whatslang
```

**Data Persistence:**

Data is stored in a Docker volume named `postgres_data`. To back up:

```bash
# Backup
docker exec whatslang-db pg_dump -U whatslang whatslang > backup.sql

# Restore
docker exec -i whatslang-db psql -U whatslang whatslang < backup.sql
```

### Option B: External Managed Database

**Advantages:**
- ✅ Better for high-traffic production
- ✅ Managed backups and scaling
- ✅ High availability options
- ✅ Separate from application lifecycle

**Supported Providers:**
- AWS RDS PostgreSQL
- Google Cloud SQL
- Azure Database for PostgreSQL
- DigitalOcean Managed Databases
- Supabase
- Neon
- Any PostgreSQL 15+ instance

**Configuration:**

1. Create a PostgreSQL database on your provider
2. Get the connection string
3. Set the `DATABASE_URL` environment variable:

```bash
DATABASE_URL=postgresql://username:password@host:5432/database
```

4. **Important**: If using an external database, you need to modify `docker-compose.yml` to remove the `postgres` service dependency:

In `docker-compose.yml`, update the backend service:

```yaml
backend:
  # Remove or comment out:
  # depends_on:
  #   postgres:
  #     condition: service_healthy
  
  environment:
    DATABASE_URL: ${DATABASE_URL}  # Use external database
```

And comment out or remove the entire `postgres` service section.

---

## Environment Configuration

### Complete Environment Variables Reference

Create a `.env` file based on `.env.example`:

```bash
# Copy the example file
cp .env.example .env

# Edit with your values
nano .env  # or vim, code, etc.
```

#### Application Settings

```bash
APP_NAME=WhatSlang
DEBUG=false                    # Set to true only for debugging
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

#### Database Configuration

```bash
# For PostgreSQL container (default):
DATABASE_URL=postgresql://whatslang:${DB_PASSWORD}@postgres:5432/whatslang
DB_PASSWORD=your_secure_password

# For external PostgreSQL:
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# For local development (SQLite):
DATABASE_URL=sqlite+aiosqlite:///./whatslang.db
```

#### WhatsApp API

```bash
WHATSAPP_BASE_URL=https://your-whatsapp-api.example.com
WHATSAPP_API_USER=your_username        # Optional, if API requires auth
WHATSAPP_API_PASSWORD=your_password    # Optional, if API requires auth
```

#### OpenAI / LLM

```bash
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=                       # Optional: custom endpoint
OPENAI_MODEL=gpt-4o-mini              # Or gpt-4, gpt-3.5-turbo, etc.
```

#### Bot Behavior

```bash
POLL_INTERVAL_SECONDS=5               # How often to check for new messages
MESSAGE_LIMIT_PER_POLL=20             # Max messages per poll
```

#### Server Settings

```bash
HOST=0.0.0.0                          # Don't change for Docker
PORT=8000                             # Backend port
RELOAD=false                          # Set to true only for development
```

---

## Docker Deployment

### Using Docker Compose (Standard)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd whatslang

# 2. Create and configure .env file
cp .env.example .env
nano .env  # Add your credentials

# 3. Start all services
docker-compose up -d

# 4. Check logs
docker-compose logs -f backend

# 5. Verify health
curl http://localhost:8000/health
```

### Using Docker Compose (Production)

For production with optimized settings:

```bash
# Use production overrides
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

The production configuration includes:
- No volume mounts for code (uses built image)
- Proper restart policies
- Optimized resource limits
- Production-ready settings

### Port Mappings

Default ports:
- **Frontend**: `3000` → Nginx serving React app
- **Backend**: `8000` → FastAPI application
- **PostgreSQL**: `5432` → Database (only if using container)

To change ports, modify `docker-compose.yml` or use environment variables.

### Updating the Deployment

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build

# Or with production config:
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

---

## Health Checks & Monitoring

### Built-in Health Checks

**Backend Health Check:**
```bash
curl http://your-domain.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "app": "WhatSlang",
  "version": "0.1.0"
}
```

**Frontend Health:**
- Access `http://your-domain.com`
- Check for "🟢 Online" indicator in top-right corner

### Docker Health Checks

The containers include built-in health checks:

```bash
# Check container health
docker ps

# Backend should show "healthy" status
# PostgreSQL should show "healthy" status
```

### Monitoring Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# PostgreSQL
docker-compose logs -f postgres
```

### Common Health Check Issues

**Backend shows unhealthy:**
1. Check environment variables are set correctly
2. Verify database connection: `docker-compose logs postgres`
3. Check WhatsApp API is accessible
4. Review backend logs: `docker-compose logs backend`

**Frontend shows "🔴 Offline":**
1. Backend is not running or not accessible
2. Check backend health endpoint
3. Verify network configuration in `docker-compose.yml`

---

## Troubleshooting

### Database Connection Issues

**Error: "could not connect to server"**

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Verify DATABASE_URL is correct
docker-compose exec backend env | grep DATABASE_URL
```

**Solution:**
- Ensure `DB_PASSWORD` matches in both backend and postgres services
- Wait for PostgreSQL to be fully ready (health check)
- Check network connectivity between containers

### WhatsApp API Connection Issues

**Error: "Failed to fetch messages from WhatsApp API"**

```bash
# Test WhatsApp API from backend container
docker-compose exec backend curl $WHATSAPP_BASE_URL/health

# Check environment variables
docker-compose exec backend env | grep WHATSAPP
```

**Solution:**
- Verify `WHATSAPP_BASE_URL` is accessible from the container
- Check authentication credentials if required
- Ensure WhatsApp API is running and healthy

### OpenAI API Issues

**Error: "Invalid API key" or "Rate limit exceeded"**

```bash
# Verify API key is set
docker-compose exec backend env | grep OPENAI_API_KEY
```

**Solution:**
- Check API key is valid and has credits
- Verify `OPENAI_BASE_URL` if using custom endpoint
- Check rate limits on your OpenAI account

### Port Conflicts

**Error: "port is already allocated"**

```bash
# Check what's using the port
lsof -i :8000  # or :3000, :5432

# Kill the process or change ports in docker-compose.yml
```

**Solution:**
- Stop conflicting services
- Or modify port mappings in `docker-compose.yml`

### Container Won't Start

```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs backend

# Restart specific service
docker-compose restart backend

# Full restart
docker-compose down
docker-compose up -d
```

### Database Migration Issues

**Error: "relation does not exist"**

The database needs to be initialized:

```bash
# Run migrations manually
docker-compose exec backend python run_migrations.py

# Or restart backend (migrations run on startup)
docker-compose restart backend
```

### Out of Memory / Resource Issues

```bash
# Check container resource usage
docker stats

# Increase Docker resources in Docker Desktop settings
# Or add resource limits in docker-compose.yml
```

---

## Production Checklist

Before going live, verify:

- [ ] All environment variables are set correctly
- [ ] Database is using PostgreSQL (not SQLite)
- [ ] Strong database password is set
- [ ] SSL/TLS is enabled (HTTPS)
- [ ] Domain is configured correctly
- [ ] Health checks are passing
- [ ] Logs are being collected
- [ ] Backups are configured (database)
- [ ] WhatsApp API is accessible
- [ ] OpenAI API key is valid and has credits
- [ ] Frontend loads correctly
- [ ] API documentation is accessible
- [ ] Test bot is working in a chat

---

## Support & Additional Resources

- **Main Documentation**: See `README.md`
- **Frontend Guide**: See `docs/QUICK_START_FRONTEND.md`
- **Development Guide**: See `docs/DEVELOPMENT.md`
- **API Documentation**: `https://your-domain.com/docs`

For issues and questions, please open a GitHub issue.

