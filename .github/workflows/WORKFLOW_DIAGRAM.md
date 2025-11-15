# CI/CD Workflow Diagram

## Overview Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Developer Actions                            │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
              ┌──────────┐  ┌──────────┐  ┌──────────┐
              │   Push   │  │   Pull   │  │   Tag    │
              │   Code   │  │  Request │  │ Release  │
              └──────────┘  └──────────┘  └──────────┘
                    │             │             │
                    └─────────────┼─────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      GitHub Actions Trigger                          │
│                   .github/workflows/docker-build.yml                 │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
          ┌──────────────────┐        ┌──────────────────┐
          │  build-backend   │        │  build-frontend  │
          │      Job         │        │       Job        │
          └──────────────────┘        └──────────────────┘
                    │                           │
                    ├───────────────────────────┤
                    │                           │
                    ▼                           ▼
          ┌──────────────────┐        ┌──────────────────┐
          │ 1. Checkout Code │        │ 1. Checkout Code │
          └──────────────────┘        └──────────────────┘
                    │                           │
                    ▼                           ▼
          ┌──────────────────┐        ┌──────────────────┐
          │ 2. Setup Buildx  │        │ 2. Setup Buildx  │
          └──────────────────┘        └──────────────────┘
                    │                           │
                    ▼                           ▼
          ┌──────────────────┐        ┌──────────────────┐
          │ 3. Login to GHCR │        │ 3. Login to GHCR │
          │  (skip on PR)    │        │  (skip on PR)    │
          └──────────────────┘        └──────────────────┘
                    │                           │
                    ▼                           ▼
          ┌──────────────────┐        ┌──────────────────┐
          │ 4. Extract Tags  │        │ 4. Extract Tags  │
          │   - latest       │        │   - latest       │
          │   - branch name  │        │   - branch name  │
          │   - version      │        │   - version      │
          │   - commit sha   │        │   - commit sha   │
          └──────────────────┘        └──────────────────┘
                    │                           │
                    ▼                           ▼
          ┌──────────────────┐        ┌──────────────────┐
          │ 5. Build & Push  │        │ 5. Build & Push  │
          │   - amd64        │        │   - amd64        │
          │   - arm64        │        │   - arm64        │
          │   - with cache   │        │   - with cache   │
          └──────────────────┘        └──────────────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  ▼
                    ┌─────────────────────────┐
                    │   Both Jobs Complete    │
                    └─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │   security-scan Job     │
                    │   (only on push)        │
                    └─────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
          ┌──────────────────┐        ┌──────────────────┐
          │  Scan Backend    │        │  Scan Frontend   │
          │  with Trivy      │        │  with Trivy      │
          └──────────────────┘        └──────────────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  ▼
                    ┌─────────────────────────┐
                    │ Upload to GitHub        │
                    │ Security Tab            │
                    └─────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Result: Images Published                     │
│                                                                      │
│  ghcr.io/madpin/whatslang/backend:latest                            │
│  ghcr.io/madpin/whatslang/backend:main                              │
│  ghcr.io/madpin/whatslang/backend:v1.0.0                            │
│  ghcr.io/madpin/whatslang/backend:main-abc1234                      │
│                                                                      │
│  ghcr.io/madpin/whatslang/frontend:latest                           │
│  ghcr.io/madpin/whatslang/frontend:main                             │
│  ghcr.io/madpin/whatslang/frontend:v1.0.0                           │
│  ghcr.io/madpin/whatslang/frontend:main-abc1234                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Trigger Scenarios

### Scenario 1: Push to Main Branch

```
Developer: git push origin main
    │
    ▼
GitHub Actions:
    ├─ Build backend → Push with tags: latest, main, main-abc1234
    ├─ Build frontend → Push with tags: latest, main, main-abc1234
    └─ Security scan → Upload results to Security tab
```

### Scenario 2: Push to Develop Branch

```
Developer: git push origin develop
    │
    ▼
GitHub Actions:
    ├─ Build backend → Push with tags: develop, develop-abc1234
    ├─ Build frontend → Push with tags: develop, develop-abc1234
    └─ Security scan → Upload results to Security tab
```

### Scenario 3: Create Version Tag

```
Developer: git tag v1.0.0 && git push origin v1.0.0
    │
    ▼
GitHub Actions:
    ├─ Build backend → Push with tags: v1.0.0, 1.0.0, 1.0, 1, latest
    ├─ Build frontend → Push with tags: v1.0.0, 1.0.0, 1.0, 1, latest
    └─ Security scan → Upload results to Security tab
```

### Scenario 4: Pull Request

```
Developer: Create PR to main
    │
    ▼
GitHub Actions:
    ├─ Build backend → Validate only (no push)
    ├─ Build frontend → Validate only (no push)
    └─ No security scan
    │
    ▼
Result: ✅ Build validation passed
```

## Image Tag Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                        Tag Generation                            │
└─────────────────────────────────────────────────────────────────┘

Event: Push to main
├─ latest              → Always points to latest main build
├─ main                → Latest from main branch
└─ main-abc1234        → Specific commit on main

Event: Push to develop
├─ develop             → Latest from develop branch
└─ develop-abc1234     → Specific commit on develop

Event: Tag v1.2.3
├─ latest              → Latest release
├─ v1.2.3              → Full version with v prefix
├─ 1.2.3               → Full semantic version
├─ 1.2                 → Major.minor version
└─ 1                   → Major version only

Event: Pull Request #42
└─ pr-42               → Build for validation (not pushed)
```

## Build Cache Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         First Build                              │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │  Download base images   │
                    │  Install dependencies   │
                    │  Build application      │
                    │  Create final image     │
                    └─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │  Save layers to cache   │
                    │  (GitHub Actions Cache) │
                    └─────────────────────────┘
                                  │
                                  ▼
                           Build Time: ~8-10 min

┌─────────────────────────────────────────────────────────────────┐
│                      Subsequent Builds                           │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │  Restore from cache     │
                    │  Only rebuild changed   │
                    │  layers                 │
                    └─────────────────────────┘
                                  │
                                  ▼
                           Build Time: ~2-5 min
```

## Parallel Execution

```
┌─────────────────────────────────────────────────────────────────┐
│                    Workflow Execution                            │
└─────────────────────────────────────────────────────────────────┘

Time: 0:00 ─────────────────────────────────────────────────────►

         ┌──────────────────────────────────┐
         │     build-backend (Job 1)        │
         │  ├─ Checkout                     │
         │  ├─ Setup Buildx                 │
         │  ├─ Login                        │
         │  ├─ Extract metadata             │
         │  └─ Build & Push (5-8 min)       │
         └──────────────────────────────────┘

         ┌──────────────────────────────────┐
         │     build-frontend (Job 2)       │
         │  ├─ Checkout                     │
         │  ├─ Setup Buildx                 │
         │  ├─ Login                        │
         │  ├─ Extract metadata             │
         │  └─ Build & Push (3-5 min)       │
         └──────────────────────────────────┘
                                  │
                                  ▼
         ┌──────────────────────────────────┐
         │     security-scan (Job 3)        │
         │  ├─ Scan backend (2 min)         │
         │  └─ Scan frontend (2 min)        │
         └──────────────────────────────────┘

Total Time: ~10-15 minutes (with cache: ~5-8 minutes)
```

## Security Scan Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Security Scanning                           │
└─────────────────────────────────────────────────────────────────┘

Images Built
    │
    ▼
┌─────────────────────┐
│   Pull Image from   │
│   GHCR              │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│   Run Trivy Scan    │
│   - OS packages     │
│   - Dependencies    │
│   - Known CVEs      │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│   Generate SARIF    │
│   Report            │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│   Upload to GitHub  │
│   Security Tab      │
└─────────────────────┘
    │
    ▼
View at: github.com/madpin/whatslang/security/code-scanning
```

## Multi-Architecture Build

```
┌─────────────────────────────────────────────────────────────────┐
│                   Multi-Arch Build Process                       │
└─────────────────────────────────────────────────────────────────┘

Single Dockerfile
    │
    ├─────────────────────┬─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
┌─────────┐         ┌─────────┐         ┌─────────┐
│ amd64   │         │ arm64   │         │ arm/v7  │
│ Build   │         │ Build   │         │ (opt)   │
└─────────┘         └─────────┘         └─────────┘
    │                     │                     │
    └─────────────────────┴─────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Create Manifest     │
              │   (Multi-arch image)  │
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Push to Registry    │
              └───────────────────────┘

Result: Docker automatically pulls correct architecture
```

## Legend

```
┌──────────┐
│   Box    │  = Process or Component
└──────────┘

    │
    ▼        = Flow Direction

    ├─       = Branch/Split

    └─       = Merge/Join
```

