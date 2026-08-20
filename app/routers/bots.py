"""Bot catalog and per-(bot, chat) controls."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.config import Settings
from app.db import Database
from app.deps import get_bots, get_db, require_auth, settings_dep
from app.schemas import (
    BotLogEntry,
    BotLogs,
    BotSettingsUpdate,
    BotStatus,
    BotSupports,
    BotType,
    SimpleMessage,
)
from app.services.bot_manager import BotManager

router = APIRouter(prefix="/api/bots", tags=["bots"])

# Bot names live in the registry and ship with the app — they're never
# user-supplied at runtime, but bot_name flows into URL paths so we still
# enforce a tight pattern as defense in depth.
_BOT_NAME_RE = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")


def _valid_bot_name(bot_name: str = Path(..., max_length=64)) -> str:
    if not _BOT_NAME_RE.match(bot_name):
        raise HTTPException(status_code=400, detail="Invalid bot name")
    return bot_name


def _valid_chat_jid_query(chat_jid: str = Query(..., max_length=200)) -> str:
    from app.security import is_valid_chat_jid

    if not is_valid_chat_jid(chat_jid):
        raise HTTPException(status_code=400, detail="Invalid chat JID")
    return chat_jid


@router.get("/types", response_model=list[BotType])
def list_bot_types(bots: BotManager = Depends(get_bots), _: object = Depends(require_auth)) -> list[BotType]:
    return [
        BotType(
            name=spec.name,
            label=spec.label,
            prefix=spec.prefix,
            emoji=spec.emoji,
            description=spec.description,
            supports=BotSupports(
                text=spec.supports_text,
                image=spec.supports_image,
                audio=spec.supports_audio,
                video=spec.supports_video,
            ),
        )
        for spec in bots.specs
    ]


@router.get("", response_model=list[BotStatus])
def list_running(bots: BotManager = Depends(get_bots), _: object = Depends(require_auth)) -> list[BotStatus]:
    return [BotStatus(**s) for s in bots.all_running_statuses()]


@router.post("/{bot_name}/start", response_model=SimpleMessage)
def start_bot(
    bot_name: str = Depends(_valid_bot_name),
    chat_jid: str = Depends(_valid_chat_jid_query),
    bots: BotManager = Depends(get_bots),
    db: Database = Depends(get_db),
    _: object = Depends(require_auth),
) -> SimpleMessage:
    if not bots.get_spec(bot_name):
        raise HTTPException(status_code=404, detail="Unknown bot")
    if not db.get_chat(chat_jid):
        raise HTTPException(status_code=404, detail="Chat not found")
    if not bots.start(bot_name, chat_jid):
        raise HTTPException(status_code=500, detail="Failed to start bot")
    return SimpleMessage(message=f"Started {bot_name} for {chat_jid}")


@router.post("/{bot_name}/stop", response_model=SimpleMessage)
def stop_bot(
    bot_name: str = Depends(_valid_bot_name),
    chat_jid: str = Depends(_valid_chat_jid_query),
    bots: BotManager = Depends(get_bots),
    _: object = Depends(require_auth),
) -> SimpleMessage:
    if not bots.get_spec(bot_name):
        raise HTTPException(status_code=404, detail="Unknown bot")
    bots.stop(bot_name, chat_jid)
    return SimpleMessage(message=f"Stopped {bot_name} for {chat_jid}")


@router.put("/{bot_name}/settings", response_model=BotStatus)
def update_settings(
    payload: BotSettingsUpdate,
    bot_name: str = Depends(_valid_bot_name),
    chat_jid: str = Depends(_valid_chat_jid_query),
    bots: BotManager = Depends(get_bots),
    db: Database = Depends(get_db),
    settings: Settings = Depends(settings_dep),
    _: object = Depends(require_auth),
) -> BotStatus:
    if not bots.get_spec(bot_name):
        raise HTTPException(status_code=404, detail="Unknown bot")

    fields: dict = {}
    if payload.answer_owner_messages is not None:
        fields["answer_owner_messages"] = payload.answer_owner_messages
    if payload.context_message_count is not None:
        # Pydantic already enforces ge=0; this is belt-and-suspenders.
        fields["context_message_count"] = payload.context_message_count
    if payload.response_chat_jid is not None:
        target = (payload.response_chat_jid or "").strip() or None
        # Schema validator already rejected anything that isn't a valid JID.
        # We additionally require the target chat to exist locally so a
        # caller can't redirect a bot's output to an arbitrary phone number.
        if target and not db.get_chat(target):
            raise HTTPException(status_code=400, detail="Target chat not found")
        fields["response_chat_jid"] = target

    # Device routing. An empty value resets to the default / source device;
    # any non-empty value must match a configured device.
    known = settings.device_id_set
    for field_name, label in (
        ("source_device_id", "source device"),
        ("target_device_id", "target device"),
    ):
        value = getattr(payload, field_name)
        if value is None:
            continue
        did = value.strip() or None
        if did and did not in known:
            raise HTTPException(status_code=400, detail=f"Unknown {label}")
        fields[field_name] = did

    if fields:
        db.upsert_assignment(bot_name, chat_jid, **fields)
    if payload.source_device_id is not None or payload.target_device_id is not None:
        bots.refresh_route(bot_name, chat_jid)

    status = bots.status(bot_name, chat_jid)
    if not status:
        raise HTTPException(status_code=404, detail="Bot not found after update")
    return BotStatus(**status)


@router.get("/{bot_name}/logs", response_model=BotLogs)
def bot_logs(
    bot_name: str = Depends(_valid_bot_name),
    chat_jid: str = Depends(_valid_chat_jid_query),
    limit: int = Query(100, ge=1, le=500),
    bots: BotManager = Depends(get_bots),
    _: object = Depends(require_auth),
) -> BotLogs:
    logs = bots.get_logs(bot_name, chat_jid, limit=limit)
    return BotLogs(
        bot_name=bot_name,
        chat_jid=chat_jid,
        logs=[BotLogEntry(**entry) for entry in logs],
    )
