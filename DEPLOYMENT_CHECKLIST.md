# WhatSlang Deployment Checklist

Use this checklist to ensure your WhatSlang deployment is properly configured and ready for production.

## Pre-Deployment Checklist

### Environment Configuration

- [ ] `.env` file created from `.env.example`
- [ ] All required environment variables are set:
  - [ ] `WHATSAPP_BASE_URL` - Your WhatsApp API endpoint
  - [ ] `WHATSAPP_API_USER` - WhatsApp API username (if required)
  - [ ] `WHATSAPP_API_PASSWORD` - WhatsApp API password (if required)
  - [ ] `OPENAI_API_KEY` - Valid OpenAI or LLM API key
  - [ ] `DB_PASSWORD` - Strong database password (if using PostgreSQL)
- [ ] Optional variables configured as needed:
  - [ ] `OPENAI_BASE_URL` - Custom LLM endpoint (if applicable)
  - [ ] `OPENAI_MODEL` - Preferred model name
  - [ ] `LOG_LEVEL` - Set to `INFO` for production
  - [ ] `DEBUG` - Set to `false` for production

### Security

- [ ] Database password is strong and unique (min 16 characters)
- [ ] No hardcoded credentials in code
- [ ] `.env` file is in `.gitignore` (not committed to git)
- [ ] API keys are valid and have appropriate permissions
- [ ] WhatsApp API is secured with authentication

### Database

- [ ] Database choice confirmed:
  - [ ] **Option A**: Using PostgreSQL container (included in docker-compose)
  - [ ] **Option B**: Using external managed database (DATABASE_URL configured)
- [ ] Database backup strategy planned
- [ ] Database connection tested

### Docker & Infrastructure

- [ ] Docker and Docker Compose installed (if deploying with Docker)
- [ ] Sufficient disk space available (min 10GB recommended)
- [ ] Sufficient RAM available (min 2GB recommended)
- [ ] Ports are available and not in use:
  - [ ] Port 3000 (Frontend)
  - [ ] Port 8000 (Backend)
  - [ ] Port 5432 (PostgreSQL, if using container)

### External Services

- [ ] WhatsApp API instance is running and accessible
- [ ] WhatsApp API health check passes
- [ ] OpenAI/LLM API is accessible and has credits
- [ ] Network connectivity verified between services

---

## Deployment Steps

### Step 1: Initial Deployment

- [ ] Repository cloned or code uploaded to server
- [ ] `.env` file configured with production values
- [ ] Docker images built successfully
- [ ] All containers started without errors

### Step 2: Service Verification

- [ ] PostgreSQL container is healthy (if using)
  ```bash
  docker-compose ps postgres
  # Should show "healthy"
  ```
- [ ] Backend container is running
  ```bash
  docker-compose ps backend
  # Should show "Up"
  ```
- [ ] Frontend container is running
  ```bash
  docker-compose ps frontend
  # Should show "Up"
  ```

### Step 3: Health Checks

- [ ] Backend health endpoint responds
  ```bash
  curl http://localhost:8000/health
  # Should return: {"status":"healthy"}
  ```
- [ ] Frontend loads in browser
  ```
  http://localhost:3000
  ```
- [ ] API documentation accessible
  ```
  http://localhost:8000/docs
  ```

### Step 4: Database Initialization

- [ ] Database migrations completed successfully
- [ ] Database tables created
- [ ] No migration errors in logs

### Step 5: Functional Testing

- [ ] Can access frontend dashboard
- [ ] Health indicator shows "🟢 Online"
- [ ] Can create a bot via UI or API
- [ ] Can register a chat via UI or API
- [ ] Can assign bot to chat
- [ ] Backend logs show message processor started
- [ ] Backend logs show scheduler started

---

## Post-Deployment Verification

### Connectivity Tests

- [ ] Backend can reach WhatsApp API
  ```bash
  docker-compose exec backend curl $WHATSAPP_BASE_URL/health
  ```
- [ ] Backend can reach OpenAI API
  ```bash
  docker-compose exec backend python -c "import openai; print('OK')"
  ```
- [ ] Frontend can reach backend
  - Check browser console for errors
  - Verify API calls succeed

### Functional Tests

- [ ] Create a test bot (translation or custom)
- [ ] Register a test WhatsApp chat
- [ ] Assign bot to chat
- [ ] Send a test message in WhatsApp
- [ ] Verify bot processes and responds
- [ ] Check message appears in Messages page
- [ ] Create a test schedule
- [ ] Trigger schedule manually
- [ ] Verify scheduled message sent

### Monitoring

- [ ] Backend logs are clean (no errors)
  ```bash
  docker-compose logs backend | grep ERROR
  ```
- [ ] Frontend logs are clean
  ```bash
  docker-compose logs frontend | grep error
  ```
- [ ] Database logs are clean
  ```bash
  docker-compose logs postgres | grep ERROR
  ```

---

## Production-Specific Checklist

### For Dokploy Deployment

- [ ] Service created in Dokploy dashboard
- [ ] Git repository connected
- [ ] Environment variables configured in Dokploy UI
- [ ] Domain configured (if applicable)
- [ ] SSL/TLS enabled
- [ ] DNS records updated
- [ ] Deployment successful
- [ ] Health checks passing in Dokploy

### Performance & Scaling

- [ ] Resource limits configured (if needed)
  - See `docker-compose.prod.yml` for examples
- [ ] Restart policies set to `always`
- [ ] Log rotation configured
- [ ] Monitoring solution in place (optional)

### Backup & Recovery

- [ ] Database backup strategy implemented
- [ ] Backup schedule configured
- [ ] Backup restoration tested
- [ ] Volume backup included (postgres_data)

### Security Hardening

- [ ] Firewall rules configured
- [ ] Only necessary ports exposed
- [ ] SSL/TLS certificates valid
- [ ] Security headers configured (Nginx)
- [ ] Rate limiting considered (if needed)

---

## Troubleshooting Common Issues

### Backend Won't Start

- [ ] Check environment variables are set
- [ ] Verify database connection
- [ ] Check logs: `docker-compose logs backend`
- [ ] Ensure PostgreSQL is healthy
- [ ] Verify WhatsApp API is accessible

### Frontend Shows "Offline"

- [ ] Backend health check passes
- [ ] Network connectivity between containers
- [ ] Check browser console for errors
- [ ] Verify Nginx proxy configuration

### Bot Not Responding

- [ ] Bot is enabled
- [ ] Bot is assigned to chat
- [ ] Chat is registered correctly
- [ ] Message processor is running (check logs)
- [ ] WhatsApp API is receiving messages
- [ ] OpenAI API key is valid

### Database Connection Errors

- [ ] PostgreSQL container is healthy
- [ ] DATABASE_URL is correct
- [ ] DB_PASSWORD matches in all places
- [ ] Network connectivity between containers
- [ ] Database exists and is initialized

---

## Rollback Plan

In case of deployment issues:

- [ ] Previous version tagged in git
- [ ] Rollback command prepared:
  ```bash
  git checkout <previous-version>
  docker-compose down
  docker-compose up -d --build
  ```
- [ ] Database backup available for restoration
- [ ] Rollback tested in staging environment

---

## Sign-Off

**Deployment Date**: _______________

**Deployed By**: _______________

**Verified By**: _______________

**Environment**: 
- [ ] Development
- [ ] Staging  
- [ ] Production

**Notes**:
_____________________________________________
_____________________________________________
_____________________________________________

---

## Quick Reference Commands

```bash
# View all logs
docker-compose logs -f

# View backend logs only
docker-compose logs -f backend

# Check container status
docker-compose ps

# Restart all services
docker-compose restart

# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# Rebuild and restart
docker-compose up -d --build

# Check backend health
curl http://localhost:8000/health

# Access backend shell
docker-compose exec backend bash

# Access database
docker-compose exec postgres psql -U whatslang

# View environment variables
docker-compose exec backend env

# Check disk usage
docker system df

# Backup database
docker exec whatslang-db pg_dump -U whatslang whatslang > backup.sql
```

---

## Additional Resources

- **Deployment Guide**: `docs/DEPLOYMENT.md`
- **Development Guide**: `docs/DEVELOPMENT.md`
- **Main README**: `README.md`
- **API Documentation**: http://your-domain.com/docs

---

**Status**: 
- [ ] ✅ All checks passed - Ready for production
- [ ] ⚠️ Some issues found - Needs attention
- [ ] ❌ Critical issues - Do not deploy

