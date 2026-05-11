"""Pytest fixtures.

Each test gets a freshly built app with a known-good environment so that
``Settings.security_check`` doesn't trip on missing values, plus a stub
``WhatsAppClient`` so we never touch the network.

The lifespan handler creates a real ``BotManager`` and a real ``Database``
(both backed by a temp file). That's intentional: the security-relevant
behaviour we want to verify is end-to-end through the actual stack.

We also synthesise a fake ``web/dist`` so the SPA catch-all route mounts
the same way as it does in production. Locally ``web/dist`` exists from
the dev workflow; on CI it usually does not, and we want both code paths
exercised identically.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

# Stable fake-SPA index that the path-traversal test fingerprints to
# confirm "the SPA fallback served, not a leaked file".
_FAKE_INDEX_HTML = (
    "<!doctype html>\n"
    '<html lang="en"><head><meta charset="UTF-8">'
    "<title>Whatslang test SPA</title></head>"
    '<body><div id="root">test-spa</div></body></html>\n'
)


def _set_env(**overrides: str) -> dict[str, str]:
    base = {
        "DASHBOARD_USER": "admin",
        "DASHBOARD_PASSWORD": "test-password-12345",
        "SESSION_SECRET": "x" * 48,
        "WHATSAPP_BASE_URL": "http://localhost:9",  # never reached
        "WHATSAPP_API_USER": "u",
        "WHATSAPP_API_PASSWORD": "p",
        "DEVICE_ID": "0000@s.whatsapp.net",
        "OPENAI_API_KEY": "sk-test",
        "ENVIRONMENT": "development",
        "ALLOWED_ORIGINS": "http://localhost:5173",
    }
    base.update(overrides)
    return base


@pytest.fixture
def temp_db(tmp_path: Path) -> Iterator[Path]:
    db = tmp_path / "messages.db"
    yield db


@pytest.fixture
def fake_web_dist(tmp_path: Path) -> Path:
    """Build a minimal ``web/dist`` so the SPA catch-all always mounts.

    We include an ``index.html`` (served by the SPA fallback) plus an
    ``assets/main.js`` so the static mount has at least one file. Tests
    fingerprint the index body to distinguish the fallback from a
    successful path-traversal that would have leaked a real file.
    """
    web_dist = tmp_path / "web_dist"
    (web_dist / "assets").mkdir(parents=True)
    (web_dist / "index.html").write_text(_FAKE_INDEX_HTML, encoding="utf-8")
    (web_dist / "assets" / "main.js").write_text(
        "// fake spa asset\n", encoding="utf-8"
    )
    return web_dist


@pytest.fixture
def app_factory(
    monkeypatch: pytest.MonkeyPatch, temp_db: Path, fake_web_dist: Path
):
    """Returns a factory so individual tests can override env vars."""

    def make(**env: str):
        for k, v in _set_env(DB_PATH=str(temp_db), **env).items():
            monkeypatch.setenv(k, v)
        # The SPA path is computed at import time, so patch the module-
        # level constant before ``create_app`` reads it.
        import app.main as _main

        monkeypatch.setattr(_main, "WEB_DIST", fake_web_dist)
        from app.config import get_settings

        get_settings.cache_clear()
        return _main.create_app()

    return make


class _FakeWhatsApp:
    """Stand-in WhatsApp client used in tests; never makes a real HTTP call."""

    def __init__(self, *_: Any, **__: Any) -> None:
        self.last_call_at = None
        self.last_error_at = None
        self.call_count = 0
        self.error_count = 0

    def get_app_status(self) -> dict[str, Any]:
        return {"reachable": False, "http_status": None, "latency_ms": 0}

    def get_messages(self, *_: Any, **__: Any) -> list[dict[str, Any]]:
        return []

    def get_groups(self, **_: Any) -> list[dict[str, Any]]:
        return []

    def get_chats(self, **_: Any) -> list[dict[str, Any]]:
        return []

    def get_contacts(self, **_: Any) -> list[dict[str, Any]]:
        return []

    def get_chat_info(self, *_: Any) -> None:
        return None

    def get_group_info(self, *_: Any) -> None:
        return None

    def get_user_info(self, *_: Any) -> None:
        return None

    def send_message(self, *_: Any, **__: Any) -> bool:
        return True

    def recent_errors(self) -> list[dict[str, Any]]:
        return []

    @staticmethod
    def is_bot_sender(*_: Any, **__: Any) -> bool:
        return False

    @staticmethod
    def extract_friendly_name(item: dict[str, Any]) -> str | None:
        return item.get("name") if isinstance(item, dict) else None


class _FakeLLM:
    """Minimal stand-in for ``LLMService`` — just enough surface for the
    tests that exercise ``/api/diagnostics`` without spending tokens."""

    def __init__(self, *_: Any, **__: Any) -> None:
        self.model = "stub-text"
        self.vision_model = "stub-vision"
        self.audio_model = "stub-audio"

    def activity_snapshot(self) -> list[dict[str, Any]]:
        return [
            {
                "surface": kind,
                "model": getattr(
                    self,
                    {
                        "text": "model",
                        "vision": "vision_model",
                        "audio": "audio_model",
                        "video": "audio_model",
                    }[kind],
                ),
                "call_count": 0,
                "success_count": 0,
                "error_count": 0,
                "last_call_at": None,
                "last_success_at": None,
                "last_error_at": None,
                "last_error_message": None,
                "last_latency_ms": None,
            }
            for kind in ("text", "vision", "audio", "video")
        ]


@pytest.fixture
def client(app_factory, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Authenticated and unauthenticated callers both use this client.

    Tests that want auth log in via ``/api/auth/login`` first; the cookie
    sticks on the TestClient session like any browser.
    """
    monkeypatch.setattr("app.main.WhatsAppClient", _FakeWhatsApp)
    monkeypatch.setattr("app.main.LLMService", _FakeLLM)
    app = app_factory()
    with TestClient(app) as tc:
        yield tc


@pytest.fixture
def open_client(app_factory, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Like ``client`` but with auth disabled, so we can test the open mode."""
    monkeypatch.setattr("app.main.WhatsAppClient", _FakeWhatsApp)
    monkeypatch.setattr("app.main.LLMService", _FakeLLM)
    app = app_factory(DASHBOARD_PASSWORD="")
    with TestClient(app) as tc:
        yield tc


@pytest.fixture(autouse=True)
def _reset_throttle():
    """Ensure each test starts with an empty login throttle."""
    from app.security import default_login_throttle

    default_login_throttle._buckets.clear()  # type: ignore[attr-defined]
    yield
    default_login_throttle._buckets.clear()  # type: ignore[attr-defined]
