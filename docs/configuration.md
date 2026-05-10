# Configuration

> Whatslang is configured **only** through environment variables, read
> by `pydantic-settings` from `.env` (in development) or the process
> environment (in production / Docker / PaaS).

The full schema lives in
[`app/config.py`](../app/config.py). This page is the human-friendly
companion: every variable, what it does, what the default is, and a
worked example.

---

## TL;DR

```bash
cp .env.example .env
$EDITOR .env
```

Set at least:

```dotenv
WHATSAPP_BASE_URL=http://localhost:8081
WHATSAPP_API_USER=
WHATSAPP_API_PASSWORD=
DEVICE_ID=

OPENAI_API_KEY=sk-...

DASHBOARD_USER=admin
DASHBOARD_PASSWORD=please-change
SESSION_SECRET=$(python -c 'import secrets; print(secrets.token_hex(32))')
```

`DEVICE_ID` is the JID of the WhatsApp account the gateway is logged
in as. It's used to detect "messages I sent". Leave blank to
auto-detect from outgoing messages.

---

## Reference

### Server

| Variable | Default | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | Bind address for uvicorn. |
| `PORT` | `8000` | Bind port for uvicorn. |
| `ENVIRONMENT` | `development` | `development` exposes `/api/docs` and sets the cookie `secure=False`. `production` hides docs and sets `secure=True`. |
| `LOG_LEVEL` | `INFO` | `DEBUG \| INFO \| WARNING \| ERROR`. `DEBUG` turns on verbose gateway logging. |
| `ALLOWED_ORIGINS` | `*` | Comma-separated list for CORS, or `*`. Required only if you serve the SPA from a different origin (rare — by default FastAPI hosts the built SPA). |

### Single-user dashboard auth

| Variable | Default | Description |
|---|---|---|
| `DASHBOARD_USER` | `admin` | The single permitted username. |
| `DASHBOARD_PASSWORD` | *(empty)* | The plain-text password. **Empty disables auth entirely** — handy on private networks behind another auth proxy. |
| `SESSION_SECRET` | *(empty → auto)* | HMAC key for the `whatslang_session` cookie. If empty, a random key is generated at startup, which means **sessions are invalidated on every restart**. Set this to a long random string in production. |
| `SESSION_MAX_AGE_SECONDS` | `604800` (7 days) | Cookie max-age. |

> Generate a strong secret:
> ```bash
> python -c 'import secrets; print(secrets.token_hex(32))'
> ```

### WhatsApp gateway

The gateway is a **separate** service you run yourself (e.g.
`whatsapp-mcp` or `wha-mcp`). Whatslang speaks REST to it.

| Variable | Default | Description |
|---|---|---|
| `WHATSAPP_BASE_URL` | *(empty)* | Base URL of your gateway, e.g. `http://localhost:8081`. **Required.** |
| `WHATSAPP_API_USER` | *(empty)* | HTTP basic-auth username, if your gateway needs it. |
| `WHATSAPP_API_PASSWORD` | *(empty)* | HTTP basic-auth password, if your gateway needs it. |
| `DEVICE_ID` | *(empty)* | JID of the WhatsApp account the gateway is logged in as (e.g. `12345@s.whatsapp.net`). Used to recognise "self" messages. Leave blank for auto-detection from the first outgoing message we observe. |

If you can `curl ${WHATSAPP_BASE_URL}/chats` and get JSON back, the
diagnostics page will say *"Gateway: reachable"* and your bots will
work.

### LLM (OpenAI / LiteLLM-compatible)

Whatslang talks to anything that exposes the OpenAI Chat Completions
API: real OpenAI, Azure OpenAI, LiteLLM, vLLM, llama.cpp's
openai-compatible server, OpenRouter, etc.

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(empty)* | Provider API key. Required to call any model. Whatslang doesn't validate this at boot — it errors when the first call is made. |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Override to point at a different provider. |
| `OPENAI_MODEL` | `gpt-4o-mini` | Default text + vision model. |
| `OPENAI_VISION_MODEL` | *(empty → falls back to `OPENAI_MODEL`)* | Override only if your provider uses a different model name for vision. |
| `OPENAI_AUDIO_MODEL` | `whisper-1` | Audio-transcription model. Used for both voice notes and the audio extracted from videos. |

#### Examples per provider

<details>
<summary><strong>OpenAI</strong></summary>

```dotenv
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
OPENAI_VISION_MODEL=
OPENAI_AUDIO_MODEL=whisper-1
```
</details>

<details>
<summary><strong>Azure OpenAI (via LiteLLM proxy, recommended)</strong></summary>

Run [LiteLLM](https://docs.litellm.ai/) as a proxy and point Whatslang
at it:

```dotenv
OPENAI_API_KEY=any-non-empty-string
OPENAI_BASE_URL=http://litellm:4000
OPENAI_MODEL=azure/gpt-4o-mini
OPENAI_VISION_MODEL=azure/gpt-4o
OPENAI_AUDIO_MODEL=azure/whisper-1
```
</details>

<details>
<summary><strong>OpenRouter</strong></summary>

```dotenv
OPENAI_API_KEY=sk-or-v1-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o-mini
OPENAI_VISION_MODEL=openai/gpt-4o
# OpenRouter doesn't expose Whisper today; route audio through OpenAI directly:
OPENAI_AUDIO_MODEL=whisper-1
```

If you only have a single key, point all three at OpenRouter and use a
provider that supports audio.
</details>

<details>
<summary><strong>Local llama.cpp / vLLM</strong></summary>

```dotenv
OPENAI_API_KEY=sk-local
OPENAI_BASE_URL=http://localhost:8080/v1
OPENAI_MODEL=qwen2.5-7b-instruct
# vision and audio off:
OPENAI_VISION_MODEL=
OPENAI_AUDIO_MODEL=
```

If `OPENAI_AUDIO_MODEL` is empty, audio bots will reply with the
"couldn't transcribe" error. That's fine — just keep audio bots off
for that deployment.
</details>

### Bot runtime

| Variable | Default | Description |
|---|---|---|
| `POLL_INTERVAL` | `5` | Seconds between gateway polls per bot. Lower = snappier, higher = lighter on the gateway. |
| `DB_PATH` | `./data/messages.db` | Where SQLite lives. **In Docker, set this to `/data/messages.db`** so the volume mount catches it. |

### Backwards compatibility

| Variable | Default | Description |
|---|---|---|
| `CHAT_JID` | *(empty)* | Legacy single-chat JID. If set, that chat is auto-seeded into the `chats` table on first boot — useful when migrating from the original "one bot, one chat" version. Safe to leave blank. |

---

## Required vs optional

`Settings.required_missing()` (called at startup and surfaced via
`/api/system`) checks the following are non-empty:

- `WHATSAPP_BASE_URL`
- `WHATSAPP_API_USER`
- `WHATSAPP_API_PASSWORD`
- `DEVICE_ID`
- `OPENAI_API_KEY`

If any are missing the app still **boots** (so you can hit
`/api/diagnostics` to see what's wrong), but bots will error out on
their first call. The diagnostics panel makes this obvious.

---

## Worked examples

### Local development (no auth)

```dotenv
HOST=127.0.0.1
PORT=8000
ENVIRONMENT=development
LOG_LEVEL=DEBUG

DASHBOARD_USER=
DASHBOARD_PASSWORD=
SESSION_SECRET=

WHATSAPP_BASE_URL=http://localhost:8081
DEVICE_ID=12345@s.whatsapp.net

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

POLL_INTERVAL=5
DB_PATH=./data/messages.db
```

### Production (Docker Compose)

```dotenv
ENVIRONMENT=production
LOG_LEVEL=INFO

DASHBOARD_USER=admin
DASHBOARD_PASSWORD=$(openssl rand -hex 16)
SESSION_SECRET=$(openssl rand -hex 32)

WHATSAPP_BASE_URL=http://wa-gateway:8081
WHATSAPP_API_USER=apiuser
WHATSAPP_API_PASSWORD=apipass
DEVICE_ID=12345@s.whatsapp.net

OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
OPENAI_AUDIO_MODEL=whisper-1

POLL_INTERVAL=5
DB_PATH=/data/messages.db
```

### Behind a self-hosted reverse proxy (Caddy, Traefik)

Same as production, plus an `ALLOWED_ORIGINS` if you put the SPA on a
separate domain. If you keep the SPA hosted by FastAPI (the default),
you don't need to change anything — same-origin requests work out of
the box.

---

## How env vars are read

[`Settings`](../app/config.py) is a `pydantic_settings.BaseSettings`
with these options:

- `env_file=".env"` — read from `.env` if present (Docker doesn't have
  this file but the env vars are passed directly).
- `case_sensitive=False` — `OPENAI_MODEL` and `openai_model` both work.
- `extra="ignore"` — unknown variables don't raise an error; safe to
  share `.env` between Whatslang and the gateway.

The single source of truth at runtime is `get_settings()`, which is
LRU-cached. To pick up changed variables, restart the process.
