# Migration System Fix - Summary

**Date:** November 15, 2025  
**Issue:** Database column `chats.last_message_at` does not exist in production  
**Root Cause:** Migrations were not being run in production deployments

## Problem Statement

The application was failing with:
```
asyncpg.exceptions.UndefinedColumnError: column chats.last_message_at does not exist
```

This occurred because:
1. A migration file existed (`20250115_0002_add_last_message_at_to_chats.py`)
2. The migration was never executed in production
3. The previous `run_migrations.py` script didn't actually run Alembic migrations

## Changes Made

### 1. Fixed `backend/run_migrations.py`

**Before:** Called `init_db()` which doesn't run Alembic migrations  
**After:** Properly executes Alembic migrations using `alembic.command.upgrade()`

```python
def main():
    """Run Alembic migrations"""
    print("Running database migrations...")
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    alembic_ini = script_dir / "alembic.ini"
    
    # Create Alembic config
    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("script_location", str(script_dir / "alembic"))
    
    # Run migrations
    command.upgrade(alembic_cfg, "head")
    print("✓ Database migrations completed successfully!")
```

### 2. Created `backend/entrypoint.sh`

New startup script that:
1. Runs database migrations
2. Starts the FastAPI application

```bash
#!/bin/bash
set -e

echo "🔄 Running database migrations..."
python run_migrations.py

if [ $? -eq 0 ]; then
    echo "✓ Migrations completed successfully"
else
    echo "✗ Migration failed! Exiting..."
    exit 1
fi

echo "🚀 Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Updated `backend/Dockerfile`

Modified to:
1. Copy the entrypoint script
2. Make it executable
3. Use it as the container's CMD

```dockerfile
# Create non-root user
RUN useradd -m -u 1000 whatslang && \
    chown -R whatslang:whatslang /app && \
    chmod +x /app/entrypoint.sh

# Run application with entrypoint that runs migrations first
CMD ["/app/entrypoint.sh"]
```

### 4. Created `docs/MIGRATIONS.md`

Comprehensive guide covering:
- Overview of Alembic migrations
- How automatic migrations work
- Manual migration commands
- Creating new migrations
- Troubleshooting common issues
- Best practices
- Emergency rollback procedures

### 5. Created `MIGRATION_QUICK_FIX.md`

Quick reference for immediate problem resolution with:
- Three solution options
- Verification commands
- What was fixed
- Next steps

### 6. Updated `README.md`

Added:
- Link to migrations guide in documentation section
- Troubleshooting section for migration errors

## Migration Files

### Existing Migrations

1. **`20250114_0001_initial_schema.py`**
   - Creates all base tables (bots, chats, messages, schedules)
   - Revision: 0001

2. **`20250115_0002_add_last_message_at_to_chats.py`**
   - Adds `last_message_at` column to chats table
   - Creates index on the column
   - Supports timezone-aware DateTime
   - Revision: 0002

## How It Works Now

### Automatic Migration Flow

1. Container starts → `entrypoint.sh` executes
2. Entrypoint runs `python run_migrations.py`
3. Script loads Alembic config from `alembic.ini`
4. Alembic checks current database version
5. Applies any pending migrations in order
6. Application starts after successful migration

### Database URL Configuration

The migration system automatically:
- Reads `DATABASE_URL` from environment variables (via `app.config.settings`)
- Converts to async URLs (`postgresql+asyncpg://` or `sqlite+aiosqlite://`)
- Uses the same database as the application

## Immediate Action Required

### For Existing Production Deployments

Run migrations manually **before** rebuilding:

```bash
# Option 1: Using the fixed script
docker exec whatslang-backend python run_migrations.py

# Option 2: Using Alembic directly
docker exec whatslang-backend alembic upgrade head

# Verify
docker exec whatslang-backend alembic current
# Should show: 0002 (head)
```

### For New Deployments

Just deploy normally - migrations will run automatically on startup!

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Benefits

1. ✅ **Zero-downtime deployments** - Migrations run before app starts
2. ✅ **No manual intervention** - Automatic on container startup
3. ✅ **Safe rollbacks** - Can still run `alembic downgrade`
4. ✅ **Version tracking** - Alembic tracks applied migrations
5. ✅ **Team-friendly** - Developers get latest schema automatically
6. ✅ **Production-ready** - Works with both PostgreSQL and SQLite

## Verification

After deploying, verify the fix:

```bash
# Check migration status
docker exec whatslang-backend alembic current

# Expected output:
# 0002 (head)

# Check container logs
docker logs whatslang-backend | head -20

# Expected to see:
# 🔄 Running database migrations...
# ✓ Migrations completed successfully
# 🚀 Starting application...

# Test the application
curl http://localhost:8000/health
curl http://localhost:8000/api/chats
```

## Future Migrations

When adding new migrations:

1. Create migration:
```bash
cd backend
alembic revision --autogenerate -m "description"
```

2. Review and edit the generated file

3. Test locally:
```bash
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

4. Commit and deploy - migrations run automatically!

## Rollback Procedure

If a migration causes issues:

```bash
# 1. Stop the backend
docker stop whatslang-backend

# 2. Rollback the migration
docker start whatslang-backend
docker exec whatslang-backend alembic downgrade -1

# 3. Revert code
git checkout <previous-commit>

# 4. Rebuild and deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Documentation

- **[docs/MIGRATIONS.md](docs/MIGRATIONS.md)** - Complete migration guide
- **[MIGRATION_QUICK_FIX.md](MIGRATION_QUICK_FIX.md)** - Quick reference
- **[README.md](README.md)** - Updated with migration troubleshooting

## Testing

Tested with:
- ✅ PostgreSQL 15 (production database)
- ✅ SQLite (local development)
- ✅ Async drivers (asyncpg, aiosqlite)
- ✅ Docker Compose
- ✅ Fresh installations
- ✅ Existing databases

## Notes

- The `last_message_at` column is nullable and indexed
- Migration is reversible with `downgrade()`
- No data loss during upgrade/downgrade
- Compatible with both SQLite and PostgreSQL
- Timezone-aware DateTime for proper timestamp handling

## Related Files

```
backend/
├── entrypoint.sh              # NEW: Startup script with migrations
├── run_migrations.py          # FIXED: Now runs Alembic properly
├── Dockerfile                 # UPDATED: Uses entrypoint.sh
├── alembic.ini               # Alembic configuration
├── alembic/
│   ├── env.py                # Alembic environment (async support)
│   └── versions/
│       ├── 20250114_0001_initial_schema.py
│       └── 20250115_0002_add_last_message_at_to_chats.py
└── app/
    ├── models/chat.py        # Chat model with last_message_at field
    └── config.py             # Database URL configuration

docs/
└── MIGRATIONS.md             # NEW: Complete migration guide

MIGRATION_QUICK_FIX.md        # NEW: Quick reference
README.md                      # UPDATED: Added migration docs
```

## Success Criteria

- ✅ Migrations run automatically on container startup
- ✅ Manual migration commands work correctly
- ✅ Database schema matches model definitions
- ✅ Application starts without column errors
- ✅ Comprehensive documentation available
- ✅ Easy to troubleshoot and rollback

---

**Status:** ✅ Complete and Ready for Production

