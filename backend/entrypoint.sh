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

