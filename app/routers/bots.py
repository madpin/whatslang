"""Bot catalog and per-(bot, chat) controls."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.db import Database
from app.deps import get_bots, get_db, require_auth
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
    bot_name: str,
    chat_jid: str,
    bots: BotManager = Depends(get_bots),
    db: Database = Depends(get_db),
    _: object = Depends(require_auth),
) -> SimpleMessage:
    if not bots.get_spec(bot_name):
        raise HTTPException(status_code=404, detail=f"Unknown bot: {bot_name}")
    if not db.get_chat(chat_jid):
        raise HTTPException(status_code=404, detail=f"Chat not found: {chat_jid}")
    if not bots.start(bot_name, chat_jid):
        raise HTTPException(status_code=500, detail="Failed to start bot")
    return SimpleMessage(message=f"Started {bot_name} for {chat_jid}")


@router.post("/{bot_name}/stop", response_model=SimpleMessage)
def stop_bot(
    bot_name: str,
    chat_jid: str,
    bots: BotManager = Depends(get_bots),
    _: object = Depends(require_auth),
) -> SimpleMessage:
    if not bots.get_spec(bot_name):
        raise HTTPException(status_code=404, detail=f"Unknown bot: {bot_name}")
    bots.stop(bot_name, chat_jid)
    return SimpleMessage(message=f"Stopped {bot_name} for {chat_jid}")


@router.put("/{bot_name}/settings", response_model=BotStatus)
def update_settings(
    bot_name: str,
    chat_jid: str,
    payload: BotSettingsUpdate,
    bots: BotManager = Depends(get_bots),
    db: Database = Depends(get_db),
    _: object = Depends(require_auth),
) -> BotStatus:
    if not bots.get_spec(bot_name):
        raise HTTPException(status_code=404, detail=f"Unknown bot: {bot_name}")

    fields: dict = {}
    if payload.answer_owner_messages is not None:
        fields["answer_owner_messages"] = payload.answer_owner_messages
    if payload.context_message_count is not None:
        if payload.context_message_count < 0:
            raise HTTPException(status_code=400, detail="context_message_count must be ≥ 0")
        fields["context_message_count"] = payload.context_message_count
    if payload.response_chat_jid is not None:
        target = (payload.response_chat_jid or "").strip() or None
        if target and not db.get_chat(target):
            raise HTTPException(status_code=400, detail=f"Target chat not found: {target}")
        fields["response_chat_jid"] = target

    if fields:
        db.upsert_assignment(bot_name, chat_jid, **fields)

    status = bots.status(bot_name, chat_jid)
    if not status:
        raise HTTPException(status_code=404, detail="Bot not found after update")
    return BotStatus(**status)


@router.get("/{bot_name}/logs", response_model=BotLogs)
def bot_logs(
    bot_name: str,
    chat_jid: str,
    limit: int = 100,
    bots: BotManager = Depends(get_bots),
    _: object = Depends(require_auth),
) -> BotLogs:
    logs = bots.get_logs(bot_name, chat_jid, limit=limit)
    return BotLogs(
        bot_name=bot_name,
        chat_jid=chat_jid,
        logs=[BotLogEntry(**entry) for entry in logs],
    )
