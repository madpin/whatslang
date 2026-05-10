# Deployment

> One container, one process, one SQLite file on a volume. Pick the
> recipe that matches your platform.

| Recipe | Best for | Files |
|---|---|---|
| [Docker Compose](#docker-compose) | Self-hosted, single VM | `Dockerfile`, `docker-compose.yml` |
| [Plain Docker](#plain-docker) | Custom orchestration | `Dockerfile` |
| [Nixpacks](#nixpacks-dokploy--coolify--older-railway) | Dokploy, Coolify, older Railway | `nixpacks.toml` |
| [Railpack](#railpack-modern-railway) | Modern Railway, Railpack-supporting hosts | `railpack.json` |
| [Bare metal / systemd](#bare-metal--systemd) | A VM, no Docker | `Makefile` |
| [Reverse proxy](#reverse-proxy) | Behind nginx / Caddy / Traefik | `Caddyfile` (sample) |

For environment variables, see [configuration.md](configuration.md).

---

## Common requirements

- A reachable WhatsApp gateway (`whatsapp-mcp` / `wha-mcp`-compatible).
- An OpenAI-compatible API key.
- A persistent volume for `data/messages.db`. **You must mount it**
  or your DB resets on every redeploy.
- `ffmpeg` for video → audio extraction. The Docker image and PaaS
  recipes install it; on bare metal, install it via your package
  manager.

---

## Docker Compose

The easy button.

```bash
git clone https://… whatslang
cd whatslang
cp .env.example .env
$EDITOR .env       # at minimum: WHATSAPP_BASE_URL, OPENAI_API_KEY
docker compose up --build -d
```

Now visit `http://localhost:8000`.

What `docker-compose.yml` does:

- Builds the multi-stage `Dockerfile` (Node 22 → Vite build, then
  Python 3.11-slim runtime with `ffmpeg`, `curl`, CA certs).
- Runs as user `appuser` (uid 1000), not root.
- Mounts a named volume `whatslang-data` at `/data` so SQLite survives
  upgrades.
- Sets `DB_PATH=/data/messages.db` automatically.
- Healthchecks `/health` every 30 s after a 40 s grace period.
- Caps log size at `10 MB × 3 files` per container.

### Useful commands

```bash
docker compose ps                  # status
docker compose logs -f             # tail
docker compose restart whatslang   # restart only the app
docker compose pull && docker compose up -d --build   # upgrade

# Backup the DB
docker compose exec whatslang \
  cp /data/messages.db /data/messages.$(date +%Y%m%d_%H%M%S).db
```

### Putting the WhatsApp gateway in the same compose

If you also run `whatsapp-mcp` via Compose, drop both into the same
`whatslang-network` and use the service name as the host:

```yaml
services:
  wa-gateway:
    image: ghcr.io/example/whatsapp-mcp:latest
    networks: [whatslang-network]
    # ... (volumes, ports, etc)

  whatslang:
    # ... existing block ...
    environment:
      - WHATSAPP_BASE_URL=http://wa-gateway:8081
      - DEVICE_ID=12345@s.whatsapp.net
    depends_on:
      - wa-gateway
```

---

## Plain Docker

If Compose isn't your thing:

```bash
docker build -t whatslang:latest .

docker volume create whatslang-data

docker run -d --name whatslang --restart unless-stopped \
  -p 8000:8000 \
  -e WHATSAPP_BASE_URL=http://host.docker.internal:8081 \
  -e DEVICE_ID=12345@s.whatsapp.net \
  -e OPENAI_API_KEY=sk-... \
  -e DASHBOARD_USER=admin \
  -e DASHBOARD_PASSWORD=please-change \
  -e SESSION_SECRET=$(openssl rand -hex 32) \
  -v whatslang-data:/data \
  whatslang:latest
```

The container always sets `DB_PATH=/data/messages.db` by default — keep
the `-v whatslang-data:/data` mount and the DB will persist across
upgrades.

---

## Nixpacks (Dokploy / Coolify / older Railway)

`nixpacks.toml` is committed and recognised automatically.

```toml
# Highlights — see nixpacks.toml for the full file.
[phases.setup]
nixPkgs = [
  "python311", "python311Packages.pip", "python311Packages.virtualenv",
  "nodejs_22", "ffmpeg-full", "curl", "cacert",
]

[phases.install]
cmds = [
  "python -m venv --copies /opt/venv",
  ". /opt/venv/bin/activate && pip install -r requirements.txt",
]
cacheDirectories = ["/root/.cache/pip"]

[phases.build]
cmds = [
  "cd web && npm ci --no-audit --no-fund",
  "cd web && npm run build",
]
cacheDirectories = ["web/node_modules", "/root/.npm"]

[start]
cmd = ". /opt/venv/bin/activate && python -m uvicorn app.main:app \
       --host 0.0.0.0 --port ${PORT:-8000} \
       --proxy-headers --forwarded-allow-ips '*'"

[variables]
DB_PATH = "/data/messages.db"
```

### Required platform configuration

- **Persistent volume** mounted at `/data` (e.g. Dokploy / Coolify
  "Volumes" section). Without it, your bot assignments and dedup table
  vanish on every redeploy.
- **Environment variables** — see [configuration.md](configuration.md).
- **Healthcheck path**: `/health` (HTTP 200).
- **Port**: `${PORT}` (the platform sets it; uvicorn picks it up).

---

## Railpack (modern Railway)

`railpack.json` is committed and recognised automatically.

```jsonc
{
  "$schema": "https://schema.railpack.com",
  "provider": "python",
  "packages": { "python": "3.11", "node": "22" },
  "steps": {
    "frontend:build": {
      "inputs": [
        { "step": "packages:mise" },
        { "local": true, "include": ["web"] }
      ],
      "caches": ["npm-install"],
      "commands": [
        "cd web && npm ci --no-audit --no-fund",
        "cd web && npm run build"
      ]
    }
  },
  "deploy": {
    "aptPackages": ["ffmpeg", "curl", "ca-certificates"],
    "inputs": [
      "...",
      { "step": "frontend:build", "include": ["web/dist"] }
    ],
    "variables": { "DB_PATH": "/data/messages.db" },
    "startCommand": "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips '*'"
  }
}
```

The `frontend:build` step is layered on top of the auto-detected
Python deploy image. `web/dist` is included in the final image; the
rest of `node_modules` is left behind.

### Required Railway settings

- **Volume** at `/data`.
- **Healthcheck** `GET /health`, expect 200.
- **Variables** — see [configuration.md](configuration.md).

---

## Bare metal / systemd

Useful when you have a VM you trust and don't want Docker.

### 1. Install OS deps

```bash
sudo apt-get install -y python3.11 python3.11-venv ffmpeg curl ca-certificates nodejs npm
```

(Adjust for your distro — `dnf`, `apk`, `pacman`.)

### 2. Clone & build

```bash
sudo useradd -r -m -d /opt/whatslang whatslang
sudo -u whatslang -i

git clone https://… /opt/whatslang/app
cd /opt/whatslang/app
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

cd web && npm ci && npm run build && cd ..

mkdir -p /opt/whatslang/data
cp .env.example /opt/whatslang/.env
$EDITOR /opt/whatslang/.env       # set DB_PATH=/opt/whatslang/data/messages.db
```

### 3. systemd unit

```ini
# /etc/systemd/system/whatslang.service
[Unit]
Description=Whatslang
After=network-online.target
Wants=network-online.target

[Service]
User=whatslang
WorkingDirectory=/opt/whatslang/app
EnvironmentFile=/opt/whatslang/.env
ExecStart=/opt/whatslang/app/.venv/bin/python -m uvicorn app.main:app \
          --host 0.0.0.0 --port 8000 \
          --proxy-headers --forwarded-allow-ips '*'
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/whatslang/data
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now whatslang
sudo systemctl status whatslang
journalctl -u whatslang -f
```

---

## Reverse proxy

You can serve directly on port 8000, but most setups put a TLS-capable
proxy in front.

### Caddy

```caddyfile
whatslang.example.com {
    encode zstd gzip
    reverse_proxy localhost:8000
}
```

That's it — Caddy auto-acquires a Let's Encrypt cert.

### nginx

```nginx
server {
    listen 443 ssl http2;
    server_name whatslang.example.com;

    ssl_certificate     /etc/letsencrypt/live/whatslang/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/whatslang/privkey.pem;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_buffering    off;
        client_max_body_size 25m;
    }
}
```

### Traefik (Docker labels)

```yaml
labels:
  - traefik.enable=true
  - traefik.http.routers.whatslang.rule=Host(`whatslang.example.com`)
  - traefik.http.routers.whatslang.entrypoints=websecure
  - traefik.http.routers.whatslang.tls.certresolver=letsencrypt
  - traefik.http.services.whatslang.loadbalancer.server.port=8000
```

> The Dockerfile already starts uvicorn with
> `--proxy-headers --forwarded-allow-ips '*'`, so `X-Forwarded-Proto`
> is honored automatically. The session cookie is marked `secure` when
> `ENVIRONMENT=production`.

---

## Healthchecks

| Path | Expected | Notes |
|---|---|---|
| `/health`, `/api/health` | `{"status":"healthy", ...}` 200 | Cheap, always returns once the app is listening. |
| `/api/ready` | `{"status":"ready", ...}` 200 | Same as `/health` today, kept distinct for k8s readiness vs liveness. |
| `/api/diagnostics` | full snapshot 200 | Heavier — pings the gateway. Don't use as your liveness probe. |

---

## Upgrades

In all setups (Docker, Compose, PaaS), upgrades amount to:

1. Pull the new code / image.
2. Re-deploy.
3. The `lifespan` migrates the DB (idempotent `ALTER TABLE`s) and
   resumes any `running=1` bot assignments. No manual migration step.

Keep a snapshot of `data/messages.db` before major upgrades:

```bash
make backup           # bare metal
docker compose exec whatslang sh -c 'cp /data/messages.db /data/messages.$(date +%s).db'
```

---

## Resource sizing

A starting point — adjust based on your number of bots and chats.

| Workload | CPU | RAM | Disk |
|---|---|---|---|
| Tiny (1–5 chats, 1–2 bots) | 0.25 vCPU | 256 MB | 1 GB |
| Small (10–50 chats, 5 bots) | 0.5 vCPU | 512 MB | 2 GB |
| Medium (200 chats, 20 bots) | 1 vCPU | 1 GB | 5 GB |
| Large | 2+ vCPU | 2+ GB | 10 GB+ |

The biggest variable is your LLM provider — most CPU/RAM goes to
network IO and JSON parsing.
