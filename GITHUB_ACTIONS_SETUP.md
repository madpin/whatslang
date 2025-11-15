# GitHub Actions CI/CD Setup Guide

This guide will help you set up and use the automated CI/CD pipeline for the WhatSlang project.

## 🚀 Quick Setup (5 minutes)

### Step 1: Enable Workflow Permissions

1. Go to https://github.com/madpin/whatslang/settings/actions
2. Scroll to **Workflow permissions**
3. Select **"Read and write permissions"**
4. Check **"Allow GitHub Actions to create and approve pull requests"**
5. Click **Save**

### Step 2: Push Your Code

The workflow will automatically trigger when you push to `main` or `develop`:

```bash
git add .
git commit -m "Add CI/CD pipeline"
git push origin main
```

### Step 3: Monitor the Build

1. Go to https://github.com/madpin/whatslang/actions
2. Click on the latest "Build and Push Docker Images" workflow
3. Watch the build progress in real-time

### Step 4: Make Images Public (Optional)

By default, images are private. To make them public:

1. Go to https://github.com/madpin?tab=packages
2. Click on `whatslang/backend`
3. Click **"Package settings"** (bottom right)
4. Scroll to **"Danger Zone"**
5. Click **"Change visibility"** → Select **"Public"**
6. Repeat for `whatslang/frontend`

## 📦 Using the Built Images

### Pull Latest Images

```bash
# For public images (no authentication needed)
docker pull ghcr.io/madpin/whatslang/backend:latest
docker pull ghcr.io/madpin/whatslang/frontend:latest

# For private images (authentication required)
echo $GITHUB_TOKEN | docker login ghcr.io -u madpin --password-stdin
docker pull ghcr.io/madpin/whatslang/backend:latest
docker pull ghcr.io/madpin/whatslang/frontend:latest
```

### Deploy Using Pre-built Images

```bash
# Use the registry configuration
docker-compose -f docker-compose.registry.yml up -d
```

## 🏷️ Version Tagging

Create version tags to trigger versioned builds:

```bash
# Create and push a version tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

This will create images with multiple tags:
- `ghcr.io/madpin/whatslang/backend:latest`
- `ghcr.io/madpin/whatslang/backend:v1.0.0`
- `ghcr.io/madpin/whatslang/backend:1.0.0`
- `ghcr.io/madpin/whatslang/backend:1.0`
- `ghcr.io/madpin/whatslang/backend:1`

## 🔒 Authentication

### For Local Development

Create a Personal Access Token (PAT):

1. Go to https://github.com/settings/tokens/new
2. Select **"New personal access token (classic)"**
3. Name: `Docker Registry Access`
4. Expiration: Choose duration
5. Scopes: Check `read:packages` (and `write:packages` if needed)
6. Click **"Generate token"**
7. Copy the token

Login to GHCR:

```bash
echo YOUR_TOKEN | docker login ghcr.io -u madpin --password-stdin
```

### For CI/CD Systems

Use the same PAT or create a dedicated one:

```bash
# In your CI/CD environment
export GITHUB_TOKEN=your_token_here
echo $GITHUB_TOKEN | docker login ghcr.io -u madpin --password-stdin
```

## 🔍 Viewing Build Status

### Build Badge

The README now includes a build status badge:

![Docker Build](https://github.com/madpin/whatslang/actions/workflows/docker-build.yml/badge.svg)

### Action Logs

View detailed logs at:
https://github.com/madpin/whatslang/actions/workflows/docker-build.yml

### Security Scans

View vulnerability reports at:
https://github.com/madpin/whatslang/security/code-scanning

## 📋 Available Images and Tags

### Backend Images

```bash
# Latest from main branch
ghcr.io/madpin/whatslang/backend:latest

# Specific branch
ghcr.io/madpin/whatslang/backend:main
ghcr.io/madpin/whatslang/backend:develop

# Specific version
ghcr.io/madpin/whatslang/backend:v1.0.0
ghcr.io/madpin/whatslang/backend:1.0.0

# Commit SHA
ghcr.io/madpin/whatslang/backend:main-abc1234
```

### Frontend Images

```bash
# Latest from main branch
ghcr.io/madpin/whatslang/frontend:latest

# Specific branch
ghcr.io/madpin/whatslang/frontend:main
ghcr.io/madpin/whatslang/frontend:develop

# Specific version
ghcr.io/madpin/whatslang/frontend:v1.0.0
ghcr.io/madpin/whatslang/frontend:1.0.0

# Commit SHA
ghcr.io/madpin/whatslang/frontend:main-abc1234
```

## 🔄 Workflow Triggers

The CI/CD pipeline runs automatically on:

### Push Events
- Push to `main` branch → Builds and pushes `latest` tag
- Push to `develop` branch → Builds and pushes `develop` tag
- Push version tag (e.g., `v1.0.0`) → Builds and pushes version tags

### Pull Requests
- PR to `main` or `develop` → Builds images but doesn't push (validation only)

## 🛠️ Troubleshooting

### Build Failing

**Check the logs:**
```bash
# View in browser
open https://github.com/madpin/whatslang/actions
```

**Common issues:**
- Missing dependencies in requirements.txt or package.json
- Dockerfile syntax errors
- Network timeouts

### Can't Pull Images

**Verify image exists:**
```bash
# Check if image was pushed
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://ghcr.io/v2/madpin/whatslang/backend/tags/list
```

**Check authentication:**
```bash
# Re-login
echo $GITHUB_TOKEN | docker login ghcr.io -u madpin --password-stdin
```

### Permission Denied

**Fix workflow permissions:**
1. Go to https://github.com/madpin/whatslang/settings/actions
2. Under "Workflow permissions", select "Read and write permissions"
3. Save changes
4. Re-run the workflow

## 📊 Monitoring

### Check Image Sizes

```bash
# Pull and inspect
docker pull ghcr.io/madpin/whatslang/backend:latest
docker images ghcr.io/madpin/whatslang/backend:latest
```

### View All Tags

```bash
# Using GitHub CLI
gh api /user/packages/container/whatslang%2Fbackend/versions

# Or visit in browser
open https://github.com/madpin/whatslang/pkgs/container/whatslang%2Fbackend
```

## 🎯 Best Practices

### 1. Use Semantic Versioning

```bash
# Major release (breaking changes)
git tag -a v2.0.0 -m "Major release with breaking changes"

# Minor release (new features)
git tag -a v1.1.0 -m "Added new features"

# Patch release (bug fixes)
git tag -a v1.0.1 -m "Bug fixes"

git push origin --tags
```

### 2. Pin Versions in Production

```yaml
# docker-compose.prod.yml
services:
  backend:
    image: ghcr.io/madpin/whatslang/backend:v1.0.0  # Pin to specific version
  frontend:
    image: ghcr.io/madpin/whatslang/frontend:v1.0.0  # Pin to specific version
```

### 3. Test Before Tagging

```bash
# Test on develop branch first
git checkout develop
git push origin develop
# Wait for build to complete and test

# Then merge to main and tag
git checkout main
git merge develop
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin main --tags
```

## 📚 Additional Resources

- [Full CI/CD Documentation](docs/CI_CD.md)
- [GitHub Actions Workflows README](.github/workflows/README.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [GitHub Container Registry Docs](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

## 🆘 Support

If you encounter issues:

1. Check the [troubleshooting section](#-troubleshooting) above
2. View workflow logs: https://github.com/madpin/whatslang/actions
3. Open an issue: https://github.com/madpin/whatslang/issues

---

**Ready to deploy?** Just push your code and let GitHub Actions handle the rest! 🚀

