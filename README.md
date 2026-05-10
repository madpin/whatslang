# Whatslang

A modular WhatsApp bot service with a sleek admin console, a declarative bot
framework, and a single-user, env-driven login. Built on FastAPI, SQLite, and
a Vite/React/TypeScript dashboard.

```
┌────────────────────┐      ┌──────────────────────┐      ┌────────────────┐
│  WhatsApp Gateway  │ ◀──▶ │  Whatslang Backend   │ ◀──▶ │  React Console │
│  (whatsapp-mcp)    │      │  (FastAPI · SQLite)  │      │  (Vite/Tailwind)│
└────────────────────┘      └──────────┬───────────┘      └────────────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │   LLM (OpenAI    │
                              │   / LiteLLM)     │
                              └──────────────────┘
```

## Highlights

- **Sleek admin console** — dashboard, chats, bots, settings, dark/light themes,
  toasts, modals, search, filters, pagination.
- **Declarative bots** — adding a bot is a few-line `BotSpec` in
  `app/bots/__init__.py`. No more wiring threads, polling loops, or media
  pipelines by hand.
- **Multimodal out of the box** — text, image (vision), audio (Whisper), and
  video → audio transcription handled in one place.
- **Multiple bots per chat** — start and stop any combination of bots in any
  chat, with independent settings (context size, self-answer, redirect target).
- **Single-user auth** — username and password are env vars; sessions are
  HMAC-signed cookies. Leave both empty to disable auth on private networks.
- **One container, two stages** — Vite builds the SPA, FastAPI serves it from
  `/web/dist`. No Nginx required.

## Quick start

### 1. Configure

```bash
cp .env.example .env
$EDITOR .env
```

At minimum you need a `WHATSAPP_BASE_URL` and an `OPENAI_API_KEY` (or any
LiteLLM-compatible endpoint via `OPENAI_BASE_URL`). To enable the dashboard
login, set both `DASHBOARD_USER` and `DASHBOARD_PASSWORD`.

### 2. Backend (Python 3.10+)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app           # http://localhost:8000
```

API docs live at `http://localhost:8000/api/docs` when
`ENVIRONMENT=development`.

### 3. Frontend (Node 20+)

```bash
cd web
npm install
npm run dev             # http://localhost:5173 (proxies /api to :8000)
```

For production, run `npm run build` once — the FastAPI app picks up
`web/dist/` automatically and serves the SPA + assets.

## Docker

```bash
docker compose up --build
```

The compose file mounts a `whatslang-data` volume to `/data` so SQLite state
survives upgrades. Healthchecks hit `/health`.

## PaaS deployments (Nixpacks / Railpack)

The repo ships with both build plans — pick whichever your platform speaks. No
extra service, no buildpacks: a single image that builds the SPA, installs
Python deps, then runs uvicorn.

| Platform                     | Use                |
|------------------------------|--------------------|
| Dokploy, Coolify, older Railway | `nixpacks.toml` |
| Railway (modern), self-hosted Railpack | `railpack.json` |

### Nixpacks (`nixpacks.toml`)

- Setup: Python 3.11, Node 22, ffmpeg, curl, CA certs (pinned nixpkgs).
- Install: `pip install -r requirements.txt` into `/opt/venv` (cached).
- Build: `cd web && npm ci && npm run build` (npm + node_modules cached).
- Start: `python -m uvicorn app.main:app …` from the venv.

### Railpack (`railpack.json`)

- Provider: `python` (auto-detects `requirements.txt`).
- Packages: `python 3.11` + `node 22` via mise.
- Custom steps: `frontend:install` → `frontend:build` (with `npm` cache layers).
- Deploy: `web/dist` is layered on top of the Python deploy image, plus
  `ffmpeg` / `curl` / `ca-certificates` as runtime apt packages.
- Start: `python -m uvicorn app.main:app …`.

### Required env vars (both)

Provide the variables from `.env.example`:

- `WHATSAPP_BASE_URL`, `WHATSAPP_API_USER`, `WHATSAPP_API_PASSWORD`, `DEVICE_ID`
- `OPENAI_API_KEY` (and optionally `OPENAI_BASE_URL`, model overrides)
- `DASHBOARD_USER`, `DASHBOARD_PASSWORD`, `SESSION_SECRET` (set the secret to a
  long random string so cookies survive restarts)
- `DB_PATH=/data/messages.db` and a writable persistent volume mounted at
  `/data`

### Healthcheck

Both plans serve `GET /health` (and `/api/health`) returning `200 OK` once the
app is up — wire it up as the platform's healthcheck.

## Adding a new bot

Edit `app/bots/__init__.py` and append a `BotSpec`:

```python
BotSpec(
    name="echo",
    label="Echo",
    prefix="!echo ",
    emoji="🔁",
    description="Repeats whatever you say.",
    text_prompt="You are a polite echo. Repeat the user's text verbatim.",
    image_mode=MediaMode.IGNORE,
    audio_mode=MediaMode.IGNORE,
    video_mode=MediaMode.IGNORE,
    answer_owner_messages_default=False,
)
```

Restart the server. The new bot shows up in the dashboard, can be assigned to
any chat, and supports per-chat configuration (context size, self-answer,
response redirection).

## Project layout

```
app/
  config.py            pydantic-settings config
  logging_setup.py     pretty/JSON logging
  db.py                SQLite repository (compatible with old schema)
  auth.py              HMAC-signed session cookies
  schemas.py           Pydantic request/response models
  deps.py              FastAPI dependency providers
  main.py              app factory + SPA mount + lifespan
  routers/
    auth.py
    bots.py
    chats.py
    system.py
  services/
    whatsapp.py        WhatsApp gateway client
    llm.py             OpenAI / LiteLLM client (text/vision/audio)
    bot_manager.py     Bot lifecycle + ring buffer logs
  bots/
    base.py            BotSpec, MediaMode, generic BotRunner
    __init__.py        Declarative catalog
web/
  src/
    api/               typed fetch client + endpoints
    components/        AppShell, Sidebar, TopBar, primitives
    lib/               theme, toast, auth context, utils
    pages/             Dashboard, Chats, ChatDetail, Bots, Settings, Login
```

## Auth model

- Both `DASHBOARD_USER` and `DASHBOARD_PASSWORD` set → login required.
- Either empty → auth disabled (handy for trusted networks or other proxies).
- `SESSION_SECRET` is used to HMAC-sign cookies. Leave blank to auto-generate
  on boot (sessions invalidate on restart in that case).

## Endpoints

| Method | Path                              | Purpose                          |
|--------|-----------------------------------|----------------------------------|
| GET    | `/api/health`, `/health`          | Liveness                         |
| GET    | `/api/system`                     | Runtime configuration snapshot   |
| GET    | `/api/stats`                      | Dashboard KPIs                   |
| POST   | `/api/auth/login`, `/logout`      | Session management               |
| GET    | `/api/auth/status`                | Current auth state               |
| GET    | `/api/bots/types`, `/api/bots`    | Catalog and running instances    |
| POST   | `/api/bots/{name}/start`,`/stop`  | Per-chat lifecycle               |
| PUT    | `/api/bots/{name}/settings`       | Per-chat tuning                  |
| GET    | `/api/bots/{name}/logs`           | Ring-buffer logs                 |
| GET    | `/api/chats`, `/api/chats/all`    | Filterable list / brief list     |
| POST   | `/api/chats`, `/api/chats/sync`   | Add manually / sync from gateway |
| POST   | `/api/chats/bulk`                 | Bulk start/stop/delete           |
| GET    | `/api/chats/{jid}`                | Chat with bot statuses           |
| DELETE | `/api/chats/{jid}`                | Remove + stop bots               |

## License

MIT — see `LICENSE` if one is present, otherwise add one before publishing.
