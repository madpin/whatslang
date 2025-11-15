# Dokploy Deployment Guide

This guide will help you deploy WhatSlang to Dokploy using pre-built Docker images from GitHub Container Registry.

## 📋 Prerequisites

### 1. Dokploy Instance
- A running Dokploy instance (self-hosted or managed)
- Access to Dokploy dashboard
- Domain name configured (optional but recommended)

### 2. External Services
- **WhatsApp API**: [go-whatsapp-web-multidevice](https://github.com/aldinokemal/go-whatsapp-web-multidevice) instance
- **LLM API**: OpenAI API key or compatible LLM endpoint

### 3. GitHub Container Registry Access
For **public images**: No authentication needed
For **private images**: GitHub Personal Access Token with `read:packages` scope

## 🚀 Quick Start (5 Minutes)

### Step 1: Create Application in Dokploy

1. Log in to your Dokploy dashboard
2. Click **"Create Application"**
3. Select **"Compose"** as the application type
4. Enter application details:
   - **Name**: `whatslang`
   - **Description**: `WhatsApp Bot Platform`

### Step 2: Connect GitHub Repository

1. Click **"Connect Repository"**
2. Select **GitHub** as the provider
3. Authorize Dokploy to access your repositories
4. Select repository: `madpin/whatslang`
5. Select branch: `main`
6. Set compose file path: `docker-compose.dokploy.yml`

### Step 3: Configure Environment Variables

In the Dokploy UI, add these environment variables:

#### Required Variables

```bash
# Database (Dokploy will generate a secure password)
DB_PASSWORD=your_secure_password_here

# WhatsApp API (REQUIRED)
WHATSAPP_API_URL=https://your-whatsapp-api.example.com
WHATSAPP_API_TOKEN=your_api_token_here
# OR if using basic auth:
WHATSAPP_API_USER=your_username
WHATSAPP_API_PASSWORD=your_password

# LLM API (at least one required)
OPENAI_API_KEY=sk-your-api-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

#### Optional Variables

```bash
# Database settings
DB_NAME=whatslang
DB_USER=whatslang

# LLM settings
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Application settings
DEBUG=false
LOG_LEVEL=INFO

# CORS (add your domain)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Frontend domain (for SSL)
FRONTEND_DOMAIN=yourdomain.com
```

### Step 4: Deploy

1. Click **"Deploy"** button
2. Dokploy will:
   - Pull images from GitHub Container Registry
   - Create containers
   - Set up networking
   - Configure SSL/TLS (if domain is set)
3. Wait for deployment to complete (~2-3 minutes)

### Step 5: Verify Deployment

1. **Check Application Status**:
   - All services should show as "Running" (green)
   - Backend, Frontend, and Postgres containers active

2. **Access the Application**:
   - Frontend: `https://yourdomain.com` (or IP:3000)
   - Backend API: `https://yourdomain.com/api` (or IP:8000)
   - API Docs: `https://yourdomain.com/api/docs`

3. **Check Health**:
   ```bash
   curl https://yourdomain.com/api/health
   # Should return: {"status":"healthy"}
   ```

## 🔧 Advanced Configuration

### Using Specific Image Versions

By default, the configuration uses `:latest` tags. For production, pin specific versions:

1. In Dokploy, go to **Application Settings**
2. Click **"Edit Compose File"**
3. Change image tags:
   ```yaml
   backend:
     image: ghcr.io/madpin/whatslang/backend:v1.0.0
   
   frontend:
     image: ghcr.io/madpin/whatslang/frontend:v1.0.0
   ```
4. Save and redeploy

### Custom Domain Configuration

1. **Add Domain in Dokploy**:
   - Go to Application → Domains
   - Click "Add Domain"
   - Enter your domain: `yourdomain.com`
   - Enable SSL/TLS
   - Save

2. **Configure DNS**:
   - Add A record pointing to your Dokploy server IP
   - Wait for DNS propagation (5-30 minutes)

3. **Update Environment Variables**:
   ```bash
   FRONTEND_DOMAIN=yourdomain.com
   CORS_ORIGINS=https://yourdomain.com
   ```

### Backend URL Configuration

The frontend uses nginx to proxy API requests to the backend. By default, it uses the internal Docker network for communication.

**Single Compose Deployment (Default)**:
- No configuration needed
- Frontend and backend communicate internally via `backend:8000`
- This is the recommended approach

**Separate Service Deployments**:
If you deploy frontend and backend as separate Dokploy applications:

1. Deploy backend first and note its URL (e.g., `https://api.yourdomain.com`)
2. In the frontend application, set environment variable:
   ```bash
   BACKEND_URL=https://api.yourdomain.com
   ```
3. Deploy frontend

**Troubleshooting Backend Connection**:
- If you see "backend could not be resolved" errors in frontend logs:
  - Verify `BACKEND_URL` is set correctly
  - For compose deployments: Use `backend:8000` (default)
  - For separate deployments: Use full URL with protocol
  - Check backend service is running and healthy

### Database Backups

Dokploy provides automatic backups. Configure them:

1. Go to Application → Backups
2. Enable automatic backups
3. Set schedule: Daily at 2 AM
4. Set retention: 7 days
5. Save

### Resource Limits

Current limits in `docker-compose.dokploy.yml`:

| Service | CPU | Memory |
|---------|-----|--------|
| Backend | 1 CPU | 1 GB |
| Frontend | 0.5 CPU | 256 MB |
| Postgres | 1 CPU | 1 GB |

To adjust:
1. Edit compose file in Dokploy
2. Modify `deploy.resources` sections
3. Redeploy

### Using Private Images

If your images are private:

1. **Create GitHub Token**:
   - Go to https://github.com/settings/tokens/new
   - Name: `Dokploy GHCR Access`
   - Scopes: `read:packages`
   - Generate and copy token

2. **Add Registry Credentials in Dokploy**:
   - Go to Settings → Registries
   - Click "Add Registry"
   - Registry: `ghcr.io`
   - Username: `madpin`
   - Password: `<your_github_token>`
   - Save

3. **Redeploy Application**

## 📊 Monitoring

### Application Logs

View logs in Dokploy:
1. Go to Application → Logs
2. Select service (backend, frontend, postgres)
3. View real-time logs
4. Filter by log level

### Metrics

Dokploy provides built-in metrics:
- CPU usage
- Memory usage
- Network traffic
- Container status

Access: Application → Metrics

### Health Checks

All services have health checks configured:

- **Backend**: HTTP check on `/health`
- **Frontend**: HTTP check on root
- **Postgres**: PostgreSQL connection check

View status: Application → Services

## 🔄 Updates and Rollbacks

### Updating to New Version

**Option 1: Automatic (using :latest)**
1. GitHub Actions builds new image
2. In Dokploy, click "Redeploy"
3. Dokploy pulls latest image
4. Rolling update applied

**Option 2: Manual (specific version)**
1. Check available versions: https://github.com/madpin/whatslang/pkgs/container/whatslang%2Fbackend
2. Edit compose file with new version
3. Click "Deploy"

### Rolling Back

1. Go to Application → Deployments
2. Find previous successful deployment
3. Click "Rollback"
4. Confirm

## 🔐 Security Best Practices

### 1. Environment Variables

- ✅ Use Dokploy's secret management
- ✅ Never commit secrets to git
- ✅ Rotate API keys regularly
- ✅ Use strong database passwords

### 2. Network Security

- ✅ Enable SSL/TLS for all domains
- ✅ Use Dokploy's built-in firewall
- ✅ Restrict database access to internal network
- ✅ Enable CORS only for your domains

### 3. Image Security

- ✅ Use specific version tags in production
- ✅ Review security scan results in GitHub
- ✅ Update images regularly
- ✅ Monitor for vulnerabilities

## 🐛 Troubleshooting

### Backend Not Starting

**Check logs**:
```bash
# In Dokploy UI: Application → Logs → backend
```

**Common issues**:
1. Missing environment variables
   - Solution: Add required vars in Dokploy UI

2. Database connection failed
   - Check `DB_PASSWORD` is set
   - Verify postgres container is running

3. WhatsApp API unreachable
   - Verify `WHATSAPP_API_URL` is correct
   - Check API is accessible from Dokploy server

### Frontend Shows "Offline"

1. **Check backend health**:
   ```bash
   curl http://backend:8000/health
   ```

2. **Verify networking**:
   - Ensure backend and frontend are on same network
   - Check Dokploy network configuration

3. **Check browser console**:
   - Open DevTools → Console
   - Look for API connection errors

### Database Issues

**Connection refused**:
1. Check postgres container is running
2. Verify `DB_PASSWORD` matches in all services
3. Check health check status

**Slow queries**:
1. Review postgres resource limits
2. Increase `POSTGRES_SHARED_BUFFERS`
3. Monitor query performance

### SSL/TLS Issues

1. **Certificate not valid**:
   - Wait for Let's Encrypt provisioning (5-10 min)
   - Check domain DNS is correct

2. **Mixed content warnings**:
   - Ensure all API calls use HTTPS
   - Update `CORS_ORIGINS` to use https://

## 📈 Scaling

### Horizontal Scaling

Dokploy supports scaling services:

1. Go to Application → Services
2. Select service (e.g., backend)
3. Click "Scale"
4. Set number of replicas: 2-3
5. Save

**Note**: Database should not be scaled horizontally. Use managed PostgreSQL for high availability.

### Vertical Scaling

Increase resources:

1. Edit compose file
2. Update resource limits:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 2G
   ```
3. Redeploy

## 💾 Backup and Restore

### Manual Backup

```bash
# In Dokploy terminal or SSH to server
docker exec whatslang-postgres-1 pg_dump -U whatslang whatslang > backup.sql
```

### Restore from Backup

```bash
# Copy backup to container
docker cp backup.sql whatslang-postgres-1:/tmp/

# Restore
docker exec whatslang-postgres-1 psql -U whatslang whatslang < /tmp/backup.sql
```

### Automated Backups

Configure in Dokploy:
1. Application → Backups
2. Enable automatic backups
3. Set schedule and retention
4. Configure backup destination (S3, etc.)

## 🔗 Integration with CI/CD

### Automatic Deployment on Push

1. **Enable Webhooks in Dokploy**:
   - Go to Application → Settings
   - Copy webhook URL

2. **Add Webhook to GitHub**:
   - Repository → Settings → Webhooks
   - Add webhook URL
   - Select events: Push to main

3. **Configure Auto-deploy**:
   - In Dokploy: Enable "Auto-deploy on push"
   - Save

Now every push to `main` will:
1. Trigger GitHub Actions
2. Build new images
3. Push to GHCR
4. Trigger Dokploy deployment
5. Rolling update applied

## 📞 Support

### Dokploy Resources
- [Dokploy Documentation](https://docs.dokploy.com)
- [Dokploy Discord](https://discord.gg/dokploy)
- [Dokploy GitHub](https://github.com/dokploy/dokploy)

### WhatSlang Resources
- [GitHub Repository](https://github.com/madpin/whatslang)
- [CI/CD Documentation](CI_CD.md)
- [Deployment Checklist](../DEPLOYMENT_CHECKLIST.md)

## 🎉 Success Checklist

- [ ] Dokploy application created
- [ ] GitHub repository connected
- [ ] Environment variables configured
- [ ] Application deployed successfully
- [ ] All services running (green status)
- [ ] Frontend accessible via domain
- [ ] Backend API responding
- [ ] Health checks passing
- [ ] SSL/TLS certificate active
- [ ] Logs showing no errors
- [ ] First bot created and tested
- [ ] Backups configured
- [ ] Monitoring set up

---

**Congratulations!** Your WhatSlang instance is now running on Dokploy! 🚀

For production use, remember to:
- Pin specific image versions
- Enable automatic backups
- Set up monitoring alerts
- Configure proper CORS origins
- Use strong passwords
- Keep images updated

