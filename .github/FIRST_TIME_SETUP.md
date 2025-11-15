# First Time CI/CD Setup Checklist

Use this checklist to set up the CI/CD pipeline for the first time.

## ✅ Pre-Push Checklist

Before pushing the CI/CD configuration to GitHub, verify these items:

### 1. Files Created
- [ ] `.github/workflows/docker-build.yml` - Main workflow file
- [ ] `.github/workflows/README.md` - Workflow documentation
- [ ] `.github/workflows/WORKFLOW_DIAGRAM.md` - Visual flow diagram
- [ ] `docs/CI_CD.md` - Comprehensive CI/CD documentation
- [ ] `docker-compose.registry.yml` - Registry configuration
- [ ] `scripts/update-registry-config.sh` - Helper script
- [ ] `GITHUB_ACTIONS_SETUP.md` - Quick setup guide
- [ ] `CI_CD_SUMMARY.md` - Implementation summary

### 2. Documentation Updated
- [ ] `README.md` - Added build badge and CI/CD section
- [ ] Repository URL updated to `madpin/whatslang`
- [ ] All placeholder `<owner>/<repo>` replaced

### 3. Docker Configuration
- [ ] Backend `Dockerfile` exists and is valid
- [ ] Frontend `Dockerfile` exists and is valid
- [ ] Both Dockerfiles can build successfully locally

### 4. Git Status
- [ ] All new files are staged
- [ ] Commit message is descriptive
- [ ] On correct branch (main or develop)

## 🚀 Push and Enable

### Step 1: Push to GitHub

```bash
# Review changes
git status

# Add all new files
git add .github/ docs/ scripts/ *.yml *.md

# Commit
git commit -m "Add GitHub Actions CI/CD pipeline

- Automated Docker image builds
- Multi-architecture support (amd64, arm64)
- Security scanning with Trivy
- Comprehensive documentation
- Helper scripts and configurations"

# Push
git push origin main
```

### Step 2: Enable Workflow Permissions

1. [ ] Go to https://github.com/madpin/whatslang/settings/actions
2. [ ] Scroll to **"Workflow permissions"**
3. [ ] Select **"Read and write permissions"**
4. [ ] Check **"Allow GitHub Actions to create and approve pull requests"**
5. [ ] Click **"Save"**

### Step 3: Verify First Build

1. [ ] Go to https://github.com/madpin/whatslang/actions
2. [ ] Click on the latest **"Build and Push Docker Images"** workflow
3. [ ] Verify all jobs are running:
   - [ ] `build-backend` job started
   - [ ] `build-frontend` job started
4. [ ] Wait for completion (~10-15 minutes for first build)
5. [ ] Verify all jobs passed:
   - [ ] `build-backend` ✅
   - [ ] `build-frontend` ✅
   - [ ] `security-scan` ✅

### Step 4: Verify Images Published

1. [ ] Go to https://github.com/madpin?tab=packages
2. [ ] Verify packages exist:
   - [ ] `whatslang/backend`
   - [ ] `whatslang/frontend`
3. [ ] Click on each package
4. [ ] Verify tags are present:
   - [ ] `latest`
   - [ ] `main`
   - [ ] `main-<sha>`

## 🔓 Make Images Public (Optional)

If you want anyone to pull images without authentication:

### For Backend Image
1. [ ] Go to https://github.com/madpin/whatslang/pkgs/container/whatslang%2Fbackend
2. [ ] Click **"Package settings"** (bottom right)
3. [ ] Scroll to **"Danger Zone"**
4. [ ] Click **"Change visibility"**
5. [ ] Select **"Public"**
6. [ ] Type package name to confirm
7. [ ] Click **"I understand, change package visibility"**

### For Frontend Image
1. [ ] Go to https://github.com/madpin/whatslang/pkgs/container/whatslang%2Ffrontend
2. [ ] Click **"Package settings"** (bottom right)
3. [ ] Scroll to **"Danger Zone"**
4. [ ] Click **"Change visibility"**
5. [ ] Select **"Public"**
6. [ ] Type package name to confirm
7. [ ] Click **"I understand, change package visibility"**

## 🧪 Test the Pipeline

### Test 1: Pull Images Locally

```bash
# For public images (no auth needed)
docker pull ghcr.io/madpin/whatslang/backend:latest
docker pull ghcr.io/madpin/whatslang/frontend:latest

# For private images (auth required)
echo $GITHUB_TOKEN | docker login ghcr.io -u madpin --password-stdin
docker pull ghcr.io/madpin/whatslang/backend:latest
docker pull ghcr.io/madpin/whatslang/frontend:latest
```

- [ ] Backend image pulled successfully
- [ ] Frontend image pulled successfully
- [ ] Images are correct size (not empty)

### Test 2: Run Images

```bash
# Test with registry configuration
docker-compose -f docker-compose.registry.yml up -d

# Wait for services to start
sleep 30

# Check health
curl http://localhost:8000/health
curl http://localhost:3000
```

- [ ] Backend starts successfully
- [ ] Frontend starts successfully
- [ ] Health checks pass
- [ ] Services communicate correctly

### Test 3: Create a Version Tag

```bash
# Create and push a version tag
git tag -a v0.1.0 -m "Initial release with CI/CD"
git push origin v0.1.0
```

- [ ] Workflow triggered by tag
- [ ] Build completed successfully
- [ ] Version tags created:
  - [ ] `v0.1.0`
  - [ ] `0.1.0`
  - [ ] `0.1`
  - [ ] `0`

### Test 4: Create a Pull Request

```bash
# Create a feature branch
git checkout -b test/ci-cd-validation
echo "# Test" >> TEST.md
git add TEST.md
git commit -m "Test PR build"
git push origin test/ci-cd-validation
```

- [ ] Create PR on GitHub
- [ ] Workflow triggered
- [ ] Build runs but doesn't push images
- [ ] All checks pass

## 📊 Verify Security Scanning

1. [ ] Go to https://github.com/madpin/whatslang/security/code-scanning
2. [ ] Verify Trivy scans are present
3. [ ] Review any vulnerabilities found
4. [ ] Create issues for critical vulnerabilities if needed

## 📝 Update Documentation

### Update README Badge

The badge should now show build status:

![Docker Build](https://github.com/madpin/whatslang/actions/workflows/docker-build.yml/badge.svg)

- [ ] Badge shows "passing" status
- [ ] Badge links to Actions page

### Share with Team

- [ ] Share `GITHUB_ACTIONS_SETUP.md` with team
- [ ] Document in team wiki/docs
- [ ] Add to onboarding materials

## 🎉 Success Criteria

All items below should be ✅:

- [ ] Workflow file is valid and runs
- [ ] Backend image builds and pushes
- [ ] Frontend image builds and pushes
- [ ] Security scans complete
- [ ] Images can be pulled and run
- [ ] Documentation is complete
- [ ] Team is informed

## 🐛 Troubleshooting

If something fails, check:

### Build Fails
- [ ] Review workflow logs at https://github.com/madpin/whatslang/actions
- [ ] Check Dockerfile syntax
- [ ] Verify all dependencies are available
- [ ] Check for network timeouts

### Permission Errors
- [ ] Verify workflow permissions are set to "Read and write"
- [ ] Check if GITHUB_TOKEN has package write access
- [ ] Verify branch protection rules don't block workflow

### Images Not Pushing
- [ ] Check if build completed successfully
- [ ] Verify you're not on a pull request (PRs don't push)
- [ ] Check workflow logs for push step

### Can't Pull Images
- [ ] Verify images were pushed (check packages page)
- [ ] For private images, ensure you're authenticated
- [ ] Check image tag exists

## 📞 Getting Help

If you encounter issues:

1. **Check Documentation**
   - `docs/CI_CD.md` - Comprehensive guide
   - `GITHUB_ACTIONS_SETUP.md` - Setup instructions
   - `.github/workflows/README.md` - Workflow reference

2. **Review Logs**
   - Workflow logs: https://github.com/madpin/whatslang/actions
   - Docker build logs in workflow output
   - Security scan results in Security tab

3. **Common Resources**
   - [GitHub Actions Docs](https://docs.github.com/en/actions)
   - [GHCR Docs](https://docs.github.com/en/packages)
   - [Docker Build Action](https://github.com/docker/build-push-action)

4. **Open an Issue**
   - https://github.com/madpin/whatslang/issues
   - Include workflow run URL
   - Include error messages

## 📅 Next Steps

After successful setup:

- [ ] Set up automated deployment
- [ ] Configure notifications (Slack/Discord)
- [ ] Add automated testing
- [ ] Set up staging environment
- [ ] Document deployment process
- [ ] Train team on using the pipeline

## ✨ Congratulations!

Once all items are checked, your CI/CD pipeline is fully operational! 🎉

Every push to main/develop will now automatically:
- Build Docker images
- Push to GitHub Container Registry
- Run security scans
- Make images available for deployment

---

**Date Completed:** _______________
**Completed By:** _______________
**Notes:** _______________

