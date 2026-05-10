# Security model

This is the long-form companion to [`SECURITY.md`](../SECURITY.md). It
walks through the threat model, the controls Whatslang ships with, and
the operational decisions you still own.

## What an attacker with API access can do

Whatslang is glue: it joins a personal WhatsApp account (via a gateway)
to an LLM (OpenAI / LiteLLM-compatible) and exposes a small admin REST
API. Anyone with credentialed HTTP access to the admin API can:

- Read the local copy of every chat the gateway has synced.
- List, start, stop and delete bots on any chat.
- **Send messages as the connected WhatsApp account** by adding a chat,
  attaching a bot, and triggering a reply.
- **Redirect a bot's output to any chat already known to the system**
  (so an attacker can also add a chat first and then redirect).
- Spend money on the configured OpenAI key.
- Read the local SQLite file by reading the `/api/diagnostics` endpoint
  (path + size, not contents).

Anyone with **unauthenticated** access additionally:

- Sees `/api/health`, `/api/ready`, the bundled SPA, and the favicon.
  Everything else returns 401.

The two important conclusions:

1. The **session cookie is the only thing standing between the public
   internet and the items above**, so the cookie's authenticity, secrecy
   and CSRF properties matter a lot.
2. The **password is the entire identity layer**, so brute-force,
   credential-stuffing and timing attacks are the main risk to authn.

## Defences in the codebase

### Authentication

- Single-user, env-driven: `DASHBOARD_USER` (default `admin`) and
  `DASHBOARD_PASSWORD`.
- Constant-time comparison via `hmac.compare_digest` so timing leaks
  don't betray which character was wrong.
- Sessions are HMAC-SHA256-signed cookies — no DB row, no JWT library,
  nothing to revoke beyond rotating `SESSION_SECRET`.
- Login throttling (`app.security.LoginThrottle`): 5 failures in 60 s
  trigger a 5-minute lockout per client IP. Successful logins clear the
  bucket. The state is in-memory and per-process.

### Cookie & CSRF

- `HttpOnly` so JavaScript can't exfiltrate the session.
- `SameSite=Strict` so the cookie is never attached to cross-site
  requests. This kills the CSRF vector for state-changing endpoints
  without needing a token.
- `Secure` when `ENVIRONMENT=production` so cookies don't ride plain
  HTTP.
- `Path=/` so the cookie is sent for every API call but not, e.g., for
  unrelated apps on different paths.

### CORS

- The middleware is configured at app-build time. If `ALLOWED_ORIGINS`
  contains `*`, **`Access-Control-Allow-Credentials` is forcibly set to
  `false`** to match the Fetch spec. Browsers refuse credentialed
  cross-origin requests with a wildcard origin anyway, so doing this
  explicitly avoids surprises in non-browser API clients.
- Production refuses to boot with `ALLOWED_ORIGINS=*`.

### Path traversal (CVE-class)

The earlier SPA fallback used `WEB_DIST / full_path` and served any file
that existed. With URL-encoded `..%2F` segments an unauthenticated caller
could read `/etc/passwd` (or any file readable by the process). The fix
in `app.security.safe_static_path`:

1. Rejects absolute / null-byte / backslash inputs up-front.
2. Resolves the join via `Path.resolve(strict=False)`.
3. Calls `relative_to(WEB_DIST.resolve())` and rejects on `ValueError`.
4. Only serves regular files that pass.

The regression is locked down with multiple parametrised tests in
`tests/test_security.py::test_spa_does_not_serve_files_outside_web_dist`.

### SSRF defence around `chat_jid`

`chat_jid` is interpolated into URLs that go to the WhatsApp gateway
(e.g. `GET {gateway}/chat/{chat_jid}/messages`,
`GET {gateway}/message/{id}/download?phone={chat_jid}`). Without
validation, a request like `/api/chats/foo%2F..%2Fadmin` would let a
caller probe arbitrary gateway endpoints.

`app.security.is_valid_chat_jid` enforces a strict regex over the user
part and an **allow-list** of WhatsApp servers (`s.whatsapp.net`,
`g.us`, `c.us`, `broadcast`, `newsletter`, `lid`). The validator is
applied in:

- The `AddChatRequest` Pydantic schema.
- The `BulkActionRequest` Pydantic schema (every entry).
- The `BotSettingsUpdate.response_chat_jid` validator.
- The `valid_chat_jid_path` dependency, used on every `/api/chats/{chat_jid}`
  and `/api/bots/{bot_name}/...?chat_jid=...` route.

### SQL injection

All queries use parameterised `?` placeholders. The dynamic SQL in
`Database._build_chat_query` interpolates only:

- The `select` clause (built from a literal allow-list inside the same
  function).
- The `sort_by` column, validated against
  `{"last_message_time", "chat_name", "message_count", "added_at"}`.
- The `order` direction, normalised to `ASC`/`DESC`.
- The literal `chat_type` / `bot_status` / `activity` values are compared
  against `==` constants.

Search uses `LIKE ?` with a parameter-bound `%search%`, so SQL injection
is impossible; the `%`/`_` LIKE wildcards aren't escaped, which means an
operator can do prefix scans but not extract data they couldn't already
read by other means.

### Body-size DoS

The 1 MiB request-body limit is enforced in middleware before any router
sees the payload. Bot/chat payloads are tiny JSON; media never flows
through this app — the gateway streams it.

### Argument injection / RCE via media

`ffmpeg-python` constructs an `argv` list and runs the subprocess
without `shell=True`. The temp file paths it sees come from
`tempfile.NamedTemporaryFile` and `tempfile.mkstemp`, never from user
input.

### Information leakage

- The `RuntimeError` exception handler logs the full exception
  server-side and returns a generic `"Internal error"` to the client.
- `/api/docs`, `/api/redoc` and `/api/openapi.json` are disabled in
  production.
- `/api/diagnostics` and `/api/system` only run after `require_auth`.
- HTTP error messages avoid echoing user-supplied identifiers (e.g.
  `"Unknown bot"` instead of `f"Unknown bot: {bot_name}"`).

### Filesystem hygiene

- `data/` is created with mode `0o700` so other users on the host can't
  read the SQLite file or the WAL.
- The `*.db` file itself is `chmod 0o600` after creation.
- `.gitignore` and `.dockerignore` both exclude `.env`, `data/`, and
  every database extension.

### HTTP headers

Every response gets:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: accelerometer=(), camera=(), geolocation=(), microphone=(), payment=()`

In production, also:

- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

### Insecure-boot guard

`Settings.security_check` (called from `create_app`) inspects the
configuration at startup. In `ENVIRONMENT=production` it raises and the
service refuses to start when:

- `DASHBOARD_PASSWORD` is empty.
- `SESSION_SECRET` is empty.
- `ALLOWED_ORIGINS=*`.

In development the same checks log a single, prominent warning.

## Things you still own as the operator

- **TLS termination.** Whatslang itself does not terminate TLS. Run it
  behind Caddy, Nginx, Traefik or your PaaS. Without HTTPS the `Secure`
  cookie flag is meaningless and the password rides plain text.
- **Network exposure.** Prefer binding to `127.0.0.1` and tunnelling, or
  putting the service on a private network. `HOST=0.0.0.0` is the
  default for container ergonomics; pair it with the password and a TLS
  proxy.
- **Backups.** The `data/` directory contains real WhatsApp content.
  Treat it like the rest of your secrets.
- **Provider key hygiene.** Rotate `OPENAI_API_KEY` if it ever shows up
  in a log line, error message, screenshot or shared notebook.
- **Multi-user.** Whatslang has one account. If you need granular roles,
  put a real auth proxy (oauth2-proxy, Cloudflare Access, …) in front.

## Tests that lock the model in

Everything in this document is exercised by `tests/test_security.py`.
That file deliberately does not use mocks for the controls themselves —
it boots the real FastAPI app and hits the real routes — so a future
refactor can't silently regress them.

```bash
source .venv/bin/activate
pytest tests/test_security.py
```
