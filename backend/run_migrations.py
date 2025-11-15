#!/usr/bin/env python3
"""Script to run database migrations"""

import asyncio
import sys
from alembic.config import Config
from alembic import command

from app.database import init_db


async def main():
    """Run migrations"""
    print("Running database migrations...")
    
    # Initialize database (create tables if not exist)
    await init_db()
    
    print("Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(main())

