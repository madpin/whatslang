# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automating CI/CD processes.

## Available Workflows

### docker-build.yml

Automatically builds and pushes Docker images to GitHub Container Registry (GHCR).

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Git tags starting with `v` (e.g., `v1.0.0`)

**What it does:**
1. Builds backend and frontend Docker images
2. Pushes images to GHCR (except on PRs)
3. Runs security scans with Trivy
4. Uploads scan results to GitHub Security

**Image locations:**
- Backend: `ghcr.io/<owner>/<repo>/backend`
- Frontend: `ghcr.io/<owner>/<repo>/frontend`

## Quick Start

### 1. First Time Setup

No setup required! The workflow uses `GITHUB_TOKEN` which is automatically provided.

### 2. Trigger a Build

**Option A: Push to main/develop**
```bash
git push origin main
```

**Option B: Create a release tag**
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

**Option C: Open a pull request**
```bash
git checkout -b feature/my-feature
git push origin feature/my-feature
# Open PR on GitHub
```

### 3. Monitor the Build

1. Go to the "Actions" tab in your GitHub repository
2. Click on "Build and Push Docker Images"
3. Select the latest run to view logs

### 4. Use the Built Images

```bash
# Authenticate
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin

# Pull images
docker pull ghcr.io/<owner>/<repo>/backend:latest
docker pull ghcr.io/<owner>/<repo>/frontend:latest

# Or use docker-compose
docker-compose -f docker-compose.registry.yml up -d
```

## Image Tags

The workflow automatically creates multiple tags for each build:

| Tag Pattern | Example | Description |
|------------|---------|-------------|
| `latest` | `latest` | Latest build from main branch |
| `<branch>` | `main`, `develop` | Latest build from that branch |
| `pr-<num>` | `pr-123` | Build from pull request |
| `<version>` | `1.0.0` | Semantic version from git tag |
| `<major>.<minor>` | `1.0` | Major.minor version |
| `<major>` | `1` | Major version only |
| `<branch>-<sha>` | `main-abc1234` | Branch with commit SHA |

## Security Scanning

Every build is automatically scanned for vulnerabilities using Trivy.

**View scan results:**
1. Go to the "Security" tab in your repository
2. Click "Code scanning alerts"
3. Filter by "Trivy"

## Troubleshooting

### Build Failed

**Check the logs:**
1. Go to Actions tab
2. Click on the failed run
3. Expand the failed step to see error details

**Common issues:**
- Dockerfile syntax error
- Missing dependencies
- Network timeout during build

### Permission Denied

**Fix:**
1. Go to Settings → Actions → General
2. Under "Workflow permissions"
3. Select "Read and write permissions"
4. Click "Save"

### Image Not Found After Build

**Verify:**
1. Check if the build completed successfully
2. Ensure you're authenticated: `docker login ghcr.io`
3. Check if the image is private (may need authentication)

### Can't Pull Private Images

**Authenticate:**
```bash
# Create a Personal Access Token with read:packages scope
# Then login:
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin
```

## Advanced Usage

### Build Specific Platforms

The workflow builds for both `linux/amd64` and `linux/arm64` by default.

To modify platforms, edit `.github/workflows/docker-build.yml`:

```yaml
platforms: linux/amd64,linux/arm64,linux/arm/v7
```

### Add Build Arguments

To pass build arguments to Docker:

```yaml
- name: Build and push Backend image
  uses: docker/build-push-action@v5
  with:
    # ... existing config ...
    build-args: |
      BUILD_DATE=${{ github.event.head_commit.timestamp }}
      VCS_REF=${{ github.sha }}
```

### Customize Tags

To modify tagging strategy, edit the `docker/metadata-action` step:

```yaml
- name: Extract metadata for Backend
  id: meta
  uses: docker/metadata-action@v5
  with:
    images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_BACKEND }}
    tags: |
      type=ref,event=branch
      type=semver,pattern={{version}}
      type=raw,value=my-custom-tag
```

## Performance

**Build times:**
- First build: ~5-10 minutes
- Subsequent builds: ~2-5 minutes (with cache)

**Cache optimization:**
- Layer caching enabled via GitHub Actions cache
- BuildKit cache mode: `max` (caches all layers)
- Cache shared across workflow runs

## Cost

**GitHub Actions:**
- Public repos: Unlimited minutes
- Private repos: 2,000 free minutes/month

**GitHub Container Registry:**
- Public images: Free unlimited storage
- Private images: 500MB free, then $0.25/GB/month

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Full CI/CD Documentation](../../docs/CI_CD.md)

