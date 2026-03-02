# Bug Fixes Summary

## Issue 1: Active Chats Not Persisting Activity

### Problem
Chats were not showing as "active" or "recent" in the dashboard because message activity wasn't being tracked in the database.

### Root Cause
The bot's `handle_message()` method was processing messages but never calling `update_message_activity()` to update the chat's `last_message_time` and `message_count` fields in the database.

### Fix
**File: `core/bot_base.py`**

Added a call to `update_message_activity()` at the beginning of `handle_message()` (line 162-164):

```python
# Update message activity for this chat
message_time = message.get("timestamp") or message.get("time")
self.db.update_message_activity(self.chat_jid, message_time=message_time)
```

### Impact
- Chats with recent bot activity will now correctly show as "active" or "recent"
- The activity filters in the dashboard will work properly
- `last_message_time` and `message_count` fields will be updated whenever a bot processes a message

---

## Issue 2: Bot State Not Persisting Between Deployments

### Problem
When you start a bot in a chat via the UI, it would stop running after a deployment/restart. The bot had to be manually restarted after every deployment.

### Root Cause
The `/bots/{bot_name}/start` and `/bots/{bot_name}/stop` endpoints only controlled the bot in memory but didn't persist the running state in the database. On restart, bots that were previously running would not auto-start.

### Fix
**Files: `api/bot_manager.py`, `api/main.py`, `core/database.py`**

#### Simplified State Model
Removed the dual "enabled/running" state system in favor of a single "running" state:
- Bots are either **running** or **stopped**
- The running state is persisted in the database
- On application restart, bots that were running will automatically restart

#### Bot Manager Changes
The `start_bot()` method now marks bots as running in the database:
```python
# Mark bot as running in database
self.database.set_bot_running_state(bot_name, chat_jid, running=True)
```

The `stop_bot()` method marks bots as not running:
```python
# Mark bot as not running in database
self.database.set_bot_running_state(bot_name, chat_jid, running=False)
```

#### Startup Behavior
On application startup, `start_running_bots()` automatically restarts all bots that were running when the app last shut down.

### Impact
- Bot state now persists between deployments and restarts
- When you start a bot, it will automatically restart after deployment
- When you stop a bot, it will remain stopped after deployment
- Simplified mental model: bots are either on or off
- No separate "enabled but not running" state to manage

---

## Testing Recommendations

### Test Issue 1 (Activity Tracking)
1. Start a bot in a chat
2. Send a message to that chat
3. Check the database: `SELECT chat_jid, last_message_time, message_count FROM chats;`
4. Verify `last_message_time` is updated and `message_count` is incremented
5. Check the dashboard with "Active" filter - the chat should appear

### Test Issue 2 (Persistence)
1. Start a bot in a chat via the UI
2. Check the database: `SELECT * FROM bot_chat_assignments WHERE chat_jid='...' AND bot_name='...';`
3. Verify `running=1`
4. Restart the application
5. Verify the bot automatically starts (check dashboard or logs)
6. Stop the bot via the UI
7. Verify `running=0` in the database
8. Restart the application again
9. Verify the bot does NOT start

---

## Database Schema Reference

### Relevant Tables

**chats table:**
```sql
CREATE TABLE chats (
    chat_jid TEXT PRIMARY KEY,
    chat_name TEXT,
    is_manual INTEGER DEFAULT 0,
    last_synced TIMESTAMP,
    last_message_time TIMESTAMP,      -- Updated by fix #1
    message_count INTEGER DEFAULT 0,  -- Updated by fix #1
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**bot_chat_assignments table:**
```sql
CREATE TABLE bot_chat_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_name TEXT NOT NULL,
    chat_jid TEXT NOT NULL,
    running INTEGER DEFAULT 0,        -- Tracks if bot should be running
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bot_name, chat_jid)
)
```

---

## Deployment Notes

These changes include a database migration that automatically renames the `enabled` column to `running` in the `bot_chat_assignments` table. The migration is handled automatically on application startup.

**Migration details:**
- The `enabled` column is renamed to `running`
- Default value changed from `1` (enabled by default) to `0` (stopped by default)
- Existing bot assignments will retain their state during migration
- The migration is idempotent and safe to run multiple times

