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
from app.routers import system as system_router
from app.services.bot_manager import BotManager
from app.services.llm import LLMService
from app.services.whatsapp import WhatsAppClient

logger = logging.getLogger(__name__)

WEB_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"

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
    whatsapp = WhatsAppClient(
        settings.whatsapp_base_url,
        username=settings.whatsapp_api_user,
        password=settings.whatsapp_api_password,
        device_id=settings.device_id,
    )
    llm = LLMService(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        base_url=settings.openai_base_url,
        vision_model=settings.openai_vision_model,
        audio_model=settings.openai_audio_model,
    )
    bots = BotManager(
        whatsapp=whatsapp,
        llm=llm,
        db=db,
        bot_device_id=settings.device_id,
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
    app = FastAPI(
        title="WhatsLang",
        description="A modular WhatsApp bot service with a sleek dashboard.",
        version=__version__,
        lifespan=lifespan,
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
        openapi_url="/api/openapi.json" if not settings.is_production else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def access_log(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
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

    app.include_router(auth_router.router)
    app.include_router(system_router.router)
    app.include_router(chats_router.router)
    app.include_router(bots_router.router)

    @app.exception_handler(RuntimeError)
    async def runtime_error(_: Request, exc: RuntimeError) -> JSONResponse:
        logger.error("Runtime error: %s", exc)
        return JSONResponse(status_code=500, content={"detail": str(exc)})

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
            target = WEB_DIST / full_path
            if full_path and target.is_file():
                return FileResponse(target)
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
