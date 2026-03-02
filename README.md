# WhatsApp Bot Service

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready, modular WhatsApp bot service with a web dashboard for managing multiple concurrent bots. Built with FastAPI and designed for easy deployment with Docker and Nixpacks (dokploy).

---

## 📖 New to the Project?

👉 **[Start with the Documentation Hub](docs/README.md)** 👈

The hub provides structured learning paths from beginner to advanced, with guides for:
- 🚀 Getting started (15 min)
- 🤖 Creating custom bots (30 min)  
- 🔐 Adding security (15 min)
- ☁️ Production deployment (45 min)

---

## ✨ Features

- 🤖 **Multiple Bots**: Run multiple bots simultaneously on the same WhatsApp chat
- 📊 **Web Dashboard**: Beautiful UI for starting, stopping, and monitoring bots
- 📝 **Real-time Logs**: Live log streaming for each bot
- 🔧 **Modular Architecture**: Easy to create and add new bots
- 🐳 **Docker Ready**: Production-ready Docker configuration
- ☁️ **Cloud Native**: Deploy to dokploy, Kubernetes, or any container platform
- 🔒 **Secure**: Environment-based configuration, no hardcoded secrets
- 📈 **Production Features**: Health checks, structured logging, graceful shutdown

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- WhatsApp API endpoint (e.g., [go-whatsapp-web-multidevice](https://github.com/aldinokemal/go-whatsapp-web-multidevice))
- OpenAI API key or LiteLLM endpoint

### Local Development

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/whatslang.git
cd whatslang
```

2. **Set up virtual environment**

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate     # On Windows

# Or use the Makefile
make venv                  # Creates .venv
source .venv/bin/activate  # Then activate it
```

3. **Install dependencies**

```bash
# Install production dependencies
pip install -r requirements.txt

# Or use the Makefile (requires active venv)
make install               # Checks for venv first

# For development (includes testing/linting tools)
make install-dev
```

4. **Configure environment variables**

```bash
cp env.example .env
# Edit .env with your actual credentials
```

5. **Run the service**

```bash
python run.py
```

6. **Access the dashboard**

Open http://localhost:8000/static/index.html in your browser

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

1. **Create .env file** with your configuration:

```bash
cp env.example .env
# Edit .env with your credentials
```

2. **Start the service**:

```bash
docker-compose up -d
```

3. **View logs**:

```bash
docker-compose logs -f
```

4. **Stop the service**:

```bash
docker-compose down
```

### Using Docker directly

```bash
# Build the image
docker build -t whatslang:latest .

# Run the container
docker run -d \
  --name whatslang \
  -p 8000:8000 \
  -e WHATSAPP_BASE_URL=your-url \
  -e WHATSAPP_API_USER=your-user \
  -e WHATSAPP_API_PASSWORD=your-password \
  -e CHAT_JID=your-chat-jid \
  -e OPENAI_API_KEY=your-key \
  -v whatslang-data:/data \
  whatslang:latest
```

## ☁️ Dokploy Deployment (Nixpacks)

Dokploy automatically detects and uses the `nixpacks.toml` configuration.

### Deployment Steps

1. **Create a new application** in Dokploy

2. **Connect your Git repository**

3. **Set environment variables** in Dokploy dashboard:
   - `WHATSAPP_BASE_URL`
   - `WHATSAPP_API_USER`
   - `WHATSAPP_API_PASSWORD`
   - `CHAT_JID`
   - `OPENAI_API_KEY`
   - `OPENAI_BASE_URL` (optional)
   - `OPENAI_MODEL` (optional)
   - `ENVIRONMENT=production`

4. **Add persistent storage** (recommended):
   - Mount path: `/data`
   - This persists the message database

5. **Deploy** - Dokploy will:
   - Detect Nixpacks configuration
   - Build using Python 3.11
   - Install dependencies
   - Start the service on port 8000

6. **Configure health checks**:
   - Liveness: `GET /health`
   - Readiness: `GET /ready`

## 💾 Data Persistence

All persistent data is stored in the `/data` directory (inside containers) or `./data/` (local development).

### What is Persisted?

- **Database** (`messages.db`) - Chat history, bot assignments, processed messages
- **Future assets** - Logs, cached data, uploads, etc.

### Dokploy Volume Setup

In Dokploy's volume configuration:
- **Container Path**: `/data`
- **Host Path**: `/var/lib/dokploy/volumes/whatslang/data` (or your preferred location)
- **Mode**: `rw` (read-write)

This ensures your data survives redeployments, updates, and container restarts.

### Backup & Restore

```bash
# Backup
docker exec whatslang-bot-service sqlite3 /data/messages.db .dump > backup.sql

# Restore
cat backup.sql | docker exec -i whatslang-bot-service sqlite3 /data/messages.db
```

**📖 For detailed persistence documentation**, see [PERSISTENCE.md](docs/PERSISTENCE.md)

## 📋 Architecture

```
whatslang/
├── api/                    # FastAPI backend
│   ├── main.py            # Main application with health checks
│   ├── bot_manager.py     # Bot lifecycle management
│   └── models.py          # API data models
├── bots/                  # Bot implementations
│   ├── translation_bot.py # Portuguese ↔ English translation
│   └── joke_bot.py        # Joke generator bot
├── core/                  # Shared infrastructure
│   ├── bot_base.py        # Base class for all bots
│   ├── whatsapp_client.py # WhatsApp API wrapper
│   ├── database.py        # SQLite message tracking
│   └── llm_service.py     # LLM API wrapper
├── data/                  # Persistent data (gitignored)
│   └── messages.db        # SQLite database
├── docs/                  # Documentation
│   ├── README.md          # Documentation index
│   ├── QUICKSTART.md      # Quick start guide
│   ├── DEPLOYMENT.md      # Deployment guide
│   ├── PERSISTENCE.md     # Data persistence guide
│   └── dev-notes/         # Development notes
├── frontend/              # Web dashboard
│   ├── index.html         # Dashboard UI
│   ├── app.js            # Frontend logic
│   └── styles.css        # Styling
├── Dockerfile            # Multi-stage Docker build
├── docker-compose.yml    # Docker Compose configuration
├── nixpacks.toml         # Nixpacks/Dokploy configuration
├── pyproject.toml        # Python project metadata
├── requirements.txt      # Python dependencies
├── env.example          # Environment variables template
└── run.py               # Simple run script
```

## 🤖 Available Bots

### Translation Bot
- **Prefix**: `[ai]`
- **Function**: Translates messages between Portuguese and English
- Auto-detects source language
- Responds only to non-bot messages

### Joke Bot
- **Prefix**: `[joke]`
- **Function**: Responds with family-friendly jokes
- Generates contextual humor
- Responds only to non-bot messages

## 🛠️ Creating Custom Bots

Create a new file in `bots/` directory (e.g., `my_bot.py`):

```python
from typing import Dict, Any, Optional
from core.bot_base import BotBase

class MyBot(BotBase):
    """Description of what your bot does."""
    
    NAME = "my_bot"         # Unique identifier
    PREFIX = "[mybot]"       # Prefix for bot messages
    
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Process a message and return a response.
        
        Args:
            message: Message dict from WhatsApp API
        
        Returns:
            Response text, or None to skip
        """
        msg_text = message.get("content", "")
        
        # Your bot logic here
        prompt = "Your LLM prompt here"
        response = self.llm.call(prompt, msg_text)
        
        return response
```

Restart the service - your bot will automatically appear in the dashboard!

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WHATSAPP_BASE_URL` | Yes | - | WhatsApp API endpoint URL |
| `WHATSAPP_API_USER` | Yes | - | WhatsApp API username |
| `WHATSAPP_API_PASSWORD` | Yes | - | WhatsApp API password |
| `CHAT_JID` | Yes | - | WhatsApp chat/group JID |
| `OPENAI_API_KEY` | Yes | - | OpenAI or LiteLLM API key |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | LLM API endpoint |
| `OPENAI_MODEL` | No | `gpt-4` | LLM model name |
| `POLL_INTERVAL` | No | `5` | Message polling interval (seconds) |
| `DB_PATH` | No | `data/messages.db` | SQLite database path |
| `HOST` | No | `0.0.0.0` | Server host |
| `PORT` | No | `8000` | Server port |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `ENVIRONMENT` | No | `development` | Environment (development/production) |

### Legacy config.yaml Support

For backward compatibility, you can still use `config.yaml`. Environment variables take precedence.

## 📊 API Endpoints

### Health & Status

- `GET /` - API information
- `GET /health` - Liveness probe (container health)
- `GET /ready` - Readiness probe (service ready to accept requests)

### Bot Management

- `GET /bots` - List all bots with status
- `GET /bots/{bot_name}/status` - Get specific bot status
- `POST /bots/{bot_name}/start` - Start a bot
- `POST /bots/{bot_name}/stop` - Stop a bot
- `GET /bots/{bot_name}/logs` - Get bot logs (limit parameter supported)

### Documentation

- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

*Note: API docs are disabled in production mode for security*

## 📈 Production Features

### Health Checks

- **Liveness**: `/health` - Returns 200 if service is running
- **Readiness**: `/ready` - Returns 200 if service is ready to handle requests

Configure in Kubernetes/Dokploy:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Structured Logging

- **Development**: Human-readable formatted logs
- **Production**: JSON structured logs for log aggregation (ELK, Datadog, etc.)

### Graceful Shutdown

- Automatically stops all running bots on shutdown
- Handles SIGTERM signals properly
- Safe for container orchestration

### Security

- Non-root user in Docker container
- No hardcoded secrets
- Environment-based configuration
- CORS configurable via `ALLOWED_ORIGINS`

## 🔍 Monitoring

### Built-in Metrics

The `/ready` endpoint provides service metrics:

```json
{
  "status": "ready",
  "services": {
    "whatsapp": "connected",
    "llm": "connected",
    "database": "connected",
    "bot_manager": "initialized"
  },
  "bots": {
    "available": 2,
    "running": 1
  }
}
```

### Logs

Access logs via:

```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f whatslang

# Dokploy
Check the logs tab in Dokploy dashboard
```

## 🐛 Troubleshooting

### Bots not responding?

1. Check logs in the dashboard or container logs
2. Verify WhatsApp API credentials
3. Ensure `CHAT_JID` is correct
4. Check that messages don't start with `[*]` (reserved for bot messages)

### LLM errors?

1. Verify `OPENAI_API_KEY` is valid
2. Check `OPENAI_BASE_URL` is accessible
3. Ensure `OPENAI_MODEL` name is correct
4. Review error messages in logs

### Frontend not loading?

1. Ensure service is running: `curl http://localhost:8000/health`
2. Check browser console for errors
3. Verify `/bots` endpoint returns JSON: `curl http://localhost:8000/bots`

### Database errors?

1. Ensure `/data` directory is writable
2. Check persistent volume is mounted (Docker/Kubernetes)
3. Verify `DB_PATH` is accessible

## 🧪 Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# With coverage
pytest --cov
```

### Code Formatting

```bash
# Format code
black .

# Lint
ruff check .

# Type checking
mypy .
```

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📚 Documentation

### 🎯 Choose Your Path

| I want to... | Read this | Time |
|--------------|-----------|------|
| 🚀 **Get started from scratch** | [Getting Started Guide](docs/GETTING_STARTED.md) | 15 min |
| ⚡ **Quick setup (experienced users)** | [Quick Start](docs/QUICKSTART.md) | 5 min |
| 🤖 **Create custom bots** | [Creating Bots Guide](docs/CREATING_BOTS.md) | 30 min |
| 🔐 **Add password protection** | [Security Guide](docs/SECURITY.md) | 15 min |
| ☁️ **Deploy to production** | [Deployment Guide](docs/DEPLOYMENT.md) | 45 min |
| 💾 **Understand data storage** | [Persistence Guide](docs/PERSISTENCE.md) | 20 min |
| 🐍 **Learn about virtual envs** | [Venv Guide](docs/VENV_GUIDE.md) | 10 min |

### 📖 Complete Documentation Hub

**For the complete documentation with learning paths and detailed guides:**

👉 **[Visit the Documentation Hub](docs/README.md)** 👈

The hub includes:
- 📚 **4 learning paths** (beginner to expert)
- 🎓 **9 comprehensive guides** covering all topics
- 🗺️ **Quick task lookup** for common operations
- 🆘 **Troubleshooting** for each area

### 🤝 Contributing & Community

- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute
- **[Changelog](CHANGELOG.md)** - Version history and changes
- **[License](LICENSE)** - MIT License

### 🔗 External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Dokploy Documentation](https://dokploy.com/docs)
- [go-whatsapp-web-multidevice](https://github.com/aldinokemal/go-whatsapp-web-multidevice)

## 💬 Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions

---

**Made with ❤️ for the WhatsApp automation community**
