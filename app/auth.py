"""Single-user, env-based authentication with signed session cookies.

Goals:
- The username and password come from `DASHBOARD_USER` / `DASHBOARD_PASSWORD`.
- If `DASHBOARD_PASSWORD` is empty, the dashboard is fully open.
- A login produces an HMAC-signed session cookie. No DB, no JWT lib needed.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, Request, status

from app.config import Settings, get_settings

SESSION_COOKIE = "whatslang_session"


@dataclass(frozen=True)
class Session:
    user: str
    issued_at: int
    expires_at: int


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64u_decode(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def _secret(settings: Settings) -> bytes:
    if settings.session_secret:
        return settings.session_secret.encode()
    # Cache a stable per-process secret if none is configured.
    # Token length: 32 random bytes = 256 bits, sufficient for HMAC-SHA256.
    global _RUNTIME_SECRET
    if not _RUNTIME_SECRET:
        _RUNTIME_SECRET = secrets.token_bytes(32)
    return _RUNTIME_SECRET


_RUNTIME_SECRET: bytes = b""


def issue_token(user: str, settings: Optional[Settings] = None) -> tuple[str, int]:
    """Return (cookie_value, max_age_seconds)."""
    s = settings or get_settings()
    now = int(time.time())
    expires = now + s.session_max_age_seconds
    payload = f"{user}:{now}:{expires}".encode()
    sig = hmac.new(_secret(s), payload, hashlib.sha256).digest()
    token = f"{_b64u(payload)}.{_b64u(sig)}"
    return token, s.session_max_age_seconds


def verify_token(token: str, settings: Optional[Settings] = None) -> Optional[Session]:
    s = settings or get_settings()
    try:
        payload_b64, sig_b64 = token.split(".", 1)
        payload = _b64u_decode(payload_b64)
        sig = _b64u_decode(sig_b64)
    except Exception:
        return None
    expected = hmac.new(_secret(s), payload, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        user, issued_str, expires_str = payload.decode().split(":")
        issued, expires = int(issued_str), int(expires_str)
    except Exception:
        return None
    if expires < int(time.time()):
        return None
    return Session(user=user, issued_at=issued, expires_at=expires)


def credentials_match(user: str, password: str, settings: Optional[Settings] = None) -> bool:
    s = settings or get_settings()
    if not s.auth_enabled:
        return True
    return hmac.compare_digest(user, s.dashboard_user) and hmac.compare_digest(
        password, s.dashboard_password
    )


def current_session(request: Request) -> Optional[Session]:
    """Return the current session if the cookie is valid, else None."""
    settings = get_settings()
    if not settings.auth_enabled:
        return Session(user=settings.dashboard_user, issued_at=0, expires_at=2**31 - 1)

    raw = request.cookies.get(SESSION_COOKIE)
    if raw and (sess := verify_token(raw, settings)):
        return sess

    # Allow Authorization: Bearer <token> as an alternative for API clients.
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return verify_token(auth_header[len("Bearer ") :].strip(), settings)
    return None


def require_session(request: Request) -> Session:
    sess = current_session(request)
    if sess is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return sess
