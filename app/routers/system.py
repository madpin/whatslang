"""System / health / diagnostics endpoints."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request

from app import __version__
from app.config import Settings
from app.db import Database
from app.deps import get_bots, get_db, get_whatsapp, require_auth, settings_dep
from app.schemas import (
    BotsDiagnostics,
    DatabaseDiagnostics,
    Diagnostics,
    GatewayDiagnostics,
    GatewayErrorEntry,
    Health,
    InboundObservation,
    LlmDiagnostics,
    LlmSurfaceActivity,
    Stats,
    SystemInfo,
)
from app.services.bot_manager import BotManager
from app.services.llm import LLMService
from app.services.whatsapp import WhatsAppClient

router = APIRouter(tags=["system"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/api/health", response_model=Health)
def health() -> Health:
    return Health(status="healthy", timestamp=_now_iso(), version=__version__)


@router.get("/api/ready", response_model=Health)
def ready() -> Health:
    return Health(status="ready", timestamp=_now_iso(), version=__version__)


@router.get("/api/system", response_model=SystemInfo)
def system_info(
    settings: Settings = Depends(settings_dep),
    _: object = Depends(require_auth),
) -> SystemInfo:
    return SystemInfo(
        version=__version__,
        environment=settings.environment,
        auth_required=settings.auth_enabled,
        whatsapp_base_url=settings.whatsapp_base_url or None,
        openai_model=settings.openai_model,
        openai_vision_model=settings.openai_vision_model or settings.openai_model,
        openai_audio_model=settings.openai_audio_model,
        poll_interval=settings.poll_interval,
        db_path=str(settings.db_path),
    )


@router.get("/api/stats", response_model=Stats)
def stats(
    db: Database = Depends(get_db),
    bots: BotManager = Depends(get_bots),
    _: object = Depends(require_auth),
) -> Stats:
    total_chats = db.count_chats()
    active_24h = db.count_chats(activity="active")
    running = sum(1 for s in bots.all_running_statuses() if s["status"] == "running")
    return Stats(
        total_chats=total_chats,
        running_bots=running,
        available_bot_types=len(bots.specs),
        active_chats_24h=active_24h,
    )


@router.get("/api/diagnostics", response_model=Diagnostics)
def diagnostics(
    request: Request,
    settings: Settings = Depends(settings_dep),
    db: Database = Depends(get_db),
    whatsapp: WhatsAppClient = Depends(get_whatsapp),
    bots: BotManager = Depends(get_bots),
    _: object = Depends(require_auth),
) -> Diagnostics:
    # Gateway state (live probe).
    gw = whatsapp.get_app_status()
    gateway = GatewayDiagnostics(
        base_url=settings.whatsapp_base_url or None,
        reachable=bool(gw.get("reachable")),
        http_status=gw.get("http_status"),
        latency_ms=gw.get("latency_ms"),
        is_connected=bool(gw.get("is_connected")),
        is_logged_in=bool(gw.get("is_logged_in")),
        device_id=gw.get("device_id"),
        error=gw.get("error"),
        last_call_at=whatsapp.last_call_at,
        last_error_at=whatsapp.last_error_at,
        call_count=whatsapp.call_count,
        error_count=whatsapp.error_count,
    )

    # LLM diagnostics — no live API call (avoid spending credits each
    # refresh). Per-surface activity comes from the in-memory tracker on
    # the ``LLMService`` instance.
    llm_service: LLMService | None = getattr(request.app.state, "llm", None)
    surfaces = (
        [LlmSurfaceActivity(**row) for row in llm_service.activity_snapshot()]
        if llm_service is not None
        else []
    )
    llm = LlmDiagnostics(
        base_url=settings.openai_base_url,
        text_model=settings.openai_model,
        vision_model=settings.openai_vision_model or settings.openai_model,
        audio_model=settings.openai_audio_model,
        api_key_set=bool(settings.openai_api_key),
        surfaces=surfaces,
    )

    # Inbound observations. Resolve a friendly chat name from the
    # ``chats`` table so the operator can recognise the conversation
    # without decoding the JID.
    obs_rows = db.list_inbound_observations()
    name_lookup: dict[str, str] = {}
    needed = {row["last_chat_jid"] for row in obs_rows if row.get("last_chat_jid")}
    for jid in needed:
        chat = db.get_chat(jid)
        if chat:
            name_lookup[jid] = chat.get("chat_name") or jid
    inbound = [
        InboundObservation(
            media_type=row["media_type"],
            last_seen_at=row["last_seen_at"],
            last_chat_jid=row["last_chat_jid"],
            last_chat_name=name_lookup.get(row.get("last_chat_jid") or ""),
            last_sender=row["last_sender"],
            total_count=int(row["total_count"]),
        )
        for row in obs_rows
    ]

    # Database stats — counts come from the live DB connection.
    db_path = str(settings.db_path)
    db_size = 0
    try:
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
    except OSError:
        db_size = 0
    chats_count = db.count_chats()
    with db._connect() as conn:  # type: ignore[attr-defined]
        try:
            assignments = int(
                conn.execute("SELECT COUNT(*) FROM bot_chat_assignments").fetchone()[0]
            )
        except Exception:
            assignments = 0
        try:
            processed = int(
                conn.execute("SELECT COUNT(*) FROM processed_messages").fetchone()[0]
            )
        except Exception:
            processed = 0
    database = DatabaseDiagnostics(
        path=db_path,
        size_bytes=db_size,
        chats=chats_count,
        assignments=assignments,
        processed_messages=processed,
    )

    bots_d = BotsDiagnostics(
        catalog_size=len(bots.specs),
        running=sum(
            1 for s in bots.all_running_statuses() if s["status"] == "running"
        ),
        poll_interval=settings.poll_interval,
    )

    recent = [GatewayErrorEntry(**e) for e in whatsapp.recent_errors()]

    return Diagnostics(
        timestamp=_now_iso(),
        version=__version__,
        environment=settings.environment,
        gateway=gateway,
        llm=llm,
        database=database,
        bots=bots_d,
        inbound=inbound,
        recent_errors=recent,
    )
