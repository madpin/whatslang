"""Security primitives shared by routers and middleware.

This module intentionally has no dependency on FastAPI request objects so
that helpers stay easy to unit-test:

- ``validate_chat_jid``  : strict allow-list parser for WhatsApp JIDs.
- ``safe_static_path``   : path join that refuses traversal outside of root.
- ``LoginThrottle``      : per-IP login attempt throttle (in-memory).
- ``redact_error``       : strips internals from messages we send to clients.

Everything here is defense-in-depth, not a replacement for putting the
service behind a TLS-terminating reverse proxy with its own ACLs.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# WhatsApp JID validation
# ---------------------------------------------------------------------------

# Allowed JID servers. Keep this conservative: anything outside this list
# is rejected. This is intentionally narrower than what WhatsApp accepts so
# that user input cannot be smuggled into a different gateway URL path.
_ALLOWED_JID_SERVERS = frozenset(
    {
        "s.whatsapp.net",   # individual contact (canonical)
        "c.us",             # individual contact (legacy)
        "g.us",             # group chat
        "broadcast",        # broadcast list
        "newsletter",       # WhatsApp channels
        "lid",              # ephemeral / linked identifiers
    }
)

# user@server, where:
#   user  = digits, dots, dashes, underscores, optional ":<device>" suffix
#   server= one of the allow-listed servers above (validated separately)
# Length cap keeps URLs and DB rows small.
_JID_RE = re.compile(r"^([A-Za-z0-9._\-]{1,128})(?::([0-9]{1,4}))?@([A-Za-z0-9.\-]{1,64})$")


def is_valid_chat_jid(value: str) -> bool:
    """Return True when ``value`` is a syntactically valid WhatsApp JID.

    The check is purely syntactic — it does not contact the gateway.
    """
    if not isinstance(value, str):
        return False
    value = value.strip()
    if not value or len(value) > 200:
        return False
    m = _JID_RE.match(value)
    if not m:
        return False
    return m.group(3).lower() in _ALLOWED_JID_SERVERS


def validate_chat_jid(value: str) -> str:
    """Validate ``value`` and return the normalized lower-case JID.

    Raises :class:`ValueError` when the JID is malformed. Callers should
    convert this to an HTTP 400 / 422 — see ``app.deps.valid_chat_jid``.
    """
    if not is_valid_chat_jid(value):
        raise ValueError(f"Invalid chat JID: {value!r}")
    return value.strip()


# ---------------------------------------------------------------------------
# Safe path joining for the SPA static handler
# ---------------------------------------------------------------------------

def safe_static_path(root: Path, user_path: str) -> Optional[Path]:
    """Join ``root`` with ``user_path`` and refuse traversal outside ``root``.

    Returns the resolved path on success, or ``None`` if the request escapes
    the root, contains absolute components, or references something that is
    not a regular file.

    Why this exists: ``Path(root) / user_path`` happily produces
    ``root/../../etc/passwd``, and ``Path.is_file()`` silently follows that
    via the OS. Without this helper, ``GET /%2E%2E%2F.../etc/passwd`` on the
    SPA fallback route would serve any file readable by the process.
    """
    if not user_path:
        return None
    # Reject obvious traversal markers and absolute paths up-front.
    if user_path.startswith(("/", "\\")) or "\x00" in user_path:
        return None
    candidate = (root / user_path).resolve(strict=False)
    try:
        root_resolved = root.resolve(strict=False)
        candidate.relative_to(root_resolved)
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate


# ---------------------------------------------------------------------------
# Login throttle
# ---------------------------------------------------------------------------

@dataclass
class _Bucket:
    failures: deque  # deque[float] — UNIX timestamps of recent failures
    locked_until: float = 0.0


class LoginThrottle:
    """In-memory per-key throttle for the login endpoint.

    Keys are typically the client IP. A burst of failures briefly locks
    the bucket so an attacker can't trivially brute-force the password.

    Defaults:
      - more than ``max_failures`` failures within ``window`` seconds locks
        the bucket for ``lock_duration`` seconds.
      - successful logins clear the bucket.

    This is intentionally simple — single process, in-memory. It will not
    survive restarts and is not shared across instances; for multi-instance
    deployments put a real WAF / rate-limiter in front of the service.
    """

    def __init__(
        self,
        *,
        max_failures: int = 5,
        window: float = 60.0,
        lock_duration: float = 300.0,
    ):
        self.max_failures = max_failures
        self.window = window
        self.lock_duration = lock_duration
        self._buckets: dict[str, _Bucket] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, float]:
        """Return ``(allowed, retry_after_seconds)`` for ``key``."""
        now = time.time()
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket and bucket.locked_until > now:
                return False, bucket.locked_until - now
        return True, 0.0

    def record_failure(self, key: str) -> None:
        now = time.time()
        with self._lock:
            bucket = self._buckets.setdefault(key, _Bucket(failures=deque()))
            bucket.failures.append(now)
            cutoff = now - self.window
            while bucket.failures and bucket.failures[0] < cutoff:
                bucket.failures.popleft()
            if len(bucket.failures) >= self.max_failures:
                bucket.locked_until = now + self.lock_duration
                bucket.failures.clear()
                logger.warning(
                    "Login throttle: locking %r for %ds after repeated failures",
                    key,
                    int(self.lock_duration),
                )

    def record_success(self, key: str) -> None:
        with self._lock:
            self._buckets.pop(key, None)


# Singleton used by the auth router. Tests override directly.
default_login_throttle = LoginThrottle()


# ---------------------------------------------------------------------------
# Error redaction
# ---------------------------------------------------------------------------

def redact_error(exc: BaseException, *, generic: str = "Internal error") -> str:
    """Return a safe message for HTTP responses.

    In production we never echo the exception's repr — it can leak file
    paths, DB internals and secrets pulled from environment variables. We
    log the full detail server-side instead.
    """
    return generic
