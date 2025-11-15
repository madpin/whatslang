# CI/CD Pipeline Documentation

## Overview

This project uses GitHub Actions to automatically build and push Docker images to GitHub Container Registry (GHCR) whenever code is pushed to the repository.

## Workflow Triggers

The CI/CD pipeline is triggered on:

- **Push to main/develop branches**: Builds and pushes images with branch tags
- **Pull requests**: Builds images but doesn't push (validation only)
- **Version tags** (e.g., `v1.0.0`): Builds and pushes with semantic version tags

## Docker Images

Two Docker images are built:

1. **Backend**: `ghcr.io/<owner>/<repo>/backend`
2. **Frontend**: `ghcr.io/<owner>/<repo>/frontend`

## Image Tags

Images are automatically tagged with:

- `latest` - Latest build from main branch
- `<branch-name>` - Branch name (e.g., `main`, `develop`)
- `pr-<number>` - Pull request number
- `<version>` - Semantic version from git tags (e.g., `1.0.0`, `1.0`, `1`)
- `<branch>-<sha>` - Branch name with git commit SHA

## Setup Instructions

### 1. Enable GitHub Container Registry

GitHub Container Registry is enabled by default for all repositories. No additional setup needed.

### 2. Configure Repository Permissions

The workflow uses `GITHUB_TOKEN` which is automatically provided. Ensure your repository has:

- **Settings → Actions → General → Workflow permissions**: Set to "Read and write permissions"

### 3. Make Images Public (Optional)

By default, images are private. To make them public:

1. Go to your GitHub profile
2. Click on "Packages"
3. Select the package (backend or frontend)
4. Go to "Package settings"
5. Scroll to "Danger Zone"
6. Click "Change visibility" and select "Public"

## Using the Images

### Pull Images

```bash
# Pull latest backend image
docker pull ghcr.io/<owner>/<repo>/backend:latest

# Pull latest frontend image
docker pull ghcr.io/<owner>/<repo>/frontend:latest

# Pull specific version
docker pull ghcr.io/<owner>/<repo>/backend:v1.0.0
```

### Authentication

For private images, authenticate with GitHub:

```bash
# Using GitHub Personal Access Token
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin

# Or using GitHub CLI
gh auth token | docker login ghcr.io -u <username> --password-stdin
```

### Update docker-compose.prod.yml

Replace the image references in `docker-compose.prod.yml`:

```yaml
services:
  backend:
    image: ghcr.io/<owner>/<repo>/backend:latest
    # ... rest of config

  frontend:
    image: ghcr.io/<owner>/<repo>/frontend:latest
    # ... rest of config
```

## Security Scanning

The pipeline includes automatic security scanning using Trivy:

- Scans both backend and frontend images
- Uploads results to GitHub Security tab
- Runs after successful builds on push events
- View results in: **Security → Code scanning alerts**

## Multi-Architecture Support

Images are built for multiple architectures:

- `linux/amd64` - Standard x86_64 architecture
- `linux/arm64` - ARM architecture (Apple Silicon, AWS Graviton, etc.)

## Build Caching

The workflow uses GitHub Actions cache to speed up builds:

- Docker layer caching enabled
- Subsequent builds are significantly faster
- Cache is shared across workflow runs

## Workflow Jobs

### 1. build-backend

- Builds the backend Docker image
- Pushes to GHCR (except on PRs)
- Uses BuildKit for optimal caching

### 2. build-frontend

- Builds the frontend Docker image
- Pushes to GHCR (except on PRs)
- Uses BuildKit for optimal caching

### 3. security-scan

- Runs after both builds complete
- Scans images for vulnerabilities
- Only runs on push events (not PRs)
- Uploads results to GitHub Security

## Monitoring Builds

### View Workflow Runs

1. Go to your repository on GitHub
2. Click "Actions" tab
3. Select "Build and Push Docker Images"
4. View individual runs and logs

### Check Build Status

Add a badge to your README:

```markdown
![Docker Build](https://github.com/<owner>/<repo>/actions/workflows/docker-build.yml/badge.svg)
```

## Troubleshooting

### Build Fails

1. Check the Actions logs for specific errors
2. Verify Dockerfile syntax
3. Ensure all dependencies are available

### Permission Denied

1. Check repository workflow permissions
2. Verify GITHUB_TOKEN has package write access
3. Check if branch protection rules block the workflow

### Image Not Found

1. Verify the image was pushed (check Actions logs)
2. Check if you need authentication for private images
3. Ensure the image tag exists

## Best Practices

### Version Tagging

Create version tags for releases:

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

This will trigger a build with semantic version tags.

### Branch Strategy

- `main` - Production-ready code, tagged as `latest`
- `develop` - Development code, tagged as `develop`
- Feature branches - Build on PR for validation

### Image Cleanup

Regularly clean up old images to save storage:

1. Go to package settings
2. Configure automatic deletion of old versions
3. Keep recent versions and tagged releases

## Integration with Deployment

### Manual Deployment

```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Restart services
docker-compose -f docker-compose.prod.yml up -d
```

### Automated Deployment

Consider setting up:

- **Watchtower**: Automatically updates running containers
- **ArgoCD**: GitOps-based deployment
- **GitHub Actions Deploy**: Add deployment job to workflow

## Environment Variables

The workflow uses these environment variables:

- `REGISTRY`: Container registry URL (ghcr.io)
- `IMAGE_NAME_BACKEND`: Backend image name
- `IMAGE_NAME_FRONTEND`: Frontend image name

## Secrets Required

- `GITHUB_TOKEN`: Automatically provided by GitHub Actions

No additional secrets needed for basic functionality.

## Cost Considerations

- GitHub Actions: 2,000 free minutes/month for private repos
- GHCR Storage: 500MB free, then $0.25/GB/month
- Public repositories: Unlimited minutes and storage

## Future Enhancements

Consider adding:

- [ ] Automated testing before build
- [ ] Deployment to staging/production
- [ ] Slack/Discord notifications
- [ ] Performance benchmarking
- [ ] Image size optimization checks
- [ ] Automatic rollback on failures

