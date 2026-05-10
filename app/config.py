"""Application settings — single source of truth, loaded from environment.

Backwards-compatible with the old `.env`: every legacy variable is still
recognized so that an existing deployment keeps working without changes.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Server ----------------------------------------------------------
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    environment: str = "development"
    allowed_origins: str = "*"

    # --- Auth (single-user from env) -------------------------------------
    dashboard_user: str = Field(
        default="admin",
        description="Username for the dashboard. Defaults to 'admin'.",
    )
    dashboard_password: str = Field(
        default="",
        description="Password for the dashboard. When empty the UI is fully open.",
    )
    session_secret: str = Field(
        default="",
        description=(
            "Secret used to sign session cookies. If empty, a random one is "
            "generated at startup (sessions reset on every restart)."
        ),
    )
    session_max_age_seconds: int = 60 * 60 * 24 * 7  # 7 days

    # --- WhatsApp API ----------------------------------------------------
    whatsapp_base_url: str = ""
    whatsapp_api_user: str = ""
    whatsapp_api_password: str = ""
    device_id: str = Field(default="", description="Bot device JID, used to detect own messages.")

    # --- LLM (OpenAI / LiteLLM compatible) -------------------------------
    openai_api_key: str = ""
    openai_base_url: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_vision_model: Optional[str] = None
    openai_audio_model: str = "whisper-1"

    # --- Bot runtime -----------------------------------------------------
    poll_interval: int = 5
    db_path: Path = Path("data/messages.db")

    # --- Legacy ----------------------------------------------------------
    chat_jid: Optional[str] = Field(
        default=None,
        description="Legacy single chat JID — auto-imported on first boot if set.",
    )

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def auth_enabled(self) -> bool:
        return bool(self.dashboard_password.strip())

    @property
    def cors_origins(self) -> list[str]:
        if self.allowed_origins.strip() in ("", "*"):
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    def required_missing(self) -> list[str]:
        """Return the list of required env vars that are missing."""
        required = {
            "WHATSAPP_BASE_URL": self.whatsapp_base_url,
            "WHATSAPP_API_USER": self.whatsapp_api_user,
            "WHATSAPP_API_PASSWORD": self.whatsapp_api_password,
            "DEVICE_ID": self.device_id,
            "OPENAI_API_KEY": self.openai_api_key,
        }
        return [k for k, v in required.items() if not v]

    # ------------------------------------------------------------------
    # Security gating
    # ------------------------------------------------------------------
    def security_check(
        self, *, strict: bool, logger: Optional[logging.Logger] = None
    ) -> list[str]:
        """Return the list of insecure configuration items.

        When ``strict`` is True (production), raise ``RuntimeError`` if any
        finding is present so the service refuses to boot. Otherwise log a
        prominent warning so developers notice in non-prod.
        """
        log = logger or logging.getLogger(__name__)
        findings: list[str] = []

        if not self.dashboard_password.strip():
            findings.append(
                "DASHBOARD_PASSWORD is empty — the admin API is fully open. "
                "Set DASHBOARD_PASSWORD before exposing the service."
            )
        elif len(self.dashboard_password) < 12:
            findings.append(
                "DASHBOARD_PASSWORD is shorter than 12 characters — pick a "
                "stronger one or put the service behind a real auth proxy."
            )

        if not self.session_secret.strip():
            findings.append(
                "SESSION_SECRET is empty — sessions will be invalidated on "
                "every restart and cannot be shared across instances. Set a "
                "stable random secret (at least 32 bytes)."
            )
        elif len(self.session_secret) < 32:
            findings.append(
                "SESSION_SECRET is shorter than 32 characters — use a longer, "
                "random value (e.g. `python -c 'import secrets; print(secrets.token_urlsafe(48))'`)."
            )

        wildcard_cors = "*" in self.cors_origins
        if wildcard_cors and self.is_production:
            findings.append(
                "ALLOWED_ORIGINS=* in production. Restrict to the exact "
                "origin(s) hosting the dashboard."
            )

        if self.host == "0.0.0.0" and not self.dashboard_password.strip():
            findings.append(
                "HOST=0.0.0.0 binds to every interface AND no password is "
                "set. Either bind to 127.0.0.1 / a private interface or set "
                "DASHBOARD_PASSWORD."
            )

        if findings:
            joined = "\n  - ".join(findings)
            if strict:
                raise RuntimeError(
                    "Refusing to start: insecure configuration in "
                    f"production:\n  - {joined}"
                )
            log.warning(
                "INSECURE CONFIGURATION (allowed in environment=%s):\n  - %s",
                self.environment,
                joined,
            )
        return findings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor."""
    return Settings()
