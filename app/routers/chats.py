"""Chat management endpoints."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db import Database
from app.deps import get_bots, get_db, get_whatsapp, require_auth
from app.schemas import (
    AddChatRequest,
    BotStatus,
    BulkActionRequest,
    Chat,
    ChatBrief,
    ChatListResponse,
    ChatWithBots,
    Pagination,
    SimpleMessage,
)
from app.services.bot_manager import BotManager
from app.services.whatsapp import WhatsAppClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chats", tags=["chats"])


def _is_group(chat_jid: str) -> bool:
    return chat_jid.endswith("@g.us")


def _row_to_chat(row: dict) -> Chat:
    return Chat(
        chat_jid=row["chat_jid"],
        chat_name=row["chat_name"] or row["chat_jid"],
        is_manual=bool(row.get("is_manual", 0)),
        is_group=_is_group(row["chat_jid"]),
        last_synced=row.get("last_synced"),
        last_message_time=row.get("last_message_time"),
        message_count=int(row.get("message_count", 0) or 0),
        added_at=row.get("added_at") or "",
    )


@router.get("/all", response_model=list[ChatBrief])
def all_chats(
    limit: int = Query(500, ge=1, le=2000),
    db: Database = Depends(get_db),
    _: object = Depends(require_auth),
) -> list[ChatBrief]:
    rows = db.list_chats(limit=limit, sort_by="chat_name", order="asc")
    return [ChatBrief(chat_jid=r["chat_jid"], chat_name=r["chat_name"] or r["chat_jid"]) for r in rows]


@router.get("/search", response_model=list[ChatBrief])
def search_chats(
    q: str = Query("", description="Substring of chat name or JID"),
    limit: int = Query(30, ge=1, le=100),
    chat_type: Optional[str] = None,
    db: Database = Depends(get_db),
    _: object = Depends(require_auth),
) -> list[ChatBrief]:
    """Lean searchable lookup that scales to large chat lists.

    Sorted by ``last_message_time`` so the most recent matches surface first.
    """
    rows = db.list_chats(
        limit=limit,
        sort_by="last_message_time",
        order="desc",
        search=q.strip() or None,
        chat_type=chat_type,
    )
    return [ChatBrief(chat_jid=r["chat_jid"], chat_name=r["chat_name"] or r["chat_jid"]) for r in rows]


@router.get("", response_model=ChatListResponse)
def list_chats(
    page: int = 1,
    per_page: int = Query(20, ge=1, le=100),
    sort: str = "last_message_time",
    order: str = "desc",
    activity: Optional[str] = None,
    bot_status: Optional[str] = None,
    chat_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Database = Depends(get_db),
    bots: BotManager = Depends(get_bots),
    _: object = Depends(require_auth),
) -> ChatListResponse:
    offset = (page - 1) * per_page
    rows = db.list_chats(
        limit=per_page,
        offset=offset,
        sort_by=sort,
        order=order,
        activity=activity,
        bot_status=bot_status,
        chat_type=chat_type,
        search=search,
    )
    total = db.count_chats(
        activity=activity, bot_status=bot_status, chat_type=chat_type, search=search
    )
    items: list[ChatWithBots] = []
    for row in rows:
        chat = _row_to_chat(row)
        bot_statuses = [BotStatus(**s) for s in bots.statuses_for_chat(chat.chat_jid)]
        items.append(ChatWithBots(**chat.model_dump(), bots=bot_statuses))
    pages = (total + per_page - 1) // per_page if per_page else 1
    return ChatListResponse(
        chats=items,
        pagination=Pagination(page=page, per_page=per_page, total=total, total_pages=max(pages, 1)),
    )


@router.post("", response_model=Chat)
def add_chat(
    payload: AddChatRequest,
    db: Database = Depends(get_db),
    whatsapp: WhatsAppClient = Depends(get_whatsapp),
    _: object = Depends(require_auth),
) -> Chat:
    name = (payload.chat_name or "").strip()
    if not name:
        name = _lookup_friendly_name(whatsapp, payload.chat_jid) or payload.chat_jid
    ok = db.add_chat(payload.chat_jid, name, is_manual=True)
    if not ok:
        existing = db.get_chat(payload.chat_jid)
        if existing:
            return _row_to_chat(existing)
        raise HTTPException(status_code=400, detail="Failed to add chat")
    chat = db.get_chat(payload.chat_jid)
    if not chat:
        raise HTTPException(status_code=500, detail="Could not load added chat")
    return _row_to_chat(chat)


def _lookup_friendly_name(whatsapp: WhatsAppClient, chat_jid: str) -> Optional[str]:
    """Best-effort friendly name lookup for a single chat."""
    if chat_jid.endswith("@g.us"):
        info = whatsapp.get_group_info(chat_jid) or whatsapp.get_chat_info(chat_jid)
    else:
        info = whatsapp.get_user_info(chat_jid) or whatsapp.get_chat_info(chat_jid)
    if not info:
        return None
    return WhatsAppClient.extract_friendly_name(info)


@router.post("/sync", response_model=SimpleMessage)
def sync_chats(
    db: Database = Depends(get_db),
    whatsapp: WhatsAppClient = Depends(get_whatsapp),
    _: object = Depends(require_auth),
) -> SimpleMessage:
    groups = whatsapp.get_groups(fetch_all=True)
    chats = whatsapp.get_chats(fetch_all=True)
    contacts = whatsapp.get_contacts(fetch_all=True)
    now = datetime.now(timezone.utc).isoformat()
    g = c = u = 0

    # Build a contact-name lookup keyed by both "user" part and full JID so we
    # can backfill DM names regardless of the shape returned by the gateway.
    contact_names: dict[str, str] = {}
    for contact in contacts:
        if not isinstance(contact, dict):
            continue
        jid = (
            contact.get("JID")
            or contact.get("jid")
            or contact.get("id")
            or contact.get("ID")
            or ""
        )
        name = WhatsAppClient.extract_friendly_name(contact)
        if jid and name:
            contact_names[str(jid)] = name
            if "@" in str(jid):
                contact_names[str(jid).split("@", 1)[0]] = name

    def _resolve_dm_name(jid: str, raw: dict) -> Optional[str]:
        # 1) name on the chat object itself
        n = WhatsAppClient.extract_friendly_name(raw)
        if n:
            return n
        # 2) contact directory match
        n = contact_names.get(jid) or contact_names.get(jid.split("@", 1)[0])
        if n:
            return n
        return None

    for grp in groups:
        jid = grp.get("JID") or grp.get("jid") or grp.get("id") or grp.get("ID")
        if not jid:
            continue
        jid = str(jid)
        name = WhatsAppClient.extract_friendly_name(grp) or jid
        if db.get_chat(jid):
            db.update_chat(jid, chat_name=name, last_synced=now)
        else:
            db.add_chat(jid, name, is_manual=False)
        g += 1

    for chat in chats:
        jid = chat.get("jid") or chat.get("JID") or chat.get("id") or chat.get("ID")
        if not jid or _is_group(str(jid)):
            continue
        jid = str(jid)
        name = _resolve_dm_name(jid, chat) or jid
        if db.get_chat(jid):
            db.update_chat(jid, chat_name=name, last_synced=now)
        else:
            db.add_chat(jid, name, is_manual=False)
        c += 1

    # Backfill any chat that still has its JID for a name (e.g. from earlier
    # sync runs before this code existed).
    for row in db.list_chats():
        jid = row["chat_jid"]
        cur_name = (row.get("chat_name") or "").strip()
        if cur_name and cur_name != jid and not cur_name.startswith(("Imported ", "Chat ", "Group ")):
            continue
        better = _resolve_dm_name(jid, {}) if not _is_group(jid) else None
        if not better:
            better = _lookup_friendly_name(whatsapp, jid)
        if better and better != cur_name:
            db.update_chat(jid, chat_name=better, last_synced=now)
            u += 1

    msg = f"Synced {g} group(s) and {c} individual chat(s)."
    if u:
        msg += f" Refined {u} display name(s)."
    return SimpleMessage(message=msg)


@router.get("/{chat_jid}", response_model=ChatWithBots)
def get_chat(
    chat_jid: str,
    db: Database = Depends(get_db),
    bots: BotManager = Depends(get_bots),
    _: object = Depends(require_auth),
) -> ChatWithBots:
    row = db.get_chat(chat_jid)
    if not row:
        raise HTTPException(status_code=404, detail="Chat not found")
    chat = _row_to_chat(row)
    statuses = [BotStatus(**s) for s in bots.statuses_for_chat(chat_jid)]
    return ChatWithBots(**chat.model_dump(), bots=statuses)


@router.delete("/{chat_jid}", response_model=SimpleMessage)
def delete_chat(
    chat_jid: str,
    db: Database = Depends(get_db),
    bots: BotManager = Depends(get_bots),
    _: object = Depends(require_auth),
) -> SimpleMessage:
    if not db.get_chat(chat_jid):
        raise HTTPException(status_code=404, detail="Chat not found")
    for spec in bots.specs:
        if bots.is_running(spec.name, chat_jid):
            bots.stop(spec.name, chat_jid)
    db.delete_chat(chat_jid)
    return SimpleMessage(message=f"Chat {chat_jid} deleted")


@router.get("/{chat_jid}/messages")
def chat_messages(
    chat_jid: str,
    limit: int = Query(20, ge=1, le=100),
    whatsapp: WhatsAppClient = Depends(get_whatsapp),
    _: object = Depends(require_auth),
) -> dict:
    messages = whatsapp.get_messages(chat_jid, limit=limit)
    return {"chat_jid": chat_jid, "messages": messages, "count": len(messages)}


@router.post("/bulk", response_model=SimpleMessage)
def bulk_action(
    payload: BulkActionRequest,
    db: Database = Depends(get_db),
    bots: BotManager = Depends(get_bots),
    _: object = Depends(require_auth),
) -> SimpleMessage:
    action = payload.action
    if action not in {"start_bots", "stop_bots", "delete_chats"}:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    succeeded = 0
    for chat_jid in payload.chat_jids:
        try:
            if action == "start_bots":
                for bot_name in db.get_running_bots_for_chat(chat_jid):
                    bots.start(bot_name, chat_jid)
                succeeded += 1
            elif action == "stop_bots":
                for spec in bots.specs:
                    if bots.is_running(spec.name, chat_jid):
                        bots.stop(spec.name, chat_jid)
                succeeded += 1
            elif action == "delete_chats":
                for spec in bots.specs:
                    if bots.is_running(spec.name, chat_jid):
                        bots.stop(spec.name, chat_jid)
                db.delete_chat(chat_jid)
                succeeded += 1
        except Exception as e:  # pragma: no cover
            logger.warning("Bulk action failed for %s: %s", chat_jid, e)

    return SimpleMessage(message=f"{action}: applied to {succeeded}/{len(payload.chat_jids)} chats")
