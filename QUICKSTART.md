# ⚡ Quick Start Guide

Get your WhatsApp Bot Service up and running in minutes!

## 🎯 Choose Your Deployment Method

### 🖥️ Local Development (3 Minutes)

Perfect for testing and development.

#### Step 1: Install Dependencies

```bash
# Clone the repository (if not already done)
git clone https://github.com/yourusername/whatslang.git
cd whatslang

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Or use the Makefile
make venv                  # Creates .venv
source .venv/bin/activate  # Then activate it

# Install dependencies (requires active venv)
make install

# Or manually
pip install -r requirements.txt
```

#### Step 2: Configure

Create a `.env` file from the template:

```bash
cp env.example .env
```

Edit `.env` with your credentials:

```bash
# Required settings
WHATSAPP_BASE_URL=https://your-whatsapp-api.com
WHATSAPP_API_USER=your-username
WHATSAPP_API_PASSWORD=your-password
CHAT_JID=your-group-jid@g.us

OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1  # Or your LiteLLM endpoint
OPENAI_MODEL=gpt-4

# Optional settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

#### Step 3: Run

```bash
python run.py
```

Then open: **http://localhost:8000/static/index.html** 🎉

---

### 🐳 Docker Compose (5 Minutes)

Recommended for local testing with production-like setup.

#### Step 1: Configure

```bash
cp env.example .env
# Edit .env with your credentials
```

#### Step 2: Start

```bash
docker-compose up -d
```

#### Step 3: Access

- **Dashboard**: http://localhost:8000/static/index.html
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

#### Manage

```bash
# View logs
docker-compose logs -f

# Stop service
docker-compose down

# Restart
docker-compose restart
```

---

### ☁️ Dokploy Deployment (10 Minutes)

Production-ready cloud deployment.

#### Step 1: Create Application

1. Log into your Dokploy dashboard
2. Click **"New Application"**
3. Select **"Git Repository"**
4. Connect your repository

#### Step 2: Configure Environment

In Dokploy, add these environment variables:

```bash
# Required
WHATSAPP_BASE_URL=https://your-whatsapp-api.com
WHATSAPP_API_USER=your-username
WHATSAPP_API_PASSWORD=your-password
CHAT_JID=your-group-jid@g.us

OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# Production settings
ENVIRONMENT=production
LOG_LEVEL=INFO
PORT=8000
```

#### Step 3: Configure Persistent Storage

Add a volume mount:
- **Container Path**: `/data`
- **Purpose**: Persists message database

#### Step 4: Deploy

Click **"Deploy"** - Dokploy will:
- ✅ Detect Nixpacks configuration
- ✅ Build with Python 3.11
- ✅ Install dependencies
- ✅ Start the service

#### Step 5: Access

Your service will be available at your Dokploy domain!

---

## 🎮 Using the Dashboard

Once running, you'll see:

### Main Dashboard Features

1. **Bot Cards** - Each bot has its own card showing:
   - Name and description
   - Current status (🟢 Running / 🔴 Stopped)
   - Start/Stop button
   - Logs button

2. **Starting a Bot**
   - Click the **Start** button
   - Status indicator turns green
   - Bot begins processing messages

3. **Viewing Logs**
   - Click the **Logs** button
   - See real-time bot activity
   - Auto-refreshes every 5 seconds

4. **Stopping a Bot**
   - Click the **Stop** button
   - Bot gracefully stops
   - Status indicator turns red

---

## 🤖 Built-in Bots

### 1. Translation Bot (`[ai]`)

**What it does:**
- Automatically translates Portuguese ↔ English
- Detects source language
- Responds to every non-bot message

**Example:**
```
You: Hello world
Bot: [ai] Olá mundo

You: Como vai?
Bot: [ai] How are you?
```

### 2. Joke Bot (`[joke]`)

**What it does:**
- Responds with family-friendly jokes
- Generates contextual humor
- Responds to every non-bot message

**Example:**
```
You: Tell me something funny
Bot: [joke] Why don't scientists trust atoms? Because they make up everything!
```

---

## 💡 Tips & Tricks

### Multiple Bots
- ✅ Run multiple bots simultaneously
- ✅ Each bot responds independently
- ✅ Bots ignore each other's messages (those starting with `[*]`)

### Message Tracking
- 🔹 On first start, bots skip existing messages
- 🔹 Each bot tracks its own processed messages
- 🔹 Restart-safe - won't reprocess old messages

### Performance
- 🔹 Default poll interval: 5 seconds
- 🔹 Adjust with `POLL_INTERVAL` environment variable
- 🔹 Lower = faster response, higher API usage
- 🔹 Higher = slower response, lower API usage

---

## 🔍 Health Checks

Verify your service is running:

```bash
# Simple health check
curl http://localhost:8000/health

# Detailed readiness check
curl http://localhost:8000/ready
```

Expected response:
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

---

## 🐛 Troubleshooting

### Can't connect to dashboard?

**Check service is running:**
```bash
curl http://localhost:8000/health
```

**Check logs:**
```bash
# Docker
docker-compose logs -f

# Local
Check terminal output
```

### Bots not responding?

1. **Check bot logs** in the dashboard
2. **Verify WhatsApp API**:
   ```bash
   curl -u username:password https://your-whatsapp-api.com/api
   ```
3. **Check CHAT_JID** is correct
4. **Verify messages** don't start with `[*]`

### LLM errors?

1. **Check API key**: Verify `OPENAI_API_KEY` is valid
2. **Test endpoint**:
   ```bash
   curl https://your-llm-endpoint.com/v1/models \
     -H "Authorization: Bearer your-api-key"
   ```
3. **Check model name**: Ensure `OPENAI_MODEL` is available

### Database errors?

1. **Check permissions**: Ensure `/data` directory is writable
2. **Check path**: Verify `DB_PATH` is correct
3. **Reset database**: Delete `messages.db` to start fresh (loses history)

### Frontend not loading?

1. **Check API**: Visit http://localhost:8000/bots
2. **Browser console**: Open DevTools and check for errors
3. **CORS issues**: Check `ALLOWED_ORIGINS` if hosting remotely

---

## 📊 Next Steps

### Create Your Own Bot

See the full guide in [README.md](README.md#creating-custom-bots)

Quick template:

```python
# bots/my_bot.py
from typing import Dict, Any, Optional
from core.bot_base import BotBase

class MyBot(BotBase):
    NAME = "my_bot"
    PREFIX = "[mybot]"
    
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        msg_text = message.get("content", "")
        # Your logic here
        return f"Got your message: {msg_text}"
```

Restart the service - your bot appears automatically! ✨

### Explore the API

Visit http://localhost:8000/docs for interactive API documentation

### Monitor Your Service

- 📊 Check `/ready` endpoint for metrics
- 📝 View logs in real-time
- 🔍 Use browser DevTools Network tab

### Production Deployment

See detailed production guide in [README.md](README.md#production-features)

---

## 🆘 Getting Help

- 📖 **Full Documentation**: [README.md](README.md)
- 🐛 **Report Issues**: GitHub Issues
- 💬 **Questions**: GitHub Discussions

---

## ⚙️ Configuration Reference

### Minimum Required Variables

```bash
WHATSAPP_BASE_URL=https://your-api.com
WHATSAPP_API_USER=username
WHATSAPP_API_PASSWORD=password
CHAT_JID=group-id@g.us
OPENAI_API_KEY=sk-your-key
```

### Optional Variables

```bash
OPENAI_BASE_URL=https://api.openai.com/v1  # Default
OPENAI_MODEL=gpt-4                          # Default
POLL_INTERVAL=5                             # Default (seconds)
DB_PATH=/data/messages.db                   # Default
ENVIRONMENT=production                      # development (default)
LOG_LEVEL=INFO                              # Default
PORT=8000                                   # Default
```

---

**Happy botting! 🤖✨**
