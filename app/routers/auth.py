"""Login / logout / status."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.auth import SESSION_COOKIE, credentials_match, current_session, issue_token
from app.config import Settings
from app.deps import settings_dep
from app.schemas import AuthStatus, LoginRequest, SimpleMessage
from app.security import default_login_throttle

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def _client_ip(request: Request) -> str:
    """Best-effort client IP for throttling.

    Honours the first ``X-Forwarded-For`` value when present (typical for
    reverse-proxy deployments) and falls back to the socket peer.
    """
    fwd = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if fwd:
        return fwd
    if request.client:
        return request.client.host
    return "unknown"


@router.get("/status", response_model=AuthStatus)
def auth_status(request: Request, settings: Settings = Depends(settings_dep)) -> AuthStatus:
    sess = current_session(request)
    return AuthStatus(
        auth_required=settings.auth_enabled,
        user=sess.user if sess else None,
    )


@router.post("/login", response_model=SimpleMessage)
def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    settings: Settings = Depends(settings_dep),
) -> SimpleMessage:
    ip = _client_ip(request)
    allowed, retry_after = default_login_throttle.check(ip)
    if not allowed:
        # Tell the client to back off (RFC 6585) but don't reveal whether the
        # account exists or not.
        retry = max(1, int(retry_after))
        logger.warning("Throttled login from %s (retry after %ds)", ip, retry)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
            headers={"Retry-After": str(retry)},
        )

    user = (payload.user or settings.dashboard_user).strip()
    if not credentials_match(user, payload.password, settings):
        default_login_throttle.record_failure(ip)
        # Don't leak which of user/password was wrong, and use a constant
        # error so timing differences from credential parsing don't help.
        logger.info("Failed login from %s", ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    default_login_throttle.record_success(ip)
    token, max_age = issue_token(user, settings)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=max_age,
        httponly=True,
        # ``strict`` blocks cross-site cookie attachment which kills the
        # CSRF vector entirely. The dashboard is single-origin so there is
        # no legitimate cross-site flow we'd lose.
        samesite="strict",
        secure=settings.is_production,
        path="/",
    )
    logger.info("User %r logged in from %s", user, ip)
    return SimpleMessage(message="Logged in")


@router.post("/logout", response_model=SimpleMessage)
def logout(response: Response, settings: Settings = Depends(settings_dep)) -> SimpleMessage:
    # Match the attribute set used at login so browsers actually drop the
    # cookie (some browsers ignore Set-Cookie deletes that don't share the
    # same SameSite/Secure attributes).
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        samesite="strict",
        secure=settings.is_production,
        httponly=True,
    )
    return SimpleMessage(message="Logged out")
