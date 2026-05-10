"""Login / logout / status."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.auth import SESSION_COOKIE, credentials_match, current_session, issue_token
from app.config import Settings
from app.deps import settings_dep
from app.schemas import AuthStatus, LoginRequest, SimpleMessage

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/status", response_model=AuthStatus)
def auth_status(request: Request, settings: Settings = Depends(settings_dep)) -> AuthStatus:
    sess = current_session(request)
    return AuthStatus(
        auth_required=settings.auth_enabled,
        user=sess.user if sess else None,
    )


@router.post("/login", response_model=SimpleMessage)
def login(
    payload: LoginRequest,
    response: Response,
    settings: Settings = Depends(settings_dep),
) -> SimpleMessage:
    user = (payload.user or settings.dashboard_user).strip()
    if not credentials_match(user, payload.password, settings):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token, max_age = issue_token(user, settings)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        path="/",
    )
    return SimpleMessage(message="Logged in")


@router.post("/logout", response_model=SimpleMessage)
def logout(response: Response) -> SimpleMessage:
    response.delete_cookie(SESSION_COOKIE, path="/")
    return SimpleMessage(message="Logged out")
