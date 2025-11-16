# Deployment Guide

This guide covers various deployment scenarios for the WhatsApp Bot Service.

## Table of Contents

- [Dokploy (Nixpacks)](#dokploy-nixpacks)
- [Docker](#docker)
- [Kubernetes](#kubernetes)
- [Traditional VPS](#traditional-vps)

---

## Dokploy (Nixpacks)

Dokploy uses Nixpacks to automatically detect and build your application.

### Prerequisites

- Dokploy instance running
- Git repository with your code
- WhatsApp API endpoint accessible from your Dokploy instance

### Step-by-Step Deployment

#### 1. Prepare Your Repository

Ensure these files are in your repository:
- `nixpacks.toml` - Nixpacks configuration
- `requirements.txt` - Python dependencies
- `api/`, `bots/`, `core/`, `frontend/` - Application code

#### 2. Create Application in Dokploy

1. Log into Dokploy dashboard
2. Navigate to your project
3. Click **"Add Service"** → **"Application"**
4. Choose **"Git Provider"**
5. Select your repository and branch

#### 3. Configure Build Settings

Dokploy will automatically detect Nixpacks. Verify:
- **Build Method**: Nixpacks (auto-detected)
- **Port**: 8000

#### 4. Set Environment Variables

Add these in the "Environment" tab:

```bash
# Required
WHATSAPP_BASE_URL=https://your-whatsapp-api.com
WHATSAPP_API_USER=your-username
WHATSAPP_API_PASSWORD=your-password
CHAT_JID=your-chat-jid@g.us

OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# Production settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

#### 5. Configure Persistent Storage

Add a volume mount:
- **Mount Path**: `/data`
- **Size**: 1GB (adjust based on usage)
- **Purpose**: Persists SQLite database

#### 6. Configure Domain (Optional)

In the "Domains" tab:
- Add your custom domain
- Enable SSL (Let's Encrypt)

#### 7. Configure Health Checks

In "Advanced" settings:

**Liveness Probe:**
- Path: `/health`
- Port: 8000
- Initial Delay: 30s
- Period: 10s

**Readiness Probe:**
- Path: `/ready`
- Port: 8000
- Initial Delay: 10s
- Period: 5s

#### 8. Deploy

Click **"Deploy"** button.

Monitor deployment:
- Watch build logs in real-time
- First deployment takes 2-3 minutes
- Subsequent deployments are faster (cached layers)

#### 9. Verify Deployment

```bash
# Check health
curl https://your-domain.com/health

# Check readiness
curl https://your-domain.com/ready

# Access dashboard
open https://your-domain.com/static/index.html
```

### Dokploy Best Practices

- **Environment Variables**: Use Dokploy's secret management
- **Logs**: Access via Dokploy dashboard logs tab
- **Scaling**: Adjust resources in "Resources" tab
- **Backups**: Enable automatic volume backups
- **Updates**: Push to Git → Dokploy auto-deploys

---

## Docker

### Using Docker Compose (Recommended)

#### 1. Create `docker-compose.yml`

Already included in the repository!

#### 2. Create `.env` file

```bash
cp env.example .env
# Edit with your credentials
```

#### 3. Start Services

```bash
docker-compose up -d
```

#### 4. Manage

```bash
# View logs
docker-compose logs -f whatslang

# Stop
docker-compose down

# Restart
docker-compose restart

# Update
git pull
docker-compose up -d --build
```

### Using Docker CLI

#### 1. Build Image

```bash
docker build -t whatslang:latest .
```

#### 2. Run Container

```bash
docker run -d \
  --name whatslang \
  --restart unless-stopped \
  -p 8000:8000 \
  -e WHATSAPP_BASE_URL=https://your-api.com \
  -e WHATSAPP_API_USER=your-user \
  -e WHATSAPP_API_PASSWORD=your-pass \
  -e CHAT_JID=your-jid@g.us \
  -e OPENAI_API_KEY=sk-your-key \
  -e ENVIRONMENT=production \
  -v whatslang-data:/data \
  whatslang:latest
```

#### 3. Manage

```bash
# View logs
docker logs -f whatslang

# Stop
docker stop whatslang

# Start
docker start whatslang

# Restart
docker restart whatslang

# Update
docker stop whatslang
docker rm whatslang
docker pull whatslang:latest  # If using registry
docker run ...  # Same command as step 2
```

---

## Kubernetes

### Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Persistent volume provisioner

### Deployment

#### 1. Create Namespace

```bash
kubectl create namespace whatslang
```

#### 2. Create Secret

```bash
kubectl create secret generic whatslang-secrets \
  --namespace=whatslang \
  --from-literal=WHATSAPP_BASE_URL=https://your-api.com \
  --from-literal=WHATSAPP_API_USER=your-user \
  --from-literal=WHATSAPP_API_PASSWORD=your-pass \
  --from-literal=CHAT_JID=your-jid@g.us \
  --from-literal=OPENAI_API_KEY=sk-your-key
```

#### 3. Create Deployment

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: whatslang
  namespace: whatslang
spec:
  replicas: 1
  selector:
    matchLabels:
      app: whatslang
  template:
    metadata:
      labels:
        app: whatslang
    spec:
      containers:
      - name: whatslang
        image: your-registry/whatslang:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        envFrom:
        - secretRef:
            name: whatslang-secrets
        volumeMounts:
        - name: data
          mountPath: /data
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: whatslang-data
```

#### 4. Create PVC

Create `k8s/pvc.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: whatslang-data
  namespace: whatslang
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

#### 5. Create Service

Create `k8s/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: whatslang
  namespace: whatslang
spec:
  selector:
    app: whatslang
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

#### 6. Create Ingress (Optional)

Create `k8s/ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: whatslang
  namespace: whatslang
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - whatslang.yourdomain.com
    secretName: whatslang-tls
  rules:
  - host: whatslang.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: whatslang
            port:
              number: 80
```

#### 7. Apply Configuration

```bash
kubectl apply -f k8s/
```

#### 8. Verify

```bash
# Check deployment
kubectl get deployments -n whatslang

# Check pods
kubectl get pods -n whatslang

# Check logs
kubectl logs -n whatslang -l app=whatslang -f

# Port forward for testing
kubectl port-forward -n whatslang svc/whatslang 8000:80
```

---

## Traditional VPS

Deploy on Ubuntu/Debian server.

### Prerequisites

- Ubuntu 20.04+ or Debian 11+
- Root or sudo access
- Domain name pointed to server IP (optional)

### Installation

#### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

#### 2. Install Python 3.11

```bash
sudo apt install -y python3.11 python3.11-venv python3-pip
```

#### 3. Clone Repository

```bash
cd /opt
sudo git clone https://github.com/yourusername/whatslang.git
cd whatslang
```

#### 4. Create Virtual Environment

```bash
sudo python3.11 -m venv .venv
sudo .venv/bin/pip install -r requirements.txt
```

#### 5. Configure Environment

```bash
sudo cp env.example .env
sudo nano .env
# Fill in your credentials
```

#### 6. Create Systemd Service

Create `/etc/systemd/system/whatslang.service`:

```ini
[Unit]
Description=WhatsApp Bot Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/whatslang
Environment="PATH=/opt/whatslang/.venv/bin"
EnvironmentFile=/opt/whatslang/.env
ExecStart=/opt/whatslang/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 7. Set Permissions

```bash
sudo chown -R www-data:www-data /opt/whatslang
sudo chmod 600 /opt/whatslang/.env
```

#### 8. Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable whatslang
sudo systemctl start whatslang
```

#### 9. Check Status

```bash
sudo systemctl status whatslang
sudo journalctl -u whatslang -f
```

### Nginx Reverse Proxy (Optional)

#### 1. Install Nginx

```bash
sudo apt install -y nginx
```

#### 2. Configure

Create `/etc/nginx/sites-available/whatslang`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

#### 3. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/whatslang /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 4. SSL with Certbot (Optional)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Maintenance

```bash
# View logs
sudo journalctl -u whatslang -f

# Restart service
sudo systemctl restart whatslang

# Update application
cd /opt/whatslang
sudo git pull
sudo .venv/bin/pip install -r requirements.txt
sudo systemctl restart whatslang

# Check service status
sudo systemctl status whatslang
```

---

## Security Considerations

### All Deployments

1. **Environment Variables**: Never commit `.env` file
2. **API Keys**: Rotate regularly
3. **HTTPS**: Always use SSL in production
4. **Firewall**: Only open necessary ports
5. **Updates**: Keep dependencies updated

### Docker Specific

- Run as non-root user (already configured)
- Use read-only filesystem where possible
- Scan images for vulnerabilities

### Kubernetes Specific

- Use Network Policies
- Enable RBAC
- Use Pod Security Standards
- Implement resource quotas

---

## Monitoring

### Health Endpoints

```bash
# Liveness (is it running?)
curl http://your-service/health

# Readiness (is it ready?)
curl http://your-service/ready
```

### Logs

- **Docker**: `docker logs -f whatslang`
- **Kubernetes**: `kubectl logs -f -l app=whatslang`
- **Systemd**: `journalctl -u whatslang -f`

### Metrics

The `/ready` endpoint provides operational metrics:

```json
{
  "status": "ready",
  "services": {
    "whatsapp": "connected",
    "llm": "connected",
    "database": "connected"
  },
  "bots": {
    "available": 2,
    "running": 1
  }
}
```

---

## Troubleshooting

### Common Issues

**Service won't start**
- Check environment variables are set
- Verify all required vars in `.env` or secrets
- Check logs for specific error messages

**Database errors**
- Ensure `/data` directory is writable
- Check persistent volume is mounted
- Verify file permissions

**WhatsApp API connection fails**
- Test API endpoint accessibility
- Verify credentials
- Check firewall rules

**LLM errors**
- Validate API key
- Test endpoint connectivity
- Verify model name

---

## Support

- Documentation: See [README.md](../README.md)
- Issues: GitHub Issues
- Community: GitHub Discussions

