# 🚨 Quick Fix: Missing Column Error

## Problem
```
asyncpg.exceptions.UndefinedColumnError: column chats.last_message_at does not exist
```

## Solution (Choose One)

### Option 1: Run Migration in Production Container
```bash
docker exec whatslang-backend python run_migrations.py
```

### Option 2: Using Alembic Directly
```bash
docker exec whatslang-backend alembic upgrade head
```

### Option 3: Restart with New Entrypoint (Automatic)
The entrypoint script now automatically runs migrations on container startup.

```bash
# Rebuild and restart
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## What Was Fixed

1. ✅ **`run_migrations.py`** - Now properly runs Alembic migrations
2. ✅ **`entrypoint.sh`** - New startup script that runs migrations before starting the app
3. ✅ **`Dockerfile`** - Updated to use the new entrypoint
4. ✅ **Documentation** - Added comprehensive [Migrations Guide](docs/MIGRATIONS.md)

## Next Steps

**For Existing Production:**
- Run Option 1 or 2 above to fix immediately
- Then update your code and rebuild to get automatic migrations

**For New Deployments:**
- Just deploy normally - migrations run automatically!

## Verify Success

```bash
# Check migration status
docker exec whatslang-backend alembic current

# Expected output: 0002 (head)

# Check logs
docker logs whatslang-backend | grep migration
```

## Need Help?

See [docs/MIGRATIONS.md](docs/MIGRATIONS.md) for:
- Detailed migration commands
- Troubleshooting guide
- Best practices
- Rollback procedures

---

**Quick Commands Reference:**

```bash
# Check current migration version
docker exec whatslang-backend alembic current

# View migration history
docker exec whatslang-backend alembic history

# Rollback one migration
docker exec whatslang-backend alembic downgrade -1

# Backup database before migrations
docker exec whatslang-db pg_dump -U whatslang whatslang > backup_$(date +%Y%m%d_%H%M%S).sql
```

