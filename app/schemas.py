"""Pydantic models exposed by the HTTP API."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.security import is_valid_chat_jid


# ----- Auth -----------------------------------------------------------------
class LoginRequest(BaseModel):
    # Bound the input so a client can't ship a megabyte of password to chew
    # CPU in the constant-time comparison.
    user: Optional[str] = Field(default=None, max_length=128)
    password: str = Field(..., min_length=1, max_length=512)


class AuthStatus(BaseModel):
    auth_required: bool
    user: Optional[str] = None


class SimpleMessage(BaseModel):
    message: str


# ----- Bot catalog ----------------------------------------------------------
class BotSupports(BaseModel):
    text: bool = True
    image: bool = False
    audio: bool = False
    video: bool = False


class BotType(BaseModel):
    name: str
    label: str
    prefix: str
    emoji: str
    description: str
    supports: BotSupports


class BotStatus(BaseModel):
    name: str
    label: str
    prefix: str
    emoji: str
    description: str
    chat_jid: str
    status: str  # "running" | "stopped"
    uptime_seconds: Optional[int] = None
    answer_owner_messages: bool = True
    context_message_count: int = 0
    response_chat_jid: Optional[str] = None
    supports: BotSupports


class BotLogEntry(BaseModel):
    timestamp: str
    level: str
    message: str


class BotLogs(BaseModel):
    bot_name: str
    chat_jid: str
    logs: list[BotLogEntry]


# ----- Chats ----------------------------------------------------------------
class Chat(BaseModel):
    chat_jid: str
    chat_name: str
    is_manual: bool = False
    is_group: bool = False
    last_synced: Optional[str] = None
    last_message_time: Optional[str] = None
    message_count: int = 0
    added_at: str


class ChatWithBots(Chat):
    bots: list[BotStatus] = Field(default_factory=list)


class ChatBrief(BaseModel):
    chat_jid: str
    chat_name: str


class Pagination(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


class ChatListResponse(BaseModel):
    chats: list[ChatWithBots]
    pagination: Pagination


class AddChatRequest(BaseModel):
    chat_jid: str = Field(..., max_length=200)
    chat_name: Optional[str] = Field(default=None, max_length=200)

    @field_validator("chat_jid")
    @classmethod
    def _check_chat_jid(cls, v: str) -> str:
        if not is_valid_chat_jid(v):
            raise ValueError("Invalid chat JID")
        return v.strip()


# Cap bulk actions so a single request can't fan out into thousands of
# gateway calls (rate limits, accidental DoS, accidental damage).
_BULK_MAX_ITEMS = 200


class BulkActionRequest(BaseModel):
    chat_jids: list[str] = Field(..., max_length=_BULK_MAX_ITEMS)
    action: Literal["start_bots", "stop_bots", "delete_chats"]

    @field_validator("chat_jids")
    @classmethod
    def _check_chat_jids(cls, v: list[str]) -> list[str]:
        for jid in v:
            if not is_valid_chat_jid(jid):
                raise ValueError(f"Invalid chat JID: {jid!r}")
        return v


class BotSettingsUpdate(BaseModel):
    answer_owner_messages: Optional[bool] = None
    context_message_count: Optional[int] = Field(default=None, ge=0, le=10_000)
    # Empty string clears it; otherwise must be a real JID we already know.
    response_chat_jid: Optional[str] = Field(default=None, max_length=200)

    @field_validator("response_chat_jid")
    @classmethod
    def _check_target(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return v
        if not is_valid_chat_jid(v):
            raise ValueError("Invalid response_chat_jid")
        return v.strip()


# ----- System ---------------------------------------------------------------
class Health(BaseModel):
    status: str
    timestamp: str
    version: str


class Stats(BaseModel):
    total_chats: int
    running_bots: int
    available_bot_types: int
    active_chats_24h: int


class SystemInfo(BaseModel):
    version: str
    environment: str
    auth_required: bool
    whatsapp_base_url: Optional[str] = None
    openai_model: str
    openai_vision_model: str
    openai_audio_model: str
    poll_interval: int
    db_path: str


# ----- Diagnostics ----------------------------------------------------------
class GatewayDiagnostics(BaseModel):
    base_url: Optional[str] = None
    reachable: bool = False
    http_status: Optional[int] = None
    latency_ms: Optional[int] = None
    is_connected: bool = False
    is_logged_in: bool = False
    device_id: Optional[str] = None
    error: Optional[str] = None
    last_call_at: Optional[str] = None
    last_error_at: Optional[str] = None
    call_count: int = 0
    error_count: int = 0


class LlmSurfaceActivity(BaseModel):
    """Per-surface (text / vision / audio / video) live activity."""

    surface: Literal["text", "vision", "audio", "video"]
    model: Optional[str] = None
    call_count: int = 0
    success_count: int = 0
    error_count: int = 0
    last_call_at: Optional[str] = None
    last_success_at: Optional[str] = None
    last_error_at: Optional[str] = None
    last_error_message: Optional[str] = None
    last_latency_ms: Optional[int] = None


class LlmDiagnostics(BaseModel):
    base_url: Optional[str] = None
    text_model: str
    vision_model: str
    audio_model: str
    api_key_set: bool
    surfaces: list[LlmSurfaceActivity] = Field(default_factory=list)


class InboundObservation(BaseModel):
    """Last observed inbound message of a given media type."""

    media_type: Literal[
        "text", "image", "audio", "video", "document", "sticker", "other"
    ]
    last_seen_at: Optional[str] = None
    last_chat_jid: Optional[str] = None
    last_chat_name: Optional[str] = None
    last_sender: Optional[str] = None
    total_count: int = 0


class DatabaseDiagnostics(BaseModel):
    path: str
    size_bytes: int
    chats: int
    assignments: int
    processed_messages: int


class BotsDiagnostics(BaseModel):
    catalog_size: int
    running: int
    poll_interval: int


class GatewayErrorEntry(BaseModel):
    timestamp: str
    where: str
    status: Optional[int] = None
    message: str


class Diagnostics(BaseModel):
    timestamp: str
    version: str
    environment: str
    gateway: GatewayDiagnostics
    llm: LlmDiagnostics
    database: DatabaseDiagnostics
    bots: BotsDiagnostics
    inbound: list[InboundObservation] = Field(default_factory=list)
    recent_errors: list[GatewayErrorEntry] = Field(default_factory=list)
