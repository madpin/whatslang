# 🚀 Dokploy Quick Start Guide

Deploy WhatSlang to Dokploy in 5 minutes using pre-built Docker images!

## ⚡ Prerequisites

- [ ] Dokploy instance running
- [ ] WhatsApp API endpoint (go-whatsapp-web-multidevice)
- [ ] OpenAI API key or compatible LLM
- [ ] Domain name (optional but recommended)

## 📋 Step-by-Step Deployment

### 1. Create Application (30 seconds)

1. Log in to Dokploy dashboard
2. Click **"Create Application"**
3. Select **"Compose"**
4. Fill in:
   - **Name**: `whatslang`
   - **Description**: `WhatsApp Bot Platform`
5. Click **"Create"**

### 2. Connect Repository (1 minute)

1. Click **"Connect Repository"**
2. Select **"GitHub"**
3. Authorize Dokploy (if first time)
4. Select: `madpin/whatslang`
5. Branch: `main`
6. Compose file: `docker-compose.dokploy.yml`
7. Click **"Save"**

### 3. Set Environment Variables (2 minutes)

Click **"Environment Variables"** and add:

#### Required (Minimum to start)

```bash
# Database
DB_PASSWORD=your_secure_random_password_here

# WhatsApp API
WHATSAPP_API_URL=https://your-whatsapp-api.example.com
WHATSAPP_API_TOKEN=your_api_token

# LLM
OPENAI_API_KEY=sk-your-openai-key-here
```

#### Recommended (For production)

```bash
# Application
DEBUG=false
LOG_LEVEL=INFO

# CORS (add your domain)
CORS_ORIGINS=https://yourdomain.com

# Domain
FRONTEND_DOMAIN=yourdomain.com
```

**Tip**: Generate secure password:
```bash
openssl rand -base64 32
```

### 4. Deploy (1 minute)

1. Click **"Deploy"** button
2. Wait for deployment (~2-3 minutes)
3. Watch logs for any errors

### 5. Verify (30 seconds)

**Check Status**:
- All services should show green (Running)
- Backend, Frontend, Postgres containers active

**Test Health**:
```bash
curl https://yourdomain.com/api/health
# Expected: {"status":"healthy"}
```

**Access Application**:
- Frontend: `https://yourdomain.com`
- API Docs: `https://yourdomain.com/api/docs`

## 🎯 What's Next?

### Configure Domain (Optional)

1. Go to Application → **Domains**
2. Click **"Add Domain"**
3. Enter: `yourdomain.com`
4. Enable **SSL/TLS**
5. Save

**DNS Configuration**:
```
Type: A
Name: @
Value: <your-dokploy-server-ip>
TTL: 300
```

### Create Your First Bot

1. Open frontend: `https://yourdomain.com`
2. Go to **"Bots"** page
3. Click **"Create Bot"**
4. Select **"Translation Bot"**
5. Configure:
   ```json
   {
     "prefix": "[ai]",
     "source_languages": ["en", "pt"],
     "translate_images": true
   }
   ```
6. Click **"Create"**

### Register a Chat

1. Go to **"Chats"** page
2. Click **"Add Chat"**
3. Enter WhatsApp chat JID
4. Assign your bot
5. Test in WhatsApp!

## 🔧 Common Issues

### "Backend not starting"

**Check logs**:
1. Go to Application → Logs
2. Select "backend" service
3. Look for error messages

**Common fixes**:
- Verify all required env vars are set
- Check `WHATSAPP_API_URL` is accessible
- Ensure `DB_PASSWORD` is set

### "Frontend shows offline"

**Fix**:
1. Check backend health: `curl http://backend:8000/health`
2. Verify backend container is running
3. Check browser console for errors

### "Database connection failed"

**Fix**:
1. Verify `DB_PASSWORD` is set
2. Check postgres container is running
3. Ensure all services on same network

## 📊 Monitoring

### View Logs

```
Application → Logs → Select Service
```

### Check Metrics

```
Application → Metrics
```

Shows:
- CPU usage
- Memory usage
- Network traffic
- Container status

### Health Checks

All services have automatic health checks:
- ✅ Backend: HTTP /health endpoint
- ✅ Frontend: HTTP root check
- ✅ Postgres: Connection check

## 🔄 Updates

### Update to Latest Version

1. GitHub Actions builds new image automatically
2. In Dokploy, click **"Redeploy"**
3. Dokploy pulls latest image
4. Rolling update applied
5. Zero downtime!

### Update to Specific Version

1. Go to Application → **Edit**
2. Modify compose file:
   ```yaml
   backend:
     image: ghcr.io/madpin/whatslang/backend:v1.0.0
   frontend:
     image: ghcr.io/madpin/whatslang/frontend:v1.0.0
   ```
3. Click **"Save"**
4. Click **"Deploy"**

## 💾 Backups

### Enable Automatic Backups

1. Go to Application → **Backups**
2. Click **"Enable Backups"**
3. Configure:
   - Schedule: `Daily at 2 AM`
   - Retention: `7 days`
   - Destination: `Local` or `S3`
4. Click **"Save"**

### Manual Backup

```bash
# SSH to Dokploy server
ssh user@your-server

# Create backup
docker exec whatslang-postgres-1 pg_dump -U whatslang whatslang > backup.sql

# Download backup
scp user@your-server:backup.sql ./
```

## 🔐 Security Checklist

- [ ] Strong `DB_PASSWORD` set
- [ ] SSL/TLS enabled for domain
- [ ] `DEBUG=false` in production
- [ ] CORS configured for your domain only
- [ ] API keys stored securely in Dokploy
- [ ] Automatic backups enabled
- [ ] Firewall configured
- [ ] Regular updates scheduled

## 📚 Additional Resources

- **[Full Dokploy Guide](docs/DOKPLOY_DEPLOYMENT.md)** - Detailed documentation
- **[CI/CD Pipeline](docs/CI_CD.md)** - How images are built
- **[Environment Variables](env.dokploy.template)** - Complete list
- **[Deployment Checklist](DEPLOYMENT_CHECKLIST.md)** - Pre-deployment steps

## 🆘 Need Help?

### Dokploy Support
- [Dokploy Docs](https://docs.dokploy.com)
- [Dokploy Discord](https://discord.gg/dokploy)

### WhatSlang Support
- [GitHub Issues](https://github.com/madpin/whatslang/issues)
- [Documentation](docs/)

## ✅ Success!

If you can:
- ✅ Access frontend at your domain
- ✅ See API docs at `/api/docs`
- ✅ Health check returns healthy
- ✅ Create and assign bots
- ✅ Receive messages from WhatsApp

**Congratulations! Your WhatSlang instance is live!** 🎉

---

**Total deployment time**: ~5 minutes
**Difficulty**: Easy ⭐
**Maintenance**: Low (automatic updates available)

