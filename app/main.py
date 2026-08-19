"""FastAPI application factory and entrypoint."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import get_settings
from app.db import Database
from app.logging_setup import configure_logging
from app.routers import auth as auth_router
from app.routers import bots as bots_router
from app.routers import chats as chats_router
from app.routers import devices as devices_router
from app.routers import system as system_router
from app.security import redact_error, safe_static_path
from app.services.bot_manager import BotManager
from app.services.llm import LLMService
from app.services.whatsapp import WhatsAppClient, WhatsAppGateway

logger = logging.getLogger(__name__)

WEB_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"

# Maximum accepted request body size. Bot/chat payloads are tiny JSON; the
# gateway streams media directly so nothing legitimate needs to be larger.
MAX_BODY_BYTES = 1 * 1024 * 1024

_PLACEHOLDER_JID_HINTS = ("your-", "<", "example", "changeme", "placeholder")


def _is_real_jid(value: str) -> bool:
    """Return True when the JID looks like a real value, not an example."""
    v = (value or "").strip().lower()
    if "@" not in v:
        return False
    return not any(hint in v for hint in _PLACEHOLDER_JID_HINTS)


def _resolve_chat_name(whatsapp: WhatsAppClient, chat_jid: str) -> str | None:
    """Best-effort friendly name lookup via the WhatsApp gateway."""
    try:
        if chat_jid.endswith("@g.us"):
            info = whatsapp.get_group_info(chat_jid) or whatsapp.get_chat_info(chat_jid) or {}
        else:
            info = whatsapp.get_user_info(chat_jid) or whatsapp.get_chat_info(chat_jid) or {}
        return WhatsAppClient.extract_friendly_name(info)
    except Exception:  # pragma: no cover — defensive only
        logger.debug("Friendly-name lookup failed for %s", chat_jid)
        return None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level, settings.environment)
    logger.info("Starting WhatsLang %s (%s)", __version__, settings.environment)

    missing = settings.required_missing()
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")

    db = Database(settings.db_path)
    # One gateway, many devices (GoWA v8). Each device is a lazily-created
    # ``WhatsAppClient`` scoped by ``X-Device-Id``. ``WhatsAppClient`` is
    # referenced through this module's namespace so tests can patch it.
    gateway = WhatsAppGateway(
        settings.whatsapp_base_url,
        username=settings.whatsapp_api_user,
        password=settings.whatsapp_api_password,
        default_device_id=settings.default_device_id,
        client_factory=WhatsAppClient,
    )
    # Back-compat single client (default device) for diagnostics and the
    # chat-list/friendly-name helpers that aren't bot-scoped.
    whatsapp = gateway.default
    llm = LLMService(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        base_url=settings.openai_base_url,
        vision_model=settings.openai_vision_model,
        audio_model=settings.openai_audio_model,
    )
    bots = BotManager(
        gateway=gateway,
        llm=llm,
        db=db,
        devices=settings.resolved_devices,
        default_device_id=settings.default_device_id,
        poll_interval=settings.poll_interval,
    )

    # Backward compatibility with the old `CHAT_JID` env variable. Skip when
    # the value is the example placeholder (e.g. "your-group-jid@g.us") so we
    # don't pollute the chat list. Try to resolve a friendly name from the
    # gateway when seeding for the first time.
    if settings.chat_jid and _is_real_jid(settings.chat_jid) and not db.get_chat(settings.chat_jid):
        friendly = _resolve_chat_name(whatsapp, settings.chat_jid)
        db.add_chat(
            settings.chat_jid,
            friendly or settings.chat_jid,
            is_manual=True,
        )

    # One-time cleanup: remove placeholder rows that older builds may have
    # written before the import-skip was in place.
    for row in db.list_chats():
        jid = row["chat_jid"]
        if not _is_real_jid(jid):
            logger.info("Removing placeholder chat row: %s", jid)
            db.delete_chat(jid)

    started = bots.resume_running_from_db()
    logger.info(
        "Loaded %d bot type(s); resumed %d running bot(s)", len(bots.specs), started
    )

    app.state.settings = settings
    app.state.db = db
    app.state.gateway = gateway
    app.state.whatsapp = whatsapp
    app.state.llm = llm
    app.state.bots = bots

    try:
        yield
    finally:
        logger.info("Shutting down — leaving bot running state intact in DB")
        bots.stop_all(persist=False)


def create_app() -> FastAPI:
    settings = get_settings()
    # Refuse insecure boot configurations in production. Done at app build
    # time so misconfigurations fail loudly instead of silently exposing the
    # admin API. See ``Settings.security_check`` for the exhaustive list.
    settings.security_check(strict=settings.is_production, logger=logger)

    app = FastAPI(
        title="WhatsLang",
        description="A modular WhatsApp bot service with a sleek dashboard.",
        version=__version__,
        lifespan=lifespan,
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
        openapi_url="/api/openapi.json" if not settings.is_production else None,
    )

    # CORS: ``allow_credentials=True`` is incompatible with ``allow_origins=*``
    # per the Fetch spec — browsers refuse to send cookies in that case. We
    # also drop credentials when the configured origin list is wildcarded so
    # that a misconfiguration doesn't trick API clients into believing they
    # have a credentialed session that the browser will silently strip.
    cors_origins = settings.cors_origins
    cors_credentialed = "*" not in cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=cors_credentialed,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
        max_age=600,
    )

    @app.middleware("http")
    async def access_log_and_security_headers(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        # Conservative security headers — the SPA does not load third-party
        # scripts or framed content. ``Content-Security-Policy`` is set to a
        # tight default; tighten or relax via a reverse proxy when needed.
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy",
            "accelerometer=(), camera=(), geolocation=(), microphone=(), payment=()",
        )
        # HSTS only meaningful on HTTPS; safe to send anyway because browsers
        # ignore it on plain HTTP responses.
        if settings.is_production:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        if not request.url.path.startswith("/assets/"):
            duration = (time.perf_counter() - start) * 1000
            logger.info(
                "%s %s -> %s in %.0fms",
                request.method,
                request.url.path,
                response.status_code,
                duration,
            )
        return response

    # ------------------------------------------------------------------
    # Body-size guard — Starlette doesn't enforce one. Reject anything
    # larger than ~1 MiB before it touches a router. Bot/chat payloads are
    # tiny JSON; media never flows through this app (it streams via the
    # gateway).
    # ------------------------------------------------------------------
    @app.middleware("http")
    async def body_size_limit(request: Request, call_next):
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > MAX_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )
        return await call_next(request)

    app.include_router(auth_router.router)
    app.include_router(system_router.router)
    app.include_router(devices_router.router)
    app.include_router(chats_router.router)
    app.include_router(bots_router.router)

    @app.exception_handler(RuntimeError)
    async def runtime_error(_: Request, exc: RuntimeError) -> JSONResponse:
        # Never echo the exception message to the client: it routinely
        # contains paths, env-var names and other internals. The full detail
        # is logged server-side.
        logger.error("Runtime error: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": redact_error(exc)},
        )

    # ----- Top-level legacy/system endpoints (no /api prefix) ------------
    @app.get("/health")
    def health_legacy() -> dict:
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": __version__,
        }

    @app.get("/ready")
    def ready_legacy() -> dict:
        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": __version__,
        }

    @app.get("/favicon.ico")
    def favicon() -> Response:
        ico = WEB_DIST / "favicon.svg"
        if ico.exists():
            return FileResponse(ico)
        return Response(status_code=204)

    # ----- Frontend (SPA) -----------------------------------------------
    if WEB_DIST.exists():
        app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

        @app.get("/", include_in_schema=False)
        @app.get("/{full_path:path}", include_in_schema=False)
        def spa(full_path: str = "") -> Response:
            # Don't shadow API routes — let them 404 naturally.
            if full_path.startswith("api") or full_path in {"health", "ready"}:
                return JSONResponse(status_code=404, content={"detail": "Not found"})
            # SECURITY: ``Path(WEB_DIST) / full_path`` would silently allow
            # traversal via URL-encoded ``../`` segments and serve any file
            # readable by the process. ``safe_static_path`` resolves the
            # join and refuses anything that escapes ``WEB_DIST``.
            if full_path:
                resolved = safe_static_path(WEB_DIST, full_path)
                if resolved is not None:
                    return FileResponse(resolved)
            return FileResponse(WEB_DIST / "index.html")
    else:
        @app.get("/")
        def root_no_ui() -> Response:
            return JSONResponse(
                {
                    "service": "WhatsLang",
                    "version": __version__,
                    "ui": "Frontend bundle not built. Run `npm install && npm run build` in `web/`.",
                    "docs": "/api/docs" if not settings.is_production else None,
                }
            )

    return app


app = create_app()


def main() -> None:
    """Run the dev server with `python -m app`."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_config=None,
        access_log=False,
    )


if __name__ == "__main__":
    main()
