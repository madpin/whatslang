#!/usr/bin/env python3
"""Script to run database migrations"""

import sys
import os
from pathlib import Path
from alembic.config import Config
from alembic import command


def main():
    """Run Alembic migrations"""
    print("Running database migrations...")
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    alembic_ini = script_dir / "alembic.ini"
    
    if not alembic_ini.exists():
        print(f"Error: alembic.ini not found at {alembic_ini}")
        sys.exit(1)
    
    # Create Alembic config
    alembic_cfg = Config(str(alembic_ini))
    
    # Set the script location (where alembic/ directory is)
    alembic_cfg.set_main_option("script_location", str(script_dir / "alembic"))
    
    try:
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        print("✓ Database migrations completed successfully!")
        return 0
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

