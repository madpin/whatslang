# 🧭 Documentation Navigation Guide

Quick reference for finding the right documentation.

## 🎯 I want to...

### Get Started
- **Start quickly** → [`QUICKSTART.md`](QUICKSTART.md) - Get running in 3-10 minutes
- **Understand the project** → [`../README.md`](../README.md) - Features, architecture, examples

### Deploy
- **Deploy to production** → [`DEPLOYMENT.md`](DEPLOYMENT.md) - Dokploy, Docker, Kubernetes, VPS
- **Set up persistence** → [`PERSISTENCE.md`](PERSISTENCE.md) - Database, backups, volumes
- **Use virtual environments** → [`VENV_GUIDE.md`](VENV_GUIDE.md) - Python venv setup

### Contribute
- **Contribute code** → [`../CONTRIBUTING.md`](../CONTRIBUTING.md) - Guidelines, standards, workflow
- **See what changed** → [`../CHANGELOG.md`](../CHANGELOG.md) - Version history

### Troubleshoot
- **Fix issues** → [`../README.md#troubleshooting`](../README.md#troubleshooting) - Common problems
- **Check health** → [`../README.md#production-features`](../README.md#production-features) - Health checks

### Develop
- **Create a bot** → [`../README.md#creating-custom-bots`](../README.md#creating-custom-bots) - Bot template
- **See implementation notes** → [`dev-notes/`](dev-notes/) - Historical dev documentation

## 📂 Documentation Structure

```
Root Level (Main Docs)
├── README.md              ⭐ Start here
├── CONTRIBUTING.md        👥 For contributors
└── CHANGELOG.md           📋 Version history

docs/ (User Guides)
├── QUICKSTART.md          🚀 Quick start
├── DEPLOYMENT.md          ☁️ Deployment
├── PERSISTENCE.md         💾 Data persistence
└── VENV_GUIDE.md         🐍 Virtual environments

docs/dev-notes/ (Development History)
└── [10 implementation summaries]
```

## 🔍 Quick Search

| Topic | File |
|-------|------|
| Getting started | [`QUICKSTART.md`](QUICKSTART.md) |
| Local development | [`../README.md`](../README.md) |
| Docker deployment | [`DEPLOYMENT.md`](DEPLOYMENT.md#docker) |
| Dokploy deployment | [`DEPLOYMENT.md`](DEPLOYMENT.md#dokploy-nixpacks) |
| Kubernetes | [`DEPLOYMENT.md`](DEPLOYMENT.md#kubernetes) |
| Database backup | [`PERSISTENCE.md`](PERSISTENCE.md) |
| Virtual environment | [`VENV_GUIDE.md`](VENV_GUIDE.md) |
| Creating bots | [`../README.md#creating-custom-bots`](../README.md#creating-custom-bots) |
| API reference | Run service → `/docs` endpoint |
| Health checks | [`../README.md#health-checks`](../README.md#health-checks) |
| Contributing | [`../CONTRIBUTING.md`](../CONTRIBUTING.md) |
| Version history | [`../CHANGELOG.md`](../CHANGELOG.md) |

## 💡 Tips

- **First time here?** Start with [`QUICKSTART.md`](QUICKSTART.md)
- **Deploying to production?** See [`DEPLOYMENT.md`](DEPLOYMENT.md)
- **Need API docs?** Run the service and visit `/docs`
- **Looking for old implementation notes?** Check [`dev-notes/`](dev-notes/)

---

[← Back to Documentation Index](README.md) | [↑ Back to Main README](../README.md)

