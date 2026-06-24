# Troubleshooting

> When in doubt, open `/diagnostics` first — most problems are visible
> on that page in less than 5 seconds.

This page is symptom → cause → fix. Keep it on standby when something
breaks.

---

## Quick triage

| Where to look | What it tells you |
|---|---|
| `/diagnostics` page | Gateway, LLM, DB, bot runtime, recent gateway errors. |
| `GET /api/health` | The process is up. |
| `GET /api/system` | Configuration the process actually loaded. |
| Per-bot **Logs** modal | Why a specific bot did or did not reply. |
| `docker compose logs -f whatslang` | Everything the process printed. |
| `data/messages.db` | Source of truth for chats, assignments, and dedup. |

---

## "I can't log in"

| Symptom | Most likely cause | Fix |
|---|---|---|
| Login page rejects valid creds | `DASHBOARD_USER`/`DASHBOARD_PASSWORD` got wrapped in quotes in `.env` | Quotes are part of the value — remove them. |
| Login works, then immediately bounces back | `SESSION_SECRET` is empty and the worker just restarted | Set `SESSION_SECRET` to a long random string so cookies survive restarts (`python -c 'import secrets; print(secrets.token_hex(32))'`). |
| Login redirects to `/login` over HTTPS but works on HTTP | Cookie has `secure=true` (because `ENVIRONMENT=production`) but the proxy is sending plain HTTP | Either set `ENVIRONMENT=development` or terminate TLS and pass `X-Forwarded-Proto: https`. The Dockerfile already sets `--proxy-headers --forwarded-allow-ips '*'`, so most proxies need no extra config. |
| No login page shown at all | `DASHBOARD_PASSWORD` is empty | That's by design — auth is disabled. Set both `DASHBOARD_USER` and `DASHBOARD_PASSWORD` to enable it. |

---

## "Bots aren't replying"

Walk down this checklist.

### 1. Is the gateway reachable?

Open `/diagnostics`. Look at the **WhatsApp gateway** card.

- **Reachable: false / latency_ms missing** → wrong `WHATSAPP_BASE_URL`,
  network issue, or the gateway crashed. Confirm with `curl
  $WHATSAPP_BASE_URL/chats`.
- **Reachable but Logged in: false** → the gateway lost its WhatsApp
  session. Re-link it (QR code, etc).
- **Recent errors** in the bottom panel → look at the most recent ones;
  they include the endpoint and the status code.

### 2. Is the bot actually running?

Open the chat detail page. Each bot card shows a green or grey dot.

- **Grey** → click **Start**.
- **Green but no replies** → continue.

### 3. Is the LLM key valid?

Open the bot's **Logs** modal. Look for the most recent entry — if
the LLM call failed, you'll see a clear error like
`Error code: 401 - Incorrect API key…`.

- **401 / 403** → rotate `OPENAI_API_KEY`, restart.
- **404 model not found** → check `OPENAI_MODEL` (and `OPENAI_VISION_MODEL`,
  `OPENAI_AUDIO_MODEL`). Some providers use different model IDs.
- **429** → you're rate-limited. The runner will retry on the next
  poll cycle.
- **Connection refused** → wrong `OPENAI_BASE_URL`.

### 4. Is the message getting filtered out?

The runner ignores:

- Messages with no `id` field (rare; gateway bug).
- Messages already in `processed_messages` for that bot.
- Empty messages (no text, no media).
- Messages from other bots (start with `[xxx]`).
- Messages from your own device when **answer_owner_messages** is off.

If you're testing by sending yourself a message, set
**Answer my own messages = on** in the bot settings.

### 5. The first message I send after starting a bot is ignored

That's intentional. On its first tick the runner marks the most recent
~20 messages as already-processed so you don't get a flood of replies
to old messages. Send a *new* message after that and it'll be picked up.

---

## "Bot replies are showing up in the wrong chat"

You've set **Send replies to another chat** for that bot. Open the
settings modal and clear the field (send an empty string via the API,
or delete and re-save in the UI).

`PUT /api/bots/{name}/settings?chat_jid=…` with `{"response_chat_jid": ""}`.

---

## "Bot keeps replying to its own replies"

The runner heuristic skips messages that start with `[xxx]` in their
first 20 chars. If you wrote a custom bot whose `prefix` doesn't match
that shape (e.g. `prefix="🤖 "`), other bots may answer it.

**Fix:** keep prefixes `[xxx]`-shaped (e.g. `[bot]`, `[ai]`,
`[summary]`).

---

## "I see duplicate replies"

Possible causes:

- You started two different bots that both reply to the same message.
  Stop the one you don't want — bot dedup is per `(message_id,
  bot_name)`, not global.
- You ran two Whatslang processes against the same DB. Don't — they'll
  both poll the same chats and both reply. SQLite is single-writer for
  this reason.
- Something polled `POST /api/bots/{name}/start` repeatedly. The
  `BotManager` is idempotent, but a thread is created at most once per
  pair, so this is rarely the actual cause.

Check `data/messages.db` for stray rows in `processed_messages` —
or just delete and resync.

---

## "Audio/video bots return 'couldn't transcribe'"

| Cause | Fix |
|---|---|
| `OPENAI_AUDIO_MODEL` is empty or invalid | Set to `whisper-1` (OpenAI) or your provider's equivalent. |
| The video has no audio track | Hard limit. The bot replies with a friendly error and stops. |
| Audio > 25 MB after extraction (or video > 100 MB) | Split the source clip — see the limits in [bots.md](bots.md#the-mediamode-enum). |
| `ffmpeg` isn't installed | The Docker image and PaaS recipes install it. On bare metal, `apt-get install -y ffmpeg`. |

---

## "Image bots return 'couldn't analyse'"

- The model in `OPENAI_VISION_MODEL` (or `OPENAI_MODEL`) doesn't
  support vision. Use `gpt-4o`, `gpt-4o-mini`, or your provider's
  vision-capable equivalent.
- The gateway's `download_image` returned empty. Watch the logs — if
  it says `Couldn't download the image`, the gateway is the issue.
- If the gateway says `failed to download media: no url present`, the
  stored media row is not decryptable through GoWA. This commonly affects
  media-only messages sent by the logged-in WhatsApp account; Whatslang
  skips those rows and handles owner captions as text.

---

## "Diagnostics shows the gateway is fine, but bots still time out"

Check the gateway's **own** logs — Whatslang only sees the surface.
Common gateway-side issues: rate limit from WhatsApp, missing
permissions for a group, or a stale device session that needs
re-pairing.

---

## "I redeployed and lost all my bot assignments"

You forgot to mount the volume.

- **Docker Compose**: the volume `whatslang-data` is named in
  `docker-compose.yml`. Don't `docker compose down -v` unless you mean it.
- **Plain Docker**: pass `-v whatslang-data:/data`.
- **PaaS**: configure a persistent volume mounted at `/data` and set
  `DB_PATH=/data/messages.db` (the recipes do this for you).
- **Bare metal**: `DB_PATH=/opt/whatslang/data/messages.db` and back up
  that file with `make backup`.

If you have a backup, just stop the service, replace `messages.db` with
your snapshot, and start. Assignments and dedup return.

---

## "The dashboard shows the right config but bots use stale settings"

The `Settings` instance is LRU-cached for the process lifetime. To
pick up new env-var values, **restart the process** (`docker compose
restart`, `make docker-restart`, or your platform's "redeploy" button).

---

## "ALTER TABLE failures on boot"

Probably a partial migration from a very old schema. The `db.py`
migrations use `with contextlib.suppress(sqlite3.OperationalError):`
for additive `ALTER TABLE`s, so they're safe to re-run.

If you actually see errors:

1. Stop the app.
2. `cp data/messages.db data/messages.db.bak`.
3. Open the DB with `sqlite3 data/messages.db` and inspect with
   `.schema bot_chat_assignments`. The expected columns are:
   `id, bot_name, chat_jid, running, answer_owner_messages,
   context_message_count, response_chat_jid, created_at`.
4. Add any missing column manually (`ALTER TABLE
   bot_chat_assignments ADD COLUMN <name> <type>`).
5. Restart.

For very old installs that still have an `enabled` column instead of
`running`: `ALTER TABLE bot_chat_assignments RENAME COLUMN enabled TO
running;`. The app does this automatically too.

---

## "I get CORS errors in the browser"

Only relevant if you're hosting the SPA on a different origin (rare —
by default FastAPI hosts the built SPA itself).

Set `ALLOWED_ORIGINS` to a comma-separated list of allowed origins.
`*` is allowed but disables credentialed requests, so the cookie won't
send. Use exact origins instead.

---

## "Healthcheck keeps failing in Docker"

- The container is genuinely down — `docker compose logs whatslang`.
- The app is up but bound to `127.0.0.1`. The Docker default in this
  repo is `0.0.0.0`, but if you overrode `HOST`, change it back.
- The container has no `curl` (e.g. you built a custom image without
  it). Add `curl` to your runtime image — the official Dockerfile
  installs it.

---

## "I want to start over"

```bash
# Compose
docker compose down -v       # WARNING: deletes the SQLite volume

# Bare metal
sudo systemctl stop whatslang
rm /opt/whatslang/data/messages.db
sudo systemctl start whatslang
```

Whatslang creates a fresh DB, runs the migrations, and waits for you
to sync chats again.

---

## Still stuck?

1. Reproduce with `LOG_LEVEL=DEBUG`.
2. Capture `/api/diagnostics` output.
3. Copy the affected bot's logs from the in-app modal or via `GET
   /api/bots/{name}/logs`.
4. File an issue with all three.
