#!/usr/bin/env python3
"""Check database state and suggest migration strategy"""

import asyncio
import sys
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings


async def check_database_state():
    """Check what tables and columns exist in the database"""
    
    print("=" * 70)
    print("Database State Checker")
    print("=" * 70)
    print(f"\nDatabase URL: {settings.database_url}")
    print()
    
    # Create async engine
    engine = create_async_engine(settings.database_url, echo=False)
    
    try:
        async with engine.begin() as conn:
            # Get database dialect
            def check_tables(connection):
                inspector = inspect(connection)
                return inspector.get_table_names()
            
            tables = await conn.run_sync(check_tables)
            
            print(f"Found {len(tables)} tables:")
            for table in sorted(tables):
                print(f"  ✓ {table}")
            
            print()
            
            # Check if alembic_version table exists
            if 'alembic_version' in tables:
                result = await conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.scalar()
                print(f"Alembic version: {version if version else 'NOT SET'}")
            else:
                print("⚠️  Alembic version table does NOT exist")
            
            print()
            
            # Check for specific tables
            required_tables = ['bots', 'chats', 'chat_bots', 'processed_messages', 'scheduled_messages']
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                print(f"❌ Missing tables: {', '.join(missing_tables)}")
            else:
                print("✓ All required tables exist")
            
            # If chats table exists, check for last_message_at column
            if 'chats' in tables:
                def check_columns(connection):
                    inspector = inspect(connection)
                    return [col['name'] for col in inspector.get_columns('chats')]
                
                columns = await conn.run_sync(check_columns)
                print(f"\nChats table columns ({len(columns)}):")
                for col in columns:
                    print(f"  - {col}")
                
                if 'last_message_at' in columns:
                    print("\n✓ last_message_at column EXISTS")
                else:
                    print("\n❌ last_message_at column MISSING")
            
            print()
            print("=" * 70)
            print("Recommendation:")
            print("=" * 70)
            
            if 'alembic_version' not in tables:
                if len(tables) == 0:
                    print("✓ Empty database - run migrations normally")
                    print("  Command: python run_migrations.py")
                elif len(missing_tables) == 0:
                    print("⚠️  Database has all tables but no Alembic version")
                    print("  Strategy: Stamp database then run pending migrations")
                    print("  Commands:")
                    print("    1. alembic stamp 0001")
                    print("    2. python run_migrations.py")
                else:
                    print("⚠️  Partial database - need manual intervention")
                    print(f"  Missing: {', '.join(missing_tables)}")
            else:
                result = await conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.scalar()
                if version:
                    print(f"✓ Database at version {version} - run migrations to update")
                    print("  Command: python run_migrations.py")
                else:
                    print("⚠️  Alembic version not set - stamp and migrate")
                    print("  Commands:")
                    print("    1. alembic stamp 0001")
                    print("    2. python run_migrations.py")
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_database_state())

