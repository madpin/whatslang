# Security policy

Whatslang is a self-hosted service that automates a personal WhatsApp
account and reads/writes from an upstream LLM provider. The blast radius of
a compromise is therefore real:

- An attacker with API access can **read every chat** the gateway can see,
  **send messages** as the connected WhatsApp account, and **spend OpenAI
  credits** through the configured key.
- The same attacker can **redirect bot output** to any chat already known
  to the system and **delete chats** stored in the local database.

This document describes how Whatslang protects against that, what you must
do as an operator, and how to report new findings.

## Hardening summary

The default codebase enforces:

| Concern | Defence |
| --- | --- |
| Authentication | Single-user, env-driven (`DASHBOARD_USER` / `DASHBOARD_PASSWORD`). HMAC-SHA256-signed session cookies. Constant-time credential comparison. |
| Brute force | Per-IP login throttle (5 failures / 60 s → 5 min lock-out). |
| Session cookie | `HttpOnly`, `SameSite=Strict`, `Secure` in production. |
| CSRF | `SameSite=Strict` blocks cookie attachment on cross-site requests; CORS refuses credentialed wildcard. |
| CORS | `ALLOWED_ORIGINS=*` is incompatible with credentialed sessions and is automatically downgraded; production refuses to boot with it. |
| Path traversal (SPA) | The static fallback resolves the request path and rejects anything outside `web/dist/`. |
| SSRF via `chat_jid` | `chat_jid` is validated against an allow-list of WhatsApp servers (`s.whatsapp.net`, `g.us`, `c.us`, `broadcast`, `newsletter`, `lid`) before it ever reaches the gateway URL. |
| SQL injection | All queries are parameterised; `ORDER BY` / sort columns are validated against an allow-list. |
| Body-size DoS | 1 MiB request-body cap enforced in middleware. |
| Argument injection | `ffmpeg-python` runs with an explicit argv list (no `shell=True`) and only on temp files we write ourselves. |
| Information leakage | API exception bodies are redacted in production; full detail is logged server-side. `/api/docs` / `/api/openapi.json` are disabled in production. |
| Insecure boot | When `ENVIRONMENT=production`, the service refuses to start with an empty `DASHBOARD_PASSWORD`, an empty `SESSION_SECRET`, or `ALLOWED_ORIGINS=*`. |
| Filesystem | The `data/` directory is created with mode `0o700`; the SQLite file is `0o600`. |
| HTTP headers | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, restrictive `Permissions-Policy`, plus HSTS in production. |

See [`docs/security.md`](docs/security.md) for the full threat model and
the rationale behind each control.

## Operator checklist

Before exposing Whatslang to anything beyond `localhost`:

1. **Set a long `DASHBOARD_PASSWORD`** (≥ 12 chars; we warn under and refuse
   to start in production with it empty).
2. **Set a stable `SESSION_SECRET`** of at least 32 random bytes:
   ```bash
   python -c 'import secrets; print(secrets.token_urlsafe(48))'
   ```
3. **Run with `ENVIRONMENT=production`** — this disables the API docs,
   enables HSTS, marks cookies as `Secure`, and turns the security
   warnings into hard boot failures.
4. **Restrict `ALLOWED_ORIGINS`** to the exact origin(s) hosting the
   dashboard. Never use `*` in production.
5. **Terminate TLS upstream** (Caddy, Nginx, Traefik, your PaaS). The
   `Secure` cookie flag is meaningless without HTTPS.
6. **Do not publish the `data/` directory.** It contains transcript
   excerpts of real WhatsApp messages.
7. **Bind to a private interface** when possible (`HOST=127.0.0.1`) and
   put the service behind your own auth proxy if you need multi-user
   access.
8. **Rotate the OpenAI key** if it ever appears in a log line, error
   message, or backup that left the host.

## Threat model

Out of scope (operator's responsibility):

- Compromise of the host running Whatslang (root on the box trumps every
  in-app control).
- Compromise of the upstream WhatsApp gateway or the LLM provider.
- Side-channel timing on the LLM provider.
- Browser exploits against logged-in admins.

In scope (the codebase tries to defend against):

- Any unauthenticated network attacker with TCP access to the service.
- An authenticated, malicious admin trying to abuse undocumented endpoints
  (we expose the same surface we document).
- A logged-out attacker brute-forcing the password.
- A cross-site attacker tricking a logged-in admin into making
  state-changing requests.

## Reporting a vulnerability

Please **do not file public issues** for suspected vulnerabilities.

Instead, email **security@whatslang.invalid** with:

- A description of the issue and its impact.
- Steps to reproduce (a minimal `curl` is ideal).
- Your suggested fix, if you have one.

We aim to:

- Acknowledge within 3 business days.
- Provide a fix or mitigation within 30 days for high-severity issues.
- Credit you in the release notes (opt-out available).
