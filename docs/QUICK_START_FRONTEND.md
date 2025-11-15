# Frontend Quick Start Guide

## 🎯 Get the Frontend Running in 5 Minutes

### Option 1: Docker (Easiest)

**Prerequisites:** Docker and Docker Compose installed

```bash
# From project root
docker-compose up -d

# Wait for services to start (30-60 seconds)
# Access frontend at: http://localhost:3000
# Backend API at: http://localhost:8000
```

That's it! The frontend is now running with the full stack.

---

### Option 2: Local Development

**Prerequisites:** Node.js 18+ and npm

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies (first time only)
npm install

# 3. Start development server
npm run dev

# Frontend will be available at: http://localhost:5173
# (Make sure backend is running at http://localhost:8000)
```

---

## 📱 Using the Frontend

### First Steps:

1. **Open in browser**: http://localhost:3000 (Docker) or http://localhost:5173 (dev)

2. **Check health status**: Look for "🟢 Online" in the top-right corner

3. **Navigate the app**: Use the sidebar on the left
   - 📊 Dashboard - Overview
   - 🤖 Bots - Manage bots
   - 💬 Chats - Register chats
   - ⏰ Schedules - Schedule messages
   - 📧 Messages - View history

### Quick Workflow:

**Step 1: Create a Bot**
1. Go to **Bots** → Click **Create Bot**
2. Select bot type (e.g., "translation")
3. Enter name and description
4. Configure bot settings
5. Click **Create Bot**

**Step 2: Register a Chat**
1. Go to **Chats** → Click **Register Chat**
2. Enter WhatsApp JID (e.g., `120363419538094902@g.us`)
3. Enter chat name
4. Select type (group/private)
5. Click **Register Chat**

**Step 3: Assign Bot to Chat**
1. Go to **Chats** → Click on your chat
2. Click **Assign Bot**
3. Select your bot
4. Set priority and enable
5. Click **Assign Bot**

**Done!** Your bot is now active in the chat.

---

## 🔧 Configuration

### Environment Variables

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

For production, change to your production API URL.

---

## 🎨 Features Overview

### Dashboard
- View stats at a glance
- See recent messages
- Quick action buttons

### Bot Management
- Create/edit/delete bots
- Dynamic configuration forms
- Enable/disable bots
- Search and filter

### Chat Management
- Register WhatsApp chats
- Assign multiple bots per chat
- Set bot priority
- Sync from WhatsApp

### Schedule Management
- One-time scheduled messages
- Recurring messages (cron)
- Visual cron builder
- Trigger manually

### Messages
- Real-time message feed (updates every 5 seconds)
- Send messages directly
- Search and filter
- Chat name resolution

---

## 🚨 Troubleshooting

### Frontend won't start (Docker)
```bash
# Check logs
docker-compose logs frontend

# Rebuild
docker-compose up -d --build frontend
```

### Frontend won't start (Dev)
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### API not connecting
1. Check backend is running: `curl http://localhost:8000/health`
2. Check VITE_API_BASE_URL in .env
3. Check browser console for errors (F12)

### "🔴 Offline" status
- Backend is not running or not accessible
- Check backend logs: `docker-compose logs backend`
- Verify WHATSAPP_BASE_URL is set correctly

---

## 📦 Building for Production

```bash
cd frontend
npm run build

# Output will be in dist/
# Serve with any static file server or use Docker
```

---

## 🎯 Next Steps

1. ✅ Frontend running
2. ✅ Backend running
3. ✅ Created a bot
4. ✅ Registered a chat
5. ✅ Assigned bot to chat

Now:
- **Monitor messages** in real-time on the Messages page
- **Schedule recurring messages** for daily reminders
- **Create more bots** with different configurations
- **Manage multiple chats** from one interface

---

## 📚 Learn More

- **Frontend README**: `frontend/README.md`
- **Backend README**: `backend/REQUIREMENTS.md`
- **Main README**: `README.md`
- **API Docs**: http://localhost:8000/docs

---

## 💡 Tips

1. **Use the refresh button** (top-right) to manually update all data
2. **Search is available** on all list pages
3. **Skeleton loaders** show while data is loading
4. **Toast notifications** confirm all actions
5. **Confirmation dialogs** prevent accidental deletions
6. **Health indicator** shows backend status in real-time
7. **Live badge** on Messages page indicates real-time updates

---

## 🎉 Enjoy Your WhatsApp Bot Platform!

Questions? Check the documentation or open an issue.

