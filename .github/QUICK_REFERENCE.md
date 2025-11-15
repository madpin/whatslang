# CI/CD Quick Reference Card

## 🚀 Quick Commands

### Pull Latest Images
```bash
docker pull ghcr.io/madpin/whatslang/backend:latest
docker pull ghcr.io/madpin/whatslang/frontend:latest
```

### Deploy with Pre-built Images
```bash
docker-compose -f docker-compose.registry.yml up -d
```

### Login to Registry
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u madpin --password-stdin
```

### Create Release
```bash
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0
```

## 📦 Image Locations

| Service | Image URL |
|---------|-----------|
| Backend | `ghcr.io/madpin/whatslang/backend` |
| Frontend | `ghcr.io/madpin/whatslang/frontend` |

## 🏷️ Common Tags

| Tag | Description | Example |
|-----|-------------|---------|
| `latest` | Latest from main | `backend:latest` |
| `main` | Main branch | `backend:main` |
| `develop` | Develop branch | `backend:develop` |
| `v1.0.0` | Version tag | `backend:v1.0.0` |
| `1.0.0` | Semver | `backend:1.0.0` |
| `main-abc1234` | Branch + SHA | `backend:main-abc1234` |

## 🔗 Important Links

| Resource | URL |
|----------|-----|
| Actions | https://github.com/madpin/whatslang/actions |
| Packages | https://github.com/madpin?tab=packages |
| Security | https://github.com/madpin/whatslang/security/code-scanning |
| Settings | https://github.com/madpin/whatslang/settings/actions |

## 📋 Workflow Triggers

| Event | Action | Push Images? |
|-------|--------|--------------|
| Push to main | Build & push | ✅ Yes |
| Push to develop | Build & push | ✅ Yes |
| Create tag v* | Build & push | ✅ Yes |
| Pull request | Build only | ❌ No |

## 🛠️ Troubleshooting

### Build Failed?
```bash
# Check logs
open https://github.com/madpin/whatslang/actions
```

### Can't Pull Image?
```bash
# Re-authenticate
echo $GITHUB_TOKEN | docker login ghcr.io -u madpin --password-stdin
```

### Permission Error?
1. Go to Settings → Actions
2. Enable "Read and write permissions"

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `GITHUB_ACTIONS_SETUP.md` | Step-by-step setup |
| `docs/CI_CD.md` | Complete documentation |
| `.github/workflows/README.md` | Workflow reference |
| `.github/FIRST_TIME_SETUP.md` | Setup checklist |
| `CI_CD_SUMMARY.md` | Implementation summary |

## ⚡ One-Liners

```bash
# Pull and deploy latest
docker-compose -f docker-compose.registry.yml pull && \
docker-compose -f docker-compose.registry.yml up -d

# View logs
docker-compose -f docker-compose.registry.yml logs -f

# Stop services
docker-compose -f docker-compose.registry.yml down

# Check image sizes
docker images | grep whatslang

# List available tags (requires gh CLI)
gh api /user/packages/container/whatslang%2Fbackend/versions

# Clean old images
docker image prune -a
```

## 🎯 Best Practices

1. **Pin versions in production**
   ```yaml
   image: ghcr.io/madpin/whatslang/backend:v1.0.0
   ```

2. **Use latest for development**
   ```yaml
   image: ghcr.io/madpin/whatslang/backend:latest
   ```

3. **Tag releases semantically**
   ```bash
   git tag -a v1.0.0 -m "Major release"
   git tag -a v1.1.0 -m "New features"
   git tag -a v1.0.1 -m "Bug fixes"
   ```

4. **Test on develop first**
   ```bash
   git checkout develop
   git push origin develop
   # Wait for build and test
   git checkout main
   git merge develop
   git push origin main
   ```

## 🔔 Status Checks

```bash
# Check backend health
docker run --rm ghcr.io/madpin/whatslang/backend:latest python -c "print('OK')"

# Check frontend
docker run --rm ghcr.io/madpin/whatslang/frontend:latest ls -la /usr/share/nginx/html

# Check image architecture
docker manifest inspect ghcr.io/madpin/whatslang/backend:latest | grep architecture
```

## 📊 Build Times

| Build Type | Time | Cache |
|------------|------|-------|
| First build | 8-10 min | ❌ No |
| Incremental | 2-5 min | ✅ Yes |
| No changes | 1-2 min | ✅ Yes |

## 💰 Cost

| Resource | Free Tier | Cost |
|----------|-----------|------|
| GitHub Actions | 2,000 min/month | $0.008/min |
| GHCR Storage | 500 MB | $0.25/GB/month |
| Public repos | Unlimited | Free |

---

**Keep this card handy for quick reference!** 📌

