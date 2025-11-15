# 🔧 Production Database Migration Fix

## Current Error

```
asyncpg.exceptions.DuplicateObjectError: type "chat_type_enum" already exists
```

**Cause:** Your production database has tables created by the old `init_db()` but Alembic doesn't know about them.

## ✅ SOLUTION (3 Simple Commands)

### Step 1: Check Database State

```bash
docker exec whatslang-backend python check_db_state.py
```

This diagnostic will show you:
- What tables exist
- What Alembic version is recorded (if any)
- What's missing
- Recommended fix strategy

### Step 2: Stamp Database (Tell Alembic Current State)

```bash
docker exec whatslang-backend alembic stamp 0001
```

**What this does:** Marks your database as being at version 0001 (initial schema) without running the migration, since your tables already exist.

### Step 3: Run Migration for Missing Column

```bash
docker exec whatslang-backend python run_migrations.py
```

**What this does:** 
- ✅ Skips migration 0001 (already stamped)
- ✅ Runs migration 0002 (adds `last_message_at` column)
- ✅ Updates Alembic version to 0002 (head)

### Step 4: Verify Success

```bash
# Check Alembic version - should show: 0002 (head)
docker exec whatslang-backend alembic current

# Test application
curl http://localhost:8000/health
curl http://localhost:8000/api/chats
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade 0001 -> 0002, add_last_message_at_to_chats
✓ Database migrations completed successfully!
```

## 🎉 Done!

Your database is now:
- ✅ At version 0002 (latest)
- ✅ Has the `last_message_at` column
- ✅ Tracked by Alembic
- ✅ Ready for future auto-migrations

## Alternative: If Tables Are Missing or Corrupt

If the database state is inconsistent, you may need to:

### Option A: Fresh Start (Data Loss!)

```bash
# ⚠️  WARNING: This destroys all data!

# Stop services
docker-compose down

# Remove database volume
docker volume rm whatslang_postgres_data

# Restart - migrations will run automatically
docker-compose up -d
```

### Option B: Manual Fix

```bash
# 1. Backup database first!
docker exec whatslang-db pg_dump -U whatslang whatslang > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Check what's missing
docker exec whatslang-backend python check_db_state.py

# 3. Create alembic_version table if needed
docker exec whatslang-db psql -U whatslang whatslang -c "
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);"

# 4. Stamp to version 0001
docker exec whatslang-backend alembic stamp 0001

# 5. Run migrations
docker exec whatslang-backend python run_migrations.py
```

## Understanding the Fix

### What Changed

I've updated the first migration (`0001_initial_schema.py`) to be **idempotent** - it can now safely run even if some objects exist:

```python
# Old (would fail if enum exists):
op.execute("CREATE TYPE chat_type_enum AS ENUM ('private', 'group', 'channel')")

# New (safe to run multiple times):
op.execute("""
    DO $$ BEGIN
        CREATE TYPE chat_type_enum AS ENUM ('private', 'group', 'channel');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
""")
```

### Why Stamp?

- Your database has tables from `init_db()` 
- But Alembic doesn't know about them (no `alembic_version` table)
- Running migration 0001 would try to create existing tables → error
- Stamping tells Alembic "treat the database as if migration 0001 was already applied"
- Then migration 0002 can run to add the missing column

## Quick Command Reference

```bash
# Check database state
docker exec whatslang-backend python check_db_state.py

# Stamp database (mark as version 0001)
docker exec whatslang-backend alembic stamp 0001

# Run migrations (applies 0002)
docker exec whatslang-backend python run_migrations.py

# Check current version
docker exec whatslang-backend alembic current

# View migration history
docker exec whatslang-backend alembic history --verbose

# Rollback if needed
docker exec whatslang-backend alembic downgrade -1
```

## Files Changed

- ✅ `backend/alembic/versions/20250114_0001_initial_schema.py` - Made idempotent
- ✅ `backend/check_db_state.py` - NEW: Database diagnostic tool

## Prevention

After this fix, future deployments will:
1. ✅ Run migrations automatically via `entrypoint.sh`
2. ✅ Track version in database
3. ✅ Apply only new migrations
4. ✅ Never duplicate objects

---

**Need Help?**
- Run `docker exec whatslang-backend python check_db_state.py` to diagnose
- Check logs: `docker logs whatslang-backend`
- See [docs/MIGRATIONS.md](docs/MIGRATIONS.md) for details

