"""FastAPI dependency providers — wired in `app.main`."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Path, Request, status

from app.auth import Session, current_session
from app.config import Settings, get_settings
from app.db import Database
from app.security import is_valid_chat_jid
from app.services.bot_manager import BotManager
from app.services.llm import LLMService
from app.services.whatsapp import WhatsAppClient, WhatsAppGateway


def settings_dep() -> Settings:
    return get_settings()


def get_db(request: Request) -> Database:
    return request.app.state.db  # type: ignore[no-any-return]


def get_whatsapp(request: Request) -> WhatsAppClient:
    return request.app.state.whatsapp  # type: ignore[no-any-return]


def get_gateway(request: Request) -> WhatsAppGateway:
    return request.app.state.gateway  # type: ignore[no-any-return]


def get_llm(request: Request) -> LLMService:
    return request.app.state.llm  # type: ignore[no-any-return]


def get_bots(request: Request) -> BotManager:
    return request.app.state.bots  # type: ignore[no-any-return]


def require_auth(
    request: Request, settings: Settings = Depends(settings_dep)
) -> Session:
    if not settings.auth_enabled:
        return Session(user=settings.dashboard_user, issued_at=0, expires_at=2**31 - 1)
    sess = current_session(request)
    if sess is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return sess


def valid_chat_jid_path(chat_jid: str = Path(..., max_length=200)) -> str:
    """Strict JID validation for path parameters.

    Untrusted ``chat_jid`` is interpolated into URLs that hit the WhatsApp
    gateway (e.g. ``GET {gateway}/chat/{chat_jid}/messages``); without
    validation, a request like ``/api/chats/foo%2F..%2Fadmin/messages``
    would let a caller probe arbitrary gateway endpoints (SSRF). The
    allow-list in :func:`app.security.is_valid_chat_jid` is intentionally
    narrower than what WhatsApp accepts.
    """
    if not is_valid_chat_jid(chat_jid):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chat JID",
        )
    return chat_jid
