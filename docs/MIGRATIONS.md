# Database Migrations Guide

This guide explains how to manage database migrations in WhatSlang using Alembic.

## Overview

WhatSlang uses [Alembic](https://alembic.sqlalchemy.org/) for database schema migrations. Migrations are automatically run on application startup in the Docker container.

## Automatic Migrations

**New in this update:** Migrations now run automatically when the backend container starts.

The `entrypoint.sh` script:
1. Runs `python run_migrations.py` to apply any pending migrations
2. Starts the FastAPI application

This ensures your database schema is always up-to-date.

## Manual Migration Commands

### Run All Pending Migrations

```bash
# In production (Docker)
docker exec whatslang-backend python run_migrations.py

# Or using Alembic directly
docker exec whatslang-backend alembic upgrade head

# In development (local)
cd backend
python run_migrations.py
# Or
alembic upgrade head
```

### Check Current Migration Status

```bash
# In production
docker exec whatslang-backend alembic current

# In development
cd backend
alembic current
```

### View Migration History

```bash
# In production
docker exec whatslang-backend alembic history

# In development
cd backend
alembic history
```

### Rollback Last Migration

```bash
# In production
docker exec whatslang-backend alembic downgrade -1

# In development
cd backend
alembic downgrade -1
```

## Creating New Migrations

### Auto-generate Migration from Model Changes

```bash
cd backend
alembic revision --autogenerate -m "description of changes"
```

This will:
1. Compare your SQLAlchemy models with the current database schema
2. Generate a migration script in `backend/alembic/versions/`
3. Include both `upgrade()` and `downgrade()` functions

### Create Empty Migration

```bash
cd backend
alembic revision -m "description of changes"
```

Then manually edit the generated file to add your migration logic.

## Migration File Structure

Migration files are in `backend/alembic/versions/` and follow this naming pattern:

```
YYYYMMDD_HHMM_XXXX_description.py
```

Example: `20250115_0002_add_last_message_at_to_chats.py`

Each migration has:
- `revision`: Unique ID for this migration
- `down_revision`: ID of the previous migration (creates a linked chain)
- `upgrade()`: Function to apply the migration
- `downgrade()`: Function to rollback the migration

## Current Migrations

1. **0001_initial_schema** - Creates all base tables (bots, chats, messages, schedules)
2. **0002_add_last_message_at_to_chats** - Adds `last_message_at` column to chats table

## Troubleshooting

### Error: Column does not exist

**Symptom:** `asyncpg.exceptions.UndefinedColumnError: column chats.xxx does not exist`

**Cause:** Migrations haven't been run on the database.

**Solution:**
```bash
docker exec whatslang-backend python run_migrations.py
```

### Error: Migration failed

**Symptom:** Migration script fails with SQL error

**Solutions:**
1. Check the database state: `docker exec whatslang-backend alembic current`
2. Review migration history: `docker exec whatslang-backend alembic history`
3. If needed, manually fix the database or rollback: `docker exec whatslang-backend alembic downgrade -1`

### Error: Alembic can't find migrations directory

**Symptom:** `FileNotFoundError: alembic/versions`

**Cause:** Running alembic from wrong directory

**Solution:** Always run alembic commands from the `backend/` directory

### Database out of sync

If your database schema and migrations are completely out of sync:

```bash
# Option 1: Start fresh (WARNING: destroys all data)
docker-compose down -v
docker-compose up -d

# Option 2: Stamp current version without running migrations
docker exec whatslang-backend alembic stamp head
```

## Best Practices

1. **Always test migrations locally first** before deploying to production
2. **Never edit an existing migration** that's been deployed to production
3. **Always include a downgrade function** to allow rollbacks
4. **Keep migrations small and focused** - one logical change per migration
5. **Test both upgrade and downgrade** before committing
6. **Backup production database** before running migrations

## Database Backup Before Migrations

Always backup your production database before running migrations:

```bash
# Backup PostgreSQL database
docker exec whatslang-db pg_dump -U whatslang whatslang > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore if needed
cat backup_YYYYMMDD_HHMMSS.sql | docker exec -i whatslang-db psql -U whatslang whatslang
```

## Development Workflow

1. Make changes to SQLAlchemy models in `backend/app/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review and edit the generated migration in `backend/alembic/versions/`
4. Test upgrade: `alembic upgrade head`
5. Test downgrade: `alembic downgrade -1`
6. Re-apply: `alembic upgrade head`
7. Commit both model changes and migration file

## Production Deployment

When deploying changes that include migrations:

1. **Backup database** (see above)
2. **Pull latest code**: `git pull`
3. **Rebuild containers**: `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`
4. Migrations run automatically on container start via `entrypoint.sh`
5. **Verify migration success**: Check logs with `docker logs whatslang-backend`

## Emergency Rollback

If a migration causes issues in production:

```bash
# 1. Stop the backend
docker stop whatslang-backend

# 2. Rollback the migration
docker exec whatslang-backend alembic downgrade -1

# 3. Optionally restore database backup
cat backup.sql | docker exec -i whatslang-db psql -U whatslang whatslang

# 4. Start the backend with previous code version
git checkout <previous-commit>
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Configuration

Migration configuration is in:
- `backend/alembic.ini` - Alembic configuration
- `backend/alembic/env.py` - Alembic environment setup
- `backend/app/config.py` - Database URL and settings

The database URL is automatically read from the `DATABASE_URL` environment variable.

## Support

For issues or questions about migrations:
1. Check the Alembic documentation: https://alembic.sqlalchemy.org/
2. Review recent migration files for examples
3. Check application logs: `docker logs whatslang-backend`

