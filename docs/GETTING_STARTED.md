# 🚀 Getting Started with WhatsApp Bot Service

**New to WhatsApp Bot Service?** Start here! This guide will take you from zero to running your first bot in minutes.

## 📍 Where Am I?

You're at the **starting line** of your WhatsApp bot journey! This guide is designed for absolute beginners.

## 🎯 What You'll Learn

By the end of this guide, you'll have:
- ✅ A running WhatsApp bot service
- ✅ Access to the web dashboard
- ✅ Your first bot responding to messages
- ✅ Understanding of basic concepts

**Time needed:** 10-15 minutes

---

## 🧠 Quick Concepts (Read First!)

Before diving in, let's understand what this service does:

### What is This?
A **web service** that runs **bots** on **WhatsApp** that you can **manage** from a **web dashboard**.

### Key Terms
- **Bot**: An automated responder (like Translation Bot, Joke Bot)
- **Chat/Group**: Your WhatsApp group where bots will respond
- **Dashboard**: A web page where you control bots
- **API**: The WhatsApp connection service

### How It Works
```
You send message → WhatsApp → Our Service → Bot processes → Bot replies
     ↑                                           ↓
     └──────────── You control bots via web dashboard
```

---

## 📋 Prerequisites

Before starting, make sure you have:

### Required
- [ ] **Python 3.10+** installed ([Download here](https://www.python.org/downloads/))
- [ ] **WhatsApp API endpoint** (e.g., [go-whatsapp-web-multidevice](https://github.com/aldinokemal/go-whatsapp-web-multidevice))
- [ ] **OpenAI API key** or LiteLLM endpoint ([Get one here](https://platform.openai.com/api-keys))

### Check Your Python Version
```bash
python3 --version
# Should show: Python 3.10.x or higher
```

---

## 🎬 Step-by-Step Setup

### Step 1: Get the Code

Clone the repository:

```bash
git clone https://github.com/yourusername/whatslang.git
cd whatslang
```

### Step 2: Set Up Python Environment

Create a virtual environment (keeps things tidy):

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # On Mac/Linux
# OR
.venv\Scripts\activate     # On Windows
```

💡 **Tip**: Your terminal prompt should now start with `(.venv)` - this means it's working!

### Step 3: Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

☕ This will take 1-2 minutes. Perfect time for a coffee break!

### Step 4: Configure Your Settings

Create your configuration file:

```bash
cp env.example .env
```

Now edit the `.env` file with your text editor:

```bash
# === REQUIRED SETTINGS ===

# Your WhatsApp API URL
WHATSAPP_BASE_URL=https://your-whatsapp-api.com

# WhatsApp API credentials
WHATSAPP_API_USER=your-username
WHATSAPP_API_PASSWORD=your-password

# The group/chat where bots will work
CHAT_JID=your-group-jid@g.us

# Your OpenAI/LLM API key
OPENAI_API_KEY=sk-your-api-key-here

# === OPTIONAL SETTINGS ===
# (You can leave these as-is for now)

OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
POLL_INTERVAL=5
```

#### 🤔 Where do I get these values?

**WHATSAPP_BASE_URL**: This is your WhatsApp API service URL. If you're using [go-whatsapp-web-multidevice](https://github.com/aldinokemal/go-whatsapp-web-multidevice), it's usually `http://localhost:3000` or your deployed URL.

**CHAT_JID**: The WhatsApp group ID. You can get this from your WhatsApp API's `/app/chats` endpoint.

**OPENAI_API_KEY**: Get this from [OpenAI's platform](https://platform.openai.com/api-keys) after creating an account.

### Step 5: Start the Service

```bash
python run.py
```

You should see something like:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

🎉 **Success!** Your service is running!

### Step 6: Open the Dashboard

Open your web browser and go to:

```
http://localhost:8000/static/index.html
```

You should see a beautiful dashboard with your available bots! 🚀

---

## 🎮 Using Your First Bot

Now let's actually use a bot:

### 1. Choose a Bot

In the dashboard, you'll see cards for each bot:
- **Translation Bot** - Translates Portuguese ↔ English
- **Joke Bot** - Generates funny jokes

### 2. Start a Bot

Click the **"Start"** button on any bot card.

The status should change from 🔴 **Stopped** to 🟢 **Running**.

### 3. Test It Out!

Go to your WhatsApp group and send a message:

**For Translation Bot:**
```
Send: "Hello, how are you?"
Bot replies: "[ai] Olá, como você está?"
```

**For Joke Bot:**
```
Send: "Tell me something funny"
Bot replies: "[joke] Why don't scientists trust atoms? Because they make up everything!"
```

### 4. View Logs

Back in the dashboard, click **"Logs"** to see what your bot is doing.

### 5. Stop a Bot

When you're done, click **"Stop"** to pause the bot.

---

## ✅ Success Checklist

You're all set if you can:

- [ ] Access the dashboard at http://localhost:8000/static/index.html
- [ ] See your bots listed
- [ ] Start a bot (status turns green)
- [ ] Bot responds in your WhatsApp group
- [ ] View bot logs in the dashboard
- [ ] Stop a bot

**All checked?** Congratulations! You're now running WhatsApp bots! 🎉

---

## 🎓 What's Next?

Now that you have the basics, explore more:

### Beginner Next Steps
- 📖 **[User Guide](USER_GUIDE.md)** - Learn all dashboard features
- 🎨 **[Creating Custom Bots](CREATING_BOTS.md)** - Make your own bot
- 🔐 **[Security Guide](SECURITY.md)** - Protect your dashboard with a password

### Advanced Topics
- 🚀 **[Deployment Guide](DEPLOYMENT.md)** - Deploy to production
- 💾 **[Data Persistence](PERSISTENCE.md)** - Understand data storage
- 🐍 **[Virtual Environments](VENV_GUIDE.md)** - Deep dive into Python environments

---

## 🆘 Troubleshooting

### Problem: "Can't connect to dashboard"

**Solution:**
1. Make sure the service is running (check terminal)
2. Try http://localhost:8000/health - should show `{"status":"healthy"}`
3. Check for errors in terminal

### Problem: "Bot not responding"

**Solution:**
1. Make sure bot is **started** (green status)
2. Check bot logs for errors
3. Verify `CHAT_JID` is correct
4. Test your WhatsApp API is working: `curl -u user:pass YOUR_WHATSAPP_API_URL/app/health`

### Problem: "Import errors when installing"

**Solution:**
1. Make sure virtual environment is activated (you should see `(.venv)` in terminal)
2. Check Python version: `python --version` (needs 3.10+)
3. Try: `pip install --upgrade pip` then reinstall requirements

### Problem: "LLM/OpenAI errors"

**Solution:**
1. Verify your `OPENAI_API_KEY` is correct
2. Check you have credits/quota available
3. Test the API: `curl https://api.openai.com/v1/models -H "Authorization: Bearer YOUR_KEY"`

### Still stuck?

- 📖 Check the [Full Troubleshooting Guide](../README.md#troubleshooting)
- 💬 Open an issue on GitHub
- 🔍 Check existing GitHub issues

---

## 💡 Pro Tips

1. **Keep your terminal open** - You'll see helpful logs there
2. **Use Incognito mode** when testing - Avoids cache issues
3. **Check the browser console** (F12) - Shows frontend errors
4. **Start simple** - Test with just one bot first
5. **Read the logs** - They tell you what's happening

---

## 📚 Learning Path

Here's your recommended learning journey:

```
1. 🎯 GETTING_STARTED.md ← You are here!
   └─→ Get service running & test first bot

2. 📖 USER_GUIDE.md
   └─→ Learn all dashboard features

3. 🎨 CREATING_BOTS.md
   └─→ Build your own custom bot

4. 🔐 SECURITY.md
   └─→ Add password protection

5. 🚀 DEPLOYMENT.md
   └─→ Deploy to production

6. 🔧 ADVANCED_TOPICS.md
   └─→ Fine-tune & optimize
```

---

## 🎉 Congratulations!

You've successfully set up your WhatsApp Bot Service! You're now ready to:

- ✨ Run multiple bots simultaneously
- 🎨 Create your own custom bots
- 🚀 Deploy to production
- 🤖 Automate your WhatsApp interactions

**Happy botting!** 🤖💬✨

---

**Questions?** Check out the [User Guide](USER_GUIDE.md) or [Full Documentation](README.md)!

