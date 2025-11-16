#!/usr/bin/env python3
"""
Simple script to run the WhatsApp Bot Service.

This is a convenience wrapper around uvicorn for local development.
For production, use uvicorn directly or Docker.
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check if required environment variables are set."""
    required_vars = [
        'WHATSAPP_BASE_URL',
        'WHATSAPP_API_USER', 
        'WHATSAPP_API_PASSWORD',
        'CHAT_JID',
        'OPENAI_API_KEY'
    ]
    
    # Try to load .env file
    env_file = Path(__file__).parent / '.env'
    config_file = Path(__file__).parent / 'config.yaml'
    
    if env_file.exists():
        print("✓ Found .env file")
    elif config_file.exists():
        print("✓ Found config.yaml file")
    else:
        print("\n⚠️  WARNING: No .env or config.yaml file found!")
        print("Please create a .env file from env.example:")
        print("  cp env.example .env")
        print("  # Edit .env with your credentials\n")
        
        # Check if env vars are set in shell
        missing = [var for var in required_vars if not os.environ.get(var)]
        if missing:
            print(f"Missing required variables: {', '.join(missing)}")
            print("\nEither:")
            print("  1. Create a .env file, or")
            print("  2. Set environment variables in your shell")
            return False
    
    return True


def main():
    """Run the development server."""
    print("=" * 60)
    print("🤖 WhatsApp Bot Service - v2.0.0")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Get configuration
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8000))
    reload = os.environ.get('DEV_RELOAD', 'false').lower() == 'true'
    
    # Print startup info
    print(f"\n📡 Server: http://{host}:{port}")
    print(f"📊 Dashboard: http://localhost:{port}/static/index.html")
    print(f"📖 API Docs: http://localhost:{port}/docs")
    print(f"🏥 Health: http://localhost:{port}/health")
    
    if reload:
        print("♻️  Auto-reload: ENABLED (development mode)")
    
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    print()
    
    try:
        import uvicorn
        
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=os.environ.get('LOG_LEVEL', 'info').lower()
        )
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("👋 Shutting down gracefully...")
        print("=" * 60)
        sys.exit(0)
    except ImportError:
        print("\n❌ Error: uvicorn not found!")
        print("Please install dependencies:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

