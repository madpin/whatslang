# Data Persistence Guide

This guide explains how persistent data is managed in the WhatsApp Bot Service, especially for deployments using Dokploy or other container platforms.

## Overview

All persistent data that needs to survive between deployments is stored in the `/data` directory inside the container. This includes:

- **Database file** (`messages.db`) - Stores chat history, bot assignments, and processed messages
- **Any future persistent assets** - Logs, cached data, uploaded files, etc.

## Directory Structure

```
whatslang/
├── data/                    # Persistent data directory (local development)
│   ├── .gitkeep            # Keeps directory in git
│   └── messages.db         # SQLite database (ignored by git)
└── docker-compose.yml      # Container configuration
```

Inside the container, data is mounted at `/data`:
```
/data/
└── messages.db             # SQLite database
```

## Configuration

### Database Path

The database path is configured via environment variables or config files:

1. **Environment Variable** (highest priority):
   ```bash
   DB_PATH=/data/messages.db
   ```

2. **Config file** (`config.yaml`):
   ```yaml
   bot_settings:
     db_path: "data/messages.db"
   ```

3. **Default**: `messages.db` (in working directory)

### Docker Setup

The `Dockerfile` creates the `/data` directory with proper permissions:
```dockerfile
RUN useradd -m -u 1000 appuser && \
    mkdir -p /data && \
    chown -R appuser:appuser /app /data
```

## Deployment Strategies

### Local Development

For local development, data is stored in the `./data` directory:

```bash
# Run locally
python run.py

# Data is stored in ./data/messages.db
```

### Docker Compose (Local)

Using the default docker-compose configuration:

```yaml
volumes:
  whatslang-data:
    driver: local
```

To access the data:
```bash
# Find the volume location
docker volume inspect whatslang_whatslang-data

# Backup the data
docker cp whatslang-bot-service:/data ./backup/
```

### Dokploy / Production Deployment

For production deployments with Dokploy, you should use a **bind mount** to persist data on the host filesystem.

#### Option 1: Dokploy Volume Mount (Recommended)

In Dokploy's volume configuration:
- **Container Path**: `/data`
- **Host Path**: `/var/lib/dokploy/volumes/whatslang/data` (or your preferred location)
- **Mode**: `rw` (read-write)

#### Option 2: Custom docker-compose.override.yml

Create a `docker-compose.override.yml` file (not tracked in git):

```yaml
version: '3.8'

services:
  whatslang:
    volumes:
      - /var/lib/dokploy/volumes/whatslang/data:/data
```

This overrides the named volume with a bind mount.

#### Option 3: Environment-Specific Compose File

Create a `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  whatslang:
    volumes:
      - /var/lib/dokploy/volumes/whatslang/data:/data
```

Deploy with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Backup and Restore

### Manual Backup

```bash
# Backup from running container
docker exec whatslang-bot-service sqlite3 /data/messages.db .dump > backup.sql

# Or copy the entire file
docker cp whatslang-bot-service:/data/messages.db ./backup/messages.db
```

### Restore from Backup

```bash
# Stop the service
docker-compose down

# Restore the database file
docker cp ./backup/messages.db whatslang-bot-service:/data/messages.db

# Or restore from SQL dump
cat backup.sql | docker exec -i whatslang-bot-service sqlite3 /data/messages.db

# Start the service
docker-compose up -d
```

### Automated Backup Script

Create a backup script for regular backups:

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/path/to/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CONTAINER="whatslang-bot-service"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
docker exec "$CONTAINER" sqlite3 /data/messages.db .dump | \
  gzip > "$BACKUP_DIR/messages_$TIMESTAMP.sql.gz"

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "messages_*.sql.gz" -mtime +30 -delete

echo "Backup completed: messages_$TIMESTAMP.sql.gz"
```

Add to crontab for daily backups:
```bash
0 2 * * * /path/to/backup.sh
```

## Migration Between Environments

### From Local to Production

```bash
# 1. Create backup from local
cp ./data/messages.db ./migration-backup.db

# 2. Transfer to production server
scp ./migration-backup.db user@server:/var/lib/dokploy/volumes/whatslang/data/messages.db

# 3. Set proper permissions
ssh user@server "chown 1000:1000 /var/lib/dokploy/volumes/whatslang/data/messages.db"

# 4. Restart the service in Dokploy
```

### From One Deployment to Another

```bash
# 1. Backup from source deployment
docker exec whatslang-bot-service sqlite3 /data/messages.db .dump > migration.sql

# 2. On new deployment, restore before first start
cat migration.sql | docker exec -i new-whatslang-container sqlite3 /data/messages.db
```

## Database Schema

The SQLite database contains three main tables:

1. **processed_messages** - Tracks messages processed by each bot
2. **chats** - Stores chat information (JID, name, sync status)
3. **bot_chat_assignments** - Maps which bots are enabled for which chats

For schema details, see `core/database.py`.

## Monitoring Disk Usage

Monitor the data directory size:

```bash
# Check size
docker exec whatslang-bot-service du -sh /data

# Check database size specifically
docker exec whatslang-bot-service ls -lh /data/messages.db
```

## Troubleshooting

### Database Locked

If you see "database is locked" errors:

```bash
# Check for processes holding locks
docker exec whatslang-bot-service fuser /data/messages.db

# Restart the service
docker-compose restart
```

### Permissions Issues

Ensure the `/data` directory is writable by the container user (UID 1000):

```bash
# On host (if using bind mount)
sudo chown -R 1000:1000 /var/lib/dokploy/volumes/whatslang/data

# Check permissions in container
docker exec whatslang-bot-service ls -la /data
```

### Missing Data After Deployment

1. Check if volume is properly mounted:
   ```bash
   docker inspect whatslang-bot-service | grep -A 10 Mounts
   ```

2. Verify data exists in volume:
   ```bash
   docker exec whatslang-bot-service ls -la /data
   ```

3. Check application logs:
   ```bash
   docker logs whatslang-bot-service | grep -i database
   ```

## Best Practices

1. **Regular Backups**: Set up automated daily backups
2. **Monitor Size**: Keep track of database growth
3. **Test Restores**: Periodically test your backup restoration process
4. **Document Paths**: Keep track of where your production data is mounted
5. **Version Control**: Never commit actual database files to git
6. **Access Control**: Restrict access to the data directory on production servers

## Security Considerations

- The database may contain message history and user data
- Ensure the host directory (for bind mounts) has restricted permissions (700 or 750)
- Use encrypted backups if storing sensitive data
- Implement retention policies to comply with data protection regulations
- Consider encrypting the SQLite database if handling sensitive information

## Future Enhancements

Potential improvements to the persistence layer:

- [ ] Support for PostgreSQL as an alternative to SQLite
- [ ] Automated backup to cloud storage (S3, Google Cloud Storage)
- [ ] Database migration system for schema updates
- [ ] Built-in backup/restore API endpoints
- [ ] Metrics and monitoring for database health

