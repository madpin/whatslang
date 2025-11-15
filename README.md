# WhatSlang

A modular WhatsApp bot platform that enables multiple AI-powered bots to interact with WhatsApp users and groups.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Docker Build](https://github.com/madpin/whatslang/actions/workflows/docker-build.yml/badge.svg)

## ✨ Features

- **🤖 Multi-bot Support**: Deploy multiple specialized bots (translation, custom logic, etc.)
- **💬 Easy Bot Assignment**: Attach/detach bots to chats with priority ordering
- **⏰ Message Scheduling**: Schedule one-time or recurring messages with cron support
- **🔌 Extensible Framework**: Create custom bots by implementing simple Python classes
- **🎨 Beautiful Web UI**: Modern React frontend for managing bots, chats, and schedules
- **📡 RESTful API**: Full-featured API with interactive documentation
- **🐳 Docker Ready**: Production-ready with Docker Compose
- **☁️ Dokploy Compatible**: Deploy easily to Dokploy or any Docker platform

## 🏗️ Architecture

**Backend:**
- FastAPI (async) + PostgreSQL/SQLite
- SQLAlchemy 2.0 ORM + Alembic migrations
- APScheduler for message scheduling
- OpenAI/LiteLLM integration
- go-whatsapp-web-multidevice API client

**Frontend:**
- React 18 + TypeScript + Vite
- Tailwind CSS + shadcn/ui components
- TanStack Query for real-time data
- Responsive design with mobile support

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (for production)
- **Python 3.11 or 3.12** (for local development)
- **Node.js 18+** (for frontend development)
- **WhatsApp API** instance ([go-whatsapp-web-multidevice](https://github.com/aldinokemal/go-whatsapp-web-multidevice))
- **OpenAI API key** or compatible LLM endpoint

### Option 1: Docker (Recommended)

```bash
# 1. Clone the repository
git clone <your-repo-url>
   cd whatslang

# 2. Configure environment
   cp .env.example .env
nano .env  # Add your credentials

# 3. Start all services
./start.sh
# Or manually: docker-compose up -d

# 4. Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development (SQLite)

```bash
# 1. Set required environment variables
export WHATSAPP_BASE_URL=https://your-whatsapp-api.example.com
export OPENAI_API_KEY=sk-your-api-key-here

# 2. Run the start script
./start-local.sh

# Backend will start at: http://localhost:8000
```

## 📖 Documentation

### Getting Started
- **[Dokploy Deployment Guide](docs/DOKPLOY_DEPLOYMENT.md)** - ⭐ Deploy to Dokploy in 5 minutes
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Deploy to Docker or production
- **[Development Guide](docs/DEVELOPMENT.md)** - Local development setup and contributing
- **[Deployment Checklist](DEPLOYMENT_CHECKLIST.md)** - Pre-deployment verification steps
- **[CI/CD Pipeline](docs/CI_CD.md)** - Automated builds and container registry

### Frontend
- **[Frontend Implementation](docs/FRONTEND_IMPLEMENTATION.md)** - Detailed frontend architecture
- **[Quick Start Frontend](docs/QUICK_START_FRONTEND.md)** - Get the UI running in 5 minutes

### Backend
- **[Requirements Guide](backend/REQUIREMENTS.md)** - Understanding Python dependencies

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required
WHATSAPP_BASE_URL=https://your-whatsapp-api.example.com
OPENAI_API_KEY=sk-your-api-key-here
DB_PASSWORD=your_secure_password

# Optional
WHATSAPP_API_USER=username
WHATSAPP_API_PASSWORD=password
OPENAI_BASE_URL=https://custom-llm-endpoint.com
OPENAI_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
```

See `.env.example` for all available options.

## 🎯 Your First Bot

### 1. Start the Application

```bash
docker-compose up -d
# Or: ./start-local.sh
```

### 2. Create a Translation Bot

```bash
curl -X POST http://localhost:8000/api/bots \
  -H "Content-Type: application/json" \
  -d '{
    "type": "translation",
    "name": "My Translation Bot",
    "description": "Translates between English and Portuguese",
    "config": {
      "prefix": "[ai]",
      "source_languages": ["en", "pt"],
      "translate_images": true
    }
  }'
```

### 3. Register Your WhatsApp Chat

```bash
curl -X POST http://localhost:8000/api/chats \
  -H "Content-Type: application/json" \
  -d '{
    "jid": "120363419538094902@g.us",
    "name": "My Group Chat",
    "chat_type": "group"
  }'
```

### 4. Assign Bot to Chat

Use the Web UI at http://localhost:3000 or via API:

```bash
curl -X POST http://localhost:8000/api/chats/{chat_id}/bots \
  -H "Content-Type: application/json" \
  -d '{
    "bot_id": "{bot_id}",
    "priority": 1,
    "enabled": true
  }'
```

### 5. Test It! 🎉

Send a message in your WhatsApp chat:

```
You: Hello, how are you today?
Bot: [ai] Olá, como você está hoje?
```

## 🌐 Web Interface

Access the beautiful web interface at **http://localhost:3000**

**Features:**
- 📊 Dashboard with stats and quick actions
- 🤖 Bot management with dynamic configuration forms
- 💬 Chat management and bot assignment
- ⏰ Schedule messages (one-time or recurring)
- 📧 Real-time message feed
- 🎨 Modern, responsive UI with dark mode support

## 🔌 API Endpoints

Full API documentation available at: **http://localhost:8000/docs**

**Key endpoints:**
- `GET /health` - Health check
- `GET /api/bots` - List all bots
- `POST /api/bots` - Create a bot
- `GET /api/chats` - List all chats
- `POST /api/chats/{id}/bots` - Assign bot to chat
- `GET /api/messages` - List processed messages
- `POST /api/schedules` - Create scheduled message

## 🛠️ Creating Custom Bots

```python
# backend/app/bots/my_bot.py

from app.bots.base import BaseBot
from app.schemas.message import Message, Response
from app.schemas.bot import BotInfo

class MyCustomBot(BaseBot):
    """My custom bot implementation"""
    
    def get_bot_info(self) -> BotInfo:
        return BotInfo(
            type="my_custom",
            name="My Custom Bot",
            description="Does something cool",
            config_schema={
                "trigger_word": {
                    "type": "string",
                    "default": "!custom"
                }
            }
        )
    
    async def process_message(self, message: Message) -> Optional[Response]:
        trigger = self.config.get("trigger_word", "!custom")
        
        if not message.content.startswith(trigger):
            return None
        
        # Your custom logic here
        result = "Custom response"
        
        return Response(
            content=result,
            reply_to=message.id
        )
```

Register in `backend/app/bots/__init__.py`:

```python
from .my_bot import MyCustomBot

AVAILABLE_BOTS = {
    "translation": TranslationBot,
    "my_custom": MyCustomBot,
}
```

See [Development Guide](docs/DEVELOPMENT.md) for detailed instructions.

## 🚢 Deployment

### Using Pre-built Images (Recommended)

GitHub Actions automatically builds and publishes Docker images on every push:

```bash
# 1. Authenticate with GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin

# 2. Pull and run pre-built images
docker-compose -f docker-compose.registry.yml up -d

# Or use specific version
docker pull ghcr.io/madpin/whatslang/backend:v1.0.0
docker pull ghcr.io/madpin/whatslang/frontend:v1.0.0
```

See [CI/CD Documentation](docs/CI_CD.md) for details on automated builds and image tags.

### Dokploy Deployment (Easiest!)

Deploy using pre-built images from GitHub Container Registry:

1. **Create Compose Application** in Dokploy
2. **Connect Repository**: `madpin/whatslang`
3. **Select Compose File**: `docker-compose.dokploy.yml`
4. **Set Environment Variables**:
   - `DB_PASSWORD` - Secure database password
   - `WHATSAPP_API_URL` - Your WhatsApp API endpoint
   - `WHATSAPP_API_TOKEN` - API token
   - `OPENAI_API_KEY` - OpenAI API key
5. **Deploy!**

Dokploy will automatically:
- ✅ Pull pre-built images from GHCR
- ✅ Start all services (frontend, backend, database)
- ✅ Configure networking and SSL/TLS
- ✅ Provide monitoring and logs

**Deployment time**: ~2-3 minutes

See [Dokploy Deployment Guide](docs/DOKPLOY_DEPLOYMENT.md) for detailed instructions.

### Production Docker Compose

```bash
# Use production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

The production configuration includes:
- No source code volume mounts
- Resource limits
- Optimized restart policies
- Production-ready settings

## 📊 Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Check all containers
docker-compose ps

# View logs
docker-compose logs -f backend
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

## 🔍 Troubleshooting

### Backend Not Starting

1. Check environment variables: `docker-compose exec backend env`
2. Verify database connection: `docker-compose logs postgres`
3. Check WhatsApp API: `curl $WHATSAPP_BASE_URL/health`
4. Review logs: `docker-compose logs backend`

### Frontend Shows "Offline"

1. Check backend health: `curl http://localhost:8000/health`
2. Verify network: `docker-compose ps`
3. Check browser console for errors

### Bot Not Responding

1. Verify bot is enabled: `GET /api/bots/{id}`
2. Check bot is assigned to chat: `GET /api/chats/{id}/bots`
3. Review message processor logs
4. Verify WhatsApp API is receiving messages

See [Deployment Guide](docs/DEPLOYMENT.md) for more troubleshooting tips.

## 🗂️ Project Structure

```
whatslang/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── bots/        # Bot implementations
│   │   ├── core/        # Core business logic
│   │   ├── models/      # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # External services
│   ├── alembic/         # Database migrations
│   └── requirements.txt
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── pages/       # Page components
│   │   ├── hooks/       # Custom hooks
│   │   └── services/    # API client
│   └── package.json
├── docs/                # Documentation
├── docker-compose.yml   # Docker configuration
├── .env.example         # Environment template
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Please see [Development Guide](docs/DEVELOPMENT.md) for:
- Local development setup
- Code style guidelines
- Testing procedures
- Pull request process

## 📝 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Documentation**: See `docs/` directory
- **API Docs**: http://localhost:8000/docs
- **Issues**: Open a GitHub issue
- **Discussions**: GitHub Discussions

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [shadcn/ui](https://ui.shadcn.com/) - Beautiful UI components
- [go-whatsapp-web-multidevice](https://github.com/aldinokemal/go-whatsapp-web-multidevice) - WhatsApp API

---

**Made with ❤️ for the WhatsApp bot community**
