"""Pytest fixtures.

Each test gets a freshly built app with a known-good environment so that
``Settings.security_check`` doesn't trip on missing values, plus a stub
``WhatsAppClient`` so we never touch the network.

The lifespan handler creates a real ``BotManager`` and a real ``Database``
(both backed by a temp file). That's intentional: the security-relevant
behaviour we want to verify is end-to-end through the actual stack.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


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
def app_factory(monkeypatch: pytest.MonkeyPatch, temp_db: Path):
    """Returns a factory so individual tests can override env vars."""

    def make(**env: str):
        for k, v in _set_env(DB_PATH=str(temp_db), **env).items():
            monkeypatch.setenv(k, v)
        from app.config import get_settings

        get_settings.cache_clear()
        from app.main import create_app

        return create_app()

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
    def __init__(self, *_: Any, **__: Any) -> None:
        pass


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
