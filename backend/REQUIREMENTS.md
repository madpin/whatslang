# Requirements Files

This project has two requirements files depending on your use case:

## requirements-local.txt (Recommended for Development)

Use this for **local development with SQLite**:

```bash
pip install -r requirements-local.txt
```

**Includes:**
- ✅ FastAPI, SQLAlchemy, Alembic
- ✅ SQLite support (aiosqlite)
- ✅ All bot functionality (OpenAI, httpx, etc.)
- ❌ No PostgreSQL dependencies (psycopg2, asyncpg)

**Advantages:**
- ✅ Faster installation (no PostgreSQL build dependencies needed)
- ✅ Works without PostgreSQL installed
- ✅ Perfect for quick testing and development

## requirements.txt (Full Setup)

Use this for **production or PostgreSQL development**:

```bash
pip install -r requirements.txt
```

**Includes:**
- ✅ Everything from requirements-local.txt
- ✅ PostgreSQL support (psycopg2-binary, asyncpg)

**Requirements:**
- Needs PostgreSQL development headers installed on your system
- On macOS: `brew install postgresql`
- On Ubuntu/Debian: `sudo apt-get install libpq-dev`

## Quick Reference

| Use Case | Requirements File | Database |
|----------|------------------|----------|
| Quick local testing | `requirements-local.txt` | SQLite |
| Local development | `requirements-local.txt` | SQLite |
| Production-like testing | `requirements.txt` | PostgreSQL |
| Docker deployment | `requirements.txt` | PostgreSQL |
| Production | `requirements.txt` | PostgreSQL |

## Scripts

The start scripts automatically use the right requirements:

- `./start-local.sh` → uses `requirements-local.txt` (SQLite)
- `./start.sh` → Docker Compose (uses `requirements.txt`)

## Troubleshooting

### psycopg2-binary build error

If you see errors about `pg_config` not found, you're trying to install PostgreSQL dependencies without PostgreSQL installed.

**Solution 1**: Use SQLite instead (recommended for local dev)
```bash
pip install -r requirements-local.txt
```

**Solution 2**: Install PostgreSQL development headers
```bash
# macOS
brew install postgresql

# Ubuntu/Debian
sudo apt-get install libpq-dev python3-dev

# Then retry
pip install -r requirements.txt
```

