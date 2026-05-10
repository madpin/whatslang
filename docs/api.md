# REST API reference

> Auto-generated docs are also available at `GET /api/docs` (Swagger
> UI) and `GET /api/openapi.json` (raw OpenAPI) when
> `ENVIRONMENT=development`.

This file is the human-edited reference. Everything is JSON in,
JSON out, served under `/api/`.

---

## Table of contents

- [Conventions](#conventions)
- [Auth](#auth)
- [System](#system)
- [Bots](#bots)
- [Chats](#chats)
- [Bulk actions](#bulk-actions)
- [Common shapes](#common-shapes)

---

## Conventions

- Base URL: same origin as the SPA (e.g. `http://localhost:8000`).
- Auth: when `DASHBOARD_PASSWORD` is set, every endpoint **except**
  `/health`, `/api/health`, and `/api/auth/*` requires a valid
  `whatslang_session` cookie.
- Errors use FastAPI's standard shape: `{"detail": "message"}` with the
  appropriate 4xx/5xx status code.
- Timestamps are ISO 8601 strings in UTC.
- All Pydantic models referenced below live in
  [`app/schemas.py`](../app/schemas.py).

---

## Auth

### `GET /api/auth/status`

Tells the SPA whether it must show the login page.

```bash
curl http://localhost:8000/api/auth/status
```

```jsonc
{
  "auth_required": true,
  "user": "admin"   // null if not logged in or if auth is disabled
}
```

### `POST /api/auth/login`

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H 'content-type: application/json' \
  -d '{"user":"admin","password":"please-change"}'
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `user` | `string?` | no | Falls back to `DASHBOARD_USER` server-side. |
| `password` | `string` | yes | |

`200`: sets a `whatslang_session` HMAC-signed cookie (httponly, samesite=lax).
`401`: bad credentials.

### `POST /api/auth/logout`

Clears the cookie. Always returns 200.

```bash
curl -X POST http://localhost:8000/api/auth/logout
```

---

## System

### `GET /health`, `GET /api/health`

Liveness probe. Always returns 200 once the app is up.

```jsonc
{ "status": "healthy", "timestamp": "2026-05-10T11:00:00Z", "version": "1.0.0" }
```

### `GET /api/ready`

Readiness probe. Same shape, status: `"ready"`.

### `GET /api/system`

A snapshot of the runtime configuration.

```jsonc
{
  "version": "1.0.0",
  "environment": "production",
  "auth_required": true,
  "whatsapp_base_url": "http://wa-gateway:8081",
  "openai_model": "gpt-4o-mini",
  "openai_vision_model": "gpt-4o-mini",
  "openai_audio_model": "whisper-1",
  "poll_interval": 5,
  "db_path": "/data/messages.db"
}
```

### `GET /api/stats`

The four KPIs for the dashboard.

```jsonc
{
  "total_chats": 47,
  "running_bots": 8,
  "available_bot_types": 4,
  "active_chats_24h": 12
}
```

### `GET /api/diagnostics`

Aggregated health snapshot. Takes ~50–500 ms because of the gateway probe.

```jsonc
{
  "timestamp": "2026-05-10T11:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "gateway": {
    "base_url": "http://wa-gateway:8081",
    "reachable": true,
    "http_status": 200,
    "latency_ms": 38,
    "is_connected": true,
    "is_logged_in": true,
    "device_id": "12345@s.whatsapp.net",
    "error": null,
    "last_call_at": "2026-05-10T10:59:55Z",
    "last_error_at": null,
    "call_count": 12483,
    "error_count": 0
  },
  "llm": {
    "base_url": "https://api.openai.com/v1",
    "text_model": "gpt-4o-mini",
    "vision_model": "gpt-4o-mini",
    "audio_model": "whisper-1",
    "api_key_set": true
  },
  "database": {
    "path": "/data/messages.db",
    "size_bytes": 1245184,
    "chats": 47,
    "assignments": 12,
    "processed_messages": 9821
  },
  "bots": {
    "catalog_size": 4,
    "running": 8,
    "poll_interval": 5
  },
  "recent_errors": [
    /* GatewayErrorEntry[], most recent first */
  ]
}
```

> The LLM panel intentionally does not call the provider — that would
> burn tokens on every refresh.

---

## Bots

### `GET /api/bots/types`

List every registered bot.

```jsonc
[
  {
    "name": "translation",
    "label": "EN ↔ PT Translator",
    "prefix": "[ai]",
    "emoji": "🌐",
    "description": "Translates between English and Portuguese ...",
    "supports": { "text": true, "image": true, "audio": true, "video": true }
  },
  ...
]
```

### `GET /api/bots`

List currently **running** instances (one entry per `(bot, chat)` thread).

```jsonc
[
  {
    "name": "translation",
    "label": "EN ↔ PT Translator",
    "prefix": "[ai]",
    "emoji": "🌐",
    "description": "...",
    "chat_jid": "12345@s.whatsapp.net",
    "status": "running",
    "uptime_seconds": 3601,
    "answer_owner_messages": true,
    "context_message_count": 0,
    "response_chat_jid": null,
    "supports": { "text": true, "image": true, "audio": true, "video": true }
  }
]
```

### `POST /api/bots/{name}/start`

Spin up the bot for a specific chat.

| Param | Type | In | Required | |
|---|---|---|---|---|
| `name` | `string` | path | yes | A bot name from `/api/bots/types`. |
| `chat_jid` | `string` | query | yes | The chat to attach the bot to. Must exist in `/api/chats`. |

```bash
curl -X POST 'http://localhost:8000/api/bots/translation/start?chat_jid=12345@s.whatsapp.net'
```

`200`: `{"message": "Started translation for 12345@s.whatsapp.net"}`.
`404`: unknown bot or unknown chat.
`500`: failed to start (see logs).

> Idempotent — calling `start` for an already-running pair returns 200
> without doing anything.

### `POST /api/bots/{name}/stop`

```bash
curl -X POST 'http://localhost:8000/api/bots/translation/stop?chat_jid=12345@s.whatsapp.net'
```

`200`: returns `{"message": "Stopped …"}`. Always idempotent.
`404`: unknown bot.

### `PUT /api/bots/{name}/settings`

Update per-chat settings. The settings persist even if the bot is
later stopped and restarted.

```bash
curl -X PUT 'http://localhost:8000/api/bots/translation/settings?chat_jid=12345@s.whatsapp.net' \
  -H 'content-type: application/json' \
  -d '{
    "answer_owner_messages": true,
    "context_message_count": 5,
    "response_chat_jid": null
  }'
```

| Field | Type | Notes |
|---|---|---|
| `answer_owner_messages` | `boolean?` | If `false`, ignore messages where `is_from_me=true`. |
| `context_message_count` | `int? ≥ 0` | Number of previous messages to include as chat history in the LLM call. `0` = stateless. |
| `response_chat_jid` | `string?` | Send the bot's reply to a different chat. Empty string clears the redirect. The target chat must exist in `/api/chats`. |

Any field set to `null` (or absent) is left unchanged. `400` if
`context_message_count < 0` or `response_chat_jid` doesn't exist.

`200`: returns the new `BotStatus` for that pair.

### `GET /api/bots/{name}/logs`

Pull the latest entries from the per-bot ring buffer.

| Param | Type | In | Default | |
|---|---|---|---|---|
| `name` | `string` | path | — | Bot name. |
| `chat_jid` | `string` | query | — | Chat. |
| `limit` | `int` | query | 100 | Max entries to return. |

```jsonc
{
  "bot_name": "translation",
  "chat_jid": "12345@s.whatsapp.net",
  "logs": [
    { "timestamp": "2026-05-10T10:59:55Z", "level": "INFO", "message": "Replied to abc123 (1 chunks)" },
    ...
  ]
}
```

> Only running bots have logs. The buffer holds up to 200 entries; once
> the bot is stopped the buffer is dropped.

---

## Chats

### `GET /api/chats`

Paginated, filterable list — backs the **Chats** page.

| Param | Type | Default | Notes |
|---|---|---|---|
| `page` | `int` | 1 | 1-based. |
| `per_page` | `int` | 20 | 1–100. |
| `sort` | `string` | `last_message_time` | One of `last_message_time`, `chat_name`, `message_count`, `added_at`. |
| `order` | `string` | `desc` | `asc` or `desc`. |
| `activity` | `string?` | — | `active` (last 24 h), `recent` (last 7 d), `idle` (>7 d or never). |
| `bot_status` | `string?` | — | `running` (any running bot) or `none` (no assignments). |
| `chat_type` | `string?` | — | `group` or `individual`. |
| `search` | `string?` | — | Substring match on `chat_name` or `chat_jid`. |

```jsonc
{
  "chats": [
    {
      "chat_jid": "12345@s.whatsapp.net",
      "chat_name": "Friends 🎉",
      "is_manual": false,
      "is_group": false,
      "last_synced": "2026-05-10T10:00:00Z",
      "last_message_time": "2026-05-10T10:59:00Z",
      "message_count": 421,
      "added_at": "2026-04-12T14:00:00Z",
      "bots": [
        /* BotStatus[] for every BotSpec, with status running|stopped */
      ]
    }
  ],
  "pagination": { "page": 1, "per_page": 20, "total": 47, "total_pages": 3 }
}
```

### `GET /api/chats/all`

Lean list — every chat, no bot statuses, no pagination. Used by the
chat picker in the bot settings modal.

| Param | Type | Default | |
|---|---|---|---|
| `limit` | `int` | 500 | 1–2000. |

```jsonc
[
  { "chat_jid": "12345@s.whatsapp.net", "chat_name": "Friends 🎉" },
  ...
]
```

### `GET /api/chats/search`

Searchable autocomplete used by the redirect-target picker.

| Param | Type | Default | |
|---|---|---|---|
| `q` | `string` | `""` | Substring of name or JID. |
| `limit` | `int` | 30 | 1–100. |
| `chat_type` | `string?` | — | `group` or `individual`. |

Returns `ChatBrief[]`, sorted by `last_message_time desc`.

### `POST /api/chats`

Add a chat manually (without a full sync).

```bash
curl -X POST http://localhost:8000/api/chats \
  -H 'content-type: application/json' \
  -d '{"chat_jid":"99999@s.whatsapp.net","chat_name":"Sandbox"}'
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `chat_jid` | `string` | yes | The WhatsApp JID. Should end in `@s.whatsapp.net` (DM) or `@g.us` (group). |
| `chat_name` | `string?` | no | Friendly name. If omitted, Whatslang queries the gateway for one and falls back to the JID. |

`200`: returns the resulting `Chat`. If the chat already existed, the
existing record is returned. `400` if neither create nor lookup
succeed.

### `POST /api/chats/sync`

Pull chats from the gateway:

- groups via `GET /groups`
- individual chats via `GET /chats`
- contacts via `GET /contacts` (used to backfill DM display names)
- best-effort name re-resolution for any chat still showing only its JID

```jsonc
{ "message": "Synced 14 group(s) and 32 individual chat(s). Refined 3 display name(s)." }
```

Idempotent — safe to call repeatedly.

### `GET /api/chats/{chat_jid}`

```jsonc
{
  "chat_jid": "12345@s.whatsapp.net",
  "chat_name": "Friends 🎉",
  "is_manual": false,
  "is_group": false,
  "last_synced": "2026-05-10T10:00:00Z",
  "last_message_time": "2026-05-10T10:59:00Z",
  "message_count": 421,
  "added_at": "2026-04-12T14:00:00Z",
  "bots": [ /* BotStatus[] for every registered bot */ ]
}
```

`404` if the chat isn't in the DB.

### `DELETE /api/chats/{chat_jid}`

Stops every bot running for the chat, then removes the chat row
(`bot_chat_assignments` is cascaded automatically).

```jsonc
{ "message": "Chat 12345@s.whatsapp.net deleted" }
```

### `GET /api/chats/{chat_jid}/messages`

Live pass-through to the gateway. Used to peek at recent messages
inside the chat detail page.

| Param | Type | Default | |
|---|---|---|---|
| `limit` | `int` | 20 | 1–100. |

```jsonc
{
  "chat_jid": "12345@s.whatsapp.net",
  "messages": [ /* gateway-shaped message objects */ ],
  "count": 20
}
```

---

## Bulk actions

### `POST /api/chats/bulk`

```bash
curl -X POST http://localhost:8000/api/chats/bulk \
  -H 'content-type: application/json' \
  -d '{
    "chat_jids": ["12345@s.whatsapp.net", "67890@g.us"],
    "action": "stop_bots"
  }'
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `chat_jids` | `string[]` | yes | List of chat JIDs to operate on. |
| `action` | `string` | yes | One of `start_bots`, `stop_bots`, `delete_chats`. |

| Action | What it does |
|---|---|
| `start_bots` | For each chat, start every bot whose assignment row has `running=1`. Useful after a manual stop. |
| `stop_bots` | For each chat, stop every bot currently running. Doesn't change assignments — they'll resume on next `start_bots` or process restart. |
| `delete_chats` | Stop bots, then delete the chat row (cascades to assignments). |

```jsonc
{ "message": "stop_bots: applied to 2/2 chats" }
```

`400` if the action isn't recognised. Per-chat failures don't fail the
whole call — they just decrease the success counter and are logged.

---

## Common shapes

### `BotStatus`

Returned by `GET /api/bots`, `GET /api/chats/{jid}`, and the settings
PUT.

```jsonc
{
  "name": "translation",
  "label": "EN ↔ PT Translator",
  "prefix": "[ai]",
  "emoji": "🌐",
  "description": "...",
  "chat_jid": "12345@s.whatsapp.net",
  "status": "running",         // "running" | "stopped"
  "uptime_seconds": 3601,      // null when stopped
  "answer_owner_messages": true,
  "context_message_count": 5,
  "response_chat_jid": null,
  "supports": { "text": true, "image": true, "audio": true, "video": true }
}
```

### `Chat`

```jsonc
{
  "chat_jid": "12345@s.whatsapp.net",
  "chat_name": "Friends 🎉",
  "is_manual": false,
  "is_group": false,
  "last_synced": "2026-05-10T10:00:00Z",
  "last_message_time": "2026-05-10T10:59:00Z",
  "message_count": 421,
  "added_at": "2026-04-12T14:00:00Z"
}
```

### `ChatWithBots`

`Chat` + `bots: BotStatus[]`.

### `ChatBrief`

```jsonc
{ "chat_jid": "...", "chat_name": "..." }
```

### `Pagination`

```jsonc
{ "page": 1, "per_page": 20, "total": 47, "total_pages": 3 }
```

### `SimpleMessage`

Used for write-y endpoints that just need to confirm success.

```jsonc
{ "message": "..." }
```

### `GatewayErrorEntry` (inside `Diagnostics.recent_errors`)

```jsonc
{
  "timestamp": "2026-05-10T10:00:00Z",
  "where": "get_messages",
  "status": 502,
  "message": "upstream timeout"
}
```

---

## Curl recipe sheet

```bash
HOST="http://localhost:8000"
COOKIE="cookies.txt"

# Login (only when DASHBOARD_PASSWORD is set)
curl -c $COOKIE -X POST "$HOST/api/auth/login" \
  -H 'content-type: application/json' \
  -d '{"user":"admin","password":"please-change"}'

# Helper for subsequent calls
api() { curl -b $COOKIE -H 'content-type: application/json' "$@"; }

# Sync chats from the gateway
api -X POST "$HOST/api/chats/sync"

# List the first 50 chats
api "$HOST/api/chats?per_page=50"

# Add a chat manually
api -X POST "$HOST/api/chats" \
  -d '{"chat_jid":"99999@s.whatsapp.net","chat_name":"Sandbox"}'

# Start translation in that chat
api -X POST "$HOST/api/bots/translation/start?chat_jid=99999@s.whatsapp.net"

# Increase its context window to 5
api -X PUT "$HOST/api/bots/translation/settings?chat_jid=99999@s.whatsapp.net" \
  -d '{"context_message_count":5}'

# Tail logs
api "$HOST/api/bots/translation/logs?chat_jid=99999@s.whatsapp.net&limit=20"

# Stop it
api -X POST "$HOST/api/bots/translation/stop?chat_jid=99999@s.whatsapp.net"
```
