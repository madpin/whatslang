#!/bin/bash
set -e

echo "🚀 Starting WhatSlang Backend..."

echo "📦 Running database migrations..."
python run_migrations.py

echo "👤 Initializing default admin user (if needed)..."
python init_default_user.py

echo "✅ Migrations and initialization complete!"
echo "🌐 Starting FastAPI application..."

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
