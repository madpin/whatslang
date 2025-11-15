# WhatSlang Development Guide

Complete guide for local development, testing, and contributing to WhatSlang.

## Table of Contents

- [Quick Start](#quick-start)
- [Local Development Setup](#local-development-setup)
- [Frontend Development](#frontend-development)
- [Backend Development](#backend-development)
- [Database Management](#database-management)
- [Creating Custom Bots](#creating-custom-bots)
- [Testing](#testing)
- [Code Style & Linting](#code-style--linting)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- **Python 3.11 or 3.12** (recommended)
- **Node.js 18+** and npm (for frontend)
- **Docker & Docker Compose** (optional, for full stack)
- **WhatsApp API instance** (go-whatsapp-web-multidevice)
- **OpenAI API key** or compatible LLM endpoint

### Fastest Way to Start

**Option 1: Local with SQLite (No Docker, No PostgreSQL)**

```bash
# 1. Set required environment variables
export WHATSAPP_BASE_URL=https://your-whatsapp-api.example.com
export OPENAI_API_KEY=sk-your-api-key-here

# 2. Run the start script
./start-local.sh
```

That's it! The script will:
- Detect and use Python 3.11/3.12
- Create virtual environment
- Install dependencies
- Initialize SQLite database
- Start the backend server

**Option 2: Docker (Full Stack)**

```bash
# 1. Create .env file
cp .env.example .env
# Edit .env with your credentials

# 2. Start all services
docker-compose up -d

# 3. Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## Local Development Setup

### Backend Setup (Python)

#### Step 1: Python Environment

```bash
cd backend

# Create virtual environment with Python 3.11 or 3.12
python3.11 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate     # On Windows
```

#### Step 2: Install Dependencies

**For SQLite (Local Development):**
```bash
pip install -r requirements-local.txt
```

**For PostgreSQL (Production-like):**
```bash
pip install -r requirements.txt
```

See `backend/REQUIREMENTS.md` for details on the difference.

#### Step 3: Configure Environment

Create `backend/.env`:

```bash
# Minimal configuration for local development
DATABASE_URL=sqlite+aiosqlite:///./whatslang.db
WHATSAPP_BASE_URL=https://your-whatsapp-api.example.com
OPENAI_API_KEY=sk-your-api-key-here

# Optional
WHATSAPP_API_USER=your_username
WHATSAPP_API_PASSWORD=your_password
OPENAI_BASE_URL=https://your-litellm-endpoint.com
OPENAI_MODEL=gpt-4o-mini
LOG_LEVEL=DEBUG
```

Or use the comprehensive `.env.example` as a template:

```bash
cp .env.example backend/.env
# Edit backend/.env with your values
```

#### Step 4: Initialize Database

```bash
# Run migrations
python run_migrations.py
```

This creates the SQLite database and all required tables.

#### Step 5: Start Backend

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the convenience script
cd ..  # Back to project root
./start-local.sh
```

Access:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

### Frontend Setup (React + TypeScript)

#### Step 1: Install Dependencies

```bash
cd frontend
npm install
```

#### Step 2: Configure Environment (Optional)

Create `frontend/.env`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

This is optional - the default Vite proxy configuration already points to `http://localhost:8000`.

#### Step 3: Start Development Server

```bash
npm run dev
```

Access: http://localhost:5173

The frontend will automatically proxy API requests to the backend at `http://localhost:8000`.

#### Frontend Development Features

- **Hot Module Replacement (HMR)**: Changes reflect instantly
- **TypeScript**: Full type checking
- **ESLint**: Code linting
- **Vite**: Fast build and dev server

---

## Frontend Development

### Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── ui/          # shadcn/ui components
│   │   ├── layout/      # Layout components
│   │   └── chats/       # Feature-specific components
│   ├── pages/           # Page components (routes)
│   ├── hooks/           # Custom React hooks
│   ├── services/        # API client
│   ├── types/           # TypeScript type definitions
│   ├── lib/             # Utilities
│   ├── App.tsx          # Main app component
│   └── main.tsx         # Entry point
├── public/              # Static assets
└── package.json
```

### Adding a New Page

1. Create page component in `src/pages/`:

```typescript
// src/pages/MyNewPage.tsx
export default function MyNewPage() {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold">My New Page</h1>
    </div>
  );
}
```

2. Add route in `src/App.tsx`:

```typescript
import MyNewPage from './pages/MyNewPage';

// In the Routes section:
<Route path="/my-new-page" element={<MyNewPage />} />
```

3. Add navigation link in `src/components/layout/Sidebar.tsx`

### Using API Hooks

All API operations have custom hooks:

```typescript
import { useBots, useChats, useMessages, useSchedules } from '@/hooks';

function MyComponent() {
  const { data: bots, isLoading, error } = useBots();
  
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return <div>{/* Use bots data */}</div>;
}
```

### Building for Production

```bash
npm run build
```

Output will be in `frontend/dist/` directory.

---

## Backend Development

### Project Structure

```
backend/
├── app/
│   ├── api/              # API route handlers
│   │   ├── bots.py
│   │   ├── chats.py
│   │   ├── messages.py
│   │   └── schedules.py
│   ├── bots/             # Bot implementations
│   │   ├── base.py       # Base bot class
│   │   └── translation.py
│   ├── core/             # Core business logic
│   │   ├── bot_manager.py
│   │   ├── message_processor.py
│   │   └── scheduler.py
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # External services
│   │   ├── llm.py
│   │   └── whatsapp_client.py
│   ├── config.py         # Configuration
│   ├── database.py       # Database setup
│   └── main.py           # FastAPI app
├── alembic/              # Database migrations
├── requirements.txt      # Full dependencies
├── requirements-local.txt # SQLite-only dependencies
└── run_migrations.py     # Migration runner
```

### Adding a New API Endpoint

1. Add route handler in appropriate file (e.g., `app/api/bots.py`):

```python
@router.get("/bots/my-endpoint")
async def my_endpoint(db: AsyncSession = Depends(get_db)):
    # Your logic here
    return {"message": "Hello"}
```

2. The route is automatically included via `app/main.py`

### Running with Auto-Reload

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Changes to Python files will automatically restart the server.

### Debugging

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload
```

Or set in `.env`:
```bash
LOG_LEVEL=DEBUG
DEBUG=true
```

---

## Database Management

### Using SQLite (Development)

SQLite is perfect for local development:

```bash
# Database URL
DATABASE_URL=sqlite+aiosqlite:///./whatslang.db

# Database file will be created at: backend/whatslang.db
```

**Advantages:**
- No installation required
- Fast and simple
- Easy to reset (just delete the file)

**View/Edit Database:**

```bash
# Install sqlite3 (usually pre-installed)
sqlite3 backend/whatslang.db

# List tables
.tables

# Query data
SELECT * FROM bots;

# Exit
.quit
```

### Using PostgreSQL (Production-like)

For testing with PostgreSQL locally:

#### Option 1: Docker Container

```bash
docker run -d \
  --name whatslang-postgres \
  -e POSTGRES_USER=whatslang \
  -e POSTGRES_PASSWORD=whatslang \
  -e POSTGRES_DB=whatslang \
  -p 5432:5432 \
  postgres:15-alpine
```

#### Option 2: Local PostgreSQL Installation

```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian
sudo apt-get install postgresql-15
sudo systemctl start postgresql

# Create database
createdb whatslang
```

#### Configure Backend

```bash
# In backend/.env
DATABASE_URL=postgresql://whatslang:whatslang@localhost:5432/whatslang
```

### Database Migrations

#### Create a New Migration

```bash
cd backend

# Generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Review the generated migration in alembic/versions/
```

#### Apply Migrations

```bash
# Using the migration script (recommended)
python run_migrations.py

# Or using alembic directly
alembic upgrade head
```

#### Rollback Migration

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>
```

#### Reset Database

```bash
# SQLite - just delete the file
rm backend/whatslang.db
python run_migrations.py

# PostgreSQL - drop and recreate
dropdb whatslang
createdb whatslang
python run_migrations.py
```

---

## Creating Custom Bots

### Step 1: Create Bot Class

Create a new file in `backend/app/bots/`:

```python
# backend/app/bots/my_custom_bot.py

from typing import Optional
from app.bots.base import BaseBot
from app.schemas.message import Message, Response
from app.schemas.bot import BotInfo

class MyCustomBot(BaseBot):
    """My custom bot that does something cool"""
    
    def get_bot_info(self) -> BotInfo:
        """Return bot metadata and configuration schema"""
        return BotInfo(
            type="my_custom",
            name="My Custom Bot",
            description="Does something cool with messages",
            config_schema={
                "trigger_word": {
                    "type": "string",
                    "description": "Word that triggers the bot",
                    "default": "!custom"
                },
                "response_prefix": {
                    "type": "string",
                    "description": "Prefix for bot responses",
                    "default": "[bot]"
                }
            }
        )
    
    async def process_message(self, message: Message) -> Optional[Response]:
        """Process incoming message and optionally return a response"""
        
        # Get configuration
        trigger = self.config.get("trigger_word", "!custom")
        prefix = self.config.get("response_prefix", "[bot]")
        
        # Check if message should be processed
        if not message.content.startswith(trigger):
            return None  # Ignore this message
        
        # Your custom logic here
        user_text = message.content[len(trigger):].strip()
        result = f"You said: {user_text}"
        
        # Return response
        return Response(
            content=f"{prefix} {result}",
            reply_to=message.id  # Optional: reply to original message
        )
```

### Step 2: Register Bot

Add your bot to `backend/app/bots/__init__.py`:

```python
from .my_custom_bot import MyCustomBot

AVAILABLE_BOTS = {
    "translation": TranslationBot,
    "my_custom": MyCustomBot,  # Add your bot here
}
```

### Step 3: Test Your Bot

1. Restart the backend server
2. Create a bot instance via API:

```bash
curl -X POST http://localhost:8000/api/bots \
  -H "Content-Type: application/json" \
  -d '{
    "type": "my_custom",
    "name": "My Test Bot",
    "config": {
      "trigger_word": "!test",
      "response_prefix": "[🤖]"
    }
  }'
```

3. Assign to a chat and test!

### Bot Development Tips

- **Use async/await**: All bot methods should be async
- **Handle errors gracefully**: Wrap in try/except
- **Return None**: If the bot shouldn't respond to a message
- **Use self.llm_service**: For AI operations
- **Use self.whatsapp_client**: For WhatsApp operations
- **Log important events**: Use `logger.info()`, `logger.error()`

---

## Testing

### Manual Testing

1. **Start the backend**:
```bash
./start-local.sh
```

2. **Use the API docs**: http://localhost:8000/docs
   - Interactive testing of all endpoints
   - Try creating bots, chats, schedules

3. **Use curl**:
```bash
# Health check
curl http://localhost:8000/health

# List bots
curl http://localhost:8000/api/bots

# Create bot
curl -X POST http://localhost:8000/api/bots \
  -H "Content-Type: application/json" \
  -d '{"type":"translation","name":"Test Bot","config":{}}'
```

4. **Use the frontend**: http://localhost:5173
   - Test all UI interactions
   - Verify real-time updates

### Testing with WhatsApp

1. Ensure your WhatsApp API is running and accessible
2. Register a test chat (use a personal chat or test group)
3. Create and assign a bot
4. Send messages in WhatsApp
5. Monitor backend logs to see processing

### Database Testing

```bash
# Check database contents
sqlite3 backend/whatslang.db "SELECT * FROM bots;"
sqlite3 backend/whatslang.db "SELECT * FROM chats;"
sqlite3 backend/whatslang.db "SELECT * FROM messages;"
```

---

## Code Style & Linting

### Python (Backend)

**Style Guide**: PEP 8

**Recommended tools**:

```bash
# Install dev dependencies
pip install black flake8 mypy

# Format code
black backend/app

# Lint
flake8 backend/app

# Type checking
mypy backend/app
```

### TypeScript (Frontend)

**Style Guide**: Standard TypeScript + ESLint

```bash
# Lint
npm run lint

# Auto-fix
npm run lint -- --fix
```

### Commit Messages

Use conventional commits:

```
feat: Add new bot type for image processing
fix: Resolve database connection timeout
docs: Update deployment guide
refactor: Simplify message processor logic
test: Add tests for translation bot
```

---

## Troubleshooting

### Backend Issues

**Import errors after adding dependencies:**
```bash
# Reinstall dependencies
pip install -r requirements-local.txt
```

**Database locked (SQLite):**
```bash
# Close all connections and restart
rm backend/whatslang.db-*
python run_migrations.py
```

**Port 8000 already in use:**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --reload --port 8001
```

### Frontend Issues

**Module not found errors:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Build errors:**
```bash
# Clear Vite cache
rm -rf frontend/dist frontend/.vite
npm run build
```

**API requests failing:**
- Check backend is running: `curl http://localhost:8000/health`
- Check proxy configuration in `vite.config.ts`
- Check browser console for CORS errors

### Python Version Issues

**Using Python 3.14+ (too new):**

```bash
# Install Python 3.11 or 3.12
# macOS
brew install python@3.11

# Ubuntu
sudo apt-get install python3.11

# Recreate virtual environment
rm -rf backend/.venv
python3.11 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r requirements-local.txt
```

### General Tips

1. **Check logs**: Most issues are visible in logs
2. **Restart services**: Often fixes transient issues
3. **Clear caches**: Python `__pycache__`, Node `node_modules`
4. **Check environment variables**: Use `env | grep VAR_NAME`
5. **Verify network connectivity**: Test API endpoints with curl

---

## Additional Resources

- **Main README**: `../README.md`
- **Deployment Guide**: `DEPLOYMENT.md`
- **Frontend Implementation**: `FRONTEND_IMPLEMENTATION.md`
- **Quick Start Frontend**: `QUICK_START_FRONTEND.md`
- **Requirements Guide**: `../backend/REQUIREMENTS.md`

---

## Getting Help

- Check the documentation
- Review logs for error messages
- Search existing GitHub issues
- Open a new issue with:
  - Steps to reproduce
  - Expected vs actual behavior
  - Relevant logs
  - Environment details (OS, Python version, etc.)

Happy coding! 🚀

