"""Regression tests for security-relevant behaviour.

These cover every issue the security audit found (see ``docs/security.md``)
so a future change can't silently regress them.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# 1. Path traversal in the SPA static handler
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "path",
    [
        "/../../../../../../etc/passwd",
        "/foo/../../../../../../etc/passwd",
        # URL-encoded ../ — the regression that previously slipped through.
        "/%2E%2E%2F%2E%2E%2F%2E%2E%2F%2E%2E%2F%2E%2E%2F%2E%2E%2Fetc%2Fpasswd",
        "/%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        # Backslashes / null bytes — clients normalise these in different
        # ways; what matters is the response body, not the status.
        "/..%5C..%5Cetc%5Cpasswd",
        "/foo%00../etc/passwd",
    ],
)
def test_spa_does_not_serve_files_outside_web_dist(client: TestClient, path: str):
    """Whatever the encoding, the SPA fallback must NEVER serve content
    from outside ``web/dist``.

    Two acceptable outcomes:

    - ``200`` carrying the SPA index (HTTP client / Starlette delivered
      the request to the SPA fallback, which returned ``index.html``).
    - ``404`` (the client/router collapsed the path before it ever
      reached our handler — also safe; nothing leaked).

    The unsafe outcome is any ``2xx`` whose body looks like ``/etc/passwd``
    or any other off-disk file. We check that explicitly.
    """
    res = client.get(path)
    assert res.status_code in (200, 404), f"{path}: {res.status_code}"
    body = res.text
    # /etc/passwd line shape: ``user:x:uid:gid:gecos:/home:/bin/sh``.
    # If any of these tokens leak into the body, traversal succeeded.
    assert "root:" not in body, f"path {path} leaked /etc/passwd"
    assert ":/bin/" not in body, f"path {path} leaked /etc/passwd"
    assert "/sbin/nologin" not in body, f"path {path} leaked /etc/passwd"
    if res.status_code == 200:
        # Should be the SPA index — fingerprint the test fixture's body.
        assert "<!doctype html>" in body.lower()
        assert "test-spa" in body


# ---------------------------------------------------------------------------
# 2. Auth is required for state-changing endpoints
# ---------------------------------------------------------------------------

def test_unauthenticated_requests_get_401(client: TestClient):
    # Sample a few different routers / methods.
    for method, path in [
        ("get", "/api/system"),
        ("get", "/api/stats"),
        ("get", "/api/diagnostics"),
        ("get", "/api/chats"),
        ("get", "/api/bots"),
        ("post", "/api/chats"),
        ("delete", "/api/chats/12345@s.whatsapp.net"),
    ]:
        res = client.request(method, path, json={"chat_jid": "12345@s.whatsapp.net"})
        assert res.status_code == 401, f"{method.upper()} {path} returned {res.status_code}"


def test_health_endpoints_remain_public(client: TestClient):
    # Orchestrators need these without credentials.
    for path in ("/health", "/ready", "/api/health", "/api/ready"):
        res = client.get(path)
        assert res.status_code == 200, path


# ---------------------------------------------------------------------------
# 3. Login throttle
# ---------------------------------------------------------------------------

def test_login_throttle_locks_after_repeated_failures(client: TestClient):
    payload = {"user": "admin", "password": "wrong"}
    last = None
    for _ in range(6):  # default threshold is 5
        last = client.post("/api/auth/login", json=payload)
    assert last is not None
    assert last.status_code in (401, 429), last.status_code
    # The very next attempt (any password) must be 429.
    res = client.post("/api/auth/login", json={"user": "admin", "password": "test-password-12345"})
    assert res.status_code == 429
    assert "Retry-After" in res.headers


def test_successful_login_clears_throttle(client: TestClient):
    # A few failures…
    for _ in range(3):
        client.post("/api/auth/login", json={"user": "admin", "password": "wrong"})
    # …then a real one resets the bucket.
    res = client.post("/api/auth/login", json={"user": "admin", "password": "test-password-12345"})
    assert res.status_code == 200
    # We can still keep failing after that without hitting the lock immediately.
    for _ in range(4):
        client.post("/api/auth/login", json={"user": "admin", "password": "wrong"})
    res = client.post("/api/auth/login", json={"user": "admin", "password": "wrong"})
    assert res.status_code == 401  # not yet 429


# ---------------------------------------------------------------------------
# 4. JID validation (SSRF defence)
# ---------------------------------------------------------------------------

def _login(client: TestClient) -> None:
    res = client.post("/api/auth/login", json={"user": "admin", "password": "test-password-12345"})
    assert res.status_code == 200, res.text


@pytest.mark.parametrize(
    "bad_jid",
    [
        "not-a-jid",
        "../../../etc/passwd",
        "x@evil.com",  # domain not on allow-list
        "x@s.whatsapp.net/extra",
        "x@.s.whatsapp.net",
        "@s.whatsapp.net",
        "",
        " " * 5,
        "x" * 250 + "@s.whatsapp.net",
    ],
)
def test_jid_validation_rejects_malformed_input(client: TestClient, bad_jid: str):
    _login(client)
    # Add chat
    res = client.post("/api/chats", json={"chat_jid": bad_jid})
    assert res.status_code in (400, 422), f"{bad_jid!r} returned {res.status_code}"
    # Bulk action — must reject the whole batch
    res = client.post(
        "/api/chats/bulk",
        json={"action": "delete_chats", "chat_jids": [bad_jid]},
    )
    assert res.status_code in (400, 422), f"bulk: {bad_jid!r} returned {res.status_code}"


@pytest.mark.parametrize(
    "good_jid",
    [
        "12345@s.whatsapp.net",
        "12345:1@s.whatsapp.net",
        "120363025@g.us",
        "abcdef.user@c.us",
    ],
)
def test_jid_validation_accepts_well_formed(client: TestClient, good_jid: str):
    _login(client)
    res = client.post("/api/chats", json={"chat_jid": good_jid, "chat_name": "x"})
    assert res.status_code in (200, 201), res.text


@pytest.mark.parametrize(
    "bad_path_jid",
    [
        # No `@server` part at all.
        "not-a-jid",
        # Domain not on the allow-list.
        "12345@evil.example.com",
        # Garbage characters.
        "12345%20unsafe@s.whatsapp.net",
    ],
)
def test_path_jid_is_validated_too(client: TestClient, bad_path_jid: str):
    """The {chat_jid} path parameter is interpolated into URLs that hit the
    WhatsApp gateway. Anything not matching the strict allow-list must be
    rejected before that interpolation happens."""
    _login(client)
    res = client.get(f"/api/chats/{bad_path_jid}")
    # Either 400 (our validator) or 422 (FastAPI's max_length).
    assert res.status_code in (400, 422), f"{bad_path_jid!r}: {res.status_code}"


# ---------------------------------------------------------------------------
# 5. CORS hardening
# ---------------------------------------------------------------------------

def test_cors_wildcard_drops_credentials(app_factory, monkeypatch):
    monkeypatch.setattr("app.main.WhatsAppClient", lambda *a, **k: None)
    monkeypatch.setattr("app.main.LLMService", lambda *a, **k: None)
    app = app_factory(ALLOWED_ORIGINS="*")
    # The starlette CORS middleware must NOT echo allow-credentials for *
    # We can introspect via a preflight OPTIONS request:
    with TestClient(app) as c:
        res = c.options(
            "/api/auth/status",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "GET",
            },
        )
        # The middleware should refuse to set Access-Control-Allow-Credentials
        # when the configured origin list is wildcarded.
        assert res.headers.get("access-control-allow-credentials") != "true"


# ---------------------------------------------------------------------------
# 6. Production refuses insecure boot
# ---------------------------------------------------------------------------

def test_production_refuses_empty_password(app_factory, monkeypatch):
    monkeypatch.setattr("app.main.WhatsAppClient", lambda *a, **k: None)
    monkeypatch.setattr("app.main.LLMService", lambda *a, **k: None)
    with pytest.raises(RuntimeError, match="DASHBOARD_PASSWORD is empty"):
        app_factory(ENVIRONMENT="production", DASHBOARD_PASSWORD="")


def test_production_refuses_empty_session_secret(app_factory, monkeypatch):
    monkeypatch.setattr("app.main.WhatsAppClient", lambda *a, **k: None)
    monkeypatch.setattr("app.main.LLMService", lambda *a, **k: None)
    with pytest.raises(RuntimeError, match="SESSION_SECRET is empty"):
        app_factory(
            ENVIRONMENT="production",
            DASHBOARD_PASSWORD="a-real-password-12345",
            SESSION_SECRET="",
        )


def test_production_refuses_wildcard_cors(app_factory, monkeypatch):
    monkeypatch.setattr("app.main.WhatsAppClient", lambda *a, **k: None)
    monkeypatch.setattr("app.main.LLMService", lambda *a, **k: None)
    with pytest.raises(RuntimeError, match="ALLOWED_ORIGINS"):
        app_factory(ENVIRONMENT="production", ALLOWED_ORIGINS="*")


# ---------------------------------------------------------------------------
# 7. Body-size guard
# ---------------------------------------------------------------------------

def test_body_size_limit(client: TestClient):
    _login(client)
    huge = "x" * (2 * 1024 * 1024)
    res = client.post("/api/chats", json={"chat_jid": "12345@s.whatsapp.net", "chat_name": huge})
    assert res.status_code == 413


# ---------------------------------------------------------------------------
# 8. Cookie attributes
# ---------------------------------------------------------------------------

def test_session_cookie_is_httponly_and_samesite_strict(client: TestClient):
    res = client.post(
        "/api/auth/login", json={"user": "admin", "password": "test-password-12345"}
    )
    assert res.status_code == 200
    set_cookie = res.headers.get("set-cookie", "")
    assert "whatslang_session=" in set_cookie
    lower = set_cookie.lower()
    assert "httponly" in lower
    assert "samesite=strict" in lower
    assert "path=/" in lower


# ---------------------------------------------------------------------------
# 9. Security headers
# ---------------------------------------------------------------------------

def test_security_headers_are_set(client: TestClient):
    res = client.get("/api/health")
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"
    assert res.headers.get("referrer-policy") == "no-referrer"
    assert "permissions-policy" in res.headers


# ---------------------------------------------------------------------------
# 10. Error messages don't leak internals
# ---------------------------------------------------------------------------

def test_runtime_error_is_redacted(client: TestClient, monkeypatch):
    """The RuntimeError exception handler must replace the message body
    with a generic one; original exception text routinely leaks paths or
    env-var names."""
    _login(client)

    # Force a RuntimeError deep inside the dependency graph by breaking
    # something the /api/stats endpoint always touches.
    from app.db import Database

    def boom(*_a, **_kw):
        raise RuntimeError(
            "super-secret internal path: /opt/whatslang/secrets.env"
        )

    monkeypatch.setattr(Database, "count_chats", boom)
    res = client.get("/api/stats")
    assert res.status_code == 500, res.text
    assert "super-secret" not in res.text
    assert "secrets.env" not in res.text
    assert "/opt/whatslang" not in res.text


# ---------------------------------------------------------------------------
# 11. Open mode (auth disabled): documented behaviour
# ---------------------------------------------------------------------------

def test_open_mode_is_open_but_warns(open_client: TestClient):
    # When DASHBOARD_PASSWORD is empty in dev, /api/auth/status reports it.
    res = open_client.get("/api/auth/status")
    assert res.status_code == 200
    body = res.json()
    assert body["auth_required"] is False


# ---------------------------------------------------------------------------
# 12. DB file permissions
# ---------------------------------------------------------------------------

def test_db_file_permissions_are_restricted(client: TestClient, tmp_path: Path):
    # Triggering any DB-touching request creates the file.
    _login(client)
    client.get("/api/chats")
    # Walk the data dir created by the lifespan handler. We can't easily
    # introspect the path the test fixture used, so just check every *.db
    # file in the repo's data dir set up by the fixture.
    import os
    import stat

    db_files = list(Path(os.environ["DB_PATH"]).parent.glob("*.db"))
    assert db_files, "DB file should exist after request"
    for f in db_files:
        mode = stat.S_IMODE(f.stat().st_mode)
        # Allow either 0o600 or 0o644 on filesystems that can't enforce
        # owner-only (some Windows mounts), but flag world-write.
        assert (mode & 0o002) == 0, f"{f} is world-writable: {oct(mode)}"
